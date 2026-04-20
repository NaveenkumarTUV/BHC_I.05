"""
deq_routes.py
-------------
FastAPI APIRouter for the Detailed Examination Quotation (DEQ) module.
DEQ quotations are linked to BHC (Building Health Check-Up) quotations.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.services.bhc_admin_auth import (
    require_admin_user,
    require_authenticated_user,
)
from backend.app.services.bhc_config_db import (
    get_user_signature,
    list_deq_sections,
    get_deq_section,
    create_deq_section,
    update_deq_section,
    delete_deq_section,
    reorder_deq_sections,
)
from backend.app.services.bhc_workflow_db import (
    list_processed_clients,
    log_workflow_audit_event,
)
from backend.app.services.deq_db import (
    create_deq_record,
    deq_dashboard_summary,
    delete_deq_record,
    get_deq_record,
    init_deq_db,
    list_deq_records,
    update_deq_record,
)
from backend.app.services.deq_output_generator import generate_deq_pdf
from backend.app.services.bhc_workflow_service import PROCESSED_DB_PATH, BHC_EXPORT_DIR, safe_filename
from backend.app.utils.paths import DATA_DIR, EXPORTS_DIR, ensure_dir

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEQ_EXPORT_DIR = EXPORTS_DIR / "deq"
DEQ_DB_PATH = PROCESSED_DB_PATH  # DEQ records live in the same DB file as BHC


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/deq", tags=["DEQ"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class DeqCreateRequest(BaseModel):
    bhc_enquiry_id: str = ""
    bhc_ref_number: str = ""
    client_name: str
    phone: str = ""
    property_type: str = ""
    area: Optional[float] = None
    issue_description: str = ""
    examination_type: str = "Structural"
    deq_quoted_amount: float = 0.0


class DeqUpdateRequest(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    remarks: Optional[str] = None
    deq_quoted_amount: Optional[float] = None
    issue_description: Optional[str] = None
    examination_type: Optional[str] = None


class DeqSectionCreateRequest(BaseModel):
    heading: str
    content_type: str = "list"
    content: list = []


class DeqSectionUpdateRequest(BaseModel):
    heading: Optional[str] = None
    content: Optional[list] = None
    is_visible: Optional[bool] = None
    content_type: Optional[str] = None


class DeqSectionReorderRequest(BaseModel):
    ordered_ids: list[int]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ALLOWED_PAYMENTS_BY_STATUS = {
    "quoted": {"pending"},
    "converted": {"pending", "paid"},
    "dropped": {"pending"},
}

ALLOWED_STATUSES = {"Quoted", "Converted", "Dropped"}
ALLOWED_PAYMENTS = {"Pending", "Paid"}


def _ensure_auth(request: Request) -> dict[str, Any]:
    return require_authenticated_user(request)


def _ensure_admin(request: Request) -> dict[str, Any]:
    return require_admin_user(request)


def _validate_status_payment(status: str | None, payment: str | None) -> None:
    if status and status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{status}'. Must be one of: {', '.join(sorted(ALLOWED_STATUSES))}.")
    if payment and payment not in ALLOWED_PAYMENTS:
        raise HTTPException(status_code=400, detail=f"Invalid payment_status '{payment}'. Must be one of: {', '.join(sorted(ALLOWED_PAYMENTS))}.")
    if status and payment:
        allowed = ALLOWED_PAYMENTS_BY_STATUS.get(status.lower(), set())
        if payment.lower() not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Payment status '{payment}' is not allowed for status '{status}'.",
            )


# ---------------------------------------------------------------------------
# DEQ Pipeline Endpoints
# ---------------------------------------------------------------------------

@router.get("/pipeline")
async def list_deq_pipeline(request: Request):
    _ensure_auth(request)
    ensure_dir(DEQ_EXPORT_DIR)
    init_deq_db(DEQ_DB_PATH)
    rows = list_deq_records(DEQ_DB_PATH)
    return {"count": len(rows), "records": rows}


@router.post("/pipeline")
async def create_deq(body: DeqCreateRequest, request: Request):
    user = _ensure_auth(request)
    if not body.client_name.strip():
        raise HTTPException(status_code=400, detail="Client name is required.")
    if body.deq_quoted_amount < 0:
        raise HTTPException(status_code=400, detail="DEQ quoted amount cannot be negative.")
    ensure_dir(DEQ_EXPORT_DIR)
    record = create_deq_record(DEQ_DB_PATH, body.model_dump())
    log_workflow_audit_event(
        DEQ_DB_PATH,
        event_type="DEQ_CREATED",
        actor_email=user.get("email", ""),
        enquiry_id=record["id"],
        severity="INFO",
        metadata={
            "deq_ref": record["deq_reference_number"],
            "bhc_ref": body.bhc_ref_number,
            "client_name": body.client_name,
        },
    )
    return {"record": record}


@router.put("/pipeline/{deq_id}")
async def update_deq(deq_id: str, body: DeqUpdateRequest, request: Request):
    user = _ensure_auth(request)
    _validate_status_payment(body.status, body.payment_status)
    existing = get_deq_record(DEQ_DB_PATH, deq_id)
    if not existing:
        raise HTTPException(status_code=404, detail="DEQ record not found.")
    ok = update_deq_record(
        DEQ_DB_PATH,
        deq_id,
        status=body.status,
        payment_status=body.payment_status,
        remarks=body.remarks,
        deq_quoted_amount=body.deq_quoted_amount,
        issue_description=body.issue_description,
        examination_type=body.examination_type,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="No fields to update.")
    log_workflow_audit_event(
        DEQ_DB_PATH,
        event_type="DEQ_UPDATED",
        actor_email=user.get("email", ""),
        enquiry_id=deq_id,
        severity="INFO",
        metadata={"status": body.status, "payment_status": body.payment_status},
    )
    updated = get_deq_record(DEQ_DB_PATH, deq_id)
    return {"record": updated}


@router.delete("/pipeline/{deq_id}")
async def delete_deq(deq_id: str, request: Request):
    admin = _ensure_admin(request)
    existing = get_deq_record(DEQ_DB_PATH, deq_id)
    if not existing:
        raise HTTPException(status_code=404, detail="DEQ record not found.")
    delete_deq_record(DEQ_DB_PATH, deq_id)
    log_workflow_audit_event(
        DEQ_DB_PATH,
        event_type="DEQ_DELETED",
        actor_email=admin.get("email", ""),
        enquiry_id=deq_id,
        severity="WARN",
        metadata={"deq_ref": existing.get("deq_reference_number", "")},
    )
    return {"deleted": True}


@router.get("/dashboard")
async def deq_dashboard(request: Request):
    _ensure_auth(request)
    init_deq_db(DEQ_DB_PATH)
    return deq_dashboard_summary(DEQ_DB_PATH)


# ---------------------------------------------------------------------------
# BHC Clients (for linking)
# ---------------------------------------------------------------------------

@router.get("/bhc-clients")
async def get_bhc_clients(request: Request):
    """Return all BHC pipeline records (for selecting which one to link a DEQ to)."""
    _ensure_auth(request)
    rows = list_processed_clients(PROCESSED_DB_PATH)
    return {"count": len(rows), "clients": rows}


# ---------------------------------------------------------------------------
# PDF Generation
# ---------------------------------------------------------------------------

@router.post("/download/pdf/{deq_id}")
async def download_deq_pdf(deq_id: str, request: Request):
    user = _ensure_auth(request)
    record = get_deq_record(DEQ_DB_PATH, deq_id)
    if not record:
        raise HTTPException(status_code=404, detail="DEQ record not found.")

    deq_data = {
        "record": record,
        "prepared_by": {
            "full_name": user.get("full_name", ""),
            "designation": user.get("designation", ""),
            "signature": get_user_signature(user["email"]),
        },
    }

    ensure_dir(DEQ_EXPORT_DIR)
    filename = safe_filename(record.get("deq_reference_number", record["id"]), "pdf")
    filename = f"DEQ_{filename}"
    output_path = DEQ_EXPORT_DIR / filename

    try:
        generate_deq_pdf(deq_data, output_path, include_signature=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    log_workflow_audit_event(
        DEQ_DB_PATH,
        event_type="DEQ_PDF_DOWNLOADED",
        actor_email=user.get("email", ""),
        enquiry_id=deq_id,
        severity="INFO",
        metadata={"deq_ref": record.get("deq_reference_number", "")},
    )

    return StreamingResponse(
        io.BytesIO(output_path.read_bytes()),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Excel Export
# ---------------------------------------------------------------------------

@router.get("/export")
async def export_deq_pipeline(request: Request):
    _ensure_auth(request)
    init_deq_db(DEQ_DB_PATH)
    rows = list_deq_records(DEQ_DB_PATH)
    if not rows:
        raise HTTPException(status_code=404, detail="No DEQ records available for export.")

    ensure_dir(DEQ_EXPORT_DIR)
    filename = f"DEQ_Pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    output_path = DEQ_EXPORT_DIR / filename

    df = pd.DataFrame(rows)
    ordered_cols = [
        "deq_reference_number",
        "bhc_ref_number",
        "client_name",
        "phone",
        "property_type",
        "area",
        "examination_type",
        "issue_description",
        "deq_quoted_amount",
        "quote_generated_date",
        "status",
        "payment_status",
        "remarks",
        "created_at",
        "updated_at",
    ]
    export_cols = [c for c in ordered_cols if c in df.columns]
    df = df[export_cols]
    col_labels = {
        "deq_reference_number": "DEQ Reference No.",
        "bhc_ref_number": "Linked BHC Ref No.",
        "client_name": "Client Name",
        "phone": "Phone",
        "property_type": "Property Type",
        "area": "Area (sq.ft)",
        "examination_type": "Examination Type",
        "issue_description": "Issues Identified",
        "deq_quoted_amount": "DEQ Quoted Amount (Rs.)",
        "quote_generated_date": "DEQ Date",
        "status": "Status",
        "payment_status": "Payment Status",
        "remarks": "Remarks",
        "created_at": "Created At",
        "updated_at": "Updated At",
    }
    df.rename(columns={k: v for k, v in col_labels.items() if k in df.columns}, inplace=True)
    df.to_excel(output_path, index=False)

    return StreamingResponse(
        io.BytesIO(output_path.read_bytes()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# DEQ Sections Admin
# ---------------------------------------------------------------------------

@router.get("/admin/sections")
async def deq_admin_list_sections(request: Request):
    _ensure_auth(request)
    return {"deq_sections": list_deq_sections()}


@router.post("/admin/sections")
async def deq_admin_create_section(body: DeqSectionCreateRequest, request: Request):
    admin = _ensure_admin(request)
    try:
        section = create_deq_section(
            heading=body.heading,
            content_type=body.content_type,
            content=body.content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"section": section}


@router.put("/admin/sections/reorder")
async def deq_admin_reorder_sections(body: DeqSectionReorderRequest, request: Request):
    _ensure_admin(request)
    sections = reorder_deq_sections(body.ordered_ids)
    return {"deq_sections": sections}


@router.put("/admin/sections/{section_id}")
async def deq_admin_update_section(section_id: int, body: DeqSectionUpdateRequest, request: Request):
    _ensure_admin(request)
    try:
        section = update_deq_section(
            section_id=section_id,
            heading=body.heading,
            content=body.content,
            is_visible=body.is_visible,
            content_type=body.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"section": section}


@router.delete("/admin/sections/{section_id}")
async def deq_admin_delete_section(section_id: int, request: Request):
    _ensure_admin(request)
    try:
        delete_deq_section(section_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"deleted": True}

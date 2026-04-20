"""
bhc_routes.py
-------------
FastAPI APIRouter for the Building Health Check (BHC) internal quotation workflow.

Primary flow:
  Microsoft Forms Excel -> Pending clients -> Generate quote -> Save in DB -> Dashboard
"""

import io
import uuid
from datetime import datetime
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.app.services.bhc_admin_auth import (
    clear_auth_cookie,
    require_admin_user,
    require_authenticated_user,
    set_auth_cookie,
)
from backend.app.services.bhc_config_db import (
    DEFAULT_ADMIN_EMAIL,
    authenticate_user_credentials,
    admin_reset_user_password,
    approve_user,
    change_user_password,
    create_user_account,
    get_admin_config,
    get_config_schema_version,
    get_user_signature,
    list_security_audit_events,
    list_user_accounts,
    log_security_audit_event,
    reset_user_password_by_email,
    replace_pricing_slabs,
    save_user_signature,
    self_register_user,
    set_security_question,
    get_security_question,
    SECURITY_QUESTIONS,
    update_company_settings,
    update_document_settings,
    update_user_profile,
    list_scope_of_work_items,
    replace_scope_of_work_items,
    list_support_document_items,
    replace_support_document_items,
    list_quotation_sections,
    create_quotation_section,
    update_quotation_section,
    delete_quotation_section,
    reorder_quotation_sections,
    SLAB_CATEGORY_STANDARD,
    SLAB_CATEGORY_NEW_BUILDING,
)
from backend.app.services.bhc_output_generator import (
    generate_quote_pdf,
)
from backend.app.services.bhc_workflow_db import (
    upsert_processed_client,
    list_processed_clients,
    get_processed_client_by_id,
    get_workflow_schema_version,
    list_workflow_audit_events,
    log_workflow_audit_event,
    update_client_status,
    dashboard_summary,
)
from backend.app.services.bhc_pricing_engine import get_pricing_config
from backend.app.services.bhc_workflow_service import (
    BHC_EXPORT_DIR,
    LOCAL_ENQUIRY_EXCEL_PATH,
    PROCESSED_DB_PATH,
    build_quote_data,
    find_client,
    get_active_excel_path_or_none,
    list_pending_clients,
    read_workflow_clients,
    safe_filename,
    validate_status_payment_combination,
)
from backend.app.utils.paths import DATA_DIR, ensure_dir

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/bhc", tags=["BHC"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class GenerateQuoteRequest(BaseModel):
    client_name: str
    phone: Optional[str] = None
    property_type: Optional[str] = None
    area: Optional[float] = None
    building_system: Optional[str] = None
    building_age: Optional[str] = None
    timestamp: Optional[str] = None
    override_final_price: Optional[float] = None
    discount_percent: Optional[float] = None


class DownloadRequest(BaseModel):
    client_name: str
    phone: Optional[str] = None
    property_type: Optional[str] = None
    area: Optional[float] = None
    building_system: Optional[str] = None
    building_age: Optional[str] = None
    timestamp: Optional[str] = None
    override_final_price: Optional[float] = None
    reference_number: Optional[str] = None
    discount_percent: Optional[float] = None
    include_signature: bool = True


class EmailDraftRequest(BaseModel):
    client_name: str
    to_email: Optional[str] = None
    phone: Optional[str] = None
    property_type: Optional[str] = None
    area: Optional[float] = None
    building_system: Optional[str] = None
    building_age: Optional[str] = None
    timestamp: Optional[str] = None
    override_final_price: Optional[float] = None
    reference_number: Optional[str] = None
    discount_percent: Optional[float] = None


class UpdateStatusRequest(BaseModel):
    enquiry_id: str
    status: Optional[str] = None
    payment_status: Optional[str] = None
    remarks: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str
    new_password: str
    security_answer: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    password: str
    is_admin: bool = False
    designation: str = ""


class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str
    designation: str = ""
    security_question: str = ""
    security_answer: str = ""


class AdminResetPasswordRequest(BaseModel):
    email: str
    new_password: str


class ApproveUserRequest(BaseModel):
    email: str


class CompanySettingsRequest(BaseModel):
    company_name: str
    company_subtitle: str
    company_address: str
    company_phone: str
    company_email: str
    contact_name: str
    urgency_surcharge_percent: str = "10"
    gst_percent: str = "18"


class DocumentSettingsRequest(BaseModel):
    company_profile_paragraphs: list[str]
    tuv_history_paragraphs: list[str]
    service_capabilities: list[str]
    payment_terms: list[str]
    deliverables: list[str]
    other_terms: list[str]
    system_generated_note: str


class PricingSlabRequest(BaseModel):
    min_area: float
    max_area: float
    label: str
    quoted_price: float


class PricingSettingsRequest(BaseModel):
    slabs: list[PricingSlabRequest]
    new_building_slabs: list[PricingSlabRequest] = []


class ScopeOfWorkRequest(BaseModel):
    rcc: list[str] = []
    steel: list[str] = []
    both: list[str] = []
    new_rcc: list[str] = []
    new_steel: list[str] = []
    new_both: list[str] = []


class SupportDocumentsRequest(BaseModel):
    rcc: list[str] = []
    steel: list[str] = []
    both: list[str] = []
    new_rcc: list[str] = []
    new_steel: list[str] = []
    new_both: list[str] = []


class QuotationSectionCreateRequest(BaseModel):
    heading: str
    content_type: str = "list"
    content: list = []


class QuotationSectionUpdateRequest(BaseModel):
    heading: Optional[str] = None
    content: Optional[list] = None
    is_visible: Optional[bool] = None
    content_type: Optional[str] = None


class QuotationSectionReorderRequest(BaseModel):
    ordered_ids: list[int]


def ensure_authenticated(request: Request) -> dict[str, Any]:
    """Return authenticated user payload or raise HTTP 401."""
    return require_authenticated_user(request)


def ensure_admin(request: Request) -> dict[str, Any]:
    """Return authenticated admin payload or raise HTTP 403."""
    return require_admin_user(request)


def _build_quote_payload(
    *,
    client_name: str,
    override_final_price: Optional[float],
    reference_number: Optional[str],
    building_system: Optional[str],
    building_age: Optional[str],
    phone: Optional[str],
    timestamp: Optional[str],
    property_type: Optional[str],
    area_sqft: Optional[float],
    discount_percent: Optional[float],
) -> dict[str, Any]:
    """Build normalized quote payload from request fields."""
    return build_quote_data(
        client_name=client_name,
        override_final_price=override_final_price,
        reference_number=reference_number,
        building_system=building_system,
        building_age=building_age,
        phone=phone,
        timestamp=timestamp,
        property_type=property_type,
        area_sqft=area_sqft,
        discount_percent=discount_percent,
    )


def _filter_processed_rows(
    rows: list[dict[str, Any]],
    *,
    search: Optional[str],
    status: Optional[str],
    payment_status: Optional[str],
    property_type: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> list[dict[str, Any]]:
    """Apply dashboard/export filters to processed rows."""
    filtered_rows = rows

    search_query = (search or "").strip().lower()
    if search_query:
        filtered_rows = [
            row
            for row in filtered_rows
            if search_query in str(row.get("client_name", "")).lower()
            or search_query in str(row.get("phone", "")).lower()
            or search_query in str(row.get("enquiry_id", "")).lower()
        ]

    status_filter = (status or "").strip().lower()
    if status_filter:
        filtered_rows = [
            row for row in filtered_rows if str(row.get("status", "")).strip().lower() == status_filter
        ]

    payment_filter = (payment_status or "").strip().lower()
    if payment_filter:
        filtered_rows = [
            row
            for row in filtered_rows
            if str(row.get("payment_status", "")).strip().lower() == payment_filter
        ]

    property_filter = (property_type or "").strip().lower()
    if property_filter:
        filtered_rows = [
            row
            for row in filtered_rows
            if str(row.get("property_type", "")).strip().lower() == property_filter
        ]

    if date_from:
        filtered_rows = [
            row for row in filtered_rows if str(row.get("quote_generated_date", ""))[:10] >= date_from
        ]

    if date_to:
        filtered_rows = [
            row for row in filtered_rows if str(row.get("quote_generated_date", ""))[:10] <= date_to
        ]

    return filtered_rows


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/excel-status")
async def excel_status(request: Request):
    ensure_authenticated(request)
    active_path = get_active_excel_path_or_none()
    exists = active_path is not None
    return {
        "file_exists": exists,
        "file_path": str(active_path) if exists else None,
        "file_name": active_path.name if exists else "bhc_enquiries.xlsx",
    }


@router.post("/upload-excel")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    """
    Upload / replace local BHC enquiry Excel file.
    This endpoint writes only to local data/bhc_enquiries.xlsx, never to EXCEL_FILE_PATH.
    """
    ensure_authenticated(request)
    allowed = {".xlsx", ".xls"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Please upload an Excel file (.xlsx or .xls).",
        )

    ensure_dir(DATA_DIR)
    content = await file.read()
    LOCAL_ENQUIRY_EXCEL_PATH.write_bytes(content)
    return {"message": "Excel file uploaded successfully.", "rows": len(read_workflow_clients(force_refresh=True))}


@router.get("/clients/pending")
async def get_pending_clients(request: Request):
    ensure_authenticated(request)
    try:
        pending = list_pending_clients()
    except HTTPException as exc:
        if exc.status_code == 404:
            return {"count": 0, "clients": []}
        raise
    return {"count": len(pending), "clients": pending}


@router.get("/clients/all")
async def get_processed_clients(request: Request):
    ensure_authenticated(request)
    rows = list_processed_clients(PROCESSED_DB_PATH)
    return {"count": len(rows), "clients": rows}


@router.get("/clients")
async def get_clients_compat(request: Request):
    ensure_authenticated(request)
    """Backward-compatible alias; now returns pending clients only."""
    data = await get_pending_clients(request)
    compat_clients = [
        {
            "name": c.get("name", ""),
            "phone": c.get("phone", ""),
            "location": c.get("location", ""),
            "property_type": c.get("property_type", ""),
            "building_system": c.get("building_system", ""),
            "area_sqft": c.get("area_sqft", ""),
            "building_age": c.get("building_age", ""),
            "urgency": c.get("urgency", ""),
            "timestamp": c.get("timestamp", ""),
            "enquiry_key": c.get("enquiry_key", ""),
        }
        for c in data["clients"]
    ]
    return {"count": len(compat_clients), "clients": compat_clients}


@router.get("/client/{name}")
async def get_client(request: Request, name: str, phone: Optional[str] = None, timestamp: Optional[str] = None):
    ensure_authenticated(request)
    c = find_client(name, phone, timestamp)
    return {
        "Client_Name": c.get("name", ""),
        "Phone_Number": c.get("phone", ""),
        "Location": c.get("location", ""),
        "Property_Type": c.get("property_type", ""),
        "Building_System": c.get("building_system", ""),
        "Area_sqft": c.get("area_sqft", ""),
        "Issue_Observed": c.get("issue_observed", ""),
        "Building_Age": c.get("building_age", ""),
        "Urgency": c.get("urgency", ""),
        "Notes": c.get("notes", ""),
        "Timestamp": c.get("timestamp", ""),
        "_area_numeric": c.get("area_numeric", 0),
    }


@router.post("/generate-quote")
async def generate_quote(body: GenerateQuoteRequest, request: Request):
    user = ensure_authenticated(request)
    quote_data = _build_quote_payload(
        client_name=body.client_name,
        override_final_price=body.override_final_price,
        reference_number=None,
        building_system=body.building_system,
        building_age=body.building_age,
        phone=body.phone,
        timestamp=body.timestamp,
        property_type=body.property_type,
        area_sqft=body.area,
        discount_percent=body.discount_percent,
    )

    enquiry_key = quote_data.get("enquiry_key", "")
    enquiry_id = str(uuid.uuid4())

    persisted_id = upsert_processed_client(
        PROCESSED_DB_PATH,
        {
            "enquiry_id": enquiry_id,
            "enquiry_key": enquiry_key,
            "client_name": quote_data["client"].get("Client_Name", ""),
            "phone": quote_data["client"].get("Phone_Number", ""),
            "property_type": quote_data["client"].get("Property_Type", ""),
            "area": quote_data["pricing"].get("area_sqft", 0),
            "quoted_amount": quote_data["pricing"].get("total_with_gst", 0),
            "reference_number": quote_data.get("reference_number", ""),
            "quote_generated_date": quote_data["generated_at"],
            "status": "Quoted",
            "payment_status": "Pending",
            "remarks": "",
            "timestamp": quote_data["client"].get("Timestamp", ""),
        },
    )

    log_workflow_audit_event(
        PROCESSED_DB_PATH,
        event_type="QUOTE_GENERATED",
        actor_email=user.get("email", ""),
        enquiry_id=persisted_id,
        severity="INFO",
        metadata={
            "client_name": quote_data["client"].get("Client_Name", ""),
            "reference_number": quote_data.get("reference_number", ""),
            "quoted_amount": quote_data["pricing"].get("total_with_gst", 0),
        },
    )

    quote_data["enquiry_id"] = persisted_id
    return quote_data


@router.post("/update-status")
async def update_status(body: UpdateStatusRequest, request: Request):
    user = ensure_authenticated(request)
    current = get_processed_client_by_id(PROCESSED_DB_PATH, body.enquiry_id)
    if not current:
        raise HTTPException(status_code=404, detail="Enquiry not found.")

    next_status = (body.status if body.status is not None else current.get("status", "")).strip().lower()
    next_payment = (body.payment_status if body.payment_status is not None else current.get("payment_status", "")).strip().lower()
    validate_status_payment_combination(next_status, next_payment)

    ok = update_client_status(
        PROCESSED_DB_PATH,
        enquiry_id=body.enquiry_id,
        status=body.status,
        payment_status=body.payment_status,
        remarks=body.remarks,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Enquiry not found or no fields to update.")

    log_workflow_audit_event(
        PROCESSED_DB_PATH,
        event_type="PIPELINE_STATUS_UPDATED",
        actor_email=user.get("email", ""),
        enquiry_id=body.enquiry_id,
        severity="INFO",
        metadata={
            "status": body.status,
            "payment_status": body.payment_status,
            "remarks": body.remarks,
        },
    )

    return {"message": "Status updated successfully."}


@router.get("/dashboard")
async def dashboard_data(request: Request):
    ensure_authenticated(request)
    try:
        total = len(read_workflow_clients())
        pending = len(list_pending_clients())
    except HTTPException as exc:
        if exc.status_code == 404:
            total = 0
            pending = 0
        else:
            raise
    return dashboard_summary(PROCESSED_DB_PATH, total_enquiries=total, pending=pending)


@router.get("/pricing-config")
async def pricing_config(request: Request):
    ensure_authenticated(request)
    return {
        "model": "area_slab",
        "slabs": get_pricing_config(SLAB_CATEGORY_STANDARD),
        "new_building_slabs": get_pricing_config(SLAB_CATEGORY_NEW_BUILDING),
    }


@router.post("/auth/login")
async def login(body: LoginRequest, response: Response):
    try:
        user = authenticate_user_credentials(body.email, body.password)
        set_auth_cookie(response, user["email"])
        log_security_audit_event(
            event_type="AUTH_LOGIN_SUCCESS",
            actor_email=user["email"],
            target="session",
            severity="INFO",
            metadata={"is_admin": bool(user.get("is_admin"))},
        )
        return {
            "message": "Login successful.",
            "user": user,
        }
    except ValueError as exc:
        log_security_audit_event(
            event_type="AUTH_LOGIN_FAILED",
            actor_email=body.email,
            target="session",
            severity="WARN",
            metadata={"reason": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/logout")
async def logout(response: Response, request: Request):
    user = ensure_authenticated(request)
    clear_auth_cookie(response, request=request)
    log_security_audit_event(
        event_type="AUTH_LOGOUT",
        actor_email=user.get("email", ""),
        target="session",
        severity="INFO",
    )
    return {"message": "Logged out successfully."}


class SecurityQuestionLookup(BaseModel):
    email: str


@router.post("/auth/security-question/lookup")
async def lookup_security_question(body: SecurityQuestionLookup):
    """Return the security question for a given email (unauthenticated)."""
    try:
        question = get_security_question(body.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"question": question}


@router.get("/auth/security-questions")
async def list_security_questions():
    """Return the list of predefined security questions."""
    return {"questions": SECURITY_QUESTIONS}


@router.post("/auth/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    try:
        reset_user_password_by_email(body.email, body.new_password, body.security_answer)
        log_security_audit_event(
            event_type="AUTH_FORGOT_PASSWORD_RESET",
            actor_email=body.email,
            target=body.email,
            severity="WARN",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Password updated successfully. Please sign in with your new password.",
    }


@router.post("/auth/register")
async def register_user(body: RegisterRequest):
    """Self-registration — creates a pending account (is_active=0) awaiting admin approval."""
    try:
        user = self_register_user(
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            designation=body.designation,
            security_question=body.security_question,
            security_answer=body.security_answer,
        )
        log_security_audit_event(
            event_type="AUTH_SELF_REGISTRATION",
            actor_email=body.email,
            target=body.email,
            severity="INFO",
        )
        return {
            "message": "Registration successful. Your account is pending admin approval.",
            "user": user,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/change-password")
async def change_password(body: ChangePasswordRequest, request: Request):
    current_user = ensure_authenticated(request)
    try:
        change_user_password(
            email=current_user["email"],
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_security_audit_event(
        event_type="AUTH_PASSWORD_CHANGED",
        actor_email=current_user.get("email", ""),
        target=current_user.get("email", ""),
        severity="INFO",
    )

    response = JSONResponse({"message": "Password changed successfully. Please sign in again with the new password."})
    clear_auth_cookie(response, request=request)
    return response


@router.get("/admin/config")
async def admin_config(request: Request):
    ensure_admin(request)
    return get_admin_config()


@router.get("/admin/audit-events")
async def admin_audit_events(request: Request, limit: int = 200):
    ensure_admin(request)
    return {
        "config_schema_version": get_config_schema_version(),
        "workflow_schema_version": get_workflow_schema_version(PROCESSED_DB_PATH),
        "security_events": list_security_audit_events(limit=limit),
        "workflow_events": list_workflow_audit_events(PROCESSED_DB_PATH, limit=limit),
    }


@router.get("/admin/users")
async def admin_users(request: Request):
    ensure_admin(request)
    return {"users": list_user_accounts(), "admin_email": DEFAULT_ADMIN_EMAIL}


@router.post("/admin/users")
async def admin_create_user(body: CreateUserRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        user = create_user_account(
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            is_admin=body.is_admin,
            created_by=admin_user["email"],
            designation=body.designation,
        )
        log_security_audit_event(
            event_type="ADMIN_USER_CREATED",
            actor_email=admin_user.get("email", ""),
            target=body.email,
            severity="INFO",
            metadata={"is_admin": bool(body.is_admin)},
        )
        return {"message": "User created successfully.", "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/admin/users/approve")
async def admin_approve_user(body: ApproveUserRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        user = approve_user(body.email)
        log_security_audit_event(
            event_type="ADMIN_USER_APPROVED",
            actor_email=admin_user.get("email", ""),
            target=body.email,
            severity="INFO",
        )
        return {"message": f"User {body.email} has been approved.", "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/admin/users/reset-password")
async def admin_reset_password(body: AdminResetPasswordRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        user = admin_reset_user_password(body.email, body.new_password)
        log_security_audit_event(
            event_type="ADMIN_PASSWORD_RESET",
            actor_email=admin_user.get("email", ""),
            target=body.email,
            severity="WARN",
        )
        return {"message": f"Password reset for {body.email}.", "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class UpdateProfileRequest(BaseModel):
    designation: str = ""
    security_question: str = ""
    security_answer: str = ""


@router.put("/user/profile")
async def user_update_profile(body: UpdateProfileRequest, request: Request):
    current_user = ensure_authenticated(request)
    user = update_user_profile(current_user["email"], body.designation)
    if body.security_question and body.security_answer:
        try:
            user = set_security_question(current_user["email"], body.security_question, body.security_answer)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Profile updated.", "user": user}


@router.post("/user/signature")
async def user_upload_signature(request: Request, file: UploadFile = File(...)):
    current_user = ensure_authenticated(request)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Signature must be a PNG or JPEG image.")
    data = await file.read()
    if len(data) > 500_000:
        raise HTTPException(status_code=400, detail="Signature image must be under 500 KB.")
    save_user_signature(current_user["email"], data)
    return {"message": "Signature saved."}


@router.get("/user/signature/{email}")
async def user_get_signature(email: str, request: Request):
    ensure_authenticated(request)
    sig = get_user_signature(email)
    if not sig:
        raise HTTPException(status_code=404, detail="No signature found for this user.")
    content_type = "image/png"
    if sig[:3] == b"\xff\xd8\xff":
        content_type = "image/jpeg"
    return Response(content=sig, media_type=content_type)


@router.put("/admin/company")
async def admin_update_company(body: CompanySettingsRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        result = update_company_settings(body.model_dump())
        log_security_audit_event(
            event_type="ADMIN_COMPANY_SETTINGS_UPDATED",
            actor_email=admin_user.get("email", ""),
            target="company_settings",
            severity="INFO",
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/admin/document")
async def admin_update_document(body: DocumentSettingsRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        result = update_document_settings(body.model_dump())
        log_security_audit_event(
            event_type="ADMIN_DOCUMENT_SETTINGS_UPDATED",
            actor_email=admin_user.get("email", ""),
            target="document_settings",
            severity="INFO",
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/admin/pricing")
async def admin_update_pricing(body: PricingSettingsRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        standard_slabs = replace_pricing_slabs(
            [slab.model_dump() for slab in body.slabs],
            slab_category=SLAB_CATEGORY_STANDARD,
        )
        new_building_slabs = replace_pricing_slabs(
            [slab.model_dump() for slab in body.new_building_slabs],
            slab_category=SLAB_CATEGORY_NEW_BUILDING,
        ) if body.new_building_slabs else get_pricing_config(SLAB_CATEGORY_NEW_BUILDING)
        result = {
            "model": "area_slab",
            "slabs": standard_slabs,
            "new_building_slabs": new_building_slabs,
        }
        log_security_audit_event(
            event_type="ADMIN_PRICING_UPDATED",
            actor_email=admin_user.get("email", ""),
            target="pricing_slabs",
            severity="INFO",
            metadata={"slab_count": len(body.slabs), "new_building_slab_count": len(body.new_building_slabs)},
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/admin/scope-of-work")
async def admin_get_scope(request: Request):
    ensure_authenticated(request)
    return {"scope_of_work": list_scope_of_work_items(), "support_documents": list_support_document_items()}


@router.put("/admin/scope-of-work")
async def admin_update_scope(body: ScopeOfWorkRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        result = replace_scope_of_work_items(body.model_dump())
        log_security_audit_event(
            event_type="ADMIN_SCOPE_UPDATED",
            actor_email=admin_user.get("email", ""),
            target="scope_of_work_items",
            severity="INFO",
        )
        return {"scope_of_work": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/admin/support-documents")
async def admin_update_support_docs(body: SupportDocumentsRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        result = replace_support_document_items(body.model_dump())
        log_security_audit_event(
            event_type="ADMIN_SUPPORT_DOCS_UPDATED",
            actor_email=admin_user.get("email", ""),
            target="support_document_items",
            severity="INFO",
        )
        return {"support_documents": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── Quotation Sections Admin Endpoints ───────────────────────────────────

@router.get("/admin/quotation-sections")
async def admin_get_quotation_sections(request: Request):
    ensure_authenticated(request)
    return {"quotation_sections": list_quotation_sections()}


@router.post("/admin/quotation-sections")
async def admin_create_quotation_section(body: QuotationSectionCreateRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        section = create_quotation_section(
            heading=body.heading,
            content_type=body.content_type,
            content=body.content,
        )
        log_security_audit_event(
            event_type="ADMIN_QS_CREATED",
            actor_email=admin_user.get("email", ""),
            target=section["section_key"],
            severity="INFO",
        )
        return {"section": section}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/admin/quotation-sections/reorder")
async def admin_reorder_quotation_sections(body: QuotationSectionReorderRequest, request: Request):
    admin_user = ensure_admin(request)
    sections = reorder_quotation_sections(body.ordered_ids)
    log_security_audit_event(
        event_type="ADMIN_QS_REORDERED",
        actor_email=admin_user.get("email", ""),
        target="quotation_sections",
        severity="INFO",
    )
    return {"quotation_sections": sections}


@router.put("/admin/quotation-sections/{section_id}")
async def admin_update_quotation_section(section_id: int, body: QuotationSectionUpdateRequest, request: Request):
    admin_user = ensure_admin(request)
    try:
        section = update_quotation_section(
            section_id=section_id,
            heading=body.heading,
            content=body.content,
            is_visible=body.is_visible,
            content_type=body.content_type,
        )
        log_security_audit_event(
            event_type="ADMIN_QS_UPDATED",
            actor_email=admin_user.get("email", ""),
            target=section["section_key"],
            severity="INFO",
        )
        return {"section": section}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/admin/quotation-sections/{section_id}")
async def admin_delete_quotation_section(section_id: int, request: Request):
    admin_user = ensure_admin(request)
    try:
        delete_quotation_section(section_id)
        log_security_audit_event(
            event_type="ADMIN_QS_DELETED",
            actor_email=admin_user.get("email", ""),
            target=str(section_id),
            severity="WARN",
        )
        return {"deleted": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/export")
async def export_processed_clients(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    property_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    ensure_authenticated(request)
    rows = list_processed_clients(PROCESSED_DB_PATH)
    rows = _filter_processed_rows(
        rows,
        search=search,
        status=status,
        payment_status=payment_status,
        property_type=property_type,
        date_from=date_from,
        date_to=date_to,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No processed client data available for the selected filters.")

    ensure_dir(BHC_EXPORT_DIR)
    has_filters = any(
        [
            (search or "").strip(),
            (status or "").strip(),
            (payment_status or "").strip(),
            (property_type or "").strip(),
            date_from,
            date_to,
        ]
    )
    filename_suffix = "_Filtered" if has_filters else ""
    filename = f"BHC_Processed_Clients{filename_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    output_path = BHC_EXPORT_DIR / filename

    df = pd.DataFrame(rows)

    # Define column order: ref no first, then client details; drop internal fields
    ordered_cols = [
        "reference_number",
        "client_name",
        "phone",
        "property_type",
        "area",
        "quoted_amount",
        "quote_generated_date",
        "status",
        "payment_status",
        "remarks",
        "timestamp",
        "created_at",
        "updated_at",
    ]
    # Only keep columns that actually exist in the DataFrame
    export_cols = [c for c in ordered_cols if c in df.columns]
    df = df[export_cols]

    # Human-friendly header names
    col_labels = {
        "reference_number": "Reference Number",
        "client_name": "Client Name",
        "phone": "Phone",
        "property_type": "Property Type",
        "area": "Area (sq.ft)",
        "quoted_amount": "Quoted Amount (₹)",
        "quote_generated_date": "Quote Date",
        "status": "Status",
        "payment_status": "Payment Status",
        "remarks": "Remarks",
        "timestamp": "Enquiry Timestamp",
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
# Download endpoints
# ---------------------------------------------------------------------------
@router.post("/download/pdf")
async def download_pdf(body: DownloadRequest, request: Request):
    current_user = ensure_authenticated(request)
    quote_data = _build_quote_payload(
        client_name=body.client_name,
        override_final_price=body.override_final_price,
        reference_number=body.reference_number,
        building_system=body.building_system,
        building_age=body.building_age,
        phone=body.phone,
        timestamp=body.timestamp,
        property_type=body.property_type,
        area_sqft=body.area,
        discount_percent=body.discount_percent,
    )
    quote_data["prepared_by"] = {
        "full_name": current_user.get("full_name", ""),
        "designation": current_user.get("designation", ""),
        "signature": get_user_signature(current_user["email"]),
    }

    ensure_dir(BHC_EXPORT_DIR)
    filename = safe_filename(quote_data.get("reference_number", body.client_name), "pdf")
    output_path = BHC_EXPORT_DIR / filename

    try:
        generate_quote_pdf(quote_data, output_path, include_signature=body.include_signature)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    return StreamingResponse(
        io.BytesIO(output_path.read_bytes()),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/preview/pdf")
async def preview_pdf(body: DownloadRequest, request: Request):
    """Generate a PDF preview (without signature) and return inline for browser display."""
    current_user = ensure_authenticated(request)
    quote_data = _build_quote_payload(
        client_name=body.client_name,
        override_final_price=body.override_final_price,
        reference_number=body.reference_number,
        building_system=body.building_system,
        building_age=body.building_age,
        phone=body.phone,
        timestamp=body.timestamp,
        property_type=body.property_type,
        area_sqft=body.area,
        discount_percent=body.discount_percent,
    )
    quote_data["prepared_by"] = {
        "full_name": current_user.get("full_name", ""),
        "designation": current_user.get("designation", ""),
        "signature": get_user_signature(current_user["email"]),
    }

    ensure_dir(BHC_EXPORT_DIR)
    filename = safe_filename(quote_data.get("reference_number", body.client_name), "pdf")
    output_path = BHC_EXPORT_DIR / f"preview_{filename}"

    try:
        generate_quote_pdf(quote_data, output_path, include_signature=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF preview generation failed: {exc}")

    pdf_bytes = output_path.read_bytes()
    # Clean up preview file
    try:
        output_path.unlink()
    except OSError:
        pass

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="preview_{filename}"'},
    )


@router.post("/email-draft")
async def download_email_draft(body: EmailDraftRequest, request: Request):
    current_user = ensure_authenticated(request)
    quote_data = _build_quote_payload(
        client_name=body.client_name,
        override_final_price=body.override_final_price,
        reference_number=body.reference_number,
        building_system=body.building_system,
        building_age=body.building_age,
        phone=body.phone,
        timestamp=body.timestamp,
        property_type=body.property_type,
        area_sqft=body.area,
        discount_percent=body.discount_percent,
    )
    quote_data["prepared_by"] = {
        "full_name": current_user.get("full_name", ""),
        "designation": current_user.get("designation", ""),
        "signature": get_user_signature(current_user["email"]),
    }

    ensure_dir(BHC_EXPORT_DIR)
    attachment_filename = safe_filename(quote_data.get("reference_number", body.client_name), "pdf")
    attachment_path = BHC_EXPORT_DIR / attachment_filename

    try:
        generate_quote_pdf(quote_data, attachment_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Draft attachment generation failed: {exc}")

    pricing = quote_data.get("pricing", {})
    ref_no = quote_data.get("reference_number", "BHC-Quotation")
    client = quote_data.get("client", {})
    to_email = (body.to_email or "").strip()

    message = EmailMessage()
    message["To"] = to_email
    message["Subject"] = f"Quotation {ref_no} - {body.client_name}"
    message["X-Unsent"] = "1"

    area_display = str(client.get("Area_sqft") or pricing.get("area_sqft") or "-")
    message.set_content(
        "\n".join(
            [
                f"Dear {body.client_name},",
                "",
                "Please find attached the quotation for Building Health Check service.",
                f"Reference: {ref_no}",
                f"Property Type: {pricing.get('property_type', '-')}",
                f"Area: {area_display}",
                f"Quoted Amount: Rs. {float(pricing.get('final_cost', 0) or 0):,.2f}",
                "",
                "Please review and let us know if any clarifications are required.",
                "",
                "Regards,",
                "TUV Rheinland",
            ]
        )
    )

    attachment_bytes = attachment_path.read_bytes()
    ctype, _ = guess_type(str(attachment_path))
    maintype, subtype = (ctype.split("/", 1) if ctype else ("application", "octet-stream"))
    message.add_attachment(
        attachment_bytes,
        maintype=maintype,
        subtype=subtype,
        filename=attachment_filename,
    )

    draft_filename = safe_filename(quote_data.get("reference_number", body.client_name), "eml")
    return StreamingResponse(
        io.BytesIO(message.as_bytes()),
        media_type="message/rfc822",
        headers={"Content-Disposition": f'attachment; filename="{draft_filename}"'},
    )




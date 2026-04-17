"""Workflow-domain helpers for the BHC quotation application."""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException

from backend.app.config import BHC_PROCESSED_DB_PATH, EXCEL_FILE_PATH
from backend.app.services.bhc_excel_reader import read_clients_from_excel
from backend.app.services.bhc_output_generator import format_quote_reference
from backend.app.services.bhc_pricing_engine import calculate_quote
from backend.app.services.bhc_workflow_db import (
    get_reference_number_by_key,
    init_db,
    next_quote_sequence_for_date,
    processed_lookup_by_key,
)
from backend.app.utils.paths import DATA_DIR, EXPORTS_DIR

DEFAULT_ENQUIRY_EXCEL_FILENAMES = (
    "Building Health Check – Inspection Request Form 1.xlsx",
    "Building Health Check - Inspection Request Form 1.xlsx",
    "Building Health Check – Inspection Request Form.xlsx",
    "Building Health Check - Inspection Request Form.xlsx",
)
LOCAL_ENQUIRY_EXCEL_PATH = DATA_DIR / "bhc_enquiries.xlsx"
PROCESSED_DB_PATH = Path(BHC_PROCESSED_DB_PATH) if BHC_PROCESSED_DB_PATH else (DATA_DIR / "bhc_processed.db")
BHC_EXPORT_DIR = EXPORTS_DIR / "bhc"

# Cache for network drive Excel candidates to avoid slow I/O on every request
_excel_candidates_cache: dict[str, Any] = {"candidates": None, "timestamp": 0.0}
_excel_data_cache: dict[str, Any] = {"clients": None, "timestamp": 0.0}
_CACHE_TTL_SECONDS = 120  # re-scan every 2 minutes

ALLOWED_PAYMENTS_BY_STATUS = {
    "quoted": {"pending"},
    "converted": {"pending", "paid"},
    "dropped": {"pending"},
}


def initialize_workflow_storage() -> None:
    """Ensure workflow storage is available before serving requests."""
    init_db(PROCESSED_DB_PATH)


def _one_drive_roots() -> list[Path]:
    roots: list[Path] = []

    for env_name in ("OneDriveCommercial", "OneDriveConsumer", "OneDrive"):
        env_value = os.environ.get(env_name, "").strip()
        if env_value:
            candidate = Path(env_value)
            if candidate not in roots:
                roots.append(candidate)

    home_dir = Path.home()
    if home_dir.exists():
        for candidate in home_dir.glob("OneDrive*"):
            if candidate.is_dir() and candidate not in roots:
                roots.append(candidate)

    return roots


def _default_excel_candidates() -> list[Path]:
    candidates: list[Path] = []
    configured_excel_path = os.environ.get("EXCEL_FILE_PATH", EXCEL_FILE_PATH).strip()

    if configured_excel_path:
        configured = Path(configured_excel_path)
        if configured.is_dir():
            # If configured path is a directory, scan it for known filenames first
            for filename in DEFAULT_ENQUIRY_EXCEL_FILENAMES:
                candidate = configured / filename
                if candidate not in candidates:
                    candidates.append(candidate)
            # Then add any other .xlsx files in the directory
            if configured.exists():
                for xlsx_file in sorted(configured.glob("*.xlsx")):
                    if xlsx_file not in candidates:
                        candidates.append(xlsx_file)
        else:
            candidates.append(configured)
        # When an explicit path is configured, do not fall back to OneDrive or local
        return candidates

    for root in _one_drive_roots():
        for filename in DEFAULT_ENQUIRY_EXCEL_FILENAMES:
            candidate = root / filename
            if candidate not in candidates:
                candidates.append(candidate)

    for filename in DEFAULT_ENQUIRY_EXCEL_FILENAMES:
        for root in _one_drive_roots():
            for candidate in root.rglob(filename):
                if candidate not in candidates:
                    candidates.append(candidate)

    if LOCAL_ENQUIRY_EXCEL_PATH not in candidates:
        candidates.append(LOCAL_ENQUIRY_EXCEL_PATH)

    return candidates


def get_active_excel_path_or_none() -> Optional[Path]:
    """Return the first available enquiry workbook candidate (cached)."""
    now = time.monotonic()
    cache = _excel_candidates_cache
    if cache["candidates"] is not None and (now - cache["timestamp"]) < _CACHE_TTL_SECONDS:
        return cache["candidates"][0] if cache["candidates"] else None

    result: list[Path] = []
    for candidate in _default_excel_candidates():
        if candidate.exists():
            result.append(candidate)
    cache["candidates"] = result
    cache["timestamp"] = now
    return result[0] if result else None


def get_excel_read_candidates() -> list[Path]:
    """Return existing Excel sources in priority order (cached)."""
    # Trigger cache population
    get_active_excel_path_or_none()
    return list(_excel_candidates_cache.get("candidates") or [])


def digits(phone: str) -> str:
    return "".join(character for character in str(phone or "") if character.isdigit())


def normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def client_enquiry_key(client: dict[str, Any], row_index: int) -> str:
    phone_key = digits(client.get("Phone_Number", ""))
    name_key = normalize_text(client.get("Client_Name", ""))
    timestamp_key = normalize_text(client.get("Timestamp", ""))

    if phone_key and timestamp_key:
        return f"phone_ts:{phone_key}|{timestamp_key}"
    if name_key and timestamp_key:
        return f"name_ts:{name_key}|{timestamp_key}"
    if phone_key:
        return f"phone:{phone_key}"

    return f"row:{row_index}"


def legacy_phone_enquiry_key(client: dict[str, Any]) -> str:
    """Backward-compatible key used by older processed rows."""
    phone_key = digits(client.get("phone", ""))
    if phone_key:
        return f"phone:{phone_key}"
    return ""


def read_workflow_clients(*, force_refresh: bool = False) -> list[dict[str, Any]]:
    """Read and normalize enquiry rows consumed by API endpoints (cached)."""
    now = time.monotonic()
    cache = _excel_data_cache
    if not force_refresh and cache["clients"] is not None and (now - cache["timestamp"]) < _CACHE_TTL_SECONDS:
        return cache["clients"]

    candidates = get_excel_read_candidates()
    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=(
                "No enquiry Excel file found. Sync the shared Microsoft Forms workbook in OneDrive, "
                "set EXCEL_FILE_PATH in .env, or place 'bhc_enquiries.xlsx' in the data folder."
            ),
        )

    raw_clients: list[dict[str, Any]] | None = None
    permission_errors: list[str] = []

    for excel_path in candidates:
        try:
            raw_clients = read_clients_from_excel(excel_path)
            break
        except PermissionError as exc:
            permission_errors.append(f"{excel_path}: {exc}")
            continue
        except Exception as exc:  # pragma: no cover - defensive route boundary
            raise HTTPException(status_code=500, detail=f"Failed to read Excel: {exc}") from exc

    if raw_clients is None:
        detail = "Failed to read Excel due to file permission issue."
        if permission_errors:
            detail = f"{detail} Tried: {' | '.join(permission_errors)}"
        raise HTTPException(status_code=503, detail=detail)

    clients: list[dict[str, Any]] = []
    for row_index, client in enumerate(raw_clients):
        clients.append(
            {
                "name": client.get("Client_Name", ""),
                "phone": client.get("Phone_Number", ""),
                "email": client.get("Client_Email", ""),
                "location": client.get("Location", ""),
                "property_type": client.get("Property_Type", ""),
                "building_system": client.get("Building_System", ""),
                "area_sqft": client.get("Area_sqft", ""),
                "area_numeric": float(client.get("_area_numeric", 0) or 0),
                "issue_observed": client.get("Issue_Observed", ""),
                "building_age": client.get("Building_Age", ""),
                "urgency": client.get("Urgency", ""),
                "gst_number": client.get("GST_Number", ""),
                "pan_number": client.get("PAN_Number", ""),
                "notes": client.get("Notes", ""),
                "timestamp": client.get("Timestamp", ""),
                "enquiry_key": client_enquiry_key(client, row_index),
            }
        )
    cache["clients"] = clients
    cache["timestamp"] = time.monotonic()
    return clients


def find_client(name: str, phone: Optional[str], timestamp: Optional[str]) -> dict[str, Any]:
    """Find an enquiry row using stable matching priority: phone -> timestamp -> name."""
    clients = read_workflow_clients()
    phone_digits = digits(phone or "")
    timestamp_key = normalize_text(timestamp or "")
    name_key = normalize_text(name)

    if phone_digits:
        for client in clients:
            if normalize_text(client["name"]) == name_key and digits(client["phone"]) == phone_digits:
                return client

    if timestamp_key:
        for client in clients:
            if normalize_text(client["name"]) == name_key and normalize_text(client["timestamp"]) == timestamp_key:
                return client

    for client in clients:
        if normalize_text(client["name"]) == name_key:
            return client

    raise HTTPException(status_code=404, detail=f"Client '{name}' not found in enquiries.")


def _detect_urgency(urgency_value: str) -> bool:
    """Detect if the enquiry is marked as urgent based on form response."""
    text = str(urgency_value or "").strip().lower()
    if not text:
        return False
    urgent_keywords = [
        "urgent", "immediately", "asap", "as soon as possible",
        "within a week", "within 1 week", "emergency", "critical",
        "high priority", "rush",
    ]
    return any(keyword in text for keyword in urgent_keywords)


def build_quote_data(
    client_name: str,
    override_final_price: Optional[float],
    reference_number: Optional[str],
    building_system: Optional[str] = None,
    building_age: Optional[str] = None,
    phone: Optional[str] = None,
    timestamp: Optional[str] = None,
    property_type: Optional[str] = None,
    area_sqft: Optional[float] = None,
    discount_percent: Optional[float] = None,
) -> dict[str, Any]:
    client_row = find_client(client_name, phone=phone, timestamp=timestamp)
    generated_at = datetime.now()

    area_value = float(area_sqft if area_sqft is not None else client_row.get("area_numeric", 0.0))
    property_value = (property_type or client_row.get("property_type") or "Residential").strip() or "Residential"
    building_system_value = (building_system or client_row.get("building_system") or "").strip()
    building_age_value = (building_age or client_row.get("building_age") or "").strip()

    client_payload = {
        "Client_Name": client_row.get("name", ""),
        "Phone_Number": client_row.get("phone", ""),
        "Location": client_row.get("location", ""),
        "Property_Type": property_value,
        "Building_System": building_system_value,
        "Area_sqft": str(client_row.get("area_sqft", "")),
        "Issue_Observed": client_row.get("issue_observed", ""),
        "Building_Age": building_age_value,
        "Urgency": client_row.get("urgency", ""),
        "Notes": client_row.get("notes", ""),
        "Timestamp": client_row.get("timestamp", ""),
        "_area_numeric": area_value,
    }

    is_urgent = _detect_urgency(client_row.get("urgency", ""))

    pricing = calculate_quote(
        property_type=property_value,
        area_sqft=area_value,
        override_final_price=override_final_price,
        client_context=client_payload,
        building_age=building_age_value,
        is_urgent=is_urgent,
    )

    discount_pct = max(0.0, float(discount_percent or 0.0))
    if discount_pct > 100.0:
        discount_pct = 100.0

    quoted_price = float(pricing.get("quoted_price", pricing.get("base_cost", 0.0)) or 0.0)
    discount_amount = 0.0

    if override_final_price is None and discount_pct > 0.0:
        discount_amount = round((quoted_price * discount_pct) / 100.0, 2)
        pricing["final_cost"] = round(max(0.0, quoted_price - discount_amount), 2)

    pricing["discount_percent"] = round(discount_pct, 2)
    pricing["discount_amount"] = round(discount_amount, 2)

    # Recalculate GST on the actual final_cost (after discount/override)
    gst_pct = float(pricing.get("gst_percent", 18.0))
    final = float(pricing.get("final_cost", 0.0))
    pricing["gst_amount"] = round(final * gst_pct / 100.0, 2)
    pricing["total_with_gst"] = round(final + pricing["gst_amount"], 2)

    enquiry_key = client_row.get("enquiry_key", "")
    existing_reference_number = get_reference_number_by_key(PROCESSED_DB_PATH, enquiry_key)
    resolved_reference_number = reference_number or existing_reference_number
    if not resolved_reference_number:
        next_sequence = next_quote_sequence_for_date(PROCESSED_DB_PATH, generated_at.strftime("%Y-%m-%d"))
        resolved_reference_number = format_quote_reference(next_sequence, generated_at)

    return {
        "client": client_payload,
        "pricing": pricing,
        "reference_number": resolved_reference_number,
        "generated_at": generated_at.isoformat(),
        "enquiry_key": enquiry_key,
    }


def list_pending_clients() -> list[dict[str, Any]]:
    """Exclude rows already persisted to processed workflow storage."""
    excel_clients = read_workflow_clients()
    processed_by_enquiry_key = processed_lookup_by_key(PROCESSED_DB_PATH)
    pending_clients: list[dict[str, Any]] = []
    for client in excel_clients:
        current_key = client.get("enquiry_key")
        legacy_key = legacy_phone_enquiry_key(client)
        if current_key in processed_by_enquiry_key:
            continue
        if legacy_key and legacy_key in processed_by_enquiry_key:
            continue
        pending_clients.append(client)
    return pending_clients


def safe_filename(file_stem: str, extension: str) -> str:
    safe_name = "".join(character if character.isalnum() or character in "_-" else "_" for character in str(file_stem or "Quotation"))
    return f"{safe_name.strip() or 'Quotation'}.{extension}"


def validate_status_payment_combination(status: str, payment_status: str) -> None:
    normalized_status = str(status or "").strip().lower()
    normalized_payment_status = str(payment_status or "").strip().lower()
    allowed_payment_statuses = ALLOWED_PAYMENTS_BY_STATUS.get(normalized_status)

    if allowed_payment_statuses is None:
        return

    if normalized_payment_status not in allowed_payment_statuses:
        allowed_text = ", ".join(sorted(option.title() for option in allowed_payment_statuses))
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid update: payment status '{normalized_payment_status.title()}' is not allowed "
                f"for status '{normalized_status.title()}'. Allowed: {allowed_text}."
            ),
        )
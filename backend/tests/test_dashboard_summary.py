from pathlib import Path

from datetime import datetime

from backend.app.services.bhc_output_generator import format_quote_reference
from backend.app.services.bhc_workflow_db import (
    dashboard_summary,
    get_reference_number_by_key,
    init_db,
    next_quote_sequence_for_date,
    upsert_processed_client,
)


def _make_record(enquiry_id: str, enquiry_key: str, amount: float, status: str, payment: str):
    return {
        "enquiry_id": enquiry_id,
        "enquiry_key": enquiry_key,
        "client_name": f"Client-{enquiry_id}",
        "phone": "9999999999",
        "property_type": "Commercial",
        "area": 10000,
        "quoted_amount": amount,
        "quote_generated_date": "2026-03-27 10:00:00",
        "status": status,
        "payment_status": payment,
        "remarks": "",
        "timestamp": "2026-03-27T10:00:00",
    }


def test_dashboard_summary_computes_quoted_and_converted_revenue(tmp_path):
    db_path = Path(tmp_path) / "test_bhc.db"
    init_db(db_path)

    upsert_processed_client(db_path, _make_record("1", "k1", 100000, "Converted", "Paid"))
    upsert_processed_client(db_path, _make_record("2", "k2", 50000, "Converted", "Pending"))
    upsert_processed_client(db_path, _make_record("3", "k3", 20000, "Quoted", "Pending"))
    upsert_processed_client(db_path, _make_record("4", "k4", 15000, "Dropped", "Pending"))

    summary = dashboard_summary(db_path, total_enquiries=10, pending=6)

    assert summary["total_enquiries"] == 10
    assert summary["pending"] == 6
    assert summary["quoted"] == 4
    assert summary["converted"] == 2
    assert summary["quoted_revenue"] == 185000.0
    assert summary["converted_revenue"] == 100000.0
    assert summary["revenue"] == summary["quoted_revenue"]


def test_quote_reference_numbers_use_daily_sequence_and_persist(tmp_path):
    db_path = Path(tmp_path) / "test_bhc.db"
    init_db(db_path)

    assert format_quote_reference(1, datetime(2026, 4, 1, 9, 30, 0)) == "BEN-HC-TUVR-20260401-0001"
    assert next_quote_sequence_for_date(db_path, "2026-04-01") == 1

    upsert_processed_client(
        db_path,
        {
            **_make_record("1", "k1", 100000, "Quoted", "Pending"),
            "reference_number": "BEN-HC-TUVR-20260401-0001",
            "quote_generated_date": "2026-04-01T09:30:00",
        },
    )

    assert get_reference_number_by_key(db_path, "k1") == "BEN-HC-TUVR-20260401-0001"
    assert next_quote_sequence_for_date(db_path, "2026-04-01") == 2
    assert next_quote_sequence_for_date(db_path, "2026-04-02") == 1

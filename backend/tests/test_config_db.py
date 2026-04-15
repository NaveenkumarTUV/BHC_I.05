from pathlib import Path

from backend.app.services.bhc_config_db import (
    get_company_settings,
    get_document_settings,
    init_config_db,
    list_pricing_slabs,
    replace_pricing_slabs,
    update_company_settings,
    update_document_settings,
)


def test_config_db_initializes_defaults(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))

    init_config_db(db_path)

    company = get_company_settings()
    document = get_document_settings()
    slabs = list_pricing_slabs()

    assert company["company_name"]
    assert company["contact_name"]
    assert document["payment_terms"]
    assert document["system_generated_note"]
    assert len(slabs) >= 1


def test_config_db_updates_company_document_and_pricing(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)

    company = update_company_settings(
        {
            "company_name": "Shared Config Company",
            "company_subtitle": "Civil Services",
            "company_address": "Bengaluru",
            "company_phone": "+91 9000000000",
            "company_email": "admin@example.com",
            "contact_name": "Admin User",
        }
    )
    document = update_document_settings(
        {
            "company_profile_paragraphs": ["Paragraph one"],
            "tuv_history_paragraphs": ["History one"],
            "service_capabilities": ["Capability one"],
            "payment_terms": ["Payment one"],
            "deliverables": ["Deliverable one"],
            "other_terms": ["Term one"],
            "system_generated_note": "System note",
        }
    )
    slabs = replace_pricing_slabs(
        [
            {"min_area": 0, "max_area": 500, "label": "0 - 500 sq.ft", "quoted_price": 5000.0},
            {"min_area": 501, "max_area": 2000, "label": "501 - 2,000 sq.ft", "quoted_price": 15000.0},
        ]
    )

    assert company["company_name"] == "Shared Config Company"
    assert document["system_generated_note"] == "System note"
    assert slabs[0]["quoted_price"] == 5000.0
from pathlib import Path

from backend.app.services.bhc_config_db import init_config_db, replace_pricing_slabs
from backend.app.services.bhc_pricing_engine import calculate_quote


def test_pricing_engine_reads_shared_sqlite_slabs(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)
    replace_pricing_slabs(
        [
            {"min_area": 0, "max_area": 1000, "label": "0 - 1,000 sq.ft", "quoted_price": 11111.0},
            {"min_area": 1001, "max_area": 3000, "label": "1,001 - 3,000 sq.ft", "quoted_price": 22222.0},
        ]
    )

    result = calculate_quote(property_type="Commercial", area_sqft=750)

    assert result["quoted_price"] == 11111.0
    assert result["area_slab"] == "0 - 1,000 sq.ft"


def test_area_slab_pricing_boundaries(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)

    first = calculate_quote(property_type="Commercial", area_sqft=2000)
    second = calculate_quote(property_type="Commercial", area_sqft=2001)
    third = calculate_quote(property_type="Commercial", area_sqft=25000)

    assert first["quoted_price"] == 10000.0
    assert first["area_slab"] == "0 - 2,000 sq.ft"

    assert second["quoted_price"] == 25000.0
    assert second["area_slab"] == "2,001 - 5,000 sq.ft"

    assert third["quoted_price"] == 100000.0
    assert third["area_slab"] == "10,001 - 25,000 sq.ft"


def test_override_final_price_wins_over_slab_price(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)

    result = calculate_quote(
        property_type="Commercial",
        area_sqft=50000,
        override_final_price=123456.78,
    )

    assert result["quoted_price"] == 200000.0
    assert result["final_cost"] == 123456.78
    assert result["is_price_overridden"] is True


def test_explicit_rcc_selection_uses_visual_rcc_scope(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)

    result = calculate_quote(
        property_type="Commercial",
        area_sqft=3000,
        client_context={"Building_System": "RCC"},
    )

    assert result["structure_type"] == "RCC"
    assert "visual assessment" in " ".join(result["scope_of_work"]).lower()


def test_explicit_steel_selection_uses_steel_scope(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)

    result = calculate_quote(
        property_type="Commercial",
        area_sqft=3000,
        client_context={"Building_System": "Steel"},
    )

    assert result["structure_type"] == "Structural Steel"
    assert any("weld" in item.lower() for item in result["scope_of_work"])


def test_explicit_both_selection_uses_combined_scope(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)

    result = calculate_quote(
        property_type="Commercial",
        area_sqft=3000,
        client_context={"Building_System": "Both"},
    )

    assert result["structure_type"] == "RCC + Structural Steel"
    assert any("rcc components" in item.lower() for item in result["scope_of_work"])
    assert any("peb" in item.lower() for item in result["scope_of_work"])
    assert any("weld" in item.lower() for item in result["scope_of_work"])

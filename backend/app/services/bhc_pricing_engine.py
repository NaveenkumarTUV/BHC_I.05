"""Pricing engine for Building Health Checkup service."""

import re
from typing import Dict, Any, Optional, List

from backend.app.services.bhc_config_db import (
    list_pricing_slabs,
    list_scope_of_work_items,
    list_support_document_items,
    get_urgency_surcharge_percent,
    get_gst_percent,
    SLAB_CATEGORY_STANDARD,
    SLAB_CATEGORY_NEW_BUILDING,
)

RCC_SERVICE_NAME = "Building Health Checkup - RCC Buildings"
STEEL_SERVICE_NAME = "Building Health Checkup - PEB Steel Structure with RCC Pedestals"
BOTH_SERVICE_NAME = "Building Health Checkup - Combined Structure (RCC + PEB Steel Structure)"

RCC_SCOPE_OF_WORK = [
    "The visual inspection includes assessment of all accessible structural components, such as columns, beams, slabs and visible flooring areas, wherein reinforced concrete members are assessed for cracks, corrosion, spalling and reinforcement exposure, while slabs are further assessed for leakage, dampness, deflection and any exposed reinforcement.",
    "Walls will be assessed for cracks, dampness, peeling or deterioration of paint and other visible signs of distress.",
    "Kitchen, Washroom, Toilet, Bathroom, Utility, Lobby and Balcony areas will be inspected to identify any signs of leakage, dampness or related issues.",
    "The terrace and roof areas, along with staircases and rainwater down pipes, will be inspected for waterproofing condition, water stagnation, drainage issues, leakage, cracks and vegetation growth.",
    "Doors and windows will be inspected for their condition, alignment, and any visible defects or damage.",
    "Electrical switches, sockets along with plumbing & fittings will be assessed for their overall condition and any visible defects.",
    "All observed defects and distress conditions will be systematically recorded with supporting photographic evidence and concise technical descriptions.",
    "The inspection is limited to visual assessment only.",
]

BOTH_SCOPE_OF_WORK = [
    "The visual inspection includes assessment of all accessible RCC components such as columns, beams, slabs and flooring areas. RC members will be assessed for cracks, spalling, corrosion and reinforcement exposure, while slabs will also be checked for leakage, dampness, deflection and exposed reinforcement.",
    "All accessible primary and secondary steel members, including columns, rafters, beams, purlins and girts, will be inspected for corrosion, rusting, coating deterioration, deformation, bending, misalignment and condition of bolts and connections.",
    "The roof system (RCC slab or metal roofing), including waterproofing, metal sheets, insulation (if accessible) and skylights, will be inspected for leakage, water ingress, dampness, cracks, sheet damage, dents and corrosion.",
    "Wall systems, including masonry walls and PEB cladding panels, will be assessed for cracks, dampness, peeling paint, corrosion, physical damage, joint gaps, sealant deterioration and leakage points.",
    "All bracing systems (steel bracing), bolted and welded connections will be inspected for corrosion, damage, missing members, tightness of fasteners and weld defects.",
    "The interface between steel structures and RCC foundations/pedestals will be checked for anchor bolt condition, looseness, corrosion, cracks in concrete, and signs of settlement or misalignment.",
    "Doors, windows, shutters, louvers, and ventilators will be inspected for alignment, operability, and damage. Electrical switches, sockets, plumbing systems and fittings will be visually assessed for condition and defects.",
    "Mezzanine floors, crane supporting structures (if applicable) and protective coatings (paint/galvanization) will be checked for structural distress, corrosion, and deterioration.",
    "All observed defects and distress conditions shall be documented with photographs and brief descriptions.",
    "The inspection is limited to visual assessment only.",
]

STEEL_SCOPE_OF_WORK = [
    "The visual inspection includes assessment of all accessible primary and secondary steel members for corrosion, rusting, coating deterioration, deformation, bending, misalignment and condition of bolts and connections.",
    "The roof system, including metal sheets, insulation (if accessible), and skylights, will be inspected for leakage, water ingress, dampness, sheet damage, dents and corrosion.",
    "Wall cladding panels will be assessed for corrosion, dents, physical damage, joint gaps, sealant deterioration and potential leakage points.",
    "All bracing systems and connections, portal bracing, along with bolted and welded joints, will be inspected for corrosion, damage, missing members, fastener condition, tightness and weld defects.",
    "The interface between the steel structure and foundation will be inspected for anchor bolt condition, looseness, corrosion, cracks in pedestal concrete and signs of settlement or base plate misalignment.",
    "Building components such as doors, shutters, windows, ventilators, drainage systems, mezzanine/crane structures and protective coatings will be inspected for alignment, operability, damage, leakage, structural distress and coating deterioration.",
    "All observed defects and distress conditions shall be documented with photographs and brief descriptions.",
    "The inspection is limited to visual assessment only.",
]

RCC_SUPPORT_DOCUMENTS_REQUIRED = [
    "The client shall provide all available building documents, including architectural, structural, and service drawings, and shall grant access to all accessible areas of the building, including terraces, water tanks, basements, and service areas.",
    "The client shall ensure safe access arrangements for inspection, including provision of ladders, scaffolding, or suitable lifting equipment wherever required, and shall grant permission for photographic documentation and recording of observed defects.",
    "The client shall nominate an authorized representative to accompany the inspection team during the site visit and facilitate coordination during the inspection process.",
]

BOTH_SUPPORT_DOCUMENTS_REQUIRED = [
    "The client shall provide available architectural and structural drawings for both RCC and PEB portions, including general arrangement and connection details.",
    "The client shall provide access to all areas of the building including terrace, roof, intermediate floors and service areas.",
    "Safe access arrangements such as ladders, scaffolding, walkways or man-lifts shall be arranged by the client for inspection at height.",
    "Permission for photographic documentation and recording of observed defects shall be provided.",
    "The client shall nominate a responsible representative to coordinate and accompany the inspection team during the site visit.",
]

STEEL_SUPPORT_DOCUMENTS_REQUIRED = [
    "The client shall provide available structural drawings including PEB general arrangement drawings, fabrication drawings and anchor bolt layout details.",
    "The client shall provide access to all areas of the structure including roof, crane runway (if applicable) and peripheral zones.",
    "Safe access arrangements such as ladders, scaffolding, man-lifts or walkways shall be arranged by the client for inspection at height.",
    "Permission for photographic documentation and recording of defects shall be provided by the client.",
    "The client shall nominate a representative to accompany the inspection team during the site visit.",
]

SERVICE_NOTES = [
    "The scope shall be executed for the applicable building system as identified in the enquiry and site observations.",
    "Validity of this offer is 60 days from the date of issue.",
    "Goods and Services Tax (GST) will be charged extra as applicable.",
    "Site visit scheduling, safe access, and required permissions shall be arranged by the client.",
    "Any additional visits beyond the agreed site scope shall be charged separately on a man-day basis along with actual expenses.",
    "Findings will be documented in a written inspection report.",
]


def get_pricing_config(slab_category: str = SLAB_CATEGORY_STANDARD) -> List[Dict[str, float | int | str | None]]:
    """Return the pricing configuration list for the given category."""
    return list_pricing_slabs(slab_category)


def _find_slab(area_sqft: float, slab_category: str = SLAB_CATEGORY_STANDARD) -> Dict[str, float | int | str | None]:
    for slab in get_pricing_config(slab_category):
        min_area = float(slab["min_area"])
        max_area = float(slab["max_area"])
        if min_area <= area_sqft <= max_area:
            return slab
    raise ValueError(
        "No pricing slab configured for this built-up area. "
        "Please review the enquiry and update the pricing configuration."
    )


def _parse_area_range(area_value: Any) -> tuple[float, float] | None:
    """Parse ranges like '25,001-50,000 Sq.ft' and return (min, max)."""
    text = str(area_value or "").replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    lo = float(match.group(1))
    hi = float(match.group(2))
    return (lo, hi) if lo <= hi else (hi, lo)


def _find_slab_from_area_input(
    area_sqft: float,
    client_context: Optional[Dict[str, Any]],
    slab_category: str,
) -> tuple[Dict[str, float | int | str | None], float]:
    """
    Resolve slab by explicit area range text first (if provided), else numeric area.
    Returns (slab, numeric_area_for_reporting).
    """
    area_text = ""
    if client_context:
        area_text = str(client_context.get("Area_sqft", "") or "")

    parsed = _parse_area_range(area_text)
    if parsed:
        low, high = parsed
        for slab in get_pricing_config(slab_category):
            min_area = float(slab["min_area"])
            max_area = float(slab["max_area"])
            if min_area <= low and high <= max_area:
                return slab, low
        # Fallback if admin slab boundaries are slightly different.
        return _find_slab(low, slab_category), low

    numeric_area = float(area_sqft or 0)
    return _find_slab(numeric_area, slab_category), numeric_area


def _is_new_building_age(building_age: Optional[str]) -> bool:
    """Return True only for explicitly new buildings (not 1-5 year old buildings)."""
    age_key = str(building_age or "").strip().lower()
    if not age_key:
        return False

    # Business rule: 1-5 years should use existing/older building pricing slabs.
    if any(token in age_key for token in ("1-5", "1 to 5", "1–5", "1—5")):
        return False

    return any(token in age_key for token in ("new building", "completely new", "brand new", "new"))


def _infer_scope_type(property_type: str, client_context: Optional[Dict[str, Any]]) -> str:
    if client_context:
        explicit_system = str(client_context.get("Building_System", "") or "").strip().lower()
        explicit_has_rcc = any(token in explicit_system for token in {"rcc", "rc", "reinforced cement concrete", "reinforced concrete"})
        explicit_has_steel = any(token in explicit_system for token in {"steel", "structural steel", "steel building", "steel structure"})
        explicit_is_combined = any(token in explicit_system for token in {"both", "combined", "combined structure", "composite", "rcc + peb", "rcc+peb"})
        if explicit_is_combined or (explicit_has_rcc and explicit_has_steel):
            return "both"
        if explicit_system in {"rcc", "rc", "reinforced cement concrete", "reinforced concrete"}:
            return "rcc"
        if explicit_system in {"steel", "structural steel", "steel building", "steel structure"}:
            return "steel"

    haystack_parts = [property_type or ""]
    if client_context:
        haystack_parts.extend([
            str(client_context.get("Building_System", "") or ""),
            str(client_context.get("Property_Type", "") or ""),
            str(client_context.get("Issue_Observed", "") or ""),
            str(client_context.get("Notes", "") or ""),
        ])
    haystack = " ".join(haystack_parts).lower()
    steel_keywords = [
        "steel",
        "structural steel",
        "peb",
        "shed",
        "weld",
        "corrosion",
        "pitting",
        "paint",
    ]
    has_steel = any(keyword in haystack for keyword in steel_keywords)
    has_rcc = any(keyword in haystack for keyword in ["rcc", "rc", "reinforced concrete", "concrete"])
    has_combined = any(keyword in haystack for keyword in ["both", "combined", "combined structure", "composite", "rcc + peb", "rcc+peb"])
    if has_combined or (has_rcc and has_steel):
        return "both"
    return "steel" if has_steel else "rcc"


def calculate_quote(
    property_type: str,
    area_sqft: float,
    override_final_price: Optional[float] = None,
    client_context: Optional[Dict[str, Any]] = None,
    building_age: Optional[str] = None,
    is_urgent: bool = False,
) -> Dict[str, Any]:
    """
    Calculate a BHC quotation.

    Args:
        property_type: Preserved for reporting only; pricing is area-slab based.
        area_sqft: Built-up area in square feet.
        override_final_price: User-supplied final price override (optional).
        client_context: Optional enquiry fields used for scope inference.
        building_age: Optional building age label (used to select new vs existing slab).
        is_urgent: Whether the enquiry has urgency; applies surcharge.

    Returns:
        Dictionary with full pricing breakdown and service details.
    """
    scope_type = _infer_scope_type(property_type, client_context)

    # ── Determine if new building ────────────────────────────
    is_new_building = _is_new_building_age(building_age)

    # ── Select slab from the correct category ────────────────
    slab_category = SLAB_CATEGORY_NEW_BUILDING if is_new_building else SLAB_CATEGORY_STANDARD
    slab, resolved_area_sqft = _find_slab_from_area_input(area_sqft, client_context, slab_category)
    quoted_price = float(slab["quoted_price"])
    slab_label = str(slab["label"])

    # ── Apply urgency surcharge ──────────────────────────────
    urgency_surcharge_percent = 0.0
    urgency_surcharge_amount = 0.0
    if is_urgent and override_final_price is None:
        urgency_surcharge_percent = get_urgency_surcharge_percent()
        urgency_surcharge_amount = round(quoted_price * urgency_surcharge_percent / 100.0, 2)
        quoted_price = round(quoted_price + urgency_surcharge_amount, 2)

    # ── Load scope from DB, fallback to hardcoded ────────────
    if is_new_building:
        new_scope_key = f"new_{scope_type}"
        db_new_scopes = list_scope_of_work_items(new_scope_key)
        db_new_support = list_support_document_items(new_scope_key)
        # If new-building scope is configured, use it; else fall back to regular
        if db_new_scopes.get(new_scope_key):
            db_scopes = db_new_scopes
            db_support = db_new_support
            scope_lookup_key = new_scope_key
        else:
            db_scopes = list_scope_of_work_items(scope_type)
            db_support = list_support_document_items(scope_type)
            scope_lookup_key = scope_type
    else:
        db_scopes = list_scope_of_work_items(scope_type)
        db_support = list_support_document_items(scope_type)
        scope_lookup_key = scope_type

    if scope_type == "steel":
        service_name = STEEL_SERVICE_NAME
        scope_of_work = db_scopes.get(scope_lookup_key, STEEL_SCOPE_OF_WORK)
        structure_type = "Structural Steel"
        support_documents_required = db_support.get(scope_lookup_key, STEEL_SUPPORT_DOCUMENTS_REQUIRED)
    elif scope_type == "both":
        service_name = BOTH_SERVICE_NAME
        scope_of_work = db_scopes.get(scope_lookup_key, BOTH_SCOPE_OF_WORK)
        structure_type = "RCC + Structural Steel"
        support_documents_required = db_support.get(scope_lookup_key, BOTH_SUPPORT_DOCUMENTS_REQUIRED)
    else:
        service_name = RCC_SERVICE_NAME
        scope_of_work = db_scopes.get(scope_lookup_key, RCC_SCOPE_OF_WORK)
        structure_type = "RCC"
        support_documents_required = db_support.get(scope_lookup_key, RCC_SUPPORT_DOCUMENTS_REQUIRED)

    if override_final_price is not None and override_final_price > 0:
        final_cost = round(override_final_price, 2)
        is_overridden = True
    else:
        final_cost = round(quoted_price, 2)
        is_overridden = False

    # ── Calculate GST ────────────────────────────────────────
    gst_percent = get_gst_percent()
    gst_amount = round(final_cost * gst_percent / 100.0, 2)
    total_with_gst = round(final_cost + gst_amount, 2)

    return {
        "service_name":       service_name,
        "scope_of_work":      scope_of_work,
        "structure_type":     structure_type,
        "building_system":    client_context.get("Building_System", structure_type) if client_context else structure_type,
        "property_type":      property_type,
        "area_sqft":          resolved_area_sqft,
        "pricing_model":      "area_slab",
        "area_slab":          slab_label,
        "slab_min_area":      slab["min_area"],
        "slab_max_area":      slab["max_area"],
        "quoted_price":       round(quoted_price, 2),
        "base_cost":          round(quoted_price, 2),
        "computed_cost":      round(quoted_price, 2),
        "rate_per_sqft":      None,
        "min_price":          None,
        "min_price_applied":  False,
        "final_cost":         final_cost,
        "is_price_overridden": is_overridden,
        "building_age":       building_age or "",
        "is_urgent":          is_urgent,
        "urgency_surcharge_percent": urgency_surcharge_percent,
        "urgency_surcharge_amount": urgency_surcharge_amount,
        "gst_percent":        gst_percent,
        "gst_amount":         gst_amount,
        "total_with_gst":     total_with_gst,
        "support_documents_required": support_documents_required,
        "notes":              SERVICE_NOTES,
    }

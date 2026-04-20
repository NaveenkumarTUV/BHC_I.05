from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.app.config import BHC_CONFIG_DB_PATH
from backend.app.utils.paths import DATA_DIR

ALLOWED_EMAIL_DOMAIN = "@ind.tuv.com"
DEFAULT_ADMIN_EMAIL = "m.naveenkumar@ind.tuv.com"
DEFAULT_ADMIN_NAME = "Naveen kumar"
DEFAULT_ADMIN_DESIGNATION = "AI Solution Architect"
PASSWORD_HASH_ITERATIONS = 200000
SESSION_DURATION_HOURS = 8
CONFIG_SCHEMA_VERSION = "7"

SLAB_CATEGORY_STANDARD = "standard"
SLAB_CATEGORY_NEW_BUILDING = "new_building"

DEFAULT_PRICING_SLABS: list[dict[str, float | int | str]] = [
    {"min_area": 0, "max_area": 2000, "label": "0 - 2,000 sq.ft", "quoted_price": 10000.0},
    {"min_area": 2001, "max_area": 5000, "label": "2,001 - 5,000 sq.ft", "quoted_price": 25000.0},
    {"min_area": 5001, "max_area": 10000, "label": "5,001 - 10,000 sq.ft", "quoted_price": 50000.0},
    {"min_area": 10001, "max_area": 25000, "label": "10,001 - 25,000 sq.ft", "quoted_price": 100000.0},
    {"min_area": 25001, "max_area": 50000, "label": "25,001 - 50,000 sq.ft", "quoted_price": 200000.0},
    {"min_area": 50001, "max_area": 100000, "label": "50,001 - 100,000 sq.ft", "quoted_price": 250000.0},
    {"min_area": 100001, "max_area": 500000, "label": "100,001 - 500,000 sq.ft", "quoted_price": 350000.0},
]

DEFAULT_NEW_BUILDING_PRICING_SLABS: list[dict[str, float | int | str]] = [
    {"min_area": 0, "max_area": 2000, "label": "0 - 2,000 sq.ft", "quoted_price": 8000.0},
    {"min_area": 2001, "max_area": 5000, "label": "2,001 - 5,000 sq.ft", "quoted_price": 20000.0},
    {"min_area": 5001, "max_area": 10000, "label": "5,001 - 10,000 sq.ft", "quoted_price": 40000.0},
    {"min_area": 10001, "max_area": 25000, "label": "10,001 - 25,000 sq.ft", "quoted_price": 80000.0},
    {"min_area": 25001, "max_area": 50000, "label": "25,001 - 50,000 sq.ft", "quoted_price": 160000.0},
    {"min_area": 50001, "max_area": 100000, "label": "50,001 - 100,000 sq.ft", "quoted_price": 200000.0},
    {"min_area": 100001, "max_area": 500000, "label": "100,001 - 500,000 sq.ft", "quoted_price": 280000.0},
]

DEFAULT_COMPANY_SETTINGS: dict[str, str] = {
    "company_name": "TUV Rheinland (India) Private Limited",
    "company_subtitle": "Building Inspection & Civil Engineering Services",
    "company_address": "TUV Rheinland (India) Private Limited, 17/B, Industrial Area, Electronic City II Phase, Bengaluru, Karnataka 560100",
    "company_phone": "+91 9108476522",
    "company_email": "Thulasi.Prasad@ind.tuv.com",
    "contact_name": "Thulasi Prasad",
    "urgency_surcharge_percent": "10",
    "gst_percent": "18",
}

DEFAULT_DOCUMENT_SETTINGS: dict[str, Any] = {
    "company_profile_paragraphs": [
        "TUV Rheinland India Pvt. Ltd. has been established in India since 1996 as a subsidiary of the TUV Rheinland Group, Germany. As part of the India, Middle East, Africa and Asia Pacific group, the organisation supports both Indian and global markets across technical advisory, testing, inspection and certification mandates.",
        "Our Consultancy and Project Management business supports clients across technical due diligence, feasibility studies, bid process management, design review, project monitoring, construction supervision, safety management, quality management, lender's engineering services, and third-party inspection assignments.",
        "Our civil and structural engineering teams support condition assessment, structural soundness studies, restoration strategy development, and rehabilitation advisory assignments for industrial, commercial, and residential assets.",
    ],
    "tuv_history_paragraphs": [
        "TUV Rheinland stands for safety and quality in virtually all areas of business and life. Founded more than 150 years ago, the organisation has evolved from the early steam boiler monitoring associations in Germany into a global independent testing and inspection service provider.",
        "The organisation's development has always been driven by one core principle: technology must benefit people, not harm them. This principle continues to guide modern activities ranging from product testing and industrial inspections to project advisory, infrastructure assessment and management system certification.",
        "With a worldwide network of specialists, TUV Rheinland supports innovation, quality assurance and safety in industrial assets, buildings, plants and infrastructure systems. The organisation combines field investigation, engineering evaluation, compliance awareness and reporting discipline in technically demanding assignments.",
        "The company has expanded its international footprint steadily over the decades and today serves clients across sectors through multi-disciplinary technical teams. The Indian operations are integrated into this global framework while maintaining strong execution capability for local site-based assignments.",
    ],
    "service_capabilities": [
        "Technical due diligence and feasibility studies",
        "Structural stability and condition assessment",
        "Project monitoring and construction supervision",
        "Safety management and quality management",
        "Testing, inspection, certification and training support",
    ],
    "payment_terms": [
        "Advance payment, if applicable as per the agreed PO or LOA terms, shall be released against invoice submission after award.",
        "Balance payments shall be released within 15 days upon submission of invoices against the agreed milestones.",
        "GST and statutory levies shall be payable extra as applicable.",
    ],
    "deliverables": [
        "Detailed visual inspection report along with overall building condition and identified defects with severity.",
    ],
    "other_terms": [
        "Client will pay GST and other statutory charges extra as per government rules.",
        "If any additional visit to the client office or site beyond the agreed scope is required, the same shall be charged on a man-day basis along with travel, boarding, lodging and out-of-pocket expenses at actuals plus handling charges wherever applicable.",
        "Safe access to the proposed plant or building location and all necessary permissions for carrying out the program shall be arranged by the client.",
        "Any extension in scope shall be mutually agreed either on a man-day basis or lump-sum basis before execution.",
        "General terms and conditions of business, if issued with the proposal, shall form an integral part of the final contract.",
    ],
    "system_generated_note": "Note: This is a system-generated quotation and does not require a signature.",
}

# ── Default quotation sections (ordered, all configurable) ───────────────
# content_type: "dynamic" = rendered by code, "list" = numbered bullet list,
#               "paragraph" = multi-paragraph text, "table" = table rows (JSON)
# is_system: True = cannot be deleted (only hidden), False = user-created
DEFAULT_QUOTATION_SECTIONS: list[dict[str, Any]] = [
    {
        "section_key": "scope_of_work",
        "heading": "Scope of Work",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "notes_exclusions",
        "heading": "Notes / Exclusions",
        "content_type": "paragraph",
        "content_json": '["Statutory / Regulatory inspections / COC certifications are not considered as part of scope. The inspection is limited to visual assessment only."]',
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deliverables",
        "heading": "Deliverables",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "timeline",
        "heading": "Proposed Timeline",
        "content_type": "table",
        "content_json": '[{"sr_no":"1","task":"Field Visit","duration":"1-2 days after all arrangements are made prior to field visit"},{"sr_no":"2","task":"Submission of Report","duration":"2-3 days after completing site testing"}]',
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "fees",
        "heading": "Fees",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "basis_of_fees",
        "heading": "Basis of fees",
        "content_type": "list",
        "content_json": '["All fees above are inclusive of GST as applicable.","The above rates are applicable for Building Health Checkup / Inspection services.","Above fees are lump-sum inclusive of inspection, mobilization-demobilization and local transport considering 8 hours of working on a normal working day.","Additional hours will be charged at 1.5 times of normal man-day rates. For Saturdays, Sundays, Public Holidays and Night Shifts, charges shall be 1.5 times the normal man-day rates.","In the event a visit is cancelled within 24-48 hours prior to the scheduled visit or for any abortive visit not attributable to TUV-R, applicable man-day rates shall be charged.","At least 02-03 working days notification shall be provided to arrange inspection."]',
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "support_documents",
        "heading": "Support Documents / Arrangements Required from Client",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "methodology",
        "heading": "Proposed Methodology",
        "content_type": "list",
        "content_json": '["TUV Rheinland (India) Private Limited will appoint a Project Coordinator, who shall be the single point of contact for the entire assignment for general coordination.","The client will provide an inspection call with a minimum of three (03) working days notice to our coordinator along with all required technical documentation.","Our coordinator shall arrange the inspection and confirm with the client regarding the visit details.","Our inspector will carry out the inspection as per the technical documentation provided by the client and submit observations to our coordinator.","Our coordinator shall review the report and then submit it to the client with necessary supporting documentation.","Reports shall be submitted within 24-48 working hours after completion of the inspection.","Our coordinator will raise the invoice after submission of reports.","The client shall ensure the Health and Safety of TUV Rheinland personnel while working at their facility by providing a safe working environment."]',
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "payment_terms",
        "heading": "Payment Terms",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "terms_conditions",
        "heading": "Terms & Conditions",
        "content_type": "paragraph",
        "content_json": '["General terms and conditions of Business attached herewith, shall be an integral part. The Terms & Conditions contained in this Quotation shall supersede all other Contractual obligations entered between the Parties and shall be deemed as final and binding on the Parties. Both TUV-R and the Customer/Client shall sign out the Quotation as a confirmation of their Business Understanding and its acceptability to one another."]',
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "other_terms",
        "heading": "Additional Terms",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "validity",
        "heading": "Validity",
        "content_type": "paragraph",
        "content_json": '["Our proposal is valid for 60 days from the date of submission. The rates shall be firm for 01 MONTH from the date of acceptance of proposal or signing the contract.","We trust you will find the above offer competitive and look forward to be associated with you. In case you need any further clarifications or discussions, please contact us. We will be pleased to furnish the same promptly. Our other General Terms and Conditions are attached herewith."]',
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "acknowledgement",
        "heading": "Acknowledgement / Order Acceptance",
        "content_type": "paragraph",
        "content_json": '["The quotation is hereby acknowledged and accepted by the Client."]',
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "about_us",
        "heading": "About Us",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
]

DEFAULT_DEQ_SECTIONS: list[dict[str, Any]] = [
    {
        "section_key": "deq_scope",
        "heading": "Scope of Detailed Examination",
        "content_type": "list",
        "content_json": json.dumps([
            "Detailed visual inspection and systematic condition mapping of all areas identified as defective or deteriorated during the Building Health Check-Up assessment.",
            "Non-destructive testing (NDT) including rebound hammer test, ultrasonic pulse velocity test and rebar locator / cover meter survey at identified locations.",
            "Core cutting and laboratory testing of concrete samples for compressive strength and carbonation depth assessment, wherever required.",
            "Crack mapping with severity classification and measurement of crack widths at all identified locations.",
            "Half-cell potential survey for corrosion activity assessment of reinforcement, as applicable.",
            "Photographic documentation and detailed reporting of all findings with repair/remediation recommendations.",
        ]),
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deq_methodology",
        "heading": "Methodology",
        "content_type": "list",
        "content_json": json.dumps([
            "Site mobilization, safety briefing and review of BHC assessment report.",
            "Detailed inspection and condition mapping of all reported and surrounding defect areas.",
            "NDT measurements (rebound hammer, UPV, cover meter) at agreed locations.",
            "Core cutting and sample collection for laboratory testing, if applicable.",
            "Data analysis, engineering interpretation and preparation of the Detailed Examination Report.",
            "Report submission with findings, severity classification, cause analysis and remediation recommendations.",
        ]),
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deq_deliverables",
        "heading": "Deliverables",
        "content_type": "list",
        "content_json": json.dumps([
            "Detailed Examination Report with findings, severity classification, cause analysis and remediation recommendations.",
            "NDT test data sheets and laboratory analysis certificates (as applicable).",
            "Photographic documentation of all defects, test locations and conditions.",
        ]),
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deq_fees",
        "heading": "Proposed Fees",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deq_payment_terms",
        "heading": "Payment Terms",
        "content_type": "dynamic",
        "content_json": "[]",
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deq_terms_conditions",
        "heading": "Terms & Conditions",
        "content_type": "paragraph",
        "content_json": json.dumps([
            "The scope of detailed examination is limited to the areas and issues identified during the Building Health Check-Up assessment. Any additional areas or scope changes shall be mutually agreed and priced separately.",
            "Client shall arrange safe access to all inspection areas and provide all required site permissions. Scaffolding, ladders or lifting equipment required for inspection at height shall be arranged by the Client.",
            "GST and other statutory charges shall be payable extra as applicable. General terms and conditions of business shall form an integral part of the contract.",
        ]),
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deq_validity",
        "heading": "Validity",
        "content_type": "paragraph",
        "content_json": json.dumps([
            "This proposal is valid for 30 days from the date of issue. The rates shall be firm for 30 days from the date of acceptance of proposal or signing of contract.",
            "We trust you will find the above offer competitive and look forward to being associated with you. For further clarifications, please contact us.",
        ]),
        "is_system": True,
        "is_visible": True,
    },
    {
        "section_key": "deq_acknowledgement",
        "heading": "Acknowledgement / Order Acceptance",
        "content_type": "paragraph",
        "content_json": json.dumps([
            "The quotation is hereby acknowledged and accepted by the Client.",
        ]),
        "is_system": True,
        "is_visible": True,
    },
]

LIST_SETTING_KEYS = {
    "company_profile_paragraphs",
    "tuv_history_paragraphs",
    "service_capabilities",
    "payment_terms",
    "deliverables",
    "other_terms",
}

# ── Default scope-of-work items per scope type ───────────────────────────
DEFAULT_SCOPE_OF_WORK: dict[str, list[str]] = {
    "rcc": [
        "The visual inspection includes assessment of all accessible structural components, such as columns, beams, slabs and visible flooring areas, wherein reinforced concrete members are assessed for cracks, corrosion, spalling and reinforcement exposure, while slabs are further assessed for leakage, dampness, deflection and any exposed reinforcement.",
        "Walls will be assessed for cracks, dampness, peeling or deterioration of paint and other visible signs of distress.",
        "Kitchen, Washroom, Toilet, Bathroom, Utility, Lobby and Balcony areas will be inspected to identify any signs of leakage, dampness or related issues.",
        "The terrace and roof areas, along with staircases and rainwater down pipes, will be inspected for waterproofing condition, water stagnation, drainage issues, leakage, cracks and vegetation growth.",
        "Doors and windows will be inspected for their condition, alignment, and any visible defects or damage.",
        "Electrical switches, sockets along with plumbing & fittings will be assessed for their overall condition and any visible defects.",
        "All observed defects and distress conditions will be systematically recorded with supporting photographic evidence and concise technical descriptions.",
        "The inspection is limited to visual assessment only.",
    ],
    "steel": [
        "The visual inspection includes assessment of all accessible primary and secondary steel members for corrosion, rusting, coating deterioration, deformation, bending, misalignment and condition of bolts and connections.",
        "The roof system, including metal sheets, insulation (if accessible), and skylights, will be inspected for leakage, water ingress, dampness, sheet damage, dents and corrosion.",
        "Wall cladding panels will be assessed for corrosion, dents, physical damage, joint gaps, sealant deterioration and potential leakage points.",
        "All bracing systems and connections, portal bracing, along with bolted and welded joints, will be inspected for corrosion, damage, missing members, fastener condition, tightness and weld defects.",
        "The interface between the steel structure and foundation will be inspected for anchor bolt condition, looseness, corrosion, cracks in pedestal concrete and signs of settlement or base plate misalignment.",
        "Building components such as doors, shutters, windows, ventilators, drainage systems, mezzanine/crane structures and protective coatings will be inspected for alignment, operability, damage, leakage, structural distress and coating deterioration.",
        "All observed defects and distress conditions shall be documented with photographs and brief descriptions.",
        "The inspection is limited to visual assessment only.",
    ],
    "both": [
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
    ],
}

DEFAULT_NEW_BUILDING_SCOPE: dict[str, list[str]] = {
    "new_rcc": [
        "Visual inspection of all accessible RCC structural components including columns, beams, slabs and flooring areas to assess construction quality, workmanship and compliance with standard practices.",
        "Assessment of concrete surfaces for honeycombing, cold joints, construction joints, surface cracks, segregation and any early signs of distress.",
        "Inspection of walls for plaster quality, alignment, plumb, cracks, dampness and finishing defects.",
        "Kitchen, Washroom, Toilet, Bathroom, Utility, Lobby and Balcony areas will be inspected for waterproofing effectiveness, leakage, dampness or related issues.",
        "Terrace and roof areas along with staircases and rainwater down pipes will be inspected for waterproofing condition, drainage adequacy, water stagnation and any construction defects.",
        "Doors and windows will be inspected for proper installation, alignment, hardware condition, sealant application and finishing quality.",
        "Electrical switches, sockets along with plumbing and fittings will be assessed for proper installation and any visible defects.",
        "All observed defects and construction quality concerns will be systematically recorded with supporting photographic evidence and concise technical descriptions.",
        "The inspection is limited to visual assessment only.",
    ],
    "new_steel": [
        "Visual inspection of all accessible primary and secondary steel members to assess fabrication quality, erection accuracy, alignment and compliance with standard practices.",
        "Assessment of all bolted and welded connections for quality of execution, tightness, weld profile, undercut, porosity and any fabrication or erection defects.",
        "The roof system including metal sheets, insulation (if accessible) and skylights will be inspected for installation quality, proper lapping, fastener condition and any signs of water ingress.",
        "Wall cladding panels will be assessed for installation quality, alignment, joint sealant application, fastener condition and any physical damage.",
        "All bracing systems including portal bracing and cross bracing will be inspected for proper installation, alignment, connection integrity and compliance with design intent.",
        "The interface between the steel structure and foundation will be inspected for anchor bolt installation quality, base plate grouting, alignment and levelling.",
        "Protective coating systems (paint/galvanization) will be assessed for application quality, coverage, DFT compliance and any early signs of coating failure or corrosion.",
        "All observed defects and construction quality concerns shall be documented with photographs and brief descriptions.",
        "The inspection is limited to visual assessment only.",
    ],
    "new_both": [
        "Visual inspection of all accessible RCC components such as columns, beams, slabs and flooring areas to assess construction quality, workmanship and compliance with standard practices. Concrete surfaces will be checked for honeycombing, cold joints, segregation and early signs of distress.",
        "All accessible primary and secondary steel members including columns, rafters, beams, purlins and girts will be inspected for fabrication quality, erection accuracy, alignment and compliance with standard practices.",
        "Assessment of all steel connections — bolted and welded — for quality of execution, tightness, weld profile and any fabrication or erection defects.",
        "The roof system (RCC slab or metal roofing) including waterproofing, metal sheets, insulation (if accessible) and skylights will be inspected for installation quality, proper execution and any signs of water ingress.",
        "Wall systems including masonry walls and PEB cladding panels will be assessed for plaster quality, alignment, installation quality, joint sealant application and any construction defects.",
        "All bracing systems (steel bracing), bolted and welded connections will be inspected for proper installation, alignment, connection integrity and design compliance.",
        "The interface between steel structures and RCC foundations/pedestals will be checked for anchor bolt installation quality, base plate grouting, concrete pedestal condition, alignment and levelling.",
        "Doors, windows, shutters, louvers and ventilators will be inspected for proper installation, alignment, hardware condition and finishing quality. Electrical and plumbing systems will be visually assessed for installation quality.",
        "Protective coating systems on steel members will be assessed for application quality, coverage and any early signs of coating failure.",
        "All observed defects and construction quality concerns shall be documented with photographs and brief descriptions.",
        "The inspection is limited to visual assessment only.",
    ],
}

DEFAULT_NEW_BUILDING_SUPPORT_DOCUMENTS: dict[str, list[str]] = {
    "new_rcc": [
        "The client shall provide all available building documents, including approved architectural, structural and service drawings, and shall grant access to all accessible areas of the building, including terraces, water tanks, basements and service areas.",
        "The client shall ensure safe access arrangements for inspection, including provision of ladders, scaffolding or suitable lifting equipment wherever required, and shall grant permission for photographic documentation and recording of observed defects.",
        "The client shall nominate an authorized representative to accompany the inspection team during the site visit and facilitate coordination during the inspection process.",
    ],
    "new_steel": [
        "The client shall provide available structural drawings including PEB general arrangement drawings, fabrication drawings, erection drawings and anchor bolt layout details.",
        "The client shall provide access to all areas of the structure including roof, crane runway (if applicable) and peripheral zones.",
        "Safe access arrangements such as ladders, scaffolding, man-lifts or walkways shall be arranged by the client for inspection at height.",
        "Permission for photographic documentation and recording of defects shall be provided by the client.",
        "The client shall nominate a representative to accompany the inspection team during the site visit.",
    ],
    "new_both": [
        "The client shall provide available architectural and structural drawings for both RCC and PEB portions, including general arrangement, fabrication and connection details.",
        "The client shall provide access to all areas of the building including terrace, roof, intermediate floors and service areas.",
        "Safe access arrangements such as ladders, scaffolding, walkways or man-lifts shall be arranged by the client for inspection at height.",
        "Permission for photographic documentation and recording of observed defects shall be provided.",
        "The client shall nominate a responsible representative to coordinate and accompany the inspection team during the site visit.",
    ],
}

DEFAULT_SUPPORT_DOCUMENTS: dict[str, list[str]] = {
    "rcc": [
        "The client shall provide all available building documents, including architectural, structural, and service drawings, and shall grant access to all accessible areas of the building, including terraces, water tanks, basements, and service areas.",
        "The client shall ensure safe access arrangements for inspection, including provision of ladders, scaffolding, or suitable lifting equipment wherever required, and shall grant permission for photographic documentation and recording of observed defects.",
        "The client shall nominate an authorized representative to accompany the inspection team during the site visit and facilitate coordination during the inspection process.",
    ],
    "steel": [
        "The client shall provide available structural drawings including PEB general arrangement drawings, fabrication drawings and anchor bolt layout details.",
        "The client shall provide access to all areas of the structure including roof, crane runway (if applicable) and peripheral zones.",
        "Safe access arrangements such as ladders, scaffolding, man-lifts or walkways shall be arranged by the client for inspection at height.",
        "Permission for photographic documentation and recording of defects shall be provided by the client.",
        "The client shall nominate a representative to accompany the inspection team during the site visit.",
    ],
    "both": [
        "The client shall provide available architectural and structural drawings for both RCC and PEB portions, including general arrangement and connection details.",
        "The client shall provide access to all areas of the building including terrace, roof, intermediate floors and service areas.",
        "Safe access arrangements such as ladders, scaffolding, walkways or man-lifts shall be arranged by the client for inspection at height.",
        "Permission for photographic documentation and recording of observed defects shall be provided.",
        "The client shall nominate a responsible representative to coordinate and accompany the inspection team during the site visit.",
    ],
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def _validate_corporate_email(email: str) -> str:
    normalized = _normalize_email(email)
    if not normalized or not normalized.endswith(ALLOWED_EMAIL_DOMAIN):
        raise ValueError(f"Only {ALLOWED_EMAIL_DOMAIN} email IDs are allowed.")
    return normalized


def _validate_password_strength(password: str) -> str:
    cleaned = str(password or "")
    if len(cleaned) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", cleaned):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", cleaned):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", cleaned):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", cleaned):
        raise ValueError("Password must contain at least one special character (e.g. @, #, !, $).")
    return cleaned


def _hash_password(password: str, salt_hex: str | None = None) -> str:
    validated_password = _validate_password_strength(password)
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        validated_password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = str(password_hash or "").split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    iterations = int(iterations_text)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password or "").encode("utf-8"),
        bytes.fromhex(salt_hex),
        iterations,
    )
    return digest.hex() == digest_hex


def _session_hash(token: str) -> str:
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


# Default bootstrap password — used only for first-time admin creation.
# Admin is forced to change it on first login (must_change_password=1).
_DEFAULT_BOOTSTRAP_PASSWORD = "Naveenkumar@123"


def _bootstrap_admin_password() -> str:
    return _DEFAULT_BOOTSTRAP_PASSWORD


def _sanitize_user_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    keys = row.keys() if hasattr(row, "keys") else []
    result: dict[str, Any] = {
        "email": str(row["email"]),
        "full_name": str(row["full_name"]),
        "is_admin": bool(row["is_admin"]),
        "is_active": bool(row["is_active"]),
        "must_change_password": bool(row["must_change_password"]),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
        "created_by": str(row["created_by"] or ""),
    }
    if "designation" in keys:
        result["designation"] = str(row["designation"] or "")
    if "has_signature" in keys:
        result["has_signature"] = bool(row["has_signature"])
    if "has_security_question" in keys:
        result["has_security_question"] = bool(row["has_security_question"])
    return result


def get_config_db_path() -> Path:
    configured_path = os.environ.get("BHC_CONFIG_DB_PATH", BHC_CONFIG_DB_PATH).strip()
    if configured_path:
        return Path(configured_path)
    return DATA_DIR / "bhc_config.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = DELETE")
    return conn


def _serialize_setting(key: str, value: Any) -> str:
    if key in LIST_SETTING_KEYS:
        if isinstance(value, str):
            items = [line.strip() for line in value.splitlines() if line.strip()]
            return json.dumps(items)
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            return json.dumps(items)
        raise ValueError(f"Setting '{key}' must be a list of strings.")
    return str(value or "").strip()


def _deserialize_setting(key: str, raw_value: str) -> Any:
    if key in LIST_SETTING_KEYS:
        try:
            parsed = json.loads(raw_value or "[]")
        except json.JSONDecodeError:
            parsed = [line.strip() for line in str(raw_value or "").splitlines() if line.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return []
    return str(raw_value or "")


def init_config_db(db_path: Path | None = None) -> None:
    resolved_path = db_path or get_config_db_path()
    with _connect(resolved_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_slabs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sort_order INTEGER NOT NULL,
                min_area REAL NOT NULL,
                max_area REAL NOT NULL,
                label TEXT NOT NULL,
                quoted_price REAL NOT NULL,
                slab_category TEXT NOT NULL DEFAULT 'standard'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_accounts (
                email TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                designation TEXT NOT NULL DEFAULT '',
                signature_blob BLOB,
                security_question TEXT NOT NULL DEFAULT '',
                security_answer_hash TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT NOT NULL DEFAULT 'system'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token_hash TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                status TEXT NOT NULL,
                resolved_at TEXT,
                resolved_by TEXT,
                notes TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS security_audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_email TEXT NOT NULL,
                target TEXT,
                severity TEXT NOT NULL DEFAULT 'INFO',
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )

        # ── Scope-of-work items table ────────────────────────────
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scope_of_work_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_type TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                item_text TEXT NOT NULL
            )
            """
        )

        # ── Support-documents items table ────────────────────────
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS support_document_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_type TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                item_text TEXT NOT NULL
            )
            """
        )

        # ── Quotation sections table (v7) ────────────────────────
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quotation_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_key TEXT NOT NULL UNIQUE,
                heading TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'list',
                content_json TEXT NOT NULL DEFAULT '[]',
                sort_order INTEGER NOT NULL,
                is_visible INTEGER NOT NULL DEFAULT 1,
                is_system INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # ── DEQ sections table ───────────────────────────────────
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deq_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_key TEXT NOT NULL UNIQUE,
                heading TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'list',
                content_json TEXT NOT NULL DEFAULT '[]',
                sort_order INTEGER NOT NULL,
                is_visible INTEGER NOT NULL DEFAULT 1,
                is_system INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        existing_setting_keys = {
            row["key"]
            for row in conn.execute("SELECT key FROM app_settings").fetchall()
        }
        for key, value in {**DEFAULT_COMPANY_SETTINGS, **DEFAULT_DOCUMENT_SETTINGS}.items():
            if key not in existing_setting_keys:
                conn.execute(
                    "INSERT INTO app_settings(key, value) VALUES (?, ?)",
                    (key, _serialize_setting(key, value)),
                )

        # Add slab_category column if missing (upgrade path)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(pricing_slabs)").fetchall()]
        if "slab_category" not in columns:
            conn.execute("ALTER TABLE pricing_slabs ADD COLUMN slab_category TEXT NOT NULL DEFAULT 'standard'")

        slab_count = conn.execute("SELECT COUNT(*) AS total FROM pricing_slabs").fetchone()["total"]
        if not slab_count:
            _replace_pricing_slabs_by_category(conn, DEFAULT_PRICING_SLABS, SLAB_CATEGORY_STANDARD)
            _replace_pricing_slabs_by_category(conn, DEFAULT_NEW_BUILDING_PRICING_SLABS, SLAB_CATEGORY_NEW_BUILDING)
        else:
            # Seed new-building slabs if missing (upgrade path)
            new_slab_count = conn.execute(
                "SELECT COUNT(*) AS total FROM pricing_slabs WHERE slab_category = ?",
                (SLAB_CATEGORY_NEW_BUILDING,),
            ).fetchone()["total"]
            if not new_slab_count:
                _replace_pricing_slabs_by_category(conn, DEFAULT_NEW_BUILDING_PRICING_SLABS, SLAB_CATEGORY_NEW_BUILDING)

        # Seed scope-of-work items
        scope_count = conn.execute("SELECT COUNT(*) AS total FROM scope_of_work_items").fetchone()["total"]
        if not scope_count:
            all_scope_defaults = {**DEFAULT_SCOPE_OF_WORK, **DEFAULT_NEW_BUILDING_SCOPE}
            for scope_type, items in all_scope_defaults.items():
                for idx, text in enumerate(items, start=1):
                    conn.execute(
                        "INSERT INTO scope_of_work_items(scope_type, sort_order, item_text) VALUES (?, ?, ?)",
                        (scope_type, idx, text),
                    )
        else:
            # Seed new-building scope if missing (upgrade path)
            new_scope_count = conn.execute(
                "SELECT COUNT(*) AS total FROM scope_of_work_items WHERE scope_type LIKE 'new_%'"
            ).fetchone()["total"]
            if not new_scope_count:
                for scope_type, items in DEFAULT_NEW_BUILDING_SCOPE.items():
                    for idx, text in enumerate(items, start=1):
                        conn.execute(
                            "INSERT INTO scope_of_work_items(scope_type, sort_order, item_text) VALUES (?, ?, ?)",
                            (scope_type, idx, text),
                        )

        # Seed support-document items
        support_count = conn.execute("SELECT COUNT(*) AS total FROM support_document_items").fetchone()["total"]
        if not support_count:
            all_support_defaults = {**DEFAULT_SUPPORT_DOCUMENTS, **DEFAULT_NEW_BUILDING_SUPPORT_DOCUMENTS}
            for scope_type, items in all_support_defaults.items():
                for idx, text in enumerate(items, start=1):
                    conn.execute(
                        "INSERT INTO support_document_items(scope_type, sort_order, item_text) VALUES (?, ?, ?)",
                        (scope_type, idx, text),
                    )
        else:
            # Seed new-building support docs if missing (upgrade path)
            new_support_count = conn.execute(
                "SELECT COUNT(*) AS total FROM support_document_items WHERE scope_type LIKE 'new_%'"
            ).fetchone()["total"]
            if not new_support_count:
                for scope_type, items in DEFAULT_NEW_BUILDING_SUPPORT_DOCUMENTS.items():
                    for idx, text in enumerate(items, start=1):
                        conn.execute(
                            "INSERT INTO support_document_items(scope_type, sort_order, item_text) VALUES (?, ?, ?)",
                            (scope_type, idx, text),
                        )

        # Seed quotation sections (v7)
        qs_count = conn.execute("SELECT COUNT(*) AS total FROM quotation_sections").fetchone()["total"]
        if not qs_count:
            now = _utcnow_iso()
            for idx, sec in enumerate(DEFAULT_QUOTATION_SECTIONS, start=1):
                conn.execute(
                    "INSERT INTO quotation_sections(section_key, heading, content_type, content_json, sort_order, is_visible, is_system, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        sec["section_key"],
                        sec["heading"],
                        sec["content_type"],
                        sec["content_json"],
                        idx * 10,
                        1 if sec["is_visible"] else 0,
                        1 if sec["is_system"] else 0,
                        now,
                        now,
                    ),
                )

        # Seed DEQ sections
        deq_count = conn.execute("SELECT COUNT(*) AS total FROM deq_sections").fetchone()["total"]
        if not deq_count:
            now = _utcnow_iso()
            for idx, sec in enumerate(DEFAULT_DEQ_SECTIONS, start=1):
                conn.execute(
                    "INSERT INTO deq_sections(section_key, heading, content_type, content_json, sort_order, is_visible, is_system, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        sec["section_key"],
                        sec["heading"],
                        sec["content_type"],
                        sec["content_json"],
                        idx * 10,
                        1 if sec["is_visible"] else 0,
                        1 if sec["is_system"] else 0,
                        now,
                        now,
                    ),
                )

        # Add designation and signature_blob columns if missing (v5 upgrade)
        user_columns = [row[1] for row in conn.execute("PRAGMA table_info(user_accounts)").fetchall()]
        if "designation" not in user_columns:
            conn.execute("ALTER TABLE user_accounts ADD COLUMN designation TEXT NOT NULL DEFAULT ''")
        if "signature_blob" not in user_columns:
            conn.execute("ALTER TABLE user_accounts ADD COLUMN signature_blob BLOB")
        if "security_question" not in user_columns:
            conn.execute("ALTER TABLE user_accounts ADD COLUMN security_question TEXT NOT NULL DEFAULT ''")
        if "security_answer_hash" not in user_columns:
            conn.execute("ALTER TABLE user_accounts ADD COLUMN security_answer_hash TEXT NOT NULL DEFAULT ''")

        _ensure_admin_user(conn)
        conn.execute("DELETE FROM user_sessions WHERE expires_at <= ?", (_utcnow_iso(),))
        conn.execute(
            "INSERT INTO schema_meta(key, value) VALUES ('config_schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (CONFIG_SCHEMA_VERSION,),
        )

        conn.commit()


def get_config_schema_version() -> str:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT value FROM schema_meta WHERE key = 'config_schema_version'").fetchone()
    return str(row["value"]) if row else CONFIG_SCHEMA_VERSION


def log_security_audit_event(
    event_type: str,
    actor_email: str,
    target: str = "",
    severity: str = "INFO",
    metadata: dict[str, Any] | None = None,
) -> None:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute(
            """
            INSERT INTO security_audit_events(
                event_time, event_type, actor_email, target, severity, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _utcnow_iso(),
                str(event_type or "UNKNOWN"),
                _normalize_email(actor_email) or "unknown@system.local",
                str(target or ""),
                str(severity or "INFO").upper(),
                json.dumps(metadata or {}, ensure_ascii=True),
            ),
        )
        conn.commit()


def list_security_audit_events(limit: int = 200) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 200), 1000))
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        rows = conn.execute(
            """
            SELECT id, event_time, event_type, actor_email, target, severity, metadata_json
            FROM security_audit_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    events: list[dict[str, Any]] = []
    for row in rows:
        raw_meta = str(row["metadata_json"] or "{}")
        try:
            parsed_meta = json.loads(raw_meta)
        except json.JSONDecodeError:
            parsed_meta = {"raw": raw_meta}
        events.append(
            {
                "id": int(row["id"]),
                "event_time": str(row["event_time"]),
                "event_type": str(row["event_type"]),
                "actor_email": str(row["actor_email"]),
                "target": str(row["target"] or ""),
                "severity": str(row["severity"]),
                "metadata": parsed_meta,
            }
        )

    return events


def _ensure_admin_user(conn: sqlite3.Connection) -> None:
    admin_email = _normalize_email(DEFAULT_ADMIN_EMAIL)
    now = _utcnow_iso()
    existing = conn.execute(
        "SELECT email, is_admin FROM user_accounts WHERE email = ?",
        (admin_email,),
    ).fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO user_accounts (
                email, full_name, designation, password_hash, is_admin, is_active, must_change_password,
                created_at, updated_at, created_by
            ) VALUES (?, ?, ?, ?, 1, 1, 0, ?, ?, 'system')
            """,
            (
                admin_email,
                DEFAULT_ADMIN_NAME,
                DEFAULT_ADMIN_DESIGNATION,
                _hash_password(_bootstrap_admin_password()),
                now,
                now,
            ),
        )
        return

    if not bool(existing["is_admin"]):
        conn.execute(
            "UPDATE user_accounts SET is_admin = 1, updated_at = ? WHERE email = ?",
            (now, admin_email),
        )


def _settings_by_keys(keys: list[str]) -> dict[str, Any]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        placeholders = ", ".join("?" for _ in keys)
        rows = conn.execute(
            f"SELECT key, value FROM app_settings WHERE key IN ({placeholders})",
            tuple(keys),
        ).fetchall()

    values = {row["key"]: _deserialize_setting(row["key"], row["value"]) for row in rows}
    defaults = {**DEFAULT_COMPANY_SETTINGS, **DEFAULT_DOCUMENT_SETTINGS}
    return {key: values.get(key, defaults[key]) for key in keys}


def get_company_settings() -> dict[str, str]:
    keys = list(DEFAULT_COMPANY_SETTINGS.keys())
    return {key: str(value) for key, value in _settings_by_keys(keys).items()}


def get_urgency_surcharge_percent() -> float:
    """Return the urgency surcharge percentage from config DB."""
    settings = get_company_settings()
    try:
        val = settings.get("urgency_surcharge_percent", "10")
        # Treat missing/empty as default 10; explicitly allow 0
        if val is None or val == "":
            return 10.0
        return float(val)
    except (ValueError, TypeError):
        return 10.0


def get_gst_percent() -> float:
    """Return the GST percentage from config DB."""
    settings = get_company_settings()
    try:
        return float(settings.get("gst_percent", "18") or "18")
    except (ValueError, TypeError):
        return 18.0


def update_company_settings(settings: dict[str, Any]) -> dict[str, str]:
    keys = list(DEFAULT_COMPANY_SETTINGS.keys())
    sanitized = {key: str(settings.get(key, "")).strip() for key in keys}
    if not sanitized["company_name"]:
        raise ValueError("Company name is required.")
    if not sanitized["contact_name"]:
        raise ValueError("Contact name is required.")
    # Validate numeric settings
    for numeric_key in ("urgency_surcharge_percent", "gst_percent"):
        val = sanitized.get(numeric_key, "")
        if val:
            try:
                fval = float(val)
                if fval < 0:
                    raise ValueError(f"{numeric_key} must not be negative.")
            except (ValueError, TypeError):
                raise ValueError(f"{numeric_key} must be a valid number.")

    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        for key, value in sanitized.items():
            conn.execute(
                "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        conn.commit()
    return get_company_settings()


def get_document_settings() -> dict[str, Any]:
    keys = list(DEFAULT_DOCUMENT_SETTINGS.keys())
    return _settings_by_keys(keys)


def update_document_settings(settings: dict[str, Any]) -> dict[str, Any]:
    keys = list(DEFAULT_DOCUMENT_SETTINGS.keys())
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        for key in keys:
            serialized_value = _serialize_setting(key, settings.get(key, DEFAULT_DOCUMENT_SETTINGS[key]))
            conn.execute(
                "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, serialized_value),
            )
        conn.commit()
    return get_document_settings()


def list_pricing_slabs(slab_category: str | None = None) -> list[dict[str, float | int | str]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        if slab_category:
            rows = conn.execute(
                "SELECT min_area, max_area, label, quoted_price, slab_category FROM pricing_slabs WHERE slab_category = ? ORDER BY sort_order ASC, id ASC",
                (slab_category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT min_area, max_area, label, quoted_price, slab_category FROM pricing_slabs ORDER BY slab_category ASC, sort_order ASC, id ASC"
            ).fetchall()
    return [
        {
            "min_area": float(row["min_area"]),
            "max_area": float(row["max_area"]),
            "label": str(row["label"]),
            "quoted_price": float(row["quoted_price"]),
            "slab_category": str(row["slab_category"]),
        }
        for row in rows
    ]


def validate_pricing_slabs(slabs: list[dict[str, Any]]) -> list[dict[str, float | int | str]]:
    if not slabs:
        raise ValueError("At least one pricing slab is required.")

    normalized: list[dict[str, float | int | str]] = []
    previous_max_area: float | None = None
    for index, slab in enumerate(slabs, start=1):
        min_area = float(slab.get("min_area", 0) or 0)
        max_area = float(slab.get("max_area", 0) or 0)
        quoted_price = float(slab.get("quoted_price", 0) or 0)
        label = str(slab.get("label", "")).strip()

        if not label:
            raise ValueError(f"Pricing slab {index} must have a label.")
        if min_area > max_area:
            raise ValueError(f"Pricing slab {index} has min area greater than max area.")
        if quoted_price < 0:
            raise ValueError(f"Pricing slab {index} must not have a negative price.")
        if previous_max_area is not None and min_area <= previous_max_area:
            raise ValueError("Pricing slabs must be arranged in ascending order without overlap.")

        normalized.append(
            {
                "min_area": min_area,
                "max_area": max_area,
                "label": label,
                "quoted_price": quoted_price,
            }
        )
        previous_max_area = max_area

    return normalized


def _replace_pricing_slabs_by_category(conn: sqlite3.Connection, slabs: list[dict[str, Any]], category: str) -> None:
    """Replace pricing slabs for a specific category only."""
    normalized_slabs = validate_pricing_slabs(slabs)
    conn.execute("DELETE FROM pricing_slabs WHERE slab_category = ?", (category,))
    for sort_order, slab in enumerate(normalized_slabs, start=1):
        conn.execute(
            "INSERT INTO pricing_slabs(sort_order, min_area, max_area, label, quoted_price, slab_category) VALUES (?, ?, ?, ?, ?, ?)",
            (
                sort_order,
                float(slab["min_area"]),
                float(slab["max_area"]),
                str(slab["label"]),
                float(slab["quoted_price"]),
                category,
            ),
        )


def replace_pricing_slabs(slabs: list[dict[str, Any]], slab_category: str = SLAB_CATEGORY_STANDARD) -> list[dict[str, float | int | str]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        _replace_pricing_slabs_by_category(conn, slabs, slab_category)
        conn.commit()
    return list_pricing_slabs(slab_category)


# ── Scope-of-work items ─────────────────────────────────────────────────

def list_scope_of_work_items(scope_type: str | None = None) -> dict[str, list[str]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        if scope_type:
            rows = conn.execute(
                "SELECT scope_type, item_text FROM scope_of_work_items WHERE scope_type = ? ORDER BY sort_order ASC, id ASC",
                (scope_type.lower(),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT scope_type, item_text FROM scope_of_work_items ORDER BY scope_type ASC, sort_order ASC, id ASC"
            ).fetchall()
    result: dict[str, list[str]] = {}
    for row in rows:
        st = str(row["scope_type"])
        result.setdefault(st, []).append(str(row["item_text"]))
    return result


VALID_SCOPE_TYPES = {"rcc", "steel", "both", "new_rcc", "new_steel", "new_both"}


def replace_scope_of_work_items(scope_data: dict[str, list[str]]) -> dict[str, list[str]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute("DELETE FROM scope_of_work_items")
        for scope_type, items in scope_data.items():
            st = str(scope_type).strip().lower()
            if st not in VALID_SCOPE_TYPES:
                raise ValueError(f"Invalid scope type: '{scope_type}'. Must be one of: {', '.join(sorted(VALID_SCOPE_TYPES))}.")
            for idx, text in enumerate(items, start=1):
                cleaned = str(text).strip()
                if cleaned:
                    conn.execute(
                        "INSERT INTO scope_of_work_items(scope_type, sort_order, item_text) VALUES (?, ?, ?)",
                        (st, idx, cleaned),
                    )
        conn.commit()
    return list_scope_of_work_items()


def list_support_document_items(scope_type: str | None = None) -> dict[str, list[str]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        if scope_type:
            rows = conn.execute(
                "SELECT scope_type, item_text FROM support_document_items WHERE scope_type = ? ORDER BY sort_order ASC, id ASC",
                (scope_type.lower(),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT scope_type, item_text FROM support_document_items ORDER BY scope_type ASC, sort_order ASC, id ASC"
            ).fetchall()
    result: dict[str, list[str]] = {}
    for row in rows:
        st = str(row["scope_type"])
        result.setdefault(st, []).append(str(row["item_text"]))
    return result


def replace_support_document_items(scope_data: dict[str, list[str]]) -> dict[str, list[str]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute("DELETE FROM support_document_items")
        for scope_type, items in scope_data.items():
            st = str(scope_type).strip().lower()
            if st not in VALID_SCOPE_TYPES:
                raise ValueError(f"Invalid scope type: '{scope_type}'. Must be one of: {', '.join(sorted(VALID_SCOPE_TYPES))}.")
            for idx, text in enumerate(items, start=1):
                cleaned = str(text).strip()
                if cleaned:
                    conn.execute(
                        "INSERT INTO support_document_items(scope_type, sort_order, item_text) VALUES (?, ?, ?)",
                        (st, idx, cleaned),
                    )
        conn.commit()
    return list_support_document_items()


# ── Quotation Sections CRUD ──────────────────────────────────────────────

def _row_to_section(row: sqlite3.Row) -> dict[str, Any]:
    content_raw = str(row["content_json"] or "[]")
    try:
        content = json.loads(content_raw)
    except json.JSONDecodeError:
        content = []
    return {
        "id": int(row["id"]),
        "section_key": str(row["section_key"]),
        "heading": str(row["heading"]),
        "content_type": str(row["content_type"]),
        "content": content,
        "sort_order": int(row["sort_order"]),
        "is_visible": bool(row["is_visible"]),
        "is_system": bool(row["is_system"]),
    }


def list_quotation_sections() -> list[dict[str, Any]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        rows = conn.execute(
            "SELECT * FROM quotation_sections ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    return [_row_to_section(row) for row in rows]


def get_quotation_section(section_id: int) -> dict[str, Any] | None:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT * FROM quotation_sections WHERE id = ?", (section_id,)
        ).fetchone()
    return _row_to_section(row) if row else None


def create_quotation_section(
    heading: str,
    content_type: str = "list",
    content: list | None = None,
) -> dict[str, Any]:
    heading = str(heading).strip()
    if not heading:
        raise ValueError("Heading is required.")
    allowed_types = {"list", "paragraph", "table", "dynamic"}
    if content_type not in allowed_types:
        raise ValueError(f"Invalid content_type. Must be one of: {', '.join(sorted(allowed_types))}.")
    content_json = json.dumps(content or [], ensure_ascii=True)
    section_key = heading.lower().replace(" ", "_").replace("/", "_")[:50]
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS mx FROM quotation_sections").fetchone()["mx"]
        # Ensure unique section_key
        existing = conn.execute("SELECT id FROM quotation_sections WHERE section_key = ?", (section_key,)).fetchone()
        if existing:
            section_key = f"{section_key}_{int(max_order) + 10}"
        conn.execute(
            "INSERT INTO quotation_sections(section_key, heading, content_type, content_json, sort_order, is_visible, is_system, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?)",
            (section_key, heading, content_type, content_json, max_order + 10, now, now),
        )
        conn.commit()
        new_row = conn.execute(
            "SELECT * FROM quotation_sections WHERE section_key = ?", (section_key,)
        ).fetchone()
    return _row_to_section(new_row)


def update_quotation_section(
    section_id: int,
    heading: str | None = None,
    content: list | None = None,
    is_visible: bool | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT * FROM quotation_sections WHERE id = ?", (section_id,)).fetchone()
        if not row:
            raise ValueError(f"Section with id {section_id} not found.")
        updates: list[str] = []
        params: list[Any] = []
        if heading is not None:
            heading = str(heading).strip()
            if not heading:
                raise ValueError("Heading cannot be empty.")
            updates.append("heading = ?")
            params.append(heading)
        if content is not None:
            updates.append("content_json = ?")
            params.append(json.dumps(content, ensure_ascii=True))
        if is_visible is not None:
            updates.append("is_visible = ?")
            params.append(1 if is_visible else 0)
        if content_type is not None:
            allowed_types = {"list", "paragraph", "table", "dynamic"}
            if content_type not in allowed_types:
                raise ValueError(f"Invalid content_type. Must be one of: {', '.join(sorted(allowed_types))}.")
            updates.append("content_type = ?")
            params.append(content_type)
        if updates:
            updates.append("updated_at = ?")
            params.append(_utcnow_iso())
            params.append(section_id)
            conn.execute(
                f"UPDATE quotation_sections SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
    return get_quotation_section(section_id)


def delete_quotation_section(section_id: int) -> bool:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT is_system FROM quotation_sections WHERE id = ?", (section_id,)).fetchone()
        if not row:
            raise ValueError(f"Section with id {section_id} not found.")
        if row["is_system"]:
            raise ValueError("System sections cannot be deleted. You can hide them instead.")
        conn.execute("DELETE FROM quotation_sections WHERE id = ?", (section_id,))
        conn.commit()
    return True


def reorder_quotation_sections(ordered_ids: list[int]) -> list[dict[str, Any]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    now = _utcnow_iso()
    with _connect(resolved_path) as conn:
        for idx, section_id in enumerate(ordered_ids):
            conn.execute(
                "UPDATE quotation_sections SET sort_order = ?, updated_at = ? WHERE id = ?",
                ((idx + 1) * 10, now, section_id),
            )
        conn.commit()
    return list_quotation_sections()


def get_admin_config() -> dict[str, Any]:
    return {
        "config_schema_version": get_config_schema_version(),
        "company": get_company_settings(),
        "document": get_document_settings(),
        "pricing": {
            "model": "area_slab",
            "slabs": list_pricing_slabs(SLAB_CATEGORY_STANDARD),
            "new_building_slabs": list_pricing_slabs(SLAB_CATEGORY_NEW_BUILDING),
        },
        "scope_of_work": list_scope_of_work_items(),
        "support_documents": list_support_document_items(),
        "quotation_sections": list_quotation_sections(),
        "users": list_user_accounts(),
        "db_path": str(get_config_db_path()),
    }


def get_user_by_email(email: str) -> dict[str, Any] | None:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        return None

    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT email, full_name, is_admin, is_active, must_change_password, designation, "
            "(CASE WHEN signature_blob IS NOT NULL AND length(signature_blob) > 0 THEN 1 ELSE 0 END) AS has_signature, "
            "(CASE WHEN security_question != '' AND security_answer_hash != '' THEN 1 ELSE 0 END) AS has_security_question, "
            "created_at, updated_at, created_by FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
    return _sanitize_user_row(row)


def list_user_accounts() -> list[dict[str, Any]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        rows = conn.execute(
            "SELECT email, full_name, is_admin, is_active, must_change_password, designation, "
            "(CASE WHEN signature_blob IS NOT NULL AND length(signature_blob) > 0 THEN 1 ELSE 0 END) AS has_signature, "
            "(CASE WHEN security_question != '' AND security_answer_hash != '' THEN 1 ELSE 0 END) AS has_security_question, "
            "created_at, updated_at, created_by FROM user_accounts ORDER BY is_admin DESC, email ASC"
        ).fetchall()
    return [_sanitize_user_row(row) for row in rows if row is not None]


def create_user_account(email: str, full_name: str, password: str, is_admin: bool, created_by: str, designation: str = "") -> dict[str, Any]:
    normalized_email = _validate_corporate_email(email)
    cleaned_name = str(full_name or "").strip()
    if not cleaned_name:
        raise ValueError("Full name is required.")

    cleaned_designation = str(designation or "").strip()
    validated_password = _validate_password_strength(password)
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        existing = conn.execute(
            "SELECT email FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if existing:
            raise ValueError("A user with this email already exists.")

        conn.execute(
            """
            INSERT INTO user_accounts (
                email, full_name, password_hash, is_admin, is_active, must_change_password,
                designation, created_at, updated_at, created_by
            ) VALUES (?, ?, ?, ?, 1, 1, ?, ?, ?, ?)
            """,
            (
                normalized_email,
                cleaned_name,
                _hash_password(validated_password),
                1 if is_admin else 0,
                cleaned_designation,
                now,
                now,
                _normalize_email(created_by) or "system",
            ),
        )
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def self_register_user(
    email: str,
    full_name: str,
    password: str,
    designation: str = "",
    security_question: str = "",
    security_answer: str = "",
) -> dict[str, Any]:
    """Self-registration: creates user with is_active=0 (pending admin approval)."""
    normalized_email = _validate_corporate_email(email)
    cleaned_name = str(full_name or "").strip()
    if not cleaned_name:
        raise ValueError("Full name is required.")

    cleaned_designation = str(designation or "").strip()
    validated_password = _validate_password_strength(password)

    # Validate security question
    sq = str(security_question or "").strip()
    sa = str(security_answer or "").strip()
    if not sq or not sa:
        raise ValueError("Security question and answer are required for registration.")
    if sq not in SECURITY_QUESTIONS:
        raise ValueError("Invalid security question.")

    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        existing = conn.execute(
            "SELECT email FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if existing:
            raise ValueError("A user with this email already exists.")

        conn.execute(
            """
            INSERT INTO user_accounts (
                email, full_name, password_hash, is_admin, is_active, must_change_password,
                designation, security_question, security_answer_hash,
                created_at, updated_at, created_by
            ) VALUES (?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_email,
                cleaned_name,
                _hash_password(validated_password),
                cleaned_designation,
                sq,
                _hash_security_answer(sa, normalized_email),
                now,
                now,
                "self",
            ),
        )
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def approve_user(email: str) -> dict[str, Any]:
    """Admin approves a pending user — sets is_active=1."""
    normalized_email = _validate_corporate_email(email)
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT email, is_active FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if row is None:
            raise ValueError("User not found.")
        if bool(row["is_active"]):
            raise ValueError("User is already active.")
        conn.execute(
            "UPDATE user_accounts SET is_active = 1, updated_at = ? WHERE email = ?",
            (now, normalized_email),
        )
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def toggle_user_active(email: str, is_active: bool) -> dict[str, Any]:
    """Admin toggles a user's active status."""
    normalized_email = _validate_corporate_email(email)
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT email FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if row is None:
            raise ValueError("User not found.")
        conn.execute(
            "UPDATE user_accounts SET is_active = ?, updated_at = ? WHERE email = ?",
            (1 if is_active else 0, now, normalized_email),
        )
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def toggle_user_admin(email: str, is_admin: bool) -> dict[str, Any]:
    """Admin grants or revokes admin access for a user."""
    normalized_email = _validate_corporate_email(email)
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT email FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if row is None:
            raise ValueError("User not found.")
        conn.execute(
            "UPDATE user_accounts SET is_admin = ?, updated_at = ? WHERE email = ?",
            (1 if is_admin else 0, now, normalized_email),
        )
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def update_user_profile(email: str, designation: str) -> dict[str, Any]:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        raise ValueError("Invalid email.")
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute(
            "UPDATE user_accounts SET designation = ?, updated_at = ? WHERE email = ?",
            (str(designation or "").strip(), now, normalized_email),
        )
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def save_user_signature(email: str, signature_data: bytes) -> None:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        raise ValueError("Invalid email.")
    if len(signature_data) > 500_000:
        raise ValueError("Signature image must be under 500 KB.")
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute(
            "UPDATE user_accounts SET signature_blob = ?, updated_at = ? WHERE email = ?",
            (signature_data, now, normalized_email),
        )
        conn.commit()


def get_user_signature(email: str) -> bytes | None:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        return None
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT signature_blob FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
    if row is None or row["signature_blob"] is None:
        return None
    return bytes(row["signature_blob"])


def authenticate_user_credentials(email: str, password: str) -> dict[str, Any]:
    normalized_email = _validate_corporate_email(email)
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)

    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT * FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if row is None:
            raise ValueError("Invalid email or password.")
        if not bool(row["is_active"]):
            raise ValueError("Your account is pending admin approval. Please contact your administrator.")

        if _verify_password(password, str(row["password_hash"])):
            return _sanitize_user_row(row) or {}

    raise ValueError("Invalid email or password.")


def change_user_password(email: str, current_password: str, new_password: str) -> dict[str, Any]:
    normalized_email = _validate_corporate_email(email)
    validated_password = _validate_password_strength(new_password)
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)

    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT * FROM user_accounts WHERE email = ?", (normalized_email,)).fetchone()
        if row is None:
            raise ValueError("User not found.")
        if not _verify_password(current_password, str(row["password_hash"])):
            raise ValueError("Current password is incorrect.")

        conn.execute(
            "UPDATE user_accounts SET password_hash = ?, must_change_password = 0, updated_at = ? WHERE email = ?",
            (_hash_password(validated_password), _utcnow_iso(), normalized_email),
        )
        conn.execute("DELETE FROM user_sessions WHERE email = ?", (normalized_email,))
        conn.commit()
    return get_user_by_email(normalized_email) or {}


# ── Security Question helpers ───────────────────────────────────────

SECURITY_ANSWER_ITERATIONS = 100000


def _hash_security_answer(answer: str, email_salt: str) -> str:
    """PBKDF2-SHA256 hash of a security answer, case-insensitive, using email as salt."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        answer.lower().encode("utf-8"),
        email_salt.encode("utf-8"),
        SECURITY_ANSWER_ITERATIONS,
    ).hex()


SECURITY_QUESTIONS = [
    "What is the name of your first pet?",
    "What city were you born in?",
    "What was the name of your first school?",
]


def set_security_question(email: str, question: str, answer: str) -> dict[str, Any]:
    normalized_email = _validate_corporate_email(email)
    question = str(question or "").strip()
    answer = str(answer or "").strip()
    if not question or not answer:
        raise ValueError("Both security question and answer are required.")
    if len(answer) < 2:
        raise ValueError("Security answer must be at least 2 characters.")
    now = _utcnow_iso()
    answer_hash = _hash_security_answer(answer, normalized_email)
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute(
            "UPDATE user_accounts SET security_question = ?, security_answer_hash = ?, updated_at = ? WHERE email = ?",
            (question, answer_hash, now, normalized_email),
        )
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def get_security_question(email: str) -> str:
    normalized_email = _validate_corporate_email(email)
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT security_question FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
    if row is None:
        raise ValueError("User not found.")
    q = str(row["security_question"] or "")
    if not q:
        raise ValueError("No security question has been set for this account. Contact administrator.")
    return q


def verify_security_answer(email: str, answer: str) -> bool:
    normalized_email = _validate_corporate_email(email)
    answer = str(answer or "").strip()
    if not answer:
        return False
    answer_hash = _hash_security_answer(answer, normalized_email)
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            "SELECT security_answer_hash FROM user_accounts WHERE email = ?",
            (normalized_email,),
        ).fetchone()
    if row is None:
        return False
    return str(row["security_answer_hash"] or "") == answer_hash


def reset_user_password_by_email(email: str, new_password: str, security_answer: str) -> dict[str, Any]:
    normalized_email = _validate_corporate_email(email)
    if not verify_security_answer(normalized_email, security_answer):
        raise ValueError("Security answer is incorrect.")
    validated_password = _validate_password_strength(new_password)
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)

    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT email FROM user_accounts WHERE email = ?", (normalized_email,)).fetchone()
        if row is None:
            raise ValueError("User not found.")

        conn.execute(
            "UPDATE user_accounts SET password_hash = ?, must_change_password = 0, updated_at = ? WHERE email = ?",
            (_hash_password(validated_password), now, normalized_email),
        )
        conn.execute("DELETE FROM user_sessions WHERE email = ?", (normalized_email,))
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def admin_reset_user_password(email: str, new_password: str) -> dict[str, Any]:
    """Admin-only password reset — bypasses security question, forces must_change_password."""
    normalized_email = _validate_corporate_email(email)
    validated_password = _validate_password_strength(new_password)
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT email FROM user_accounts WHERE email = ?", (normalized_email,)).fetchone()
        if row is None:
            raise ValueError("User not found.")
        conn.execute(
            "UPDATE user_accounts SET password_hash = ?, must_change_password = 1, updated_at = ? WHERE email = ?",
            (_hash_password(validated_password), now, normalized_email),
        )
        conn.execute("DELETE FROM user_sessions WHERE email = ?", (normalized_email,))
        conn.commit()
    return get_user_by_email(normalized_email) or {}


def create_user_session(email: str) -> str:
    normalized_email = _validate_corporate_email(email)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = now + timedelta(hours=SESSION_DURATION_HOURS)
    session_token = secrets.token_urlsafe(32)
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute(
            "DELETE FROM user_sessions WHERE expires_at <= ? OR email = ?",
            (now.isoformat(), normalized_email),
        )
        conn.execute(
            "INSERT INTO user_sessions(session_token_hash, email, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_session_hash(session_token), normalized_email, now.isoformat(), expires_at.isoformat()),
        )
        conn.commit()
    return session_token


def get_session_user(session_token: str) -> dict[str, Any] | None:
    hashed_token = _session_hash(session_token)
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute(
            """
            SELECT u.email, u.full_name, u.is_admin, u.is_active, u.must_change_password,
                   u.designation,
                   (CASE WHEN u.signature_blob IS NOT NULL AND length(u.signature_blob) > 0 THEN 1 ELSE 0 END) AS has_signature,
                   (CASE WHEN u.security_question != '' AND u.security_answer_hash != '' THEN 1 ELSE 0 END) AS has_security_question,
                   u.created_at, u.updated_at, u.created_by
            FROM user_sessions s
            JOIN user_accounts u ON u.email = s.email
            WHERE s.session_token_hash = ? AND s.expires_at > ?
            """,
            (hashed_token, now),
        ).fetchone()
        conn.execute("DELETE FROM user_sessions WHERE expires_at <= ?", (now,))
        conn.commit()
    if row is None or not bool(row["is_active"]):
        return None
    return _sanitize_user_row(row)


def delete_user_session(session_token: str) -> None:
    hashed_token = _session_hash(session_token)
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        conn.execute("DELETE FROM user_sessions WHERE session_token_hash = ?", (hashed_token,))
        conn.commit()


# ── DEQ Sections CRUD ────────────────────────────────────────────────────


def _row_to_deq_section(row: sqlite3.Row) -> dict[str, Any]:
    content_raw = str(row["content_json"] or "[]")
    try:
        content = json.loads(content_raw)
    except json.JSONDecodeError:
        content = []
    return {
        "id": int(row["id"]),
        "section_key": str(row["section_key"]),
        "heading": str(row["heading"]),
        "content_type": str(row["content_type"]),
        "content": content,
        "sort_order": int(row["sort_order"]),
        "is_visible": bool(row["is_visible"]),
        "is_system": bool(row["is_system"]),
    }


def list_deq_sections() -> list[dict[str, Any]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        rows = conn.execute(
            "SELECT * FROM deq_sections ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    return [_row_to_deq_section(row) for row in rows]


def get_deq_section(section_id: int) -> dict[str, Any] | None:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT * FROM deq_sections WHERE id = ?", (section_id,)).fetchone()
    return _row_to_deq_section(row) if row else None


def create_deq_section(
    heading: str,
    content_type: str = "list",
    content: list | None = None,
) -> dict[str, Any]:
    heading = str(heading).strip()
    if not heading:
        raise ValueError("Heading is required.")
    allowed_types = {"list", "paragraph", "table", "dynamic"}
    if content_type not in allowed_types:
        raise ValueError(f"Invalid content_type. Must be one of: {', '.join(sorted(allowed_types))}.")
    content_json = json.dumps(content or [], ensure_ascii=True)
    section_key = "deq_" + heading.lower().replace(" ", "_").replace("/", "_")[:40]
    now = _utcnow_iso()
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS mx FROM deq_sections").fetchone()["mx"]
        existing = conn.execute("SELECT id FROM deq_sections WHERE section_key = ?", (section_key,)).fetchone()
        if existing:
            section_key = f"{section_key}_{int(max_order) + 10}"
        conn.execute(
            "INSERT INTO deq_sections(section_key, heading, content_type, content_json, sort_order, is_visible, is_system, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?)",
            (section_key, heading, content_type, content_json, max_order + 10, now, now),
        )
        conn.commit()
        new_row = conn.execute("SELECT * FROM deq_sections WHERE section_key = ?", (section_key,)).fetchone()
    return _row_to_deq_section(new_row)


def update_deq_section(
    section_id: int,
    heading: str | None = None,
    content: list | None = None,
    is_visible: bool | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT * FROM deq_sections WHERE id = ?", (section_id,)).fetchone()
        if not row:
            raise ValueError(f"DEQ Section with id {section_id} not found.")
        updates: list[str] = []
        params: list[Any] = []
        if heading is not None:
            heading = str(heading).strip()
            if not heading:
                raise ValueError("Heading cannot be empty.")
            updates.append("heading = ?")
            params.append(heading)
        if content is not None:
            updates.append("content_json = ?")
            params.append(json.dumps(content, ensure_ascii=True))
        if is_visible is not None:
            updates.append("is_visible = ?")
            params.append(1 if is_visible else 0)
        if content_type is not None:
            allowed_types = {"list", "paragraph", "table", "dynamic"}
            if content_type not in allowed_types:
                raise ValueError(f"Invalid content_type. Must be one of: {', '.join(sorted(allowed_types))}.")
            updates.append("content_type = ?")
            params.append(content_type)
        if updates:
            updates.append("updated_at = ?")
            params.append(_utcnow_iso())
            params.append(section_id)
            conn.execute(
                f"UPDATE deq_sections SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
    return get_deq_section(section_id)


def delete_deq_section(section_id: int) -> bool:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    with _connect(resolved_path) as conn:
        row = conn.execute("SELECT is_system FROM deq_sections WHERE id = ?", (section_id,)).fetchone()
        if not row:
            raise ValueError(f"DEQ Section with id {section_id} not found.")
        if row["is_system"]:
            raise ValueError("System DEQ sections cannot be deleted. You can hide them instead.")
        conn.execute("DELETE FROM deq_sections WHERE id = ?", (section_id,))
        conn.commit()
    return True


def reorder_deq_sections(ordered_ids: list[int]) -> list[dict[str, Any]]:
    resolved_path = get_config_db_path()
    init_config_db(resolved_path)
    now = _utcnow_iso()
    with _connect(resolved_path) as conn:
        for idx, section_id in enumerate(ordered_ids):
            conn.execute(
                "UPDATE deq_sections SET sort_order = ?, updated_at = ? WHERE id = ?",
                ((idx + 1) * 10, now, section_id),
            )
        conn.commit()
    return list_deq_sections()
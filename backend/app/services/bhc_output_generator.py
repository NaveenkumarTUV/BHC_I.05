"""
bhc_output_generator.py
-----------------------
Generates BHC quotation documents for the BHC workflow.
The active application flow uses PDF output; legacy Excel and Word helpers remain
in this module but are not exposed by the current BHC routes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from backend.app.services.bhc_config_db import get_company_settings, get_document_settings

REFERENCE_PREFIX = "BEN-HC-TUVR"

SUPPORT_DOCUMENTS_REQUIRED = [
    "The client shall provide all available building documents, including architectural, structural, and service drawings, and shall grant access to all accessible areas of the building, including terraces, water tanks, basements, and service areas.",
    "The client shall ensure safe access arrangements for inspection, including provision of ladders, scaffolding, or suitable lifting equipment wherever required, and shall grant permission for photographic documentation and recording of observed defects.",
    "The client shall nominate an authorized representative to accompany the inspection team during the site visit and facilitate coordination during the inspection process.",
]

TIMELINE_TASKS = [
    {
        "sr_no": "1",
        "task": "Field Visit",
        "duration": "1-2 days after all arrangements are made prior to field visit",
    },
    {
        "sr_no": "2",
        "task": "Submission of Report",
        "duration": "2-3 days after completing site testing",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def format_quote_reference(sequence: int, generated_at: datetime | None = None) -> str:
    """Generate a daily quotation reference like BEN-HC-TUVR-20260401-0001."""
    stamp = generated_at or datetime.now()
    return f"{REFERENCE_PREFIX}-{stamp.strftime('%Y%m%d')}-{int(sequence):04d}"


def _ref_number(client_name: str = "") -> str:
    """Backward-compatible fallback for callers that do not supply a reference number."""
    return format_quote_reference(sequence=1)


def _format_inr(amount: float) -> str:
    """Format a number as Indian Rupees string."""
    return f"Rs. {amount:,.2f}"


def _pdf_safe(text: str) -> str:
    """
    Encode text to latin-1, replacing any non-encodable characters.
    Required because the legacy fpdf library only supports latin-1 internally.
    Common replacements: em/en dashes → hyphen, rupee sign → Rs., bullet → -.
    """
    replacements = {
        "\u2014": "--",   # em dash
        "\u2013": "-",    # en dash
        "\u2022": "-",    # bullet
        "\u20b9": "Rs.",  # rupee sign
        "\u2019": "'",    # right single quote
        "\u2018": "'",    # left single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2026": "...",  # ellipsis
        "\u00d7": "x",    # multiplication sign
        "\u00b2": "2",    # superscript 2
        "\u00b3": "3",    # superscript 3
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _proposal_subject(client: Dict[str, Any], pricing: Dict[str, Any]) -> str:
    location = client.get("Location") or "client premises"
    property_type = client.get("Property_Type") or "property"
    return (
        f"Building Health Checkup for the identified "
        f"{property_type} at {location}"
    )


def _background_paragraphs(client: Dict[str, Any], pricing: Dict[str, Any]) -> list[str]:
    client_name = client.get("Client_Name") or "the Client"
    subject = _proposal_subject(client, pricing)
    return [
        f"{client_name} (hereinafter referred to as the 'Client') is looking to appoint a consultant to carry out {subject} (hereinafter referred to as the 'Services').",
        f"Client has invited TÜV Rheinland (India) Pvt. Ltd. (hereinafter referred to as 'TUV-R' or 'Consultant') to submit an offer for {subject}, based on the discussions and enquiry details shared for the project.",
        "TÜV Rheinland (India) Pvt. Ltd. being in a position to provide such services is submitting this proposal for the kind consideration of the Client.",
    ]


# ---------------------------------------------------------------------------
# PDF Generator (fpdf)
# ---------------------------------------------------------------------------

def generate_quote_pdf(quote_data: Dict[str, Any], output_path: Path, *, include_signature: bool = True) -> Path:
    """Generate a BHC quotation PDF in the 3-page TÜV Rheinland format.

    Args:
        include_signature: When False the preparer's signature image is omitted
                           (used for preview mode).
    """
    from fpdf import FPDF

    client   = quote_data["client"]
    pricing  = quote_data["pricing"]
    ref_no   = quote_data.get("reference_number") or _ref_number(client.get("Client_Name", "CLIENT"))
    date_str = datetime.now().strftime("%d %B %Y")
    company_settings = get_company_settings()
    document_settings = get_document_settings()

    # TÜV Rheinland brand palette
    TUV_BLUE = (0, 100, 160)
    TUV_DARK = (0, 58, 92)
    NAVY = (0, 58, 92)
    BLACK = (0, 0, 0)
    GREY = (120, 120, 120)
    WHITE = (255, 255, 255)
    LIGHT_BG = (235, 243, 250)
    ACCENT_LIGHT = (79, 170, 213)
    TABLE_STRIPE = (245, 248, 252)

    # Locate logo
    _logo_path = output_path.parent.parent / "tuv_logo.png"
    if not _logo_path.exists():
        _logo_path = Path(__file__).resolve().parents[3] / "data" / "tuv_logo.png"
    logo_available = _logo_path.exists()

    class TuvPDF(FPDF):
        def header(self):
            # ── Navy header bar ──
            self.set_fill_color(*NAVY)
            self.rect(0, 0, 210, 20, "F")
            # TÜV blue accent line under header
            self.set_fill_color(*TUV_BLUE)
            self.rect(0, 20, 210, 1.5, "F")

            # Logo on the right
            if logo_available:
                try:
                    self.image(str(_logo_path), x=172, y=2, h=16)
                except Exception:
                    pass

            self.set_y(3)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*WHITE)
            self.cell(90, 6, _pdf_safe(company_settings["company_name"]), align="L")
            self.set_font("Helvetica", "B", 14)
            self.cell(60, 6, "QUOTATION", align="C")
            self.set_y(10)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(180, 210, 240)
            self.cell(90, 5, "Precisely Right.", align="L")
            self.set_text_color(*BLACK)
            self.ln(14)

        def footer(self):
            self.set_y(-22)
            self.set_draw_color(*TUV_BLUE)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(2)
            self.set_font("Helvetica", "", 6)
            self.set_text_color(*GREY)
            self.cell(0, 3, _pdf_safe(f"Quotation Ref: {ref_no}"), align="C", ln=True)
            self.cell(0, 3, _pdf_safe(company_settings["company_name"]), align="C", ln=True)
            self.cell(0, 3, _pdf_safe(company_settings["company_address"]), align="C", ln=True)
            self.set_font("Helvetica", "", 6)
            self.cell(95, 3, _pdf_safe(f"CIN No. U72501KA1996PTC020653"))
            self.cell(95, 3, _pdf_safe(f"Page {self.page_no()} of {{nb}}"), align="R")
            self.set_text_color(*BLACK)

    pdf = TuvPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=24)
    pdf.set_margins(15, 22, 15)

    # ═══════════════════════════════════════════════════════════════
    # PAGE 1
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()

    # ── Quotation Ref & Date ─────────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _pdf_safe(f"Quotation Ref: {ref_no}"), ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _pdf_safe(f"Date: {date_str}"), ln=True)
    pdf.ln(3)

    # ── Kind Attn ────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Kind Attn:", ln=True)
    pdf.ln(1)
    pdf.set_font("Helvetica", "BU", 9)
    pdf.cell(0, 5, _pdf_safe(client.get("Client_Name", "-")), ln=True)
    pdf.set_font("Helvetica", "U", 9)
    location = client.get("Location", "")
    if location:
        pdf.cell(0, 5, _pdf_safe(location), ln=True)
    phone_display = client.get("Phone_Number", "")
    if phone_display:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, _pdf_safe(f"Phone: {phone_display}"), ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _pdf_safe(f"Dear Sir/Madam,"), ln=True)
    pdf.ln(2)

    # ── Subject ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(15, 5, "Subject:")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(165, 5, _pdf_safe(_proposal_subject(client, pricing)))
    pdf.ln(2)

    # ── Reference / Background ───────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Reference:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for para in _background_paragraphs(client, pricing):
        pdf.multi_cell(180, 5, _pdf_safe(para))
        pdf.ln(1)
    pdf.ln(2)

    # ── I. Scope of Work ─────────────────────────────────────────
    def section_number_header(number: str, title: str):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        pdf.cell(10, 6, number)
        pdf.cell(0, 6, _pdf_safe(title), ln=True)
        # Blue accent underline
        pdf.set_draw_color(*TUV_BLUE)
        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 100, pdf.get_y())
        pdf.set_text_color(*BLACK)
        pdf.ln(2)

    section_number_header("I.", "Scope of Work:")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(10, 5, "")
    pdf.cell(0, 5, _pdf_safe(pricing.get("service_name", "")), ln=True)
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "", 9)
    for idx, item in enumerate(pricing.get("scope_of_work", []), start=1):
        pdf.cell(10, 5, "")
        pdf.cell(6, 5, f"{idx}.")
        pdf.multi_cell(160, 5, _pdf_safe(item))

    # Notes / Exclusions
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(10, 5, "")
    pdf.cell(30, 5, "Notes / Exclusions:")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(140, 5, _pdf_safe(
        "Statutory / Regulatory inspections / COC certifications are not considered as part of scope. "
        "The inspection is limited to visual assessment only."
    ))
    pdf.ln(2)

    # ── II. Deliverables ─────────────────────────────────────────
    section_number_header("II.", "Deliverables:")
    pdf.set_font("Helvetica", "", 9)
    deliverables = document_settings.get("deliverables", [])
    for item in deliverables:
        pdf.cell(14, 5, "")
        pdf.cell(4, 5, "-")
        pdf.multi_cell(160, 5, _pdf_safe(item))
    pdf.ln(2)

    # ── II-A. Proposed Timeline ──────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(14, 5, "")
    pdf.cell(0, 5, "Proposed Timeline:", ln=True)
    pdf.set_text_color(*BLACK)
    pdf.ln(1)
    # Table header
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.cell(14, 6, "")
    pdf.cell(15, 6, "  Sr.", fill=True, border=1)
    pdf.cell(55, 6, "  Task", fill=True, border=1)
    pdf.cell(86, 6, "  Duration", fill=True, border=1, ln=True)
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "", 8)
    for task in TIMELINE_TASKS:
        pdf.set_fill_color(*LIGHT_BG)
        pdf.cell(14, 6, "")
        pdf.cell(15, 6, _pdf_safe(f"  {task['sr_no']}"), fill=True, border=1)
        pdf.cell(55, 6, _pdf_safe(f"  {task['task']}"), fill=True, border=1)
        pdf.cell(86, 6, _pdf_safe(f"  {task['duration']}"), fill=True, border=1, ln=True)
    pdf.ln(3)

    # ── III. Fees ────────────────────────────────────────────────
    section_number_header("III.", "Fees:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(10, 5, "")
    pdf.cell(0, 5, "We propose the following fees for the above-mentioned services:", ln=True)
    pdf.ln(1)

    _fee_row_alt = [False]
    def fee_row(label: str, value: str, bold: bool = False, highlight: bool = False):
        style = "B" if bold else ""
        pdf.set_font("Helvetica", style, 9)
        if highlight:
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
        elif bold:
            pdf.set_fill_color(*LIGHT_BG)
            pdf.set_text_color(*NAVY)
        else:
            bg = TABLE_STRIPE if _fee_row_alt[0] else (255, 255, 255)
            pdf.set_fill_color(*bg)
            pdf.set_text_color(*BLACK)
        _fee_row_alt[0] = not _fee_row_alt[0]
        pdf.cell(14, 7, "")
        pdf.cell(96, 7, _pdf_safe(f"  {label}"), fill=True, border=1)
        pdf.cell(60, 7, _pdf_safe(f"  {value}"), fill=True, border=1, align="R", ln=True)
        pdf.set_text_color(*BLACK)

    fee_row("Applicable Area Slab", pricing.get("area_slab", "-"))
    fee_row("Built-up Area", f"{pricing.get('area_sqft', 0):,.0f} sq.ft")
    fee_row("Base Fee (excl. GST)", _format_inr(pricing.get("quoted_price", 0)))

    # Urgency surcharge
    if float(pricing.get("urgency_surcharge_amount", 0) or 0) > 0:
        surcharge_pct = float(pricing.get("urgency_surcharge_percent", 0))
        fee_row(f"Urgency Surcharge ({surcharge_pct:g}%)",
                _format_inr(pricing.get("urgency_surcharge_amount", 0)))

    # Discount
    if float(pricing.get("discount_amount", 0) or 0) > 0:
        discount_pct = float(pricing.get("discount_percent", 0))
        fee_row(f"Discount ({discount_pct:g}%)",
                f"- {_format_inr(abs(float(pricing.get('discount_amount', 0))))}")

    fee_row("Subtotal (excl. GST)", _format_inr(pricing.get("final_cost", 0)), bold=True)

    gst_pct = float(pricing.get("gst_percent", 18))
    gst_amount = float(pricing.get("gst_amount", 0))
    total_with_gst = float(pricing.get("total_with_gst", 0))

    fee_row(f"GST ({gst_pct:g}%)", _format_inr(gst_amount))
    fee_row("TOTAL QUOTATION AMOUNT (incl. GST)", _format_inr(total_with_gst), bold=True, highlight=True)

    pdf.ln(2)

    # ── Basis of Fees ────────────────────────────────────────────
    pdf.set_font("Helvetica", "BU", 9)
    pdf.cell(14, 5, "")
    pdf.cell(0, 5, "Basis of fees:", ln=True)
    pdf.set_font("Helvetica", "", 8)
    basis_of_fees = [
        f"All fees above are inclusive of GST @ {gst_pct:g}% as applicable.",
        "The above rates are applicable for Building Health Checkup / Inspection services.",
        "Above fees are lump-sum inclusive of inspection, mobilization-demobilization and local transport considering 8 hours of working on a normal working day.",
        "Additional hours will be charged at 1.5 times of normal man-day rates. For Saturdays, Sundays, Public Holidays and Night Shifts, charges shall be 1.5 times the normal man-day rates.",
        "In the event a visit is cancelled within 24-48 hours prior to the scheduled visit or for any abortive visit not attributable to TUV-R, applicable man-day rates shall be charged.",
        "At least 02-03 working days notification shall be provided to arrange inspection.",
    ]
    for idx, item in enumerate(basis_of_fees, start=1):
        pdf.cell(14, 4, "")
        pdf.cell(4, 4, "-")
        pdf.multi_cell(158, 4, _pdf_safe(item))
    pdf.ln(3)

    # ═══════════════════════════════════════════════════════════════
    # PAGE 2 (may flow from page 1 naturally due to auto page break)
    # ═══════════════════════════════════════════════════════════════

    # ── III-A. Support Documents Required ────────────────────────
    support_docs = pricing.get("support_documents", []) or SUPPORT_DOCUMENTS_REQUIRED
    if support_docs:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(14, 5, "")
        pdf.cell(0, 5, "Support Documents / Arrangements Required from Client:", ln=True)
        pdf.set_text_color(*BLACK)
        pdf.set_font("Helvetica", "", 8)
        for idx, item in enumerate(support_docs, start=1):
            pdf.cell(14, 4, "")
            pdf.cell(5, 4, f"{idx}.")
            pdf.multi_cell(157, 4, _pdf_safe(item))
        pdf.ln(3)

    # ── IV. Proposed Methodology ─────────────────────────────────
    section_number_header("IV.", "Proposed Methodology")
    pdf.set_font("Helvetica", "", 9)
    methodology_steps = [
        "TUV Rheinland India will appoint a Project Coordinator, who shall be the single point of contact for the entire assignment for general coordination.",
        "The client will provide an inspection call with a minimum of three (03) working days notice to our coordinator along with all required technical documentation.",
        "Our coordinator shall arrange the inspection and confirm with the client regarding the visit details.",
        "Our inspector will carry out the inspection as per the technical documentation provided by the client and submit observations to our coordinator.",
        "Our coordinator shall review the report and then submit it to the client with necessary supporting documentation.",
        "Reports shall be submitted within 24-48 working hours after completion of the inspection.",
        "Our coordinator will raise the invoice after submission of reports.",
        f"The client shall ensure the Health and Safety of {company_settings['company_name']} personnel while working at their facility by providing a safe working environment.",
    ]
    for idx, step in enumerate(methodology_steps, start=1):
        pdf.cell(10, 5, "")
        pdf.cell(6, 5, f"{idx}.")
        pdf.multi_cell(160, 5, _pdf_safe(step))
    pdf.ln(3)

    # ── V. Payment Terms ─────────────────────────────────────────
    section_number_header("V.", "Payment Terms:")
    pdf.set_font("Helvetica", "", 9)
    for idx, item in enumerate(document_settings.get("payment_terms", []), start=1):
        pdf.cell(10, 5, "")
        pdf.cell(6, 5, f"{idx}.")
        pdf.multi_cell(160, 5, _pdf_safe(item))
    pdf.ln(3)

    # ── VI. Terms & Conditions ───────────────────────────────────
    section_number_header("VI.", "Terms & Conditions:")
    pdf.set_font("Helvetica", "", 9)
    tc_text = (
        f"General terms and conditions of Business of {company_settings['company_name']} attached herewith, shall be an "
        f"integral part. The Terms & Conditions contained in this Quotation shall supersede all other Contractual "
        f"obligations entered between the Parties and shall be deemed as final and binding on the Parties. Both "
        f"TUV-R and the Customer/Client shall sign out the Quotation as a confirmation of their Business "
        f"Understanding and its acceptability to one another."
    )
    pdf.cell(10, 5, "")
    pdf.multi_cell(170, 5, _pdf_safe(tc_text))
    pdf.ln(1)
    # Additional terms
    for idx, item in enumerate(document_settings.get("other_terms", []), start=1):
        pdf.cell(10, 5, "")
        pdf.cell(6, 5, f"{idx}.")
        pdf.multi_cell(160, 5, _pdf_safe(item))
    pdf.ln(3)

    # ── VII. Validity ────────────────────────────────────────────
    section_number_header("VII.", "Validity:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(10, 5, "")
    pdf.multi_cell(170, 5, _pdf_safe(
        "Our proposal is valid for 60 days from the date of submission. The rates shall be firm for 01 MONTH "
        "from the date of acceptance of proposal or signing the contract."
    ))
    pdf.ln(1)
    pdf.cell(10, 5, "")
    pdf.multi_cell(170, 5, _pdf_safe(
        "We trust you will find the above offer competitive and look forward to be associated with you. In case "
        "you need any further clarifications or discussions, please contact us. We will be pleased to furnish the "
        "same promptly. Our other General Terms and Conditions are attached herewith."
    ))
    pdf.ln(4)

    # ── Signature Block (Page 2) ─────────────────────────────────
    prepared_by = quote_data.get("prepared_by") or {}
    preparer_name = prepared_by.get("full_name", "").strip()
    preparer_designation = prepared_by.get("designation", "").strip()
    preparer_signature: bytes | None = prepared_by.get("signature")

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Yours sincerely,", ln=True)
    pdf.ln(3)
    company_short = company_settings["company_name"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 5, _pdf_safe(f"For {company_short},"))
    pdf.cell(90, 5, _pdf_safe(f"For {company_short},"), ln=True)

    # Left side: preparer's signature image (if available and requested)
    sig_y = pdf.get_y()
    if include_signature and preparer_signature:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(preparer_signature)
            tmp_path = tmp.name
        try:
            pdf.image(tmp_path, x=15, y=sig_y + 1, h=10)
        except Exception:
            pass
        finally:
            import os as _os
            _os.unlink(tmp_path)
    pdf.ln(12)

    pdf.set_draw_color(*NAVY)
    pdf.line(15, pdf.get_y(), 90, pdf.get_y())
    pdf.line(110, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8)
    left_name = _pdf_safe(preparer_name) if preparer_name else "Sales Person Name & Signature"
    pdf.cell(90, 4, left_name)
    pdf.cell(90, 4, "Cost Centre / Operation Head Name & Signature", ln=True)
    pdf.set_font("Helvetica", "", 8)
    left_desig = _pdf_safe(preparer_designation) if preparer_designation else "Designation - Business Stream"
    pdf.cell(90, 4, left_desig)
    pdf.cell(90, 4, "Designation of Cost Centre / Operation Head", ln=True)
    pdf.ln(2)

    # ═══════════════════════════════════════════════════════════════
    # PAGE 3 – Acknowledgement / Order Acceptance
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "Acknowledgement / Order Acceptance:", ln=True)
    pdf.set_draw_color(*TUV_BLUE)
    pdf.set_line_width(0.6)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.set_text_color(*BLACK)
    pdf.ln(6)

    client_name = client.get("Client_Name", "the Client")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(180, 6, _pdf_safe(
        f"The quotation is hereby acknowledged and accepted by {client_name}."
    ))
    pdf.ln(12)

    # Signature columns
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 5, _pdf_safe(f"For, {client_name}"))
    pdf.cell(90, 5, _pdf_safe(f"For, {company_short},"), ln=True)
    pdf.ln(16)

    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.3)
    pdf.line(15, pdf.get_y(), 90, pdf.get_y())
    pdf.line(110, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 8)
    pdf.cell(90, 4, "Signature & Date of Client")
    pdf.cell(90, 4, "Signature & Date of Cost Centre / Operation Head", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "BU", 8)
    pdf.cell(90, 4, "Name & Designation of Client Representative")
    pdf.cell(90, 4, "Name & Designation of Cost Centre / Operation Head", ln=True)
    pdf.ln(16)

    # ── Company Profile (bottom of page 3) ───────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, "About Us:", ln=True)
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "", 8)
    for para in document_settings.get("company_profile_paragraphs", []):
        pdf.multi_cell(180, 4, _pdf_safe(para))
        pdf.ln(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path

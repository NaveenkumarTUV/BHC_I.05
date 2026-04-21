"""
bhc_output_generator.py
-----------------------
Generates BHC quotation documents for the BHC workflow.
The active application flow uses PDF output; legacy Excel and Word helpers remain
in this module but are not exposed by the current BHC routes.
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from backend.app.services.bhc_config_db import get_company_settings, get_document_settings, list_quotation_sections

REFERENCE_PREFIX = "BEN-HC-TUVR"
logger = logging.getLogger("bhc.output")


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
        f"Client has invited TUV Rheinland (India) Private Limited (hereinafter referred to as 'TUV-R' or 'Consultant') to submit an offer for {subject}, based on the discussions and enquiry details shared for the project.",
        f"TUV Rheinland (India) Private Limited being in a position to provide such services is submitting this proposal for the kind consideration of the Client.",
    ]


# ---------------------------------------------------------------------------
# PDF Generator (fpdf)
# ---------------------------------------------------------------------------

def generate_quote_pdf(quote_data: Dict[str, Any], output_path: Path, *, include_signature: bool = True) -> Path:
    """Generate a BHC quotation PDF using configurable quotation sections from DB."""
    from fpdf import FPDF

    client   = quote_data["client"]
    pricing  = quote_data["pricing"]
    ref_no   = quote_data.get("reference_number") or _ref_number(client.get("Client_Name", "CLIENT"))
    date_str = datetime.now().strftime("%d %B %Y")
    company_settings = get_company_settings()
    document_settings = get_document_settings()

    # Load all quotation sections from DB (ordered by sort_order)
    all_sections = list_quotation_sections()
    sections_map: Dict[str, Dict[str, Any]] = {s["section_key"]: s for s in all_sections}
    visible_sections = [s for s in all_sections if s["is_visible"]]

    # TÜV Rheinland brand palette
    NAVY = (0, 58, 92)
    TUV_BLUE = (0, 100, 160)
    BLACK = (0, 0, 0)
    GREY = (120, 120, 120)
    WHITE = (255, 255, 255)
    LIGHT_BG = (235, 243, 250)
    TABLE_STRIPE = (245, 248, 252)

    # Locate header logo — prefer quotation_logo.jpg as shown in the reference format
    import sys as _sys
    from backend.app.utils.paths import DATA_DIR
    _logo_render_path: Path | None = None
    _logo_temp_path: Path | None = None
    _logo_search_dirs: list[Path] = []
    if getattr(_sys, "frozen", False):
        _logo_search_dirs.append(Path(_sys._MEIPASS) / "data" / "assets")
    _logo_search_dirs.append(DATA_DIR / "assets")
    for _logo_dir in _logo_search_dirs:
        for _logo_name in ("quotation_logo.jpg", "quotation_logo.png", "tuv_logo.jpg", "tuv_logo.png"):
            _candidate = _logo_dir / _logo_name
            if _candidate.exists():
                _logo_render_path = _candidate
                break
        if _logo_render_path is not None:
            break

    if _logo_render_path is None:
        logger.warning("Header logo not found in data/assets/")
    else:
        logger.info("Header logo selected: %s", _logo_render_path)

    # fpdf validates PNG headers strictly; re-save any image as a valid PNG via Pillow.
    if _logo_render_path is not None:
        try:
            import tempfile as _tempfile
            from PIL import Image as _PilImage
            _im = _PilImage.open(_logo_render_path).convert("RGB")
            with _tempfile.NamedTemporaryFile(suffix=".png", delete=False) as _tmp:
                _tmp_name = _tmp.name
            _im.save(_tmp_name, format="PNG")
            _im.close()
            _logo_temp_path = Path(_tmp_name)
            _logo_render_path = _logo_temp_path
            logger.info("Logo converted to valid PNG -> %s", _tmp_name)
        except Exception:
            logger.exception("Logo PNG conversion failed; logo will be skipped")
            _logo_render_path = None

    class TuvPDF(FPDF):
        def header(self):
            # White header background matching reference format
            self.set_fill_color(*WHITE)
            self.rect(0, 0, 210, 22, "F")
            # Outer border around the header box
            self.set_draw_color(*NAVY)
            self.set_line_width(0.4)
            self.rect(10, 1, 190, 20)
            # Vertical divider after company name column (at x=75)
            self.line(85, 1, 85, 21)
            # Vertical divider before logo column (at x=150)
            self.line(150, 1, 150, 21)
            # Company name — left column, bold blue, centered
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*TUV_BLUE)
            self.set_xy(10, 5)
            self.cell(75, 11, _pdf_safe(company_settings["company_name"]), align="C")
            # QUOTATION — centre column, bold blue
            self.set_font("Helvetica", "B", 13)
            self.set_xy(85, 5)
            self.cell(65, 11, "QUOTATION", align="C")
            # Logo — right column
            if _logo_render_path is not None:
                try:
                    self.image(str(_logo_render_path), x=152, y=2, w=46, h=18)
                except Exception:
                    logger.exception("Header logo render failed for %s", _logo_render_path)
            self.set_text_color(*BLACK)
            self.ln(24)

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
            self.cell(95, 3, _pdf_safe("CIN No. U72501KA1996PTC020653"))
            self.cell(95, 3, _pdf_safe(f"Page {self.page_no()} of {{nb}}"), align="R")
            self.set_text_color(*BLACK)

    pdf = TuvPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.set_margins(15, 28, 15)

    # Section numbering counter
    _sec_counter = [0]

    def section_number_header(title: str, *, numbered: bool = True):
        if numbered:
            _sec_counter[0] += 1
            num_label = _roman(_sec_counter[0]) + "."
        else:
            num_label = ""
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        if num_label:
            pdf.cell(10, 6, num_label)
            pdf.cell(0, 6, _pdf_safe(title), ln=True)
        else:
            pdf.cell(0, 6, _pdf_safe(title), ln=True)
        pdf.set_text_color(*BLACK)
        pdf.ln(2)

    def _roman(n: int) -> str:
        vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        result = ""
        for v, s in vals:
            while n >= v:
                result += s
                n -= v
        return result

    # ── Helper renderers per content_type ──

    def render_numbered_list(items: list, indent: int = 10, font_size: int = 9):
        pdf.set_font("Helvetica", "", font_size)
        for idx, item in enumerate(items, start=1):
            pdf.cell(indent, 5, "")
            pdf.cell(6, 5, f"{idx}.")
            pdf.multi_cell(160, 5, _pdf_safe(str(item)))

    def render_bullet_list(items: list, indent: int = 14, font_size: int = 8):
        pdf.set_font("Helvetica", "", font_size)
        for item in items:
            pdf.cell(indent, 4, "")
            pdf.cell(4, 4, "-")
            pdf.multi_cell(158, 4, _pdf_safe(str(item)))

    def render_paragraphs(items: list, indent: int = 10, font_size: int = 9):
        pdf.set_font("Helvetica", "", font_size)
        for para in items:
            pdf.cell(indent, 5, "")
            pdf.multi_cell(170, 5, _pdf_safe(str(para)))
            pdf.ln(1)

    def render_image_section(items: list):
        pdf.set_font("Helvetica", "", 9)
        for item in items:
            if isinstance(item, dict):
                image_path_raw = str(item.get("path") or item.get("image_path") or "").strip()
                caption = str(item.get("caption") or "").strip()
                width_mm = float(item.get("width_mm") or 120)
            else:
                image_path_raw = str(item or "").strip()
                caption = ""
                width_mm = 120

            if not image_path_raw:
                continue

            image_path = Path(image_path_raw)
            if not image_path.is_absolute():
                image_path = DATA_DIR / image_path_raw
            if not image_path.exists():
                continue

            width_mm = max(40.0, min(170.0, width_mm))
            x = (210 - width_mm) / 2.0
            try:
                pdf.image(str(image_path), x=x, y=pdf.get_y(), w=width_mm)
                # move cursor below image with a safe estimate for common image ratios
                estimated_h = width_mm * 0.65
                pdf.set_y(pdf.get_y() + estimated_h + 2)
                if caption:
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.cell(0, 4, _pdf_safe(caption), ln=True, align="C")
                    pdf.set_font("Helvetica", "", 9)
                pdf.ln(2)
            except Exception:
                continue

    def render_timeline_table(items: list):
        # Detect format: new multi-col with _col_headers, or legacy task/duration
        headers = None
        data_rows = list(items)
        if data_rows and isinstance(data_rows[0], dict) and data_rows[0].get("_col_headers"):
            hdr = data_rows[0]
            if isinstance(hdr.get("headers"), list):
                headers = [str(h) for h in hdr["headers"]]
            else:
                headers = [str(hdr.get("col1", "Column 1")), str(hdr.get("col2", "Column 2"))]
            data_rows = data_rows[1:]

        if headers is not None:
            # ── Generic N-column table (no Sr. no.) ──
            n = len(headers)
            indent = 14
            col_w = 156.0 / n
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
            pdf.cell(indent, 6, "")
            for i, h in enumerate(headers):
                pdf.cell(col_w, 6, f"  {_pdf_safe(h)}", fill=True, border=1, ln=(i == n - 1))
            pdf.set_text_color(*BLACK)
            pdf.set_font("Helvetica", "", 8)
            for row in data_rows:
                pdf.set_fill_color(*LIGHT_BG)
                pdf.cell(indent, 6, "")
                if isinstance(row.get("cells"), list):
                    cells = row["cells"]
                    for i in range(n):
                        val = str(cells[i]) if i < len(cells) else ""
                        pdf.cell(col_w, 6, f"  {_pdf_safe(val)}", fill=True, border=1, ln=(i == n - 1))
                else:
                    # Fallback: use task/duration keys for 2-col tables
                    vals = [str(row.get("task", "")), str(row.get("duration", ""))]
                    for i in range(n):
                        val = vals[i] if i < len(vals) else ""
                        pdf.cell(col_w, 6, f"  {_pdf_safe(val)}", fill=True, border=1, ln=(i == n - 1))
        else:
            # ── Legacy system timeline with Sr. no. column ──
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
            pdf.cell(14, 6, "")
            pdf.cell(15, 6, "  Sr.", fill=True, border=1)
            pdf.cell(55, 6, "  Task", fill=True, border=1)
            pdf.cell(86, 6, "  Duration", fill=True, border=1, ln=True)
            pdf.set_text_color(*BLACK)
            pdf.set_font("Helvetica", "", 8)
            for task in data_rows:
                pdf.set_fill_color(*LIGHT_BG)
                pdf.cell(14, 6, "")
                pdf.cell(15, 6, _pdf_safe(f"  {task.get('sr_no', '')}"), fill=True, border=1)
                pdf.cell(55, 6, _pdf_safe(f"  {task.get('task', '')}"), fill=True, border=1)
                pdf.cell(86, 6, _pdf_safe(f"  {task.get('duration', '')}"), fill=True, border=1, ln=True)

    # ── Dynamic section renderer for fees ──

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

    def render_fees_section():
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(10, 5, "")
        pdf.cell(0, 5, "We propose the following fees for the above-mentioned services:", ln=True)
        pdf.ln(1)
        fee_row("Applicable Area Slab", pricing.get("area_slab", "-"))
        fee_row("Built-up Area", f"{pricing.get('area_sqft', 0):,.0f} sq.ft")
        fee_row("Base Fee (excl. GST)", _format_inr(pricing.get("quoted_price", 0)))
        if float(pricing.get("urgency_surcharge_amount", 0) or 0) > 0:
            surcharge_pct = float(pricing.get("urgency_surcharge_percent", 0))
            fee_row(f"Urgency Surcharge ({surcharge_pct:g}%)",
                    _format_inr(pricing.get("urgency_surcharge_amount", 0)))
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
    pincode = client.get("Pincode", "")
    if location and pincode:
        pdf.cell(0, 5, _pdf_safe(f"{location} - {pincode}"), ln=True)
    elif location:
        pdf.cell(0, 5, _pdf_safe(location), ln=True)
    elif pincode:
        pdf.cell(0, 5, _pdf_safe(f"Pincode: {pincode}"), ln=True)
    phone_display = client.get("Phone_Number", "")
    if phone_display:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, _pdf_safe(f"Phone: {phone_display}"), ln=True)
    gst_number = str(client.get("GST_Number", "")).strip()
    if gst_number:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, _pdf_safe(f"GSTIN: {gst_number}"), ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _pdf_safe("Dear Sir/Madam,"), ln=True)
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

    # ═══════════════════════════════════════════════════════════════
    # Render all visible sections in sort_order
    # ═══════════════════════════════════════════════════════════════
    company_short = company_settings["company_name"]
    client_name = client.get("Client_Name", "the Client")

    for sec in visible_sections:
        key = sec["section_key"]
        heading = sec["heading"]
        content_type = sec["content_type"]
        content = sec.get("content", [])

        # ── Dynamic sections (content from quote data / document_settings) ──

        if key == "scope_of_work":
            section_number_header(heading + ":")
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
            pdf.ln(2)

        elif key == "notes_exclusions":
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(10, 5, "")
            pdf.cell(30, 5, _pdf_safe(heading + ":"))
            pdf.set_font("Helvetica", "", 9)
            text = content[0] if content else ""
            pdf.multi_cell(140, 5, _pdf_safe(str(text)))
            pdf.ln(2)

        elif key == "deliverables":
            section_number_header(heading + ":")
            pdf.set_font("Helvetica", "", 9)
            for item in document_settings.get("deliverables", []):
                pdf.cell(14, 5, "")
                pdf.cell(4, 5, "-")
                pdf.multi_cell(160, 5, _pdf_safe(item))
            pdf.ln(2)

        elif key == "timeline":
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*NAVY)
            pdf.cell(14, 5, "")
            pdf.cell(0, 5, _pdf_safe(heading + ":"), ln=True)
            pdf.set_text_color(*BLACK)
            pdf.ln(1)
            render_timeline_table(content)
            pdf.ln(3)

        elif key == "fees":
            section_number_header(heading + ":")
            render_fees_section()
            pdf.ln(2)

        elif key == "basis_of_fees":
            pdf.set_font("Helvetica", "BU", 9)
            pdf.cell(14, 5, "")
            pdf.cell(0, 5, _pdf_safe(heading + ":"), ln=True)
            render_bullet_list(content)
            pdf.ln(3)

        elif key == "support_documents":
            support_docs = pricing.get("support_documents", [])
            if support_docs:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*NAVY)
                pdf.cell(14, 5, "")
                pdf.cell(0, 5, _pdf_safe(heading + ":"), ln=True)
                pdf.set_text_color(*BLACK)
                render_numbered_list(support_docs, indent=14, font_size=8)
                pdf.ln(3)

        elif key == "methodology":
            section_number_header(heading)
            render_numbered_list(content)
            pdf.ln(3)

        elif key == "payment_terms":
            section_number_header(heading + ":")
            render_numbered_list(document_settings.get("payment_terms", []))
            pdf.ln(3)

        elif key == "terms_conditions":
            section_number_header(heading + ":")
            render_paragraphs(content)
            pdf.ln(1)
            # Additional terms from document settings
            other = document_settings.get("other_terms", [])
            if other:
                render_numbered_list(other)
            pdf.ln(3)

        elif key == "other_terms":
            # Rendered as part of terms_conditions above (dynamic from document_settings)
            pass

        elif key == "validity":
            section_number_header(heading + ":")
            render_paragraphs(content)
            pdf.ln(4)

        elif key == "acknowledgement":
            # Force new page for acknowledgement
            pdf.add_page()
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*NAVY)
            pdf.cell(0, 8, _pdf_safe(heading + ":"), ln=True)
            pdf.set_text_color(*BLACK)
            pdf.ln(6)
            ack_text = content[0] if content else f"The quotation is hereby acknowledged and accepted by {client_name}."
            ack_text = ack_text.replace("the Client", client_name)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(180, 6, _pdf_safe(ack_text))
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
            pdf.cell(90, 4, "Signature & Date of Authorized Signatory", ln=True)
            pdf.ln(6)
            pdf.set_font("Helvetica", "BU", 8)
            pdf.cell(90, 4, "Name & Designation of Client Representative")
            pdf.cell(90, 4, "Name & Designation of Authorized Signatory", ln=True)
            pdf.ln(16)

        elif key == "about_us":
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*NAVY)
            pdf.cell(0, 5, _pdf_safe(heading + ":"), ln=True)
            pdf.set_text_color(*BLACK)
            pdf.set_font("Helvetica", "", 8)
            for para in document_settings.get("company_profile_paragraphs", []):
                pdf.multi_cell(180, 4, _pdf_safe(para))
                pdf.ln(1)

        else:
            # ── Custom / generic sections ──
            section_number_header(heading + ":")
            if content_type == "list":
                render_numbered_list(content)
            elif content_type == "paragraph":
                render_paragraphs(content)
            elif content_type == "table":
                render_timeline_table(content)
            elif content_type == "image":
                render_image_section(content)
            pdf.ln(3)

        # ── Signature block before acknowledgement page ──
        if key == "validity":
            prepared_by = quote_data.get("prepared_by") or {}
            preparer_name = prepared_by.get("full_name", "").strip()
            preparer_designation = prepared_by.get("designation", "").strip()
            preparer_signature: bytes | None = prepared_by.get("signature")
            signature_applied = False

            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, "Yours sincerely,", ln=True)
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, _pdf_safe(f"For {company_short},"), ln=True)

            sig_y = pdf.get_y()
            if include_signature and preparer_signature:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(preparer_signature)
                    tmp_path = tmp.name
                try:
                    pdf.image(tmp_path, x=15, y=sig_y + 1, h=10)
                    signature_applied = True
                except Exception:
                    pass
                finally:
                    import os as _os
                    _os.unlink(tmp_path)
            pdf.ln(12)

            pdf.set_draw_color(*NAVY)
            pdf.line(15, pdf.get_y(), 90, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 8)
            left_name = _pdf_safe(preparer_name) if preparer_name else "Authorized Signatory"
            pdf.cell(0, 4, left_name, ln=True)
            pdf.set_font("Helvetica", "", 8)
            left_desig = _pdf_safe(preparer_designation) if preparer_designation else "Designation"
            pdf.cell(0, 4, left_desig, ln=True)
            if not signature_applied:
                pdf.set_font("Helvetica", "I", 7)
                pdf.cell(0, 4, _pdf_safe("Note: This is a system-generated quotation; signature is not required."), ln=True)
            pdf.ln(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    if _logo_temp_path is not None:
        try:
            os.unlink(_logo_temp_path)
        except OSError:
            pass
    return output_path

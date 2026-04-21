"""
deq_output_generator.py
-----------------------
Generates Detailed Examination Quotation (DEQ) PDFs.
DEQ quotations are linked to a BHC (Building Health Check-Up) quotation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from backend.app.services.bhc_config_db import (
    get_company_settings,
    get_document_settings,
    list_deq_sections,
)

DEQ_REFERENCE_PREFIX = "BEN-DE-TUVR"


def _format_inr(amount: float) -> str:
    return f"Rs. {amount:,.2f}"


def _pdf_safe(text: str) -> str:
    replacements = {
        "\u2014": "--", "\u2013": "-", "\u2022": "-", "\u20b9": "Rs.",
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u00d7": "x", "\u00b2": "2", "\u00b3": "3",
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_deq_pdf(
    deq_data: Dict[str, Any],
    output_path: Path,
    *,
    include_signature: bool = True,
) -> Path:
    """Generate a DEQ quotation PDF using configurable DEQ sections from DB."""
    from fpdf import FPDF

    record = deq_data["record"]
    ref_no = record.get("deq_reference_number", "BEN-DE-TUVR")
    bhc_ref = record.get("bhc_ref_number", "")
    client_name = record.get("client_name", "Client")
    phone = record.get("phone", "")
    property_type = record.get("property_type", "")
    area = float(record.get("area", 0) or 0)
    issue_description = record.get("issue_description", "")
    examination_type = record.get("examination_type", "Structural")
    deq_amount = float(record.get("deq_quoted_amount", 0) or 0)

    date_str = datetime.now().strftime("%d %B %Y")
    company_settings = get_company_settings()
    document_settings = get_document_settings()

    all_sections = list_deq_sections()
    visible_sections = [s for s in all_sections if s["is_visible"]]

    # Compute GST
    gst_pct = 18.0
    gst_amount = round(deq_amount * gst_pct / 100, 2)
    total_with_gst = round(deq_amount + gst_amount, 2)

    # Brand palette
    NAVY = (0, 58, 92)
    TUV_BLUE = (0, 100, 160)
    BLACK = (0, 0, 0)
    GREY = (120, 120, 120)
    WHITE = (255, 255, 255)
    LIGHT_BG = (235, 243, 250)
    TABLE_STRIPE = (245, 248, 252)

    from backend.app.utils.paths import get_logo_path
    _logo_path = get_logo_path()
    logo_available = _logo_path is not None

    company_short = company_settings["company_name"]

    class TuvPDF(FPDF):
        def header(self):
            self.set_fill_color(*NAVY)
            self.rect(0, 0, 210, 20, "F")
            self.set_fill_color(*TUV_BLUE)
            self.rect(0, 20, 210, 1.5, "F")
            self.set_y(3)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*WHITE)
            self.cell(90, 6, _pdf_safe(company_settings["company_name"]), align="L")
            self.set_font("Helvetica", "B", 13)
            self.cell(30, 6, "DEQ QUOTATION", align="C")
            if logo_available:
                try:
                    self.image(str(_logo_path), x=172, y=2, h=16)
                except Exception:
                    pass
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
            self.cell(0, 3, _pdf_safe(f"DEQ Ref: {ref_no}"), align="C", ln=True)
            self.cell(0, 3, _pdf_safe(company_settings["company_name"]), align="C", ln=True)
            self.cell(0, 3, _pdf_safe(company_settings["company_address"]), align="C", ln=True)
            self.set_font("Helvetica", "", 6)
            self.cell(95, 3, _pdf_safe("CIN No. U72501KA1996PTC020653"))
            self.cell(95, 3, _pdf_safe(f"Page {self.page_no()} of {{nb}}"), align="R")
            self.set_text_color(*BLACK)

    pdf = TuvPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=24)
    pdf.set_margins(15, 22, 15)

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

    def render_table(items: list):
        """Render a generic multi-column table (same as BHC renderer)."""
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
                cells = row.get("cells", [])
                for i in range(n):
                    val = str(cells[i]) if i < len(cells) else ""
                    pdf.cell(col_w, 6, f"  {_pdf_safe(val)}", fill=True, border=1, ln=(i == n - 1))
        else:
            for row in data_rows:
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(14, 5, "")
                pdf.multi_cell(166, 5, _pdf_safe(str(row)))

    def render_fees_section():
        _alt = [False]
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
                bg = TABLE_STRIPE if _alt[0] else (255, 255, 255)
                pdf.set_fill_color(*bg)
                pdf.set_text_color(*BLACK)
            _alt[0] = not _alt[0]
            pdf.cell(14, 7, "")
            pdf.cell(96, 7, _pdf_safe(f"  {label}"), fill=True, border=1)
            pdf.cell(60, 7, _pdf_safe(f"  {value}"), fill=True, border=1, align="R", ln=True)
            pdf.set_text_color(*BLACK)

        pdf.set_font("Helvetica", "", 9)
        pdf.cell(10, 5, "")
        pdf.cell(0, 5, "We propose the following fees for the above-mentioned services:", ln=True)
        pdf.ln(1)
        fee_row("Examination Type", _pdf_safe(examination_type))
        if area > 0:
            fee_row("Area", f"{area:,.0f} sq.ft")
        fee_row("Detailed Examination Fee (excl. GST)", _format_inr(deq_amount))
        fee_row(f"GST ({gst_pct:g}%)", _format_inr(gst_amount))
        fee_row("TOTAL QUOTATION AMOUNT (incl. GST)", _format_inr(total_with_gst), bold=True, highlight=True)

    # ═══════════════════════════════════════════════════════════════
    # PAGE 1
    # ═══════════════════════════════════════════════════════════════
    pdf.add_page()

    # Ref & Date
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, _pdf_safe(f"DEQ Ref: {ref_no}"), ln=True)
    if bhc_ref:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, _pdf_safe(f"Ref. to BHC Quotation: {bhc_ref}"), ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _pdf_safe(f"Date: {date_str}"), ln=True)
    pdf.ln(3)

    # Kind Attn
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Kind Attn:", ln=True)
    pdf.ln(1)
    pdf.set_font("Helvetica", "BU", 9)
    pdf.cell(0, 5, _pdf_safe(client_name), ln=True)
    if phone:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, _pdf_safe(f"Phone: {phone}"), ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Dear Sir/Madam,", ln=True)
    pdf.ln(2)

    # Subject
    subject_line = (
        f"Detailed Examination Quotation for {property_type} of {client_name}"
        if property_type else
        f"Detailed Examination Quotation for {client_name}"
    )
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(15, 5, "Subject:")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(165, 5, _pdf_safe(subject_line))
    pdf.ln(2)

    # Background
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Background:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    bg_paras = [
        f"Following the Building Health Check-Up assessment carried out for {client_name} "
        f"(BHC Quotation Ref: {bhc_ref}), certain deficiencies and structural concerns have been identified "
        f"that require detailed examination to establish the severity, extent and appropriate remediation measures." if bhc_ref else
        f"Following the Building Health Check-Up assessment carried out for {client_name}, "
        f"certain deficiencies and structural concerns have been identified "
        f"that require detailed examination to establish the severity, extent and appropriate remediation measures.",
    ]
    if issue_description:
        bg_paras.append(f"Issues identified: {issue_description}")
    bg_paras.append(
        f"TUV Rheinland (India) Private Limited is pleased to submit this proposal for the "
        f"Detailed Examination services for the kind consideration of {client_name}."
    )
    for para in bg_paras:
        pdf.multi_cell(180, 5, _pdf_safe(para))
        pdf.ln(1)
    pdf.ln(2)

    # ═══════════════════════════════════════════════════════════════
    # Render visible DEQ sections
    # ═══════════════════════════════════════════════════════════════
    for sec in visible_sections:
        key = sec["section_key"]
        heading = sec["heading"]
        content_type = sec["content_type"]
        content = sec.get("content", [])

        if key == "deq_fees":
            section_number_header(heading + ":")
            render_fees_section()
            pdf.ln(2)

        elif key == "deq_payment_terms":
            section_number_header(heading + ":")
            render_numbered_list(document_settings.get("payment_terms", []))
            pdf.ln(3)

        elif key == "deq_acknowledgement":
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

        elif key == "deq_validity":
            section_number_header(heading + ":")
            render_paragraphs(content)
            pdf.ln(4)

            # Signature block after validity
            prepared_by = deq_data.get("prepared_by") or {}
            preparer_name = prepared_by.get("full_name", "").strip()
            preparer_designation = prepared_by.get("designation", "").strip()
            preparer_signature: bytes | None = prepared_by.get("signature")

            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, "Yours sincerely,", ln=True)
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, _pdf_safe(f"For {company_short},"), ln=True)

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
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(0, 4, _pdf_safe(preparer_name) if preparer_name else "Authorized Signatory", ln=True)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 4, _pdf_safe(preparer_designation) if preparer_designation else "Designation", ln=True)
            pdf.ln(2)

        else:
            # Generic sections (list / paragraph / table)
            section_number_header(heading + ":")
            if content_type == "list":
                render_numbered_list(content)
            elif content_type == "paragraph":
                render_paragraphs(content)
            elif content_type == "table":
                render_table(content)
            pdf.ln(3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path

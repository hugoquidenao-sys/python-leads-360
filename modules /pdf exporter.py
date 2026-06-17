"""
exporters/pdf_exporter.py - Exportación de propuestas comerciales a PDF

Genera un PDF por empresa con la propuesta generada por IA,
usando ReportLab con formato profesional.
"""
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)

from config import OUTPUT_DIR
from utils.logger import logger


# ── Paleta de colores ─────────────────────────────────────────────────────────────
BLUE_DARK   = colors.HexColor("#1F3864")
BLUE_MED    = colors.HexColor("#2E75B6")
BLUE_LIGHT  = colors.HexColor("#D6E4F7")
RED_HOT     = colors.HexColor("#C00000")
ORANGE_WARM = colors.HexColor("#E07000")
GRAY_LIGHT  = colors.HexColor("#F2F2F2")
GRAY_MED    = colors.HexColor("#888888")

CLASS_COLORS = {
    "HOT":  RED_HOT,
    "WARM": ORANGE_WARM,
    "COLD": BLUE_MED,
}


def export_proposal_pdf(
    company:        dict,
    proposal_text:  str,
    score:          int,
    classification: str,
    email_text:     str = "",
    firm_name:      str = "Asesoría Contable & Tributaria",
) -> Path:
    """
    Genera un PDF con la propuesta comercial.

    Args:
        company:        dict con datos de la empresa
        proposal_text:  texto de la propuesta (generado por IA)
        score:          score del lead
        classification: COLD / WARM / HOT
        email_text:     correo sugerido (opcional, en segunda página)
        firm_name:      nombre de la asesoría

    Returns:
        Path al PDF generado
    """
    safe_name = re.sub(r"[^\w\-]", "_", company.get("name", "empresa"))
    filename   = f"propuesta_{safe_name}.pdf"
    output_path = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles  = _build_styles()
    content = _build_content(
        styles, company, proposal_text, score, classification, email_text, firm_name
    )

    doc.build(content)
    logger.info(f"✓ PDF generado: {output_path}")
    return output_path


# ── Estilos ───────────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontSize=20,
            textColor=BLUE_DARK,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=GRAY_MED,
            spaceAfter=16,
            fontName="Helvetica",
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Normal"],
            fontSize=12,
            textColor=BLUE_DARK,
            spaceBefore=12,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#333333"),
            spaceAfter=8,
            leading=14,
            fontName="Helvetica",
            alignment=TA_JUSTIFY,
        ),
        "badge": ParagraphStyle(
            "badge",
            parent=base["Normal"],
            fontSize=13,
            textColor=colors.white,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
    }


def _build_content(
    styles, company, proposal_text, score, classification, email_text, firm_name
) -> list:
    """Construye el contenido del PDF."""
    content = []
    cls_color = CLASS_COLORS.get(classification, BLUE_MED)

    # ── Banner superior ────────────────────────────────────────────────────────
    banner_data = [[
        Paragraph(f"<b>{firm_name}</b>", ParagraphStyle(
            "banner", fontSize=14, textColor=colors.white,
            fontName="Helvetica-Bold", alignment=TA_LEFT
        )),
        Paragraph(
            f"Score: {score}/100  |  {classification}",
            ParagraphStyle("banner_r", fontSize=12, textColor=colors.white,
                           fontName="Helvetica-Bold", alignment=TA_CENTER)
        ),
        Paragraph(
            datetime.now().strftime("%d/%m/%Y"),
            ParagraphStyle("banner_date", fontSize=10, textColor=colors.white,
                           fontName="Helvetica", alignment=TA_CENTER)
        ),
    ]]
    banner_table = Table(banner_data, colWidths=[3.5*inch, 2.5*inch, 1.5*inch])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_DARK),
        ("TEXTCOLOR",  (0, 0), (-1, -1), colors.white),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (0, -1), 16),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 16),
    ]))
    content.append(banner_table)
    content.append(Spacer(1, 0.3 * inch))

    # ── Título de la empresa ───────────────────────────────────────────────────
    content.append(Paragraph(
        f"PROPUESTA COMERCIAL", styles["title"]
    ))
    content.append(Paragraph(
        f"Preparada para: <b>{company.get('name', '')}</b>  |  "
        f"{company.get('city', '')}  |  {company.get('category', '')}",
        styles["subtitle"]
    ))
    content.append(HRFlowable(width="100%", thickness=2, color=cls_color))
    content.append(Spacer(1, 0.2 * inch))

    # ── Clasificación badge ────────────────────────────────────────────────────
    badge_data = [[
        Paragraph(f"⭐ Lead {classification}  —  Score de oportunidad: {score}/100",
                  styles["badge"])
    ]]
    badge_table = Table(badge_data, colWidths=[7.5 * inch])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), cls_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    content.append(badge_table)
    content.append(Spacer(1, 0.25 * inch))

    # ── Cuerpo de la propuesta ─────────────────────────────────────────────────
    _add_proposal_body(content, proposal_text, styles)

    # ── Pie de página ──────────────────────────────────────────────────────────
    content.append(Spacer(1, 0.3 * inch))
    content.append(HRFlowable(width="100%", thickness=1, color=GRAY_MED))
    content.append(Paragraph(
        f"<font size='8' color='#888888'>Documento generado por Python Leads 360 "
        f"el {datetime.now().strftime('%d/%m/%Y %H:%M')} — Uso interno</font>",
        ParagraphStyle("footer", fontSize=8, textColor=GRAY_MED,
                       alignment=TA_CENTER, fontName="Helvetica")
    ))

    # ── Segunda página: correo sugerido ───────────────────────────────────────
    if email_text and "[Error" not in email_text:
        from reportlab.platypus import PageBreak
        content.append(PageBreak())
        content.append(Paragraph("CORREO COMERCIAL SUGERIDO", styles["section"]))
        content.append(HRFlowable(width="100%", thickness=1, color=BLUE_MED))
        content.append(Spacer(1, 0.15 * inch))
        for line in email_text.split("\n"):
            if line.strip():
                content.append(Paragraph(line, styles["body"]))
            else:
                content.append(Spacer(1, 0.1 * inch))

    return content


def _add_proposal_body(content: list, proposal_text: str, styles: dict) -> None:
    """Parsea y formatea el texto de la propuesta."""
    for line in proposal_text.split("\n"):
        line = line.strip()
        if not line:
            content.append(Spacer(1, 0.08 * inch))
            continue

        # Líneas en MAYÚSCULAS → sección
        if line.isupper() and len(line) > 3:
            content.append(Paragraph(line, styles["section"]))
        # Ítems de lista
        elif line.startswith(("-", "•", "*")):
            content.append(Paragraph(
                f"• {line.lstrip('-•* ')}",
                ParagraphStyle("bullet", parent=styles["body"],
                               leftIndent=16, spaceAfter=4)
            ))
        # Texto numerado
        elif re.match(r"^\d+\.", line):
            content.append(Paragraph(
                line, ParagraphStyle("numbered", parent=styles["body"],
                                     leftIndent=16, spaceAfter=4)
            ))
        # Texto normal
        else:
            content.append(Paragraph(line, styles["body"]))

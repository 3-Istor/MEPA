from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_certificate_pdf(name: str, score: int, certificate_id: str, issued_date: str) -> bytes:
    buffer = BytesIO()
    width, height = landscape(A4)
    document = SimpleDocTemplate(
        buffer,
        pagesize=(width, height),
        leftMargin=24 * mm,
        rightMargin=24 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Certificat MEPA",
        author="Programme MEPA",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "CertificateTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=30,
        textColor=colors.HexColor("#000091"),
        alignment=1,
        spaceAfter=12,
    )
    body = ParagraphStyle(
        "CertificateBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=13,
        leading=19,
        alignment=1,
        textColor=colors.HexColor("#1f1f1f"),
    )
    name_style = ParagraphStyle(
        "CertificateName",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#000091"),
        spaceBefore=8,
        spaceAfter=8,
    )
    small = ParagraphStyle(
        "CertificateSmall",
        parent=body,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
    )

    story = []
    flag = Table([["", "", ""]], colWidths=[55 * mm, 55 * mm, 55 * mm], rowHeights=[5 * mm])
    flag.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#000091")),
        ("BACKGROUND", (1, 0), (1, 0), colors.white),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#E1000F")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8D8D8")),
    ]))
    story.extend([
        flag,
        Spacer(1, 10 * mm),
        Paragraph("PLATEFORME IA CLAIR - PROJET ETUDIANT MEPA", small),
        Spacer(1, 4 * mm),
        Paragraph("Certificat de sensibilisation à l'intelligence artificielle", title),
        Paragraph("Ce certificat atteste que", body),
        Paragraph(name, name_style),
        Paragraph(
            "a suivi le parcours de sensibilisation comprenant les capsules vidéo et leurs QCM, "
            "le laboratoire de prompts et les exercices de prévention contre les arnaques assistées par IA.",
            body,
        ),
        Spacer(1, 8 * mm),
    ])

    score_table = Table(
        [[Paragraph(f"Score obtenu : <b>{score}/100</b>", body), Paragraph("Seuil de validation : <b>70/100</b>", body)]],
        colWidths=[75 * mm, 75 * mm],
    )
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F6FF")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#000091")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DBE6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([
        score_table,
        Spacer(1, 10 * mm),
        Paragraph(
            "Compétences travaillées : esprit critique, protection des données, vérification de l'information, "
            "détection des manipulations et rédaction responsable de prompts.",
            body,
        ),
        Spacer(1, 11 * mm),
        Table(
            [[Paragraph(f"Certificat n° {certificate_id}<br/>Généré le {issued_date}", small),
              Paragraph("Signature fictive du programme MEPA<br/>____________________________", small)]],
            colWidths=[85 * mm, 85 * mm],
            style=TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]),
        ),
    ])

    def draw_border(canvas, _doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#000091"))
        canvas.setLineWidth(4)
        canvas.rect(10 * mm, 10 * mm, width - 20 * mm, height - 20 * mm)
        canvas.setStrokeColor(colors.HexColor("#E1000F"))
        canvas.setLineWidth(1.5)
        canvas.rect(13 * mm, 13 * mm, width - 26 * mm, height - 26 * mm)
        canvas.restoreState()

    document.build(story, onFirstPage=draw_border)
    return buffer.getvalue()

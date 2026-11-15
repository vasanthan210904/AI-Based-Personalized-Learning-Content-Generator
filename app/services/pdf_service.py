"""Professional PDF export for generated learning material (ReportLab)."""
from __future__ import annotations

import io
import re
from pathlib import Path
from xml.sax.saxutils import escape

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..constants import AI_MODES

FONT_DIR = Path(__file__).resolve().parent.parent / "static" / "fonts"

LATIN_REGULAR = "NotoSans"
LATIN_BOLD = "NotoSans-Bold"
DEV_REGULAR = "NotoSansDevanagari"
DEV_BOLD = "NotoSansDevanagari-Bold"

_fonts_ok = False


def _register_fonts() -> None:
    global _fonts_ok
    if LATIN_REGULAR in pdfmetrics.getRegisteredFontNames():
        _fonts_ok = True
        return
    files = {
        LATIN_REGULAR: "NotoSans-Regular.ttf",
        LATIN_BOLD: "NotoSans-Bold.ttf",
        DEV_REGULAR: "NotoSansDevanagari-Regular.ttf",
        DEV_BOLD: "NotoSansDevanagari-Bold.ttf",
    }
    try:
        for name, filename in files.items():
            path = FONT_DIR / filename
            if not path.exists():
                raise FileNotFoundError(filename)
            pdfmetrics.registerFont(TTFont(name, str(path)))
        _fonts_ok = True
    except Exception:  # pragma: no cover - missing assets fallback
        current_app.logger.warning("Bundled PDF fonts unavailable; falling back to Helvetica.")
        _fonts_ok = False


_register_fonts()

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+(?:[\s\u0900-\u097F]+)?")


def _font_names(bold: bool) -> tuple[str, str]:
    if _fonts_ok:
        return (LATIN_BOLD if bold else LATIN_REGULAR, DEV_BOLD if bold else DEV_REGULAR)
    return ("Helvetica-Bold" if bold else "Helvetica", "Helvetica-Bold" if bold else "Helvetica")


def rich(text, *, bold: bool = False) -> str:
    """Escape text and wrap Devanagari runs with a Devanagari font."""
    text = "" if text is None else str(text)
    latin_font, dev_font = _font_names(bold)
    if not _fonts_ok:
        return escape(text).replace("\n", "<br/>")

    parts: list[str] = []
    last = 0
    for match in DEVANAGARI_RE.finditer(text):
        parts.append(escape(text[last : match.start()]))
        parts.append(f'<font name="{dev_font}">{escape(match.group())}</font>')
        last = match.end()
    parts.append(escape(text[last:]))
    return "".join(parts).replace("\n", "<br/>")


def _styles():
    base = getSampleStyleSheet()
    latin, latin_bold = _font_names(False)[0], _font_names(True)[0]
    return {
        "brand": ParagraphStyle(
            "brand",
            parent=base["Normal"],
            fontName=latin_bold,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#4F46E5"),
            spaceAfter=2,
        ),
        "project": ParagraphStyle(
            "project",
            parent=base["Normal"],
            fontName=latin,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748B"),
        ),
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=latin_bold,
            fontSize=22,
            leading=27,
            textColor=colors.HexColor("#1E1B4B"),
            spaceAfter=4,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName=latin,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#475569"),
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=latin_bold,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#4338CA"),
            spaceBefore=14,
            spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontName=latin_bold,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=7,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=latin,
            fontSize=9.3,
            leading=14.2,
            textColor=colors.HexColor("#334155"),
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["BodyText"],
            fontName=latin,
            fontSize=9.3,
            leading=13.6,
            textColor=colors.HexColor("#334155"),
            leftIndent=14,
            bulletIndent=3,
            spaceAfter=3,
        ),
        "meta_label": ParagraphStyle(
            "meta_label",
            parent=base["Normal"],
            fontName=latin_bold,
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#64748B"),
        ),
        "meta_value": ParagraphStyle(
            "meta_value",
            parent=base["Normal"],
            fontName=latin,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0F172A"),
        ),
        "note": ParagraphStyle(
            "note",
            parent=base["Normal"],
            fontName=latin,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#92400E"),
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName=latin,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#94A3B8"),
        ),
    }


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 16 * mm, A4[0] - 18 * mm, 16 * mm)
    latin, _ = _font_names(False)
    canvas.setFont(latin, 7.5)
    canvas.setFillColor(colors.HexColor("#94A3B8"))
    canvas.drawString(18 * mm, 11 * mm, "LearnForge AI · Personalized Learning Document")
    canvas.drawRightString(A4[0] - 18 * mm, 11 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _bullets(items, styles, numbered: bool = False):
    story = []
    for index, item in enumerate(items, start=1):
        if not str(item).strip():
            continue
        bullet = f"{index}." if numbered else "•"
        story.append(
            Paragraph(rich(item), styles["bullet"], bulletText=bullet)
        )
    return story


def _section(title: str, number: int, styles):
    return Paragraph(f"{number:02d} &nbsp;{rich(title, bold=True)}", styles["h2"])


def build_content_pdf(record, student_name: str) -> io.BytesIO:
    """Build a clean multi-page PDF for a LearningContent record."""
    data = record.generated_content or {}
    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=22 * mm,
        title=f"{data.get('title') or record.title} - LearnForge AI",
        author="LearnForge AI",
        subject="Personalized learning material",
    )

    story = []
    latin_bold = _font_names(True)[0]
    latin_regular = _font_names(False)[0]

    brand = Table(
        [
            [
                Paragraph("LEARNFORGE AI", styles["brand"]),
                Paragraph("PERSONALIZED LEARNING DOCUMENT", styles["project"]),
            ]
        ],
        colWidths=[doc.width * 0.35, doc.width * 0.65],
    )
    brand.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor("#C7D2FE")),
            ]
        )
    )
    story.append(brand)
    story.append(Spacer(1, 10))
    story.append(Paragraph(rich(data.get("title") or record.title), styles["title"]))
    story.append(
        Paragraph(
            rich(
                f"{record.subject.subject_name if record.subject else ''} · "
                f"{record.learning_level} level · {record.content_type}"
            ),
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 9))

    generated = record.created_at.strftime("%d %B %Y, %H:%M UTC")
    mode_label = AI_MODES.get(record.ai_mode, AI_MODES["demo"])["label"]
    meta_rows = [
        [
            Paragraph("STUDENT", styles["meta_label"]),
            Paragraph(rich(student_name), styles["meta_value"]),
            Paragraph("SUBJECT", styles["meta_label"]),
            Paragraph(rich(record.subject.subject_name if record.subject else ""), styles["meta_value"]),
        ],
        [
            Paragraph("TOPIC", styles["meta_label"]),
            Paragraph(rich(record.topic.topic_name if record.topic else ""), styles["meta_value"]),
            Paragraph("LEVEL", styles["meta_label"]),
            Paragraph(rich(record.learning_level), styles["meta_value"]),
        ],
        [
            Paragraph("CONTENT TYPE", styles["meta_label"]),
            Paragraph(rich(record.content_type), styles["meta_value"]),
            Paragraph("STYLE", styles["meta_label"]),
            Paragraph(rich(record.explanation_style), styles["meta_value"]),
        ],
        [
            Paragraph("LANGUAGE", styles["meta_label"]),
            Paragraph(rich(record.language), styles["meta_value"]),
            Paragraph("GENERATED", styles["meta_label"]),
            Paragraph(generated, styles["meta_value"]),
        ],
        [
            Paragraph("MODE", styles["meta_label"]),
            Paragraph(rich(mode_label), styles["meta_value"]),
            Paragraph("", styles["meta_label"]),
            Paragraph("", styles["meta_value"]),
        ],
    ]
    meta = Table(meta_rows, colWidths=[26 * mm, doc.width / 2 - 26 * mm, 28 * mm, doc.width / 2 - 28 * mm])
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#F1F5F9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 8))

    if record.ai_mode != "live":
        note_text = record.ai_note or AI_MODES.get(record.ai_mode, AI_MODES["demo"])["description"]
        note = Table(
            [[Paragraph(rich(f"DEMO MODE · {note_text}"), styles["note"])]],
            colWidths=[doc.width],
        )
        note.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#FDE68A")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(note)
        story.append(Spacer(1, 6))
    else:
        story.append(
            Paragraph(
                rich(
                    "Generated live by AI. Always cross-check important facts against your course material."
                ),
                styles["footer"],
            )
        )

    section_no = 1
    if data.get("introduction"):
        story.append(_section("Introduction", section_no, styles))
        story.append(Paragraph(rich(data["introduction"]), styles["body"]))
        section_no += 1

    if data.get("learning_objectives"):
        story.append(_section("Learning Objectives", section_no, styles))
        story.extend(_bullets(data["learning_objectives"], styles))
        section_no += 1

    if data.get("basic_concepts"):
        story.append(_section("Basic Concepts", section_no, styles))
        for concept in data["basic_concepts"]:
            heading = concept.get("heading", "")
            explanation = concept.get("explanation", "")
            if heading:
                story.append(Paragraph(rich(heading, bold=True), styles["h3"]))
            if explanation:
                story.append(Paragraph(rich(explanation), styles["body"]))
        section_no += 1

    if data.get("detailed_explanation"):
        story.append(_section("Detailed Explanation", section_no, styles))
        for paragraph in re.split(r"\n\s*\n", str(data["detailed_explanation"])):
            if paragraph.strip():
                story.append(Paragraph(rich(paragraph.strip()), styles["body"]))
        section_no += 1

    if data.get("important_definitions"):
        story.append(_section("Important Definitions", section_no, styles))
        rows = [
            [
                Paragraph("<b>Term</b>", styles["h3"]),
                Paragraph("<b>Definition</b>", styles["h3"]),
            ]
        ]
        for item in data["important_definitions"]:
            rows.append(
                [
                    Paragraph(rich(item.get("term", ""), bold=True), styles["body"]),
                    Paragraph(rich(item.get("definition", "")), styles["body"]),
                ]
            )
        table = Table(rows, colWidths=[42 * mm, doc.width - 42 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
        section_no += 1

    if data.get("key_terms"):
        story.append(_section("Key Terms", section_no, styles))
        story.append(
            Paragraph(
                rich(" · ".join(str(term) for term in data["key_terms"])), styles["body"]
            )
        )
        section_no += 1

    if data.get("step_by_step"):
        story.append(_section("Step-by-Step Explanation", section_no, styles))
        story.extend(_bullets(data["step_by_step"], styles, numbered=True))
        section_no += 1

    if data.get("real_world_examples"):
        story.append(_section("Real-World Examples", section_no, styles))
        story.extend(_bullets(data["real_world_examples"], styles))
        section_no += 1

    if data.get("practical_applications"):
        story.append(_section("Practical Applications", section_no, styles))
        story.extend(_bullets(data["practical_applications"], styles))
        section_no += 1

    if data.get("advantages") or data.get("disadvantages"):
        story.append(_section("Advantages and Disadvantages", section_no, styles))
        adv = [Paragraph("<b>Advantages</b>", styles["h3"])]
        adv += [Paragraph(rich(f"• {item}"), styles["body"]) for item in data.get("advantages", [])]
        if not data.get("advantages"):
            adv.append(Paragraph("Not applicable for this topic.", styles["body"]))
        dis = [Paragraph("<b>Disadvantages</b>", styles["h3"])]
        dis += [Paragraph(rich(f"• {item}"), styles["body"]) for item in data.get("disadvantages", [])]
        if not data.get("disadvantages"):
            dis.append(Paragraph("Not applicable for this topic.", styles["body"]))
        columns = Table(
            [[adv, dis]],
            colWidths=[doc.width / 2 - 3 * mm, doc.width / 2 - 3 * mm],
            hAlign="LEFT",
        )
        columns.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F0FDF4")),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FEF2F2")),
                    ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(columns)
        section_no += 1

    if data.get("important_points"):
        story.append(_section("Important Points", section_no, styles))
        story.extend(_bullets(data["important_points"], styles))
        section_no += 1

    if data.get("summary"):
        story.append(_section("Summary", section_no, styles))
        story.append(Paragraph(rich(data["summary"]), styles["body"]))
        section_no += 1

    if data.get("revision_tips"):
        story.append(_section("Revision Tips", section_no, styles))
        story.extend(_bullets(data["revision_tips"], styles))
        section_no += 1

    if data.get("faqs"):
        story.append(_section("Frequently Asked Questions", section_no, styles))
        for faq in data["faqs"]:
            block = [
                Paragraph(rich(f"Q: {faq.get('question', '')}", bold=True), styles["h3"]),
                Paragraph(rich(f"A: {faq.get('answer', '')}"), styles["body"]),
            ]
            story.append(KeepTogether(block))

    destination = buffer
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    destination.seek(0)
    return destination

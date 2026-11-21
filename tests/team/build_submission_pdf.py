from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "pdf" / "Project_24I-3020_24I-3063_24I-3165_B.pdf"
PAGE_W, PAGE_H = A4
LEFT = RIGHT = 19 * mm
TOP = 20 * mm
BOTTOM = 18 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT


def plain(text: str) -> str:
    text = text.replace("\u2010", "-").replace("\u2011", "-")
    text = text.replace("\u2012", "-").replace("\u2013", "-")
    text = text.replace("\u2014", "-").replace("\u2212", "-")
    return text


def inline_markup(text: str) -> str:
    text = plain(text)
    token_re = re.compile(r"(`[^`]+`|\*\*.+?\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))")
    out: list[str] = []
    pos = 0
    for match in token_re.finditer(text):
        out.append(escape(text[pos:match.start()]).replace("\n", "<br/>"))
        token = match.group(0)
        if token.startswith("`"):
            out.append(f'<font name="Code">{escape(token[1:-1])}</font>')
        elif token.startswith("**"):
            out.append(f"<b>{escape(token[2:-2])}</b>")
        elif token.startswith("*"):
            out.append(f"<i>{escape(token[1:-1])}</i>")
        else:
            m = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", token)
            label, href = m.group(1), m.group(2)
            label = escape(label)
            href = escape(href, {"\"": "&quot;"})
            if href.startswith(("https://", "http://", "mailto:")):
                out.append(f'<link href="{href}" color="#176B87">{label}</link>')
            else:
                out.append(label)
        pos = match.end()
    out.append(escape(text[pos:]).replace("\n", "<br/>"))
    return "".join(out)


def cell_text(raw: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(inline_markup(raw.strip()), style)


def parse_table(lines: list[str], styles):
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-+:?", c.replace(" ", "")) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    cols = max(map(len, rows))
    rows = [r + [""] * (cols - len(r)) for r in rows]
    header = rows[0]
    body = rows[1:]
    if cols > 3:
        flow = []
        for n, row in enumerate(body, 1):
            card = [[Paragraph(f"<b>{inline_markup(header[i])}</b>", styles["TableKey"]),
                     cell_text(row[i], styles["TableCell"])] for i in range(cols)]
            title = Paragraph(f"<b>Record {n}</b>", styles["SmallHeading"])
            table = Table(card, colWidths=[34 * mm, CONTENT_W - 34 * mm], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF4F6")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D6DC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            flow.extend([KeepTogether([title, table]), Spacer(1, 5)])
        return flow
    data = [[cell_text(c, styles["TableHeader"]) for c in header]]
    data += [[cell_text(c, styles["TableCell"]) for c in row] for row in body]
    widths = [CONTENT_W / cols] * cols
    if cols == 2:
        widths = [CONTENT_W * 0.31, CONTENT_W * 0.69]
    elif cols == 3:
        widths = [CONTENT_W * 0.22, CONTENT_W * 0.45, CONTENT_W * 0.33]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B57")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F8")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D6DC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [table, Spacer(1, 7)]


def markdown_flows(path: Path, styles):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    flows = []
    paragraph: list[str] = []
    code: list[str] = []
    in_code = False
    i = 0

    def flush_paragraph():
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            flows.append(Paragraph(inline_markup(text), styles["BodyTextCustom"]))
            flows.append(Spacer(1, 4))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            flush_paragraph()
            if in_code:
                code_text = plain("\n".join(code))
                flows.append(Preformatted(code_text, styles["CodeBlock"], maxLineLength=100))
                flows.append(Spacer(1, 5))
                code.clear()
            in_code = not in_code
            i += 1
            continue
        if in_code:
            code.append(line)
            i += 1
            continue
        if not line.strip():
            flush_paragraph()
            i += 1
            continue
        if line.startswith("|"):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            flows.extend(parse_table(table_lines, styles))
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            style = styles.get(f"Heading{min(level, 3)}", styles["Heading3Custom"])
            flows.append(Paragraph(inline_markup(heading.group(2)), style))
            i += 1
            continue
        if line.startswith("---") and len(line.strip()) >= 3:
            flush_paragraph()
            flows.append(Spacer(1, 5))
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+[.)]\s+", line):
            flush_paragraph()
            m = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", line)
            flows.append(Paragraph("&#8226; " + inline_markup(m.group(1)), styles["ListCustom"]))
            i += 1
            continue
        if line.startswith("> "):
            flush_paragraph()
            flows.append(Paragraph(inline_markup(line[2:]), styles["QuoteCustom"]))
            i += 1
            continue
        paragraph.append(line)
        i += 1
    flush_paragraph()
    if in_code and code:
        flows.append(Preformatted(plain("\n".join(code)), styles["CodeBlock"], maxLineLength=100))
    return flows


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename, styles):
        super().__init__(str(filename), pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
                         topMargin=TOP, bottomMargin=BOTTOM, title="Libris Circulation SQE Report",
                         author="Libris SQE Team - Section B")
        frame = Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="normal")
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self.draw_page)])
        self.styles = styles

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D5E0E5"))
        canvas.setLineWidth(0.6)
        canvas.line(LEFT, PAGE_H - 13 * mm, PAGE_W - RIGHT, PAGE_H - 13 * mm)
        canvas.setFont("Arial", 8)
        canvas.setFillColor(colors.HexColor("#536B78"))
        canvas.drawString(LEFT, PAGE_H - 10 * mm, "LIBRIS / SOFTWARE QUALITY ENGINEERING")
        canvas.line(LEFT, 12 * mm, PAGE_W - RIGHT, 12 * mm)
        canvas.drawString(LEFT, 7.5 * mm, "Section B | 21 November 2026 | Release recommendation: HOLD")
        canvas.drawRightString(PAGE_W - RIGHT, 7.5 * mm, f"Page {doc.page}")
        canvas.restoreState()


def main():
    root = ROOT
    font_dir = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("Arial", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(font_dir / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Code", str(font_dir / "consola.ttf")))
    base = getSampleStyleSheet()
    styles = {
        "CoverTitle": ParagraphStyle("CoverTitle", fontName="Arial-Bold", fontSize=27, leading=33,
            textColor=colors.HexColor("#173B57"), alignment=TA_LEFT, spaceAfter=10),
        "CoverSub": ParagraphStyle("CoverSub", fontName="Arial", fontSize=13, leading=19,
            textColor=colors.HexColor("#426273"), spaceAfter=5),
        "BodyTextCustom": ParagraphStyle("BodyTextCustom", parent=base["BodyText"], fontName="Arial",
            fontSize=9, leading=13, textColor=colors.HexColor("#1E2E36"), alignment=TA_LEFT,
            spaceAfter=3, splitLongWords=1),
        "Heading1": ParagraphStyle("Heading1Custom", fontName="Arial-Bold", fontSize=18, leading=23,
            textColor=colors.HexColor("#173B57"), spaceBefore=10, spaceAfter=8, keepWithNext=True),
        "Heading2": ParagraphStyle("Heading2Custom", fontName="Arial-Bold", fontSize=13, leading=17,
            textColor=colors.HexColor("#176B87"), spaceBefore=9, spaceAfter=5, keepWithNext=True),
        "Heading3": ParagraphStyle("Heading3Custom", fontName="Arial-Bold", fontSize=10.5, leading=14,
            textColor=colors.HexColor("#23485D"), spaceBefore=7, spaceAfter=4, keepWithNext=True),
        "Heading3Custom": ParagraphStyle("Heading3Fallback", fontName="Arial-Bold", fontSize=10.5,
            leading=14, textColor=colors.HexColor("#23485D"), spaceBefore=7, spaceAfter=4, keepWithNext=True),
        "TableHeader": ParagraphStyle("TableHeader", fontName="Arial-Bold", fontSize=7.6, leading=9.4,
            textColor=colors.white),
        "TableCell": ParagraphStyle("TableCell", fontName="Arial", fontSize=7.2, leading=9.2,
            textColor=colors.HexColor("#1E2E36"), splitLongWords=1),
        "TableKey": ParagraphStyle("TableKey", fontName="Arial", fontSize=7, leading=9,
            textColor=colors.HexColor("#1E2E36"), splitLongWords=1),
        "SmallHeading": ParagraphStyle("SmallHeading", fontName="Arial-Bold", fontSize=8.5,
            leading=11, textColor=colors.HexColor("#176B87"), spaceBefore=4, spaceAfter=3),
        "ListCustom": ParagraphStyle("ListCustom", fontName="Arial", fontSize=9, leading=12.5,
            leftIndent=12, firstLineIndent=-8, spaceAfter=2, textColor=colors.HexColor("#1E2E36")),
        "QuoteCustom": ParagraphStyle("QuoteCustom", fontName="Arial", fontSize=8.5, leading=12,
            leftIndent=14, borderColor=colors.HexColor("#176B87"), borderWidth=1, borderPadding=5,
            textColor=colors.HexColor("#426273"), spaceAfter=5),
        "CodeBlock": ParagraphStyle("CodeBlock", fontName="Code", fontSize=7, leading=9,
            backColor=colors.HexColor("#F2F5F6"), borderColor=colors.HexColor("#D5E0E5"),
            borderWidth=0.5, borderPadding=5, leftIndent=4, rightIndent=4, spaceAfter=5),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    story = [Spacer(1, 35 * mm),
             Paragraph("Libris Circulation<br/>Test Completion &amp; Quality Evidence", styles["CoverTitle"]),
             Spacer(1, 5 * mm),
             Paragraph("Section B | Final group submission draft", styles["CoverSub"]),
             Spacer(1, 4 * mm),
             Paragraph("Abdullah Adnan - 24I-3020<br/>Muhammad Shaheer - 24I-3063<br/>Taha Sohail - 24I-3165", styles["CoverSub"]),
             Spacer(1, 10 * mm)]
    band = Table([[Paragraph("RELEASE DECISION: HOLD", ParagraphStyle("Hold", fontName="Arial-Bold",
                  fontSize=15, leading=19, textColor=colors.white))]], colWidths=[CONTENT_W])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#9D3C36")),
                              ("LEFTPADDING", (0, 0), (-1, -1), 12),
                              ("TOPPADDING", (0, 0), (-1, -1), 10),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story += [band, Spacer(1, 12 * mm),
              Paragraph("Prepared 21 November 2026", styles["CoverSub"]),
              Paragraph("Public repository: https://github.com/Artfever/libris-SQE-Project", styles["BodyTextCustom"]),
              Paragraph("This report includes Phase 4 results and Phase 5 follow-up. Release remains on HOLD pending MySQL concurrency, a post-fix passive ZAP scan, and team-member verification and viva evidence.", styles["BodyTextCustom"]),
              PageBreak()]

    sections = [
        ("TEST_COMPLETION_REPORT.md", "Completion report"),
        ("PHASE4_REPORT.md", "Phase 4 quality evidence"),
        ("TEST_BASIS.md", "Test basis and requirements"),
        ("USE_CASES.md", "Circulation use cases"),
        ("TEST_PLAN.md", "Risk-based test plan and release criteria"),
        ("TRACEABILITY_ESTIMATE.md", "Traceability and estimates"),
        ("evidence/api-integration-2026-11-21.md", "API integration evidence"),
        ("evidence/defect-quality-metrics-2026-11-21.md", "Defect analyses and weekly metrics"),
        ("evidence/phase5-findings-remediation-2026-11-21.md", "Phase 5 finding triage and fixes"),
        ("evidence/pitest/README.md", "Mutation analysis"),
        ("evidence/sonarqube/README.md", "SonarQube analysis"),
        ("AI_USE.md", "AI-use record"),
    ]
    for idx, (rel, title) in enumerate(sections):
        path = root / "tests" / "team" / rel
        if not path.is_file():
            raise FileNotFoundError(path)
        story.append(Paragraph(f"Appendix {chr(65 + idx)} - {escape(title)}", styles["Heading1"]))
        story.extend(markdown_flows(path, styles))
        if idx != len(sections) - 1:
            story.append(PageBreak())
    ReportDoc(OUT, styles).build(story)
    print(OUT)


if __name__ == "__main__":
    main()

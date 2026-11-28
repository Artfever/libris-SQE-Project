from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "pdf" / "Project_24I-3020_24I-3063_24I-3165_B.pdf"
REPO = "https://github.com/Artfever/libris-SQE-Project"
FAST_LOGO = Path(__file__).with_name("fast-logo-black.png")
PAGE_W, PAGE_H = A4
LEFT = RIGHT = TOP = BOTTOM = 25.4 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT


def plain(text: str) -> str:
    text = text.replace("\u2010", "-").replace("\u2011", "-")
    text = text.replace("\u2012", "-").replace("\u2013", "-")
    text = text.replace("\u2014", "-").replace("\u2212", "-")
    return text


def inline_markup(text: str, source: Path | None = None, revision: str = "main") -> str:
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
            out.append(f"<b>{inline_markup(token[2:-2], source, revision)}</b>")
        elif token.startswith("*"):
            out.append(f"<i>{inline_markup(token[1:-1], source, revision)}</i>")
        else:
            m = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", token)
            label, href = m.group(1), m.group(2)
            label = escape(label)
            if source is not None and not href.startswith(("https://", "http://", "mailto:", "#")):
                destination = (source.parent / href).resolve()
                if destination.is_relative_to(ROOT) and destination.exists():
                    route = "tree" if destination.is_dir() else "blob"
                    href = f"{REPO}/{route}/{revision}/{quote(destination.relative_to(ROOT).as_posix())}"
            href = escape(href, {"\"": "&quot;"})
            if href.startswith(("https://", "http://", "mailto:")):
                out.append(f'<link href="{href}"><u>{label}</u></link>')
            else:
                out.append(label)
        pos = match.end()
    out.append(escape(text[pos:]).replace("\n", "<br/>"))
    return "".join(out)


def parse_table(lines: list[str], styles, source: Path, revision: str):
    def markup(text: str) -> str:
        return inline_markup(text.strip(), source, revision)

    def cell_text(raw: str, style: ParagraphStyle) -> Paragraph:
        return Paragraph(markup(raw), style)

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
    risk_matrix = cols == 6 and header[0] == "Likelihood / impact"
    if cols > 4 and not risk_matrix:
        flow = []
        for row in body:
            card = [[Paragraph(f"<b>{markup(header[i])}</b>", styles["TableKey"]),
                     cell_text(row[i], styles["TableCell"])] for i in range(cols)]
            label_width = 37 * mm
            table = Table(card, colWidths=[label_width, CONTENT_W - label_width], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
                ("LINEBELOW", (0, -1), (-1, -1), 0.35, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            flow.extend([KeepTogether([table]), Spacer(1, 9)])
        return flow
    data = [[cell_text(c, styles["TableHeader"]) for c in header]]
    data += [[cell_text(c, styles["TableCell"]) for c in row] for row in body]
    widths = [CONTENT_W / cols] * cols
    if cols == 2:
        widths = [CONTENT_W * 0.31, CONTENT_W * 0.69]
    elif cols == 3:
        widths = [CONTENT_W * 0.22, CONTENT_W * 0.45, CONTENT_W * 0.33]
    elif cols == 4 and header[0] == "Release criterion":
        widths = [CONTENT_W * share for share in (0.17, 0.27, 0.36, 0.20)]
    elif risk_matrix:
        widths = [CONTENT_W * share for share in (0.18, 0.10, 0.10, 0.23, 0.24, 0.15)]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    rules = [
        ("LINEABOVE", (0, 0), (-1, 0), 0.65, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.55, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.55, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if len(data) > 2:
        rules.append(("LINEABOVE", (0, 2), (-1, -1), 0.25, colors.black))
    table.setStyle(TableStyle(rules))
    return [table, Spacer(1, 7)]


def markdown_flows(path: Path, styles, revision: str):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    # The generated section heading already names each imported document.
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    flows = []
    paragraph: list[str] = []
    code: list[str] = []
    in_code = False
    i = 0

    def markup(text: str) -> str:
        return inline_markup(text, path, revision)

    def flush_paragraph():
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            flows.append(Paragraph(markup(text), styles["BodyTextCustom"]))
            flows.append(Spacer(1, 4))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            flush_paragraph()
            if in_code:
                code_text = plain("\n".join(code))
                flows.append(Preformatted(code_text, styles["CodeBlock"], maxLineLength=84))
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
            flows.extend(parse_table(table_lines, styles, path, revision))
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            style = styles[f"Heading{max(2, min(level, 3))}"]
            flows.append(Paragraph(markup(heading.group(2)), style))
            i += 1
            continue
        if line.startswith("---") and len(line.strip()) >= 3:
            flush_paragraph()
            flows.append(Spacer(1, 5))
            i += 1
            continue
        unordered_list = re.match(r"^\s*[-*]\s+", line)
        ordered_list = re.match(r"^\s*\d+[.)]\s+", line)
        starts_with_one = re.match(r"^\s*1[.)]\s+", line)
        if unordered_list or (ordered_list and (not paragraph or starts_with_one)):
            flush_paragraph()
            m = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", line)
            marker = line.strip().split(maxsplit=1)[0] if ordered_list else "\u2022"
            item = [m.group(1)]
            i += 1
            while i < len(lines):
                continuation = lines[i]
                if not re.match(r"^\s{2,}\S", continuation):
                    break
                if re.match(r"^(?:[-*]|\d+[.)])\s+|^```", continuation.lstrip()):
                    break
                item.append(continuation.strip())
                i += 1
            flows.append(Paragraph(markup(" ".join(item)), styles["ListCustom"], bulletText=marker))
            continue
        if line.startswith("> "):
            flush_paragraph()
            flows.append(Paragraph(markup(line[2:]), styles["QuoteCustom"]))
            i += 1
            continue
        paragraph.append(line)
        i += 1
    flush_paragraph()
    if in_code and code:
        flows.append(Preformatted(plain("\n".join(code)), styles["CodeBlock"], maxLineLength=84))
    return flows


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename, styles):
        super().__init__(str(filename), pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
                         topMargin=TOP, bottomMargin=BOTTOM, title="Libris Circulation SQE Report",
                         author="Libris SQE Team - Section B")
        frame = Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="normal",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self.draw_page)])
        self.styles = styles

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and hasattr(flowable, "section_key"):
            title = flowable.getPlainText()
            key = flowable.section_key
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0)
            self.notify("TOCEntry", (0, title, self.page, key))

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.45)
        border_inset = 8 * mm
        canvas.rect(border_inset, border_inset,
                    PAGE_W - 2 * border_inset, PAGE_H - 2 * border_inset,
                    stroke=1, fill=0)
        if doc.page == 1:
            canvas.restoreState()
            return
        canvas.setFillColor(colors.black)
        canvas.setLineWidth(0.35)
        canvas.setFont("Report", 9)
        canvas.drawString(LEFT, PAGE_H - 15 * mm, "SE3002 | Software Quality Engineering")
        canvas.drawRightString(PAGE_W - RIGHT, PAGE_H - 15 * mm, "Libris Circulation")
        canvas.line(LEFT, PAGE_H - 18 * mm, PAGE_W - RIGHT, PAGE_H - 18 * mm)
        canvas.line(LEFT, 18 * mm, PAGE_W - RIGHT, 18 * mm)
        canvas.drawString(LEFT, 13 * mm, "FAST NUCES | Fall 2026 | Section B")
        canvas.drawRightString(PAGE_W - RIGHT, 13 * mm, f"Page {doc.page}")
        canvas.restoreState()


def main():
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    root = ROOT
    font_dir = Path("C:/Windows/Fonts")
    for name, filename in (("Report", "times.ttf"), ("Report-Bold", "timesbd.ttf"),
                           ("Report-Italic", "timesi.ttf"), ("Report-BoldItalic", "timesbi.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily("Report", normal="Report", bold="Report-Bold",
                                  italic="Report-Italic", boldItalic="Report-BoldItalic")
    pdfmetrics.registerFont(TTFont("Code", str(font_dir / "consola.ttf")))
    body = ParagraphStyle("ReportBody", fontName="Report", fontSize=11, leading=15,
                          alignment=TA_LEFT, textColor=colors.black, splitLongWords=1)

    def style(name, **options):
        return ParagraphStyle(name, parent=body, **options)

    styles = {
        "CoverTitle": style("CoverTitle", fontName="Report-Bold", fontSize=30,
                            leading=35, alignment=TA_CENTER, spaceAfter=7),
        "CoverUniversity": style("CoverUniversity", fontName="Report-Bold", fontSize=16,
                                 leading=20, alignment=TA_CENTER, spaceAfter=4),
        "CoverSub": style("CoverSubtitle", fontSize=14, leading=19, alignment=TA_CENTER, spaceAfter=4),
        "CoverMeta": style("CoverMeta", alignment=TA_CENTER, leading=17, spaceAfter=5),
        "BodyTextCustom": body,
        "Heading1": style("SectionHeading", fontName="Report-Bold", fontSize=20,
                          leading=25, spaceAfter=13, keepWithNext=True),
        "Heading2": style("Subheading", fontName="Report-Bold", fontSize=14,
                          leading=18, spaceBefore=12, spaceAfter=5, keepWithNext=True),
        "Heading3": style("MinorHeading", fontName="Report-Bold", fontSize=11.5,
                          leading=15, spaceBefore=9, spaceAfter=4, keepWithNext=True),
        "TableHeader": style("TableHeader", fontName="Report-Bold", fontSize=9.5, leading=12),
        "TableCell": style("TableCell", fontSize=9.5, leading=12),
        "TableKey": style("TableKey", fontSize=9.5, leading=12),
        "ListCustom": style("ReportList", leftIndent=24, bulletIndent=5,
                            bulletFontName="Report", bulletFontSize=11, spaceAfter=3),
        "QuoteCustom": style("ReportQuote", fontName="Report-Italic", leftIndent=15, spaceAfter=6),
        "CodeBlock": style("CodeBlock", fontName="Code", fontSize=8.5, leading=11,
                           leftIndent=7, rightIndent=7, spaceAfter=6),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    logo = Image(str(FAST_LOGO), width=62 * mm, height=30 * mm, kind="proportional")
    logo.hAlign = "CENTER"
    story = [
        Spacer(1, 12 * mm), logo, Spacer(1, 10 * mm),
        Paragraph("National University of Computer &amp; Emerging Sciences", styles["CoverUniversity"]),
        Paragraph("SE3002 | Software Quality Engineering", styles["CoverMeta"]),
        Paragraph("Fall 2026 | Section B", styles["CoverMeta"]),
        Spacer(1, 21 * mm),
        Paragraph("Libris Circulation", styles["CoverTitle"]),
        Paragraph("Final Project Report", styles["CoverSub"]),
        Paragraph("Test Completion and Quality Evidence", styles["CoverMeta"]),
        Spacer(1, 19 * mm),
        Paragraph("<b>Prepared by</b>", styles["CoverMeta"]),
        Paragraph("Abdullah Adnan (24I-3020)<br/>Muhammad Shaheer (24I-3063)<br/>"
                  "Taha Sohail (24I-3165)", styles["CoverMeta"]),
        Spacer(1, 14 * mm),
        Paragraph("27 November 2026", styles["CoverMeta"]),
        Paragraph(f'<link href="{REPO}"><u>{REPO}</u></link>', styles["CoverMeta"]),
        Paragraph(f"Repository revision {revision}", styles["CoverMeta"]),
        PageBreak(),
    ]

    contents = TableOfContents()
    contents.levelStyles = [style("ContentsEntry", fontSize=11, leading=19)]
    contents.dotsMinLevel = 0
    story.extend([Paragraph("Contents", styles["Heading1"]), contents, PageBreak()])

    sections = [
        ("RUBRIC_EVIDENCE.md", "Rubric and current execution evidence"),
        ("evidence/registration-2026-11-20.md", "Section B registration record"),
        ("ENVIRONMENT.md", "Reproducible environment and upstream baseline"),
        ("REPOSITORY_RULES.md", "Team and area ownership"),
        ("PHASE4_REPORT.md", "Phase 4 quality evidence"),
        ("TEST_BASIS.md", "Test basis and requirements"),
        ("USE_CASES.md", "Circulation use cases"),
        ("TEST_PLAN.md", "Risk-based test plan and release criteria"),
        ("TRACEABILITY_ESTIMATE.md", "Traceability and estimates"),
        ("unit/README.md", "Line, branch, MCC and MC/DC evidence"),
        ("api/README.md", "OpenAPI generator and integration instructions"),
        ("evidence/api-integration-2026-11-21.md", "API integration evidence"),
        ("evidence/defect-quality-metrics-2026-11-21.md", "Defect analyses and weekly metrics"),
        ("evidence/phase5-findings-remediation-2026-11-21.md", "Phase 5 finding triage and fixes"),
        ("evidence/central-takeover-2026-11-22.md", "Historical use-case consolidation and verification"),
        ("evidence/pitest/README.md", "Mutation analysis"),
        ("evidence/pitest/SURVIVOR_REVIEW.md", "Full mutant review"),
        ("evidence/sonarqube/README.md", "SonarQube analysis"),
        ("evidence/ci-gate-demonstration-2026-11-21.md", "Red and corrected pull requests"),
        ("AI_USE.md", "AI-use record"),
        ("RELEASE_DECISION.md", "Final release decision"),
    ]
    for idx, (rel, title) in enumerate(sections):
        path = root / "tests" / "team" / rel
        if not path.is_file():
            raise FileNotFoundError(path)
        heading = Paragraph(f"{idx + 1}. {escape(title)}", styles["Heading1"])
        heading.section_key = f"section-{idx + 1}"
        story.append(heading)
        story.extend(markdown_flows(path, styles, revision))
        if idx != len(sections) - 1:
            story.append(PageBreak())
    ReportDoc(OUT, styles).multiBuild(story)
    print(OUT)


if __name__ == "__main__":
    main()

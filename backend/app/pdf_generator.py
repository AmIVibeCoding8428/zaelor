"""Generates the downloadable Zaelor wealth plan PDF report via ReportLab.

Takes the already-computed structured plan (+ Claude memo) and the original
questionnaire input, and lays it out as a two-identity print document:

- Page 1 (Cover): a printed interpretation of the ZAELOR homepage — black
  background, Sora wordmark, gold accents.
- Page 2 onward (Report): an institutional wealth-advisory document — white
  background, EB Garamond for prose, Inter for anything numeric/tabular.

Purely presentational — no financial calculation happens here. All figures
are read straight from the already-computed `plan` dict.

Fonts: EB Garamond (serif, prose) + Inter (sans, tables/figures) + Sora
(cover only, matching the site). All three are Google Fonts variable fonts,
instantiated to static Regular/Bold/Italic TTFs with fonttools and vendored
under app/assets/fonts/ (OFL licensed) so they embed correctly — ReportLab
cannot use a variable font's weight axis directly.
"""

import io
import os
import re
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as canvas_module
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.lineplots import LinePlot

REPORT_VERSION = "v1.0"

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

_FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

_FONT_FILES = {
    "EBGaramond": "EBGaramond-Regular.ttf",
    "EBGaramond-Bold": "EBGaramond-Bold.ttf",
    "EBGaramond-Italic": "EBGaramond-Italic.ttf",
    "EBGaramond-BoldItalic": "EBGaramond-BoldItalic.ttf",
    "Inter": "Inter-Regular.ttf",
    "Inter-Bold": "Inter-Bold.ttf",
    "Sora": "Sora-Regular.ttf",
    "Sora-Medium": "Sora-Medium.ttf",
    "Sora-SemiBold": "Sora-SemiBold.ttf",
    "Sora-Bold": "Sora-Bold.ttf",
    "Sora-ExtraBold": "Sora-ExtraBold.ttf",
}


def _register_fonts():
    for name, filename in _FONT_FILES.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(_FONT_DIR, filename)))

    pdfmetrics.registerFontFamily(
        "EBGaramond",
        normal="EBGaramond",
        bold="EBGaramond-Bold",
        italic="EBGaramond-Italic",
        boldItalic="EBGaramond-BoldItalic",
    )
    pdfmetrics.registerFontFamily(
        "Inter", normal="Inter", bold="Inter-Bold", italic="Inter", boldItalic="Inter-Bold"
    )


_register_fonts()

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

# Cover (matches the site exactly — see frontend/src/index.css).
COVER_BG = colors.HexColor("#080808")
COVER_TEXT = colors.HexColor("#FFFFFF")
COVER_SECONDARY = colors.HexColor("#9A9A9A")
GOLD = colors.HexColor("#C9A34E")

# Report pages — institutional, white/black/gold only.
INK = colors.HexColor("#161513")
INK_SECONDARY = colors.HexColor("#5B564D")
HAIRLINE = colors.HexColor("#DDD6C7")
PAGE_W, PAGE_H = A4
MARGIN_X = 2.2 * cm
MARGIN_TOP = 2.6 * cm
# US Letter (27.94cm tall) is 1.76cm shorter than A4 (29.7cm). Most print
# drivers top-anchor when the source page doesn't match the tray, so the
# deficit shows up as the bottom of the page being cropped. Keeping every
# bit of chrome at least ~2cm above the true A4 bottom edge means nothing
# is lost if this A4 PDF is ever printed "actual size" onto Letter stock.
MARGIN_BOTTOM = 3.3 * cm

DISCLAIMER_PARAGRAPHS = [
    "This report has been generated using information voluntarily provided by the user and a "
    "deterministic financial planning model. It is a planning illustration, not a certified "
    "financial statement.",
    "Monte Carlo simulations project a range of probabilistic outcomes based on historical and "
    "assumed market behavior. They are estimates only and do not guarantee future performance, "
    "positive or negative.",
    "Tax, FEMA, DTAA and other regulatory treatments referenced in this report reflect rules "
    "understood at the time of generation. These frameworks change over time and may not apply "
    "to your circumstances at the time of reading.",
    "All investments are subject to market risk, including the possible loss of principal. Past "
    "performance of any asset class is not indicative of future results.",
    "This report is intended strictly for educational and personal planning purposes. It does "
    "not constitute investment, tax, legal or financial advice of any kind.",
    "Before acting on any information in this report, you should consult a licensed financial "
    "advisor, chartered accountant, or tax counsel qualified to advise on your specific situation.",
]

# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------

COVER_WORDMARK = ParagraphStyle(
    "CoverWordmark", fontName="Sora-ExtraBold", fontSize=68, leading=68,
    textColor=COVER_TEXT, alignment=TA_CENTER, tracking=-0.5,
)
COVER_TAGLINE = ParagraphStyle(
    "CoverTagline", fontName="Sora-Medium", fontSize=17, leading=22,
    textColor=COVER_TEXT, alignment=TA_CENTER, spaceBefore=14,
)
COVER_SUPPORTING = ParagraphStyle(
    "CoverSupporting", fontName="Sora", fontSize=10.5, leading=16,
    textColor=COVER_SECONDARY, alignment=TA_CENTER, spaceBefore=8,
)
COVER_META_LABEL = ParagraphStyle(
    "CoverMetaLabel", fontName="Sora-SemiBold", fontSize=8, leading=12,
    textColor=GOLD, alignment=TA_CENTER, tracking=2,
)
COVER_META_VALUE = ParagraphStyle(
    "CoverMetaValue", fontName="Sora", fontSize=11, leading=15,
    textColor=COVER_TEXT, alignment=TA_CENTER, spaceAfter=16,
)

SECTION_EYEBROW = ParagraphStyle(
    "SectionEyebrow", fontName="Inter-Bold", fontSize=8.5, leading=11,
    textColor=GOLD, alignment=TA_LEFT, spaceAfter=4, tracking=2,
)
SECTION_TITLE = ParagraphStyle(
    "SectionTitle", fontName="EBGaramond-Bold", fontSize=22, leading=26,
    textColor=INK, alignment=TA_LEFT, spaceAfter=14,
)
SUBSECTION_TITLE = ParagraphStyle(
    "SubsectionTitle", fontName="EBGaramond-Bold", fontSize=13.5, leading=17,
    textColor=INK, alignment=TA_LEFT, spaceBefore=14, spaceAfter=8,
)
BODY = ParagraphStyle(
    "Body", fontName="EBGaramond", fontSize=11.3, leading=17,
    textColor=INK, alignment=TA_JUSTIFY, spaceAfter=9,
)
LEAD = ParagraphStyle(
    "Lead", parent=BODY, fontSize=12.5, leading=19, textColor=INK, spaceAfter=12,
)

# Memo headings — the Claude-generated advisory memo is markdown (#/##
# headings, **bold**, tables); levels 1-2 read as gold subheadings, 3+ as
# smaller ink subheadings, mirroring frontend/src/lib/markdownLite.jsx.
MEMO_HEADING_STYLES = {
    1: ParagraphStyle("MemoH1", fontName="EBGaramond-Bold", fontSize=16, leading=20, textColor=GOLD, spaceBefore=16, spaceAfter=8),
    2: ParagraphStyle("MemoH2", fontName="EBGaramond-Bold", fontSize=14, leading=18, textColor=GOLD, spaceBefore=14, spaceAfter=7),
    3: ParagraphStyle("MemoH3", fontName="EBGaramond-Bold", fontSize=12, leading=16, textColor=INK, spaceBefore=12, spaceAfter=6),
    4: ParagraphStyle("MemoH4", fontName="EBGaramond-Bold", fontSize=11.3, leading=15, textColor=INK, spaceBefore=10, spaceAfter=5),
}
MEMO_HEADING_STYLES[5] = MEMO_HEADING_STYLES[4]
MEMO_HEADING_STYLES[6] = MEMO_HEADING_STYLES[4]

FIGURE_HUGE = ParagraphStyle(
    "FigureHuge", fontName="Inter-Bold", fontSize=46, leading=48,
    textColor=GOLD, alignment=TA_LEFT,
)
FIGURE_LABEL = ParagraphStyle(
    "FigureLabel", fontName="Inter-Bold", fontSize=8, leading=11,
    textColor=INK_SECONDARY, alignment=TA_LEFT, tracking=1.5,
)
FIGURE_MED = ParagraphStyle(
    "FigureMed", fontName="Inter-Bold", fontSize=17, leading=20,
    textColor=INK, alignment=TA_LEFT,
)

KPI_VALUE = ParagraphStyle(
    "KpiValue", fontName="Inter-Bold", fontSize=15.5, leading=19,
    textColor=INK, alignment=TA_LEFT, spaceBefore=2,
)
KPI_VALUE_GOLD = ParagraphStyle("KpiValueGold", parent=KPI_VALUE, textColor=colors.HexColor("#A9812E"))

TABLE_HEADER = ParagraphStyle(
    "TableHeader", fontName="Inter-Bold", fontSize=8.3, leading=11,
    textColor=colors.white, alignment=TA_LEFT,
)
TABLE_CELL = ParagraphStyle(
    "TableCell", fontName="Inter", fontSize=8.8, leading=12.5,
    textColor=INK, alignment=TA_LEFT,
)
TABLE_CELL_BOLD = ParagraphStyle("TableCellBold", parent=TABLE_CELL, fontName="Inter-Bold")
TABLE_CELL_NOTE = ParagraphStyle(
    "TableCellNote", parent=TABLE_CELL, fontName="EBGaramond-Italic", fontSize=8.8, textColor=INK_SECONDARY,
)

BULLET = ParagraphStyle(
    "Bullet", fontName="EBGaramond", fontSize=11.3, leading=17,
    textColor=INK, alignment=TA_LEFT, leftIndent=14, spaceAfter=8,
    bulletFontName="EBGaramond-Bold", bulletFontSize=11.3, bulletIndent=0,
)

DISCLAIMER_TITLE = ParagraphStyle(
    "DisclaimerTitle", fontName="EBGaramond-Bold", fontSize=16, leading=20,
    textColor=INK, alignment=TA_LEFT, spaceAfter=12,
)
DISCLAIMER_BODY = ParagraphStyle(
    "DisclaimerBody", fontName="EBGaramond", fontSize=8.7, leading=13.5,
    textColor=INK_SECONDARY, alignment=TA_JUSTIFY, spaceAfter=8,
)

CAPTION = ParagraphStyle(
    "Caption", fontName="EBGaramond-Italic", fontSize=9, leading=13,
    textColor=INK_SECONDARY, alignment=TA_LEFT, spaceBefore=6,
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_inr(amount) -> str:
    """Format a number as an INR amount using Indian digit grouping, e.g. Rs 1,23,45,678."""
    if amount is None:
        return "N/A"
    amount = round(float(amount))
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))
    if len(digits) <= 3:
        grouped = digits
    else:
        last_three = digits[-3:]
        rest = digits[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        grouped = ",".join(parts) + "," + last_three
    return f"{sign}Rs {grouped}"


def _format_crores(amount) -> str:
    if amount is None:
        return "N/A"
    return f"Rs {float(amount) / 1e7:,.2f} Cr"


def _yes_no(value) -> str:
    return "Yes" if value else "No"


def _pct(value, decimals=1) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


# ---------------------------------------------------------------------------
# Markdown-lite — the Claude-generated memo is markdown (#/## headings,
# **bold**, tables, lists). This mirrors the block parser in
# frontend/src/lib/markdownLite.jsx so the PDF renders the same memo as
# formatted prose instead of dumping raw markdown syntax onto the page.
# ---------------------------------------------------------------------------

def _escape_xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline_markdown_to_xml(text: str) -> str:
    """Escapes XML special chars, then re-introduces **bold** as <b> tags —
    the small subset of ReportLab's mini-XML that Paragraph understands."""
    text = _escape_xml(text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") or (bool(line.strip()) and "|" in line)


def _is_table_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(re.match(r"^\|?[\s:|-]+\|?$", stripped)) and "-" in stripped


def _parse_table_row(line: str) -> list:
    stripped = line.strip()
    stripped = re.sub(r"^\|", "", stripped)
    stripped = re.sub(r"\|$", "", stripped)
    return [cell.strip() for cell in stripped.split("|")]


def _parse_markdown_blocks(markdown: str) -> list:
    lines = (markdown or "").split("\n")
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if line.strip() == "":
            i += 1
            continue

        if line.strip() == "---":
            blocks.append({"type": "hr"})
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            blocks.append({"type": "heading", "level": len(heading_match.group(1)), "text": heading_match.group(2)})
            i += 1
            continue

        if _is_table_row(line) and i + 1 < n and _is_table_separator(lines[i + 1]):
            header = _parse_table_row(line)
            rows = []
            i += 2
            while i < n and _is_table_row(lines[i]) and lines[i].strip() != "":
                rows.append(_parse_table_row(lines[i]))
                i += 1
            blocks.append({"type": "table", "header": header, "rows": rows})
            continue

        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            blocks.append({"type": "ul", "items": items})
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            blocks.append({"type": "ol", "items": items})
            continue

        paragraph_lines = []
        while (
            i < n
            and lines[i].strip() != ""
            and lines[i].strip() != "---"
            and not re.match(r"^#{1,6}\s+", lines[i])
            and not re.match(r"^\s*[-*]\s+", lines[i])
            and not re.match(r"^\s*\d+\.\s+", lines[i])
        ):
            paragraph_lines.append(lines[i])
            i += 1
        blocks.append({"type": "p", "text": " ".join(paragraph_lines)})

    return blocks


def _markdown_table_flowable(header: list, rows: list):
    num_cols = max(len(header), max((len(r) for r in rows), default=0))
    content_width = PAGE_W - 2 * MARGIN_X
    col_width = content_width / num_cols

    table_rows = [[Paragraph(_inline_markdown_to_xml(cell), TABLE_HEADER) for cell in header]]
    for row in rows:
        padded = row + [""] * (num_cols - len(row))
        table_rows.append([Paragraph(_inline_markdown_to_xml(cell), TABLE_CELL) for cell in padded])

    return _styled_table(table_rows, col_widths=[col_width] * num_cols)


def _render_markdown_lite(markdown: str) -> list:
    blocks = _parse_markdown_blocks(markdown)
    story = []

    for block in blocks:
        block_type = block["type"]

        if block_type == "heading":
            style = MEMO_HEADING_STYLES.get(block["level"], MEMO_HEADING_STYLES[4])
            story.append(Paragraph(_inline_markdown_to_xml(block["text"]), style))
        elif block_type == "hr":
            story.append(HRFlowable(width="100%", thickness=0.5, color=HAIRLINE, spaceBefore=8, spaceAfter=8))
        elif block_type == "ul":
            for item in block["items"]:
                story.append(Paragraph(_inline_markdown_to_xml(item), BULLET, bulletText="•"))
        elif block_type == "ol":
            for index, item in enumerate(block["items"], start=1):
                story.append(Paragraph(f"{index}. {_inline_markdown_to_xml(item)}", BULLET))
        elif block_type == "table":
            story.append(_markdown_table_flowable(block["header"], block["rows"]))
            story.append(Spacer(1, 0.25 * cm))
        else:
            story.append(Paragraph(_inline_markdown_to_xml(block["text"]), BODY))

    return story


# ---------------------------------------------------------------------------
# Cover page (Page 1)
# ---------------------------------------------------------------------------

def _cover_story(user_input: dict, generated_on: str) -> list:
    story = [
        Spacer(1, 6.2 * cm),
        Paragraph("ZAELOR", COVER_WORDMARK),
        HRFlowable(width=1.4 * cm, thickness=1.4, color=GOLD, hAlign="CENTER", spaceBefore=10, spaceAfter=10),
        Paragraph("Wealth Beyond Borders.", COVER_TAGLINE),
        Paragraph("AI-powered cross-border wealth planning for global Indians.", COVER_SUPPORTING),
        Spacer(1, 3.2 * cm),
    ]

    meta_rows = [
        ("PREPARED FOR", "Private Client"),
        ("REPORT GENERATED ON", generated_on),
        ("REPORT VERSION", REPORT_VERSION),
    ]
    for label, value in meta_rows:
        story.append(Paragraph(label, COVER_META_LABEL))
        story.append(Paragraph(value, COVER_META_VALUE))

    story.append(Spacer(1, 1.6 * cm))
    story.append(Paragraph("Private Wealth Advisory Report &middot; UAE Edition", COVER_SUPPORTING))
    story.append(Paragraph("100% anonymous &middot; no personal data collected or stored", COVER_SUPPORTING))
    return story


def _draw_cover_background(canvas, doc):
    """Runs via the Cover PageTemplate's onPage hook — i.e. before that
    page's flowables are drawn, so the fill sits behind the wordmark rather
    than painting over it."""
    canvas.saveState()
    canvas.setFillColor(COVER_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Report chrome — header / footer for page 2 onward
# ---------------------------------------------------------------------------

def _make_report_header_footer(generated_on: str):
    """Runs via the Report PageTemplate's onPage hook, before that page's
    flowables are drawn. Draws everything except the 'Page X of Y' label —
    the total page count isn't known until the whole story has been laid
    out, so that one piece is added afterwards by _ZaelorCanvas."""

    def _draw(canvas, doc):
        canvas.saveState()

        # Header
        canvas.setFont("Inter-Bold", 8.3)
        canvas.setFillColor(INK)
        canvas.drawString(MARGIN_X, PAGE_H - 1.5 * cm, "ZAELOR")
        canvas.setFont("Inter", 8.3)
        canvas.setFillColor(INK_SECONDARY)
        canvas.drawString(MARGIN_X + 1.15 * cm, PAGE_H - 1.5 * cm, "|  Private Wealth Advisory Report")
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(0.8)
        canvas.line(MARGIN_X, PAGE_H - 1.7 * cm, PAGE_W - MARGIN_X, PAGE_H - 1.7 * cm)

        # Footer — kept well clear of the true page-bottom edge (see
        # MARGIN_BOTTOM) so it survives printing on shorter US Letter stock.
        canvas.setStrokeColor(HAIRLINE)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN_X, 2.55 * cm, PAGE_W - MARGIN_X, 2.55 * cm)
        canvas.setFont("Inter", 7.6)
        canvas.setFillColor(INK_SECONDARY)
        canvas.drawString(MARGIN_X, 2.15 * cm, f"Generated {generated_on}")
        canvas.drawCentredString(PAGE_W / 2, 2.15 * cm, "Confidential")

        canvas.restoreState()

    return _draw


class _ZaelorCanvas(canvas_module.Canvas):
    """Buffers every page so the footer can print 'Page X of Y' — the total
    page count isn't known until the whole story has been laid out. Only
    adds that one label; the header/footer chrome itself is drawn per-page,
    before content, via each PageTemplate's onPage hook."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_report_pages = max(len(self._saved_page_states) - 1, 0)  # exclude cover
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self.saveState()
                self.setFont("Inter", 7.6)
                self.setFillColor(INK_SECONDARY)
                page_label = f"Page {self._pageNumber - 1} of {total_report_pages}"
                self.drawRightString(PAGE_W - MARGIN_X, 2.15 * cm, page_label)
                self.restoreState()
            canvas_module.Canvas.showPage(self)
        canvas_module.Canvas.save(self)


# ---------------------------------------------------------------------------
# Shared table styling
# ---------------------------------------------------------------------------

def _styled_table(rows, col_widths, header=True, align_numeric_from=None):
    table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, HAIRLINE),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, GOLD),
            ("TOPPADDING", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
        ]
    if align_numeric_from is not None:
        style.append(("ALIGN", (align_numeric_from, 0), (-1, -1), "RIGHT"))
    table.setStyle(TableStyle(style))
    return table


def _section_heading(eyebrow: str, title: str) -> list:
    return [
        Paragraph(eyebrow.upper(), SECTION_EYEBROW),
        Paragraph(title, SECTION_TITLE),
        HRFlowable(width="100%", thickness=0.8, color=GOLD, spaceAfter=16),
    ]


# ---------------------------------------------------------------------------
# Charts (vector — print resolution, correct aspect ratio, no rasterization)
# ---------------------------------------------------------------------------

def _monte_carlo_chart(monte_carlo: dict) -> Drawing:
    median = monte_carlo.get("median_case") or []
    best = monte_carlo.get("best_case") or []
    worst = monte_carlo.get("worst_case") or []

    width, height = 16.6 * cm, 8.6 * cm
    drawing = Drawing(width, height)

    plot = LinePlot()
    plot.x = 1.4 * cm
    plot.y = 1.1 * cm
    plot.width = width - 2.0 * cm
    plot.height = height - 2.0 * cm

    years = list(range(1, len(median) + 1))
    series_best = list(zip(years, best))
    series_median = list(zip(years, median))
    series_worst = list(zip(years, worst))
    plot.data = [series_best, series_median, series_worst]

    max_value = max(best) if best else 1

    def _cr_format(value):
        return f"{value / 1e7:,.1f} Cr"

    plot.yValueAxis.valueMin = 0
    plot.yValueAxis.valueMax = max_value * 1.08
    plot.yValueAxis.labelTextFormat = _cr_format
    plot.yValueAxis.labels.fontName = "Inter"
    plot.yValueAxis.labels.fontSize = 7.6
    plot.yValueAxis.labels.fillColor = INK_SECONDARY
    plot.yValueAxis.strokeColor = HAIRLINE
    plot.yValueAxis.gridStrokeColor = HAIRLINE
    plot.yValueAxis.visibleGrid = True
    plot.yValueAxis.gridStrokeWidth = 0.4

    plot.xValueAxis.valueMin = 1
    plot.xValueAxis.valueMax = years[-1] if years else 1
    plot.xValueAxis.labels.fontName = "Inter"
    plot.xValueAxis.labels.fontSize = 7.6
    plot.xValueAxis.labels.fillColor = INK_SECONDARY
    plot.xValueAxis.strokeColor = HAIRLINE

    # Best case — thin dashed line, muted.
    plot.lines[0].strokeColor = colors.HexColor("#8A8477")
    plot.lines[0].strokeWidth = 1
    plot.lines[0].strokeDashArray = (2, 2)
    plot.lines[0].symbol = None
    # Median — solid gold, the primary series.
    plot.lines[1].strokeColor = GOLD
    plot.lines[1].strokeWidth = 2.4
    plot.lines[1].symbol = None
    # Worst case — thin dashed line, muted.
    plot.lines[2].strokeColor = colors.HexColor("#B8B2A3")
    plot.lines[2].strokeWidth = 1
    plot.lines[2].strokeDashArray = (2, 2)
    plot.lines[2].symbol = None

    drawing.add(plot)

    # Hand-drawn legend, top-right, matching the report's restrained palette.
    legend_items = [("Median", GOLD, False), ("Best Case", colors.HexColor("#8A8477"), True), ("Worst Case", colors.HexColor("#B8B2A3"), True)]
    lx = width - 8.6 * cm
    ly = height - 0.35 * cm
    for label, color, dashed in legend_items:
        drawing.add(Line(lx, ly, lx + 0.55 * cm, ly, strokeColor=color, strokeWidth=2, strokeDashArray=(2, 2) if dashed else None))
        drawing.add(String(lx + 0.7 * cm, ly - 0.11 * cm, label, fontName="Inter", fontSize=7.6, fillColor=INK_SECONDARY))
        lx += 2.85 * cm

    return drawing


_ALLOCATION_SLICE_COLORS = [
    GOLD,
    colors.HexColor("#E8E4DA"),
    colors.HexColor("#9A9284"),
    colors.HexColor("#6B7280"),
    colors.HexColor("#4B4B4B"),
    colors.HexColor("#5C5648"),
]


def _allocation_pie(allocations: dict) -> Drawing:
    entries = sorted(allocations.items(), key=lambda kv: kv[1], reverse=True)

    # No on-slice labels — percentages already live in the legend table beside
    # it, and reportlab's Pie label placement can overflow the Drawing's
    # declared bounds and collide with surrounding flowables.
    size = 7.6 * cm
    drawing = Drawing(size, size)
    pie = Pie()
    pie.x = 0.2 * cm
    pie.y = 0.2 * cm
    pie.width = size - 0.4 * cm
    pie.height = size - 0.4 * cm
    pie.data = [value for _, value in entries]
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1.5
    for i, _ in enumerate(entries):
        pie.slices[i].fillColor = _ALLOCATION_SLICE_COLORS[i % len(_ALLOCATION_SLICE_COLORS)]
    drawing.add(pie)
    return drawing


def _allocation_legend_table(allocations: dict) -> Table:
    entries = sorted(allocations.items(), key=lambda kv: kv[1], reverse=True)
    rows = []
    for i, (name, value) in enumerate(entries):
        swatch = Drawing(9, 9)
        from reportlab.graphics.shapes import Rect
        swatch.add(Rect(0, 0, 9, 9, fillColor=_ALLOCATION_SLICE_COLORS[i % len(_ALLOCATION_SLICE_COLORS)], strokeColor=None))
        rows.append([swatch, Paragraph(name, TABLE_CELL), Paragraph(f"{value}%", TABLE_CELL_BOLD)])

    table = Table(rows, colWidths=[0.7 * cm, 5.4 * cm, 1.8 * cm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
    ]))
    return table


# ---------------------------------------------------------------------------
# Report sections (Page 2 onward)
# ---------------------------------------------------------------------------

def _kpi_strip(items) -> Table:
    """items: list of (label, value, gold: bool)"""
    label_row = [Paragraph(label, FIGURE_LABEL) for label, _, _ in items]
    value_row = [Paragraph(value, KPI_VALUE_GOLD if gold else KPI_VALUE) for _, value, gold in items]
    table = Table([label_row, value_row], colWidths=[17.1 * cm / len(items)] * len(items))
    table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LINEBELOW", (0, 1), (-1, 1), 0.8, GOLD),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
    ]))
    return table


def _executive_summary_section(plan: dict, user_input: dict) -> list:
    monte_carlo = plan.get("monte_carlo", {})
    sip_plan = plan.get("sip_plan", {})
    probability = monte_carlo.get("probability_of_success")

    story = _section_heading("Section 01", "Executive Summary")

    kpi_items = [
        ("PROBABILITY OF SUCCESS", _pct(probability), True),
        ("TARGET CORPUS", _format_crores(user_input.get("target_retirement_corpus")), False),
        ("MONTHLY SIP REQUIRED", _format_inr((sip_plan.get("monthly_sip_required") or {}).get("total")), False),
        ("RETIREMENT AGE", str(user_input.get("target_retirement_age", "N/A")), False),
    ]
    story.append(_kpi_strip(kpi_items))
    story.append(Spacer(1, 0.3 * cm))

    memo = (plan.get("memo") or "").strip()
    if memo:
        story += _render_markdown_lite(memo)
    else:
        story.append(Paragraph(
            "This report sets out a complete, tax-aware wealth plan for an NRI resident in the "
            "UAE, covering asset allocation, monthly investment strategy, and the probability of "
            "reaching the client's stated retirement goal.", BODY,
        ))

    return story


def _client_inputs_section(user_input: dict) -> list:
    story = _section_heading("Section 02", "Client Inputs Summary")
    story.append(Paragraph(
        "The figures below are exactly as provided by the client at the time this plan was "
        "generated. No personal or identifying information was collected or stored.", BODY,
    ))
    story.append(Spacer(1, 0.2 * cm))

    rows = [[Paragraph("Input", TABLE_HEADER), Paragraph("Value", TABLE_HEADER)]]
    fields = [
        ("Current Age", str(user_input.get("age", "N/A"))),
        ("Target Retirement Age", str(user_input.get("target_retirement_age", "N/A"))),
        ("Country of Residence", str(user_input.get("country_of_residence", "N/A"))),
        ("Monthly Income", _format_inr(user_input.get("monthly_income"))),
        ("Monthly Expenses", _format_inr(user_input.get("monthly_expenses"))),
        ("Monthly Feasible Investment", _format_inr(user_input.get("monthly_feasible_investment_amount"))),
        ("Existing Indian Assets", _format_inr(user_input.get("existing_indian_assets"))),
        ("Existing Foreign Assets", _format_inr(user_input.get("existing_foreign_assets"))),
        ("Risk Appetite", str(user_input.get("risk_appetite", "N/A")).capitalize()),
        ("Target Retirement Corpus", _format_inr(user_input.get("target_retirement_corpus"))),
        ("Repatriation Intent", _yes_no(user_input.get("repatriation_intent"))),
        ("TRC + Form 10F on File", _yes_no(user_input.get("has_trc_form10f"))),
    ]
    for label, value in fields:
        rows.append([Paragraph(label, TABLE_CELL), Paragraph(value, TABLE_CELL_BOLD)])

    story.append(_styled_table(rows, col_widths=[9 * cm, 8.1 * cm]))
    return story


def _probability_section(plan: dict, user_input: dict) -> list:
    monte_carlo = plan.get("monte_carlo", {})
    probability = monte_carlo.get("probability_of_success")
    num_sims = monte_carlo.get("num_simulations", 10_000)

    story = _section_heading("Section 03", "Probability of Success")
    story.append(Paragraph(_pct(probability), FIGURE_HUGE))
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph(
        f"Across {num_sims:,} simulated market paths, this is the share of outcomes in which the "
        f"client's portfolio reaches or exceeds the target corpus of "
        f"{_format_crores(user_input.get('target_retirement_corpus'))} by the stated retirement age of "
        f"{user_input.get('target_retirement_age', 'N/A')}.",
        LEAD,
    ))
    story.append(Paragraph(
        "A probability of success in the 70&ndash;90% range is generally considered a robust "
        "planning target for a retirement horizon of this length &mdash; it allows for meaningful "
        "market volatility while remaining achievable without excessive risk-taking. Figures below "
        "this range warrant either a higher monthly contribution, a later retirement age, or a "
        "revised target corpus, each explored later in this report.",
        BODY,
    ))
    return story


def _monte_carlo_section(plan: dict) -> list:
    monte_carlo = plan.get("monte_carlo", {})
    assumptions = monte_carlo.get("assumptions", {})
    asset_assumptions = assumptions.get("asset_class_assumptions", {})

    story = _section_heading("Section 04", "Monte Carlo Analysis")
    story.append(Paragraph(
        f"Projected net worth over {monte_carlo.get('years_to_retirement', 'N/A')} years, "
        f"based on {monte_carlo.get('num_simulations', 10_000):,} simulated market scenarios "
        "drawn from the return and volatility assumptions below.",
        BODY,
    ))
    story.append(Spacer(1, 0.25 * cm))
    story.append(_monte_carlo_chart(monte_carlo))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Market Assumptions", SUBSECTION_TITLE))
    rows = [[Paragraph(h, TABLE_HEADER) for h in ("Asset Class", "Expected Annual Return", "Volatility")]]
    for asset, a in asset_assumptions.items():
        rows.append([
            Paragraph(asset, TABLE_CELL),
            Paragraph(_pct(a.get("expected_return", 0) * 100), TABLE_CELL),
            Paragraph(_pct(a.get("volatility", 0) * 100), TABLE_CELL),
        ])
    story.append(_styled_table(rows, col_widths=[7 * cm, 5.5 * cm, 4.6 * cm], align_numeric_from=1))
    story.append(Paragraph(
        f"Annual inflation assumption: {_pct((assumptions.get('annual_inflation_rate') or 0) * 100)}. "
        f"{assumptions.get('contribution_timing', '')}",
        CAPTION,
    ))
    return story


def _asset_allocation_section(plan: dict) -> list:
    asset_allocation = plan.get("asset_allocation", {})
    allocations = asset_allocation.get("allocations", {})
    reasons = asset_allocation.get("reasons", {})
    sip_by_asset = (plan.get("sip_plan", {}).get("monthly_sip_required") or {}).get("by_asset_class", {})

    story = _section_heading("Section 05", "Asset Allocation")
    story.append(Paragraph(
        "The portfolio below is calibrated to the client's investment horizon, stated risk "
        "appetite, and repatriation intent, and reflects restrictions applicable to NRI investors "
        "(new Sovereign Gold Bonds are not available to NRIs; the gold allocation instead uses "
        f"{asset_allocation.get('gold_category_name', 'a Gold ETF/Mutual Fund')}).",
        BODY,
    ))
    story.append(Spacer(1, 0.2 * cm))

    chart_and_legend = Table(
        [[_allocation_pie(allocations), _allocation_legend_table(allocations)]],
        colWidths=[8.2 * cm, 8.9 * cm],
    )
    chart_and_legend.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(chart_and_legend)
    story.append(Spacer(1, 0.3 * cm))

    rows = [[Paragraph(h, TABLE_HEADER) for h in ("Asset", "Allocation", "Monthly SIP", "Rationale")]]
    for asset, pct in sorted(allocations.items(), key=lambda kv: kv[1], reverse=True):
        rows.append([
            Paragraph(asset, TABLE_CELL_BOLD),
            Paragraph(f"{pct}%", TABLE_CELL),
            Paragraph(_format_inr(sip_by_asset.get(asset, 0)), TABLE_CELL),
            Paragraph(reasons.get(asset, ""), TABLE_CELL_NOTE),
        ])
    story.append(_styled_table(rows, col_widths=[3.4 * cm, 2.4 * cm, 3 * cm, 8.3 * cm]))
    return story


def _sip_strategy_section(plan: dict) -> list:
    sip_plan = plan.get("sip_plan", {})
    total = (sip_plan.get("monthly_sip_required") or {}).get("total")
    step_up = sip_plan.get("sip_step_up")

    story = _section_heading("Section 06", "SIP Strategy")
    story.append(Paragraph(_format_inr(total), FIGURE_MED))
    story.append(Paragraph("Required monthly SIP, held flat for the full investment horizon.", CAPTION))
    story.append(Spacer(1, 0.35 * cm))

    if step_up:
        story.append(Paragraph("Step-Up SIP Alternative", SUBSECTION_TITLE))
        benefit = step_up.get("projected_benefit")
        benefit_str = f"+{benefit} pts" if isinstance(benefit, (int, float)) and benefit >= 0 else f"{benefit} pts"
        story.append(Paragraph(
            f"Increasing the monthly SIP by {step_up.get('annual_step_up_pct')}% every year — in line "
            f"with typical career salary growth — lets the client start at a lower monthly figure of "
            f"{_format_inr(step_up.get('starting_monthly_sip'))} instead of "
            f"{_format_inr(step_up.get('flat_monthly_sip_required'))}, while still targeting the same "
            f"corpus. Modeled with the step-up applied, probability of success moves from "
            f"{_pct(step_up.get('probability_of_success_without_stepup'))} to "
            f"{_pct(step_up.get('probability_of_success_with_stepup'))} "
            f"&mdash; a projected benefit of {benefit_str}.",
            BODY,
        ))

    by_asset = (sip_plan.get("monthly_sip_required") or {}).get("by_asset_class", {})
    if by_asset:
        story.append(Paragraph("Monthly SIP by Asset Class", SUBSECTION_TITLE))
        rows = [[Paragraph(h, TABLE_HEADER) for h in ("Asset Class", "Monthly Contribution")]]
        for asset, amount in sorted(by_asset.items(), key=lambda kv: kv[1], reverse=True):
            rows.append([Paragraph(asset, TABLE_CELL), Paragraph(_format_inr(amount), TABLE_CELL_BOLD)])
        story.append(_styled_table(rows, col_widths=[9 * cm, 8.1 * cm], align_numeric_from=1))

    return story


def _feasibility_section(plan: dict) -> list:
    sip_plan = plan.get("sip_plan", {})
    monte_carlo = plan.get("monte_carlo", {})
    total = (sip_plan.get("monthly_sip_required") or {}).get("total") or 0
    current = sip_plan.get("monthly_feasible_investment_amount")
    gap = (total - current) if current is not None else None
    status = sip_plan.get("feasibility_status")
    suggestion = sip_plan.get("alternative_suggestion")

    story = _section_heading("Section 07", "Feasibility Assessment")

    rows = [[Paragraph(h, TABLE_HEADER) for h in ("Current Plan", "Recommended Plan", "Gap", "Success Probability", "Status")]]
    rows.append([
        Paragraph(_format_inr(current), TABLE_CELL_BOLD),
        Paragraph(_format_inr(total), TABLE_CELL_BOLD),
        Paragraph(_format_inr(max(gap, 0)) if gap is not None else "N/A", TABLE_CELL_BOLD),
        Paragraph(_pct(monte_carlo.get("probability_of_success")), TABLE_CELL_BOLD),
        Paragraph("Adjust Plan" if status == "not_feasible" else "On Track", TABLE_CELL_BOLD),
    ])
    story.append(_styled_table(rows, col_widths=[3.1 * cm, 3.7 * cm, 2.6 * cm, 4.2 * cm, 3.5 * cm]))
    story.append(Spacer(1, 0.3 * cm))

    if status == "not_feasible" and suggestion:
        if suggestion.get("type") == "extend_timeline":
            note = (
                f"The required SIP exceeds the client's stated feasible investment amount. Extending "
                f"the investment horizon by {suggestion.get('extra_years')} year(s) — to "
                f"{suggestion.get('adjusted_years')} years total — brings the required SIP down to "
                f"{_format_inr(suggestion.get('monthly_sip_required'))}, within budget, while still "
                f"reaching the original target corpus."
            )
        elif suggestion.get("type") == "reduce_corpus":
            note = (
                f"The required SIP exceeds the client's stated feasible investment amount, and no "
                f"reasonable extension of the timeline closes the gap. At the client's stated feasible "
                f"SIP of {_format_inr(suggestion.get('monthly_sip_required'))}, the achievable corpus "
                f"within the original horizon is approximately "
                f"{_format_crores(suggestion.get('adjusted_corpus'))}, against the original target."
            )
        else:
            note = "The required SIP exceeds the client's stated feasible investment amount."
        story.append(Paragraph(note, BODY))
    else:
        story.append(Paragraph(
            "The client's stated feasible monthly investment amount meets or exceeds the SIP "
            "required to reach the target corpus within the stated horizon. No adjustment to the "
            "plan is required at this time.",
            BODY,
        ))

    return story


def _tax_allocation_section(plan: dict) -> list:
    tax_and_accounts = plan.get("tax_and_accounts", {})
    accounts = tax_and_accounts.get("recommended_accounts", [])
    risk_flags = tax_and_accounts.get("risk_flags", [])

    story = _section_heading("Section 08", "Tax-Aware Allocation")
    story.append(Paragraph(
        "Recommended account structure for holding and repatriating assets between India and the "
        "UAE, based on the client's stated repatriation intent and existing asset base.",
        BODY,
    ))
    story.append(Spacer(1, 0.15 * cm))

    rows = [[Paragraph(h, TABLE_HEADER) for h in ("Account", "Recommended", "Repatriation", "Rationale")]]
    for account in accounts:
        rows.append([
            Paragraph(f"{account.get('account_type')} &mdash; {account.get('full_name', '')}", TABLE_CELL_BOLD),
            Paragraph("Yes" if account.get("recommended") else "Optional", TABLE_CELL),
            Paragraph(account.get("repatriation", ""), TABLE_CELL),
            Paragraph(account.get("reason", ""), TABLE_CELL_NOTE),
        ])
    story.append(_styled_table(rows, col_widths=[4.1 * cm, 3.1 * cm, 4.1 * cm, 5.8 * cm]))

    if risk_flags:
        story.append(Paragraph("Risk Flags", SUBSECTION_TITLE))
        for flag in risk_flags:
            story.append(Paragraph(flag.get("message", ""), BULLET, bulletText="•"))

    return story


def _retirement_timeline_section(plan: dict) -> list:
    r = plan.get("recommended_retirement_age")
    story = _section_heading("Section 09", "Retirement Timeline")

    if not r:
        story.append(Paragraph(
            "A recommended retirement age could not be modeled from the inputs provided.", BODY,
        ))
        return story

    story.append(Paragraph(f"{r.get('recommended_retirement_age', 'N/A')} Years", FIGURE_HUGE))
    story.append(Paragraph("Recommended retirement age", CAPTION))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(r.get("explanation", ""), LEAD))

    rows = [[Paragraph(h, TABLE_HEADER) for h in ("Stated Age", "Recommended Age", "Probability at Recommended Age", "Threshold Used")]]
    rows.append([
        Paragraph(str(r.get("stated_retirement_age", "N/A")), TABLE_CELL_BOLD),
        Paragraph(str(r.get("recommended_retirement_age", "N/A")), TABLE_CELL_BOLD),
        Paragraph(_pct(r.get("probability_of_success")), TABLE_CELL_BOLD),
        Paragraph(_pct(r.get("threshold_used")), TABLE_CELL_BOLD),
    ])
    story.append(_styled_table(rows, col_widths=[4.2 * cm, 4.2 * cm, 5.2 * cm, 3.5 * cm]))
    return story


def _recommendations_section(plan: dict) -> list:
    sip_plan = plan.get("sip_plan", {})
    step_up = sip_plan.get("sip_step_up")
    retirement = plan.get("recommended_retirement_age")

    story = _section_heading("Section 10", "Recommendations")

    items = []
    if sip_plan.get("feasibility_status") == "not_feasible":
        suggestion = sip_plan.get("alternative_suggestion") or {}
        if suggestion.get("type") == "extend_timeline":
            items.append(
                f"Extend the investment horizon by {suggestion.get('extra_years')} year(s) to bring "
                f"the required SIP within the client's stated budget."
            )
        elif suggestion.get("type") == "reduce_corpus":
            items.append(
                f"Recalibrate the target corpus to approximately "
                f"{_format_crores(suggestion.get('adjusted_corpus'))} at the client's current feasible SIP."
            )
    else:
        items.append("Maintain the current monthly SIP — the plan is on track to reach the target corpus.")

    if step_up:
        items.append(
            f"Adopt a {step_up.get('annual_step_up_pct')}% annual step-up on the SIP to reduce the "
            f"starting contribution while preserving the long-term target."
        )

    if retirement and retirement.get("meets_threshold") and retirement.get("recommended_retirement_age") != retirement.get("stated_retirement_age"):
        if retirement["recommended_retirement_age"] < retirement["stated_retirement_age"]:
            items.append(
                f"Current savings pace already supports retiring at "
                f"{retirement['recommended_retirement_age']}, {retirement['stated_retirement_age'] - retirement['recommended_retirement_age']} "
                f"year(s) earlier than planned."
            )
        else:
            items.append(
                f"Consider retiring at {retirement['recommended_retirement_age']} instead of "
                f"{retirement['stated_retirement_age']} to raise the probability of success to an "
                f"acceptable threshold."
            )

    risk_flags = plan.get("tax_and_accounts", {}).get("risk_flags", [])
    if risk_flags:
        items.append(f"Address the {len(risk_flags)} tax/FEMA risk flag(s) identified in Section 08 before executing this plan.")

    if not items:
        items.append("No further action required at this time — continue monitoring the plan annually.")

    for item in items:
        story.append(Paragraph(item, BULLET, bulletText="•"))

    return story


def _final_wealth_plan_section(plan: dict, user_input: dict) -> list:
    monte_carlo = plan.get("monte_carlo", {})
    sip_plan = plan.get("sip_plan", {})
    asset_allocation = plan.get("asset_allocation", {})
    retirement = plan.get("recommended_retirement_age") or {}

    story = _section_heading("Section 11", "Final Wealth Plan")
    story.append(Paragraph(
        "A consolidated summary of the wealth plan detailed in this report, suitable for quick "
        "reference.",
        BODY,
    ))
    story.append(Spacer(1, 0.15 * cm))

    rows = [[Paragraph(h, TABLE_HEADER) for h in ("Metric", "Value")]]
    summary_fields = [
        ("Target Retirement Corpus", _format_inr(user_input.get("target_retirement_corpus"))),
        ("Stated Retirement Age", str(user_input.get("target_retirement_age", "N/A"))),
        ("Recommended Retirement Age", str(retirement.get("recommended_retirement_age", "N/A"))),
        ("Monthly SIP Required", _format_inr((sip_plan.get("monthly_sip_required") or {}).get("total"))),
        ("Probability of Success", _pct(monte_carlo.get("probability_of_success"))),
        ("Dominant Asset Class", max(asset_allocation.get("allocations", {"N/A": 0}).items(), key=lambda kv: kv[1])[0]),
        ("Feasibility Status", "On Track" if sip_plan.get("feasibility_status") != "not_feasible" else "Requires Adjustment"),
    ]
    for label, value in summary_fields:
        rows.append([Paragraph(label, TABLE_CELL), Paragraph(value, TABLE_CELL_BOLD)])
    story.append(_styled_table(rows, col_widths=[9 * cm, 8.1 * cm]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "This plan should be revisited annually, or whenever the client's income, expenses, or "
        "goals change materially, to ensure it continues to reflect an achievable path to the "
        "stated retirement objective.",
        BODY,
    ))
    return story


def _disclaimer_section() -> list:
    story = [
        Paragraph("Important Disclaimer", DISCLAIMER_TITLE),
        HRFlowable(width="100%", thickness=0.6, color=HAIRLINE, spaceAfter=12),
    ]
    for paragraph in DISCLAIMER_PARAGRAPHS:
        story.append(Paragraph(paragraph, DISCLAIMER_BODY))
    return story


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------

def build_pdf_report(user_input: dict, plan: dict) -> bytes:
    """Render the full Zaelor wealth plan PDF and return it as raw bytes."""
    buffer = io.BytesIO()
    generated_on = date.today().strftime("%d %B %Y")

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        title="Zaelor Private Wealth Advisory Report",
        author="Zaelor",
    )

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=2.4 * cm, rightPadding=2.4 * cm, topPadding=0, bottomPadding=0, id="cover")
    report_frame = Frame(
        MARGIN_X, MARGIN_BOTTOM,
        PAGE_W - 2 * MARGIN_X, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        id="report",
    )

    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=_draw_cover_background),
        PageTemplate(id="Report", frames=[report_frame], onPage=_make_report_header_footer(generated_on)),
    ])

    story = []
    story += _cover_story(user_input, generated_on)
    story.append(NextPageTemplate("Report"))
    story.append(PageBreak())

    sections = [
        _executive_summary_section(plan, user_input),
        _client_inputs_section(user_input),
        _probability_section(plan, user_input),
        _monte_carlo_section(plan),
        _asset_allocation_section(plan),
        _sip_strategy_section(plan),
        _feasibility_section(plan),
        _tax_allocation_section(plan),
        _retirement_timeline_section(plan),
        _recommendations_section(plan),
        _final_wealth_plan_section(plan, user_input),
    ]
    for i, section in enumerate(sections):
        story += section
        if i < len(sections) - 1:
            story.append(PageBreak())

    story.append(PageBreak())
    story += _disclaimer_section()

    doc.build(story, canvasmaker=_ZaelorCanvas)

    return buffer.getvalue()

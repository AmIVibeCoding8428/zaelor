"""Generates the downloadable Zaelor wealth plan PDF report via ReportLab.

Takes the already-computed structured plan (+ Claude memo) and the original
questionnaire input, and lays it out as a styled PDF. Purely presentational —
no financial calculation happens here.
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BACKGROUND = colors.HexColor("#0A0A0A")
CARD = colors.HexColor("#111111")
GOLD = colors.HexColor("#C8A24C")
TEXT = colors.HexColor("#F5F5F5")
SECONDARY_TEXT = colors.HexColor("#A1A1A1")
BODY_TEXT = colors.HexColor("#1A1A1A")

DISCLAIMER_TEXT = (
    "This report is generated using assumptions based on publicly available "
    "information and user-provided inputs. It is intended for educational "
    "purposes and should not be considered personalized financial or tax "
    "advice."
)

_styles = getSampleStyleSheet()

WORDMARK_STYLE = ParagraphStyle(
    "Wordmark", parent=_styles["Title"], fontName="Helvetica-Bold",
    fontSize=30, textColor=GOLD, alignment=1, spaceAfter=6,
)
TAGLINE_STYLE = ParagraphStyle(
    "Tagline", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=12, textColor=TEXT, alignment=1, spaceAfter=2,
)
SUBTITLE_STYLE = ParagraphStyle(
    "Subtitle", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=9, textColor=SECONDARY_TEXT, alignment=1,
)
SECTION_HEADING_STYLE = ParagraphStyle(
    "SectionHeading", parent=_styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=14, textColor=GOLD, spaceBefore=18, spaceAfter=8,
)
KPI_LABEL_STYLE = ParagraphStyle(
    "KpiLabel", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=9, textColor=SECONDARY_TEXT, alignment=1,
)
KPI_VALUE_STYLE = ParagraphStyle(
    "KpiValue", parent=_styles["Normal"], fontName="Helvetica-Bold",
    fontSize=18, textColor=colors.white, alignment=1, spaceBefore=4,
)
BODY_STYLE = ParagraphStyle(
    "Body", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=10, textColor=BODY_TEXT, leading=15,
)
RISK_FLAG_STYLE = ParagraphStyle(
    "RiskFlag", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=9.5, textColor=BODY_TEXT, leading=14, spaceAfter=6,
    leftIndent=10,
)
DISCLAIMER_STYLE = ParagraphStyle(
    "Disclaimer", parent=_styles["Normal"], fontName="Helvetica-Oblique",
    fontSize=8, textColor=SECONDARY_TEXT, leading=11,
)
TABLE_CELL_STYLE = ParagraphStyle(
    "TableCell", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=8.5, textColor=BODY_TEXT, leading=11,
)
TABLE_HEADER_STYLE = ParagraphStyle(
    "TableHeader", parent=_styles["Normal"], fontName="Helvetica-Bold",
    fontSize=9, textColor=colors.black, leading=11,
)


def _cell(text) -> Paragraph:
    """Wrap table cell text in a Paragraph so ReportLab wraps it instead of truncating it."""
    return Paragraph(str(text), TABLE_CELL_STYLE)


def _header_cell(text) -> Paragraph:
    return Paragraph(str(text), TABLE_HEADER_STYLE)


def _format_inr(amount) -> str:
    """Format a number as an INR amount using Indian digit grouping, e.g. 1,23,45,678."""
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
    return f"{sign}Rs. {grouped}"


def _cover_section(generated_on: str) -> list:
    return [
        Spacer(1, 1.5 * cm),
        Paragraph("ZAELOR", WORDMARK_STYLE),
        Paragraph("Wealth beyond borders.", TAGLINE_STYLE),
        Spacer(1, 0.3 * cm),
        Paragraph("Personalized NRI Wealth Plan &mdash; UAE Edition", SUBTITLE_STYLE),
        Paragraph(f"Generated on {generated_on} &middot; 100% anonymous &middot; no personal data stored", SUBTITLE_STYLE),
        Spacer(1, 0.6 * cm),
        HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=6),
    ]


def _hero_kpi_section(plan: dict, user_input: dict) -> list:
    monte_carlo = plan.get("monte_carlo", {})
    sip_plan = plan.get("sip_plan", {})

    probability = monte_carlo.get("probability_of_success")
    probability_str = f"{probability}%" if probability is not None else "N/A"
    target_corpus_str = _format_inr(user_input.get("target_retirement_corpus"))
    monthly_sip_str = _format_inr(
        (sip_plan.get("monthly_sip_required") or {}).get("total")
    )
    retirement_age = user_input.get("target_retirement_age")
    retirement_age_str = str(retirement_age) if retirement_age is not None else "N/A"

    kpis = [
        ("Probability of Success", probability_str),
        ("Target Corpus", target_corpus_str),
        ("Monthly SIP Required", monthly_sip_str),
        ("Retirement Age", retirement_age_str),
    ]

    cells = [[Paragraph(label, KPI_LABEL_STYLE)] for label, _ in kpis]
    value_cells = [[Paragraph(value, KPI_VALUE_STYLE)] for _, value in kpis]

    col_width = 4.3 * cm
    table = Table(
        [value_cells, cells],
        colWidths=[col_width] * 4,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, GOLD),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#222222")),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
        ("TOPPADDING", (0, -1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    return [
        Paragraph("Wealth Plan Summary", SECTION_HEADING_STYLE),
        table,
    ]


def _allocation_table_section(plan: dict) -> list:
    asset_allocation = plan.get("asset_allocation", {})
    allocations = asset_allocation.get("allocations", {})
    sip_by_asset = (plan.get("sip_plan", {}).get("monthly_sip_required") or {}).get(
        "by_asset_class", {}
    )
    expected_returns = {
        "Indian Equity": "12%",
        "International ETFs": "9%",
        "Indian Debt": "7%",
        "Gold": "8%",
        "REITs/Real Estate": "9%",
        "Cash": "4%",
    }

    header = [_header_cell(h) for h in ("Asset", "Allocation %", "Monthly SIP", "Expected Return")]
    rows = [header]
    for asset, pct in allocations.items():
        rows.append([
            _cell(asset),
            _cell(f"{pct}%"),
            _cell(_format_inr(sip_by_asset.get(asset, 0))),
            _cell(expected_returns.get(asset, "N/A")),
        ])

    table = Table(rows, colWidths=[5 * cm, 3 * cm, 4.5 * cm, 3.5 * cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return [
        Paragraph("Recommended Asset Allocation", SECTION_HEADING_STYLE),
        table,
    ]


def _tax_accounts_section(plan: dict) -> list:
    tax_and_accounts = plan.get("tax_and_accounts", {})
    accounts = tax_and_accounts.get("recommended_accounts", [])

    header = [_header_cell(h) for h in ("Account", "Recommended", "Repatriation", "Reason")]
    rows = [header]
    for account in accounts:
        rows.append([
            _cell(f"{account.get('account_type')} ({account.get('full_name', '')})"),
            _cell("Yes" if account.get("recommended") else "Optional"),
            _cell(account.get("repatriation", "")),
            _cell(account.get("reason", "")),
        ])

    table = Table(rows, colWidths=[3.5 * cm, 2 * cm, 4.5 * cm, 6.5 * cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return [
        Paragraph("Tax &amp; Account Recommendations (NRE / NRO / FCNR)", SECTION_HEADING_STYLE),
        table,
    ]


def _memo_section(plan: dict) -> list:
    memo = plan.get("memo", "")
    paragraphs = [Paragraph(line, BODY_STYLE) for line in memo.split("\n") if line.strip()]
    return [
        Paragraph("Advisory Summary", SECTION_HEADING_STYLE),
        *paragraphs,
    ]


def _risk_flags_section(plan: dict) -> list:
    risk_flags = plan.get("tax_and_accounts", {}).get("risk_flags", [])
    if not risk_flags:
        return []

    items = [
        Paragraph(f"&bull; {flag.get('message', '')}", RISK_FLAG_STYLE)
        for flag in risk_flags
    ]
    return [
        Paragraph("Risk Flags", SECTION_HEADING_STYLE),
        *items,
    ]


def _disclaimer_section() -> list:
    return [
        Spacer(1, 1 * cm),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=6),
        Paragraph(DISCLAIMER_TEXT, DISCLAIMER_STYLE),
    ]


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(2 * cm, 1.2 * cm, "ZAELOR")
    canvas.setFillColor(SECONDARY_TEXT)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf_report(user_input: dict, plan: dict) -> bytes:
    """Render the full Zaelor wealth plan PDF and return it as raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Zaelor Wealth Plan Report",
    )

    generated_on = date.today().strftime("%d %B %Y")

    story = []
    story += _cover_section(generated_on)
    story += _hero_kpi_section(plan, user_input)
    story += _allocation_table_section(plan)
    story += _tax_accounts_section(plan)
    story += _memo_section(plan)
    story += _risk_flags_section(plan)
    story += _disclaimer_section()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    return buffer.getvalue()

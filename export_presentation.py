from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT = r"C:\Users\PHIRI\Desktop\EMK Links Art Gallery Console\emk-links-art-gallery-presentation.pdf"
PAGE = landscape(A4)
ink = colors.HexColor("#18251f")
muted = colors.HexColor("#69766e")
rust = colors.HexColor("#a94f32")
acid = colors.HexColor("#d8ef70")
sage = colors.HexColor("#cfe4d3")
paper = colors.HexColor("#f4f1e9")
panel = colors.HexColor("#fffdf8")
line = colors.HexColor("#d9ded4")

styles = getSampleStyleSheet()
kicker = ParagraphStyle("Kicker", parent=styles["Normal"], fontName="Courier", fontSize=8, leading=10, textColor=rust, spaceAfter=10)
title = ParagraphStyle("Title", parent=styles["Title"], fontName="Times-Bold", fontSize=31, leading=33, textColor=ink, spaceAfter=12)
subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontName="Times-Roman", fontSize=14, leading=18, textColor=muted, spaceAfter=12)
heading = ParagraphStyle("Heading", parent=styles["Heading1"], fontName="Times-Bold", fontSize=21, leading=24, textColor=ink, spaceAfter=12)
card_title = ParagraphStyle("CardTitle", parent=styles["Heading3"], fontName="Times-Bold", fontSize=13, leading=16, textColor=ink, spaceAfter=7)
body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13, textColor=colors.HexColor("#4e5c54"))
label = ParagraphStyle("Label", parent=styles["Normal"], fontName="Courier", fontSize=7.5, leading=10, textColor=rust, spaceAfter=5)
metric = ParagraphStyle("Metric", parent=styles["Normal"], fontName="Courier-Bold", fontSize=22, leading=25, textColor=ink, spaceAfter=4)
metric_label = ParagraphStyle("MetricLabel", parent=styles["Normal"], fontName="Courier", fontSize=7.5, leading=10, textColor=muted)
callout = ParagraphStyle("Callout", parent=styles["Normal"], fontName="Times-Roman", fontSize=11.5, leading=15, textColor=ink)
link_style = ParagraphStyle("Link", parent=styles["Normal"], fontName="Courier", fontSize=10, leading=14, textColor=rust)


def P(text, style=body):
    return Paragraph(text, style)


def card(label_text, heading_text, copy, accent=acid, width=56 * mm, height=42 * mm):
    table = Table([[[P(label_text, label), P(heading_text, card_title), P(copy, body)]]], colWidths=[width], rowHeights=[height])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), panel),
        ("BOX", (0, 0), (-1, -1), 0.6, line),
        ("LINEABOVE", (0, 0), (-1, 0), 3, accent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def footer(canvas, document):
    canvas.saveState()
    canvas.setFillColor(paper)
    canvas.rect(0, 0, PAGE[0], PAGE[1], fill=1, stroke=0)
    canvas.setStrokeColor(colors.Color(24 / 255, 37 / 255, 31 / 255, alpha=0.06))
    canvas.setLineWidth(0.35)
    for x in range(0, int(PAGE[0]), int(12 * mm)):
        canvas.line(x, 0, x, PAGE[1])
    for y in range(0, int(PAGE[1]), int(12 * mm)):
        canvas.line(0, y, PAGE[0], y)
    canvas.setFillColor(acid)
    canvas.rect(PAGE[0] - 42 * mm, PAGE[1] - 8 * mm, 42 * mm, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(sage)
    canvas.saveState()
    canvas.translate(PAGE[0] - 24 * mm, PAGE[1] - 48 * mm)
    canvas.rotate(32)
    canvas.rect(-4 * mm, -28 * mm, 8 * mm, 56 * mm, fill=1, stroke=0)
    canvas.restoreState()
    canvas.setFillColor(rust)
    canvas.rect(18 * mm, PAGE[1] - 4 * mm, 18 * mm, 4 * mm, fill=1, stroke=0)
    canvas.setFillColor(muted)
    canvas.setFont("Courier", 7.5)
    canvas.drawString(24 * mm, 11 * mm, "EMK LINKS / ART GALLERY CONSOLE")
    canvas.drawRightString(PAGE[0] - 24 * mm, 11 * mm, str(document.page))
    canvas.restoreState()


def slide(story, kicker_text, heading_text, content):
    story.extend([P(kicker_text, kicker), P(heading_text, heading), content, PageBreak()])


def row(cards):
    table = Table([cards], colWidths=[61 * mm] * len(cards), hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]))
    return table


story = []
story.extend([P("EMK / PRESENTATION BRIEF / 01", kicker), Spacer(1, 10 * mm), P("The link gallery", title), P("A professional Streamlit console for turning EMK artwork links into a clear, searchable, measurable gallery workflow.", subtitle), Spacer(1, 8 * mm), Table([[P("From scattered links to a curated collection with visible business priorities.", callout)]], colWidths=[225 * mm], style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#edf4d8")), ("LINEBEFORE", (0, 0), (0, -1), 4, acid), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]), PageBreak()])
slide(story, "THE BUSINESS CHALLENGE", "Curated work deserves a reliable path to discovery.", row([card("PROBLEM", "Links are hard to manage", "Artwork, artist, category, image, and destination data can become fragmented across messages, documents, and social channels.", rust), card("RISK", "Audience attention leaks", "Broken or unreviewed destinations interrupt the visitor journey and weaken campaign confidence."), card("OPPORTUNITY", "Make the collection actionable", "One shared console connects curation, link health, catalog intelligence, and the next marketing move.", colors.HexColor("#8aad7f"))]))
slide(story, "THE SOLUTION", "One console for the collection and the decision.", row([card("01 / BROWSE", "Visual catalog", "Artwork cards make the collection easy to scan by title, artist, category, and status."), card("02 / CURATE", "Protected controls", "Curators can add, import, export, review, and restore catalog records from the control room."), card("03 / MEASURE", "Business intelligence", "Catalog health becomes visible through live coverage, review queue, link checks, and category mix."), card("04 / ACT", "Operational response", "Every insight ends with a recommended action for curation, promotion, or link repair.")]))
slide(story, "DATA TO ACTION", "The decision brief makes the numbers useful.", row([card("01 / BUSINESS PROBLEM", "What needs attention?", "Identify broken links, review backlog, or a discovery gap.", rust), card("02 / DATA", "What is happening?", "Use catalog totals, live status, drafts, reviews, and link checks."), card("03 / INSIGHT", "What does it mean?", "Translate the evidence into audience, curation, or campaign impact.", colors.HexColor("#8aad7f")), card("04 / BUSINESS ACTION", "What happens next?", "Repair, review, publish, feature, or plan the next collection move.", ink)]))
slide(story, "WHAT STAKEHOLDERS CAN SEE", "A clearer operating picture.", row([card("06", "Works indexed", "Every artwork has a visible place in the collection."), card("04", "Live links", "Published destinations are separated from review and draft work."), card("01", "Review queue", "Curators can see what needs attention before promotion.", rust), card("06", "Artists / studios", "The collection's contributor mix is visible at a glance.", colors.HexColor("#8aad7f"))]))
slide(story, "RECOMMENDED OPERATING RHYTHM", "Use the console as a lightweight growth system.", row([card("WEEKLY", "Curate the queue", "Review draft and review items, confirm destinations, and select the strongest works for the next feature."), card("BEFORE CAMPAIGNS", "Check the journey", "Run link checks, repair failed destinations, and confirm that every promoted work reaches the intended page.", colors.HexColor("#8aad7f")), card("MONTHLY", "Read the mix", "Use categories, artists, status, and year span to shape programming, storytelling, and audience outreach.", rust)]))
slide(story, "LIVE DEMO", "EMK Links / Art Gallery Console", P("Open the deployed console to browse the gallery and demonstrate the decision brief.", subtitle))
story.extend([P("https://emk-links-art-gallery-console-yq2mayvjbdiappem9wjnjf.streamlit.app/?embed=true", link_style), Spacer(1, 7 * mm), row([card("VISITOR ACCESS", "Public gallery", "The embed URL opens the gallery directly for visitors and stakeholders."), card("CURATOR ACCESS", "Control room", "Authorized users can unlock catalog management and operational tools.", rust), card("OUTCOME", "From insight to action", "A shared source of truth for art links, collection health, and marketing decisions.", colors.HexColor("#8aad7f"))])])

# Remove the trailing page break from the final slide.
if isinstance(story[-1], PageBreak):
    story.pop()
doc = SimpleDocTemplate(OUTPUT, pagesize=PAGE, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=10 * mm, bottomMargin=12 * mm, title="EMK Links Art Gallery Console Presentation", author="EMK Links")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)

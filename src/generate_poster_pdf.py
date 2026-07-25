"""Generate the FYP exhibition poster as a print-ready A2 PDF.

Produces: outputs/Final_Poster_AgroAI.pdf

Conforms to the IN4911 / IN4921 Final Year Project Exhibition poster guidelines:
  Header  — group number, group name, project title
  Main    — problem statement & objectives, system architecture, key modules,
            methodology, visual illustrations, key results / conclusion
  Footer  — faculty, department, degree programme, member index numbers and
            names, supervisor
  Size    — A2 portrait (420 mm x 594 mm)

Colour scheme and figures are shared with the final report and defence deck.
All quoted results come from the real collected dataset (outputs/results_real/).

Usage:  python src/generate_poster_figures.py && python src/generate_poster_pdf.py
"""

from __future__ import annotations

import os

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, FrameBreak,
                                Image, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTER_FIGS = os.path.join(ROOT, "outputs", "poster")
OUT_PATH = os.path.join(ROOT, "outputs", "Final_Poster_AgroAI.pdf")

# ---- Fields the guideline requires -----------------------------------------
# NOTE: the group number is not recorded anywhere in the project repository.
# Set GROUP_NUMBER below before printing.
GROUP_NUMBER = "___"          # <-- FILL THIS IN
GROUP_NAME = "Agro AI"
MODULE_CODE = "IN4911 — Comprehensive Group Project"

PROJECT_TITLE = "AI-Powered Harvest Yield Prediction for"
PROJECT_TITLE_2 = "Non-Cash Crops (Big Onion) in Sri Lanka"

FACULTY = "Faculty of Information Technology"
DEPARTMENT = "Department of Information Technology"
DEGREE = "B.Sc. (Hons) in Information Technology"
UNIVERSITY = "University of Moratuwa, Sri Lanka"
SUPERVISOR = "Dr. Firdhous M.F.M."
MEMBERS = [("214019K", "Arkam B.H.M."),
           ("214192G", "Sharuja B."),
           ("214193K", "Shathurya P.")]

# ---- Palette (shared with the report and the deck) -------------------------
NAVY = HexColor("#0d366b")
NAVY_DEEP = HexColor("#09264c")
BLUE = HexColor("#2a78d6")
BLUE_PALE = HexColor("#cde2fb")
ORANGE = HexColor("#eb6834")
ORANGE_PALE = HexColor("#fbe0d5")
VIOLET = HexColor("#4a3aa7")
VIOLET_PALE = HexColor("#ddd9f2")
SURFACE = HexColor("#ffffff")
PANEL = HexColor("#f4f3f0")
INK = HexColor("#0b0b0b")
INK_2 = HexColor("#3d3c3a")
INK_MUTED = HexColor("#6f6e69")
RULE = HexColor("#d9d8d3")
WHITE = HexColor("#ffffff")

# ---- Geometry --------------------------------------------------------------
PAGE_W, PAGE_H = 420 * mm, 594 * mm
MARGIN = 14 * mm
GUTTER = 9 * mm
HEADER_H = 74 * mm
FOOTER_H = 66 * mm
COL_W = (PAGE_W - 2 * MARGIN - GUTTER) / 2
BODY_TOP = PAGE_H - HEADER_H - 7 * mm
BODY_BOTTOM = FOOTER_H + 7 * mm
BODY_H = BODY_TOP - BODY_BOTTOM

F = "Helvetica"
FB = "Helvetica-Bold"
FO = "Helvetica-Oblique"

# ---- Paragraph styles ------------------------------------------------------
BODY = ParagraphStyle("body", fontName=F, fontSize=12, leading=15.2,
                      textColor=INK_2, alignment=TA_JUSTIFY, spaceAfter=4)
BODY_TIGHT = ParagraphStyle("bodyt", parent=BODY, spaceAfter=0)
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=6.5 * mm,
                        bulletIndent=1.5 * mm, spaceAfter=3.5, alignment=0)
LEAD = ParagraphStyle("lead", parent=BODY, fontSize=12.5, leading=15.8,
                      textColor=INK)
CAPTION = ParagraphStyle("cap", fontName=FO, fontSize=10, leading=12.5,
                         textColor=INK_MUTED, alignment=TA_CENTER, spaceBefore=2)
CELL = ParagraphStyle("cell", fontName=F, fontSize=11, leading=13.5,
                      textColor=INK_2)
CELL_B = ParagraphStyle("cellb", parent=CELL, fontName=FB, textColor=INK)


def B(text: str) -> Paragraph:
    return Paragraph(text, BULLET, bulletText="•")


# ---- Custom flowables ------------------------------------------------------

class SectionHeading(Flowable):
    """A numbered section heading with an accent bar and a hairline rule."""

    def __init__(self, number: str, text: str, width: float, color=NAVY):
        super().__init__()
        self.number, self.text, self.width, self.color = number, text, width, color
        self.height = 13 * mm

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.rect(0, 4.6 * mm, 6.2 * mm, 6.2 * mm, stroke=0, fill=1)
        c.setFillColor(self.color)
        c.setFont(FB, 9.5)
        c.drawCentredString(3.1 * mm, 6.4 * mm, self.number)
        c.setFillColor(WHITE)
        c.setFont(FB, 9.5)
        c.drawCentredString(3.1 * mm, 6.4 * mm, self.number)
        c.setFillColor(NAVY)
        c.setFont(FB, 19)
        c.drawString(8.8 * mm, 5.4 * mm, self.text)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.9)
        c.line(0, 2.4 * mm, self.width, 2.4 * mm)


class StatRow(Flowable):
    """A row of headline figures."""

    def __init__(self, stats, width: float, height=27 * mm):
        super().__init__()
        self.stats, self.width, self.height = stats, width, height

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        n = len(self.stats)
        gap = 3.5 * mm
        w = (self.width - gap * (n - 1)) / n
        for i, (value, label, color) in enumerate(self.stats):
            x = i * (w + gap)
            c.setFillColor(PANEL)
            c.rect(x, 0, w, self.height, stroke=0, fill=1)
            c.setFillColor(color)
            c.rect(x, self.height - 1.6 * mm, w, 1.6 * mm, stroke=0, fill=1)
            c.setFillColor(color)
            c.setFont(FB, 26)
            c.drawCentredString(x + w / 2, self.height - 12.5 * mm, value)
            c.setFillColor(INK_2)
            c.setFont(F, 9.6)
            for j, line in enumerate(label.split("\n")):
                c.drawCentredString(x + w / 2, self.height - 18.4 * mm - j * 4.4 * mm,
                                    line)


class Callout(Flowable):
    """A tinted panel used for the two research novelties."""

    def __init__(self, title, lines, width, color, tint, height=None):
        super().__init__()
        self.title, self.lines, self.width = title, lines, width
        self.color, self.tint = color, tint
        self.height = height or (11 * mm + 5.2 * mm * len(lines))

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.tint)
        c.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        c.setFillColor(self.color)
        c.rect(0, 0, 1.8 * mm, self.height, stroke=0, fill=1)
        c.setFillColor(self.color)
        c.setFont(FB, 13)
        c.drawString(5.5 * mm, self.height - 7.4 * mm, self.title)
        c.setFillColor(INK_2)
        c.setFont(F, 11.2)
        for i, line in enumerate(self.lines):
            c.drawString(5.5 * mm, self.height - 13.4 * mm - i * 5.2 * mm, line)


class Result(Flowable):
    """The headline outcome strip."""

    def __init__(self, width, height=23 * mm):
        super().__init__()
        self.width, self.height = width, height

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY)
        c.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FB, 12)
        c.drawString(6 * mm, self.height - 8 * mm, "BEST MODEL — Physics-residual hybrid")
        c.setFont(F, 11)
        c.setFillColor(BLUE_PALE)
        c.drawString(6 * mm, self.height - 14.6 * mm,
                     "RMSE 3.90 MT/Ha   ·   MAE 3.35 MT/Ha   ·   R² 0.091   "
                     "·   MAPE 23.3 %   ·   90 % interval ±6.85 MT/Ha")
        c.setFont(FO, 9.6)
        c.setFillColor(HexColor("#86b6ef"))
        c.drawString(6 * mm, self.height - 20 * mm,
                     "Leave-One-Year-Out cross-validation over 28 collected "
                     "seasonal records (4 districts × 7 years, Yala).")


def fig(path: str, width: float, caption: str | None = None):
    """Scale an image to a column width, preserving aspect ratio."""
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    out = []
    if os.path.exists(full):
        iw, ih = ImageReader(full).getSize()
        out.append(Image(full, width=width, height=width * ih / iw))
    else:
        out.append(Paragraph(f"[missing figure: {path}]", CAPTION))
    if caption:
        out.append(Paragraph(caption, CAPTION))
    return out


def _table(data, widths, *, header=True):
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, RULE),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                  ("LINEBELOW", (0, 0), (-1, 0), 0, NAVY)]
    t.setStyle(TableStyle(style))
    return t


# ---- Page furniture --------------------------------------------------------

def draw_page(canvas, _doc):
    c = canvas
    c.saveState()

    # ---------------- Header ----------------
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, stroke=0, fill=1)
    c.setFillColor(ORANGE)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, 2.6 * mm, stroke=0, fill=1)

    y = PAGE_H - 14 * mm
    c.setFillColor(HexColor("#86b6ef"))
    c.setFont(FB, 11.5)
    c.drawString(MARGIN, y, MODULE_CODE.upper()
                 + "   ·   FINAL YEAR PROJECT EXHIBITION 2026")

    # Group number chip + group name
    y -= 10.5 * mm
    chip_w = 46 * mm
    c.setFillColor(ORANGE)
    c.rect(MARGIN, y - 2.2 * mm, chip_w, 9.6 * mm, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FB, 12.5)
    c.drawCentredString(MARGIN + chip_w / 2, y + 0.9 * mm,
                        f"GROUP {GROUP_NUMBER}")
    c.setFillColor(WHITE)
    c.setFont(FB, 12.5)
    c.drawString(MARGIN + chip_w + 6 * mm, y + 0.9 * mm,
                 f"GROUP NAME:  {GROUP_NAME.upper()}")

    # Project title
    y -= 15 * mm
    c.setFillColor(WHITE)
    c.setFont(FB, 30)
    c.drawString(MARGIN, y, PROJECT_TITLE)
    y -= 12.5 * mm
    c.drawString(MARGIN, y, PROJECT_TITLE_2)

    y -= 9.5 * mm
    c.setFillColor(BLUE_PALE)
    c.setFont(F, 13)
    c.drawString(MARGIN, y,
                 "Pre-harvest, district-level yield forecasting from open weather, "
                 "satellite and soil data — with calibrated uncertainty.")

    # ---------------- Footer ----------------
    c.setFillColor(PANEL)
    c.rect(0, 0, PAGE_W, FOOTER_H, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, FOOTER_H - 1.8 * mm, PAGE_W, 1.8 * mm, stroke=0, fill=1)

    # Left block — institution
    fy = FOOTER_H - 11 * mm
    c.setFillColor(NAVY)
    c.setFont(FB, 13)
    c.drawString(MARGIN, fy, FACULTY)
    c.setFillColor(INK_2)
    c.setFont(F, 11.5)
    c.drawString(MARGIN, fy - 6.2 * mm, DEPARTMENT)
    c.drawString(MARGIN, fy - 11.8 * mm, DEGREE)
    c.drawString(MARGIN, fy - 17.4 * mm, UNIVERSITY)

    # Middle block — members
    mx = MARGIN + 132 * mm
    c.setFillColor(NAVY)
    c.setFont(FB, 11.5)
    c.drawString(mx, fy, "GROUP MEMBERS")
    c.setFont(F, 11.5)
    c.setFillColor(INK_2)
    for i, (index, name) in enumerate(MEMBERS):
        c.setFont(FB, 11.5)
        c.setFillColor(INK)
        c.drawString(mx, fy - 6.6 * mm - i * 5.6 * mm, index)
        c.setFont(F, 11.5)
        c.setFillColor(INK_2)
        c.drawString(mx + 25 * mm, fy - 6.6 * mm - i * 5.6 * mm, name)

    # Right block — supervisor
    sx = MARGIN + 252 * mm
    c.setFillColor(NAVY)
    c.setFont(FB, 11.5)
    c.drawString(sx, fy, "PROJECT SUPERVISOR")
    c.setFillColor(INK)
    c.setFont(FB, 13)
    c.drawString(sx, fy - 7.4 * mm, SUPERVISOR)
    c.setFillColor(INK_2)
    c.setFont(F, 11)
    c.drawString(sx, fy - 13.6 * mm, FACULTY + ",")
    c.drawString(sx, fy - 18.8 * mm, "University of Moratuwa")

    # Accent rule between the two body columns
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    x_mid = MARGIN + COL_W + GUTTER / 2
    c.line(x_mid, BODY_BOTTOM, x_mid, BODY_TOP)
    c.restoreState()


# ---- Story -----------------------------------------------------------------

def story():
    w = COL_W
    s = []

    # ============ LEFT COLUMN ============
    s.append(SectionHeading("1", "Problem Statement", w))
    s.append(Paragraph(
        "Sri Lanka consumes roughly <b>220,000 metric tons</b> of big onion each "
        "year. Domestic cultivation covers only part of that demand and the "
        "balance is imported at a direct foreign-exchange cost.", LEAD))
    s.append(Paragraph(
        "Unlike paddy, big onion has <b>no crop-cutting survey methodology</b>. "
        "Yield figures are compiled from the subjective assessments of "
        "agricultural officers, they carry no quantified error, and they are "
        "finalised only <b>after</b> the crop has been harvested and sold — "
        "while import volumes must be committed months in advance.", BODY))
    s.append(Spacer(1, 3 * mm))
    s.append(StatRow([("220,000", "MT consumed\nnationally per year", ORANGE),
                      ("0", "crop-cutting surveys\nfor this crop", VIOLET),
                      ("28", "trustworthy records\nthat actually exist", BLUE)], w))
    s.append(Spacer(1, 6 * mm))

    s.append(SectionHeading("2", "Project Objectives", w))
    for txt in [
        "<b>Data foundation</b> — integrate district yield, daily weather, "
        "satellite vegetation and soil data into one clean, reproducible dataset.",
        "<b>Feature engineering</b> — derive agronomically meaningful predictors "
        "of thermal, water and canopy status.",
        "<b>Comparative modelling</b> — train classical, deep, symbolic and "
        "physics-hybrid models under one identical protocol.",
        "<b>Honest evaluation</b> — leakage-free cross-validation, paired "
        "significance testing and calibrated prediction intervals.",
        "<b>Attribution and ablation</b> — quantify what each data source and "
        "each predictor actually contributes.",
        "<b>Delivery</b> — a documented REST service and a decision-support "
        "dashboard for non-technical users.",
    ]:
        s.append(B(txt))
    s.append(Spacer(1, 5 * mm))

    s.append(SectionHeading("3", "Methodology", w))
    s.append(Paragraph(
        "<b>Data.</b> Four open streams — DCS district yield, NASA POWER and "
        "CHIRPS weather, MODIS and Sentinel-2 vegetation and land-surface "
        "temperature via Google Earth Engine, and ISRIC SoilGrids — are reduced "
        "to one record per district, season and year.", BODY))
    s.append(Paragraph(
        "<b>Features.</b> 32 predictors in five groups: weather aggregates (9), "
        "vegetation dynamics (11), yield history (5), soil (4) and three "
        "cross-modal interaction terms encoding agronomic hypotheses.", BODY))
    s.append(Paragraph(
        "<b>Models.</b> Nine predictors trained identically — Random Forest, "
        "XGBoost, SVR, LSTM, BiLSTM, 1D-CNN, hybrid CNN-LSTM, symbolic "
        "regression and a physics-residual hybrid — plus a constrained convex "
        "stacking layer.", BODY))
    s.append(Paragraph(
        "<b>Evaluation.</b> <b>Leave-One-Year-Out cross-validation</b>: an entire "
        "year is held out, hyperparameters are tuned inside the training "
        "partition only, and every fitted quantity is re-estimated per fold. A "
        "random split would leak information between districts of the same year "
        "and flatter the result. Models are compared with the paired Wilcoxon "
        "signed-rank test, and split-conformal intervals are attached to every "
        "forecast.", BODY))
    s.append(Spacer(1, 5 * mm))

    s.append(SectionHeading("4", "Key Modules & Components", w))
    rows = [[Paragraph("<font color='#ffffff'><b>Module</b></font>", CELL),
             Paragraph("<font color='#ffffff'><b>Responsibility</b></font>", CELL),
             Paragraph("<font color='#ffffff'><b>Owner</b></font>", CELL)]]
    for mod, resp, owner in [
        ("Data pipeline", "Source ingestion, key reconciliation, season "
                          "windowing, cleaning, 32-predictor engineering", "Sharuja B."),
        ("Prediction engine", "Nine models, LOYO-CV harness, stacking, "
                              "conformal calibration, SHAP attribution", "Arkam B.H.M."),
        ("REST service", "Validated prediction endpoint with interval, "
                         "attribution and provenance; 8 endpoints", "Arkam B.H.M."),
        ("Dashboard", "Choropleth overview, prediction form with context "
                      "prefill, explainability and advisory views", "Shathurya P."),
    ]:
        rows.append([Paragraph(mod, CELL_B), Paragraph(resp, CELL),
                     Paragraph(owner, CELL)])
    s.append(_table(rows, [w * 0.24, w * 0.54, w * 0.22]))
    s.append(Spacer(1, 6 * mm))

    s.append(SectionHeading("5", "Research Novelty", w, color=VIOLET))
    s.append(Callout(
        "1 — Physics-residual hybrid",
        ["A closed-form agronomic backbone (FAO-33 water response, growing",
         "degree days, heat stress) supplies what would otherwise have to be",
         "learned; a Random Forest models only the residual. Just two",
         "parameters are fitted, and they are refitted inside every fold."],
        w, VIOLET, VIOLET_PALE))
    s.append(Spacer(1, 3.5 * mm))
    s.append(Callout(
        "2 — Season-aware hybrid CNN-LSTM",
        ["A CNN branch reads the vegetation trajectory and an LSTM branch the",
         "weather sequence. The Yala/Maha indicator is injected after feature",
         "extraction, so both branches share parameters across seasons and",
         "only the dense head learns season-specific yield baselines."],
        w, BLUE, BLUE_PALE))

    s.append(FrameBreak())

    # ============ RIGHT COLUMN ============
    s.append(SectionHeading("6", "System Architecture", w))
    s += fig(os.path.join(POSTER_FIGS, "architecture.png"), w,
             "Four external data streams feed three build modules; the serving "
             "layer reads persisted artefacts and never trains.")
    s.append(Spacer(1, 5 * mm))

    s.append(SectionHeading("7", "Key Results", w, color=ORANGE))
    s.append(Result(w))
    s.append(Spacer(1, 3.5 * mm))
    s += fig(os.path.join(POSTER_FIGS, "results.png"), w)
    s.append(Spacer(1, 2 * mm))
    s += fig(os.path.join(POSTER_FIGS, "physics.png"), w,
             "The agronomic prior lifts R² by +0.070 over the same learner "
             "used alone — the project's clearest positive finding.")
    s.append(Spacer(1, 4 * mm))

    s.append(SectionHeading("8", "Outcomes & Conclusion", w))
    for txt in [
        "<b>Classical models win decisively.</b> Every deep architecture scores "
        "below a constant-mean predictor; the paired Wilcoxon test rejects "
        "parity at p &lt; 0.0001. At 28 records, capacity is a liability.",
        "<b>Domain knowledge beats extra parameters.</b> The mechanistic "
        "backbone improves R² from 0.020 to 0.091, and the convex stack "
        "independently assigns it the largest weight (0.399).",
        "<b>No single data stream suffices.</b> A six-configuration ablation "
        "puts every individual source below the baseline; only the full set "
        "approaches it, and the two engineered interaction terms outrank every "
        "raw measurement in the SHAP ranking.",
        "<b>The limit is data, not engineering.</b> Identical code reaches "
        "R² 0.842 on a larger reference sample, so the constraint is the "
        "size of the obtainable record.",
        "<b>Next</b> — extend the record backwards and to the Maha season, mask "
        "satellite aggregation to cultivated onion extent, and forecast at "
        "operational lead time.",
    ]:
        s.append(B(txt))
    return s


def build() -> str:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    doc = BaseDocTemplate(OUT_PATH, pagesize=(PAGE_W, PAGE_H),
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=HEADER_H, bottomMargin=FOOTER_H,
                          title="Agro AI — FYP Exhibition Poster",
                          author=", ".join(n for _, n in MEMBERS))
    left = Frame(MARGIN, BODY_BOTTOM, COL_W, BODY_H, id="left",
                 leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    right = Frame(MARGIN + COL_W + GUTTER, BODY_BOTTOM, COL_W, BODY_H, id="right",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="poster", frames=[left, right],
                                       onPage=draw_page)])
    doc.build(story())
    return OUT_PATH


if __name__ == "__main__":
    print(f"Poster written to: {build()}")
    if GROUP_NUMBER.strip("_") == "":
        print("\n!! GROUP_NUMBER is still a placeholder — set it in "
              "src/generate_poster_pdf.py before printing.")

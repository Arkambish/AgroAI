"""Generate the FYP final-defence presentation as a .pptx.

Produces: outputs/Final_Presentation_AgroAI.pptx

Design: 16:9, deep-navy section dividers with an orange accent, off-white content
slides with navy headings. Deliberately NOT a green/agriculture theme. Chart
colours come from src/generate_deck_figures.py, whose palette was validated for
colour-vision deficiency (blue / orange / violet, all-pairs pass).

Every result quoted is from the real collected dataset (outputs/results_real/).
The one synthetic figure is labelled as such on its slide.

Speaker notes are attached to every slide.

Usage:  python src/generate_deck_figures.py && python src/generate_deck_pptx.py
"""

from __future__ import annotations

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(ROOT, "outputs", "deck")
FIGS = os.path.join(ROOT, "outputs", "plots", "figures")
REAL_PLOTS = os.path.join(ROOT, "outputs", "plots_real", "results")
OUT_PATH = os.path.join(ROOT, "outputs", "Final_Presentation_AgroAI.pptx")

# ---- Theme -----------------------------------------------------------------
NAVY = RGBColor(0x0D, 0x36, 0x6B)        # section / title background
NAVY_DEEP = RGBColor(0x09, 0x26, 0x4C)
SURFACE = RGBColor(0xFC, 0xFC, 0xFB)     # content background
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK_2 = RGBColor(0x52, 0x51, 0x4E)
INK_MUTED = RGBColor(0x8A, 0x89, 0x83)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ORANGE = RGBColor(0xEB, 0x68, 0x34)      # accent
BLUE = RGBColor(0x2A, 0x78, 0xD6)
VIOLET = RGBColor(0x4A, 0x3A, 0xA7)
PALE = RGBColor(0xCD, 0xE2, 0xFB)

FONT = "Helvetica Neue"
FONT_FALLBACK = "Arial"

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.85)
BODY_W = W - 2 * MARGIN


# ---- Primitives ------------------------------------------------------------

def _blank(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _rect(slide, left, top, width, height, color: RGBColor):
    from pptx.enum.shapes import MSO_SHAPE
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def _text(slide, left, top, width, height, *, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, word_wrap=True):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = word_wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.paragraphs[0].alignment = align
    return tf


def _run(para, text, *, size, color, bold=False, italic=False, spacing=None):
    r = para.add_run()
    r.text = text
    f = r.font
    f.name = FONT
    f.size = Pt(size)
    f.color.rgb = color
    f.bold = bold
    f.italic = italic
    if spacing is not None:
        para.line_spacing = spacing
    return r


def _para(tf, *, first=False, space_before=0, space_after=6, align=PP_ALIGN.LEFT):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    return p


def _notes(slide, text: str) -> None:
    slide.notes_slide.notes_text_frame.text = text


# ---- Slide templates -------------------------------------------------------

def title_slide(prs, *, eyebrow, title, subtitle, members, supervisor, footer):
    s = _blank(prs)
    _bg(s, NAVY)
    _rect(s, 0, 0, Inches(0.22), H, ORANGE)

    tf = _text(s, Inches(1.15), Inches(1.5), Inches(11.0), Inches(0.4))
    _run(_para(tf, first=True), eyebrow, size=15, color=PALE, bold=True)

    tf = _text(s, Inches(1.15), Inches(2.05), Inches(11.0), Inches(1.9))
    p = _para(tf, first=True, space_after=0)
    _run(p, title, size=40, color=WHITE, bold=True, spacing=1.08)
    p = _para(tf, space_before=10)
    _run(p, subtitle, size=22, color=PALE, spacing=1.15)

    _rect(s, Inches(1.15), Inches(4.62), Inches(1.5), Inches(0.045), ORANGE)

    tf = _text(s, Inches(1.15), Inches(5.0), Inches(11.0), Inches(1.5))
    for i, m in enumerate(members):
        p = _para(tf, first=(i == 0), space_after=3)
        _run(p, m, size=15, color=WHITE)
    p = _para(tf, space_before=12)
    _run(p, supervisor, size=15, color=PALE)

    tf = _text(s, Inches(1.15), Inches(6.75), Inches(11.0), Inches(0.4))
    _run(_para(tf, first=True), footer, size=13, color=RGBColor(0x86, 0xB6, 0xEF))
    return s


def section_slide(prs, *, number, title, blurb):
    s = _blank(prs)
    _bg(s, NAVY_DEEP)
    _rect(s, 0, 0, Inches(0.22), H, ORANGE)

    tf = _text(s, Inches(1.15), Inches(2.6), Inches(10.5), Inches(0.5))
    _run(_para(tf, first=True), number, size=16, color=ORANGE, bold=True)

    tf = _text(s, Inches(1.15), Inches(3.1), Inches(10.5), Inches(1.0))
    _run(_para(tf, first=True), title, size=36, color=WHITE, bold=True)

    tf = _text(s, Inches(1.15), Inches(4.25), Inches(9.5), Inches(1.0))
    _run(_para(tf, first=True), blurb, size=17, color=PALE, spacing=1.3)
    return s


def _wrapped_lines(text: str, *, size_pt: float, width_in: float,
                   char_w=0.52) -> int:
    """Conservative estimate of how many lines `text` occupies in a box."""
    import math
    char_w_in = size_pt * char_w / 72
    per_line = max(1, int(width_in / char_w_in))
    return max(1, math.ceil(len(text) / per_line))


def _content_header(s, title, kicker=None):
    """Draw the slide header and return the y where body content may start.

    The returned top accounts for a title that wraps to two lines, so a long
    title cannot overlap the body beneath it.
    """
    _bg(s, SURFACE)
    _rect(s, 0, 0, W, Inches(0.13), NAVY)
    top = Inches(0.62)
    if kicker:
        tf = _text(s, MARGIN, top, BODY_W, Inches(0.3))
        _run(_para(tf, first=True), kicker.upper(), size=12, color=ORANGE, bold=True)
        top = Inches(1.0)

    lines = _wrapped_lines(title, size_pt=28, width_in=BODY_W / Inches(1))
    title_h = Inches(0.6) * lines
    tf = _text(s, MARGIN, top, BODY_W, title_h)
    _run(_para(tf, first=True), title, size=28, color=NAVY, bold=True)

    base = Inches(1.85) if kicker else Inches(1.5)
    return base + (title_h - Inches(0.6))


def bullets_slide(prs, *, title, kicker=None, bullets, takeaway=None, notes=""):
    """bullets: list of (head, body) or plain strings."""
    s = _blank(prs)
    top = _content_header(s, title, kicker)
    height = H - top - (Inches(1.55) if takeaway else Inches(0.6))
    tf = _text(s, MARGIN, top, BODY_W, height)

    # Step the type down when a slide is text-heavy, so bullets never run into
    # the takeaway band.
    est_lines = sum(
        _wrapped_lines((i[0] + "  " + i[1]) if isinstance(i, tuple) else i,
                       size_pt=17, width_in=BODY_W / Inches(1))
        for i in bullets)
    dense = est_lines > 9 or len(bullets) >= 6
    size = 15.5 if dense else 17
    gap = 8 if dense else 11

    for i, item in enumerate(bullets):
        head, body = item if isinstance(item, tuple) else (None, item)
        p = _para(tf, first=(i == 0), space_before=0 if i == 0 else gap, space_after=2)
        _run(p, "▸  ", size=size, color=ORANGE, bold=True)
        if head:
            _run(p, head + "  ", size=size, color=INK, bold=True)
        _run(p, body, size=size, color=INK_2, spacing=1.22)

    if takeaway:
        _takeaway(s, takeaway)
    _notes(s, notes)
    return s


def _takeaway(s, text):
    band_top = H - Inches(1.35)
    band_h = Inches(0.8)
    _rect(s, MARGIN, band_top, BODY_W, band_h, RGBColor(0xF2, 0xF1, 0xEE))
    _rect(s, MARGIN, band_top, Inches(0.06), band_h, ORANGE)
    # Text box spans the full band, middle-anchored, so a two-line takeaway
    # stays inside the band instead of spilling past it.
    tf = _text(s, MARGIN + Inches(0.3), band_top, BODY_W - Inches(0.6), band_h,
               anchor=MSO_ANCHOR.MIDDLE)
    _run(_para(tf, first=True), text, size=15, color=NAVY, bold=True)


def image_slide(prs, *, title, kicker=None, image, caption=None, notes="",
                max_h=Inches(4.75)):
    s = _blank(prs)
    top = _content_header(s, title, kicker)
    path = image if os.path.isabs(image) else os.path.join(ROOT, image)

    if os.path.exists(path):
        from PIL import Image
        with Image.open(path) as im:
            iw, ih = im.size
        avail_w, avail_h = BODY_W, max_h
        scale = min(avail_w / iw, avail_h / ih)
        w, h = Emu(int(iw * scale)), Emu(int(ih * scale))
        s.shapes.add_picture(path, int((W - w) / 2), top + Inches(0.1), w, h)
        cap_top = top + Inches(0.1) + h + Inches(0.16)
    else:
        tf = _text(s, MARGIN, top + Inches(1.5), BODY_W, Inches(0.5), align=PP_ALIGN.CENTER)
        _run(_para(tf, first=True), f"[missing: {image}]", size=14, color=INK_MUTED, italic=True)
        cap_top = top + Inches(2.2)

    if caption:
        tf = _text(s, MARGIN, cap_top, BODY_W, Inches(0.5), align=PP_ALIGN.CENTER)
        _run(_para(tf, first=True), caption, size=13, color=INK_MUTED)
    _notes(s, notes)
    return s


def stat_slide(prs, *, title, kicker=None, stats, footnote=None, notes=""):
    """stats: list of (value, label, color)."""
    s = _blank(prs)
    top = _content_header(s, title, kicker)
    n = len(stats)
    gap = Inches(0.32)
    card_w = int((BODY_W - gap * (n - 1)) / n)
    card_h = Inches(2.9)
    card_top = top + Inches(0.55)

    for i, (value, label, color) in enumerate(stats):
        left = MARGIN + i * (card_w + gap)
        _rect(s, left, card_top, card_w, card_h, RGBColor(0xF2, 0xF1, 0xEE))
        _rect(s, left, card_top, card_w, Inches(0.07), color)
        tf = _text(s, left + Inches(0.28), card_top + Inches(0.62),
                   card_w - Inches(0.56), Inches(1.2))
        _run(_para(tf, first=True), value, size=48, color=color, bold=True)
        tf = _text(s, left + Inches(0.28), card_top + Inches(1.85),
                   card_w - Inches(0.56), Inches(0.9))
        _run(_para(tf, first=True), label, size=14, color=INK_2, spacing=1.22)

    if footnote:
        tf = _text(s, MARGIN, card_top + card_h + Inches(0.45), BODY_W, Inches(0.8))
        _run(_para(tf, first=True), footnote, size=15, color=INK_2, spacing=1.25)
    _notes(s, notes)
    return s


def table_slide(prs, *, title, kicker=None, header, rows, highlight=None,
                col_widths=None, notes="", takeaway=None):
    s = _blank(prs)
    top = _content_header(s, title, kicker)
    n_rows, n_cols = len(rows) + 1, len(header)
    height = min(Inches(0.42) * n_rows, H - top - Inches(1.7))
    shape = s.shapes.add_table(n_rows, n_cols, MARGIN, top + Inches(0.25),
                               BODY_W, height)
    table = shape.table
    table.first_row = True

    if col_widths:
        total = sum(col_widths)
        for j, wgt in enumerate(col_widths):
            table.columns[j].width = Emu(int(BODY_W * wgt / total))

    for j, h in enumerate(header):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.margin_left = cell.margin_right = Inches(0.1)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        _run(p, h, size=12, color=WHITE, bold=True)

    for i, row in enumerate(rows, start=1):
        is_hl = highlight is not None and (i - 1) == highlight
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = (PALE if is_hl else
                                        (RGBColor(0xF7, 0xF6, 0xF4) if i % 2 else SURFACE))
            cell.margin_left = cell.margin_right = Inches(0.1)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            _run(p, val, size=11.5, color=INK if is_hl else INK_2, bold=is_hl)

    if takeaway:
        _takeaway(s, takeaway)
    _notes(s, notes)
    return s


def two_col_slide(prs, *, title, kicker=None, left_head, left_items,
                  right_head, right_items, takeaway=None, notes=""):
    s = _blank(prs)
    top = _content_header(s, title, kicker)
    col_w = int((BODY_W - Inches(0.55)) / 2)
    height = H - top - (Inches(1.6) if takeaway else Inches(0.6))

    for idx, (head, items, color) in enumerate(
            ((left_head, left_items, ORANGE), (right_head, right_items, BLUE))):
        left = MARGIN + idx * (col_w + Inches(0.55))
        _rect(s, left, top, Inches(0.05), Inches(0.32), color)
        tf = _text(s, left + Inches(0.2), top, col_w - Inches(0.2), Inches(0.35))
        _run(_para(tf, first=True), head, size=17, color=NAVY, bold=True)
        tf = _text(s, left, top + Inches(0.55), col_w, height - Inches(0.55))
        for i, it in enumerate(items):
            p = _para(tf, first=(i == 0), space_before=0 if i == 0 else 9, space_after=2)
            _run(p, "•  ", size=15, color=color, bold=True)
            _run(p, it, size=15, color=INK_2, spacing=1.2)

    if takeaway:
        _takeaway(s, takeaway)
    _notes(s, notes)
    return s


def closing_slide(prs, *, title, lines, footer):
    s = _blank(prs)
    _bg(s, NAVY)
    _rect(s, 0, 0, Inches(0.22), H, ORANGE)
    tf = _text(s, Inches(1.15), Inches(2.5), Inches(10.5), Inches(1.0))
    _run(_para(tf, first=True), title, size=42, color=WHITE, bold=True)
    _rect(s, Inches(1.15), Inches(3.75), Inches(1.5), Inches(0.045), ORANGE)
    tf = _text(s, Inches(1.15), Inches(4.15), Inches(10.0), Inches(1.8))
    for i, line in enumerate(lines):
        p = _para(tf, first=(i == 0), space_after=8)
        _run(p, line, size=17, color=PALE, spacing=1.25)
    tf = _text(s, Inches(1.15), Inches(6.75), Inches(10.5), Inches(0.4))
    _run(_para(tf, first=True), footer, size=13, color=RGBColor(0x86, 0xB6, 0xEF))
    return s


# ---- The deck --------------------------------------------------------------

def build() -> str:
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # 1 — Title
    title_slide(
        prs,
        eyebrow="FINAL YEAR PROJECT  ·  FINAL PRESENTATION  ·  LEVEL 4",
        title="AI-Powered Harvest Yield Prediction",
        subtitle="for Non-Cash Crops (Big Onion) in Sri Lanka",
        members=["214019K   Arkam B.H.M.        ·  ML / DL modelling and serving",
                 "214192G   Sharuja B.             ·  Data engineering and features",
                 "214193K   Shathurya P.         ·  Dashboard and visualisation"],
        supervisor="Supervised by Dr. Firdhous M.F.M.",
        footer="Group Agro AI  ·  Faculty of Information Technology, University of Moratuwa  ·  2026",
    )

    # 2 — Agenda
    bullets_slide(
        prs, title="What we will cover", kicker="Agenda",
        bullets=[
            ("The problem", "no pre-harvest yield forecast exists for big onion in Sri Lanka"),
            ("Related work", "what others have done, and the five gaps we target"),
            ("Our approach", "multi-source data, 32 predictors, nine models, one honest protocol"),
            ("Two novelties", "a physics-residual hybrid and a season-aware CNN-LSTM"),
            ("Results", "what 28 real records actually support — including what failed"),
            ("Contributions, limitations and what comes next", ""),
        ],
        notes="Keep this to 30 seconds. Signal early that we will report negative "
              "results as well as positive ones — that framing protects us later.")

    # 3 — Problem
    stat_slide(
        prs, title="Sri Lanka cannot see its onion harvest coming", kicker="The problem",
        stats=[("220,000", "metric tons of big onion consumed nationally each year", ORANGE),
               ("0", "crop-cutting surveys for big onion — unlike paddy, none exist", VIOLET),
               ("After", "harvest is when the yield figure finally arrives", BLUE)],
        footnote="Import volumes must be committed months before the domestic crop reaches "
                 "market. Today that decision is made against last year's outcome and a "
                 "subjective field assessment with no quantified error.",
        notes="The key line: this is not an improvement to an existing service. There is no "
              "existing service. Yield estimates for big onion come from agricultural "
              "instructors' judgement, not measurement, and they arrive too late to act on.")

    # 4 — Why hard
    two_col_slide(
        prs, title="Why this is technically hard", kicker="The problem",
        left_head="What drives yield",
        left_items=["Soil water availability and irrigation scheduling",
                    "Thermal accumulation across the growing season",
                    "Canopy development and radiation interception",
                    "Pest and disease pressure",
                    "Cultivar choice and fertiliser regime"],
        right_head="What we can actually observe",
        right_items=["Daily weather (reanalysis, spatially complete)",
                     "Satellite vegetation indices and land surface temperature",
                     "Static soil properties from global grids",
                     "District yield history — itself subjectively estimated",
                     "Nothing about management decisions"],
        takeaway="Most of what determines yield is unobserved. That places a ceiling on "
                 "achievable accuracy before any model is chosen.",
        notes="Anticipate the 'why is your R² low' question here, early, on our own terms. "
              "The unobserved-driver argument is the honest answer and it is better made "
              "in the setup than in the defence.")

    # 5 — Aim
    bullets_slide(
        prs, title="Aim and objectives", kicker="Scope",
        bullets=[
            ("Aim", "forecast big onion yield by district and season, before harvest, "
                    "from open data — with honest, calibrated uncertainty"),
            ("1  Data foundation", "integrate yield, weather, satellite and soil to one clean grain"),
            ("2  Feature engineering", "derive agronomically meaningful predictors"),
            ("3  Comparative modelling", "classical, deep, symbolic and physics-hybrid under one protocol"),
            ("4  Honest evaluation", "leakage-free cross-validation, significance tests, conformal intervals"),
            ("5  Attribution and ablation", "quantify what each data source and predictor contributes"),
            ("6  Delivery", "REST service and a decision-support dashboard"),
        ],
        notes="Objective 4 is the one to emphasise. The evaluation protocol is a deliberate "
              "design decision, not a formality, and it is why our numbers are lower than "
              "papers that use random splits.")

    # 6 — Section: related work
    section_slide(prs, number="01", title="Review of others' work",
                  blurb="Four traditions — classical ML, deep and hybrid architectures, "
                        "mechanistic crop models, and the Sri Lankan literature — and "
                        "what none of them covers.")

    # 7 — Related work table
    table_slide(
        prs, title="Where the literature stands", kicker="Related work",
        header=["Work", "Crop / region", "Method", "Limitation for our problem"],
        rows=[["Jabed et al. (2024)", "Multiple / global", "Review of ML and DL", "No small-sample guidance"],
              ["Chikwendu et al. (2025)", "Multiple", "RF, XGBoost, SVR, ANN", "Random split leaks temporal information"],
              ["Rajpoot & Chandrakar (2025)", "Cereals", "Hybrid CNN-LSTM", "Validated only at large sample size"],
              ["Shahhosseini et al. (2021)", "Corn / US", "Crop model + ML", "Needs a full APSIM-class simulator"],
              ["Amarasinghe et al. (2024)", "Rice / Sri Lanka", "Feature-engineered ML", "Paddy has crop-cutting surveys"],
              ["Iqbal et al. (2023)", "Onion / Bangladesh", "Supervised ML", "Climate only; no satellite, no seasons"],
              ["Sutharsan & Yogendran (2023)", "Red onion / Sri Lanka", "Multiple regressors", "Predicts price, not yield"]],
        col_widths=[2.3, 2.0, 2.0, 3.2],
        takeaway="No published work predicts big onion yield for Sri Lankan districts.",
        notes="Do not read the table. Point at the last two rows: the closest Sri Lankan "
              "onion work is about price, and the closest onion yield work is Bangladeshi "
              "and climate-only.")

    # 8 — Gaps
    bullets_slide(
        prs, title="Five gaps we target", kicker="Related work",
        bullets=[
            ("Gap 1", "no big onion yield prediction system exists for Sri Lanka"),
            ("Gap 2", "no guidance on model choice under severe data scarcity for vegetables"),
            ("Gap 3", "mechanistic and learned components are rarely combined at this scale"),
            ("Gap 4", "bimodal Yala/Maha seasonality is not represented architecturally"),
            ("Gap 5", "no decomposition of which data source is worth paying for"),
        ],
        takeaway="Each gap maps to one contribution in this project — we return to this map at the end.",
        notes="Set up the callback. Slide 24 repeats these five and shows what we delivered "
              "against each.")

    # 9 — Section: approach
    section_slide(prs, number="02", title="Our approach",
                  blurb="Four data streams reduced to one grain, 32 engineered predictors, "
                        "nine models, and an evaluation protocol built to not flatter us.")

    # 10 — Architecture
    image_slide(prs, title="Top-level system architecture", kicker="Our approach",
                image=os.path.join(FIGS, "figure_4_1_system_architecture.png"),
                caption="Data integration → modelling and evaluation → REST serving → dashboard. "
                        "Modules are separated by file and HTTP interfaces.",
                notes="Emphasise that the serving layer never trains. Models can be retrained "
                      "without touching the service, and the service restarts without retraining.")

    # 11 — Data sources
    table_slide(
        prs, title="Four data streams, one grain", kicker="Our approach",
        header=["Stream", "Source", "Native grain", "Role"],
        rows=[["District yield", "DCS Sri Lanka; FAOSTAT", "District · season · year", "Target and yield-history predictors"],
              ["Daily weather", "NASA POWER; CHIRPS", "Daily", "Temperature, rainfall, humidity, radiation"],
              ["Vegetation indices", "MODIS, Sentinel-2 via Earth Engine", "5–16 day composite", "Canopy vigour, anomaly, growth rate"],
              ["Land surface temp.", "MODIS MOD11A1", "Daily, 1 km", "Day and night thermal regime"],
              ["Soil properties", "ISRIC SoilGrids250m", "Static, 250 m", "pH, organic carbon, clay, sand"]],
        col_widths=[1.8, 2.6, 2.0, 3.1],
        takeaway="Everything is reduced to one record per district, season and year.",
        notes="Mention the Maha boundary problem: the season runs October to March, so a naive "
              "calendar-year grouping splits one season into two records. We define season as "
              "an explicit month list.")

    # 12 — Features
    two_col_slide(
        prs, title="32 engineered predictors", kicker="Our approach",
        left_head="Measured and derived",
        left_items=["Weather (9) — growing degree days, heat stress days, SPI drought index, "
                    "rainfall totals and extremes",
                    "Satellite (11) — NDVI mean/max/min, anomaly, time-to-peak, growth rate, "
                    "EVI, NDWI, day and night LST",
                    "History (5) — previous season, previous year, three-year average, "
                    "season indicator, previous extent",
                    "Soil (4) — pH, organic carbon, clay and sand fraction"],
        right_head="Interaction terms — encoded hypotheses",
        right_items=["rainfall × NDVI — rain only helps when there is a canopy to use it",
                     "temperature × humidity — evaporative demand and fungal disease pressure",
                     "NDVI × LST — is the green canopy also thermally stressed?",
                     "These three are the only features built from hypothesis rather than "
                     "measurement — and two of them top the SHAP ranking"],
        takeaway="Yield-history features are shifted within district so a record never sees its own target.",
        notes="The leakage point is worth saying out loud: an early version used an unshifted "
              "rolling average and produced R² above 0.99. We caught it by disbelieving the number.")

    # 13 — Models
    table_slide(
        prs, title="Nine models, one protocol", kicker="Our approach",
        header=["Model", "Family", "Why it is in the comparison"],
        rows=[["Random Forest", "Bagged trees", "Variance reduction; robust small-sample baseline"],
              ["XGBoost", "Boosted trees", "Bias reduction under explicit regularisation"],
              ["SVR", "Kernel method", "Capacity independent of sample size"],
              ["LSTM / BiLSTM", "Recurrent", "Temporal integration of the weather sequence"],
              ["1D-CNN", "Convolutional", "Local shape of the NDVI trajectory"],
              ["Hybrid CNN-LSTM", "Two-branch", "NOVELTY — season injected after feature extraction"],
              ["Symbolic regression", "Genetic programming", "A human-readable closed-form equation"],
              ["Physics-residual", "Mechanistic + ML", "NOVELTY — agronomic prior plus learned residual"],
              ["Convex stacking", "Ensemble", "Constrained blend of all of the above"]],
        col_widths=[2.4, 2.2, 4.9],
        notes="Flag the two novelty rows now; the next two slides open them up.")

    # 14 — Section: novelty
    section_slide(prs, number="03", title="Two novelties",
                  blurb="One asks what to do when there is not enough data to learn from. "
                        "The other asks how to represent two monsoon seasons in one network.")

    # 15 — Novelty 1
    bullets_slide(
        prs, title="Novelty 1 — the physics-residual hybrid", kicker="Novelty",
        bullets=[
            ("The problem", "with 28 records, every relationship learned from data spends "
                            "statistical budget we do not have"),
            ("The idea", "supply the agronomy instead of learning it, and let the model "
                         "learn only what the physics cannot explain"),
            ("Stage 1 — mechanistic backbone", "thermal time (growing degree days), water "
                                               "limitation (FAO-33, onion Ky ≈ 1.1), heat stress — "
                                               "multiplied into one suitability term"),
            ("Calibration", "only two parameters — an intercept and a slope — are fitted, "
                            "and they are refitted inside every cross-validation fold"),
            ("Stage 2 — learned residual", "a Random Forest on the difference between "
                                           "observed yield and the calibrated backbone"),
        ],
        takeaway="A prior that is only approximately right is worth more than the degrees of freedom it saves.",
        notes="If asked why not a full crop simulator like APSIM: it needs parameterisation "
              "and calibration data we do not have. Our backbone is three lines of arithmetic "
              "and gets a measurable part of the same benefit.")

    # 16 — Novelty 2
    image_slide(prs, title="Novelty 2 — season-aware hybrid CNN-LSTM", kicker="Novelty",
                image=os.path.join(FIGS, "figure_5_2_cnn_lstm_hybrid.png"),
                caption="The season indicator is concatenated AFTER both branches finish feature "
                        "extraction — so the branches share parameters across seasons and only the "
                        "small dense head learns season-specific baselines.",
                max_h=Inches(4.35),
                notes="The data-efficiency argument: separate per-season models would halve the "
                      "sample per parameter. Appending season to the input would let the filters "
                      "specialise on season and dissipate the same advantage more subtly. "
                      "IMPORTANT — be upfront that the collected data is Yala-only, so this "
                      "specific claim is tested on synthetic data, not real. Do not oversell it.")

    # 17 — Evaluation protocol
    two_col_slide(
        prs, title="How we evaluate — and why it lowers our score", kicker="Protocol",
        left_head="What most papers do",
        left_items=["Split records at random into train and test",
                    "Districts from the same year land on both sides",
                    "They share a weather regime and a monsoon anomaly",
                    "The model effectively sees the answer for the year it predicts",
                    "Reported scores are optimistic and do not survive deployment"],
        right_head="What we do",
        right_items=["Leave-One-Year-Out: hold out an entire year, rotate through all seven",
                     "Hyperparameters chosen by an inner search inside the training partition only",
                     "Every fitted quantity — including the physics calibration — refitted per fold",
                     "Models compared with the paired Wilcoxon signed-rank test",
                     "Split-conformal prediction intervals attached to every forecast"],
        takeaway="A random split would have given us far better-looking numbers. It would also have been wrong.",
        notes="This is the most important methodological slide. If a panel member questions "
              "the low R², return here.")

    # 18 — Section: results
    section_slide(prs, number="04", title="Results",
                  blurb="Everything that follows is measured on the 28 seasonal records we "
                        "actually collected. One slide, clearly labelled, uses synthetic data.")

    # 19 — Dataset reality
    stat_slide(
        prs, title="What the data actually is", kicker="Results",
        stats=[("28", "seasonal records collected — 4 districts × 7 years", VIOLET),
               ("32", "candidate predictors — more features than observations", ORANGE),
               ("1", "season only — Yala; no Maha in the collected record", BLUE)],
        footnote="Anuradhapura, Kurunegala, Matale and Polonnaruwa, 2019–2025. Mean yield "
                 "16.39 MT/Ha (range 8.50–24.06). Each cross-validation fold trains on 24 records. "
                 "Read every result that follows against this slide.",
        notes="Do not apologise for this. State it as a finding about the domain: this is how "
              "much trustworthy data exists for this crop. The Yala-only limitation is what "
              "prevents us validating the season-injection claim on real data — say so before "
              "anyone asks.")

    # 20 — Model comparison
    image_slide(prs, title="Model comparison under Leave-One-Year-Out CV", kicker="Results",
                image=os.path.join(DECK, "model_comparison.png"),
                caption="Physics-residual hybrid leads at RMSE 3.90 MT/Ha, R² 0.091. "
                        "Every deep architecture falls below the mean predictor.",
                notes="Two things to say. First, the winner is the physics hybrid — the novelty "
                      "pays. Second, the whole deep family is below the baseline and the two "
                      "convolutional models are catastrophic at R² near −7.")

    # 21 — DL finding
    bullets_slide(
        prs, title="Finding 1 — deep learning fails at this scale", kicker="Results",
        bullets=[
            ("The outcome", "all four deep architectures score below a constant-mean predictor; "
                            "the paired Wilcoxon test rejects parity with the classical family at p < 0.0001"),
            ("The hybrid CNN-LSTM does not beat its own components", "it sits between the CNN and the LSTM"),
            ("Why", "representation learning trades sample efficiency for expressive power — "
                    "at 24 training records per fold there is nothing to trade with"),
            ("It is not a bug", "the same code reaches R² 0.842 on a larger sample (slide 27)"),
            ("It survives scale", "even at ~160 records the classical models still lead 0.842 to 0.271"),
        ],
        takeaway="Actionable guidance the literature does not give: at this sample size, do not start with deep learning.",
        notes="Own this result rather than defending it. The published hybrid architectures are "
              "validated on datasets three orders of magnitude larger. Showing where the "
              "advantage disappears is a genuine contribution.")

    # 22 — Physics ablation
    image_slide(prs, title="Finding 2 — the agronomic prior earns its place", kicker="Results",
                image=os.path.join(DECK, "physics_ablation.png"),
                caption="Backbone alone is worse than the mean. Learner alone reaches 0.020. "
                        "Together they reach 0.091 — a +0.070 lift over the same learner.",
                max_h=Inches(4.3),
                notes="The mechanism matters more than the magnitude. The backbone helps not "
                      "because it is accurate — it is not — but because it removes work from "
                      "the learner. Honest caveat: heat stress days are zero throughout the "
                      "Yala data, so the benefit comes from thermal time and water only.")

    # 23 — Stacking
    image_slide(prs, title="Finding 3 — stacking beats the mean, not the best model", kicker="Results",
                image=os.path.join(DECK, "stacking.png"),
                caption="The learned convex blend clearly beats the equal-weight mean — the "
                        "forecast-combination puzzle does not hold here — but no blend beats "
                        "the single physics-residual hybrid.",
                max_h=Inches(4.3),
                notes="The convex optimiser assigned 0.399 to the physics hybrid and exactly "
                      "zero to the CNN — an independent confirmation of Finding 2 by a "
                      "completely different route. We report this as a negative result and "
                      "serve the single model, not the stack.")

    # 24 — Ablation
    image_slide(prs, title="Which data source is worth paying for?", kicker="Results",
                image=os.path.join(DECK, "ablation_sources.png"),
                caption="Six configurations, identical model, protocol and seed. Only the "
                        "full set approaches the baseline.",
                max_h=Inches(4.3),
                notes="Two honest readings. Soil alone looks strongest among single sources, "
                      "but static per-district features act as a district identifier — that is "
                      "a baseline effect, not soil science. And weather+satellite is worse than "
                      "either alone: adding features adds variance faster than information. "
                      "Textbook curse of dimensionality, made visible.")

    # 25 — Per district
    image_slide(prs, title="Predictability varies sharply by district", kicker="Results",
                image=os.path.join(DECK, "per_district.png"),
                caption="Anuradhapura is most predictable; Kurunegala is worst by R² but "
                        "better than Matale by absolute error.",
                max_h=Inches(4.2),
                notes="Explain the apparent contradiction — it is a good sign of understanding. "
                      "R² is normalised by each district's own variance and Kurunegala's spread "
                      "is narrowest, so a moderate absolute error consumes a large share of a "
                      "small variance. For an operational user, absolute error is what matters.")

    # 26 — SHAP
    image_slide(prs, title="What drives the forecast", kicker="Results",
                image=os.path.join(DECK, "shap_top.png"),
                caption="Two of the three engineered interaction terms outrank every raw "
                        "measurement they were built from.",
                max_h=Inches(4.3),
                notes="This validates the feature engineering directly. In a regime where the "
                      "model cannot discover interactions from data, the interactions have to "
                      "be supplied. Caveat if pressed: attributions describe what the fitted "
                      "model does, not necessarily what nature does.")

    # 27 — Uncertainty
    image_slide(prs, title="Every forecast ships with a calibrated interval", kicker="Results",
                image=os.path.join(DECK, "conformal.png"),
                caption="Split-conformal, distribution-free, at 90% nominal coverage. "
                        "Interval width ranks the models the same way point error does.",
                max_h=Inches(4.3),
                notes="Be honest about the coverage figure: empirical coverage is 1.00 because "
                      "we calibrate and measure on the same 28 residuals, and the finite-sample "
                      "correction lands near the maximum residual. The intervals are "
                      "conservative, not tight. But a wide honest interval beats a narrow "
                      "dishonest one — ±6.85 on a mean of 16.39 tells a planner to hedge.")

    # 28 — Synthetic validation
    image_slide(prs, title="Is the pipeline correct? Yes — and here is the proof", kicker="Architecture validation",
                image=os.path.join(DECK, "sample_size.png"),
                caption="SYNTHETIC REFERENCE. The right-hand bar is not a claim about Sri Lankan "
                        "onion yield — it shows the same code on an adequate sample.",
                max_h=Inches(4.2),
                notes="This is the answer to 'is your low R² a bug?'. Identical pipeline, "
                      "identical code, only the input differs. 0.020 on 28 records becomes "
                      "0.842 on ~160. The limiting factor is the sample, not the "
                      "implementation. Be scrupulous that this bar is labelled synthetic.")

    # 29 — Contributions
    table_slide(
        prs, title="Contributions against the five gaps", kicker="Contributions",
        header=["Gap", "What we delivered"],
        rows=[["1  No system for big onion in Sri Lanka",
               "First end-to-end pipeline, REST service and dashboard for the crop"],
              ["2  No small-sample model guidance",
               "Nine families, one protocol, paired significance tests — with a replication at larger n"],
              ["3  Mechanistic + learned rarely combined",
               "Closed-form FAO-33 / GDD backbone + residual learner, +0.070 R², independently confirmed by stacking weights"],
              ["4  Bimodal seasonality not architectural",
               "Season-injection design contributed; validation incomplete — collected data is Yala-only"],
              ["5  No data-source decomposition",
               "Six-configuration ablation on real and synthetic data, plus conformal intervals per model"]],
        col_widths=[3.4, 6.1],
        notes="Note gap 4 honestly — design contributed, validation incomplete. A panel will "
              "respect the distinction far more than an overclaim, and they will find it anyway.")

    # 30 — Limitations
    two_col_slide(
        prs, title="What bounds these conclusions", kicker="Limitations",
        left_head="Limitations",
        left_items=["28 records is the binding constraint on every number",
                    "Yala only — the season-injection claim is untested on real data",
                    "Conformal coverage of 1.00 is an artefact of a 28-point calibration set",
                    "Cultivar, irrigation, fertiliser and pest pressure are all unobserved",
                    "Ground-truth yield is itself subjectively estimated",
                    "District-level aggregation hides within-district heterogeneity"],
        right_head="Further work, in priority order",
        right_items=["Extend the record — backfill the satellite archive, add Maha and more districts",
                     "Mask satellite aggregation to cultivated onion extent, not whole districts",
                     "Extend the mechanistic backbone — soil water balance, stage-dependent sensitivity",
                     "Add management covariates, even coarse district-level ones",
                     "Evaluate at operational lead time — forecast 4–8 weeks before harvest",
                     "Field-validate the dashboard with DCS and district officers"],
        notes="Leading with limitations is a strength in a defence. Every one of these is "
              "specific and most trace back to sample size. The lead-time point is the one a "
              "practitioner would actually raise: we currently use full-season predictors.")

    # 31 — Conclusion
    bullets_slide(
        prs, title="Conclusion", kicker="Wrapping up",
        bullets=[
            ("We built the capability", "reproducible pipeline, nine models, leakage-free protocol, "
                                        "calibrated uncertainty, attribution, REST service and dashboard"),
            ("Best model", "physics-residual hybrid — R² 0.091, MAE 3.35 MT/Ha, 23.3% MAPE on real data"),
            ("The 0.75 target was not met", "and the reason is the size of the obtainable record, "
                                            "not the construction of the system"),
            ("The durable findings are methodological", "deep learning fails at this scale; a lightweight "
                                                        "agronomic prior measurably helps; estimated blend "
                                                        "weights beat uniform averaging; engineered "
                                                        "interactions outrank raw measurements"),
            ("The path forward is concrete", "a longer record, a crop mask, a fuller backbone, "
                                             "management covariates"),
        ],
        takeaway="Accuracy is bounded by an information constraint, not an engineering one — and we can name what would lift it.",
        notes="Land on the framing: for a crop on which national import decisions turn and for "
              "which no forecast exists at all, a calibrated and explainable pre-harvest "
              "estimate with a stated interval is worth having. We established that it can be "
              "built and what it will take to make it good.")

    # 32 — Close
    closing_slide(
        prs, title="Thank you",
        lines=["Questions and discussion",
               "",
               "Full report, source code, trained models and all result artefacts "
               "are available in the project repository."],
        footer="Group Agro AI  ·  Arkam B.H.M. · Sharuja B. · Shathurya P.  ·  University of Moratuwa 2026",
    )

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    prs.save(OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    path = build()
    print(f"Presentation written to: {path}")

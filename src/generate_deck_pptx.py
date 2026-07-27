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
            ("Our approach", "multi-source data, real daily weather, one honest protocol"),
            ("The method", "PADR — an agronomic model whose crop constants are estimated, not assumed"),
            ("Results", "what we found when we audited our own data, and what 28 records support"),
            ("Two findings we withdraw", "and why reporting them is the point"),
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
                  blurb="Four data streams reduced to one grain, 37,988 real daily weather "
                        "records, and an evaluation protocol built to not flatter us.")

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
        prs, title="Engineered predictors, after the cull", kicker="Our approach",
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
        prs, title="What we compare, and against what", kicker="Our approach",
        header=["Model", "Family", "Why it is in the comparison"],
        rows=[["Train mean", "Naive", "THE BAR — best available without knowing the held-out year"],
              ["Oracle year-mean", "Reference", "NOT ACHIEVABLE — bounds what perfect year knowledge buys"],
              ["Random Forest", "Bagged trees", "Variance reduction; robust small-sample baseline"],
              ["XGBoost", "Boosted trees", "Bias reduction under explicit regularisation"],
              ["SVR", "Kernel method", "Capacity independent of sample size"],
              ["District mean / persistence", "Naive", "Do district identity or last year carry the signal?"],
              ["PADR", "Mechanistic, estimated", "THE METHOD — 17 parameters, constants fitted from data"]],
        col_widths=[2.6, 2.3, 4.6],
        notes="The two reference rows matter more than the models. Without the oracle row nobody "
              "can tell whether a negative score is the model's fault or the protocol's.")

    # 14 — Section: the method
    section_slide(prs, number="03", title="The method",
                  blurb="A seventeen-parameter agronomic response model whose crop "
                        "constants are estimated from data rather than assumed.")

    # 15 — PADR
    bullets_slide(
        prs, title="PADR — phenology-aligned differentiable response", kicker="The method",
        bullets=[
            ("The shape", "yield = attainable yield × ∫ β(τ) · f_temp · f_water · f_waterlog dτ"),
            ("What is new", "the FAO-33 and thermal constants are ESTIMATED, not fixed — "
                            "existing hybrids freeze the crop model and fit ML on its residual"),
            ("Shrinkage to physics", "each constant is penalised toward its textbook value, so it "
                                     "moves only when the data pay for the move"),
            ("Seventeen parameters", "against 44,929 in the CNN-LSTM it replaces — a model this "
                                     "small is the only kind 24 training rows can support"),
            ("Fitted by L-BFGS-B", "multi-start, agronomic box bounds, refit from scratch inside "
                                   "every fold"),
        ],
        takeaway="The fitted constants are the scientific output. They survive even when the "
                 "prediction does not.",
        notes="The distinction to hammer: Shahhosseini et al. run a crop model with published "
              "coefficients and fit a learner to the residual. We estimate the coefficients. "
              "That is a method claim, not a domain claim, and it is what the supervisor asked "
              "for.")

    # 16 — Phenological time
    bullets_slide(
        prs, title="Weather on a thermal clock, not a calendar", kicker="The method",
        bullets=[
            ("The problem", "'September rainfall' means a different developmental moment in "
                            "each district-year"),
            ("Satellite could not solve it", "onion is 0.002–0.89% of any district's land area, so "
                                             "district-mean NDVI measures paddy and scrub — "
                                             "25 of 28 district-years failed to anchor"),
            ("What worked instead", "harvest date from the DCS monthly production distribution — "
                                    "genuinely crop-specific, and it moves across 51 days"),
            ("Thermal time backwards", "planting located by accumulating degree-days back from "
                                       "harvest; 28 of 28 anchored, zero fallbacks"),
            ("It behaves like physics", "hot Anuradhapura completes a season in 78–86 days; "
                                        "cooler Matale needs 90–99 for the same heat"),
        ],
        notes="If asked why not NDVI: it is an area argument, not a sensor argument. A crop on "
              "0.1% of the pixels cannot move a district mean. We tried it, measured the "
              "failure, and report it.")

    # 17 — Protocol
    bullets_slide(
        prs, title="How we evaluate — and why it lowers our score", kicker="Protocol",
        bullets=[
            ("Leave-one-year-out", "hold out a whole year; every fitted quantity, including all "
                                   "scaling, estimated inside the fold"),
            ("Why not a random split", "records from one year share a weather regime; a random "
                                       "split would report a far more flattering and entirely "
                                       "misleading number"),
            ("Four leaks found and removed", "anomalies had been standardised on the full panel; "
                                             "the target had been winsorised at full-sample "
                                             "percentiles"),
            ("Yield lags dropped, not repaired", "under LOYO the row for year k+1 carries year k's "
                                                 "observed yield — no clean fix inside this protocol"),
            ("Observations weighted by area", "cells span 3.5 to 1,765 hectares; treating them as "
                                              "equally reliable is not defensible"),
        ],
        takeaway="An honest protocol is why our numbers are lower than published work using random splits.",
        notes="This slide is our insurance. Every low number later is a consequence of choices "
              "defended here.")

    # 18 — Section: results
    section_slide(prs, number="04", title="Results",
                  blurb="What we found when we audited our own data — and what the corrected "
                        "panel can and cannot support.")

    # 19 — Data integrity
    stat_slide(
        prs, title="We audited our own dataset. It did not survive.", kicker="Results",
        stats=[("40%", "of the target variable was fabricated — 50 of 124 month-rows", ORANGE),
               ("442", "MT/ha implied by one record; onion's world record is ~100", VIOLET),
               ("0.68", "correlation between the old target and the corrected one", BLUE)],
        footnote="The fabrication reached the TARGET, not just the covariates: yield varies "
                 "month to month within every cell and the target was their unweighted mean. "
                 "Rebuilt from 87 genuine DCS records as total production over total harvested area.",
        notes="Lead with this. It is the least comfortable slide and the most credible one. A "
              "panel that sees us find and report our own contamination will trust everything "
              "that follows.")

    # 20 — The ceiling
    image_slide(prs, title="The 0.75 target was not difficult. It was unattainable.",
                kicker="Results",
                image=os.path.join(REAL_PLOTS, "variance_ceiling.png"),
                caption="64% of variance lies between years and leave-one-year-out removes it by "
                        "construction; measurement error is 54% of what remains within a year.",
                notes="This is the single most important slide in the deck. The proposal target "
                      "was set before anyone knew the structure of the record. No model of any "
                      "architecture could have reached 0.75 here. Say the number: the ceiling is "
                      "0.162.")

    # 21 — Scoreboard
    image_slide(prs, title="Every model loses to predicting the mean", kicker="Results",
                image=os.path.join(REAL_PLOTS, "padr_scoreboard.png"),
                caption="Leave-one-year-out R² on the corrected target. The oracle row uses the "
                        "held-out year's own mean and is not achievable — it bounds what perfect "
                        "knowledge of the year effect would buy.",
                notes="Do not apologise for this slide. Read against the ceiling it is the "
                      "expected outcome, and the next slide explains the mechanism.")

    # 22 — Why
    image_slide(prs, title="Why: the stress index cannot move far enough", kicker="Results",
                image=os.path.join(REAL_PLOTS, "stress_vs_yield.png"),
                caption="Stress index varies 8%. Observed yield varies 35%. Thermal stress is "
                        "near-constant in the tropics, and water deficit almost never binds under "
                        "tank irrigation.",
                notes="The key sentence: a model whose output varies eight per cent cannot "
                      "explain a target that varies thirty-five, whatever coefficients you give "
                      "it. This is structural, not a tuning failure. And removing 2022 and 2024 "
                      "makes it relatively WORSE, so the signal is absent, not masked.")

    # 23 — Power
    image_slide(prs, title="Would we have found a signal if one were there?",
                kicker="Results — the linchpin",
                image=os.path.join(REAL_PLOTS, "power_curve.png"),
                caption="On simulated panels PADR recovers a weather signal driving as "
                        "little as 6% of yield variance at n=28. It recovered none from the "
                        "real data — so the true signal is below 6%.",
                notes="This is the slide that turns 'our model failed' into 'the signal is "
                      "not there'. A negative result from an underpowered instrument says "
                      "nothing about the world; this measures the instrument. Two honesty "
                      "points if pressed: the curve is non-monotonic because we ran only two "
                      "replicates per amplitude, and we used a single optimiser start from the "
                      "literature values — which is deliberately OPTIMISTIC, so failing to "
                      "detect under those conditions errs the safe way.")

    # 24 — Learned constants
    image_slide(prs, title="FAO-33 overstates weather sensitivity for this crop",
                kicker="Results — the positive finding",
                image=os.path.join(REAL_PLOTS, "learned_constants.png"),
                caption="Pinning the coefficients to published values produces the right amount "
                        "of variation (35%) but the worst score of any configuration (R² −1.54). "
                        "T_opt and W_max are recovered to within 3%; Ky and T_crit are NOT "
                        "identifiable at n=28 and are not claimed.",
                notes="Strongest positive result, and transferable: learning the constants does "
                      "not add explanatory power so much as REMOVE spurious sensitivity — stress "
                      "CV falls 22.4% to 8.1% while R² improves 0.57. IMPORTANT CAVEAT: our "
                      "recovery experiment shows Ky returns its prior (1.108) when fitted to data "
                      "generated with 0.966. The tight fold spread on Ky was the shrinkage prior, "
                      "not evidence — precision without accuracy. So we claim T_opt and W_max, "
                      "not Ky. The FAO-overstatement finding survives because it rests on the "
                      "ablation contrast, not on any single point estimate.")

    # 25 — Ablations
    image_slide(prs, title="Two claims survived. Two did not.", kicker="Results",
                image=os.path.join(REAL_PLOTS, "ablation_claims.png"),
                caption="Each design claim tested against its own control. Learning the physics "
                        "and moderate shrinkage are supported; thermal-time indexing and the "
                        "waterlogging term are not.",
                notes="Volunteer the nulls. An ablation in which every proposed component happens "
                      "to help is not a credible ablation, and a panel knows it. Thermal time is "
                      "negligible because temperature barely varies here; waterlogging binds in "
                      "3.5% of intervals in one year.")

    # 26 — Beta curve
    image_slide(prs, title="When does weather matter for onion?", kicker="Results",
                image=os.path.join(REAL_PLOTS, "beta_curve.png"),
                caption="Estimated sensitivity declines monotonically — roughly seven times more "
                        "weight on establishment than on harvest. Band shows the range across folds.",
                notes="Hedge this one appropriately: the underlying stress signal is weak, so the "
                      "curve is estimated from little information. The shape is stable across "
                      "folds and agronomically plausible for a crop whose bulb is set early, but "
                      "it is not a well-identified estimate.")

    # 27 — Uncertainty
    table_slide(
        prs, title="Honest intervals — and what they reveal", kicker="Results",
        header=["Model", "Coverage", "Half-width (MT/ha)"],
        rows=[["Oracle year-mean (not achievable)", "0.929", "6.70"],
              ["Train mean", "0.893", "14.90"],
              ["PADR", "0.893", "15.29"],
              ["XGBoost", "0.929", "16.42"],
              ["Random Forest", "0.929", "17.63"]],
        col_widths=[4.2, 2.4, 2.9],
        notes="The interim report said coverage was 1.000 for all twelve models. That was a "
              "tautology — the quantile was computed from the same residuals it was then "
              "measured on. Year-blocked cross-conformal gives 0.911 against a nominal 0.90. "
              "But the width is the finding: plus or minus 15.3 on a mean of 17.9 is plus or "
              "minus 85%. These forecasts are not decision-useful, and the interval is the "
              "evidence for saying so.")

    # 28 — What we withdrew
    bullets_slide(
        prs, title="Two findings we are withdrawing", kicker="Corrections",
        bullets=[
            ("Withdrawn — 'deep learning fails at this scale'",
             "the sequence tensor fed to the LSTM and CNN models was manufactured from the "
             "seasonal aggregates through a fixed sine curve; it was a deterministic, invertible "
             "function of the tabular features the classical models already had, carrying zero "
             "extra information"),
            ("Withdrawn — 'synthetic R² 0.842 validates the architecture'",
             "that data was generated by a known functional form inside our own data loader, with "
             "the vegetation index built as a function of the yield it later predicted — "
             "recovering it proves only that an estimator can invert a function it was handed"),
            ("What replaced them",
             "37,988 genuine daily NASA POWER records now feed the sequence models; a proper "
             "comparison is stated as further work rather than claimed here"),
        ],
        takeaway="Reporting this is better than letting a convenient negative result stand unexamined.",
        notes="Expect a question here. The answer: we found these ourselves, before submission, "
              "by auditing our own inputs. That is the process working.")

    # 29 — Contributions
    table_slide(
        prs, title="What this work contributes", kicker="Contributions",
        header=["Contribution", "Evidence"],
        rows=[["Data integrity finding",
               "40% fabricated target identified and rebuilt from 87 genuine DCS records"],
              ["A quantified account of what the panel supports",
               "64% year / 2% district variance split; measurement error 54% of within-year; "
               "attainable R² bounded at 0.162"],
              ["Locally estimated agronomic coefficients",
               "+0.566 R² over fixed physics; FAO-33 shown to overstate weather sensitivity ~4×"],
              ["Diagnosis that the agro-climatic channel is inactive",
               "8% stress variation against 35% in yield; removing anomalous years worsens the fit"],
              ["Methodological corrections",
               "four leaks removed, fabricated sequences replaced, tautological conformal fixed, "
               "extent weighting introduced"]],
        col_widths=[3.4, 6.1],
        notes="Note that four of five contributions are things we found by being sceptical of our "
              "own pipeline. That is the story of this project.")

    # 30 — Limitations
    two_col_slide(
        prs, title="What bounds these conclusions", kicker="Limitations",
        left_head="Limitations",
        left_items=["28 records, 4 districts, 7 years, Yala only — no Maha data exists",
                    "Kurunegala and Matale share one weather grid cell — identical daily series",
                    "Kurunegala's NDVI is a Matale proxy; its soil profile is absent entirely",
                    "Six records excluded on an agronomic bound, not source verification",
                    "The 2022 fertilizer-ban attribution is timing, not established causation",
                    "No fertilizer, irrigation, cultivar or price data was available"],
        right_head="Further work, in priority order",
        right_items=["Collect input and management data — this is where the signal actually is",
                     "Re-run the ML vs DL comparison properly on the real daily sequences",
                     "Mask satellite aggregation to cultivated onion parcels",
                     "Finer reanalysis to separate Kurunegala from Matale meteorologically",
                     "Verify the six flagged records against the DCS publication",
                     "Apply the ceiling calculation across published short-panel yield studies"],
        notes="The first item is the real conclusion. Our finding tells the next person exactly "
              "what to collect, and it is not more weather data.")

    # 31 — Conclusion
    bullets_slide(
        prs, title="Conclusion", kicker="Wrapping up",
        bullets=[
            ("We asked whether weather predicts onion yield here", "and answered it: it does not, "
                                                                   "at district-season resolution"),
            ("The target was unattainable, and we proved it", "64% of variance is removed by the "
                                                              "protocol; measurement error takes half "
                                                              "the rest; the ceiling is 0.162"),
            ("The mechanistic model is what made the answer possible", "a random forest scoring "
                                                                       "−0.56 tells you nothing; PADR "
                                                                       "reports which mechanisms are "
                                                                       "inactive and by how much"),
            ("One transferable positive result", "FAO-33 coefficients overstate weather sensitivity "
                                                 "for big onion under tank irrigation — calibrate locally"),
            ("We corrected our own record", "a fabricated target, a manufactured input tensor and a "
                                            "tautological uncertainty calculation, all found and reported"),
        ],
        takeaway="A well-diagnosed negative result, with its errors stated openly, is worth more "
                 "than a favourable number that cannot be defended.",
        notes="Land here. We did not get the number we wanted. We got something more useful: an "
              "explanation of why that number was never available, and a clear statement of what "
              "the next person should collect.")

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

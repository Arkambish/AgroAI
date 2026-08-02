"""
Builds the 15-minute Agro AI final-year-project presentation (13 slides, 16:9).

Design system: agricultural green / dark green / cream, with onion-gold accents.
All diagrams are drawn from native PowerPoint shapes (no images), so every slide
stays editable. Speaker notes are embedded in each slide's notes pane.

Run:  python src/build_viva_deck.py
Out:  outputs/deck/AgroAI_Final_Presentation_15min.pptx
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# ----------------------------------------------------------------------------- palette
DEEP = RGBColor(0x0E, 0x3B, 0x2B)
GREEN = RGBColor(0x2F, 0x7D, 0x4F)
LEAF = RGBColor(0x4E, 0x9E, 0x63)
MINT = RGBColor(0xE8, 0xF1, 0xE7)
MINT2 = RGBColor(0xF3, 0xF8, 0xF2)
CREAM = RGBColor(0xFB, 0xF8, 0xF1)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GOLD = RGBColor(0xC8, 0x7A, 0x1E)
GOLD_D = RGBColor(0x9B, 0x5A, 0x12)
GOLD_L = RGBColor(0xFB, 0xEF, 0xDC)
INK = RGBColor(0x1D, 0x2A, 0x22)
BODY = RGBColor(0x3A, 0x4A, 0x40)
MUTED = RGBColor(0x6B, 0x7A, 0x70)
LINE = RGBColor(0xD6, 0xE0, 0xD6)
GREY_L = RGBColor(0xED, 0xEF, 0xEC)
GREY_B = RGBColor(0x7E, 0x8A, 0x82)
PALE = RGBColor(0xC8, 0xDF, 0xD1)   # body text on deep green
PALE2 = RGBColor(0xBF, 0xD7, 0xC6)  # secondary text on deep green
PALE3 = RGBColor(0x9F, 0xC7, 0xAB)  # tertiary / eyebrow on deep green

F = "Calibri"  # swap to "Aptos" here if the presenting machine has Office 2024+

SW, SH = 13.333, 7.5
ML, MR = 0.62, 0.62
CW = SW - ML - MR  # 12.093


# ----------------------------------------------------------------------------- helpers
def T(text, sz=11, b=False, c=BODY, al="l", sb=0, sa=2, it=False, spc=None, ln=None):
    """One paragraph spec."""
    return dict(text=text, sz=sz, b=b, c=c, al=al, sb=sb, sa=sa, it=it, spc=spc, ln=ln)


_AL = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}


def write(tf, items, anchor=None, wrap=True, margins=(0, 0, 0, 0)):
    tf.word_wrap = wrap
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [
        Inches(m) for m in margins
    ]
    if anchor is not None:
        tf.vertical_anchor = anchor
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = _AL[it["al"]]
        p.space_before = Pt(it["sb"])
        p.space_after = Pt(it["sa"])
        if it["ln"]:
            p.line_spacing = it["ln"]
        r = p.add_run()
        r.text = it["text"]
        f = r.font
        f.name, f.size, f.bold, f.italic = F, Pt(it["sz"]), it["b"], it["it"]
        f.color.rgb = it["c"]
        if it["spc"]:
            r._r.get_or_add_rPr().set("spc", str(int(it["spc"] * 100)))
    return tf


def tbox(slide, x, y, w, h, items, anchor=MSO_ANCHOR.TOP, margins=(0, 0, 0, 0)):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    write(tb.text_frame, items, anchor=anchor, margins=margins)
    return tb


def shp(slide, x, y, w, h, kind=MSO_SHAPE.ROUNDED_RECTANGLE, fill=None, line=None,
        lw=1.0, adj=0.10, grad=None, angle=0):
    s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    try:
        if adj is not None and len(s.adjustments):
            s.adjustments[0] = adj
    except Exception:
        pass
    if grad:
        try:
            s.fill.gradient()
            s.fill.gradient_angle = angle
            st = s.fill.gradient_stops
            st[0].color.rgb, st[0].position = grad[0], 0.0
            st[1].color.rgb, st[1].position = grad[1], 1.0
        except Exception:
            s.fill.solid()
            s.fill.fore_color.rgb = grad[0]
    elif fill is not None:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    else:
        s.fill.background()
    if line is not None:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    else:
        s.line.fill.background()
    s.text_frame.word_wrap = True
    return s


def card(slide, x, y, w, h, items, fill=MINT2, line=LINE, adj=0.06, pad=0.22,
         anchor=MSO_ANCHOR.TOP, accent=None):
    shp(slide, x, y, w, h, fill=fill, line=line, adj=adj)
    if accent:
        shp(slide, x, y + 0.14, 0.055, h - 0.28, kind=MSO_SHAPE.RECTANGLE,
            fill=accent, adj=None)
    tbox(slide, x + pad, y + 0.15, w - 2 * pad, h - 0.3, items, anchor=anchor)


def pill(slide, x, y, w, h, text, fill=MINT, line=None, c=DEEP, sz=10.5, b=True,
         al="c", adj=0.5):
    s = shp(slide, x, y, w, h, fill=fill, line=line, adj=adj)
    write(s.text_frame, [T(text, sz, b, c, al, sa=0, ln=0.92)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.07, 0.07, 0.02, 0.02))
    return s


def box(slide, x, y, w, h, lines, fill=MINT, line=None, adj=0.09):
    s = shp(slide, x, y, w, h, fill=fill, line=line, adj=adj)
    write(s.text_frame, lines, anchor=MSO_ANCHOR.MIDDLE,
          margins=(0.09, 0.09, 0.03, 0.03))
    return s


def arrow_r(slide, x, y, w=0.26, h=0.16, c=LEAF):
    shp(slide, x, y - h / 2, w, h, kind=MSO_SHAPE.RIGHT_ARROW, fill=c, adj=None)


def arrow_d(slide, x, y, w=0.16, h=0.20, c=LEAF):
    shp(slide, x - w / 2, y, w, h, kind=MSO_SHAPE.DOWN_ARROW, fill=c, adj=None)


def icon(slide, x, y, d, glyph, fill=GREEN, c=WHITE, sz=13):
    s = shp(slide, x, y, d, d, kind=MSO_SHAPE.OVAL, fill=fill, adj=None)
    write(s.text_frame, [T(glyph, sz, True, c, "c", sa=0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0, 0, 0, 0))


# ----------------------------------------------------------------------------- chrome
def new_slide(prs, bg=CREAM):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    shp(s, 0, 0, SW, SH, kind=MSO_SHAPE.RECTANGLE, fill=bg, adj=None)
    return s


def header(slide, kicker, title, sub=None, kc=GREEN):
    tbox(slide, ML, 0.36, CW * 0.8, 0.26,
         [T(kicker.upper(), 10.5, True, kc, sa=0, spc=1.6)])
    tbox(slide, ML, 0.60, CW * 0.86, 0.55, [T(title, 29, True, DEEP, sa=0, ln=0.95)])
    shp(slide, ML, 1.26, 1.05, 0.05, kind=MSO_SHAPE.RECTANGLE, fill=GOLD, adj=None)
    if sub:
        tbox(slide, ML + 1.22, 1.19, CW - 1.3, 0.3, [T(sub, 11.5, False, MUTED, sa=0)])


def footer(slide, num, presenter, mod=None):
    shp(slide, ML, 6.88, CW, 0.012, kind=MSO_SHAPE.RECTANGLE, fill=LINE, adj=None)
    left = "Agro AI  ·  Big Onion Yield Prediction  ·  University of Moratuwa"
    if mod:
        left = f"{mod}  ·  " + left
    tbox(slide, ML, 6.96, CW * 0.72, 0.3, [T(left, 8.5, False, MUTED, sa=0)])
    tbox(slide, SW - MR - 4.0, 6.96, 4.0, 0.3,
         [T(f"{presenter}   |   {num} / 13", 8.5, True, GREEN, "r", sa=0)])


def module_tag(slide, n, name):
    w = 2.9
    x = SW - MR - w
    s = shp(slide, x, 0.34, w, 0.42, fill=DEEP, adj=0.5)
    write(s.text_frame, [T(f"MODULE {n}  ·  {name}", 9.5, True, WHITE, "c", sa=0,
                           spc=0.8)], anchor=MSO_ANCHOR.MIDDLE)


# ============================================================================= slides
def slide1(prs):
    s = new_slide(prs, DEEP)
    shp(s, 0, 0, SW, SH, kind=MSO_SHAPE.RECTANGLE, adj=None,
        grad=(DEEP, RGBColor(0x1C, 0x5E, 0x40)), angle=315)
    # decorative field bands
    shp(s, -1.0, 6.18, 16, 2.0, kind=MSO_SHAPE.PARALLELOGRAM,
        fill=RGBColor(0x14, 0x4B, 0x35), adj=None)
    shp(s, -1.0, 6.72, 16, 2.0, kind=MSO_SHAPE.PARALLELOGRAM,
        fill=RGBColor(0x10, 0x42, 0x2F), adj=None)
    for i, xx in enumerate([9.55, 10.55, 11.55]):
        shp(s, xx, 1.05, 0.62, 0.62, kind=MSO_SHAPE.OVAL,
            fill=GOLD if i == 1 else RGBColor(0xE0, 0x9C, 0x45), adj=None)
    shp(s, 9.55, 1.9, 2.62, 0.05, kind=MSO_SHAPE.RECTANGLE, fill=GOLD, adj=None)
    tbox(s, 9.55, 2.0, 3.2, 0.9,
         [T("Yala season  ·  Matale  ·  Anuradhapura", 10, False,
            PALE2, sa=1),
          T("Polonnaruwa  ·  Kurunegala", 10, False, PALE2, sa=0)])

    tbox(s, ML, 1.02, 8.5, 0.3,
         [T("FINAL YEAR PROJECT  ·  LEVEL 4  ·  2026", 11, True,
            PALE3, sa=0, spc=1.8)])
    tbox(s, ML, 1.42, 8.7, 2.5,
         [T("An Explainable AI-Driven Decision Support System for "
            "Big Onion Yield Prediction", 33, True, WHITE, sa=6, ln=0.94),
          T("Using Multi-Source Climate, Soil and Yield Data in Sri Lanka",
            17, False, PALE, sa=0, ln=1.0)])

    shp(s, ML, 3.72, 1.05, 0.05, kind=MSO_SHAPE.RECTANGLE, fill=GOLD, adj=None)

    tbox(s, ML, 4.0, 3.2, 0.3, [T("GROUP  ·  AGRO AI", 10.5, True, GOLD, sa=0, spc=1.4)])
    members = [("214019K", "Arkam B.H.M."), ("214192G", "Sharuja B."),
               ("214193K", "Shathurya P.")]
    for i, (idx, nm) in enumerate(members):
        x = ML + i * 2.72
        shp(s, x, 4.34, 2.5, 0.72, fill=RGBColor(0x18, 0x53, 0x3B), adj=0.09)
        tbox(s, x + 0.18, 4.44, 2.2, 0.55,
             [T(nm, 12, True, WHITE, sa=1), T(idx, 9.5, False, PALE3, sa=0)])

    tbox(s, ML, 5.34, 6.4, 0.9,
         [T("Supervised by:  Dr. Firdhous M.F.M.", 12, True, WHITE, sa=3),
          T("Faculty of Information Technology,  University of Moratuwa", 11,
            False, PALE, sa=0)])

    s.notes_slide.notes_text_frame.text = (
        "Good morning. We are Group Agro AI. I am Arkam, with Sharuja and Shathurya, "
        "supervised by Dr. Firdhous of the Faculty of Information Technology.\n\n"
        "Our project is an explainable AI-driven decision support system that forecasts "
        "big onion yield before harvest, at district level, for the Yala season in "
        "Matale, Anuradhapura, Polonnaruwa and Kurunegala.\n\n"
        "In the next 15 minutes: three minutes on the problem and our solution, then "
        "four minutes on each of our three modules. (~20 s)")
    tbox(s, SW - MR - 3.0, 6.96, 3.0, 0.3,
         [T("Arkam B.H.M.   |   1 / 13", 8.5, True, PALE3, "r",
            sa=0)])
    return s


def slide2(prs):
    s = new_slide(prs)
    header(s, "Section 1  ·  Introduction", "Problem and Motivation",
           "Why a pre-harvest forecast does not exist today")

    left = [
        T("The gap today", 14, True, DEEP, sa=7),
        T("Big onion is one of Sri Lanka's most economically significant "
          "field crops.", 11.5, False, BODY, sa=7),
        T("No systematic pre-harvest yield forecasting method exists for the "
          "crop.", 11.5, False, BODY, sa=7),
        T("Figures are compiled mainly from subjective field assessments by "
          "agricultural instructors and divisional officers.", 11.5, False, BODY, sa=7),
        T("Reliable yield information becomes available only after the harvest "
          "is already sold.", 11.5, False, BODY, sa=7),
        T("Late, unquantified estimates make import planning, price "
          "stabilisation, timely intervention and resource allocation "
          "difficult.", 11.5, False, BODY, sa=0),
    ]
    card(s, ML, 1.58, 4.95, 3.30, left, fill=WHITE, accent=GOLD)

    card(s, ML, 5.02, 4.95, 1.60,
         [T("Two compounding difficulties", 12, True, DEEP, sa=5),
          T("Yield depends on weather, soil, crop history, regional conditions "
            "and cultivation practice — and the usable Sri Lankan big onion "
            "record is very small, which makes conventional AI development "
            "hard.", 10.5, False, BODY, sa=0)],
         fill=GOLD_L, line=RGBColor(0xEC, 0xD6, 0xAF))

    rx, rw = 5.86, SW - MR - 5.86
    bw = (rw - 3 * 0.20) / 4

    tbox(s, rx, 1.58, rw, 0.26,
         [T("CURRENT SITUATION", 10, True, GREY_B, sa=0, spc=1.4)])
    cur = ["Field observations", "Subjective estimates", "Results after harvest",
           "Late decisions"]
    for i, t in enumerate(cur):
        x = rx + i * (bw + 0.20)
        last = i == 3
        box(s, x, 1.88, bw, 0.92, [T(t, 10.5, True, GOLD_D if last else GREY_B, "c",
                                     sa=0, ln=0.92)],
            fill=GOLD_L if last else GREY_L,
            line=RGBColor(0xEC, 0xD6, 0xAF) if last else None)
        if i < 3:
            arrow_r(s, x + bw + 0.01, 2.34, w=0.18, c=GREY_B)

    tbox(s, rx, 3.28, rw, 0.26,
         [T("REQUIRED SITUATION", 10, True, GREEN, sa=0, spc=1.4)])
    req = ["Multi-source data", "AI prediction before harvest",
           "Explainable result", "Early decisions"]
    for i, t in enumerate(req):
        x = rx + i * (bw + 0.20)
        last = i == 3
        box(s, x, 3.58, bw, 0.92,
            [T(t, 10.5, True, WHITE if last else DEEP, "c", sa=0, ln=0.92)],
            fill=GREEN if last else MINT)
        if i < 3:
            arrow_r(s, x + bw + 0.01, 4.04, w=0.18)

    shp(s, rx, 4.82, rw, 1.8, fill=WHITE, line=LINE, adj=0.05)
    tbox(s, rx + 0.24, 4.96, rw - 0.48, 1.5,
         [T("What a forecast would change", 12.5, True, DEEP, sa=6),
          T("Import sizing  —  size imports against an evidence-based "
            "expectation of the domestic crop rather than last year's outcome.",
            10.5, False, BODY, sa=5),
          T("Field intervention  —  identify districts trending towards a "
            "shortfall while irrigation or pest advice can still help.",
            10.5, False, BODY, sa=5),
          T("Negotiating power  —  give farmer organisations a defensible basis "
            "for forward prices with collectors.", 10.5, False, BODY, sa=0)])

    s.notes_slide.notes_text_frame.text = (
        "Big onion is economically significant, yet unlike paddy there is no "
        "crop-cutting survey for it. District figures are compiled from subjective "
        "field assessments, they carry unquantified error, and they arrive after the "
        "crop is already harvested and sold.\n\n"
        "Follow the top strip: observations, subjective estimates, results after "
        "harvest — decisions are always late. The bottom strip is what we need: "
        "multi-source data, an AI prediction issued before harvest, an explained "
        "result, and early decisions.\n\n"
        "Two things make this hard. Yield depends on weather, soil, crop history, "
        "regional conditions and management, and the usable Sri Lankan record for "
        "this crop is very small — so conventional AI development is difficult.\n\n"
        "Getting this right changes import sizing, field intervention, and farmers' "
        "negotiating position. (~70 s)")
    footer(s, 2, "Arkam B.H.M.")
    return s


def slide3(prs):
    s = new_slide(prs)
    header(s, "Section 1  ·  Introduction", "Proposed Solution, Aim and Users",
           "An explainable AI-driven decision support system")

    stages = [("Data Sources", "Yield · Weather · Soil · Satellite"),
              ("Data Pipeline", "Clean · Reconcile · Engineer features"),
              ("Prediction Engine", "Train · Compare · Combine · Calibrate"),
              ("Explainability &\nDecision Support", "SHAP · ERI · Dashboard · Assistant")]
    bw = (CW - 3 * 0.42) / 4
    for i, (t, sub) in enumerate(stages):
        x = ML + i * (bw + 0.42)
        fill = DEEP if i == 3 else (GREEN if i == 2 else MINT)
        tc = WHITE if i >= 2 else DEEP
        sc = PALE2 if i >= 2 else MUTED
        sh = shp(s, x, 1.58, bw, 1.06, fill=fill, adj=0.09)
        write(sh.text_frame,
              [T(t.replace("\n", " "), 12.5, True, tc, "c", sa=2, ln=0.92),
               T(sub, 9, False, sc, "c", sa=0, ln=0.95)],
              anchor=MSO_ANCHOR.MIDDLE, margins=(0.1, 0.1, 0.03, 0.03))
        if i < 3:
            arrow_r(s, x + bw + 0.06, 2.11, w=0.30, c=LEAF)

    deliver = [
        "District-level yield forecast issued before harvest",
        "Prediction expressed in metric tons per hectare",
        "A calibrated uncertainty interval, not a bare number",
        "The factors that drove each individual prediction",
        "Comparison across districts and across years",
        "Interactive dashboard in English, Sinhala and Tamil",
    ]
    shp(s, ML, 2.92, 7.55, 2.62, fill=WHITE, line=LINE, adj=0.05)
    tbox(s, ML + 0.24, 3.06, 7.1, 0.3,
         [T("What the system delivers", 12.5, True, DEEP, sa=0)])
    for i, t in enumerate(deliver):
        col, row = i % 2, i // 2
        x = ML + 0.24 + col * 3.62
        y = 3.44 + row * 0.66
        icon(s, x, y + 0.07, 0.20, "•", fill=GOLD, sz=11)
        tbox(s, x + 0.30, y, 3.22, 0.6, [T(t, 10.5, False, BODY, sa=0, ln=0.95)])

    ux, uw = 8.42, SW - MR - 8.42
    shp(s, ux, 2.92, uw, 2.62, fill=DEEP, adj=0.05)
    tbox(s, ux + 0.24, 3.06, uw - 0.48, 0.3,
         [T("Primary users", 12.5, True, WHITE, sa=0)])
    users = ["Department of Census and Statistics",
             "Department of Agriculture & Ministry officials",
             "District agricultural officers",
             "Farmer organisations", "Researchers and students"]
    for i, u in enumerate(users):
        pill(s, ux + 0.24, 3.44 + i * 0.40, uw - 0.48, 0.33, u,
             fill=RGBColor(0x18, 0x53, 0x3B), c=WHITE, sz=10, b=False, al="l", adj=0.3)

    sc = shp(s, ML, 5.76, CW, 0.86, fill=GOLD_L, line=RGBColor(0xEC, 0xD6, 0xAF),
             adj=0.14)
    write(sc.text_frame,
          [T("Scope   ·   Yala season — the crop's principal commercial season   ·   "
             "Matale · Anuradhapura · Polonnaruwa · Kurunegala   ·   "
             "Output: average yield in MT / Ha with a prediction interval",
             11.5, True, GOLD_D, "c", sa=0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.2, 0.2, 0.02, 0.02))

    s.notes_slide.notes_text_frame.text = (
        "Our solution is an explainable AI-driven decision support system, built as a "
        "single pipeline: data sources feed a data pipeline, which feeds a prediction "
        "engine, whose outputs are turned into explanation and decision support.\n\n"
        "It predicts district-level yield before harvest for the Yala season across "
        "four districts, in metric tons per hectare, with an uncertainty interval, an "
        "explanation of the drivers, and district and year comparison — delivered in "
        "English, Sinhala and Tamil.\n\n"
        "The users are the people who actually take the decisions: DCS statistical "
        "officers validating estimates, DoA and Ministry analysts sizing imports, "
        "district officers targeting extension effort, farmer organisations, and "
        "researchers.\n\n"
        "The system is built as three modules. Sharuja will start with the data "
        "pipeline. (~75 s)")
    footer(s, 3, "Arkam B.H.M.")
    return s


def slide4(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 1", "Data Pipeline and Feature Engineering",
           "Turning eight heterogeneous sources into one trustworthy dataset")
    module_tag(s, 1, "Data Pipeline")

    shp(s, ML, 1.62, 3.42, 4.96, fill=DEEP, adj=0.05)
    tbox(s, ML + 0.26, 1.80, 2.9, 1.0, [T("01", 44, True, GOLD, sa=0, ln=0.85)])
    tbox(s, ML + 0.26, 2.70, 2.9, 3.7,
         [T("Data Pipeline and\nFeature Engineering", 15.5, True, WHITE, sa=8, ln=0.95),
          T("MAIN RESPONSIBILITY", 9, True, GOLD, sa=4, spc=1.2),
          T("Collect, clean, reconcile, transform and integrate heterogeneous "
            "agricultural data into a reliable machine-learning dataset.",
            11, False, PALE, sa=8),
          T("OWNER", 9, True, GOLD, sa=4, spc=1.2),
          T("Sharuja B.  ·  214192G", 11, True, WHITE, sa=0)])
    shp(s, ML + 0.26, 5.72, 2.90, 0.012, kind=MSO_SHAPE.RECTANGLE, fill=GREEN,
        adj=None)
    tbox(s, ML + 0.26, 5.86, 2.90, 0.60,
         [T("Eight raw source files reduced to one analysis dataset at the "
            "district–season–year grain.", 9.5, False, PALE2, sa=0, ln=1.02)])

    rx = ML + 3.42 + 0.34
    rw = SW - MR - rx
    cw2 = (rw - 0.30) / 2
    ch = (4.96 - 0.30) / 2
    sources = [
        ("Y", "Historical yield & cultivated extent",
         ["Department of Census and Statistics", "FAOSTAT",
          "District · season · year — prediction target"], GREEN),
        ("W", "Daily weather",
         ["NASA POWER reanalysis", "CHIRPS rainfall",
          "Temperature · rainfall · humidity · radiation"], LEAF),
        ("S", "Soil properties",
         ["ISRIC SoilGrids 250 m", "Static per district",
          "pH · organic carbon · clay · sand"], GOLD),
        ("V", "Satellite-derived indices",
         ["MODIS MOD13 / MOD11 products",
          "Reduced server-side in Google Earth Engine",
          "NDVI · EVI · NDWI · day/night LST"], RGBColor(0x2A, 0x6E, 0x8F)),
    ]
    for i, (g, title, lines, col) in enumerate(sources):
        x = rx + (i % 2) * (cw2 + 0.30)
        y = 1.62 + (i // 2) * (ch + 0.30)
        shp(s, x, y, cw2, ch, fill=WHITE, line=LINE, adj=0.06)
        icon(s, x + 0.24, y + 0.24, 0.42, g, fill=col, sz=14)
        tbox(s, x + 0.78, y + 0.26, cw2 - 1.0, 0.5,
             [T(title, 12.5, True, DEEP, sa=0, ln=0.95)])
        for j, ln in enumerate(lines):
            tbox(s, x + 0.24, y + 0.92 + j * 0.42, cw2 - 0.48, 0.4,
                 [T("—  " + ln, 10.5, False, BODY if j < 2 else MUTED, sa=0, ln=0.95)])

    s.notes_slide.notes_text_frame.text = (
        "Thank you Arkam. I am Sharuja, and I own Module 1 — the data pipeline and "
        "feature engineering.\n\n"
        "My responsibility is to collect, clean, reconcile, transform and integrate "
        "heterogeneous agricultural data into one reliable machine-learning dataset. "
        "Every number the other two modules produce depends on this stage.\n\n"
        "Four data streams. First, historical yield and cultivated extent from the "
        "Department of Census and Statistics and FAOSTAT — this is our prediction "
        "target. Second, daily weather: NASA POWER reanalysis, chosen because the "
        "dry-zone ground station network is sparse and has gaps, plus CHIRPS for "
        "rainfall, which is better validated for tropical precipitation. Third, static "
        "soil properties from ISRIC SoilGrids. Fourth, MODIS vegetation indices and "
        "land-surface temperature, reduced server-side in Google Earth Engine so no raw "
        "imagery ever enters the model. (~70 s)")
    footer(s, 4, "Sharuja B.", "Module 1")
    return s


def slide5(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 1", "Data Processing and Feature Engineering",
           "One reproducible path from raw files to model-ready features")
    module_tag(s, 1, "Data Pipeline")

    steps = ["Raw data collection", "District & year matching", "Seasonal filtering",
             "Data cleaning", "Missing-value handling", "Aggregation",
             "Feature engineering", "Final dataset"]
    bw = (CW - 3 * 0.34) / 4
    for i, t in enumerate(steps):
        col, row = i % 4, i // 4
        x = ML + col * (bw + 0.34)
        y = 1.58 + row * 0.92
        last = i == 7
        sh = shp(s, x, y, bw, 0.72, fill=DEEP if last else MINT, adj=0.10)
        write(sh.text_frame,
              [T(f"{i + 1}.  {t}", 11, True, WHITE if last else DEEP, "c", sa=0,
                 ln=0.92)],
              anchor=MSO_ANCHOR.MIDDLE, margins=(0.08, 0.08, 0.02, 0.02))
        if col < 3:
            arrow_r(s, x + bw + 0.03, y + 0.36, w=0.26)
        if i == 3:
            arrow_d(s, x + bw / 2, y + 0.74, h=0.16)

    shp(s, ML, 3.62, 5.62, 1.42, fill=WHITE, line=LINE, adj=0.06)
    tbox(s, ML + 0.22, 3.74, 5.2, 1.2,
         [T("Sources disagree on grain, format and identifiers", 12, True, DEEP, sa=5),
          T("Weather is daily  ·  yield is seasonal or yearly  ·  satellite arrives "
            "as time-based composites  ·  soil is static  ·  district names and "
            "identifiers differ between sources.", 10.5, False, BODY, sa=6,
            ln=1.02),
          T("Nothing can simply be joined — every stream is reconciled to the "
            "common key before any modelling begins.", 10.5, True, GREEN, sa=0,
            ln=1.02)])

    kx, kw = ML + 5.62 + 0.30, CW - 5.62 - 0.30
    shp(s, kx, 3.62, kw, 1.42, fill=MINT, adj=0.06)
    tbox(s, kx + 0.22, 3.72, kw - 0.44, 0.28,
         [T("Everything is reduced to one common key", 12, True, DEEP, sa=0)])
    kb = (kw - 0.44 - 2 * 0.16) / 3
    for i, t in enumerate(["Weather\ndaily", "Satellite\ncomposites", "Soil\nstatic"]):
        box(s, kx + 0.22 + i * (kb + 0.16), 4.06, kb, 0.42,
            [T(t.replace("\n", " · "), 9.5, False, MUTED, "c", sa=0, ln=0.9)],
            fill=WHITE)
    arrow_d(s, kx + kw / 2, 4.52, h=0.14)
    box(s, kx + 0.22, 4.68, kw - 0.44, 0.30,
        [T("District  —  Season  —  Year", 12, True, WHITE, "c", sa=0)], fill=GREEN)

    tbox(s, ML, 5.14, 8.2, 0.28,
         [T("PREDICTIVE FEATURE CATEGORIES", 10, True, GREEN, sa=0, spc=1.4)])
    feats = ["Weather aggregates", "Rainfall & water-stress indicators",
             "Temperature & heat-stress indicators", "Growing degree days",
             "Satellite vegetation indices", "Land-surface temperature",
             "Soil properties", "Historical yield features",
             "Agronomic interaction terms"]
    fw, fh = (8.12 - 2 * 0.16) / 3, 0.34
    for i, t in enumerate(feats):
        x = ML + (i % 3) * (fw + 0.16)
        y = 5.44 + (i // 3) * (fh + 0.11)
        pill(s, x, y, fw, fh, t, fill=WHITE, line=LINE, c=BODY, sz=9.5, b=False,
             al="c", adj=0.4)

    bx = ML + 8.12 + 0.30
    bw2 = SW - MR - bx
    shp(s, bx, 5.14, bw2, 1.54, fill=DEEP, adj=0.07)
    tbox(s, bx + 0.20, 5.44, bw2 - 0.40, 1.0,
         [T("≈ 32", 30, True, GOLD, sa=0, ln=0.85),
          T("predictive features constructed per district-season-year",
            10.5, False, PALE, sa=0, ln=0.98)])

    s.notes_slide.notes_text_frame.text = (
        "This is the pipeline. Eight stages, every one writing its output to disk, so "
        "the pipeline is restartable and every intermediate is inspectable.\n\n"
        "The hard part is the middle. The sources disagree: weather is daily, yield is "
        "seasonal, satellite arrives as composites, soil is static, and the same "
        "district is not always spelled or keyed identically. So I define a canonical "
        "district vocabulary in configuration and map every source onto it at load "
        "time — and a name that fails to map raises an error rather than silently "
        "dropping the row, because a silent drop gives you a smaller dataset with no "
        "sign that anything went wrong.\n\n"
        "Everything is then reduced to one common key: district, season, year. Means "
        "for state variables like temperature, sums for fluxes like rainfall, counts "
        "for threshold-crossing events.\n\n"
        "From that I engineer roughly 32 predictors across nine categories. Growing "
        "degree days and heat-stress days needed real agronomic judgement — the base "
        "and critical temperatures come from the Department of Agriculture HORDI "
        "guidelines for big onion. The interaction terms encode agronomic hypotheses, "
        "not statistical convenience. (~85 s)")
    footer(s, 5, "Sharuja B.", "Module 1")
    return s


def slide6(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 1", "Data Scarcity and Augmentation",
           "Treating training-set size as a design variable, not a fixed limit")
    module_tag(s, 1, "Data Pipeline")

    methods = [
        ("CTGAN synthetic generation",
         "A conditional tabular GAN learns the joint distribution of predictors and "
         "target, then samples new rows from it.",
         "Most expressive — but needs many real records to learn a trustworthy "
         "distribution."),
        ("Physics-based proxy",
         "Environmental predictors of real records are perturbed within physically "
         "plausible bounds; yield follows a lightweight agronomic response.",
         "Generated samples respect biological limits by construction."),
        ("Bootstrap + Gaussian noise",
         "Draws with replacement from existing records and perturbs continuous "
         "features by a small variance.",
         "Stays closest to the empirical data distribution."),
    ]
    bw = (CW - 2 * 0.34) / 3
    for i, (t, d, n) in enumerate(methods):
        x = ML + i * (bw + 0.34)
        shp(s, x, 1.58, bw, 2.06, fill=WHITE, line=LINE, adj=0.06)
        shp(s, x, 1.58, bw, 0.055, kind=MSO_SHAPE.RECTANGLE,
            fill=[GOLD, LEAF, GREEN][i], adj=None)
        tbox(s, x + 0.22, 1.76, bw - 0.44, 1.24,
             [T(t, 12.5, True, DEEP, sa=6, ln=0.95),
              T(d, 10, False, BODY, sa=0, ln=1.0)])
        shp(s, x + 0.22, 3.04, bw - 0.44, 0.012, kind=MSO_SHAPE.RECTANGLE,
            fill=LINE, adj=None)
        tbox(s, x + 0.22, 3.11, bw - 0.44, 0.46,
             [T(n, 9.5, True, MUTED, sa=0, it=True, ln=1.0)])

    w = shp(s, ML, 3.84, CW, 0.82, fill=GOLD_L, line=RGBColor(0xEC, 0xD6, 0xAF),
            adj=0.16)
    icon(s, ML + 0.22, 3.99, 0.52, "!", fill=GOLD, sz=17)
    tbox(s, ML + 0.92, 3.98, CW - 1.2, 0.6,
         [T("Leakage guard  —  augmentation is applied only inside each training "
            "fold", 12.5, True, GOLD_D, sa=2),
          T("The held-out year always consists exclusively of real, unaugmented "
            "records, so reported accuracy can never be inflated by a synthetic "
            "row resembling the answer.", 10, False, GOLD_D, sa=0)])

    tbox(s, ML, 4.84, CW, 0.28,
         [T("MODULE 1 FEATURES", 10, True, GREEN, sa=0, spc=1.4)])
    row1 = ["Multi-source data integration", "Automated preprocessing",
            "Physical-range validation", "Missing-data treatment",
            "Seasonal alignment"]
    row2 = ["Data-source reconciliation", "Synthetic data augmentation",
            "Reproducible feature generation", "Train/test leakage prevention"]
    w1 = (CW - 4 * 0.15) / 5
    for i, t in enumerate(row1):
        pill(s, ML + i * (w1 + 0.15), 5.14, w1, 0.38, t, fill=MINT, c=DEEP, sz=9.5,
             b=False, adj=0.4)
    w2 = (CW - 3 * 0.15) / 4
    for i, t in enumerate(row2):
        pill(s, ML + i * (w2 + 0.15), 5.62, w2, 0.38, t, fill=MINT, c=DEEP, sz=9.5,
             b=False, adj=0.4)

    o = shp(s, ML, 6.16, CW, 0.60, fill=DEEP, adj=0.18)
    write(o.text_frame,
          [T("MODULE 1 OUTPUT   ·   a cleaned, validated, feature-engineered and "
             "reproducible dataset, ready for the prediction engine",
             12, True, WHITE, "c", sa=0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.2, 0.2, 0.02, 0.02))

    s.notes_slide.notes_text_frame.text = (
        "Even after reconciliation the dataset is small by machine-learning standards, "
        "so we treated the size of the training partition as a design variable rather "
        "than a fixed constraint.\n\n"
        "We evaluated three augmentation strategies under an identical downstream "
        "learner and identical cross-validation, so the comparison isolates the "
        "augmentation method itself. A CTGAN that learns the joint distribution; a "
        "physics-based proxy that perturbs environmental predictors within plausible "
        "bounds and derives yield from an agronomic response; and bootstrap "
        "resampling with injected Gaussian noise.\n\n"
        "The critical design point is the leakage guard. Before any synthetic record "
        "was generated, a sample of real records was withdrawn and reserved as a "
        "common evaluation set, and augmentation is applied only inside each training "
        "fold. The held-out year is always real, unaugmented data — so accuracy can "
        "never be inflated by a synthetic near-duplicate of the answer.\n\n"
        "The output of my module is a cleaned, validated, feature-engineered and "
        "reproducible dataset. Arkam will now take it into the prediction engine. "
        "(~70 s)")
    footer(s, 6, "Sharuja B.", "Module 1")
    return s


def slide7(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 2", "ML / DL Prediction and Evaluation Engine",
           "Four modelling philosophies, one identical protocol")
    module_tag(s, 2, "Prediction Engine")

    shp(s, ML, 1.58, CW, 0.62, fill=DEEP, adj=0.14)
    tbox(s, ML + 0.24, 1.66, CW - 0.5, 0.5,
         [T("MAIN RESPONSIBILITY   ·   train, compare, evaluate, combine and "
            "calibrate different prediction models   ·   owner: Arkam B.H.M. "
            "(214019K)", 11.5, True, WHITE, sa=0)])

    fams = [
        ("Classical machine learning", GREEN,
         ["Random Forest", "XGBoost", "Support Vector Regression"],
         "Suited to structured, tabular agricultural data and robust at small "
         "sample sizes."),
        ("Deep learning", RGBColor(0x2A, 0x6E, 0x8F),
         ["LSTM", "Bidirectional LSTM", "1D-CNN", "Hybrid CNN-LSTM"],
         "Analyse the growing season as a sequence, where timing of an event "
         "matters as much as its size."),
        ("Interpretable & hybrid", GOLD,
         ["Symbolic Regression", "Physics-Informed Residual Model"],
         "Symbolic regression yields a readable equation; the physics model fuses "
         "agronomy with machine learning."),
    ]
    bw = (CW - 2 * 0.34) / 3
    for i, (t, col, items, why) in enumerate(fams):
        x = ML + i * (bw + 0.34)
        shp(s, x, 2.42, bw, 3.34, fill=WHITE, line=LINE, adj=0.05)
        shp(s, x, 2.42, bw, 0.06, kind=MSO_SHAPE.RECTANGLE, fill=col, adj=None)
        tbox(s, x + 0.24, 2.62, bw - 0.48, 0.36, [T(t, 13, True, DEEP, sa=0)])
        for j, it in enumerate(items):
            pill(s, x + 0.24, 3.04 + j * 0.44, bw - 0.48, 0.38, it, fill=MINT,
                 c=DEEP, sz=10.5, b=True, al="l", adj=0.35)
        shp(s, x + 0.24, 4.88, bw - 0.48, 0.012, kind=MSO_SHAPE.RECTANGLE,
            fill=LINE, adj=None)
        tbox(s, x + 0.24, 4.96, bw - 0.48, 0.64,
             [T(why, 10, False, MUTED, sa=0, it=True, ln=1.02)])

    b = shp(s, ML, 5.98, CW, 0.74, fill=MINT, adj=0.14)
    write(b.text_frame,
          [T("All nine base models are trained on the same dataset under the same "
             "evaluation protocol with fixed seeds — so the comparison between "
             "families is meaningful rather than a leaderboard artefact.",
             11.5, True, DEEP, "c", sa=0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.3, 0.3, 0.02, 0.02))

    s.notes_slide.notes_text_frame.text = (
        "Thank you Sharuja. I own Module 2 — the prediction and evaluation engine. My "
        "responsibility is to train, compare, evaluate, combine and calibrate the "
        "models.\n\n"
        "We deliberately span four modelling philosophies, because at this sample size "
        "you cannot assume in advance which one wins.\n\n"
        "Classical machine learning — Random Forest for variance reduction, XGBoost "
        "for bias reduction under explicit L1 and L2 regularisation, and Support "
        "Vector Regression whose capacity is controlled by the regularisation constant "
        "rather than by the number of observations. Deliberately orthogonal inductive "
        "biases.\n\n"
        "Deep learning — LSTM and bidirectional LSTM integrate cumulative exposure "
        "across the season; the 1D-CNN detects local shape, like the abruptness of a "
        "rainfall event or the width of a hot spell; the hybrid runs both branches and "
        "concatenates them. All four are deliberately small, with dropout and early "
        "stopping.\n\n"
        "Interpretable and hybrid — symbolic regression evolves an equation an "
        "agricultural officer can read and check by hand, and the physics-informed "
        "residual model supplies established agronomy as structure so the learner only "
        "has to model what the physics does not explain.\n\n"
        "Crucially, all of them see the same data under the same protocol with fixed "
        "seeds. (~75 s)")
    footer(s, 7, "Arkam B.H.M.", "Module 2")
    return s


def slide8(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 2", "Prediction Pipeline and Ensemble",
           "From engineered dataset to a single combined forecast")
    module_tag(s, 2, "Prediction Engine")

    steps = ["Engineered dataset", "Train multiple models",
             "Generate out-of-fold predictions", "Compare model performance",
             "Combine models through stacking", "Final yield prediction"]
    x, w, h, g = ML, 5.30, 0.66, 0.19
    for i, t in enumerate(steps):
        y = 1.58 + i * (h + g)
        first, last = i == 0, i == len(steps) - 1
        fill = MINT if first else (DEEP if last else WHITE)
        line = None if first or last else LINE
        sh = shp(s, x, y, w, h, fill=fill, line=line, adj=0.14)
        write(sh.text_frame,
              [T(t, 11.5, True, WHITE if last else DEEP, "l", sa=0)],
              anchor=MSO_ANCHOR.MIDDLE, margins=(0.52, 0.12, 0.02, 0.02))
        n = shp(s, x + 0.14, y + 0.16, 0.34, 0.34, kind=MSO_SHAPE.OVAL,
                fill=GOLD if last else GREEN, adj=None)
        write(n.text_frame, [T(str(i + 1), 10.5, True, WHITE, "c", sa=0)],
              anchor=MSO_ANCHOR.MIDDLE)
        if not last:
            arrow_d(s, x + w / 2, y + h + 0.015, h=0.16)

    rx = ML + w + 0.42
    rw = SW - MR - rx

    shp(s, rx, 1.58, rw, 2.30, fill=WHITE, line=LINE, adj=0.05)
    tbox(s, rx + 0.24, 1.70, rw - 0.48, 0.3,
         [T("Ensemble / stacking strategies", 13, True, DEEP, sa=0)])
    strat = [("Equal-weight averaging", "estimates nothing"),
             ("Inverse-RMSE weighting", "estimates one reliability scalar per model"),
             ("Constrained convex weighting",
              "non-negative weights summing to one, so the blend cannot be driven "
              "outside the base predictions")]
    for i, (a, b2) in enumerate(strat):
        y = 2.08 + i * 0.58
        icon(s, rx + 0.24, y + 0.10, 0.20, "•", fill=GOLD, sz=11)
        tbox(s, rx + 0.54, y, rw - 0.80, 0.56,
             [T(a, 11, True, DEEP, sa=1), T(b2, 9.5, False, MUTED, sa=0, ln=0.98)])

    shp(s, rx, 4.06, rw, 1.86, fill=MINT, adj=0.05)
    tbox(s, rx + 0.24, 4.18, rw - 0.48, 0.3,
         [T("Module outputs", 13, True, DEEP, sa=0)])
    outs = ["Predicted yield in metric tons per hectare",
            "Best single model or ensemble prediction",
            "Persisted trained model artefacts",
            "Model-comparison results across all families"]
    for i, o in enumerate(outs):
        pill(s, rx + 0.24, 4.56 + i * 0.32, rw - 0.48, 0.28, o, fill=WHITE, c=BODY,
             sz=10, b=False, al="l", adj=0.3)

    n = shp(s, rx, 6.10, rw, 0.62, fill=GOLD_L, line=RGBColor(0xEC, 0xD6, 0xAF),
            adj=0.16)
    write(n.text_frame,
          [T("The meta-learner is fitted only on out-of-fold predictions, so it "
             "learns from realistic errors — never from a model's own training "
             "residuals.", 10, True, GOLD_D, "l", sa=0, ln=1.0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.22, 0.22, 0.02, 0.02))

    s.notes_slide.notes_text_frame.text = (
        "This is the pipeline. The engineered dataset goes in; every model is trained; "
        "each produces an out-of-fold prediction for every record — meaning the "
        "prediction for a record always comes from a version of the model that never "
        "saw that record. Those out-of-fold records are the substrate for everything "
        "downstream: the significance tests, the stacking layer, the calibration, and "
        "the attribution.\n\n"
        "We then compare performance and combine the models by stacking. Three "
        "combiners, deliberately, so we can test the forecast-combination puzzle "
        "instead of assuming it: an equal-weight mean that estimates nothing; "
        "inverse-RMSE weighting that estimates one scalar per model; and a constrained "
        "convex fit whose weights are non-negative and sum to one, so the blend always "
        "lies within the range of the base predictions and cannot be driven outside it "
        "by large opposing weights.\n\n"
        "The output is a yield figure in metric tons per hectare, the persisted model "
        "artefacts, and the full comparison table — all of which the serving layer "
        "hands to Module 3. (~75 s)")
    footer(s, 8, "Arkam B.H.M.", "Module 2")
    return s


def slide9(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 2", "Honest Evaluation and Uncertainty",
           "Leave-One-Year-Out validation and distribution-free intervals")
    module_tag(s, 2, "Prediction Engine")

    years = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
    lx, cw2, gap = ML + 1.05, 0.66, 0.075
    tbox(s, ML, 1.56, 6.60, 0.26,
         [T("LEAVE-ONE-YEAR-OUT CROSS-VALIDATION", 10, True, GREEN, sa=0, spc=1.3)])
    for i, y in enumerate(years):
        b = shp(s, lx + i * (cw2 + gap), 1.86, cw2, 0.30, fill=None, adj=None,
                kind=MSO_SHAPE.RECTANGLE)
        write(b.text_frame, [T(y, 9.5, True, MUTED, "c", sa=0)],
              anchor=MSO_ANCHOR.MIDDLE)
    rows = [("Fold 1", 0), ("Fold 2", 1), ("Fold 3", 2), ("...", None), ("Fold 7", 6)]
    for r, (lab, test) in enumerate(rows):
        y = 2.20 + r * 0.375
        tbox(s, ML, y + 0.03, 1.0, 0.28, [T(lab, 9.5, True, DEEP, "l", sa=0)])
        if test is None:
            tbox(s, lx, y + 0.02, 5.4, 0.28,
                 [T("·  ·  ·   rotate through every year   ·  ·  ·", 9.5, False,
                    MUTED, "c", sa=0)])
            continue
        for i in range(7):
            is_t = i == test
            b = shp(s, lx + i * (cw2 + gap), y, cw2, 0.30, adj=0.2,
                    fill=GOLD if is_t else MINT)
            write(b.text_frame,
                  [T("Test" if is_t else "Train", 8.5, True,
                     WHITE if is_t else GREEN, "c", sa=0)],
                  anchor=MSO_ANCHOR.MIDDLE)

    rx = lx + 7 * (cw2 + gap) + 0.30
    rw = SW - MR - rx
    shp(s, rx, 1.56, rw, 1.42, fill=WHITE, line=LINE, adj=0.06)
    tbox(s, rx + 0.22, 1.66, rw - 0.44, 1.24,
         [T("Why not a random split?", 12, True, DEEP, sa=4),
          T("Districts within a year share a weather regime, a monsoon anomaly and a "
            "national price environment. A random split puts records from the same "
            "year on both sides of the boundary — letting the model see the answer "
            "for a year it is then asked to predict, and reporting a score that would "
            "not survive deployment.", 9.5, False, BODY, sa=0, ln=1.0)])

    tbox(s, rx + 0.02, 3.10, rw, 0.26,
         [T("EVALUATION METRICS", 10, True, GREEN, sa=0, spc=1.3)])
    mets = ["RMSE", "MAE", "R²", "MAPE"]
    mw = (rw - 3 * 0.12) / 4
    for i, m in enumerate(mets):
        pill(s, rx + i * (mw + 0.12), 3.40, mw, 0.34, m, fill=MINT, c=DEEP, sz=10.5)
    pill(s, rx, 3.86, rw, 0.34,
         "Paired statistical significance testing on per-record residuals",
         fill=DEEP, c=WHITE, sz=9.5, b=True, adj=0.3)

    cy = 4.36
    shp(s, ML, cy, CW, 1.56, fill=MINT, adj=0.05)
    tbox(s, ML + 0.26, cy + 0.14, 5.6, 1.3,
         [T("Calibrated uncertainty — conformal prediction", 13, True, DEEP, sa=5),
          T("A single number invites false confidence. Split-conformal prediction is "
            "distribution-free: it assumes nothing about residuals being Gaussian or "
            "the model being correctly specified, and it attaches a lower and an upper "
            "yield boundary to every forecast — exactly what an import, resource or "
            "policy decision needs.", 10, False, BODY, sa=0, ln=1.02)])

    bx, bw3 = 6.60, 5.05
    tbox(s, bx, cy + 0.16, bw3, 0.26,
         [T("EXAMPLE OUTPUT", 9.5, True, GREEN, sa=0, spc=1.3)])
    shp(s, bx, cy + 0.62, bw3, 0.22, kind=MSO_SHAPE.ROUNDED_RECTANGLE,
        fill=RGBColor(0xD3, 0xE3, 0xD4), adj=0.5)
    shp(s, bx + 0.95, cy + 0.62, 2.55, 0.22, kind=MSO_SHAPE.ROUNDED_RECTANGLE,
        fill=LEAF, adj=0.5)
    shp(s, bx + 2.05, cy + 0.50, 0.09, 0.46, kind=MSO_SHAPE.RECTANGLE, fill=DEEP,
        adj=None)
    tbox(s, bx + 0.55, cy + 0.90, 1.0, 0.26, [T("10.8", 10, True, MUTED, "c", sa=0)])
    tbox(s, bx + 1.60, cy + 0.90, 1.0, 0.26, [T("12.5", 11, True, DEEP, "c", sa=0)])
    tbox(s, bx + 3.00, cy + 0.90, 1.0, 0.26, [T("14.2", 10, True, MUTED, "c", sa=0)])
    tbox(s, bx, cy + 1.16, bw3, 0.3,
         [T("Predicted yield 12.5 MT/Ha   ·   prediction interval 10.8 – 14.2 MT/Ha",
            10, True, DEEP, sa=0)])

    tbox(s, ML, 6.02, CW, 0.26,
         [T("MODULE 2 FEATURES", 10, True, GREEN, sa=0, spc=1.4)])
    cols = [["Multiple-model comparison", "Small-data-aware modelling",
             "Physics-informed prediction"],
            ["Symbolic equation generation", "Ensemble stacking",
             "Leave-One-Year-Out validation"],
            ["Statistical significance testing", "Calibrated prediction intervals",
             "Reproducible model training"]]
    colw = (CW - 2 * 0.30) / 3
    for i, col in enumerate(cols):
        x = ML + i * (colw + 0.30)
        shp(s, x, 6.30, colw, 0.50, fill=WHITE, line=LINE, adj=0.14)
        tbox(s, x + 0.16, 6.36, colw - 0.32, 0.4,
             [T("   ·   ".join(col), 9, False, BODY, "c", sa=0, ln=1.0)])

    s.notes_slide.notes_text_frame.text = (
        "The evaluation protocol is arguably the most consequential choice in the "
        "project.\n\n"
        "A random train-test split is not acceptable here. Districts within a year "
        "share a weather regime, a monsoon anomaly and a national price environment, "
        "so a random split puts records from the same year on both sides of the "
        "boundary — the model effectively sees the answer for a year it is then asked "
        "to predict, and the reported score would not survive deployment.\n\n"
        "So we use Leave-One-Year-Out. Hold out one complete year, train on the "
        "remaining years, predict the held-out year, and rotate through every year. "
        "Every fitted quantity — including all scaling and the augmentation — is "
        "estimated inside the fold, and hyperparameter selection is nested inside the "
        "training partition so the held-out year never influences model selection "
        "either. We report RMSE, MAE, R-squared and MAPE, and we compare models with "
        "a paired significance test on per-record residuals rather than on raw "
        "leaderboard positions.\n\n"
        "Finally, uncertainty. A single point forecast invites false confidence. "
        "Split-conformal prediction is distribution-free — it assumes nothing about "
        "the residuals being Gaussian — and gives a lower and an upper boundary. So "
        "instead of '12.5', the user sees 12.5 with an interval of 10.8 to 14.2, which "
        "is the information an import or resource decision actually needs. Shathurya "
        "will now show how we communicate that. (~75 s)")
    footer(s, 9, "Arkam B.H.M.", "Module 2")
    return s


def slide10(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 3", "Explainability — SHAP Attribution",
           "Turning a model output into a reason a district officer can act on")
    module_tag(s, 3, "Decision Support")

    shp(s, ML, 1.58, CW, 0.58, fill=DEEP, adj=0.14)
    tbox(s, ML + 0.24, 1.65, CW - 0.5, 0.46,
         [T("MAIN RESPONSIBILITY   ·   transform technical model outputs into "
            "understandable, actionable information for non-technical agricultural "
            "stakeholders   ·   owner: Shathurya P. (214193K)",
            11, True, WHITE, sa=0)])

    lw = 5.20
    card(s, ML, 2.34, lw, 1.50,
         [T("Global explanation", 12.5, True, DEEP, sa=5),
          T("A ranking of mean absolute attribution across all records — which "
            "predictors matter in general. Computed once and cached for the "
            "explainability view.", 10.5, False, BODY, sa=0, ln=1.02)],
         fill=WHITE, accent=GREEN)
    card(s, ML, 4.00, lw, 1.50,
         [T("Local explanation", 12.5, True, DEEP, sa=5),
          T("Computed on demand against the submitted feature vector — why this "
            "district, in this year, came out high or low. This is what an "
            "agricultural officer actually needs.", 10.5, False, BODY, sa=0, ln=1.02)],
         fill=WHITE, accent=GOLD)
    shp(s, ML, 5.66, lw, 0.56, fill=MINT, adj=0.14)
    tbox(s, ML + 0.22, 5.72, lw - 0.44, 0.46,
         [T("Positive contribution  →  increases the predicted yield", 10.5, True,
            GREEN, sa=2),
          T("Negative contribution  →  reduces the predicted yield", 10.5, True,
            GOLD_D, sa=0)])

    cx = ML + lw + 0.40
    cwid = SW - MR - cx
    shp(s, cx, 2.34, cwid, 3.88, fill=WHITE, line=LINE, adj=0.05)
    tbox(s, cx + 0.26, 2.46, cwid - 0.52, 0.3,
         [T("Local contributions for one district-year", 12.5, True, DEEP, sa=0)])

    zero = cx + 3.93
    scale = 2.40  # inches per MT/Ha
    shp(s, zero - 0.02, 2.94, 0.025, 2.68, kind=MSO_SHAPE.RECTANGLE, fill=GREY_B,
        adj=None)
    tbox(s, zero - 0.24, 5.62, 0.48, 0.24, [T("0", 9, False, MUTED, "c", sa=0)])
    tbox(s, cx + 0.26, 5.62, cwid - 0.52, 0.24,
         [T("contribution in MT / Ha", 9, False, MUTED, "r", sa=0)])

    contrib = [("Adequate rainfall", 0.8), ("Suitable growing degree days", 0.5),
               ("High heat-stress days", -0.7), ("Poor previous-year yield", -0.3)]
    for i, (lab, v) in enumerate(contrib):
        y = 3.10 + i * 0.68
        tbox(s, cx + 0.20, y + 0.04, 1.88, 0.42,
             [T(lab, 9.5, True, DEEP, "r", sa=0, ln=0.95)])
        bl = abs(v) * scale
        bx0 = zero if v > 0 else zero - bl
        b = shp(s, bx0, y + 0.05, bl, 0.34, fill=LEAF if v > 0 else GOLD, adj=0.22)
        sign = "+" if v > 0 else "−"
        write(b.text_frame,
              [T(f"{sign}{abs(v):.1f}", 9.5, True, WHITE,
                 "r" if v > 0 else "l", sa=0)],
              anchor=MSO_ANCHOR.MIDDLE, margins=(0.09, 0.09, 0.01, 0.01))

    tbox(s, cx + 0.26, 5.92, cwid - 0.52, 0.30,
         [T("Illustrative structure only — actual contributions are computed per "
            "district-year from the persisted tree model.", 9, False, MUTED, sa=0,
            it=True, ln=1.0)])

    s.notes_slide.notes_text_frame.text = (
        "Thank you Arkam. I am Shathurya, and I own Module 3 — explainability and "
        "decision support. My responsibility is to turn technical model outputs into "
        "information a non-technical agricultural stakeholder can act on.\n\n"
        "We use SHAP, because its attributions are the Shapley values of a cooperative "
        "game where the features are the players and the payoff is the prediction — "
        "which gives them a uniqueness property heuristic importance measures lack, "
        "and TreeExplainer computes them exactly for tree ensembles.\n\n"
        "Two artefacts. A global explanation — the ranking of mean absolute "
        "attribution across all records, which answers which predictors matter in "
        "general. And a local explanation, computed live against the submitted feature "
        "vector, which answers why this district in this year came out high or low. "
        "The second is what an officer actually asks for, which is why the SHAP "
        "computation is invoked in the presentation layer rather than only once in the "
        "analysis pipeline.\n\n"
        "The chart shows the shape of that output. Positive contributions push the "
        "prediction up, negative ones pull it down — adequate rainfall and suitable "
        "growing degree days lifting the forecast, heat-stress days and a poor "
        "previous year pulling it down. I want to be explicit that these figures "
        "illustrate the structure; the real numbers are computed per district-year "
        "from the persisted model. (~80 s)")
    footer(s, 10, "Shathurya P.", "Module 3")
    return s


def slide11(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 3",
           "Explainability Reliability Index (ERI)",
           "How much confidence should the user place in the explanation?")
    module_tag(s, 3, "Decision Support")

    tiers = [("High reliability", GREEN, MINT,
              "Explanations agree across folds and the interval is tight relative "
              "to the district's historical range."),
             ("Moderate reliability", GOLD, GOLD_L,
              "Some disagreement across folds, or a comparatively wide interval — "
              "read the drivers with care."),
             ("Low reliability", RGBColor(0xB0, 0x4A, 0x2A),
              RGBColor(0xFB, 0xEB, 0xE6),
              "Unstable attribution or a very wide interval — treat the explanation "
              "as indicative only.")]
    bw = (CW - 2 * 0.34) / 3
    for i, (t, col, bg, d) in enumerate(tiers):
        x = ML + i * (bw + 0.34)
        shp(s, x, 1.58, bw, 1.50, fill=bg, adj=0.07)
        icon(s, x + 0.24, 1.78, 0.40, "●", fill=col, sz=13)
        tbox(s, x + 0.76, 1.80, bw - 1.0, 0.36, [T(t, 12.5, True, DEEP, sa=0)])
        tbox(s, x + 0.24, 2.30, bw - 0.48, 0.7,
             [T(d, 10, False, BODY, sa=0, ln=1.02)])

    tbox(s, ML, 3.24, CW, 0.28,
         [T("SIGNALS COMBINED IN THE INDEX", 10, True, GREEN, sa=0, spc=1.4)])
    sigs = [("Cross-fold consistency",
             "Rank correlation between each fold's attribution and the full-data "
             "attribution"),
            ("Explanation agreement",
             "Do independent attribution results point at the same drivers?"),
            ("Stability under perturbation",
             "Does the explanation survive a small change to the inputs?"),
            ("Interval width",
             "Conformal half-width, expressed relative to the district's historical "
             "yield range")]
    sw = (CW - 3 * 0.28) / 4
    for i, (t, d) in enumerate(sigs):
        x = ML + i * (sw + 0.28)
        shp(s, x, 3.54, sw, 1.28, fill=WHITE, line=LINE, adj=0.07)
        shp(s, x, 3.54, sw, 0.05, kind=MSO_SHAPE.RECTANGLE, fill=LEAF, adj=None)
        tbox(s, x + 0.20, 3.70, sw - 0.40, 1.0,
             [T(t, 11.5, True, DEEP, sa=4, ln=0.95),
              T(d, 9.5, False, BODY, sa=0, ln=1.0)])

    e = shp(s, ML, 5.00, CW, 0.86, fill=DEEP, adj=0.13)
    write(e.text_frame,
          [T("Prediction   +   Uncertainty   +   Explanation   +   Reliability   =   "
             "Decision-ready output", 16, True, WHITE, "c", sa=0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.2, 0.2, 0.02, 0.02))

    shp(s, ML, 6.00, CW, 0.72, fill=MINT, adj=0.13)
    tbox(s, ML + 0.26, 6.10, CW - 0.52, 0.56,
         [T("Why it matters", 11, True, DEEP, sa=2),
          T("A prediction explanation should not only state why the system produced a "
            "result — it should also communicate how reliable that explanation is. "
            "The index is deliberately formula-based and auditable, not a second "
            "black-box model scoring the first.", 10, False, BODY, sa=0, ln=1.0)])

    s.notes_slide.notes_text_frame.text = (
        "A SHAP ranking or a prediction interval, presented alone, does not tell a "
        "non-technical user how much to trust either one. The Explainability "
        "Reliability Index closes that gap by compressing several reliability signals "
        "into one interpretable badge shown alongside every forecast.\n\n"
        "Four signals. Cross-fold consistency — the rank correlation between the "
        "attribution obtained in each Leave-One-Year-Out fold and the attribution from "
        "the full-data model. Agreement between explanation results. Stability under a "
        "small perturbation of the inputs. And the conformal interval width, expressed "
        "relative to the district's own historical yield range, so a wide interval on "
        "a low-yield district is not scored the same as the same absolute width on a "
        "high-yield one.\n\n"
        "The design choice I want to highlight: the index is a formula, not a model. "
        "Scoring the reliability of one model with a second uninspectable model would "
        "defeat the whole purpose — so the ERI can be recomputed by hand from its "
        "published components for any prediction.\n\n"
        "Prediction, plus uncertainty, plus explanation, plus reliability — that is "
        "what makes an output decision-ready. (~70 s)")
    footer(s, 11, "Shathurya P.", "Module 3")
    return s


def slide12(prs):
    s = new_slide(prs)
    header(s, "Section 2  ·  Module 3", "Dashboard and Prediction-Grounded Assistant",
           "Next.js decision-support interface in English, Sinhala and Tamil")
    module_tag(s, 3, "Decision Support")

    lw = 7.20
    groups = [("Predict & compare", GREEN,
               "District-level yield prediction  ·  Sri Lankan district choropleth "
               "map  ·  district-to-district comparison  ·  year-to-year comparison  "
               "·  context-aware form with automatically prefilled values"),
              ("Explain & trust", GOLD,
               "Point prediction with its prediction interval  ·  SHAP feature-"
               "contribution chart  ·  ERI reliability badge  ·  the symbolic-"
               "regression equation as a readable cross-check"),
              ("Decide & operate", RGBColor(0x2A, 0x6E, 0x8F),
               "Recommendation view in plain language  ·  model-comparison panel  ·  "
               "administrative and technical view  ·  English, Sinhala and Tamil")]
    for i, (t, col, d) in enumerate(groups):
        y = 1.62 + i * 1.50
        shp(s, ML, y, lw, 1.36, fill=WHITE, line=LINE, adj=0.06)
        shp(s, ML, y + 0.13, 0.055, 1.10, kind=MSO_SHAPE.RECTANGLE, fill=col,
            adj=None)
        tbox(s, ML + 0.26, y + 0.16, lw - 0.5, 0.32, [T(t, 13, True, DEEP, sa=0)])
        tbox(s, ML + 0.26, y + 0.52, lw - 0.5, 0.78,
             [T(d, 10.5, False, BODY, sa=0, ln=1.04)])

    rx = ML + lw + 0.36
    rw = SW - MR - rx
    shp(s, rx, 1.62, rw, 4.36, fill=DEEP, adj=0.05)
    tbox(s, rx + 0.24, 1.74, rw - 0.48, 0.62,
         [T("Prediction-grounded RAG assistant", 13.5, True, WHITE, sa=3, ln=0.95),
          T("“Why is Anuradhapura's predicted yield lower than last year?”",
            10, False, GOLD, sa=0, it=True, ln=1.0)])

    flow = ["User selects district and year", "System predicts yield",
            "Dashboard shows uncertainty and explanations",
            "User asks a follow-up question",
            "Assistant answers from retrieved system outputs"]
    for i, t in enumerate(flow):
        y = 2.46 + i * 0.58
        last = i == len(flow) - 1
        b = shp(s, rx + 0.24, y, rw - 0.48, 0.46,
                fill=GOLD if last else RGBColor(0x18, 0x53, 0x3B), adj=0.16)
        write(b.text_frame,
              [T(t, 10, True, WHITE, "l", sa=0, ln=0.95)],
              anchor=MSO_ANCHOR.MIDDLE, margins=(0.14, 0.1, 0.02, 0.02))
        if not last:
            arrow_d(s, rx + rw / 2, y + 0.47, h=0.11, c=GOLD)

    tbox(s, rx + 0.24, 5.36, rw - 0.48, 0.56,
         [T("Retrieval is scoped to this system's own outputs — SHAP values, the ERI "
            "score, the conformal interval and historical yield, keyed by district "
            "and year — so answers stay traceable to a specific prediction instead of "
            "being generated from general knowledge of onion cultivation.",
            8.5, False, PALE2, sa=0, ln=1.02)])

    o = shp(s, ML, 6.14, CW, 0.56, fill=GOLD_L, line=RGBColor(0xEC, 0xD6, 0xAF),
            adj=0.20)
    write(o.text_frame,
          [T("MODULE 3 OUTPUT   ·   an understandable, explainable, multilingual and "
             "reliability-aware decision-support interface",
             11.5, True, GOLD_D, "c", sa=0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.2, 0.2, 0.02, 0.02))

    s.notes_slide.notes_text_frame.text = (
        "The delivery layer is a Next.js dashboard with locale-aware routing, and its "
        "views map onto the four user groups.\n\n"
        "Predict and compare: district-level prediction, a Sri Lankan choropleth, "
        "district and year comparison, and a context-aware form that prefills the most "
        "recent known predictor values — because we are not going to ask an officer to "
        "type thirty-two numbers.\n\n"
        "Explain and trust: the point prediction with its interval, the SHAP "
        "contribution chart, the ERI badge, and the symbolic-regression equation as a "
        "readable cross-check. Decide and operate: a plain-language recommendation "
        "view, the model-comparison panel for technical users, and full English, "
        "Sinhala and Tamil support — because the district-level users do not all work "
        "in English.\n\n"
        "The assistant is the part I want to emphasise. A user asks, in plain "
        "language, 'why is Anuradhapura's predicted yield lower than last year?' The "
        "assistant retrieves the relevant prediction, SHAP attribution, ERI score, "
        "conformal interval and historical yield — keyed by district, season and year "
        "— and constructs the answer from those retrieved values through a "
        "template-based factual layer, with the language model handling only phrasing "
        "and translation. It does not answer from general knowledge of onion "
        "cultivation. That retrieval-then-template-then-language-model ordering is "
        "what keeps answers traceable and reduces unsupported explanations. (~75 s)")
    footer(s, 12, "Shathurya P.", "Module 3")
    return s


def slide13(prs):
    s = new_slide(prs)
    header(s, "Conclusion", "The Complete System and Its Value",
           "From fragmented agricultural data to decision-ready forecasts")

    stages = [("Historical yield  +  Weather  +  Soil  +  Satellite data", MINT, DEEP),
              ("Module 1  ·  Data integration and feature engineering", WHITE, DEEP),
              ("Module 2  ·  ML/DL prediction, ensemble and uncertainty", WHITE, DEEP),
              ("Flask REST API  ·  serving and integration layer", GREY_L, BODY),
              ("Module 3  ·  Explainability, ERI, dashboard and assistant", WHITE,
               DEEP),
              ("Early and informed agricultural decisions", DEEP, WHITE)]
    x, w, h, g = ML, 6.30, 0.64, 0.155
    for i, (t, fill, tc) in enumerate(stages):
        y = 1.58 + i * (h + g)
        line = LINE if fill == WHITE else None
        sh = shp(s, x, y, w, h, fill=fill, line=line, adj=0.15)
        write(sh.text_frame, [T(t, 11.5, True, tc, "c", sa=0, ln=0.95)],
              anchor=MSO_ANCHOR.MIDDLE, margins=(0.16, 0.16, 0.02, 0.02))
        if i < len(stages) - 1:
            arrow_d(s, x + w / 2, y + h + 0.01, h=0.135, c=LEAF)

    rx = ML + w + 0.42
    rw = SW - MR - rx
    tbox(s, rx, 1.56, rw, 0.28,
         [T("KEY VALUE", 10, True, GREEN, sa=0, spc=1.5)])
    vals = ["Predicts big onion yield before harvest",
            "Designed explicitly for severe data scarcity",
            "Provides uncertainty instead of only a single number",
            "Makes AI predictions understandable and actionable"]
    for i, v in enumerate(vals):
        y = 1.88 + i * 0.74
        shp(s, rx, y, rw, 0.62, fill=WHITE, line=LINE, adj=0.13)
        icon(s, rx + 0.18, y + 0.13, 0.36, str(i + 1), fill=GOLD, sz=12)
        tbox(s, rx + 0.66, y + 0.10, rw - 0.86, 0.46,
             [T(v, 11, True, DEEP, sa=0, ln=0.95)])

    st = shp(s, rx, 4.90, rw, 1.06, fill=MINT, adj=0.09)
    write(st.text_frame,
          [T("Agro AI converts fragmented agricultural data into early, explainable "
             "and decision-ready big onion yield forecasts for Sri Lanka.",
             12.5, True, DEEP, "l", sa=0, ln=1.05)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.24, 0.24, 0.02, 0.02))

    ty = shp(s, rx, 6.06, rw, 0.72, fill=DEEP, adj=0.13)
    write(ty.text_frame,
          [T("Thank You  —  Questions and Discussion", 15, True, WHITE, "c", sa=1),
           T("Arkam B.H.M.  ·  Sharuja B.  ·  Shathurya P.", 9.5, False,
             PALE2, "c", sa=0)],
          anchor=MSO_ANCHOR.MIDDLE, margins=(0.1, 0.1, 0.02, 0.02))

    s.notes_slide.notes_text_frame.text = (
        "To close, this is the whole system in one view. Four data streams enter "
        "Module 1, which integrates and engineers them. Module 2 trains, compares, "
        "combines and calibrates the models. The Flask REST API is the integration "
        "layer — it never trains, it only loads the persisted artefacts and serves "
        "them, which means a model can be retrained without touching the service and "
        "the service can be restarted without retraining. Module 3 turns those "
        "artefacts into explanation, reliability and a multilingual dashboard, and out "
        "the other end come early, informed agricultural decisions.\n\n"
        "Four things we would ask you to take away. It predicts before harvest, which "
        "is a capability that does not currently exist for this crop. It is designed "
        "explicitly for severe data scarcity rather than assuming the sample sizes the "
        "published literature assumes. It reports uncertainty instead of a single "
        "confident number. And it makes the prediction understandable and actionable "
        "rather than a black box.\n\n"
        "Agro AI converts fragmented agricultural data into early, explainable and "
        "decision-ready big onion yield forecasts for Sri Lanka.\n\n"
        "Thank you — we are happy to take questions. (~60 s)")
    footer(s, 13, "Arkam B.H.M.")
    return s


# ============================================================================= build
# (slide no. -> presenter, seconds, section) — sums to 900 s = 15:00
CUES = {
    1:  ("Arkam B.H.M.",  20, "Introduction"),
    2:  ("Arkam B.H.M.",  70, "Introduction"),
    3:  ("Arkam B.H.M.",  75, "Introduction"),
    4:  ("Sharuja B.",    70, "Module 1"),
    5:  ("Sharuja B.",    85, "Module 1"),
    6:  ("Sharuja B.",    70, "Module 1"),
    7:  ("Arkam B.H.M.",  75, "Module 2"),
    8:  ("Arkam B.H.M.",  75, "Module 2"),
    9:  ("Arkam B.H.M.",  75, "Module 2"),
    10: ("Shathurya P.",  80, "Module 3"),
    11: ("Shathurya P.",  70, "Module 3"),
    12: ("Shathurya P.",  75, "Module 3"),
    13: ("Arkam B.H.M.",  60, "Conclusion"),
}


def stamp_cues(prs):
    """Prefix every notes page with presenter, target time and running total."""
    run = 0
    for i, slide in enumerate(prs.slides, 1):
        who, secs, sec = CUES[i]
        run += secs
        cue = (f"[ SLIDE {i}/13 | {sec} | {who} | target {secs}s | "
               f"cumulative {run // 60}:{run % 60:02d} of 15:00 ]")
        tf = slide.notes_slide.notes_text_frame
        tf.text = cue + "\n\n" + tf.text


def build(out_path: Path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
    for fn in (slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8,
               slide9, slide10, slide11, slide12, slide13):
        fn(prs)
    stamp_cues(prs)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)
    return out_path


if __name__ == "__main__":
    out = build(Path("outputs/deck/AgroAI_Final_Presentation_15min.pptx"))
    print(f"written: {out}")

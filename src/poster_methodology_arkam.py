"""
Poster methodology figure - Arkam B.H.M. (214019K)
ML/DL & Modelling Research component, AgroAI final year project.

Renders a print-quality methodology flow diagram (PNG, 300 dpi) sized for an
A2 poster panel. Deterministic: no data reads, pure vector layout.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OUT = Path(__file__).resolve().parents[1] / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- palette
INK = "#16232B"
MUTED = "#5B6F7A"
RULE = "#D5DEE2"
PAGE = "#FFFFFF"

GREEN_D = "#0F5F4C"
GREEN_M = "#1E8168"
GREEN_L = "#E7F3EF"

AMBER_D = "#9A6206"
AMBER_M = "#D08A0B"
AMBER_L = "#FDF2DF"

BLUE_D = "#1D5478"
BLUE_M = "#2C7BAA"
BLUE_L = "#E7F0F6"

SLATE_D = "#3A4A54"
SLATE_M = "#637986"
SLATE_L = "#EEF2F4"

for family in ("Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"):
    try:
        matplotlib.rcParams["font.family"] = family
        break
    except Exception:  # pragma: no cover
        continue
matplotlib.rcParams["font.family"] = ["Helvetica", "Arial", "DejaVu Sans"]

W, H = 100.0, 74.0
fig, ax = plt.subplots(figsize=(15.0, 11.1), dpi=300)
fig.patch.set_facecolor(PAGE)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
ax.set_position([0, 0, 1, 1])


def box(x, y, w, h, title, lines, edge, fill, accent, title_size=8.4,
        body_size=6.9, bar=True):
    """Card with a coloured left rule, bold title and bullet body."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.75",
        linewidth=1.15, edgecolor=edge, facecolor=fill, zorder=3))
    if bar:
        ax.add_patch(FancyBboxPatch(
            (x + 0.45, y + 0.55), 0.55, h - 1.1,
            boxstyle="round,pad=0,rounding_size=0.27",
            linewidth=0, facecolor=accent, zorder=4))
    tx = x + 2.0
    ax.text(tx, y + h - 2.15, title, fontsize=title_size, fontweight="bold",
            color=INK, va="top", ha="left", zorder=5)
    for i, ln in enumerate(lines):
        ax.text(tx, y + h - 4.35 - i * 2.05, ln, fontsize=body_size,
                color=MUTED, va="top", ha="left", zorder=5)


def lane(y, h, num, title, sub, accent, deep):
    """Left-hand stage chip."""
    ax.add_patch(FancyBboxPatch(
        (1.6, y), 14.2, h,
        boxstyle="round,pad=0,rounding_size=0.75",
        linewidth=0, facecolor=deep, zorder=3))
    ax.add_patch(Circle((4.4, y + h - 2.9), 1.42, facecolor=PAGE,
                        edgecolor="none", zorder=4))
    ax.text(4.4, y + h - 2.9, num, fontsize=9.2, fontweight="bold",
            color=deep, ha="center", va="center", zorder=5)
    ax.text(6.7, y + h - 2.9, title, fontsize=8.6, fontweight="bold",
            color=PAGE, ha="left", va="center", zorder=5)
    for i, ln in enumerate(sub):
        ax.text(3.0, y + h - 5.7 - i * 1.72, ln, fontsize=6.15,
                color="#D9EBE5" if deep == GREEN_D else "#E3EDF3",
                ha="left", va="top", zorder=5)


def flow(y_bottom_above, y_top_below, x=57.0):
    """Connector confined strictly to the gap between two bands."""
    ax.add_patch(FancyArrowPatch(
        (x, y_bottom_above - 0.35), (x, y_top_below + 0.45),
        arrowstyle="-|>", mutation_scale=12,
        linewidth=1.5, color=SLATE_M, zorder=2,
        shrinkA=0, shrinkB=0))


# ---------------------------------------------------------------- header
ax.add_patch(FancyBboxPatch(
    (1.6, H - 8.4), W - 3.2, 7.2,
    boxstyle="round,pad=0,rounding_size=0.85",
    linewidth=0, facecolor=GREEN_D, zorder=3))
ax.text(3.6, H - 3.0, "METHODOLOGY  —  ML / DL & MODELLING RESEARCH",
        fontsize=13.0, fontweight="bold", color=PAGE, va="center", ha="left",
        zorder=5)
ax.text(3.6, H - 6.1,
        "Arkam B.H.M.  (214019K)   |   Integrity-first modelling pipeline for "
        "Big Onion yield under severe label scarcity  (n = 28 district-years)",
        fontsize=7.6, color="#BEDDD3", va="center", ha="left", zorder=5)

X0, XW = 17.4, W - 19.0
COLS4 = [(X0 + i * (XW / 4), XW / 4 - 1.15) for i in range(4)]
COLS3 = [(X0 + i * (XW / 3), XW / 3 - 1.15) for i in range(3)]

# ------------------------------------------------------- 1 DATA FOUNDATION
y1, h1 = 53.6, 10.6
lane(y1, h1, "1", "DATA FOUNDATION",
     ["Reduce four independent", "streams to one common", "district-season-year key"],
     GREEN_M, GREEN_D)
for (x, w), (t, ls) in zip(COLS4, [
    ("DCS Yield Panel", ["87 genuine month-records", "Yield = production / extent",
                         "28 district-years, 2019-25"]),
    ("NASA POWER", ["37,988 daily records", "4 district centroids",
                    "2000-2025 climatology"]),
    ("SoilGrids 250 m", ["pH, organic carbon", "clay %, sand %",
                         "static per district"]),
    ("MODIS / GEE", ["NDVI, EVI, NDWI, LST", "server-side seasonal",
                     "reduction (scope-limited)"]),
]):
    box(x, y1, w, h1, t, ls, GREEN_M, GREEN_L, GREEN_M)

# --------------------------------------------------------- 2 INTEGRITY GATE
y2, h2 = 40.6, 10.6
lane(y2, h2, "2", "INTEGRITY GATE",
     ["Nothing is modelled until", "every target value traces", "to a real DCS record"],
     AMBER_M, AMBER_D)
for (x, w), (t, ls) in zip(COLS4, [
    ("Provenance Audit", ["50 / 124 rows flagged", "source = synthetic",
                          "target rebuilt from source"]),
    ("Plausibility Filter", ["6 impossible records cut", "(worst 442 MT/ha)",
                             "thousands-separator parse fix"]),
    ("Leakage Removal", ["4 look-ahead leaks", "1981-2018 climatology base",
                         "lagged-yield terms dropped"]),
    ("Extent Weighting", ["Cells span 3.5-1,765 ha", "weight = sqrt(area), mean 1",
                          "weighted + unweighted reported"]),
]):
    box(x, y2, w, h2, t, ls, AMBER_M, AMBER_L, AMBER_M)

# ------------------------------------------------ 3 ATTAINABILITY ANALYSIS
y3, h3 = 27.6, 10.6
lane(y3, h3, "3", "ATTAINABILITY",
     ["Establish what the panel", "can support before any", "model is ranked"],
     BLUE_M, BLUE_D)
for (x, w), (t, ls) in zip(COLS3, [
    ("Variance Decomposition", ["Between years  63.6 %", "Between districts  2.2 %",
                                "Residual  34.2 %"]),
    ("Measurement-Error Model", ["Weighted spread of the", "month-records per cell",
                                 "53.6 % of within-year var"]),
    ("Attainable Ceiling", ["Implied LOYO R2 = 0.162", "Proposal target 0.75 was",
                            "unreachable by any model"]),
]):
    box(x, y3, w, h3, t, ls, BLUE_M, BLUE_L, BLUE_M)

# ----------------------------------------------------------- 4 MODEL FAMILY
y4, h4 = 14.6, 10.6
lane(y4, h4, "4", "MODEL FAMILY",
     ["Nine predictors trained", "under one identical", "protocol and seed"],
     GREEN_M, GREEN_D)
for (x, w), (t, ls, ed, fl, ac) in zip(COLS4, [
    ("Classical", ["Random Forest, XGBoost", "SVR (RBF), depth + L1/L2",
                   "capped, nested tuning"], GREEN_M, GREEN_L, GREEN_M),
    ("Deep Sequence", ["LSTM, BiLSTM, 1D-CNN,", "hybrid CNN-LSTM (44,929 p)",
                       "weights reset every fold"], GREEN_M, GREEN_L, GREEN_M),
    ("Symbolic + Stack", ["gplearn GP over top-5", "SHAP predictors; convex",
                          "simplex-constrained blend"], GREEN_M, GREEN_L, GREEN_M),
    ("PADR  (contribution)", ["Phenology-Aligned Differentiable",
                              "Response - 17 parameters,",
                              "agronomic constants ESTIMATED"],
     AMBER_M, AMBER_L, AMBER_M),
]):
    box(x, y4, w, h4, t, ls, ed, fl, ac, body_size=6.55)

# ------------------------------------------------------- 5 HONEST EVALUATION
y5, h5 = 1.6, 10.6
lane(y5, h5, "5", "HONEST EVALUATION",
     ["Every fitted quantity", "re-estimated inside the", "fold; nothing pooled"],
     BLUE_M, BLUE_D)
for (x, w), (t, ls) in zip(COLS4, [
    ("Leave-One-Year-Out", ["7 folds x 4 held-out cells", "Nested inner tuning",
                            "Wilcoxon paired residuals"]),
    ("Mechanism Ablations", ["7 arms isolate each claim", "Learned vs fixed physics:",
                             "dR2 = +0.566"]),
    ("Power + Identifiability", ["Detects weather signal at", "6 % of variance; 5 / 7",
                                 "constants recovered"]),
    ("Blocked Conformal", ["Year-blocked cross-conformal", "Coverage 0.911 vs 0.90",
                           "Half-width +/- 15.3 MT/ha"]),
]):
    box(x, y5, w, h5, t, ls, BLUE_M, BLUE_L, BLUE_M)

# ------------------------------------------------------------ connectors
flow(y1, y2 + h2)
flow(y2, y3 + h3)
flow(y3, y4 + h4)
flow(y4, y5 + h5)

fig.savefig(OUT / "arkam_methodology.png", dpi=300, facecolor=PAGE,
            bbox_inches="tight", pad_inches=0.22)
fig.savefig(OUT / "arkam_methodology.pdf", facecolor=PAGE,
            bbox_inches="tight", pad_inches=0.22)
print("wrote", OUT / "arkam_methodology.png")

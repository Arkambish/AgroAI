"""Poster-specific figures for the A2 exhibition poster.

Redraws the system architecture in the poster's palette (navy / blue / violet /
orange — no green), without the report's embedded figure caption, and with the
current model count. Also renders a compact results panel sized for a poster
column.

Output: outputs/poster/*.png
Usage:  python src/generate_poster_figures.py
"""

from __future__ import annotations

import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "outputs", "results_real")
OUT = os.path.join(ROOT, "outputs", "poster")

SURFACE = "#ffffff"
NAVY = "#0d366b"
BLUE = "#2a78d6"
BLUE_PALE = "#cde2fb"
ORANGE = "#eb6834"
ORANGE_PALE = "#fbe0d5"
VIOLET = "#4a3aa7"
VIOLET_PALE = "#ddd9f2"
INK = "#0b0b0b"
INK_2 = "#52514e"
GREY_PALE = "#eeedea"
NEUTRAL = "#c9c8c2"


def _box(ax, x, y, w, h, label, *, face, edge, text_color=INK, size=9.2,
         weight="normal", radius=0.02):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=1.4, zorder=2))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=size, color=text_color, fontweight=weight, zorder=3,
            linespacing=1.45)


def _arrow(ax, start, end, *, color=INK_2):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=13,
        linewidth=1.2, color=color, zorder=1,
        shrinkA=1, shrinkB=1))


def architecture() -> str:
    fig, ax = plt.subplots(figsize=(8.6, 4.9))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # --- Row 1: external data sources -------------------------------------
    ax.text(1, 96.5, "EXTERNAL DATA SOURCES", fontsize=10.5, color=ORANGE,
            fontweight="bold")
    sources = ["DCS yield\nreports", "NASA POWER\n+ CHIRPS",
               "MODIS / Sentinel-2\n(Earth Engine)", "MODIS\nsurface temp.",
               "ISRIC\nSoilGrids"]
    sw, gap = 17.2, 3.5
    for i, s in enumerate(sources):
        _box(ax, i * (sw + gap), 84.5, sw, 9.5, s,
             face=ORANGE_PALE, edge=ORANGE, size=9.6)
        _arrow(ax, (i * (sw + gap) + sw / 2, 84.5), (24, 72.5))

    # --- Row 2: the three build modules -----------------------------------
    mods = [
        (0, BLUE_PALE, BLUE,
         "MODULE 1 — Data pipeline\n(Sharuja B.)\n\nIngestion · reconciliation\ncleaning · 32 features"),
        (34.3, VIOLET_PALE, VIOLET,
         "MODULE 2 — Prediction engine\n(Arkam B.H.M.)\n\n9 models · LOYO-CV · SHAP\nconformal · Flask REST API"),
        (68.6, ORANGE_PALE, ORANGE,
         "MODULE 3 — Dashboard\n(Shathurya P.)\n\nNext.js · choropleth\nexplainability · advisory"),
    ]
    for x, face, edge, label in mods:
        _box(ax, x, 55.5, 31.4, 17.0, label, face=face, edge=edge, size=9.6)

    _arrow(ax, (31.4, 64.0), (34.3, 64.0))
    _arrow(ax, (65.7, 64.0), (68.6, 64.0))
    for x in (15.7, 50.0, 84.3):
        _arrow(ax, (x, 55.5), (x, 45.5))

    # --- Row 3: persisted artefact store -----------------------------------
    _box(ax, 0, 34.5, 100, 11.0,
         "PERSISTED ARTEFACT STORE\n"
         "processed dataset · trained models · out-of-fold predictions · metrics\n"
         "conformal quantiles · SHAP attributions · symbolic equation",
         face=GREY_PALE, edge=NEUTRAL, size=9.6)

    for x in (25, 50, 75):
        _arrow(ax, (x, 34.5), (x, 24.0))

    # --- Row 4: end users --------------------------------------------------
    ax.text(1, 26.0, "END USERS", fontsize=10.5, color=NAVY, fontweight="bold")
    users = ["Dept. of Census\n& Statistics",
             "Dept. of Agriculture\npolicy planners",
             "District agricultural\nofficers",
             "Researchers\n& students"]
    uw, ugap = 22.7, 2.8
    for i, u in enumerate(users):
        _box(ax, i * (uw + ugap), 12.0, uw, 11.0, u,
             face="#f7f6f4", edge=NAVY, size=9.6)

    fig.tight_layout(pad=0.2)
    path = os.path.join(OUT, "architecture.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def results_panel() -> str:
    """Compact RMSE comparison sized for one poster column."""
    # Panel-local palette. Scoped here so the architecture and physics figures
    # keep the original navy/blue/violet scheme.
    R_NOVELTY = "#123725"   # was VIOLET  #4a3aa7
    R_CLASSICAL = "#4A663C"   # was BLUE    #2a78d6
    R_DEEP = "#D49237"   # was ORANGE  #eb6834

    with open(os.path.join(RESULTS, "model_comparison.csv"), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rows.sort(key=lambda r: float(r["RMSE"]), reverse=True)

    pretty = {"PADR": "PADR", "PhysResidual": "Physics-residual hybrid",
              "RandomForest": "Random Forest",
              "XGBoost": "XGBoost", "SVR": "SVR", "StackConvex": "Stack (convex)",
              "StackInvRMSE": "Stack (inv-RMSE)", "StackMean": "Stack (mean)",
              "BiLSTM": "BiLSTM", "SymbolicRegression": "Symbolic regression",
              "LSTM": "LSTM", "CNN_LSTM_Hybrid": "Hybrid CNN-LSTM", "CNN": "1D-CNN"}
    fam = {"RandomForest": R_CLASSICAL, "XGBoost": R_CLASSICAL, "SVR": R_CLASSICAL,
           "LSTM": R_DEEP, "BiLSTM": R_DEEP, "CNN": R_DEEP, "CNN_LSTM_Hybrid": R_DEEP}

    names = [pretty[r["Model"]] for r in rows]
    vals = [float(r["RMSE"]) for r in rows]
    colors = [fam.get(r["Model"], R_NOVELTY) for r in rows]

    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    y = range(len(names))
    ax.barh(list(y), vals, height=0.62, color=colors)
    for i, v in enumerate(vals):
        ax.text(v + 0.16, i, f"{v:.2f}", va="center", fontsize=10.5,
                color=INK, fontweight="600")
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=10.5, color=INK)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(length=0)
    ax.set_xlim(0, max(vals) * 1.14)
    ax.invert_yaxis()
    ax.set_xlabel("RMSE (MT/Ha) — lower is better", fontsize=10.5, color=INK_2,
                  labelpad=8)

    handles = [plt.Rectangle((0, 0), 1, 1, color=c)
               for c in (R_NOVELTY, R_CLASSICAL, R_DEEP)]
    ax.legend(handles, ["Novelty / hybrid", "Classical ML", "Deep learning"],
              loc="lower right", frameon=False, fontsize=10, labelcolor=INK_2,
              handlelength=1.1, handleheight=1.1)
    fig.tight_layout(pad=0.3)
    path = os.path.join(OUT, "results.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def scoreboard_panel() -> str:
    """LOYO R2 for every model against the attainable ceiling, in the poster palette.

    This is the figure that carries the finding: R2 has a built-in reference, so
    'worse than predicting the mean' is visible as a bar left of zero. The RMSE
    panel cannot show that.
    """
    S_PADR = "#123725"
    S_OTHER = "#4A663C"
    S_CEIL = "#D49237"
    S_ORACLE = "#b9b8b1"

    with open(os.path.join(RESULTS, "padr_comparison.csv"), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(os.path.join(RESULTS, "variance_decomposition.json"), encoding="utf-8") as fh:
        ceiling = float(json.load(fh)["implied_loyo_r2_ceiling"])

    rows.sort(key=lambda r: float(r["R2"]))
    pretty = {"Oracle_YearMean": "Oracle year-mean  (not achievable)",
              "TrainMean": "Train mean  (no features)", "DistrictMean": "District mean",
              "XGBoost": "XGBoost", "PADR": "PADR", "RandomForest": "Random Forest",
              "SVR_rbf": "SVR", "Persistence": "Persistence"}

    names = [pretty.get(r["Model"], r["Model"]) for r in rows]
    vals = [float(r["R2"]) for r in rows]
    colors = [S_ORACLE if r["achievable"].strip().lower() != "true"
              else (S_PADR if r["Model"] == "PADR" else S_OTHER) for r in rows]

    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    y = list(range(len(names)))
    ax.barh(y, vals, height=0.62, color=colors, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + (0.022 if v >= 0 else -0.022), i, f"{v:+.3f}",
                va="center", ha="left" if v >= 0 else "right",
                fontsize=10.5, color=INK, fontweight="600", zorder=4)

    ax.axvline(0, color=NEUTRAL, lw=1.2, zorder=2)
    ax.axvline(ceiling, color=S_CEIL, lw=2.0, ls="--", zorder=4)
    ax.text(ceiling + 0.015, len(names) - 0.45, f"attainable ceiling  {ceiling:.3f}",
            color=S_CEIL, fontsize=10, va="center", fontweight="600", zorder=5)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10.5, color=INK)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(length=0)
    span = max(vals) - min(vals)
    ax.set_xlim(min(vals) - 0.17 * span, max(vals) + 0.30 * span)
    ax.set_xlabel("Leave-One-Year-Out R²  —  left of 0 is worse than predicting the mean",
                  fontsize=10.5, color=INK_2, labelpad=8)

    fig.tight_layout(pad=0.3)
    path = os.path.join(OUT, "scoreboard.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def ceiling_panel() -> str:
    """Where the variance lives, and what R2 was therefore reachable.

    The headline results figure: it explains why every model score on the poster
    is negative before the reader can mistake it for a modelling failure.
    """
    C_KEY = "#123725"
    C_SEC = "#4A663C"
    C_CEIL = "#D49237"
    C_DEAD = "#b9b8b1"

    with open(os.path.join(RESULTS, "variance_decomposition.json"), encoding="utf-8") as fh:
        summary = json.load(fh)
    with open(os.path.join(RESULTS, "padr_comparison.csv"), encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["achievable"].strip().lower() == "true"]
    best = max(float(r["R2"]) for r in rows)
    ceiling = float(summary["implied_loyo_r2_ceiling"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.75),
                                   gridspec_kw={"width_ratios": [1.16, 1.0]})
    fig.patch.set_facecolor(SURFACE)

    # ---- left: variance decomposition
    labels = ["between YEAR", "between DISTRICT", "residual"]
    shares = [summary["year_pct"], summary["district_pct"], summary["residual_pct"]]
    ax1.set_facecolor(SURFACE)
    ax1.barh(labels, shares, color=[C_KEY, C_SEC, C_DEAD], height=0.58, zorder=3)
    for i, v in enumerate(shares):
        ax1.text(v + 1.4, i, f"{v:.1f}%", va="center", fontsize=12,
                 fontweight="bold", color=INK, zorder=4)
    ax1.annotate("leave-one-year-out\nremoves this by design",
                 xy=(shares[0] * 0.55, 0.34), xytext=(shares[0] * 0.55, 1.30),
                 fontsize=9.6, color=C_CEIL, fontweight="600",
                 ha="center", va="center",
                 arrowprops={"arrowstyle": "-|>", "color": C_CEIL, "lw": 1.5})
    ax1.set_xlim(0, max(shares) * 1.26)
    ax1.invert_yaxis()
    ax1.set_xlabel("share of total variance (%)", fontsize=10, color=INK_2, labelpad=6)
    ax1.set_title("Where yield variance lives", fontsize=12.5, color=INK,
                  loc="left", pad=10, fontweight="bold")

    # ---- right: attainable R2
    names = ["original\ntarget", "implied\nceiling", "best achieved\n(train mean)"]
    vals = [0.75, ceiling, best]
    ax2.set_facecolor(SURFACE)
    bars = ax2.bar(names, vals, color=[C_DEAD, C_CEIL, C_KEY], width=0.56, zorder=3)
    for bar, v in zip(bars, vals):
        ax2.text(bar.get_x() + bar.get_width() / 2, v + (0.035 if v >= 0 else -0.075),
                 f"{v:.3f}", ha="center", fontsize=12, fontweight="bold",
                 color=INK, zorder=4)
    ax2.axhline(0, color=NEUTRAL, lw=1.2, zorder=2)
    ax2.set_ylim(min(vals) - 0.22, 1.0)
    ax2.set_ylabel("R²", fontsize=10, color=INK_2)
    ax2.set_title("Attainable R² under LOYO", fontsize=12.5, color=INK,
                  loc="left", pad=10, fontweight="bold")
    ax2.text(0.99, 0.90,
             "measurement error alone is\n"
             f"{100 * summary['measurement_share_of_within_year_var']:.0f}% "
             "of within-year variance",
             transform=ax2.transAxes, fontsize=9.4, color=INK_2,
             va="top", ha="right")

    for ax in (ax1, ax2):
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(NEUTRAL)
        ax.tick_params(colors=INK_2, labelsize=10.5, length=0)

    fig.suptitle("The R² > 0.75 target was not difficult — it was unattainable",
                 fontsize=14.5, color=INK, x=0.008, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(OUT, "ceiling.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def physics_panel() -> str:
    """The headline novelty result, sized for a poster column."""
    d = json.load(open(os.path.join(RESULTS, "physics_residual.json"), encoding="utf-8"))
    vals = [d["backbone_only_metrics"]["R2"], d["plain_randomforest_R2"],
            d["hybrid_metrics"]["R2"]]
    labels = ["Agronomic\nbackbone alone", "Random Forest\nalone", "Physics-residual\nhybrid"]

    fig, ax = plt.subplots(figsize=(8.0, 2.5))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.bar([0, 1, 2], vals, width=0.5, color=[NEUTRAL, NEUTRAL, VIOLET], zorder=3)
    ax.axhline(0, color=INK_2, linewidth=1.1, zorder=4)
    span = max(vals) - min(vals)
    for i, v in enumerate(vals):
        ax.text(i, v + (span * 0.05 if v >= 0 else -span * 0.05), f"{v:+.3f}",
                ha="center", va="bottom" if v >= 0 else "top",
                fontsize=11, color=INK, fontweight="700")
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(labels, fontsize=10, color=INK)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.set_yticks([])
    ax.tick_params(length=0)
    ax.set_ylim(min(vals) - span * 0.28, max(vals) + span * 0.28)
    fig.tight_layout(pad=0.3)
    path = os.path.join(OUT, "physics.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def build() -> list[str]:
    os.makedirs(OUT, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    })
    return [architecture(), results_panel(), physics_panel()]


if __name__ == "__main__":
    for p in build():
        print("wrote", os.path.relpath(p, ROOT))

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
    with open(os.path.join(RESULTS, "model_comparison.csv"), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rows.sort(key=lambda r: float(r["RMSE"]), reverse=True)

    pretty = {"PhysResidual": "Physics-residual hybrid  (best)", "RandomForest": "Random Forest",
              "XGBoost": "XGBoost", "SVR": "SVR", "StackConvex": "Stack (convex)",
              "StackInvRMSE": "Stack (inv-RMSE)", "StackMean": "Stack (mean)",
              "BiLSTM": "BiLSTM", "SymbolicRegression": "Symbolic regression",
              "LSTM": "LSTM", "CNN_LSTM_Hybrid": "Hybrid CNN-LSTM", "CNN": "1D-CNN"}
    fam = {"RandomForest": BLUE, "XGBoost": BLUE, "SVR": BLUE,
           "LSTM": ORANGE, "BiLSTM": ORANGE, "CNN": ORANGE, "CNN_LSTM_Hybrid": ORANGE}

    names = [pretty[r["Model"]] for r in rows]
    vals = [float(r["RMSE"]) for r in rows]
    colors = [fam.get(r["Model"], VIOLET) for r in rows]

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

    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (VIOLET, BLUE, ORANGE)]
    ax.legend(handles, ["Novelty / hybrid", "Classical ML", "Deep learning"],
              loc="lower right", frameon=False, fontsize=10, labelcolor=INK_2,
              handlelength=1.1, handleheight=1.1)
    fig.tight_layout(pad=0.3)
    path = os.path.join(OUT, "results.png")
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

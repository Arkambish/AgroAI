"""Generate presentation-quality figures for the FYP final-defence deck.

Regenerates the key result charts in the deck's palette (blue / orange / violet
— deliberately no green) with clean typography and direct value labels, so the
slides do not inherit the pipeline's default matplotlib styling.

Palette validated with the dataviz skill's checker (all-pairs, light surface):
worst CVD ΔE 13.0, worst normal-vision ΔE 16.3, all slots >= 3:1 on surface.

Output: outputs/deck/*.png
Usage:  python src/generate_deck_figures.py
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "outputs", "results_real")
SYNTH_RESULTS = os.path.join(ROOT, "outputs", "results")
OUT = os.path.join(ROOT, "outputs", "deck")

# ---- Palette ---------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#8a8983"
GRID = "#e4e3df"

BLUE = "#2a78d6"     # slot 1 — classical ML
ORANGE = "#eb6834"   # slot 2 — deep learning
VIOLET = "#4a3aa7"   # slot 7 — novelty / hybrid
NEUTRAL = "#c9c8c2"  # de-emphasised bars
RED = "#e34948"      # below-baseline emphasis

FAMILY_COLOR = {"Classical ML": BLUE, "Deep learning": ORANGE, "Novelty / hybrid": VIOLET}

FAMILY_OF = {
    "PhysResidual": "Novelty / hybrid",
    "StackConvex": "Novelty / hybrid",
    "StackInvRMSE": "Novelty / hybrid",
    "StackMean": "Novelty / hybrid",
    "SymbolicRegression": "Novelty / hybrid",
    "RandomForest": "Classical ML",
    "XGBoost": "Classical ML",
    "SVR": "Classical ML",
    "LSTM": "Deep learning",
    "BiLSTM": "Deep learning",
    "CNN": "Deep learning",
    "CNN_LSTM_Hybrid": "Deep learning",
}

PRETTY = {
    "PhysResidual": "Physics-residual hybrid",
    "RandomForest": "Random Forest",
    "XGBoost": "XGBoost",
    "SVR": "SVR",
    "StackConvex": "Stack (convex)",
    "StackInvRMSE": "Stack (inv-RMSE)",
    "StackMean": "Stack (mean)",
    "BiLSTM": "BiLSTM",
    "SymbolicRegression": "Symbolic regression",
    "LSTM": "LSTM",
    "CNN_LSTM_Hybrid": "Hybrid CNN-LSTM",
    "CNN": "1D-CNN",
}


def _base_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "text.color": INK,
        "axes.labelcolor": INK_2,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.8,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "figure.dpi": 200,
    })


def _strip(ax, *, keep_x=False, keep_y=False) -> None:
    """Recessive axes: drop spines and the axis the direct labels replace."""
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    if not keep_x:
        ax.set_xticks([])
    if not keep_y:
        ax.set_yticks([])


def _read_comparison(path: str) -> list[dict]:
    import csv
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------

def fig_model_comparison() -> str:
    """Horizontal RMSE bars, coloured by model family. Lower is better."""
    rows = _read_comparison(os.path.join(RESULTS, "model_comparison.csv"))
    rows.sort(key=lambda r: float(r["RMSE"]), reverse=True)

    names = [PRETTY.get(r["Model"], r["Model"]) for r in rows]
    rmse = [float(r["RMSE"]) for r in rows]
    r2 = [float(r["R2"]) for r in rows]
    colors = [FAMILY_COLOR[FAMILY_OF[r["Model"]]] for r in rows]

    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    y = range(len(names))
    ax.barh(list(y), rmse, height=0.62, color=colors)

    for i, (v, r) in enumerate(zip(rmse, r2)):
        ax.text(v + 0.18, i, f"{v:.2f}", va="center", ha="left",
                fontsize=10.5, color=INK, fontweight="600")
        ax.text(v + 1.35, i, f"R² {r:+.3f}", va="center", ha="left",
                fontsize=9.5, color=INK_MUTED)

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=11, color=INK)
    _strip(ax, keep_y=True)
    ax.set_xlim(0, max(rmse) * 1.30)
    ax.invert_yaxis()
    ax.set_xlabel("RMSE  (MT/Ha)  —  lower is better", fontsize=10.5, labelpad=10)

    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in FAMILY_COLOR.values()]
    ax.legend(handles, list(FAMILY_COLOR), loc="lower right", frameon=False,
              fontsize=10.5, labelcolor=INK_2, handlelength=1.1, handleheight=1.1)

    fig.tight_layout()
    path = os.path.join(OUT, "model_comparison.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def _r2_bars(labels, values, colors, title_note, filename, *, figsize=(10.5, 5.2),
             note=None):
    """Shared vertical-bar renderer for the R² comparisons, with a zero baseline."""
    fig, ax = plt.subplots(figsize=figsize)
    x = range(len(labels))
    ax.bar(list(x), values, width=0.55, color=colors, zorder=3)
    ax.axhline(0, color=INK_2, linewidth=1.1, zorder=4)

    span = max(values) - min(min(values), 0)
    for i, v in enumerate(values):
        off = span * 0.035
        ax.text(i, v + (off if v >= 0 else -off), f"{v:+.3f}",
                ha="center", va="bottom" if v >= 0 else "top",
                fontsize=11, color=INK, fontweight="600")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10.5, color=INK)
    _strip(ax, keep_x=True)
    ax.set_ylim(min(min(values), 0) - span * 0.22, max(values) + span * 0.22)
    ax.set_ylabel("R²", fontsize=10.5, labelpad=8)
    ax.text(0, 1.04, title_note, transform=ax.transAxes, fontsize=10.5,
            color=INK_MUTED, ha="left")
    if note:
        ax.text(0, -0.20, note, transform=ax.transAxes, fontsize=9.5,
                color=INK_MUTED, ha="left")

    fig.tight_layout()
    path = os.path.join(OUT, filename)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_physics_ablation() -> str:
    """Backbone alone vs learner alone vs the hybrid."""
    d = json.load(open(os.path.join(RESULTS, "physics_residual.json"), encoding="utf-8"))
    values = [
        d["backbone_only_metrics"]["R2"],
        d["plain_randomforest_R2"],
        d["hybrid_metrics"]["R2"],
    ]
    labels = ["Mechanistic backbone\nalone", "Random Forest\nalone", "Physics-residual\nhybrid"]
    return _r2_bars(labels, values, [NEUTRAL, NEUTRAL, VIOLET],
                    "Zero line = predicting the mean", "physics_ablation.png",
                    figsize=(8.6, 5.0),
                    note="Adding the agronomic prior lifts R² by +0.070 over the same learner alone.")


def fig_stacking() -> str:
    d = json.load(open(os.path.join(RESULTS, "stacking_summary.json"), encoding="utf-8"))
    c = d["combiners"]
    best = json.load(open(os.path.join(RESULTS, "best_model_metrics.json"), encoding="utf-8"))
    labels = ["Equal-weight\nmean", "Inverse-RMSE\nweights", "Convex\n(learned)", "Best single model\n(physics-residual)"]
    values = [c["StackMean"]["R2"], c["StackInvRMSE"]["R2"], c["StackConvex"]["R2"], best["R2"]]
    return _r2_bars(labels, values, [NEUTRAL, NEUTRAL, BLUE, VIOLET],
                    "Zero line = predicting the mean", "stacking.png",
                    figsize=(9.6, 5.0),
                    note="Learned weights beat the equal-weight mean — but no blend beats the single best model.")


def fig_ablation_sources() -> str:
    rows = _read_comparison(os.path.join(RESULTS, "ablation_results.csv"))
    pretty = {"A_Weather_only": "Weather\nonly", "B_Satellite_only": "Satellite\nonly",
              "C_Historical_only": "History\nonly", "D_Soil_only": "Soil\nonly",
              "E_Weather+Satellite": "Weather +\nSatellite", "F_All_features": "All\nsources"}
    labels = [pretty[r["Experiment"]] for r in rows]
    values = [float(r["R2"]) for r in rows]
    colors = [BLUE if r["Experiment"] == "F_All_features" else NEUTRAL for r in rows]
    return _r2_bars(labels, values, colors,
                    "Zero line = predicting the mean", "ablation_sources.png",
                    figsize=(10.2, 5.0),
                    note="No single stream carries the signal; only the full set approaches the baseline.")


def fig_per_district() -> str:
    """Small multiples — R² and MAE side by side. Never a dual axis."""
    districts = ["Anuradhapura", "Polonnaruwa", "Matale", "Kurunegala"]
    r2 = [0.361, 0.220, 0.023, -1.183]
    mae = [2.176, 3.301, 4.381, 3.540]

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.9))
    for ax, vals, title, fmt, color in (
        (axes[0], r2, "R²  —  higher is better", "{:+.3f}", BLUE),
        (axes[1], mae, "MAE (MT/Ha)  —  lower is better", "{:.2f}", ORANGE),
    ):
        x = range(len(districts))
        ax.bar(list(x), vals, width=0.55, color=color, zorder=3)
        ax.axhline(0, color=INK_2, linewidth=1.0, zorder=4)
        span = max(vals) - min(min(vals), 0)
        for i, v in enumerate(vals):
            off = span * 0.04
            ax.text(i, v + (off if v >= 0 else -off), fmt.format(v), ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=10.5,
                    color=INK, fontweight="600")
        ax.set_xticks(list(x))
        ax.set_xticklabels(districts, fontsize=10, color=INK, rotation=18, ha="right")
        _strip(ax, keep_x=True)
        ax.set_ylim(min(min(vals), 0) - span * 0.25, max(vals) + span * 0.25)
        ax.text(0, 1.05, title, transform=ax.transAxes, fontsize=10.5,
                color=INK_MUTED, ha="left")

    fig.text(0.01, -0.03,
             "The ranking reverses between the two measures: R² is normalised by each "
             "district's own variance, and Kurunegala's is smallest.",
             fontsize=9.5, color=INK_MUTED, ha="left")
    fig.tight_layout()
    path = os.path.join(OUT, "per_district.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_sample_size() -> str:
    """The headline argument: identical code, two sample sizes."""
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    labels = ["Collected data\n28 records", "Synthetic reference\n~160 records"]
    values = [0.0908, 0.8421]
    ax.bar([0, 1], values, width=0.38, color=[VIOLET, BLUE], zorder=3)
    ax.axhline(0.75, color=RED, linewidth=1.4, linestyle="--", zorder=4)
    # Label sits left of the first bar so it never overlaps a mark.
    ax.text(-0.44, 0.768, "target R² = 0.75", fontsize=10, color=RED,
            ha="left", va="bottom")
    for i, v in enumerate(values):
        ax.text(i, v + 0.03, f"{v:.3f}", ha="center", fontsize=13,
                color=INK, fontweight="700")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels, fontsize=11, color=INK)
    _strip(ax, keep_x=True)
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Best-model R²", fontsize=10.5, labelpad=8)
    ax.text(0, 1.04, "Identical pipeline, identical code — only the sample size differs",
            transform=ax.transAxes, fontsize=10.5, color=INK_MUTED)
    fig.tight_layout()
    path = os.path.join(OUT, "sample_size.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_conformal() -> str:
    d = json.load(open(os.path.join(RESULTS, "conformal.json"), encoding="utf-8"))
    items = sorted(((PRETTY.get(k, k), v["q"], k) for k, v in d.items()),
                   key=lambda t: t[1], reverse=True)
    names = [i[0] for i in items]
    q = [i[1] for i in items]
    colors = [VIOLET if i[2] == "PhysResidual" else NEUTRAL for i in items]

    fig, ax = plt.subplots(figsize=(10.4, 5.6))
    y = range(len(names))
    ax.barh(list(y), q, height=0.6, color=colors)
    for i, v in enumerate(q):
        ax.text(v + 0.35, i, f"±{v:.2f}", va="center", fontsize=10.5, color=INK)
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=10.5, color=INK)
    _strip(ax, keep_y=True)
    ax.set_xlim(0, max(q) * 1.16)
    ax.invert_yaxis()
    ax.set_xlabel("90% conformal interval half-width  (MT/Ha)  —  narrower is better",
                  fontsize=10.5, labelpad=10)
    ax.text(0, 1.03, "Mean observed yield is 16.39 MT/Ha", transform=ax.transAxes,
            fontsize=10.5, color=INK_MUTED)
    fig.tight_layout()
    path = os.path.join(OUT, "conformal.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_shap() -> str:
    """Top-8 SHAP attributions, highlighting the engineered interaction terms."""
    data = json.load(open(os.path.join(RESULTS, "feature_importance.json"), encoding="utf-8"))[:8]
    interactions = {"temp_x_humidity", "rainfall_x_ndvi", "ndvi_x_lst"}
    names = [d["name"] for d in data][::-1]
    vals = [d["mean_abs_shap"] for d in data][::-1]
    colors = [ORANGE if n in interactions else BLUE for n in names]

    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    y = range(len(names))
    ax.barh(list(y), vals, height=0.6, color=colors)
    for i, v in enumerate(vals):
        ax.text(v + max(vals) * 0.015, i, f"{v:.3f}", va="center",
                fontsize=10.5, color=INK)
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=11, color=INK)
    _strip(ax, keep_y=True)
    ax.set_xlim(0, max(vals) * 1.16)
    ax.set_xlabel("Mean |SHAP| attribution", fontsize=10.5, labelpad=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=ORANGE),
               plt.Rectangle((0, 0), 1, 1, color=BLUE)]
    ax.legend(handles, ["Engineered interaction term", "Measured predictor"],
              loc="lower right", frameon=False, fontsize=10.5, labelcolor=INK_2,
              handlelength=1.1, handleheight=1.1)
    fig.tight_layout()
    path = os.path.join(OUT, "shap_top.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def build() -> list[str]:
    os.makedirs(OUT, exist_ok=True)
    _base_style()
    return [
        fig_model_comparison(),
        fig_physics_ablation(),
        fig_stacking(),
        fig_ablation_sources(),
        fig_per_district(),
        fig_sample_size(),
        fig_conformal(),
        fig_shap(),
    ]


if __name__ == "__main__":
    for p in build():
        print("wrote", os.path.relpath(p, ROOT))

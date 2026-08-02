"""
Poster panel — "Model Families", Arkam B.H.M. (214019K)

Drop-in replacement for the plain bullet list in the Prediction Engine &
Comparative Modelling column. Sized for a single A2 poster column and drawn in
the same card language as arkam_methodology.png so the panel reads as one system.

Parameter counts are the trained values from outputs/results_real/model_comparison.csv.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#16232B"
MUTED = "#5B6F7A"
PAGE = "#FFFFFF"

GREEN_D = "#123725"   # novelty / PADR
GREEN_M = "#4A663C"   # classical + symbolic
GREEN_L = "#EDF2EA"
AMBER_M = "#D49237"   # deep learning
AMBER_L = "#FBF1E3"
DARK_L = "#E4EBE5"

matplotlib.rcParams["font.family"] = ["Helvetica", "Arial", "DejaVu Sans"]

W, H = 100.0, 61.0
fig, ax = plt.subplots(figsize=(7.6, 4.64), dpi=300)
fig.patch.set_facecolor(PAGE)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
ax.set_position([0, 0, 1, 1])

# ------------------------------------------------------------------ header
ax.add_patch(FancyBboxPatch(
    (1.2, 51.6), W - 2.4, 8.2,
    boxstyle="round,pad=0,rounding_size=0.9",
    linewidth=0, facecolor=GREEN_D, zorder=3))
ax.text(4.0, 57.1, "MODEL FAMILIES", fontsize=15.0, fontweight="bold",
        color=PAGE, va="center", ha="left", zorder=5)
ax.text(4.0, 53.6,
        "Nine predictors  ·  one identical protocol  ·  one fixed seed",
        fontsize=8.6, color="#AFC6B4", va="center", ha="left", zorder=5)


def family(y, h, name, models, note, badge, edge, fill, accent,
           name_color=INK, badge_fg=PAGE):
    ax.add_patch(FancyBboxPatch(
        (1.2, y), W - 2.4, h,
        boxstyle="round,pad=0,rounding_size=0.85",
        linewidth=1.2, edgecolor=edge, facecolor=fill, zorder=3))
    ax.add_patch(FancyBboxPatch(
        (1.75, y + 0.7), 0.75, h - 1.4,
        boxstyle="round,pad=0,rounding_size=0.34",
        linewidth=0, facecolor=accent, zorder=4))

    ax.text(4.2, y + h - 2.6, name, fontsize=11.4, fontweight="bold",
            color=name_color, va="center", ha="left", zorder=5)
    ax.text(4.2, y + h - 6.3, models, fontsize=9.0, color=INK,
            va="center", ha="left", zorder=5)
    ax.text(4.2, y + h - 9.4, note, fontsize=8.0, color=MUTED,
            va="center", ha="left", zorder=5, style="italic")

    # right-hand parameter badge
    bw = 20.0
    ax.add_patch(FancyBboxPatch(
        (W - 2.9 - bw, y + h / 2 - 3.05), bw, 6.1,
        boxstyle="round,pad=0,rounding_size=0.75",
        linewidth=0, facecolor=accent, zorder=4))
    ax.text(W - 2.9 - bw / 2, y + h / 2 + 0.95, badge[0], fontsize=11.0,
            fontweight="bold", color=badge_fg, ha="center", va="center", zorder=5)
    ax.text(W - 2.9 - bw / 2, y + h / 2 - 1.85, badge[1], fontsize=7.4,
            color=badge_fg, ha="center", va="center", zorder=5)


ROW_H = 11.4
family(38.4, ROW_H, "Classical ML",
       "Random Forest  ·  XGBoost  ·  SVR (RBF)",
       "depth-capped, L1+L2, nested inner tuning",
       ("3", "models"), GREEN_M, GREEN_L, GREEN_M)

family(25.6, ROW_H, "Deep sequence",
       "LSTM  ·  BiLSTM  ·  1D-CNN  ·  Hybrid CNN-LSTM",
       "weights re-initialised every fold; early stopping",
       ("8.6k–77.6k", "parameters"), AMBER_M, AMBER_L, AMBER_M)

family(12.8, ROW_H, "Symbolic regression",
       "Genetic programming over the top-5 SHAP predictors",
       "closed-form equation an officer can read and check",
       ("5", "predictors"), GREEN_M, GREEN_L, GREEN_M)

family(0.0, ROW_H, "PADR   — technical contribution",
       "Phenology-Aligned Differentiable Response",
       "agronomic constants estimated, not assumed",
       ("17", "parameters"), GREEN_D, DARK_L, GREEN_D)

fig.savefig(OUT / "arkam_model_families.png", dpi=300, facecolor=PAGE,
            bbox_inches="tight", pad_inches=0.16)
fig.savefig(OUT / "arkam_model_families.pdf", facecolor=PAGE,
            bbox_inches="tight", pad_inches=0.16)
print("wrote", OUT / "arkam_model_families.png")

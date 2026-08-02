"""Schematic figures for the FINAL report.

These replace the interim-report schematics in outputs/plots/figures/, which had
drifted from the text and the code. Every label here is traceable:

  4.1  four modules, matching section 4.5 ("data integration, modelling, serving
       and presentation ... separated by file and HTTP interfaces"). The interim
       version showed three modules and a PostgreSQL store that does not exist
       (api.py still carries "TODO: Implement PostgreSQL storage here").
  4.2  the nine stages named in section 4.4. The interim version showed five
       stages with entirely different names.
  5.1  data flow with the file interfaces section 5.2 promises ("each arrow
       represents a file written by one component and read by the next"), and
       all nine base learners rather than seven.
  5.3  the logical artefact schema of section 5.9, keyed as the text states,
       rather than a seven-table relational ERD that was never built.
  6.1  the hybrid's learning curve, restyled to match the chapter 7 figures and
       annotated with what it actually is: one LOYO fold, validation split of
       15% of ~24 training records.

Figure 5.2 (hybrid architecture) is regenerated unchanged in structure — it
already matched dl_models.py layer for layer — with two corrected numbers.

Output goes to outputs/plots/figures_final/ so the interim report's figures stay
byte-identical.

Run with:
  .venv/bin/python src/generate_final_figures.py
"""

import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT_DIR = 'outputs/plots/figures_final'
DPI = 300

# Palette shared with figures_padr.py so the whole report reads as one system.
BLUE, ORANGE, GREEN, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, INK_2, MUTED = '#0b0b0b', '#52514e', '#898781'
GRID, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'
EDGE = '#5b5a55'

# Tints — light enough to carry black body text at 3:1 or better.
T_SOURCE = '#fbe3cf'   # external data
T_DATA = '#d3e4f7'     # data / integration
T_MODEL = '#f7d7c7'    # modelling (the author's component)
T_SERVE = '#cdeee0'    # serving
T_VIEW = '#fdecc4'     # presentation
T_STORE = '#ecebe4'    # file store
T_USER = '#e2e1da'     # end users


def _box(ax, x, y, w, h, text, color=T_DATA, fontsize=10, weight='normal',
         align='center', ink=INK):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.06',
        linewidth=1.0, edgecolor=EDGE, facecolor=color))
    tx = x + w / 2 if align == 'center' else x + 0.18
    ax.text(tx, y + h / 2, text, ha=align, va='center', color=ink,
            fontsize=fontsize, fontweight=weight, linespacing=1.45)


def _arrow(ax, x1, y1, x2, y2, lw=1.4, color=EDGE, style='-|>', ls='-'):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
        color=color, linewidth=lw, linestyle=ls, shrinkA=0, shrinkB=0))


def _canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, ylim)
    ax.axis('off')
    fig.patch.set_facecolor(SURFACE)
    # Let the drawing fill the figure. Without this the default axes margins
    # leave a wide empty band under every diagram, which Word then scales up.
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    return fig, ax


def _save(fig, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    # No suptitle on any figure: Word supplies the numbered caption, and the
    # interim figures double-captioned because they baked the title into the PNG.
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)
    print(f'  ✓ {path}')
    return path


# ---------------------------------------------------------------------------
# Figure 4.1 — Top-level architecture: FOUR modules (section 4.5)
# ---------------------------------------------------------------------------

def figure_4_1_system_architecture():
    fig, ax = _canvas(14, 9.6, 14, 10.6)

    sources = [
        ('DCS season\nyield reports', 0.30, 2.35),
        ('NASA POWER\nweather API', 3.00, 2.35),
        ('Google Earth Engine\n(MODIS, Sentinel-2,\nCHIRPS, MODIS LST)', 5.70, 2.90),
        ('SoilGrids\nREST API', 9.05, 2.20),
        ('FAOSTAT\n(reference only)', 11.50, 2.20),
    ]
    for text, x, w in sources:
        _box(ax, x, 9.10, w, 1.20, text, T_SOURCE, 8.5)

    _box(ax, 0.30, 6.75, 6.55, 1.75,
         'MODULE 1 — Data acquisition and integration\n'
         'season window · grain reconciliation · 32 predictors\n'
         'writes data/processed/ and stops',
         T_DATA, 9.5, 'bold')
    _box(ax, 7.15, 6.75, 6.55, 1.75,
         'MODULE 2 — Modelling and evaluation\n'
         '9 base learners + 3 stack combiners · LOYO-CV\n'
         'conformal intervals · SHAP · ablation',
         T_MODEL, 9.5, 'bold')

    _box(ax, 1.60, 4.95, 10.80, 1.05,
         'FILE INTERFACE  —  data/processed/ · outputs/models/ · outputs/results/ · outputs/plots/\n'
         'no database: every hand-off between modules is a file on disk',
         T_STORE, 9.5, 'bold')

    _box(ax, 0.30, 2.85, 6.55, 1.55,
         'MODULE 3 — Serving\n'
         'Flask REST API · loads artefacts at start-up · never trains\n'
         '/predict · /context · /models/compare · /feature-importance',
         T_SERVE, 9.5, 'bold')
    _box(ax, 7.15, 2.85, 6.55, 1.55,
         'MODULE 4 — Presentation\n'
         'Next.js dashboard · Leaflet choropleth · SHAP panels\n'
         'consumes HTTP only, holds no model logic',
         T_VIEW, 9.5, 'bold')

    users = [
        ('DCS statistical\nofficers', 0.30, 3.15),
        ('DoA / Ministry\npolicy analysts', 3.75, 3.15),
        ('District agricultural\nofficers', 7.20, 3.15),
        ('Researchers\nand students', 10.65, 3.05),
    ]
    for text, x, w in users:
        _box(ax, x, 0.55, w, 1.15, text, T_USER, 8.5)

    for _, x, w in sources:
        _arrow(ax, x + w / 2, 9.10, 3.55, 8.50, lw=0.9, color=MUTED)
    _arrow(ax, 6.85, 7.62, 7.15, 7.62, lw=1.8)          # M1 → M2
    _arrow(ax, 3.55, 6.75, 3.55, 6.00, lw=1.4)          # M1 → store
    _arrow(ax, 10.45, 6.75, 10.45, 6.00, lw=1.4)        # M2 → store
    _arrow(ax, 3.55, 4.95, 3.55, 4.40, lw=1.4)          # store → M3
    _arrow(ax, 6.85, 3.62, 7.15, 3.62, lw=1.8)          # M3 → M4 (HTTP)
    ax.text(7.00, 4.52, 'HTTP', ha='center', fontsize=8, color=INK_2,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.15', fc=SURFACE, ec='none'))
    for _, x, w in users:
        _arrow(ax, 10.45, 2.85, x + w / 2, 1.70, lw=0.9, color=MUTED)

    handles = [
        Rectangle((0, 0), 1, 1, fc=T_SOURCE, ec=EDGE, label='External data'),
        Rectangle((0, 0), 1, 1, fc=T_DATA, ec=EDGE, label='Integration'),
        Rectangle((0, 0), 1, 1, fc=T_MODEL, ec=EDGE, label='Modelling'),
        Rectangle((0, 0), 1, 1, fc=T_SERVE, ec=EDGE, label='Serving'),
        Rectangle((0, 0), 1, 1, fc=T_VIEW, ec=EDGE, label='Presentation'),
        Rectangle((0, 0), 1, 1, fc=T_USER, ec=EDGE, label='End users'),
    ]
    ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.055),
              ncol=6, frameon=False, fontsize=8.5, labelcolor=INK_2)
    fig.text(0.5, -0.055,
             'Module 2 and Module 3 are the author\'s contribution; Module 1 and Module 4 '
             'were built by other group members.',
             fontsize=8.5, color=INK_2, style='italic', ha='center')

    return _save(fig, 'figure_4_1_system_architecture.png')


# ---------------------------------------------------------------------------
# Figure 4.2 — the NINE stages of section 4.4
# ---------------------------------------------------------------------------

def figure_4_2_pipeline_stages():
    fig, ax = _canvas(14, 8.4, 14, 9.4)

    # (title, detail, fill) in the order section 4.4 describes them.
    stages = [
        ('Stage 1 — Load and reconcile',
         'each source on its own grain →\ndistrict-season-year key', T_DATA),
        ('Stage 2 — Preprocess',
         'range validation · district-median\nimputation · categorical encoding', T_DATA),
        ('Stage 3 — Engineer features',
         '32 predictors in five groups,\nincluding 3 interaction terms', T_DATA),
        ('Stage 4 — Exploratory analysis',
         'distribution, correlation and\nseasonal plots; no model artefact', T_DATA),
        ('Stage 5 — Train classical models',
         'Random Forest · XGBoost · SVR\nnested search under LOYO-CV', T_MODEL),
        ('Stage 6 — Symbolic and physics-residual',
         'GP equation over top 5 predictors;\nmechanistic backbone + RF residual', T_MODEL),
        ('Stage 7 — Train deep models',
         'LSTM · BiLSTM · 1D-CNN ·\nhybrid CNN-LSTM, early stopping', T_MODEL),
        ('Stage 8 — Combine, calibrate, explain',
         'stacking · split-conformal quantiles\nSHAP · six-configuration ablation', T_SERVE),
        ('Stage 9 — Compare and persist',
         'ranking · paired significance tests\nartefacts written for serving', T_SERVE),
    ]

    cols, box_w, box_h = 3, 4.05, 1.85
    gap_x, gap_y = 0.55, 0.62
    x0, y_top = 0.55, 7.05

    centres = []
    for i, (title, detail, fill) in enumerate(stages):
        r, c = divmod(i, cols)
        x = x0 + c * (box_w + gap_x)
        y = y_top - r * (box_h + gap_y)
        _box(ax, x, y, box_w, box_h, '', fill, 9)
        ax.text(x + box_w / 2, y + box_h - 0.48, title, ha='center', va='center',
                fontsize=9.5, fontweight='bold', color=INK)
        ax.text(x + box_w / 2, y + 0.62, detail, ha='center', va='center',
                fontsize=8.3, color=INK_2, linespacing=1.5)
        centres.append((x, y, x + box_w / 2, y + box_h / 2))

    # Sequential arrows: along each row, then wrap to the row below.
    for i in range(len(stages) - 1):
        r, c = divmod(i, cols)
        xa, ya, cxa, cya = centres[i]
        xb, yb, cxb, cyb = centres[i + 1]
        if c < cols - 1:
            _arrow(ax, xa + box_w, cya, xb, cyb, lw=1.6)
        else:
            # wrap: down the right edge, back across, into the next row's left box
            ax.plot([cxa, cxa], [ya, ya - gap_y / 2], color=EDGE, lw=1.6)
            ax.plot([cxa, cxb], [ya - gap_y / 2, ya - gap_y / 2], color=EDGE, lw=1.6)
            _arrow(ax, cxb, ya - gap_y / 2, cxb, yb + box_h, lw=1.6)

    ax.text(0.55, 1.02,
            'Every stage writes its output to disk, so the pipeline is restartable at any '
            'stage and every intermediate is inspectable.',
            fontsize=9, color=INK_2, style='italic')
    ax.text(0.55, 0.52,
            'Stages 5 to 9 are the author\'s contribution. Stage 1 falls back to a '
            'calibrated synthetic generator only for architecture validation; the '
            'real-data run does not use it.',
            fontsize=8.5, color=INK_2)

    handles = [
        Rectangle((0, 0), 1, 1, fc=T_DATA, ec=EDGE, label='Data preparation (1–4)'),
        Rectangle((0, 0), 1, 1, fc=T_MODEL, ec=EDGE, label='Model training (5–7)'),
        Rectangle((0, 0), 1, 1, fc=T_SERVE, ec=EDGE, label='Combine and persist (8–9)'),
    ]
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.035),
              ncol=3, frameon=False, fontsize=8.5, labelcolor=INK_2)

    return _save(fig, 'figure_4_2_pipeline_stages.png')


# ---------------------------------------------------------------------------
# Figure 5.1 — data flow, with file interfaces and all nine base learners
# ---------------------------------------------------------------------------

def figure_5_1_data_flow():
    fig, ax = _canvas(15, 9.8, 15, 10.4)

    lanes = [
        ('External\nsources', 9.30),
        ('Integration', 7.30),
        ('Analysis\ndataset', 5.75),
        ('Modelling\nand serving', 3.30),
        ('End users', 0.95),
    ]
    for label, y in lanes:
        ax.text(0.08, y, label, rotation=90, fontsize=8.5, color=MUTED,
                va='center', ha='center', fontweight='bold')

    sources = [
        ('Google Earth Engine\nMODIS · Sentinel-2\nCHIRPS · MODIS LST', 0.70, 3.05),
        ('NASA POWER\nREST API\n(daily weather)', 4.05, 2.55),
        ('DCS season reports\n(district yield,\nextent)', 6.90, 2.75),
        ('SoilGrids\nREST API\n(static soil)', 9.95, 2.40),
        ('FAOSTAT\n(national\nreference)', 12.60, 2.10),
    ]
    for text, x, w in sources:
        _box(ax, x, 8.60, w, 1.45, text, T_SOURCE, 8.3)

    _box(ax, 1.30, 6.75, 12.35, 1.15,
         'INTEGRATION  —  pandas · requests · earthengine-api\n'
         'cloud masking · season window · grain reconciliation · range and unit QC',
         T_DATA, 9.5, 'bold')

    _box(ax, 2.60, 5.20, 9.75, 1.05,
         'data/processed/integrated_dataset.csv  ·  features_tabular.csv\n'
         'one row per district-season-year  ·  32 predictors  ·  yield in MT/ha',
         T_STORE, 9.3, 'bold')

    _box(ax, 0.55, 2.35, 7.35, 2.35,
         'MODELLING AND EVALUATION\n\n'
         'Classical    Random Forest · XGBoost · SVR\n'
         'Symbolic     genetic-programming equation\n'
         'Mechanistic  physics-residual (PADR backbone + RF)\n'
         'Deep         LSTM · BiLSTM · 1D-CNN · hybrid CNN-LSTM\n'
         'Combined     convex stack · inverse-RMSE · mean\n\n'
         'LOYO-CV · nested search · conformal · SHAP · Wilcoxon',
         T_MODEL, 8.6, 'bold', align='left')

    _box(ax, 8.30, 3.35, 3.05, 1.35,
         'Flask REST API\n/predict · /context\n/models/compare\n/feature-importance',
         T_SERVE, 8.6, 'bold')
    _box(ax, 8.30, 2.35, 3.05, 0.75,
         'outputs/results/\noof_*.json · conformal.json',
         T_STORE, 8.3)
    _box(ax, 11.75, 2.85, 2.80, 1.85,
         'Next.js dashboard\n\nLeaflet choropleth\nprediction form\nSHAP panels\nadmin comparison',
         T_VIEW, 8.6, 'bold')

    _box(ax, 3.90, 0.45, 7.20, 0.95,
         'DCS statistical officers · policy analysts · district officers · researchers',
         T_USER, 9.3, 'bold')

    for _, x, w in sources:
        _arrow(ax, x + w / 2, 8.60, x + w / 2, 7.90, lw=1.0, color=MUTED)
    _arrow(ax, 7.45, 6.75, 7.45, 6.25, lw=1.8)
    _arrow(ax, 4.20, 5.20, 4.20, 4.70, lw=1.8)
    _arrow(ax, 7.90, 4.00, 8.30, 4.00, lw=1.6)
    _arrow(ax, 6.40, 2.72, 8.30, 2.72, lw=1.2, color=MUTED)
    _arrow(ax, 9.83, 3.10, 9.83, 3.35, lw=1.2, color=MUTED)
    _arrow(ax, 11.35, 4.00, 11.75, 4.00, lw=1.6)
    _arrow(ax, 13.15, 2.85, 11.10, 1.40, lw=1.4)

    fig.text(0.055, -0.015,
             'Every arrow crossing a lane boundary is a file written by one component and '
             'read by the next; there are no in-memory hand-offs between major stages.',
             fontsize=8.8, color=INK_2, style='italic')
    fig.text(0.055, -0.048,
             'The serving tier loads persisted artefacts at start-up and never trains, so a '
             'retraining run cannot corrupt a running service.',
             fontsize=8.5, color=INK_2)

    return _save(fig, 'figure_5_1_data_flow.png')


# ---------------------------------------------------------------------------
# Figure 5.2 — hybrid CNN-LSTM. Structure verified against dl_models.py.
# ---------------------------------------------------------------------------

def figure_5_2_cnn_lstm_hybrid():
    fig, ax = _canvas(15, 11, 15, 12.2)

    _box(ax, 0.80, 10.75, 3.90, 1.05,
         'Satellite input  (11, 1)\nseason_mean_ndvi … season_mean_lst_night\n'
         '11 vegetation and thermal indices',
         T_SOURCE, 8.6, 'bold')
    _box(ax, 5.45, 10.75, 4.05, 1.05,
         'Weather input  (5, 4)\n5 intra-season steps ×\ntemp, rainfall, humidity, solar',
         T_SOURCE, 8.6, 'bold')
    _box(ax, 10.25, 10.75, 3.95, 1.05,
         'Season indicator  (1,)\nYala = 1, Maha = 0\nscalar, not a sequence',
         T_MODEL, 8.6, 'bold')

    ax.text(2.75, 10.35, 'CNN branch', ha='center', fontsize=10,
            fontweight='bold', color=BLUE)
    ax.text(7.48, 10.35, 'LSTM branch', ha='center', fontsize=10,
            fontweight='bold', color=GREEN)
    ax.text(12.22, 10.35, 'direct injection', ha='center', fontsize=10,
            fontweight='bold', color=ORANGE)

    cnn = [
        ('Conv1D(32, k=3, ReLU, same)', '128 params  →  (11, 32)'),
        ('BatchNormalization', '128 params (64 non-trainable)'),
        ('Conv1D(64, k=3, ReLU, same)', '6,208 params  →  (11, 64)'),
        ('GlobalAveragePooling1D', '0 params  →  (64,)'),
    ]
    lstm = [
        ('LSTM(64, return_sequences=True)', '17,664 params  →  (5, 64)'),
        ('Dropout(0.2)', '0 params'),
        ('LSTM(32)', '12,416 params  →  (32,)'),
        ('Dropout(0.2)', '0 params  →  (32,)'),
    ]

    y, h, gap = 9.05, 0.98, 0.30
    for i, ((c_name, c_shape), (l_name, l_shape)) in enumerate(zip(cnn, lstm)):
        yy = y - i * (h + gap)
        _box(ax, 0.80, yy, 3.90, h, '', T_DATA, 8.5)
        ax.text(2.75, yy + h * 0.63, c_name, ha='center', fontsize=8.6, color=INK)
        ax.text(2.75, yy + h * 0.26, c_shape, ha='center', fontsize=7.8, color=INK_2)
        _box(ax, 5.45, yy, 4.05, h, '', T_SERVE, 8.5)
        ax.text(7.48, yy + h * 0.63, l_name, ha='center', fontsize=8.6, color=INK)
        ax.text(7.48, yy + h * 0.26, l_shape, ha='center', fontsize=7.8, color=INK_2)
        if i:
            _arrow(ax, 2.75, yy + h + gap, 2.75, yy + h, lw=1.2)
            _arrow(ax, 7.48, yy + h + gap, 7.48, yy + h, lw=1.2)
    _arrow(ax, 2.75, 10.75, 2.75, 10.03, lw=1.4)
    _arrow(ax, 7.48, 10.75, 7.48, 10.03, lw=1.4)

    _box(ax, 10.25, 6.24, 3.95, 0.98, 'identity  (no transformation)', '#faf3e6', 8.6)
    _arrow(ax, 12.22, 10.75, 12.22, 7.22, lw=1.4, color=ORANGE)

    _box(ax, 0.80, 4.10, 13.40, 0.85,
         'Concatenate  [ CNN 64  |  LSTM 32  |  season 1 ]  →  (97,)',
         T_MODEL, 10.5, 'bold')
    for x, colour in ((2.75, EDGE), (7.48, EDGE), (12.22, ORANGE)):
        _arrow(ax, x, 5.21, x, 4.95, lw=1.4, color=colour)

    head = [
        ('Dense(64, ReLU)', '6,272 params'),
        ('Dropout(0.3)', '0 params'),
        ('Dense(32, ReLU)', '2,080 params'),
    ]
    for i, (name, shape) in enumerate(head):
        yy = 3.05 - i * 0.90
        _box(ax, 4.30, yy, 6.40, 0.66, '', T_VIEW, 9)
        ax.text(7.50, yy + 0.42, name, ha='center', fontsize=8.8, color=INK)
        ax.text(7.50, yy + 0.16, shape, ha='center', fontsize=7.8, color=INK_2)
        if i:
            _arrow(ax, 7.50, yy + 0.90, 7.50, yy + 0.66, lw=1.2)
    _arrow(ax, 7.50, 4.10, 7.50, 3.71, lw=1.4)

    _box(ax, 4.30, 0.30, 6.40, 0.70,
         'Dense(1, linear)  →  predicted yield (MT/ha)\n33 params',
         '#f6dfc9', 9.5, 'bold')
    _arrow(ax, 7.50, 1.25, 7.50, 1.00, lw=1.4)

    fig.text(0.055, -0.012,
             'Season injection after feature extraction: because neither branch sees the '
             'season variable, both learn extractors valid for either season and train on\n'
             'the whole dataset, while only the dense head — 8,385 of 44,929 parameters — '
             'learns season-specific baselines.',
             fontsize=8.6, color=INK_2, linespacing=1.6)
    fig.text(0.055, -0.048,
             'The collected panel covers Yala only, so this design could be exercised on '
             'the synthetic run but not evaluated on real data (section 7.6).',
             fontsize=8.4, color=ORANGE, style='italic')

    ax.text(14.20, 2.70,
            'Total parameters   44,929\n'
            'Trainable          44,865\n'
            'Non-trainable          64\n'
            '(BatchNorm moving statistics)',
            ha='right', va='top', fontsize=8.2, color=INK_2, family='monospace',
            bbox=dict(boxstyle='round,pad=0.45', fc=SURFACE, ec=BASELINE, lw=0.9))

    return _save(fig, 'figure_5_2_cnn_lstm_hybrid.png')


# ---------------------------------------------------------------------------
# Figure 5.3 — logical artefact schema of section 5.9
# ---------------------------------------------------------------------------

def figure_5_3_artefact_schema():
    fig, ax = _canvas(14.5, 9.2, 14.5, 9.8)

    def table(x, y, w, title, rows, fill, key_note=None):
        head_h, row_h = 0.62, 0.42
        h = head_h + row_h * len(rows)
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.05',
            linewidth=1.0, edgecolor=EDGE, facecolor=SURFACE))
        ax.add_patch(Rectangle((x, y + h - head_h), w, head_h,
                               facecolor=fill, edgecolor=EDGE, linewidth=1.0))
        ax.text(x + w / 2, y + h - head_h / 2, title, ha='center', va='center',
                fontsize=9.5, fontweight='bold', color=INK, family='monospace')
        for i, (tag, field) in enumerate(rows):
            yy = y + h - head_h - row_h * (i + 0.5)
            ax.plot([x, x + w], [yy + row_h / 2, yy + row_h / 2],
                    color=GRID, lw=0.7, zorder=1)
            ax.text(x + 0.16, yy, tag, ha='left', va='center', fontsize=7.6,
                    color=ORANGE if tag == 'KEY' else MUTED, family='monospace',
                    fontweight='bold' if tag == 'KEY' else 'normal')
            ax.text(x + 0.92, yy, field, ha='left', va='center', fontsize=8.2,
                    color=INK, family='monospace')
        if key_note:
            ax.text(x + w / 2, y - 0.26, key_note, ha='center', fontsize=7.8,
                    color=INK_2, style='italic',
                    bbox=dict(boxstyle='round,pad=0.18', fc=SURFACE, ec='none'))
        return x, y, w, h

    ax.text(0.25, 9.45, 'Keyed on district-season-year', fontsize=9.5,
            fontweight='bold', color=INK)
    a = table(0.25, 5.15, 4.35, 'features_tabular.csv', [
        ('KEY', 'District'),
        ('KEY', 'Season'),
        ('KEY', 'Year'),
        ('', '32 predictor columns'),
        ('', 'avg_yield_mt_ha  (target)'),
    ], T_DATA, '28 rows on the collected panel')

    b = table(5.10, 5.15, 4.35, 'oof_<model>.json', [
        ('KEY', 'District'),
        ('KEY', 'Season'),
        ('KEY', 'Year'),
        ('KEY', 'model'),
        ('', 'y_true, y_pred, fold_year'),
    ], T_MODEL, 'same key plus a model dimension')

    ax.text(9.95, 9.45, 'Keyed on model alone', fontsize=9.5,
            fontweight='bold', color=INK)
    c = table(9.95, 7.05, 4.30, 'model_comparison.csv', [
        ('KEY', 'Model'),
        ('', 'RMSE, MAE, R2, MAPE'),
        ('', 'Train_Time_s, Parameters'),
    ], T_SERVE)
    d = table(9.95, 4.85, 4.30, 'conformal.json', [
        ('KEY', 'model'),
        ('', 'alpha, half_width'),
        ('', 'n_calibration'),
    ], T_SERVE)
    e = table(9.95, 2.65, 4.30, 'feature_importance.json', [
        ('KEY', 'model'),
        ('', 'predictor, mean_abs_shap'),
        ('', 'rank'),
    ], T_SERVE)

    table(2.65, 1.55, 4.35, 'models/<model>.pkl | .keras', [
        ('KEY', 'model'),
        ('', 'fitted estimator'),
        ('', 'refit on all records after CV'),
    ], T_VIEW, 'loaded by the serving tier at start-up')

    _arrow(ax, 4.60, 6.35, 5.10, 6.35, lw=1.4)
    ax.text(4.85, 6.80, 'per fold', ha='center', fontsize=7.6, color=INK_2,
            bbox=dict(boxstyle='round,pad=0.18', fc=SURFACE, ec='none'))
    for y in (7.60, 5.90, 3.70):
        _arrow(ax, 9.45, 6.35, 9.95, y, lw=1.1, color=MUTED)
    ax.text(9.68, 6.35, 'aggregated\nover folds', ha='center', va='center',
            fontsize=7.4, color=INK_2, linespacing=1.4,
            bbox=dict(boxstyle='round,pad=0.2', fc=SURFACE, ec='none'))
    _arrow(ax, 2.42, 5.15, 3.60, 3.43, lw=1.1, color=MUTED)

    fig.text(0.018, -0.015,
             'This is a logical schema over files, not a relational database. The store is '
             'the filesystem: each artefact is a CSV, JSON or pickle written by the\n'
             'modelling module and read by the serving module. api.py still carries a '
             '"TODO: implement PostgreSQL storage" marker — no database is deployed.',
             fontsize=8.5, color=INK_2, linespacing=1.6)

    return _save(fig, 'figure_5_3_artefact_schema.png')


# ---------------------------------------------------------------------------
# Figure 6.1 — the hybrid's learning curve, honestly labelled
# ---------------------------------------------------------------------------

def figure_6_1_hybrid_learning_curve(history_path=None):
    """Restyle the hybrid learning curve and state what the curve actually is.

    The interim/synthetic version was a bare seaborn default that clashed with
    every chapter 7 figure, carried no early-stop marker, and gave no hint that
    the validation trace comes from one LOYO fold with a 15% split of roughly
    24 training records.
    """
    history_path = history_path or 'outputs/results_real/dl_history_hybrid_cnn_lstm.json'
    if not os.path.exists(history_path):
        print(f'  ⚠ {history_path} not found — skipping Figure 6.1 '
              f'(re-run the DL stage to persist per-fold history)')
        return None

    hist = json.load(open(history_path))
    train, val = hist['loss'], hist.get('val_loss') or []

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(BASELINE)
    ax.tick_params(colors=MUTED, labelsize=9)

    epochs = range(1, len(train) + 1)
    ax.plot(epochs, train, color=BLUE, lw=2, label='training loss', zorder=3)
    if val:
        ax.plot(range(1, len(val) + 1), val, color=ORANGE, lw=2,
                label='validation loss (15% of ~24 records)', zorder=3)
        best = int(min(range(len(val)), key=lambda i: val[i]))
        stopped_early = best + 1 < len(val)
        ax.axvline(best + 1, color=MUTED, ls='--', lw=1.2, zorder=2)
        if stopped_early:
            note = (f'best validation epoch {best + 1} of {len(val)}\n'
                    f'early stopping restored these weights')
            colour = INK_2
        else:
            # The real-data run inherited SYNTHETIC_MODE_DL_EPOCHS = 50, so the
            # patience-20 early stop never fired: the cap bound first, with
            # validation loss still descending. Say so on the figure.
            note = (f'no early stop — the {len(val)}-epoch cap bound first,\n'
                    f'with validation loss still falling')
            colour = ORANGE
        ax.annotate(note,
                    xy=(best + 1, val[best]), xytext=(best + 1, max(val) * 0.74),
                    fontsize=8.4, color=colour, ha='right',
                    arrowprops=dict(arrowstyle='->', color=MUTED, lw=1.0))
        ax.annotate('', xy=(len(train), train[-1]), xytext=(len(train), val[-1]),
                    arrowprops=dict(arrowstyle='<->', color=INK_2, lw=1.2))
        ax.text(len(train) - 0.6, (train[-1] + val[-1]) / 2,
                f'generalisation gap\n{val[-1] / max(train[-1], 1e-9):.1f}×',
                fontsize=8.4, color=INK_2, ha='right', va='center')

    ax.set_title('Hybrid CNN-LSTM — loss on the final leave-one-year-out fold',
                 color=INK, fontsize=11, loc='left', pad=10)
    ax.set_xlabel('epoch', color=INK_2, fontsize=9)
    ax.set_ylabel('loss (MSE, MT/ha²)', color=INK_2, fontsize=9)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2, loc='upper right')

    fig.text(0.005, -0.05,
             'One fold, not an average: the validation trace is a 15% split of roughly 24 '
             'training records, so it is a weak estimate. It is shown because the '
             'persistent\ngap is the point — the network has more capacity than 28 records '
             'can constrain. Section 7.4 gives the leave-one-year-out outcome.',
             fontsize=8.3, color=INK_2, linespacing=1.6)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, 'figure_6_1_hybrid_learning_curve.png')
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)
    print(f'  ✓ {path}')
    return path


def main():
    print('Generating corrected final-report schematics…')
    figure_4_1_system_architecture()
    figure_4_2_pipeline_stages()
    figure_5_1_data_flow()
    figure_5_2_cnn_lstm_hybrid()
    figure_5_3_artefact_schema()
    figure_6_1_hybrid_learning_curve()
    print(f'Done → {OUT_DIR}/')


if __name__ == '__main__':
    main()

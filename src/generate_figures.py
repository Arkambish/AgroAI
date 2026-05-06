"""Generate the 5 figures referenced in the Agro AI interim report.

Outputs (300 DPI PNGs) go to outputs/plots/figures/:
  - figure_4_1_system_architecture.png
  - figure_4_2_pipeline_stages.png
  - figure_5_1_data_flow.png
  - figure_5_2_cnn_lstm_hybrid.png
  - figure_5_3_database_schema.png

Run with:
  .venv/bin/python src/generate_figures.py
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.patches import ConnectionPatch

OUT_DIR = 'outputs/plots/figures'
os.makedirs(OUT_DIR, exist_ok=True)
DPI = 300

# Color palette
DATA_COLOR = '#FFB347'      # orange — data
PROCESS_COLOR = '#87CEEB'   # sky blue — processing
ML_COLOR = '#90EE90'        # light green — ML
DL_COLOR = '#DDA0DD'        # plum — DL
NOVEL_COLOR = '#FF6B6B'     # coral — novelty highlight
OUTPUT_COLOR = '#FFD700'    # gold — outputs
USER_COLOR = '#B0C4DE'      # light steel blue — users
EDGE_COLOR = '#444444'


def _box(ax, x, y, w, h, text, color=PROCESS_COLOR, fontsize=10, fontweight='normal'):
    """Draw a rounded rectangle box with centred text."""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.03,rounding_size=0.05",
                         linewidth=1.2, edgecolor=EDGE_COLOR,
                         facecolor=color, alpha=0.9)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fontsize, fontweight=fontweight, wrap=True)


def _arrow(ax, x1, y1, x2, y2, style='->', color=EDGE_COLOR, lw=1.5,
           connectionstyle='arc3,rad=0', linestyle='-'):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, mutation_scale=15,
                            color=color, linewidth=lw,
                            connectionstyle=connectionstyle, linestyle=linestyle)
    ax.add_patch(arrow)


# ---------------------------------------------------------------------------
# Figure 4.1 — High-Level System Architecture
# ---------------------------------------------------------------------------

def figure_4_1_system_architecture():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('Figure 4.1 — High-Level System Architecture',
                 fontsize=14, fontweight='bold', pad=20)

    # External data sources (top)
    sources = [
        ('DCS Yield\nReports', 0.5),
        ('NASA POWER\nWeather API', 3.0),
        ('Google Earth\nEngine\n(MODIS, S2,\nCHIRPS)', 5.5),
        ('SoilGrids\nAPI', 8.5),
        ('FAOSTAT\n(reference)', 11.0),
    ]
    for text, x in sources:
        _box(ax, x, 8.5, 2.2, 1.2, text, color=DATA_COLOR, fontsize=9)

    # Module 1: Data Pipeline (Sharuja)
    _box(ax, 0.5, 5.5, 4.2, 2.0,
         'MODULE 1\nData Pipeline\n(Sharuja B.)\n\nIngestion · Cleaning ·\nFeature Engineering',
         color=PROCESS_COLOR, fontsize=10, fontweight='bold')

    # Module 2: ML/DL Engine (Arkam)
    _box(ax, 5.0, 5.5, 4.2, 2.0,
         'MODULE 2\nML/DL Prediction Engine\n(Arkam B.H.M.)\n\n7 Models · LOYO-CV ·\nSHAP · Flask API',
         color=NOVEL_COLOR, fontsize=10, fontweight='bold')

    # Module 3: Visualization (Shathurya)
    _box(ax, 9.5, 5.5, 4.2, 2.0,
         'MODULE 3\nVisualization & Dashboard\n(Shathurya P.)\n\nReact/Next.js · Leaflet ·\nSHAP plots',
         color=DL_COLOR, fontsize=10, fontweight='bold')

    # Storage layer
    _box(ax, 2.5, 3.0, 9.0, 1.4,
         'PostgreSQL Database  +  data/processed/  +  outputs/models/',
         color='#E8E8E8', fontsize=10, fontweight='bold')

    # End users
    _box(ax, 1.0, 0.5, 3.0, 1.4, 'DCS &\nDept. of Agri.\nofficers', color=USER_COLOR, fontsize=9)
    _box(ax, 5.0, 0.5, 3.0, 1.4, 'District\nagricultural\nofficers', color=USER_COLOR, fontsize=9)
    _box(ax, 9.0, 0.5, 4.0, 1.4, 'Agri. researchers\n& policy planners', color=USER_COLOR, fontsize=9)

    # Arrows
    # Sources -> Module 1
    for _, x in sources:
        _arrow(ax, x + 1.1, 8.5, 2.6, 7.5, lw=1)
    # Module 1 -> Module 2
    _arrow(ax, 4.7, 6.5, 5.0, 6.5, lw=2)
    # Module 2 -> Module 3
    _arrow(ax, 9.2, 6.5, 9.5, 6.5, lw=2)
    # Modules -> storage
    for x in [2.6, 7.1, 11.6]:
        _arrow(ax, x, 5.5, x, 4.4, lw=1.5)
    # Storage -> users (via Module 3)
    _arrow(ax, 7.0, 3.0, 7.0, 1.9, lw=1.5)

    # Legend
    legend_elements = [
        Rectangle((0, 0), 1, 1, facecolor=DATA_COLOR, edgecolor=EDGE_COLOR, label='External data'),
        Rectangle((0, 0), 1, 1, facecolor=PROCESS_COLOR, edgecolor=EDGE_COLOR, label='Data pipeline'),
        Rectangle((0, 0), 1, 1, facecolor=NOVEL_COLOR, edgecolor=EDGE_COLOR, label='ML/DL engine'),
        Rectangle((0, 0), 1, 1, facecolor=DL_COLOR, edgecolor=EDGE_COLOR, label='Visualization'),
        Rectangle((0, 0), 1, 1, facecolor=USER_COLOR, edgecolor=EDGE_COLOR, label='End users'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.02),
              ncol=5, frameon=False, fontsize=9)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'figure_4_1_system_architecture.png')
    fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✓ {out}')


# ---------------------------------------------------------------------------
# Figure 4.2 — System Pipeline Stages
# ---------------------------------------------------------------------------

def figure_4_2_pipeline_stages():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('Figure 4.2 — System Pipeline Stages',
                 fontsize=14, fontweight='bold', pad=20)

    stages = [
        ('Stage 1\nData Acquisition',
         'GEE Python API\nNASA POWER REST\nDCS PDF extraction', DATA_COLOR),
        ('Stage 2\nPreprocessing',
         'Cleaning, missing-value\nimputation, temporal\nalignment to seasons', PROCESS_COLOR),
        ('Stage 3\nFeature Engineering',
         'NDVI/EVI/NDWI\nGDD, SPI, lagged yield\ninteraction features', PROCESS_COLOR),
        ('Stage 4\nModel Training\n& Evaluation',
         '7 models, LOYO-CV\nGridSearchCV tuning\nWilcoxon tests', NOVEL_COLOR),
        ('Stage 5\nVisualization\n& Reporting',
         'Spatial yield maps\nSHAP explainability\nDashboard delivery', DL_COLOR),
    ]

    n = len(stages)
    box_w = 2.2
    gap = 0.55
    total_w = n * box_w + (n - 1) * gap
    start_x = (14 - total_w) / 2

    # Draw boxes first
    box_xs = []
    for i, (title, desc, color) in enumerate(stages):
        x = start_x + i * (box_w + gap)
        box_xs.append(x)
        # Title box
        _box(ax, x, 3.8, box_w, 1.5, title, color=color, fontsize=10, fontweight='bold')
        # Description box
        _box(ax, x, 1.8, box_w, 1.8, desc, color='#F5F5F5', fontsize=9)

    # Draw arrows in the horizontal gaps between adjacent boxes
    for i in range(n - 1):
        x_start = box_xs[i] + box_w
        x_end = box_xs[i + 1]
        ax.annotate('', xy=(x_end, 4.55), xytext=(x_start, 4.55),
                    arrowprops=dict(arrowstyle='-|>', lw=2.5, color=EDGE_COLOR,
                                    mutation_scale=22))

    # Annotation: Arkam's responsibility is Stage 4 + parts of 5
    ax.annotate('Arkam B.H.M.\n(Stage 4 + serving API)',
                xy=(start_x + 3 * (box_w + gap) + box_w / 2, 5.3),
                xytext=(start_x + 3 * (box_w + gap) + box_w / 2, 6.4),
                ha='center', fontsize=10, fontweight='bold', color='#B22222',
                arrowprops=dict(arrowstyle='->', color='#B22222', lw=1.5))

    ax.text(7, 0.8,
            'Multi-source agricultural data → trained yield-prediction models → '
            'decision-support dashboard',
            ha='center', fontsize=10, style='italic', color='#444')

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'figure_4_2_pipeline_stages.png')
    fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✓ {out}')


# ---------------------------------------------------------------------------
# Figure 5.1 — Data Flow Diagram
# ---------------------------------------------------------------------------

def figure_5_1_data_flow():
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('Figure 5.1 — Data Flow Diagram',
                 fontsize=14, fontweight='bold', pad=20)

    # Layer 1: External data sources
    sources = [
        ('Google Earth Engine\n(MODIS, Sentinel-2,\nCHIRPS, MODIS LST)', 0.3, 8.0, 3.2, 1.6),
        ('NASA POWER\nREST API\n(weather)', 4.0, 8.0, 2.6, 1.6),
        ('DCS Survey\nPDF Reports\n(yield)', 7.1, 8.0, 2.6, 1.6),
        ('SoilGrids\nREST API\n(soil)', 10.2, 8.0, 2.6, 1.6),
        ('FAOSTAT\nCSV download', 13.3, 8.0, 1.5, 1.6),
    ]
    for text, x, y, w, h in sources:
        _box(ax, x, y, w, h, text, color=DATA_COLOR, fontsize=9)

    # Layer 2: ETL pipeline
    _box(ax, 1.5, 6.0, 12.0, 1.2,
         'ETL PIPELINE  —  Python (pandas, requests, earthengine-api)\n'
         'Cloud masking · temporal alignment · seasonal aggregation · QC checks',
         color=PROCESS_COLOR, fontsize=10, fontweight='bold')

    # Layer 3: Database
    _box(ax, 3.0, 4.2, 9.0, 1.0,
         'PostgreSQL Database  (district, year, season, 32 features, yield)',
         color='#E8E8E8', fontsize=10, fontweight='bold')

    # Layer 4: ML/DL engine (Arkam)
    _box(ax, 0.5, 2.0, 6.5, 1.6,
         'ML/DL Prediction Engine\n'
         'RF · XGBoost · SVR · LSTM · BiLSTM · CNN · Hybrid CNN-LSTM\n'
         'LOYO-CV · GridSearchCV · SHAP · Wilcoxon tests',
         color=NOVEL_COLOR, fontsize=9, fontweight='bold')

    # Layer 4 right: Flask REST API
    _box(ax, 7.5, 2.0, 3.0, 1.6,
         'Flask REST API\n/health · /predict\n/models/compare\n/feature-importance',
         color=ML_COLOR, fontsize=9, fontweight='bold')

    # Layer 4 far right: Frontend
    _box(ax, 11.0, 2.0, 3.5, 1.6,
         'React/Next.js\nDashboard\nLeaflet maps · SHAP plots',
         color=DL_COLOR, fontsize=9, fontweight='bold')

    # Layer 5: End users
    _box(ax, 4.0, 0.2, 7.0, 1.2,
         'End Users  —  DCS · DOA · District officers · Researchers',
         color=USER_COLOR, fontsize=10, fontweight='bold')

    # Arrows: sources -> ETL
    for _, x, y, w, h in sources:
        _arrow(ax, x + w / 2, y, x + w / 2, 7.2, lw=1)

    # ETL -> DB
    _arrow(ax, 7.5, 6.0, 7.5, 5.2, lw=2)
    # DB -> ML
    _arrow(ax, 4.0, 4.2, 4.0, 3.6, lw=2)
    # ML -> API
    _arrow(ax, 7.0, 2.8, 7.5, 2.8, lw=2)
    # API -> Frontend
    _arrow(ax, 10.5, 2.8, 11.0, 2.8, lw=2)
    # Frontend -> Users
    _arrow(ax, 12.7, 2.0, 9.0, 1.4, lw=1.5)
    # Direct ML -> Users (via API+Frontend) decorative
    _arrow(ax, 4.0, 2.0, 6.0, 1.4, lw=1, linestyle='--')

    # Section label brackets
    ax.text(0.05, 8.8, 'External\nSources', rotation=90, fontsize=9, color='#666',
            va='center', fontweight='bold')
    ax.text(0.05, 6.6, 'Sharuja B.', rotation=90, fontsize=9, color='#666',
            va='center', fontweight='bold')
    ax.text(0.05, 4.7, 'Storage', rotation=90, fontsize=9, color='#666',
            va='center', fontweight='bold')
    ax.text(0.05, 2.8, 'Arkam B.H.M.', rotation=90, fontsize=9, color='#666',
            va='center', fontweight='bold')
    ax.text(0.05, 0.8, 'End Users', rotation=90, fontsize=9, color='#666',
            va='center', fontweight='bold')

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'figure_5_1_data_flow.png')
    fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✓ {out}')


# ---------------------------------------------------------------------------
# Figure 5.2 — CNN-LSTM Hybrid Architecture (the novelty figure)
# ---------------------------------------------------------------------------

def figure_5_2_cnn_lstm_hybrid():
    fig, ax = plt.subplots(figsize=(15, 11))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 12)
    ax.axis('off')
    ax.set_title('Figure 5.2 — Hybrid CNN-LSTM Architecture (Arkam\'s novel contribution)',
                 fontsize=14, fontweight='bold', pad=20)

    # ---- Inputs (top) ----
    # Satellite input (left)
    _box(ax, 1.0, 10.0, 3.5, 1.0,
         'Satellite Input\n(11 features, 1)\nNDVI, EVI, NDWI, LST...',
         color=DATA_COLOR, fontsize=9, fontweight='bold')
    # Weather input (middle)
    _box(ax, 5.7, 10.0, 3.6, 1.0,
         'Weather Input\n(5 timesteps, 4 features)\ntemp, rainfall, humidity, solar',
         color=DATA_COLOR, fontsize=9, fontweight='bold')
    # Season input (right)
    _box(ax, 10.5, 10.0, 3.5, 1.0,
         'Season Indicator\n(Yala=1, Maha=0)\nshape: (1,)',
         color=NOVEL_COLOR, fontsize=9, fontweight='bold')

    # ---- CNN branch (left column) ----
    cnn_layers = [
        (8.6, 'Conv1D(32 filters, kernel=3, ReLU, padding=same)'),
        (7.5, 'BatchNormalization'),
        (6.4, 'Conv1D(64 filters, kernel=3, ReLU, padding=same)'),
        (5.3, 'GlobalAveragePooling1D\n→ output (64,)'),
    ]
    for y, text in cnn_layers:
        _box(ax, 0.5, y, 4.5, 0.85, text, color=ML_COLOR, fontsize=9)

    # ---- LSTM branch (middle column) ----
    lstm_layers = [
        (8.6, 'LSTM(64 units, return_sequences=True)'),
        (7.5, 'Dropout(0.2)'),
        (6.4, 'LSTM(32 units, return_sequences=False)'),
        (5.3, 'Dropout(0.2)\n→ output (32,)'),
    ]
    for y, text in lstm_layers:
        _box(ax, 5.3, y, 4.4, 0.85, text, color=DL_COLOR, fontsize=9)

    # Branch labels
    ax.text(2.75, 9.6, 'CNN Branch', ha='center', fontsize=11,
            fontweight='bold', color='#1f7a1f')
    ax.text(7.5, 9.6, 'LSTM Branch', ha='center', fontsize=11,
            fontweight='bold', color='#7a1f7a')
    ax.text(12.25, 9.6, 'Season Indicator\n(direct injection)', ha='center', fontsize=10,
            fontweight='bold', color='#B22222')

    # Season indicator pass-through (just a vertical line down to the merge)
    _box(ax, 11.5, 5.3, 1.5, 0.85, 'identity', color='#FFE4E1', fontsize=9)

    # ---- Merge ----
    merge_y = 4.0
    _box(ax, 1.5, merge_y, 12.0, 0.9,
         'Concatenate ([CNN_out (64), LSTM_out (32), season (1)] → vector of 97)',
         color=NOVEL_COLOR, fontsize=11, fontweight='bold')

    # ---- Dense layers ----
    _box(ax, 4.0, 2.7, 7.0, 0.8, 'Dense(64 units, ReLU)', color=PROCESS_COLOR, fontsize=10)
    _box(ax, 4.0, 1.7, 7.0, 0.8, 'Dropout(0.3)', color=PROCESS_COLOR, fontsize=10)
    _box(ax, 4.0, 0.7, 7.0, 0.8, 'Dense(32 units, ReLU)', color=PROCESS_COLOR, fontsize=10)

    # ---- Output ----
    _box(ax, 5.5, -0.4, 4.0, 0.8,
         'Dense(1, linear) → Predicted Yield (MT/Ha)',
         color=OUTPUT_COLOR, fontsize=11, fontweight='bold')

    # ---- Arrows ----
    # Inputs to first layer of each branch
    _arrow(ax, 2.75, 10.0, 2.75, 9.45, lw=1.5)
    _arrow(ax, 7.5, 10.0, 7.5, 9.45, lw=1.5)
    _arrow(ax, 12.25, 10.0, 12.25, 6.15, lw=1.5)

    # Inside CNN branch
    for y in [8.6, 7.5, 6.4]:
        _arrow(ax, 2.75, y, 2.75, y - 0.25, lw=1.2)
    # Inside LSTM branch
    for y in [8.6, 7.5, 6.4]:
        _arrow(ax, 7.5, y, 7.5, y - 0.25, lw=1.2)

    # Branches -> merge
    _arrow(ax, 2.75, 5.3, 2.75, 4.9, lw=1.5)
    _arrow(ax, 7.5, 5.3, 7.5, 4.9, lw=1.5)
    _arrow(ax, 12.25, 5.3, 12.25, 4.9, lw=1.5)

    # Merge -> Dense layers
    _arrow(ax, 7.5, 4.0, 7.5, 3.5, lw=2)
    _arrow(ax, 7.5, 2.7, 7.5, 2.5, lw=1.5)
    _arrow(ax, 7.5, 1.7, 7.5, 1.5, lw=1.5)
    _arrow(ax, 7.5, 0.7, 7.5, 0.4, lw=1.5)

    # Annotation box explaining the novelty
    novelty_text = (
        'NOVELTY: The season indicator is concatenated AFTER feature\n'
        'extraction, allowing the model to share CNN/LSTM feature\n'
        'extractors across seasons while learning season-specific\n'
        'yield baselines in the final dense layers.'
    )
    ax.text(0.3, -1.3, novelty_text, fontsize=9.5, color='#B22222',
            fontweight='bold', va='top',
            bbox=dict(boxstyle='round,pad=0.4', edgecolor='#B22222',
                      facecolor='#FFF5F5', linewidth=1.2))

    # Parameter count annotation
    ax.text(13.0, -1.3,
            'Total parameters: ~45,000\nTrainable: 100%',
            fontsize=9, color='#444', va='top',
            bbox=dict(boxstyle='round,pad=0.4', edgecolor='#888',
                      facecolor='#F8F8F8', linewidth=0.8))

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'figure_5_2_cnn_lstm_hybrid.png')
    fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✓ {out}')


# ---------------------------------------------------------------------------
# Figure 5.3 — Database Schema
# ---------------------------------------------------------------------------

def figure_5_3_database_schema():
    """ER diagram. Tables drawn TOP-DOWN: title at top, body below.
    `y` parameter is the TOP edge of the table (title bar)."""
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    ax.set_title('Figure 5.3 — Database Schema',
                 fontsize=14, fontweight='bold', pad=20)

    def _table(ax, x, y_top, name, fields, color, w=3.6):
        """Draw an ER table. Title sits at y_top; body extends downward."""
        head_h = 0.55
        row_h = 0.42
        body_h = row_h * len(fields)
        # Title strip at top
        _box(ax, x, y_top - head_h, w, head_h, name, color=color,
             fontsize=10.5, fontweight='bold')
        # Body below the title
        body_y = y_top - head_h - body_h
        rect = Rectangle((x, body_y), w, body_h, facecolor='white',
                         edgecolor=EDGE_COLOR, linewidth=1)
        ax.add_patch(rect)
        for i, f in enumerate(fields):
            row_top = y_top - head_h - i * row_h
            ax.text(x + 0.12, row_top - row_h / 2,
                    f, fontsize=8.2, family='monospace', va='center')
            if i < len(fields) - 1:
                ax.plot([x, x + w], [row_top - row_h, row_top - row_h],
                        color='#DDD', lw=0.5)
        return body_y, body_h

    # Layout (3 columns): left=lookups, middle=central+predictions, right=feature tables
    # Column 1 (left): districts on top, seasons below
    _table(ax, 0.3, 11.0, 'districts',
           ['PK  district_id  SERIAL',
            '    name         VARCHAR',
            '    centroid_lat NUMERIC',
            '    centroid_lon NUMERIC'], DATA_COLOR)

    _table(ax, 0.3, 7.6, 'seasons',
           ['PK  season_id   SERIAL',
            '    name        VARCHAR',
            '    start_month INT',
            '    end_month   INT'], DATA_COLOR)

    # Column 2 (middle): yield_observations (central) on top, model_predictions below
    _table(ax, 5.6, 11.0, 'yield_observations',
           ['PK  obs_id            SERIAL',
            'FK  district_id       INT',
            'FK  season_id         INT',
            '    year              INT',
            '    avg_yield_mt_ha   NUMERIC',
            '    extent_hectares   NUMERIC',
            '    source            VARCHAR',
            '    created_at        TIMESTAMP'], NOVEL_COLOR, w=4.2)

    _table(ax, 5.6, 5.5, 'model_predictions',
           ['PK  pred_id          SERIAL',
            'FK  obs_id           INT',
            '    model_name       VARCHAR',
            '    predicted_yield  NUMERIC',
            '    ci_lower         NUMERIC',
            '    ci_upper         NUMERIC',
            '    rmse             NUMERIC',
            '    created_at       TIMESTAMP'], OUTPUT_COLOR, w=4.2)

    # Column 3 (right): three feature tables, top-down
    _table(ax, 11.4, 11.0, 'weather_features',
           ['FK  obs_id              INT',
            '    season_avg_temp     NUMERIC',
            '    season_total_rain   NUMERIC',
            '    season_avg_humidity NUMERIC',
            '    growing_degree_days NUMERIC',
            '    drought_index_spi   NUMERIC'], PROCESS_COLOR, w=4.3)

    _table(ax, 11.4, 7.5, 'satellite_features',
           ['FK  obs_id           INT',
            '    season_mean_ndvi NUMERIC',
            '    season_max_ndvi  NUMERIC',
            '    ndvi_anomaly     NUMERIC',
            '    season_mean_evi  NUMERIC',
            '    season_mean_lst  NUMERIC'], ML_COLOR, w=4.3)

    _table(ax, 11.4, 4.0, 'soil_features',
           ['FK  district_id    INT',
            '    soil_ph        NUMERIC',
            '    organic_carbon NUMERIC',
            '    clay_pct       NUMERIC',
            '    sand_pct       NUMERIC'], DL_COLOR, w=4.3)

    # Relationship arrows
    # districts (right edge ~3.9) → yield_observations (left edge 5.6)
    _arrow(ax, 3.9, 10.7, 5.6, 10.4, lw=1.2, style='->', color='#666')
    ax.text(4.3, 10.85, '1..N', fontsize=8, color='#666')
    # seasons → yield_observations
    _arrow(ax, 3.9, 7.3, 5.6, 9.7, lw=1.2, style='->', color='#666')
    ax.text(4.3, 8.7, '1..N', fontsize=8, color='#666')
    # yield_observations → weather_features
    _arrow(ax, 9.8, 10.7, 11.4, 10.7, lw=1.2, style='->', color='#666')
    ax.text(10.3, 10.9, '1..1', fontsize=8, color='#666')
    # yield_observations → satellite_features
    _arrow(ax, 9.8, 9.3, 11.4, 7.2, lw=1.2, style='->', color='#666')
    ax.text(10.3, 8.5, '1..1', fontsize=8, color='#666')
    # yield_observations → model_predictions
    _arrow(ax, 7.7, 8.4, 7.7, 5.5, lw=1.2, style='->', color='#666')
    ax.text(7.85, 7.0, '1..N', fontsize=8, color='#666')
    # districts → soil_features (district-static, dashed)
    _arrow(ax, 3.9, 9.6, 11.4, 3.7, lw=1.2, style='->', color='#999',
           connectionstyle='arc3,rad=-0.25', linestyle='--')
    ax.text(7.3, 1.6, 'soil is district-static (no obs FK)',
            fontsize=8, color='#777', style='italic')

    # Legend
    legend_elements = [
        Rectangle((0, 0), 1, 1, facecolor=DATA_COLOR, label='Lookup tables'),
        Rectangle((0, 0), 1, 1, facecolor=NOVEL_COLOR, label='Central fact'),
        Rectangle((0, 0), 1, 1, facecolor=PROCESS_COLOR, label='Weather'),
        Rectangle((0, 0), 1, 1, facecolor=ML_COLOR, label='Satellite'),
        Rectangle((0, 0), 1, 1, facecolor=DL_COLOR, label='Soil'),
        Rectangle((0, 0), 1, 1, facecolor=OUTPUT_COLOR, label='Predictions'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.02),
              ncol=6, frameon=False, fontsize=9)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'figure_5_3_database_schema.png')
    fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✓ {out}')


# ---------------------------------------------------------------------------

def main():
    print(f'Generating interim-report figures → {OUT_DIR}/')
    figure_4_1_system_architecture()
    figure_4_2_pipeline_stages()
    figure_5_1_data_flow()
    figure_5_2_cnn_lstm_hybrid()
    figure_5_3_database_schema()
    print('\nDone. Drop the PNGs into your Word/PDF report.')


if __name__ == '__main__':
    main()

# Big Onion Yield Prediction — Agro AI

End-to-end system for predicting big onion (Allium cepa) harvest yield across four Sri Lankan districts (Matale, Anuradhapura, Polonnaruwa, Kurunegala) for the Yala and Maha seasons.

University of Moratuwa, Faculty of Information Technology, FYP 2026.

| Member | Index | Component |
|---|---|---|
| Arkam B.H.M. | 214019K | ML/DL modelling pipeline + Flask API |
| Sharuja B. | 214192G | Data engineering + feature engineering |
| Shathurya P. | 214193K | Dashboard + visualisation + decision-support |

## What's in this repo

```
src/             Python ML/DL pipeline + Flask serving API   (Arkam)
frontend/        Next.js 16 dashboard                         (Shathurya)
data/            raw CSVs (when collected) + synthetic + processed
outputs/         trained models, plots, result CSVs
docs/            8 explainer markdowns + interim report + proposal + figures
main.py          run the whole ML/DL pipeline
requirements.txt Python deps
```

The ML/DL pipeline trains 7 models — RF, XGBoost, SVR, LSTM, BiLSTM, 1D-CNN, and a novel **Hybrid CNN-LSTM** with season indicator — on multi-source agricultural data (DCS yield, NASA POWER weather, MODIS NDVI/EVI, Sentinel-2, CHIRPS rainfall, MODIS LST, SoilGrids), and serves the best one over a Flask REST API. The dashboard consumes that API and presents predictions via an interactive choropleth, smart prediction form, SHAP explainability, and a model-comparison admin panel.

## Quick start (fresh clone)

You need **Python 3.12** (TensorFlow 2.16–2.17 doesn't support 3.13/3.14 yet) and **Node ≥ 20** (Next.js 16 requirement).

```bash
git clone https://github.com/Arkambish/AgroAI.git
cd AgroAI
```

### 1 — Run the ML/DL pipeline (Arkam's component)

```bash
# Python venv + install
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Full pipeline (uses synthetic data when raw CSVs are missing). ~6 min on CPU.
python main.py

# Faster iterations during development:
python main.py --skip-shap            # skip SHAP
python main.py --skip-dl --skip-shap  # ML only (~1 min)
python main.py --skip-eda             # skip EDA plots

# Generate the architecture figures used in the interim report:
python src/generate_figures.py
```

After this, `outputs/` contains the trained models, all plots, the model comparison CSV, and the SHAP feature-importance JSON.

### 2 — Start the Flask API

macOS port 5000 is taken by AirPlay Receiver, so use 5050:

```bash
PORT=5050 python src/api.py
# → http://localhost:5050
```

API endpoints (all consumed by the dashboard):

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check |
| `/predict` | POST | Predict yield from a feature payload |
| `/models/compare` | GET | Model-comparison metrics |
| `/feature-importance` | GET | Top-15 SHAP features |
| `/context` | GET | Prefill values for the predict form (`?district=&season=&year=`) |
| `/districts` | GET | Districts/seasons/years for dropdowns |

### 3 — Run the dashboard (Shathurya's component)

In a second terminal, with the API still running:

```bash
cd frontend
npm install
cp .env.local.example .env.local   # only needed if backend isn't on :5050
npm run dev
# → http://localhost:3000
```

The dashboard has four pages:

| Route | What it does |
|---|---|
| `/` | KPI cards, choropleth map, Yala-vs-Maha comparison chart |
| `/predict` | Smart prediction form with auto-prefilled features |
| `/explainability` | Top-15 SHAP feature attributions |
| `/admin` | Sortable model performance table + RMSE/R² chart |

Production build + start:

```bash
cd frontend
npm run build
npm run start
```

> Trained models, generated plots, and `node_modules/` are **not** version-controlled (see `.gitignore`). Run `python main.py` and `npm install` once after cloning to regenerate them.

## What the pipeline does

1. Loads multi-source data (DCS yield, NASA POWER weather, MODIS NDVI/EVI, Sentinel-2, CHIRPS rainfall, MODIS LST, SoilGrids). Falls back to a calibrated synthetic generator if any raw CSV is missing.
2. Preprocesses + engineers features (weather aggregates, vegetation indices, historical yield, soil, interaction terms).
3. Runs EDA — distribution / time-series / correlation / seasonal / district plots.
4. Trains 3 ML models (Random Forest, XGBoost, SVR) and 4 DL models (LSTM, BiLSTM, 1D-CNN, hybrid CNN-LSTM with season indicator) using **Leave-One-Year-Out CV** for honest temporal evaluation.
5. Runs a 6-experiment ablation study to quantify each data source's contribution.
6. Computes SHAP values on the best model.
7. Saves all artefacts under `outputs/` and exposes them via the Flask API and the Next.js dashboard.

## Layout

```
data/raw/             drop real CSVs here when collected
data/synthetic/       regenerated deterministically from seed=42
data/processed/       cleaned + feature-engineered training data
outputs/models/       *.pkl (sklearn) + *.keras (TF)
outputs/plots/        eda/, training/, results/, figures/
outputs/results/      comparison CSVs, JSON metrics, final_summary.txt
src/                  Python pipeline (see config.py for all knobs)
src/api.py            Flask REST API
frontend/             Next.js 16 dashboard (App Router, TypeScript, Tailwind 4)
docs/                 8 explainer markdowns + interim report + proposal
main.py               run the whole pipeline
```

## Documentation

If you're new to the project, read the explainers in `docs/` in order:

1. [docs/00_OVERVIEW.md](docs/00_OVERVIEW.md) — project at a glance
2. [docs/01_PROBLEM_AND_DATA.md](docs/01_PROBLEM_AND_DATA.md) — agricultural problem and data sources
3. [docs/02_ML_DL_FUNDAMENTALS.md](docs/02_ML_DL_FUNDAMENTALS.md) — ML/DL crash course
4. [docs/03_PIPELINE_WALKTHROUGH.md](docs/03_PIPELINE_WALKTHROUGH.md) — every Python file explained
5. [docs/04_MODELS_EXPLAINED.md](docs/04_MODELS_EXPLAINED.md) — all 7 models in plain English
6. [docs/05_NOVELTY_AND_RESEARCH.md](docs/05_NOVELTY_AND_RESEARCH.md) — research contribution
7. [docs/06_RESULTS_AND_INTERPRETATION.md](docs/06_RESULTS_AND_INTERPRETATION.md) — what the numbers mean
8. [docs/07_HOW_TO_RUN.md](docs/07_HOW_TO_RUN.md) — command-by-command runbook

The interim report itself is at [docs/Interim_Report_AgroAI.md](docs/Interim_Report_AgroAI.md), and the original proposal at [docs/Proposal FYP.md](docs/Proposal%20FYP.md).

## Notes

- DL models use **50 epochs/fold** by default in synthetic-mode (`SYNTHETIC_MODE_DL_EPOCHS` in `src/config.py`). Bump to 200 for real data.
- TensorFlow saves models in the modern `.keras` format (replaces legacy `.h5`).
- All randomness is seeded (`RANDOM_STATE=42`) — the synthetic dataset and all training runs are reproducible.
- The dashboard is hand-written shadcn-style components on Radix UI + Tailwind 4 (no shadcn CLI because its templates currently target Tailwind 3).

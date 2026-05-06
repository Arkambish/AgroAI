# Big Onion Yield Prediction — Agro AI

ML/DL pipeline for predicting big onion (Allium cepa) harvest yield across four Sri Lankan districts (Matale, Anuradhapura, Polonnaruwa, Jaffna) for the Yala and Maha seasons.

University of Moratuwa, Faculty of Information Technology, FYP 2026.
Arkam B.H.M. (214019K) — ML/DL modelling component.

## Quick start (fresh clone)

Requires **Python 3.12** (TensorFlow 2.16–2.17 doesn't support 3.13/3.14 yet).

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# Create the virtual environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Full pipeline (uses synthetic data when raw CSVs are missing)
python main.py

# Faster iterations
python main.py --skip-shap            # skip SHAP (slow on KernelExplainer)
python main.py --skip-dl --skip-shap  # ML only
python main.py --skip-eda             # skip EDA plots

# Generate the interim-report figures
python src/generate_figures.py

# Serve the trained model (default port 5000; override on macOS where AirPlay grabs 5000)
python src/api.py            # http://localhost:5000
PORT=5050 python src/api.py  # http://localhost:5050
```

> Trained models, generated plots, and result CSVs are **not** version-controlled (see `.gitignore`). Run `python main.py` once after cloning to regenerate them.

## What it does

1. Loads multi-source data (DCS yield, NASA POWER weather, MODIS NDVI/EVI, Sentinel-2, CHIRPS rainfall, MODIS LST, SoilGrids). Falls back to a calibrated synthetic generator if any raw CSV is missing.
2. Preprocesses + engineers features (weather aggregates, vegetation indices, historical yield, soil, interaction terms).
3. Runs EDA — distribution / time-series / correlation / seasonal / district plots.
4. Trains 3 ML models (Random Forest, XGBoost, SVR) and 4 DL models (LSTM, BiLSTM, 1D-CNN, hybrid CNN-LSTM with season indicator) using **Leave-One-Year-Out CV** for honest temporal evaluation.
5. Runs a 6-experiment ablation study to quantify each data source's contribution.
6. Computes SHAP values on the best model.
7. Saves all artefacts under `outputs/` and exposes a Flask `/predict` API.

## Layout

```
data/raw/         drop real CSVs here when collected
data/synthetic/   regenerated deterministically from seed=42
outputs/models/   *.pkl (sklearn) + *.keras (TF)
outputs/plots/    eda/, training/, results/
outputs/results/  comparison CSVs, JSON metrics, final_summary.txt
src/              pipeline modules — see config.py for all knobs
```

## Notes

- DL models use **50 epochs/fold** by default in synthetic-mode (see `SYNTHETIC_MODE_DL_EPOCHS` in `src/config.py`). Bump to 200 for real data.
- TensorFlow saves models in the modern `.keras` format (replaces legacy `.h5`).
- All randomness is seeded (`RANDOM_STATE=42`).

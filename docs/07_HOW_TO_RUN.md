# 07 — How to Run the Project

Step-by-step commands. Open Terminal, paste each block, hit enter.

## 0. Prerequisites

You need:
- macOS (this guide), Linux, or WSL on Windows.
- **Python 3.12** installed. Check by running:
  ```bash
  python3.12 --version
  ```
  If not installed, download from https://www.python.org/downloads/

> If you're on Python 3.13 or 3.14: TensorFlow doesn't support those yet. Install Python 3.12 alongside.

## 1. First-time setup (do this once)

```bash
# Navigate to the project folder
cd /Users/arqm7/Documents/FYP/Model

# Create a virtual environment (an isolated Python install just for this project)
python3.12 -m venv .venv

# Activate it (must do this every new terminal session)
source .venv/bin/activate

# Upgrade pip to the latest
pip install -U pip

# Install all the packages from requirements.txt
pip install -r requirements.txt
```

The last command downloads ~2 GB of packages (TensorFlow is large). Takes ~5 minutes on a good connection.

After this, you should see something like:
```
Successfully installed numpy-1.26.4 pandas-3.0.2 ... tensorflow-2.17.1 ...
```

## 2. Activate the venv (every new terminal)

Whenever you open a fresh terminal, you need to activate the venv first:
```bash
cd /Users/arqm7/Documents/FYP/Model
source .venv/bin/activate
```

You'll know it's active because your prompt now starts with `(.venv)`.

## 3. Run the full pipeline

```bash
python main.py
```

This:
1. Generates synthetic data (since real CSVs aren't in `data/raw/` yet).
2. Preprocesses it.
3. Engineers features.
4. Runs EDA → 6 plots in `outputs/plots/eda/`.
5. Trains 3 ML models (RF, XGBoost, SVR) — **~1 minute**.
6. Trains 4 DL models (LSTM, BiLSTM, CNN, Hybrid) — **~5 minutes** on CPU.
7. Runs the 6-experiment ablation study.
8. Runs SHAP feature importance.
9. Generates the final comparison and summary.

Total time: **~6 minutes** the first run.

When done you'll see:
```
============================================================
  PIPELINE COMPLETE in 5.7 minutes
  Results saved to: outputs/
============================================================
```

## 4. Faster iteration (skip slow steps)

While iterating on the code, you don't need to re-train DL models every time. Skip them:

```bash
# Skip DL models and SHAP — runs in ~1 minute
python main.py --skip-dl --skip-shap

# Skip just SHAP (DL is fine to run)
python main.py --skip-shap

# Skip EDA (you've seen the plots already)
python main.py --skip-eda

# Run only the orchestrator + final comparison (after you've trained models)
python main.py --skip-eda --skip-ml --skip-dl --skip-ablation --skip-shap
```

All flags:
- `--skip-eda` — don't regenerate EDA plots
- `--skip-ml` — don't retrain ML models
- `--skip-dl` — don't retrain DL models (saves ~5 min)
- `--skip-ablation` — don't rerun ablation (saves ~30 sec)
- `--skip-shap` — don't run SHAP (saves ~15 sec)

## 5. View the results

After running, look at:

```bash
# Open the summary in your editor or terminal
cat outputs/results/final_summary.txt

# Open the model comparison CSV in numbers/excel
open outputs/results/model_comparison.csv

# Open the key bar chart
open outputs/plots/results/model_comparison_bar.png

# Open the SHAP summary
open outputs/plots/results/shap_summary.png

# Browse all plots in Finder
open outputs/plots/
```

`open` is the macOS command — on Linux use `xdg-open`, on Windows use `start`.

## 6. Run the prediction API

The API serves your best trained model over HTTP so other code (like Shathurya's dashboard) can request predictions.

### Start the server

macOS port 5000 is taken by AirPlay, so use a different port:

```bash
PORT=5050 python src/api.py
```

You'll see:
```
[api] Loaded RandomForest (metrics={...})
 * Running on http://127.0.0.1:5050
```

Leave this terminal running. Open a **new** terminal for the next step.

### Test the API

In the new terminal (also activate the venv first):

```bash
cd /Users/arqm7/Documents/FYP/Model
source .venv/bin/activate

# Health check
curl http://localhost:5050/health
# → {"model":"RandomForest","service":"BigOnion Yield Predictor","status":"ok"}

# Make a prediction
curl -X POST http://localhost:5050/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "district": "Matale",
    "season": "Yala",
    "season_total_rainfall": 850,
    "season_avg_temp": 28.5,
    "season_mean_ndvi": 0.65,
    "soil_ph": 6.2,
    "prev_year_yield": 16.0
  }'

# → {"confidence_lower":..., "predicted_yield_MT_per_Ha":..., ...}

# View all model metrics
curl http://localhost:5050/models/compare

# View top-15 SHAP features
curl http://localhost:5050/feature-importance
```

### Stop the server

Go back to the terminal running the server. Press `Ctrl+C`.

## 7. When real data arrives

You'll receive 7 CSV files from Sharuja:
- `dcs_yield.csv`
- `nasa_power_weather.csv`
- `modis_ndvi_evi.csv`
- `sentinel2_indices.csv`
- `chirps_rainfall.csv`
- `modis_lst.csv`
- `soil_data.csv`

Drop them into `data/raw/` (the folder is already there). Then:

```bash
python main.py
```

The loader checks `data/raw/` first; only generates synthetic data if any file is missing. With all 7 present, it'll load and merge them automatically.

**Probably also wanted with real data:**
- Edit `src/config.py` and bump `SYNTHETIC_MODE_DL_EPOCHS` from 50 to 200, OR change the DL training code to use `MAX_EPOCHS` directly. With real data the longer training will help.
- Replace the synthetic monthly weather expansion in `src/feature_engineer.py` with a real reader for monthly NASA POWER series, if you have them. (Consult [docs/03_PIPELINE_WALKTHROUGH.md](03_PIPELINE_WALKTHROUGH.md).)

## 8. Common issues and fixes

### "ModuleNotFoundError: No module named 'X'"

You forgot to activate the venv. Run:
```bash
source .venv/bin/activate
```

### "Address already in use" on port 5000

macOS AirPlay. Use:
```bash
PORT=5050 python src/api.py
```

### "Python 3.14 not supported by TensorFlow"

Your default `python3` is 3.13/3.14. Use `python3.12` explicitly:
```bash
python3.12 -m venv .venv
```

### Plots don't show / matplotlib errors

The pipeline uses a **non-interactive backend** (saves to PNG, doesn't pop up windows). If you want to view plots inline in a Jupyter notebook, you'd need extra setup — but for the FYP, just open the PNGs directly with `open outputs/plots/...`.

### Pipeline crashes mid-run

Models are saved **immediately after each is trained**, so partial progress is preserved. To resume:
```bash
# Skip the steps that already finished
python main.py --skip-ml   # if ML completed but DL crashed
```

### "tensorflow gives loads of warnings"

Normal. TensorFlow logs `oneDNN`, `XLA`, etc. messages — they're informational, not errors. The pipeline already silences most of them via `os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'`.

### Want to delete everything and start fresh

```bash
# Wipe outputs (keeps data/, src/, etc.)
rm -rf outputs/
python main.py

# Wipe everything except code
rm -rf outputs/ data/processed/ data/synthetic/
python main.py
```

## 9. Useful exploration commands

```bash
# What's the structure?
tree -L 3 -I '.venv|__pycache__'   # if `tree` isn't installed: brew install tree
# Or:
find . -type d -not -path '*/.venv*' -not -path '*/__pycache__*' | head -40

# How big are the model files?
ls -lh outputs/models/

# What's in a JSON file?
python3 -c "import json; print(json.dumps(json.load(open('outputs/results/feature_importance.json')), indent=2))" | head -30

# Quick stats on the synthetic dataset
python3 -c "
import pandas as pd
df = pd.read_csv('data/synthetic/synthetic_dataset.csv')
print(f'Rows: {len(df)}, Cols: {len(df.columns)}')
print(df.describe())
"
```

## 10. Don't break things

- **Don't edit files inside `outputs/` or `.venv/`** — they're regenerated.
- **Do edit `src/config.py`** to change hyperparameters.
- **Do edit `src/data_loader.py`** if you need to adjust the synthetic generator.
- If you're scared of breaking something, copy `src/` to `src_backup/` before editing.

## 11. What to do next

1. Read [00_OVERVIEW.md](00_OVERVIEW.md) → [01_PROBLEM_AND_DATA.md](01_PROBLEM_AND_DATA.md) → [02_ML_DL_FUNDAMENTALS.md](02_ML_DL_FUNDAMENTALS.md) in order.
2. Run `python main.py` and look at the plots in `outputs/plots/`.
3. Open the synthetic dataset (`data/synthetic/synthetic_dataset.csv`) in Numbers / Excel — get a feel for what the rows look like.
4. Open `outputs/results/final_summary.txt` and read the 9 findings.
5. When you're ready to write the report, use [05_NOVELTY_AND_RESEARCH.md](05_NOVELTY_AND_RESEARCH.md) and [06_RESULTS_AND_INTERPRETATION.md](06_RESULTS_AND_INTERPRETATION.md) as your structure.

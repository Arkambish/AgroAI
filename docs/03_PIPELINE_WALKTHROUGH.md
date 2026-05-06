# 03 — Pipeline Walkthrough (file by file)

This walks through every file in the project. After reading this you should know what each piece of code is doing and why.

## Mental model: the pipeline as a conveyor belt

```
Step 1   data_loader.py        Raw CSVs (or synthetic) → one DataFrame
Step 2   preprocessor.py       Clean + validate that DataFrame
Step 3   feature_engineer.py   Build the matrices the models need
Step 4   eda.py                Save plots + print stats
Step 5   ml_models.py          Train Random Forest, XGBoost, SVR
Step 6   dl_models.py          Train LSTM, BiLSTM, CNN, Hybrid
Step 7   ablation.py           Run 6 feature-subset experiments
Step 8   evaluator.py          Compare all 7 models, write summary
Step 9   explainer.py          SHAP on best model
         api.py                Serve best model via REST
```

`main.py` is the conveyor belt operator — it calls each step in order.

---

## `requirements.txt`

Lists every Python package the project needs and their versions. `pip install -r requirements.txt` reads this and installs all of them. Notable choices:

- `tensorflow>=2.16,<2.18` — the deep learning library. We use Google's TensorFlow with the Keras 3 API for building neural networks.
- `xgboost>=2.0` — gradient-boosted tree library, one of the most reliable ML algorithms ever.
- `scikit-learn>=1.3,<1.6` — the workhorse ML library (Random Forest, SVR, scaling, cross-validation).
- `shap>=0.42` — the explainability library for SHAP values.
- `flask>=3.0` + `flask-cors` — the lightweight web framework for the prediction API.
- `numpy<2.0` — there's a NumPy 2.0 ecosystem incompatibility right now; this pin avoids it.

---

## `src/config.py`

The settings file. Every hyperparameter, every threshold, every grid is here so you only need to change things in one place.

Key sections:

```python
RANDOM_STATE = 42                       # Fixed seed → reproducible results
DISTRICTS = ['Matale', ...]             # The 4 districts
SEASONS = ['Yala', 'Maha']              # The 2 seasons
TARGET_COLUMN = 'Avg_Yield_MT_per_Ha'   # What we're predicting
```

Then **feature groups** for the ablation study:
```python
WEATHER_FEATURES   = [...]   # 9 weather-derived features
SATELLITE_FEATURES = [...]   # 11 NDVI/EVI/LST features
HISTORICAL_FEATURES = [...]  # 5 lagged-yield features
SOIL_FEATURES       = [...]  # 4 static soil features
INTERACTION_FEATURES = [...]  # 3 multiplied features
ALL_FEATURES = WEATHER + SATELLITE + HISTORICAL + SOIL + INTERACTION  # 32 total
```

Then **hyperparameter grids** for the three ML models:
```python
RF_PARAMS = {'n_estimators': [100,200,500], ...}     # full grid
RF_PARAMS_FAST = {'n_estimators': [200], ...}        # smaller, faster grid actually used
```
The "FAST" variants are used so LOYO-CV (which trains 20× per model) finishes in minutes, not hours.

Then **DL settings**:
```python
LSTM_UNITS = [64, 32]               # First LSTM layer has 64 neurons, second has 32
DROPOUT_RATE = 0.2                  # Drop 20% of neurons during training
LEARNING_RATE = 0.001               # Adam optimiser step size
BATCH_SIZE = 16                     # 16 examples per gradient update
MAX_EPOCHS = 200                    # Maximum training passes
EARLY_STOPPING_PATIENCE = 20        # Stop if val loss doesn't improve for 20 epochs
SEQUENCE_LENGTH = 5                 # 5 monthly timesteps
SYNTHETIC_MODE_DL_EPOCHS = 50       # Cap to 50 when using synthetic data
```

---

## `src/data_loader.py`

**Purpose:** load raw data or generate synthetic.

Three functions:

### `check_data_availability()`
Looks for the 7 expected CSV files in `data/raw/`. Returns a dict like `{'dcs_yield': True, 'nasa_power': False, ...}`. Prints ✓ Found / ✗ Missing for each.

### `generate_synthetic_data()`
Generates the fake dataset (calibrated to published ranges — see [01_PROBLEM_AND_DATA.md](01_PROBLEM_AND_DATA.md)).

The flow:
1. Loop over years 2004–2023, districts, seasons.
2. For each, sample yield from a Gaussian (`np.random.normal(mean, std)`) where the mean depends on the district and season.
3. Add a per-year `climate_shock` so wet/dry years correlate across districts.
4. Sample weather (rainfall, temperature, humidity, solar) from realistic distributions.
5. Sample NDVI from `0.3 + yield/30 + noise` — this is what makes NDVI predictive of yield in synthetic data (the model has to *discover* this relationship).
6. After all rows are generated, compute lagged features (`prev_season_yield`, `yield_3yr_avg`) by shifting within each (district, season) group.
7. Compute interaction features (`rainfall_x_ndvi = rainfall × ndvi`).
8. Drop rows with NaN (the first year has no lag), save to `data/synthetic/synthetic_dataset.csv`.

The seed `RANDOM_STATE=42` makes this deterministic — re-running gives identical output.

### `load_real_data()`
For when CSVs exist: read each, merge them all on `(District, Year, Season)`. Currently a placeholder for when real data arrives.

### `load_data()` (the entry point)
Dispatches: if all 7 files exist, call `load_real_data()`; otherwise `generate_synthetic_data()`.

---

## `src/preprocessor.py`

**Purpose:** clean and validate.

Steps:
1. Drop rows where target (`Avg_Yield_MT_per_Ha`) is NaN.
2. Drop rows with negative or zero yield (a sanity check).
3. Drop rows with unknown districts/seasons.
4. **Forward-fill** lagged features within each (district, season) group — handles the synthetic generator's edge cases.
5. **Median-fill** any remaining NaN in numeric features.
6. **Winsorise** the target — clip values at the 1st and 99th percentile. This caps absurd outliers without removing the rows.
7. Save to `data/processed/integrated_dataset.csv`.

Why these steps? Real-world data is messy: missing values, typos, occasional sensor errors. Even on synthetic data we run all the checks, so the pipeline is ready for real data.

---

## `src/feature_engineer.py`

**Purpose:** convert the cleaned DataFrame into the matrices each model expects.

Returns four things:

1. **`X_tabular`**: a 2D NumPy array of shape `(n_samples, 32)` — one row per observation, 32 features. Used by RF, XGBoost, SVR.
2. **`y`**: a 1D NumPy array of shape `(n_samples,)` — the yield labels.
3. **`feature_names`**: list of the 32 feature names (so we can label SHAP plots).
4. **`seq_payload`**: a dict containing the multi-modal tensors for DL:
   - `weather_seq`: `(n_samples, 5, 4)` — 5 monthly timesteps × 4 weather variables
   - `satellite`: `(n_samples, 11, 1)` — 11 satellite features as a 1D "image" for the CNN
   - `season`: `(n_samples, 1)` — Yala=1 / Maha=0 indicator for the hybrid model
   - `y`, `years`, `districts`, `seasons` — metadata

The function `_synthesise_weather_sequence()` deserves a callout. Since real monthly data isn't available, this expands seasonal aggregates into 5-step sequences:
- Temperature: bell-shaped curve (cool start, hot middle, cooler end)
- Rainfall: front-loaded (more rain early in the season)
- Humidity, solar: roughly flat
- Plus 2% noise per step

When real monthly NASA POWER data arrives, replace this function with a real reader. The DL models will keep working.

Outputs saved:
- `data/processed/features_tabular.csv` — human-readable CSV of the tabular features
- `data/processed/features_sequential.pkl` — the DL tensors as a Python pickle (binary file)

---

## `src/eda.py`

**Purpose:** Exploratory Data Analysis. Generates 6 plots and prints summary statistics. Lets you (and your supervisor) actually *see* the data before modelling.

Functions:

| Function | Plot |
|---|---|
| `_yield_distribution(df)` | Histograms of yield by district and season |
| `_yield_timeseries(df)` | Line plots of yield over time, one panel per district |
| `_correlation_heatmap(df)` | Top-15 features ranked by Pearson correlation with yield |
| `_feature_distributions(df)` | Histograms of the top-10 most-correlated features |
| `_seasonal_comparison(df)` | Box plots: Yala vs Maha per district, with significance markers |
| `_district_comparison(df)` | Bar chart: mean yield per district × season |

`_print_stats()` prints the data summary table to the terminal.

All plots saved at 150 DPI to `outputs/plots/eda/`.

---

## `src/visualizer.py`

**Purpose:** Shared plotting helpers used by both ML and DL models. Keeps the plot style consistent.

Functions:

- `actual_vs_predicted(y_true, y_pred, model_name, save_path, districts)` — the classic scatter plot with the y=x diagonal. R² is annotated. Points coloured by district.
- `residual_plot(y_true, y_pred, ...)` — residuals (actual − predicted) vs predicted values, with outliers (|res| > 2σ) highlighted in red.
- `feature_importance_plot(importances, names, ..., top_k=15)` — horizontal bar chart of the top 15 features.
- `learning_curve_plot(history, ...)` — training loss vs validation loss over epochs (for DL models).

---

## `src/ml_models.py`

**Purpose:** train the three classical ML models.

Each model has a function:

- `train_random_forest(X, y, feature_names, df)`
- `train_xgboost(X, y, feature_names, df)`
- `train_svr(X, y, feature_names, df)`

Each function follows the same protocol:

1. **Inner tuning**: GridSearchCV with TimeSeriesSplit(5) on the FAST hyperparameter grid → pick best params.
2. **Outer evaluation**: LOYO-CV → for each year, train on every other year, predict the held-out year. Concatenate all out-of-fold predictions.
3. **Final refit**: train one more time on *all* data with the best params. This is the deployable model.
4. **Save artefacts**:
   - The final model (`outputs/models/rf_best.pkl` etc.) — Pickle is Python's binary serialisation.
   - The scaler if applicable (`svr_scaler.pkl` for SVR).
   - The OOF predictions in JSON (`outputs/results/oof_randomforest.json`) — used by the evaluator.
   - The plots (scatter, residuals, feature importance).

The shared helper `_loyo_predictions()` does the actual cross-validation loop. For SVR it scales features inside each fold (so the scaler never sees test data — preventing data leakage).

---

## `src/dl_models.py`

**Purpose:** train the four deep learning models.

Top of file: `tf.random.set_seed(42)` to make TensorFlow reproducible.

### Model builders

Each builder returns a fresh, compiled Keras model:

- `build_lstm(n_weather)` — 2-layer LSTM
- `build_bilstm(n_weather)` — 2-layer Bidirectional LSTM
- `build_cnn(n_features)` — 1D CNN with batch normalisation
- `build_cnn_lstm_hybrid(n_satellite, n_weather)` — the **novel architecture**. Three inputs, two branches that get concatenated, then dense layers and a final scalar output.

All compiled with:
```python
optimizer=Adam(LEARNING_RATE)   # adaptive optimiser, very common
loss='mse'                       # mean squared error (regression)
metrics=['mae']                  # also track mean absolute error
```

### Training loops

Three separate LOYO loops, one for each input shape:

- `_train_loyo_seq()` — sequence input only (LSTM, BiLSTM)
- `_train_loyo_cnn()` — tabular-as-1D input (CNN)
- `_train_loyo_hybrid()` — three inputs (Hybrid)

Each loop:
1. For each year, split train/test.
2. Scale features using stats from training data only.
3. Build a fresh model.
4. Fit with `validation_split=0.15` (15% of training data for validation).
5. Add callbacks: `EarlyStopping`, `ReduceLROnPlateau`, `ModelCheckpoint`.
6. Predict on the held-out year.
7. `tf.keras.backend.clear_session()` — frees memory between folds.

After LOYO, refit one final model on all data and save as `.keras` format.

---

## `src/ablation.py`

**Purpose:** quantify how much each data source contributes.

Six experiments using XGBoost as the base learner:

| Code | Features used | Tests |
|---|---|---|
| A | Weather only | Weather baseline |
| B | Satellite only | Satellite baseline |
| C | Historical (lagged yield) only | Memory baseline |
| D | Soil only | Soil baseline |
| E | Weather + Satellite | Two-source combo |
| F | All 32 features | Full multi-source model |

For each, run LOYO-CV → compute RMSE/MAE/R² → save row to `outputs/results/ablation_results.csv`. Plot all R² values as a bar chart.

The headline number: `Δ R² (Weather → Weather+Satellite)`. On synthetic data this was **+55 percentage points** — i.e. satellite is doing most of the heavy lifting.

---

## `src/evaluator.py`

**Purpose:** combine all the per-model OOF predictions into a single comparison table and the final research summary.

Steps:

1. Read every `outputs/results/oof_*.json` file produced by the ML and DL training.
2. Pull the metrics from each into one DataFrame.
3. Sort by R² descending → save as `outputs/results/model_comparison.csv`.
4. Generate `outputs/plots/results/model_comparison_bar.png` — RMSE (solid bars) and R² (hatched bars) for all 7 models, with the target R²=0.75 line.
5. Save best model metadata to `outputs/results/best_model_metrics.json` (the API reads this).
6. Run statistical tests (Wilcoxon + paired t) comparing pooled ML errors vs pooled DL errors.
7. Compute per-district R² (which districts are easiest/hardest to predict?).
8. Compute Yala vs Maha RMSE.
9. Write everything as plain text to `outputs/results/final_summary.txt` — the **9 research findings** that go into your report.

---

## `src/explainer.py`

**Purpose:** SHAP analysis on the best tree-based model.

Why tree-based even if a DL model wins? `shap.TreeExplainer` is fast (seconds). `shap.KernelExplainer` for DL models is slow (minutes-hours) and gives noisier estimates. For an FYP report, the tree-based explanation is more reliable.

Steps:
1. Load the best model (RF or XGBoost).
2. `shap.TreeExplainer(model).shap_values(X)` → a `(n_samples, n_features)` matrix of SHAP values.
3. Compute `mean(|SHAP|)` per feature → ranked feature importance.
4. Generate three plots:
   - **`shap_summary.png`** — beeswarm: every dot is one prediction, vertical position is the feature, horizontal position is the SHAP value, colour is the feature value. The richest single visualisation in the project.
   - **`shap_importance.png`** — bar chart of mean |SHAP|, top 15.
   - **`shap_dependence_<top_feature>.png`** — how the most-important feature's value relates to its SHAP value. Reveals non-linear effects.
5. Persist top-15 to `outputs/results/feature_importance.json` (the API reads this).

---

## `src/api.py`

**Purpose:** serve the trained model as a REST API for downstream consumption (Shathurya's dashboard).

Flask app with four endpoints:

| Endpoint | Method | What it does |
|---|---|---|
| `/health` | GET | Sanity check: returns `{"status": "ok"}` |
| `/predict` | POST | Takes feature values, returns predicted yield + 95% confidence interval |
| `/models/compare` | GET | Returns the model_comparison.csv as JSON |
| `/feature-importance` | GET | Returns the SHAP top-15 as JSON |

`/predict` example:
```bash
curl -X POST http://localhost:5050/predict \
  -H 'Content-Type: application/json' \
  -d '{"district":"Matale","season":"Yala","season_mean_ndvi":0.65,...}'

# Response:
{
  "district": "Matale",
  "season": "Yala",
  "predicted_yield_MT_per_Ha": 16.2,
  "confidence_lower": 12.1,
  "confidence_upper": 20.3,
  "model": "RandomForest",
  "model_r2": 0.84
}
```

Confidence interval = `prediction ± 1.96 × RMSE` (the standard 95% Gaussian interval).

Port note: macOS uses port 5000 for AirPlay Receiver. Use `PORT=5050 python src/api.py` to override.

---

## `main.py`

**Purpose:** the orchestrator. Reads command-line flags, calls each module in order.

```python
df = load_data()                          # Step 1
df = preprocess(df)                       # Step 2
X, y, names, seq = engineer_features(df)  # Step 3

if not args.skip_eda:    run_eda(df)                       # Step 4
if not args.skip_ml:     train_all_ml_models(X, y, ...)    # Step 5
if not args.skip_dl:     train_all_dl_models(seq, df)      # Step 6
if not args.skip_ablation: ablation_df = run_ablation_study(df)  # Step 7
if not args.skip_shap:   run_shap_analysis(X, names)       # Step 9 (before 8)
generate_final_comparison(ablation=ablation_df)            # Step 8
```

The `--skip-*` flags let you turn off slow steps during iteration:

```bash
python main.py                       # Full run (~6 min)
python main.py --skip-dl --skip-shap # ML only (~1 min) — for iterating quickly
python main.py --skip-eda            # Skip plots if you've seen them
```

`sys.path.insert(0, 'src')` at the top makes the `src/` directory importable, so `from config import *` works without turning `src/` into a Python package.

---

## How a single prediction actually flows through

Trace one observation through the pipeline:

1. **Loader** generates one row: `{district: 'Matale', year: 2020, season: 'Yala', yield: 16.2, rainfall: 850, ndvi: 0.68, ...}`
2. **Preprocessor** validates it, fills any NaNs, clips outliers — row passes through unchanged.
3. **Feature engineer** turns it into:
   - A 32-element feature vector for ML.
   - A 5×4 weather sequence + 11×1 satellite tensor + season indicator for the hybrid DL.
4. **ML training**: held out from one LOYO fold (the year=2020 fold). When that fold runs, the trained model predicts this row → 16.0. (Actual is 16.2, error 0.2.)
5. **OOF prediction saved** to `oof_randomforest.json`.
6. **Evaluator** reads OOF, computes overall RMSE/MAE/R² — this row contributes one error to those aggregates.
7. **Best model refit** on all data including this row → saved to `outputs/models/rf_best.pkl`.
8. **API call** with the same feature values → loads `rf_best.pkl`, predicts → 16.1. Returns `{"predicted_yield_MT_per_Ha": 16.1, "confidence_lower": 12.0, "confidence_upper": 20.2}`.

That's the whole journey.

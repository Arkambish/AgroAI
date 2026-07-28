# 09 — System Audit: What Is Actually Implemented

> **Scope and method.** This document is a read-only, code-level audit of the AgroAI/AgriSense repository as it exists on disk. Every claim below is traceable to a specific file, line number, or an actual value read from an output artifact (CSV/JSON) under `outputs/`. It does **not** restate the proposal, the interim/final report narrative, or `docs/00`–`docs/07` — where those documents' claims were checked against code and found to hold, that is noted; where they diverge from what the code does, that is flagged as a gap in §7. Line numbers refer to the files as they exist at the time of this audit (2026-07-26, branch `shathurya-update`).

---

## 1. System Overview

**End-to-end flow, as implemented:**

1. **Data in** — `src/data_loader.py` produces a table of 32 features + target yield per (District, Season, Year), either by aggregating a real monthly CSV (`load_collected_data()`) or by simulating one (`generate_synthetic_data()`). Feature engineering/median-fill is done inline in the same functions; `src/feature_engineer.py` and `src/preprocessor.py` handle scaling/train-test splitting for the ML/DL scripts.
2. **Model** — `main.py` orchestrates training of multiple model families (tree ensembles, symbolic regression, a physics-informed hybrid, deep sequence models, and stacking ensembles) under a Leave-One-Year-Out (LOYO) protocol, then `src/evaluator.py` ranks them by R² and writes `best_model_metrics.json`.
3. **Prediction (serving)** — `src/api.py` is a Flask app that loads one persisted tabular model (XGBoost, RandomForest, or SVR only — see §3) and serves `/predict`, computing a point estimate, a conformal-calibrated confidence interval, live SHAP values, and a live per-request Explanation Reliability Index (ERI).
4. **Explanation** — `src/xai/*.py` computes four offline, dataset-level XAI artifacts (grounding, stability, consensus, ERI) plus `src/explainer.py` (SHAP) and `src/symbolic.py` (symbolic regression), all persisted as JSON/PNG under `outputs/results{,_real}/`. Some of this is also computed live per-request inside `/predict`.
5. **UI** — `dashboard/` (Next.js, App Router, `next-intl` i18n) is the only active frontend. It calls `/districts`, `/context`, `/baseline`, `/predict`, `/api/chat`, `/api/recommend` — it does **not** call 6 of the 13 backend routes (see §5).

### Top-level modules

| Module | Responsibility (evidence) |
|---|---|
| `src/` | Python backend: data loading, feature engineering, model training (ML/DL/hybrid/stacking), evaluation, XAI, conformal prediction, Flask API, and report/figure-generation scripts (`generate_*`, `final_report_content.py`). |
| `src/xai/` | Subpackage implementing offline explainability: `grounding.py`, `stability.py`, `consensus.py`, `eri.py`, orchestrated by `run_xai.py`. |
| `dashboard/` | Active Next.js 16 (App Router) frontend consumed by end users; i18n via `next-intl`, 3 locales (`en`, `si`, `ta`). |
| `frontend/` | **Legacy/dead** — a separate, older Next.js app. Last touched by commit `b2b8a82`/`6f7c154` (2026-06-18); superseded by `dashboard/`. Contains only `next-env.d.ts` and `node_modules` at present (its source appears to have been removed while the directory itself was left behind). |
| `data/` | Raw/collected/synthetic/processed datasets. `data/raw/` is empty (`.gitkeep` only); `data/collected/` holds the manually merged real CSV; `data/synthetic/` and `data/processed{,_real}/` hold generated/feature-engineered tables. |
| `outputs/` | All generated artifacts: `results/` and `results_real/` (metrics + XAI JSON per data variant), `models/` and `models_real/` (persisted `.pkl` model files), `plots/`, `plots_real/`, `poster/`, `deck/`, plus the compiled Final Report/Poster/Presentation files. |
| `docs/` | Narrative documentation (`00`–`07`), the FYP proposal, interim report, and presentation guide — **not code**, treated here only as something to check code against, not to restate. |
| `main.py` | CLI entry point (`python main.py` / `--real`) that runs the full training→evaluation→XAI pipeline end-to-end and writes all `outputs/` artifacts. |

---

## 2. Data Pipeline

### 2.1 Data sources actually loaded in code

| Source | File : function | What it loads |
|---|---|---|
| Manually merged real dataset | `src/data_loader.py` : `load_collected_data()` (L161-272) | Reads `data/collected/FYP data(manual) - onion_unique_per_key.csv` (path constant `COLLECTED_FILE`, `src/config.py` L24) — one CSV, monthly grain, columns `year, month, season, district, temperature_c, rainfall, humidity_pct, evi_i, ndvi_i, clay_0_5cm, ph_0_5cm, sand_0_5cm, yield_mt_per_ha, source`. |
| Synthetic simulator | `src/data_loader.py` : `generate_synthetic_data()` (L39-130) | Loads nothing from disk; draws all values from `numpy.random.default_rng` per hand-set per-district parameters (`district_params`, L44-49). |
| "Raw" 7-file real pipeline | `src/data_loader.py` : `load_real_data()` (L133-151) + `REQUIRED_FILES` (L19-27) | Expects `data/raw/dcs_yield.csv`, `nasa_power_weather.csv`, `modis_ndvi_evi.csv`, `sentinel2_indices.csv`, `chirps_rainfall.csv`, `modis_lst.csv`, `soil_data.csv`. **`data/raw/` is empty** (verified: only `.gitkeep`) — this function is never actually exercised in the current repo state; `check_data_availability()` (L30-36) always reports all 7 missing, so `load_data()` (L275-290) falls through to `generate_synthetic_data()` whenever `DATA_VARIANT != 'real'`. |

**Other raw exports present but not read by any Python loader**: `data/collected/FYP data(manual) - Daily weather data.csv`, `- NDVI-EVI.csv`, `- Sentinal.csv`, `- soil.csv`, `- Geospatial data.csv`, `- FAOSTAT_Data.csv`, `- real all datas.csv`. These are referenced only as citation text in report/figure-generation scripts (`generate_figures.py`, `generate_interim_docx.py`, `final_report_content.py`), never via `pd.read_csv` — they appear to be the original exports that were manually merged (outside the codebase) into `onion_unique_per_key.csv`.

### 2.2 All 32 features — exact sourcing

Canonical list defined in `src/config.py` L36-61 (`WEATHER_FEATURES` 9, `SATELLITE_FEATURES` 11, `HISTORICAL_FEATURES` 5, `SOIL_FEATURES` 4, `INTERACTION_FEATURES` 3 = 32 total). Table below shows sourcing under the **real path** (`load_collected_data()`, `src/data_loader.py`), the path actually exercised when `DATA_VARIANT=real`.

| # | Feature | Sourcing type | Evidence (`src/data_loader.py`) |
|---|---|---|---|
| 1 | `season_avg_temp` | Aggregate — mean of monthly `temperature_c` | L194 `avg_temp = float(temp.mean())`; L201 |
| 2 | `season_total_rainfall` | Aggregate — sum of monthly `rainfall` | L202 `round(float(rain.sum()), 3)` |
| 3 | `season_avg_humidity` | Aggregate — mean of monthly `humidity_pct` | L203 `round(float(hum.mean()), 3)` |
| 4 | `season_avg_solar_rad` | **Hardcoded constant** `18.0` | L204 `'season_avg_solar_rad': 18.0,  # not measured → constant` |
| 5 | `growing_degree_days` | Derived formula from temp | L205 `clip(temp - 10.0, 0, None).sum() * 30.0` |
| 6 | `heat_stress_days` | Derived aggregate — count of months with temp > 32°C | L206 `int((temp > 32.0).sum())` |
| 7 | `drought_index_spi` | Derived post-hoc — z-score of seasonal rainfall vs (District,Season) group mean/std | L207 (placeholder `np.nan`), computed at L237-239 |
| 8 | `temp_range` | Derived — `temp.max() - temp.min()` | L208 |
| 9 | `max_daily_rainfall` | Aggregate — `rain.max()` | L209 |
| 10 | `season_mean_ndvi` | Aggregate — mean of monthly `ndvi_i` | L211 |
| 11 | `season_max_ndvi` | Aggregate — `ndvi.max()` | L212 |
| 12 | `season_min_ndvi` | Aggregate — `ndvi.min()` | L213 |
| 13 | `ndvi_std` | Aggregate — `ndvi.std(ddof=0)` | L214 |
| 14 | `ndvi_anomaly` | Derived post-hoc — NDVI minus its (District,Season) group mean | L215 (placeholder), computed at L235-236 |
| 15 | `time_to_peak_ndvi` | Derived — `(month_of_peak - first_month) * 30` | L192-193, L216 |
| 16 | `ndvi_growth_rate` | Derived — slope of `np.polyfit(order, ndvi, 1)` | L191, L217 |
| 17 | `season_mean_evi` | Aggregate — mean of monthly `evi_i` | L218 |
| 18 | `season_mean_ndwi` | **Hardcoded constant** `0.1` | L219 `'season_mean_ndwi': 0.1,  # not measured → constant` |
| 19 | `season_mean_lst_day` | Algebraic proxy — `avg_temp + 6.0` ("LST ≈ air temp + ~6°C") | L220 |
| 20 | `season_mean_lst_night` | Algebraic proxy — `avg_temp − 6.0` | L221 |
| 21 | `prev_season_yield` | Derived — `shift(1)` of target within (District,Season) group | L228 (placeholder), L246 |
| 22 | `prev_year_yield` | Derived — identical `shift(1)` computation (no distinct year-vs-season lag logic implemented) | L247 |
| 23 | `yield_3yr_avg` | Derived — `shift(1).rolling(3, min_periods=1).mean()` | L248 |
| 24 | `season_indicator` | Derived flag — `1 if season=='Yala' else 0` | L199 |
| 25 | `extent_prev_season` | **Hardcoded constant** — `fillna(400.0)` | L229 (placeholder), L251 `# DCS extent not in file` |
| 26 | `soil_ph` | Aggregate + unit rescale — mean of `ph_0_5cm` ÷ 10 (SoilGrids stores ×10) | L223 |
| 27 | `organic_carbon` | **Hardcoded constant** — `fillna(1.8)` | L224 (placeholder), L250 `# SoilGrids soc not in file` |
| 28 | `clay_pct` | Aggregate + rescale — mean of `clay_0_5cm` ÷ 10 | L225 |
| 29 | `sand_pct` | Aggregate + rescale — mean of `sand_0_5cm` ÷ 10 | L226 |
| 30 | `rainfall_x_ndvi` | Algebraic — `season_total_rainfall * season_mean_ndvi` | L253 |
| 31 | `temp_x_humidity` | Algebraic — `season_avg_temp * season_avg_humidity` | L254 |
| 32 | `ndvi_x_lst` | Algebraic — `season_mean_ndvi * season_mean_lst_day` | L255 |

Any residual NaNs (e.g. first-year lag rows) are **median-filled** at L258-263. This exact tiering (measured / derived / algebraic / constant) is independently re-encoded in `src/xai/grounding.py` (L93-135) as the basis for the Explanation Reliability Index (§4).

**Synthetic path** (`generate_synthetic_data()`, L39-130): every one of the 32 features is drawn from `rng.normal`/`rng.uniform` calls parameterised per-district (L44-49, L76-107) — none are loaded from a real file. The 3 interaction features (L120-122) and the 3 historical-yield features (L112-118) are algebraic/derived from the simulated values, same as the real path.

### 2.3 Dataset variants

| | Synthetic | Real (collected) |
|---|---|---|
| Generated/loaded by | `generate_synthetic_data()`, `src/data_loader.py` L39-130 | `load_collected_data()`, `src/data_loader.py` L161-272 |
| Raw input | None (pure simulation) | `data/collected/FYP data(manual) - onion_unique_per_key.csv` — **124 monthly rows** |
| Districts | 4: `Matale, Anuradhapura, Polonnaruwa, Jaffna` (L44-49, 53) — a subset of `config.DISTRICTS`, which also lists `Kurunegala` (real-only) | 4: `Anuradhapura, Kurunegala, Matale, Polonnaruwa` (typo `Polannaruwa` in source, fixed via `DISTRICT_FIXES` L158) |
| Seasons | Both `Yala` and `Maha` | **`Yala` only** — no `Maha` rows exist in the source file |
| Years | 2004–2023 (L54, `range(2004, 2024)`) | 2019–2025 (7 years; printed at L270-271) |
| Seasonal-grain row count | **136 rows** after `dropna()` (verified: `data/synthetic/synthetic_dataset.csv` = 137 lines incl. header) | **28 rows** = 4 districts × 7 years × 1 season (verified: `data/collected/processed_real_seasonal.csv` = 29 lines incl. header) |
| Feature-engineered copy used for training | `data/processed/integrated_dataset.csv` (137 lines = 136 rows, verified) | `data/processed_real/integrated_dataset.csv` (29 lines = 28 rows, verified) |
| Provenance caveat | N/A | **The "real" source file itself is a blend**: its `source` column shows **74 rows tagged `real`, 50 rows tagged `synthetic`** (verified by direct read of the CSV). `load_collected_data()` does not filter on this column — it prints the value-counts as a log line (L178) but aggregates all 124 rows regardless of provenance. So the pipeline's "real" dataset variant is ~60% genuinely-measured, ~40% synthetic-sourced rows, silently blended before seasonal aggregation. |

Variant is selected via the `DATA_VARIANT` env var (`src/config.py` L12, default `'synthetic'`; set to `'real'` by `main.py --real`), which redirects `MODELS_DIR`/`RESULTS_DIR`/`PROCESSED_DIR`/plot dirs to `*_real`-suffixed paths (`config.py` L15-20).

---

## 3. Models

### 3.1 Every model trained/compared

| Model(s) | File | Training/eval protocol |
|---|---|---|
| RandomForest, XGBoost, SVR | `src/ml_models.py` | Inner `GridSearchCV` + `TimeSeriesSplit` on `*_FAST` grids (`config.py` L89-91); outer Leave-One-Year-Out (LOYO) via `_loyo_predictions`. XGBoost adds `monotone_constraints` forcing non-decreasing yield in NDVI/EVI. |
| Symbolic Regression | `src/symbolic.py` (`train_symbolic_regression`, L54-108) | `gplearn.genetic.SymbolicRegressor` restricted to ≤5 features (SHAP top-5 if available, else `PREFERRED_FEATURES` L24-43); same LOYO protocol, reusing `ml_models._loyo_predictions`. |
| Physics-Residual Hybrid (`PhysResidual`) | `src/physics_residual.py` (`train_physics_residual`, L123-187) | Two-stage: hand-coded FAO-33/GDD mechanistic backbone + RandomForest on the residual. Also evaluates a `backbone`-only (mechanistic-only) ablation. |
| LSTM, BiLSTM, 1D-CNN, CNN-LSTM Hybrid | `src/dl_models.py` (`train_all_dl_models`, L257-366) | Keras/TensorFlow, LOYO-CV, `EarlyStopping` + `ReduceLROnPlateau`, epochs capped at `SYNTHETIC_MODE_DL_EPOCHS=50` regardless of variant. |
| StackMean, StackInvRMSE, StackConvex | `src/stacking.py` (`run_stacking`, L145-187) | Combines existing `oof_*.json` predictions via nested LOYO weight-fitting (weights fit on train years only); does not train a new base learner. |
| Ablation study (data-source contribution, not a served model) | `src/ablation.py` (`run_ablation_study`, L54-107) | XGBoost-only, 6 feature-source subsets. |

Dead configuration found: `config.py` L64-86 defines full-size `RF_PARAMS`/`XGB_PARAMS`/`SVR_PARAMS` grids — a repo-wide search shows these are never imported anywhere; only the `*_FAST` grids (L89-91) are actually used.

### 3.2 Model selection ("best")

`src/evaluator.py` : `generate_final_comparison()` (L196-240): loads every `oof_*.json`, builds `model_comparison.csv` **sorted descending by R²** (L215), and crowns row 0 as best (L224, `best = comparison.iloc[0]`) — **R² is the sole selection criterion**, written to `best_model_metrics.json` (L231-233).

**Selected-best-model vs. actually-served-model discrepancy**: `src/api.py` : `_load_state()` (L286-329) reads `best_model_metrics.json` but its `candidates` dict only recognizes `XGBoost`, `RandomForest`, `SVR` (L295-299): `name = metrics.get('Model') if metrics.get('Model') in candidates else None` (L300). On the real-data variant, the evaluator's crowned best is `PhysResidual`, which is **not** in `candidates` — so `name` falls back to `None` and the API instead serves whichever of XGBoost→RandomForest→SVR has a saved `.pkl` artefact first (L301-305). **The live API never serves the model the evaluator calls "best" for the real-data variant.**

### 3.3 Reported performance — exact values from output files

**`outputs/results/model_comparison.csv` (synthetic, n=136):**

| Model | RMSE | MAE | R2 | MAPE |
|---|---|---|---|---|
| RandomForest | 2.0677 | 1.6824 | **0.8421** | 24.68 |
| SymbolicRegression | 2.0944 | 1.6572 | 0.8380 | 23.01 |
| XGBoost | 2.3030 | 1.8596 | 0.8041 | 26.59 |
| SVR | 2.8676 | 2.2984 | 0.6963 | 33.81 |
| CNN | 4.4423 | 3.6005 | 0.2711 | 35.49 |
| CNN_LSTM_Hybrid | 4.9434 | 3.9557 | 0.0974 | 36.59 |
| BiLSTM | 5.1006 | 4.0954 | 0.0391 | 66.27 |
| LSTM | 5.1478 | 4.2112 | 0.0212 | 64.92 |

Best (`outputs/results/best_model_metrics.json`): **RandomForest, R²=0.8421**. (PhysResidual and stacking were not run for the synthetic variant — no corresponding `oof_*.json` exists in `outputs/results/`.)

**`outputs/results_real/model_comparison.csv` (real, n=28):**

| Model | RMSE | MAE | R2 | MAPE |
|---|---|---|---|---|
| PhysResidual | 3.9021 | 3.3497 | **0.0908** | 23.32 |
| RandomForest | 4.0506 | 3.3932 | 0.0203 | 23.44 |
| XGBoost | 4.0677 | 3.4392 | 0.0120 | 23.76 |
| SVR | 4.1684 | 3.4836 | −0.0375 | 24.55 |
| StackConvex | 4.3237 | 3.6222 | −0.1162 | 24.36 |
| StackInvRMSE | 4.3261 | 3.6694 | −0.1175 | 23.28 |
| BiLSTM | 4.5186 | 3.6261 | −0.2192 | 23.33 |
| SymbolicRegression | 4.5823 | 3.9126 | −0.2538 | 27.19 |
| StackMean | 5.0621 | 4.2961 | −0.5301 | 25.39 |
| LSTM | 7.3132 | 5.7093 | −2.1935 | 33.30 |
| CNN_LSTM_Hybrid | 11.6126 | 10.8517 | −7.0521 | 64.47 |
| CNN | 11.6973 | 10.7711 | −7.1700 | 62.91 |

Best (`outputs/results_real/best_model_metrics.json`): **PhysResidual, R²=0.0908** — on real data, **no model explains meaningful yield variance**; 8 of 12 models have negative R² (worse than predicting the mean).

**Ablation (`ablation_results.csv`, XGBoost, data-source subsets):**

| Experiment | N_features | Synthetic R2 | Real R2 |
|---|---|---|---|
| A_Weather_only | 9 | 0.2561 | −0.8044 |
| B_Satellite_only | 11 | 0.8015 | −0.6662 |
| C_Historical_only | 5 | 0.4708 | −0.8741 |
| D_Soil_only | 4 | −0.4078 | −0.2567 |
| E_Weather+Satellite | 20 | 0.8094 | −0.9158 |
| F_All_features | 32 | 0.8286 | −0.0819 |

**Physics-residual detail** (`outputs/results_real/physics_residual.json`): calibration `a=18.9828, b=−4.3576`; hybrid R²=0.0908 vs. mechanistic-backbone-only R²=−0.2221 vs. plain RandomForest R²=0.0203 — the hybrid beats both its own backbone and plain RF, but explanatory power is still near zero. Note in the file itself: `heat_stress_days` is 0 across all real Yala rows, so the heat term of the mechanistic formula is inert.

**Stacking detail** (`outputs/results_real/stacking_summary.json`): `forecast_combination_puzzle`: *"learned convex blend beats the equal-weight mean (puzzle does NOT hold here)"* — StackConvex R²=−0.1162 vs. StackMean R²=−0.5301. StackConvex weights concentrate on `physresidual` (0.3987) and `xgboost` (0.2711), with `cnn` weighted 0.0.

**Top SHAP features** (`feature_importance.json`): Synthetic top-3: `ndvi_x_lst` (2.185), `season_min_ndvi` (0.677), `season_mean_ndvi` (0.577). Real top-3: `temp_x_humidity` (1.404), `season_mean_evi` (0.484), `drought_index_spi` (0.148).

### 3.4 Uncertainty quantification — split conformal prediction

**File**: `src/conformal.py` : `compute_conformal(alpha=0.1)` (L23-58). Computes, per model, the LOYO out-of-fold absolute-residual quantile `q = quantile(|residuals|, level, method='higher')` where `level = min(1, ceil((n+1)(1−α))/n)`, then reports empirical coverage = fraction of residuals ≤ q. Target coverage = 0.9.

| Model | Synthetic q (±MT/Ha) | Synthetic coverage (n=136) | Real q (±MT/Ha) | Real coverage (n=28) |
|---|---|---|---|---|
| RandomForest | 3.398 | 0.919 | 7.451 | 1.0 |
| XGBoost | 3.935 | 0.919 | 8.025 | 1.0 |
| SVR | 4.887 | 0.919 | 7.967 | 1.0 |
| SymbolicRegression | 3.660 | 0.919 | 8.734 | 1.0 |
| PhysResidual | — (not run) | — | 6.852 | 1.0 |
| CNN | 7.403 | 0.919 | 19.114 | 1.0 |
| LSTM | 8.608 | 0.919 | 17.284 | 1.0 |
| BiLSTM | 8.572 | 0.919 | 10.951 | 1.0 |
| CNN_LSTM_Hybrid | 8.256 | 0.919 | 21.863 | 1.0 |

On the real variant (n=28), coverage clamps to 1.0 for every model — the level formula's `min(1.0, …)` clamp effectively uses the maximum residual as the quantile at this small sample size, producing very wide but not sharply informative intervals (e.g. CNN ±19.1 MT/Ha against yields in the ~8–24 MT/Ha range).

---

## 4. Explainability / XAI Layer

| Method | File : function | What it computes | Output |
|---|---|---|---|
| SHAP (dataset-level) | `src/explainer.py` : `run_shap_analysis()` (L44-106) | `shap.TreeExplainer` on the best *tree* model, `mean_abs_shap` per feature, ranks top 15 | `outputs/results{_variant}/feature_importance.json`, plots |
| SHAP (per-request, live) | `src/api.py` (`run_prediction`, ~L398-409) | Same TreeExplainer, computed on the single request's feature vector | Inline in `/predict` response (`shap_values`) — not persisted |
| Symbolic Regression | `src/symbolic.py` : `train_symbolic_regression()` (L54-108) | `gplearn` genetic program over ≤5 features, LOYO-evaluated, converted to a readable equation | `outputs/results{_variant}/symbolic_equation.json`/`.txt`. Real-variant equation features: `drought_index_spi, prev_year_yield, rainfall_x_ndvi, season_mean_evi, temp_x_humidity` |
| Explanation Stability | `src/xai/stability.py` : `get_stability_scores()` (L163-218) | Per feature: `1 − normalized_IQR` of SHAP importance across 7 LOYO refits (real variant); global coefficient = mean pairwise Spearman ρ between fold importance vectors | `outputs/results{_variant}/explanation_stability.json` |
| Explanation Consensus | `src/xai/consensus.py` : `get_consensus_scores()` (L60-109) | Agreement count (0–3) across 3 "voters": SHAP top-10, permutation-importance top-10, symbolic-equation membership; `consensus_j = votes/3` | `outputs/results{_variant}/explanation_consensus.json` |
| Feature Grounding | `src/xai/grounding.py` : `GROUNDING_REGISTRY` (L93-135, static) + `get_grounding_scores()` (L148-158) | **Not computed from data** — a hand-curated lookup table classifying each feature's provenance tier (1.00 measured → 0.05 constant proxy), built by manual inspection of `data_loader.py` | `outputs/results{_variant}/feature_grounding.json` |
| Explanation Reliability Index (ERI) | `src/xai/eri.py` : `compute_eri()` (L58-89), `weight_sensitivity_sweep()` (L92-142) | `ERI_j = (stability_j + grounding_j + consensus_j)/3` per feature; aggregate `ERI = Σ(|SHAP_j|·ERI_j)/Σ|SHAP_j|`; sensitivity sweep grids the 3 weights over 66 combinations | `outputs/results{_variant}/eri.json` |
| Chat/RAG context assembly | `src/explanation_context.py` : `get_prediction_context()` (L69-113) | Not a numeric XAI method — keyword-based intent extraction (`extract_intent`, L57-64, no NLU model) + repackaging of the current prediction, top-5 SHAP features, CI, and 5-year yield history into an LLM prompt context | Consumed by `POST /api/chat` |
| Ablation (data-source contribution) | `src/ablation.py` : `run_ablation_study()` | Model/data-source contribution study, not a per-feature explanation method | `outputs/results{_variant}/ablation_results.csv`; **not exposed via any API endpoint** |
| Orchestration | `src/xai/run_xai.py` : `main()` (L35-99) | Runs grounding → LOYO diagnostics → stability → consensus → ERI in sequence, offline (`python -m src.xai.run_xai`), separate from the API's live per-request SHAP/ERI | Writes all 4 JSON files |

**Reported values**: dataset-level ERI = **0.7434 (synthetic)**, **0.6219 (real)**. Real-variant `explanation_stability_coefficient` = **0.7501** (n_folds=7). Real-variant ERI weight-sensitivity sweep: of 66 weight combinations, **64 (96.97%) produce a different top-5 ranking than the equal-weight baseline**, with 32 distinct top-5 sets — the composite ranking is highly sensitive to the (arbitrary) 1/3-1/3-1/3 weighting choice, a finding explicitly present in `eri.json` itself.

### XAI endpoints and frontend consumption

| Artifact | API route | Called by dashboard? |
|---|---|---|
| SHAP top-15 (dataset) | `GET /feature-importance` | **No caller in `dashboard/`** |
| SHAP (per-request) | inline in `POST /predict` | Yes — `explain/page.tsx`, `ReliabilityWaterfall.tsx` |
| Symbolic equation | `GET /equation` | **No caller in `dashboard/`** |
| Stability | `GET /stability` | **No caller in `dashboard/`** |
| Consensus | `GET /consensus` | **No caller in `dashboard/`** |
| Grounding | no dedicated route | N/A (read in-process only, by `eri.py`) |
| ERI (dataset-level) | `GET /explanation-reliability` | **No caller in `dashboard/`** |
| ERI (per-request) | inline in `POST /predict` (`eri`, `per_feature_eri`) | Yes — `explain/page.tsx` (§6), `ReliabilityWaterfall.tsx` |
| Chat/RAG context | `POST /api/chat` | Yes — `ChatAssistant.tsx` |

**Confirmed via repo-wide grep** of `dashboard/` for the literal path strings `feature-importance`, `/equation`, `explanation-reliability`, `/stability`, `/consensus`, `models/compare`: zero matches in every case. Five of the seven XAI computation methods (SHAP-dataset, symbolic, stability, consensus, ERI-dataset) have working GET endpoints that are never called by the deployed frontend; ERI and per-request SHAP only reach the UI because they're embedded as fields inside the `/predict` response, not through their own dedicated routes.

---

## 5. API (`src/api.py`, 953 lines)

The file's own module docstring (L1-16) lists 12 routes but **omits `/equation`**, which exists in code at L490 — confirmed by a full route scan (`@app.route`, 13 matches).

| Method | Path | Handler line | Returns | Called from dashboard? |
|---|---|---|---|---|
| GET | `/health` | 356 | `{status, model, service}` | Yes — `getHealth()` |
| POST | `/predict` | 465 | Full prediction payload (see below) | Yes — `predictYield()`, used on 4 pages |
| GET | `/models/compare` | 472 | `model_comparison.csv` as JSON records | **No** |
| GET | `/feature-importance` | 481 | `feature_importance.json` (SHAP top-15) | **No** |
| GET | `/equation` | 490 | `symbolic_equation.json` | **No** |
| GET | `/explanation-reliability` | 500 | `eri.json` (dataset-level) | **No** |
| GET | `/stability` | 513 | `explanation_stability.json` | **No** |
| GET | `/consensus` | 526 | `explanation_consensus.json` | **No** |
| GET | `/context` | 539 | 32 resolved feature values + provenance for (district,season,year) | Yes — `getContext()`, used by `predict/page.tsx` |
| GET | `/baseline` | 643 | Historical yield stats for (district,season) | Yes — `getBaseline()`, used by `predict/`, `recommend/` pages |
| GET | `/districts` | 655 | `{districts, seasons, years, variant, source}` | Yes — `getDistricts()` |
| POST | `/api/chat` | 761 | `{answer, context_used}` | Yes — `sendChatMessage()`, `ChatAssistant.tsx` |
| POST | `/api/recommend` | 884 | `{recommendation, context_used}` | Yes — `getRecommendation()`, `recommend/page.tsx` |

**`/predict` response shape** (L432-456): `district, season, year, predicted_yield_MT_per_Ha, confidence_lower, confidence_upper, confidence, shap_values, model, model_r2, interval_method, interval_coverage, feature_sources, resolved_features, data_completeness, eri, per_feature_eri`. The `eri`/`per_feature_eri` fields are computed live per-request (L430: `compute_eri(shap_dict)`), distinct from the dataset-level `eri.json` served by `/explanation-reliability`.

**Flagged — endpoints with no caller (6 of 13)**: `/models/compare`, `/feature-importance`, `/equation`, `/explanation-reliability`, `/stability`, `/consensus`. These appear intended for direct inspection / FYP report tooling rather than the live dashboard.

**Flagged — dead code inside `api.py`**: a `# TODO: Implement PostgreSQL storage here` comment at L458-460 — no persistence layer exists; every `/predict` call is stateless.

**Frontend calls with no matching endpoint**: none found. Every exported call in `dashboard/lib/api.ts` (`sendChatMessage`, `getRecommendation`, `getHealth`, `getDistricts`, `getContext`, `getBaseline`, `predictYield`) matches a real route.

**Port mismatch note**: `dashboard/lib/api.ts` defaults `API_BASE_URL` to `http://localhost:5050` (inline comment: "macOS port 5000 is AirPlay, so Flask runs on 5050"), while `src/api.py` (L952) defaults its own `PORT` env var to `'5000'` — the two only agree if `PORT=5050` is set when launching the Flask app.

---

## 6. Dashboard / Frontend

### 6.1 Routes (`dashboard/app/`)

| Route file | What it does | API call(s) |
|---|---|---|
| `app/page.tsx` | Root — unconditionally `redirect("/en")`, no UI | none |
| `app/layout.tsx` | Root HTML shell, font, static metadata | none |
| `app/[locale]/layout.tsx` | Validates locale, deep-merges `messages/{locale}.json` over `messages/en.json` (so any missing key silently falls back to English), wraps children in `NextIntlClientProvider` + `Navbar` | none (static message imports) |
| `app/[locale]/page.tsx` (Home) | Fetches districts/seasons/years, batch-predicts every district for the latest year, renders `DistrictMap`, district-focus card, 4 `StatCard`s | `getDistricts()` → `GET /districts`; `predictYieldsForAllDistricts()` → N × `POST /predict` |
| `app/[locale]/predict/page.tsx` | Main input form: district/season/year + optional extent/last-yield + `AdvancedOverrides`; submits farmer-known fields only, backend resolves the rest | `getDistricts()`, `getContext()` → `GET /context`, `getBaseline()` → `GET /baseline`, `predictYield()` → `POST /predict` |
| `app/[locale]/explain/page.tsx` | Reads the last prediction from `localStorage`, renders SHAP explanation as a diverging bar list ("Simple" view) or the new `ReliabilityWaterfall` chart ("Reliability" view), computes an ERI badge from `prediction.eri` (thresholds `<0.4` low / `<0.7` medium / else high) | No direct network call — reads `PredictResponse` written to `localStorage` by `predict/page.tsx` |
| `app/[locale]/recommend/page.tsx` | Rule-based risk/strategy cards from SHAP sign/magnitude, plus an AI-generated recommendation banner; what-if comparison against real historical `baseline.max` | `getBaseline()` → `GET /baseline`; `getRecommendation()` → `POST /api/recommend` |

### 6.2 Components (`dashboard/components/`)

| Component | Purpose |
|---|---|
| `AdvancedOverrides.tsx` | Collapsible "Tier C" expert-override panel for soil/NDVI/weather inputs, with min/max validation |
| `ChatAssistant.tsx` | Posts questions to `POST /api/chat`, renders the answer + an expandable "grounded in this data" section |
| `DistrictMap.tsx` | Interactive Leaflet map of 4 target districts (static GeoJSON), colored by predicted-yield category |
| `FieldInputCard.tsx` | "Tier A" district/season/year + extent/last-yield form |
| `KnownDataPanel.tsx` | Displays ~28 system-supplied ("Tier B") feature values with provenance badges (`user`/`district_season_mean`/`global_mean`/etc.) |
| `LanguageSwitcher.tsx` | Locale switcher, persists choice to `localStorage`, rewrites URL locale segment |
| `Navbar.tsx` | Top nav with locale-aware links + embedded `LanguageSwitcher` |
| `PredictionResultCard.tsx` | Displays confidence interval, R²-derived reliability note, baseline comparison, data-completeness note |
| `StatCard.tsx` | Generic stat tile used on the homepage |
| `charts/ReliabilityWaterfall.tsx` (new, untracked) | Hand-rolled SVG bar chart encoding each SHAP factor's magnitude as bar length and its per-feature ERI as opacity/hatch overlay |

### 6.3 i18n

Locale files: `dashboard/messages/en.json`, `si.json`, `ta.json`. Programmatic leaf-key diff (all three files parsed and compared, not eyeballed):

| | en | si | ta |
|---|---|---|---|
| Leaf-key count | 236 | 219 | 219 |

**si.json and ta.json are each missing exactly the same 17 keys**, the entire `chat.*` namespace:
`chat.title, chat.subtitle, chat.placeholder, chat.send, chat.emptyState, chat.needsPrediction, chat.thinking, chat.error, chat.notConfigured, chat.basedOnData, chat.hidePrediction, chat.showPrediction, chat.dataPrediction, chat.dataConfidence, chat.dataTopFactors, chat.dataHistory, chat.dataBaseline`

No extra/orphan keys exist in si.json or ta.json relative to en.json. Because `app/[locale]/layout.tsx` deep-merges each locale over the English fallback, this does not crash or show raw keys — `ChatAssistant` silently renders in English for Sinhala/Tamil users. Root cause: commit `a2c3a73` ("added rag, chat") added the `chat` namespace to `en.json` but only added unrelated keys (`recommend.aiTitle` etc.) to `si.json`/`ta.json` in the same commit — the `chat` namespace was never translated. By contrast, the newer `explain.reliability.*` keys (from the current uncommitted diff) are fully translated identically in all three locales.

### 6.4 Mock/placeholder data

`dashboard/lib/sample-api.ts` (24 lines) is the only mock-data file anywhere in `dashboard/` (confirmed via repo-wide grep for `sample-api|predictYieldMock|USE_MOCK`). It is used only when `NEXT_PUBLIC_USE_MOCK=true` (default is unset/false, so the real `/predict` endpoint is hit by default). Its hardcoded `shap_values` keys — `rainfall, temperature, humidity, soil_moisture, soil_ph` — **do not match the real 32-feature schema** (real names are `season_total_rainfall`, `season_avg_temp`, `season_avg_humidity`, etc., and there is no `soil_moisture` feature at all); if the mock were ever enabled, `convertSHAPToExplanation`'s substring-matching would bucket `soil_moisture` into a generic "other" category. This mock file was not updated alongside the current feature schema.

---

## 7. What Is Not Yet Implemented / Known Gaps

| Gap | Evidence |
|---|---|
| `load_real_data()` (7-file raw pipeline) is dead code | `data/raw/` contains only `.gitkeep`; `check_data_availability()` always reports all 7 files missing, so this function path is never exercised |
| Full-size hyperparameter grids (`RF_PARAMS`, `XGB_PARAMS`, `SVR_PARAMS`, `config.py` L64-86) are defined but never used | Repo-wide search finds no import of these symbols; only `*_FAST` variants are used |
| `/ablation` (data-source contribution study) has no API endpoint | `src/ablation.py` output (`ablation_results.csv`) is never served — no matching route in `src/api.py` |
| PostgreSQL persistence for predictions is a stub | `src/api.py` L458-460: `# TODO: Implement PostgreSQL storage here` — every `/predict` call is stateless, nothing is stored |
| 6 of 13 API endpoints are orphaned from the live dashboard | `/models/compare`, `/feature-importance`, `/equation`, `/explanation-reliability`, `/stability`, `/consensus` — confirmed zero callers via repo-wide grep of `dashboard/` |
| Evaluator's "best" model is not always the model actually served | `src/api.py` `_load_state()` `candidates` only recognizes XGBoost/RandomForest/SVR; real-variant best (`PhysResidual`) is silently skipped in favor of a fallback |
| `frontend/` is a legacy, superseded directory | Last touched 2026-06-18 (commits `b2b8a82`, `6f7c154`), now contains only `next-env.d.ts`/`node_modules` while `dashboard/` is the actively developed app |
| si/ta locales missing the entire `chat.*` translation namespace (17 keys) | Verified via programmatic key diff, §6.3; silently falls back to English via `mergeMessages`, not a crash but a real localization gap |
| `dashboard/lib/sample-api.ts` mock data is stale vs. the real feature schema | Mock `shap_values` keys (`soil_moisture`, etc.) don't exist in the real 32-feature list; only activates behind `NEXT_PUBLIC_USE_MOCK=true` |
| 4 features are hardcoded constants, not measured data, in the real-data pipeline | `season_avg_solar_rad` (18.0), `season_mean_ndwi` (0.1), `organic_carbon` (1.8), `extent_prev_season` (400.0) — all independently confirmed at grounding tier 0.05 ("constant_proxy") in `src/xai/grounding.py`; without consulting the grounding registry or ERI output, these could be mistaken for measured values in downstream reporting |
| On real data, no model reaches usable predictive power | Best real-variant R² is 0.0908 (PhysResidual); the FYP's own `TARGET_R2 = 0.75` (`config.py` L109) is met only on the synthetic variant (`final_summary.txt`: "Reaches target R² > 0.75? YES" synthetic / "NO" real) |
| "Real" dataset variant is itself a real/synthetic blend | `onion_unique_per_key.csv`'s `source` column: 74 rows `real`, 50 rows `synthetic`, merged without filtering by `load_collected_data()` |
| Real-variant conformal intervals are near-degenerate | Empirical coverage clamps to 1.0 for every model at n=28 (small-sample quantile-level clamp in `conformal.py`), meaning the reported "calibration" doesn't discriminate between models at this sample size |

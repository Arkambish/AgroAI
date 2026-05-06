# 06 — Results and Interpretation

This is what's actually in `outputs/` after running `python main.py` on the synthetic data, and what every number means.

## Where to find each result

```
outputs/
├── models/                           ← saved trained models
│   ├── rf_best.pkl                   → Random Forest
│   ├── xgb_best.pkl                  → XGBoost
│   ├── svr_best.pkl + svr_scaler.pkl → SVR + its scaler
│   ├── lstm_best.keras               → LSTM
│   ├── bilstm_best.keras             → BiLSTM
│   ├── cnn_best.keras                → CNN
│   └── cnn_lstm_hybrid_best.keras    → Hybrid (NOVEL)
│
├── plots/
│   ├── eda/                          ← exploratory plots
│   │   ├── yield_distribution.png
│   │   ├── yield_timeseries.png
│   │   ├── correlation_heatmap.png
│   │   ├── feature_distributions.png
│   │   ├── seasonal_comparison.png
│   │   └── district_comparison.png
│   ├── training/                     ← DL learning curves
│   │   ├── lstm_learning_curve.png
│   │   ├── bilstm_learning_curve.png
│   │   ├── cnn_learning_curve.png
│   │   └── cnn_lstm_learning_curve.png
│   └── results/                      ← model-comparison & SHAP
│       ├── actual_vs_pred_*.png      (one per model — 7 files)
│       ├── residuals_*.png           (RF, XGB, SVR)
│       ├── feature_importance_*.png  (RF, XGB)
│       ├── model_comparison_bar.png  ← the key chart
│       ├── ablation_comparison.png   ← the key ablation chart
│       ├── shap_summary.png          ← the key SHAP chart
│       ├── shap_importance.png
│       └── shap_dependence_<top>.png
│
└── results/
    ├── model_comparison.csv          ← the leaderboard
    ├── ablation_results.csv          ← 6-experiment ablation
    ├── feature_importance.json       ← top-15 SHAP features
    ├── best_model_metrics.json       ← used by the API
    ├── final_summary.txt             ← the 9 research findings
    └── oof_*.json                    ← per-model fold-by-fold predictions
```

---

## The leaderboard: `model_comparison.csv`

Sorted by R² descending. Synthetic-data run:

```
Model            RMSE    MAE     R²      MAPE     Train_Time_s   Parameters
RandomForest     2.067   1.681   0.842   24.66    4.78           -
XGBoost          2.162   1.756   0.827   25.52    4.01           -
SVR              2.868   2.298   0.696   33.81    0.07           -
CNN              4.442   3.601   0.271   35.49    51.19          8,577
CNN_LSTM_Hybrid  4.943   3.956   0.097   36.59    83.66          44,929
BiLSTM           5.101   4.095   0.039   66.27    72.58          77,601
LSTM             5.148   4.211   0.021   64.92    51.74          30,625
```

### How to read this

- **RMSE = 2.07 MT/Ha** for Random Forest means: on average, predictions miss the actual yield by ~2 metric tons per hectare. Given yields range from ~5 to ~24 MT/Ha, that's ~10% relative error — reasonable.
- **R² = 0.842** means RF explains 84.2% of the variance in yield. Excellent for synthetic data.
- **MAPE = 24.66%** is high because some Maha-season Jaffna yields are small (~5 MT/Ha) — small denominators inflate percentage errors. RMSE/MAE/R² are more reliable metrics for this regime.
- **Training time** for tree models is seconds; DL models took ~50–80s due to LOYO-CV with 17 folds × 50 epochs each.

### Why DL underperforms here

These DL R² values (0.02–0.27) look terrible. They are — but for an expected reason: **152 rows is genuinely too few for these architectures**. LSTMs typically need thousands of sequences. The synthetic data is simple enough that tree models nail it instantly.

This is itself a **finding**: with current data availability for big onion, classical ML is sufficient and superior. Once Sharuja delivers real monthly NASA POWER + MODIS data over 20+ years, the DL models should improve substantially.

---

## The ablation: `ablation_results.csv`

```
Experiment              N_features  RMSE    MAE     R²
A_Weather_only          9           4.488   3.674   0.256
B_Satellite_only        11          2.318   1.867   0.802
C_Historical_only       5           3.785   3.041   0.471
D_Soil_only             4           6.174   5.036   -0.408
E_Weather+Satellite     20          2.272   1.794   0.809
F_All_features          32          2.154   1.747   0.829
```

### Interpretation

- **B (Satellite only) gets R² = 0.802** — almost as good as F (full model). Satellite imagery alone explains ~80% of yield variance. **Powerful finding.**
- **A (Weather only) gets R² = 0.256** — weather is much less predictive than satellite for synthetic data. (In real data, with proper monthly resolution, weather may matter more — TBD.)
- **D (Soil only) gets R² = -0.408** — soil features alone are *worse than predicting the mean*. Soil is necessary but not sufficient context.
- **C (Historical only) gets R² = 0.471** — last year's yield is a moderate predictor. The Persistence model (predict same as last year) actually works decently in agriculture.
- **E (Weather + Satellite) = 0.809**, only marginally better than B alone (0.802). **Adding weather to satellite barely improves over satellite alone** — they're correlated.
- **F (All) = 0.829**, only +2.0 pp over E. The other features (historical, soil, interactions) add small but real value.

### The headline claim for the report

> *"In the ablation study, satellite-derived vegetation indices alone achieve R² = 0.80, while weather features alone achieve only R² = 0.26. Adding satellite to weather yields a +55 percentage-point improvement, establishing satellite imagery as the most informative single data source for big onion yield prediction in Sri Lanka."*

This sentence justifies the engineering investment in Google Earth Engine integration.

---

## Per-model plots

For every model, three plots are generated. Use them to judge model quality at a glance.

### `actual_vs_pred_<model>.png`

A scatter plot. X-axis = actual yield, Y-axis = predicted yield. The dashed line is `y = x` (perfect prediction). Points are coloured by district.

**What to look for:**
- Tight cluster around the line → good model.
- Systematic bias (all points above or below line) → model is consistently over/under-predicting.
- Cluster splits by colour → model performs differently across districts.
- Outliers far from the line → specific years/districts the model struggles with.

### `residuals_<model>.png` (ML models only)

Residual = actual − predicted. X-axis = predicted yield, Y-axis = residual. Horizontal line at 0.

**What to look for:**
- Residuals randomly scattered around 0 → model is well-calibrated.
- Residuals form a pattern (e.g. growing as predicted increases) → model has bias.
- Red dots (|residual| > 2σ) flag outlier predictions.

### `feature_importance_<model>.png` (RF and XGBoost)

Horizontal bar chart of the top 15 features, ranked by built-in importance (mean decrease in impurity for RF, gain for XGB).

---

## SHAP plots

### `shap_summary.png` — the most informative single plot

A "beeswarm" plot. Each row is a feature. Each dot is one prediction (so 152 dots per row).
- Horizontal position = SHAP value (how much that feature pushed the prediction higher/lower than the dataset average).
- Colour = the feature's value (red = high, blue = low).

**Reading it:**
- Features at the top are most important overall.
- A red cluster on the right: high feature values → push prediction up. (E.g. high NDVI → higher yield.)
- A red cluster on the left: high feature values → push prediction down.
- Wide spread = strong influence (sign and magnitude).

### `shap_importance.png`

Bar chart of mean |SHAP value| per feature, top 15. Equivalent to the beeswarm rank but quicker to read.

### `shap_dependence_<top_feature>.png`

For the most-important feature, plot its **value** (X-axis) against its **SHAP value** (Y-axis). Reveals non-linear dependencies.

For example, if the top feature is `ndvi_x_lst` and the dependence plot looks like a U-shape, that means moderate values of NDVI×LST are *bad* and extreme values are *good* — a non-linear relationship that linear models would miss.

---

## The summary text: `final_summary.txt`

```
BIG ONION YIELD PREDICTION — RESEARCH FINDINGS
============================================================

1. Best performing model: RandomForest with R²=0.842, RMSE=2.067 MT/Ha
2. Does DL outperform ML? NO (Wilcoxon p=0.0000)
3. Does CNN-LSTM hybrid beat standalone CNN/LSTM? NO
4. Top 3 most important features: ndvi_x_lst, season_min_ndvi, season_mean_ndvi
5. Ablation Δ R² (Weather → Weather+Satellite): +55.33 percentage points
6. RMSE Yala=2.114, Maha=2.018
7. Easiest district to predict: Matale (R²=0.878)
8. Hardest district to predict: Anuradhapura (R²=0.756)
9. Reaches target R² > 0.75? YES
```

### Each finding, interpreted

1. **RF is best** — expected for tabular ML on small data.
2. **DL does NOT beat ML** with Wilcoxon p < 0.0001 — *statistically significant* finding. With 152 rows, classical ML wins. (Does not generalise; with real data this may flip.)
3. **Hybrid does NOT beat standalone CNN** — also expected with synthetic data, since the hybrid has more parameters to overfit. The hypothesis remains valid for real data.
4. **Top features** confirm the role of vegetation indices. `ndvi_x_lst` (NDVI × Land Surface Temperature interaction) is #1 — captures combined "greenness × heat stress" effect.
5. **Ablation** shows satellite is the heavy hitter.
6. **Yala vs Maha RMSE** are similar (2.11 vs 2.02), suggesting the model handles both seasons comparably.
7. **Matale easiest, Anuradhapura hardest** — interesting, since both are dry-zone. Worth investigating if real data confirms this.
8. **Target R² > 0.75 achieved** by RF on synthetic data ✓

---

## What changes when real data arrives

Things that should improve:

- **DL models** will benefit from real monthly weather sequences (5 timesteps × 4 vars → maybe 12-16 timesteps × 8 vars). With more variation per row, LSTMs have more to learn.
- **Hybrid model** should outperform standalone DL once season-specific patterns become learnable.
- **R² values** may go down somewhat (synthetic data has clean linear correlations; real data is noisier).
- **Target R² > 0.75** may or may not be achievable for the very first run; tuning hyperparameters (`MAX_EPOCHS=200`, full grid in `RF_PARAMS`) will be needed.

Things that probably won't change:

- **Satellite > weather** in importance — empirical results from rice/maize literature consistently show this.
- **RF and XGBoost will be top contenders** — tabular ML truths persist.
- **Methodology** — LOYO-CV, ablation, SHAP, statistical tests — all valid for both synthetic and real data.

---

## Reading the OOF JSON files

`outputs/results/oof_<model>.json` contains the full per-row predictions:

```json
{
  "model_name": "RandomForest",
  "metrics": {
    "Model": "RandomForest",
    "RMSE": 2.0668,
    "MAE": 1.6812,
    "R2": 0.8422,
    "MAPE": 24.66,
    ...
  },
  "rows": [
    {"Year": 2005, "Season": "Maha", "District": "Matale",
     "actual": 8.41, "predicted": 7.93},
    ...
  ]
}
```

Useful for:
- Custom analysis (e.g. "which years did RF struggle most?").
- Pulling specific predictions for the final report.
- Building error visualisations in your own notebooks.

The evaluator already uses these to compute statistical tests and per-district R².

---

## What to put in the FYP final report

A suggested order of figures and tables:

| Figure / Table | Source |
|---|---|
| Table 1: Data sources | [01_PROBLEM_AND_DATA.md](01_PROBLEM_AND_DATA.md) |
| Table 2: Model architectures (parameters, layers) | [04_MODELS_EXPLAINED.md](04_MODELS_EXPLAINED.md) summary table |
| Figure 1: Yield distribution | `outputs/plots/eda/yield_distribution.png` |
| Figure 2: Yield over time | `outputs/plots/eda/yield_timeseries.png` |
| Figure 3: Correlation heatmap | `outputs/plots/eda/correlation_heatmap.png` |
| Table 3: Model comparison (LOYO-CV) | `outputs/results/model_comparison.csv` |
| Figure 4: Model comparison bar chart | `outputs/plots/results/model_comparison_bar.png` |
| Figure 5: Best-model actual vs predicted | `outputs/plots/results/actual_vs_pred_rf.png` |
| Figure 6: Hybrid CNN-LSTM architecture diagram | (your own diagram from [04_MODELS_EXPLAINED.md](04_MODELS_EXPLAINED.md)) |
| Table 4: Ablation results | `outputs/results/ablation_results.csv` |
| Figure 7: Ablation comparison | `outputs/plots/results/ablation_comparison.png` |
| Figure 8: SHAP summary (beeswarm) | `outputs/plots/results/shap_summary.png` |
| Figure 9: Top SHAP feature dependence | `outputs/plots/results/shap_dependence_<top>.png` |
| Table 5: Per-district & seasonal accuracy | extracted from `final_summary.txt` |
| Statistical test results (Wilcoxon, paired t) | from terminal output / `final_summary.txt` |

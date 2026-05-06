# 05 — Novelty and Research Contribution

This document is what you'll lean on when writing the introduction, methodology, and discussion sections of your final report. It explains *what is new* about this work and *why it matters*.

## The research gap (what doesn't exist yet)

Look at what the literature has done for crop yield prediction:

| What's been done | Where |
|---|---|
| Rice (paddy) yield prediction in Sri Lanka using ML | Amarasinghe et al. 2024 (cited in your proposal) |
| Maize/wheat yield prediction with LSTM | Many papers, mostly US/EU |
| CNN on satellite RGB images for yield | Several papers, mostly cash crops |
| Deep learning surveys in agriculture | Kamilaris & Prenafeta-Boldú 2018 |

What **doesn't** exist yet:

1. **No big-onion yield prediction system** for Sri Lanka — the proposal explicitly says this.
2. **No vegetable yield prediction** under the data-scarcity conditions typical of Sri Lankan horticulture (no crop-cutting surveys → ~150 data points, not thousands).
3. **No bimodal-monsoon-aware architectures** — most models are built for single-season cash crops.
4. **No quantitative ablation** showing how much each data source contributes to vegetable yield prediction in Sri Lanka.

This research targets all four gaps.

---

## Three concrete novelties

### Novelty 1: First ML vs DL comparison for vegetable yield prediction with scarce data

**The question this research answers:**
> "When you have only ~150 records spread across 4 districts and 20 years, does deep learning beat classical machine learning for crop yield prediction?"

**Why this is a contribution:**
The conventional wisdom from imagenet-style problems is "more parameters + more data = better". But in agriculture, especially for non-cash crops in developing countries, you don't have ImageNet-scale data. You have a few decades of patchy government surveys. The field needs *guidance* on whether DL is even worth the complexity in this regime.

By running 3 ML models and 4 DL models on the same data with the same evaluation protocol (LOYO-CV) and the same statistical tests (Wilcoxon, paired t), this research gives a defensible answer.

**Expected contribution to the field:**
- If ML wins: "for vegetable yield prediction in data-scarce contexts, classical ML is sufficient" — a useful negative result that saves practitioners from wasting effort on DL.
- If DL wins: "DL methods, when carefully regularised and architecturally tuned to bimodal seasonality, transcend the data-scarcity barrier" — a positive result that opens up DL adoption.

Either way, **the comparison itself is the contribution.**

### Novelty 2: A hybrid CNN-LSTM architecture for the bimodal Yala/Maha monsoon system

**The architectural innovation:**

Most multi-modal yield models look like this:

```
Concatenate(satellite_features, weather_features)
   ↓
Dense layers
   ↓
Yield prediction
```

This loses the spatial structure of satellite data and the temporal structure of weather data. Both get flattened into one vector.

**This research's hybrid:**

```
Satellite ─→ CNN branch ─┐
                          │
Weather  ─→ LSTM branch ─┼─→ Concatenate ─→ Dense ─→ Yield
                          │
Season   ─────────────────┘  (Yala=1, Maha=0)
```

The novelty is **threefold**:

1. **Preserves modality structure** before merging. The CNN branch learns vegetation patterns; the LSTM branch learns weather temporal dynamics. Each modality is processed by a network architecture *suited to its data type*.

2. **Explicit season indicator injection.** The Yala/Maha indicator is concatenated *after* the heavy feature extraction, just before the final dense layers. This means:
   - The CNN/LSTM branches learn season-agnostic feature extractors (better data efficiency).
   - The final dense layers learn season-specific yield baselines.
   - It's effectively soft multi-task learning in one model — the model "knows" which season's pattern to apply.

3. **Calibrated for scarce data.** The architecture has only ~45,000 parameters (compare: a typical image classifier has millions). Combined with 20% dropout and early stopping, it's regularised hard. This is engineered for the FYP data regime, not borrowed from a different domain.

**Why this matters:**
Bimodal monsoon agriculture is the norm in tropical Asia (Sri Lanka, India, Bangladesh, parts of SE Asia). An architecture that natively handles bimodal seasonality is reusable across the region for many crops, not just big onion.

### Novelty 3: Quantitative ablation across 6 data-source configurations

**The ablation experiments:**

| Code | Features | What it tests |
|---|---|---|
| A | Weather only | Weather baseline |
| B | Satellite only | Satellite baseline |
| C | Historical (lagged yield) only | Memory baseline |
| D | Soil only | Soil baseline |
| E | Weather + Satellite | Two-source synergy |
| F | All sources combined | Full multi-source value |

For each, run LOYO-CV → record RMSE, MAE, R² → produce a comparison plot.

**Why this is novel for vegetable yield in Sri Lanka:**

No published study has decomposed the contribution of each data source for big onion in Sri Lanka. Your supervisor and field practitioners can use these ablation numbers to answer:

- "If I can only afford one data stream, which one gives me the most yield-prediction power?"
- "Is satellite data worth the engineering cost for this use case?"
- "How much does soil data add once I already have weather + satellite?"

**Synthetic-data preview of findings:**

```
A_Weather_only        R² = 0.256
B_Satellite_only      R² = 0.802
C_Historical_only     R² = 0.471
D_Soil_only           R² = -0.408   ← negative R² means worse than predicting the mean
E_Weather+Satellite   R² = 0.809
F_All_features        R² = 0.829
```

The headline: **satellite data alone explains ~80% of yield variance**, weather alone explains only ~26%, and adding weather to satellite barely improves R² (0.802 → 0.809). This suggests satellite imagery is the **single highest-value data stream** for big onion yield prediction.

(These are synthetic-data numbers — the magnitudes will shift with real data, but the methodology is the contribution.)

---

## Methodological rigour (also a contribution)

These are practices borrowed from rigorous ML research that elevate the FYP:

### Leave-One-Year-Out CV
Most yield-prediction papers split data randomly into train/test. That's wrong for time-series — it leaks future information. LOYO-CV is the time-series-correct evaluation. Using it explicitly addresses a well-known methodological flaw in the agricultural ML literature.

### Statistical significance testing
Reporting "RF gets R² = 0.842, XGB gets R² = 0.827" without a statistical test doesn't tell you if the difference is real or noise. The Wilcoxon signed-rank test on paired residuals does. Including this elevates the analysis from "leaderboard reporting" to "scientific comparison".

### SHAP for interpretability
Showing R² is not enough — agricultural stakeholders want to know *why* the model thinks yield will be 16 MT/Ha. SHAP gives per-prediction and per-feature attributions. Including SHAP plots in your final report addresses the well-known "black-box problem" critique that often hits ML-in-agriculture papers.

### Reproducibility
Every random seed is fixed (`RANDOM_STATE=42`). Every artefact is saved (models, plots, CSVs, JSONs). Anyone can re-run `python main.py` and get the same numbers. This satisfies the FAIR data / reproducible science principles your supervisor will appreciate.

---

## How this fits the FYP report structure

Map this research to standard chapters:

| Chapter | What goes there |
|---|---|
| **Introduction** | Problem from [01_PROBLEM_AND_DATA.md](01_PROBLEM_AND_DATA.md) — onion imports, lack of survey methodology, food security |
| **Literature Review** | Existing rice/maize/wheat yield prediction work; identify the gaps listed at the top of this file |
| **Methodology** | Pipeline architecture from [03_PIPELINE_WALKTHROUGH.md](03_PIPELINE_WALKTHROUGH.md); model architectures from [04_MODELS_EXPLAINED.md](04_MODELS_EXPLAINED.md); LOYO-CV evaluation protocol |
| **Experimental Setup** | Data sources table; hyperparameter grids; evaluation metrics; statistical tests |
| **Results** | Model comparison table + bar chart; per-district R²; Yala vs Maha analysis |
| **Discussion** | Three novelty sections from above; ablation findings (which data source matters most?); SHAP interpretation; ML-vs-DL verdict for this data regime |
| **Conclusion** | Best model + R² achieved; whether target R² > 0.75 was met; recommendations for stakeholders; future work |
| **Appendix** | Configuration files; full LOYO fold-by-fold tables; all 17 generated plots |

---

## Talking points for your supervisor / viva

When asked "what's novel about your research?":

1. **"This is the first published machine learning system for big onion yield prediction in Sri Lanka."**
2. **"I've designed a hybrid CNN-LSTM architecture that natively handles the bimodal Yala/Maha monsoon system, by injecting a season indicator into the final dense layers — letting the model learn season-specific yield baselines while sharing earlier feature extraction across seasons."**
3. **"I've conducted a rigorous comparison of three classical ML and four deep learning models using Leave-One-Year-Out Cross-Validation and statistical significance tests, answering whether DL is worth the complexity in data-scarce vegetable yield prediction."**
4. **"I've decomposed the contribution of each data source via a six-experiment ablation study, providing actionable guidance to practitioners about which data streams are essential vs redundant."**

When asked "why does it matter?":

1. **Food security**: Sri Lanka is import-dependent for big onion. Better forecasts → better import planning → more stable prices → more reliable food supply.
2. **Foreign exchange**: Big onion imports cost foreign exchange. Better forecasts → smarter imports → savings.
3. **Farmer welfare**: Early forecasts help farmers price decisions and resource allocation.
4. **Methodology transferable**: The bimodal-monsoon architecture works for other tropical Asian crops in similar climate regimes.

When asked "how does this differ from existing work?":

- "Amarasinghe et al. (2024) did rice yield in Sri Lanka — but rice has crop-cutting surveys with thousands of data points; vegetables don't. My work targets the data-scarce vegetable regime."
- "Kamilaris & Prenafeta-Boldú (2018) surveyed deep learning in agriculture broadly — but didn't address bimodal monsoon systems or vegetable-specific challenges."
- "Most yield-prediction CNN-LSTM hybrids are designed for cash crops with monthly satellite mosaics; mine is engineered for the data scarcity and seasonal bimodality of South Asian non-cash crops."

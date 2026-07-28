# Final Presentation Guide — AgroAI Big Onion Yield Prediction
### Arkam B.H.M. (214019K) · ML/DL Modelling Component
**Written as a hand-over briefing from a senior researcher. Assumes you know nothing. Read top to bottom once, then use Part 9 (Q&A) as drill material.**

---

## How to use this document

| Part | What it gives you | Read when |
|---|---|---|
| 1 | The 60-second pitch + your exact scope | First, memorise |
| 2 | The domain (onions, Yala/Maha, why anyone cares) | Day 1 |
| 3 | The data — what you REALLY have | Day 1 (most important part) |
| 4 | ML/DL from zero — every concept you must be able to define | Day 2 |
| 5 | The 12 models, plain English | Day 2–3 |
| 6 | How the system was built, file by file | Day 3 |
| 7 | Research gaps + the four novelties | Day 4 (this is your marks) |
| 8 | Results, and how to present a low R² honestly | Day 4 |
| 9 | Advantages, disadvantages, limitations | Day 5 |
| 10 | Slide-by-slide deck plan with timings | Day 5 |
| 11 | Demo script | Day 6 |
| 12 | Q&A bank — 40 questions with answers | Day 6–7, drill out loud |
| 13 | Optional fixes that would strengthen you before the viva | If you have time |
| 14 | Commands + vocabulary cheat sheet | Keep open during demo |

**A warning before you start.** Some of the older files in `docs/` (`00_OVERVIEW.md`, `05_NOVELTY_AND_RESEARCH.md`) were written when the project ran on *synthetic* (fake, computer-generated) data. They quote R² values like 0.80 and claim "~150 data points" and Yala-**and**-Maha coverage. **Those numbers are not your real results.** Your real results are in `outputs/results_real/`, and they are much weaker. This guide is written against the real numbers. If an evaluator opens an old doc and quotes 0.80 at you, say: *"That figure is from the synthetic-data development phase used to validate the pipeline end-to-end. The real-data results are in outputs/results_real, and I report those."* Never defend the synthetic numbers as if they were real. That is the single fastest way to lose credibility.

---

# PART 1 — The project in 60 seconds

## The one-paragraph pitch (memorise this)

> "Sri Lanka consumes about 200,000 metric tons of big onion a year and imports a large share of it, which costs foreign exchange. Unlike paddy, there is no crop-cutting survey for onions — yield is estimated by agricultural officers by eye, and only *after* harvest. Our project builds an AI system that forecasts district-level big onion yield in metric tons per hectare *before* harvest, using weather data, satellite vegetation indices, soil properties and historical yields. My component is the modelling research: I built and compared twelve models — classical machine learning, deep learning, a symbolic-regression equation, a physics-informed hybrid, and three ensemble combiners — under a strict Leave-One-Year-Out evaluation protocol, and I quantified how much each data source actually contributes."

## Your exact scope (know the boundary)

| Member | Component | Owns |
|---|---|---|
| **Arkam B.H.M. (you)** | **ML/DL modelling pipeline + Flask serving API** | `src/`, `main.py`, `outputs/`, all model results, the research findings |
| Sharuja B. | Data engineering + feature engineering | `data/collected/`, data acquisition from GEE/NASA POWER, the 32 features |
| Shathurya P. | Dashboard + visualisation + decision support | `dashboard/` (Next.js), the map, the UI |

**If asked about data collection**, you say: *"Sharuja owns acquisition and integration; I consume the integrated dataset she produces and I own everything from feature matrix to model to served prediction."* Don't claim her work. Don't disown it either — you must be able to *describe* it (Part 3).

**Your research question**, stated formally:

> *Under severe data scarcity (n = 28 seasonal observations), do deep learning architectures outperform classical machine learning for vegetable yield prediction, and can domain knowledge — encoded as a mechanistic agronomic backbone — recover predictive skill that pure statistical learning cannot?*

That second half is your strongest card. Hold it.

---

# PART 2 — The domain

You must sound like you understand onions, not just Python.

## The crop

- **Big onion** = *Allium cepa*. A bulb crop. Introduced to Sri Lanka by the British in 1855; commercial cultivation scaled up under the Department of Agriculture in the 1950s.
- Grown mainly in **Matale (especially Dambulla — over 50% of national production), Anuradhapura, Polonnaruwa, Kurunegala, Puttalam, Jaffna**.
- **Yield** is measured in **metric tons per hectare (MT/Ha)**. Your data ranges from **8.5 to 24.1 MT/Ha**, averaging **16.4**.

## The two seasons (this matters a lot)

Sri Lanka has a **bimodal** (two-peaked) monsoon system. Agriculture is organised into two seasons:

| Season | Months | Character for onion |
|---|---|---|
| **Yala** | April – August | The **main** onion season. Drier conditions in the dry/intermediate zones suit bulb formation. |
| **Maha** | October – March | **Off-season** for onion. Wetter, lower yields — roughly 3,400 kg/acre vs 8,800 kg/acre peak-season in Matale. |

> **Critical fact about your project: your real dataset contains Yala only.** All 28 rows are Yala. There is no Maha data. This has consequences for your novelty claims that you MUST get ahead of — see Part 7 and the Q&A. Do not let an evaluator discover this before you say it.

## Why the problem exists

- For **paddy**, the Department of Census and Statistics (DCS) runs **crop-cutting surveys** across 4,000+ tracts per season. Thousands of ground-truth measurements. Rich data.
- For **vegetables including big onion**, there is **no equivalent methodology**. Yield is estimated by consultation with agricultural officers and visual assessment.
- Result: estimates are (a) subjective, (b) inconsistent, and (c) **only available at or after harvest** — too late for import policy, price stabilisation, or farmer planning.

## Who would use the output

Department of Census and Statistics · Department of Agriculture · agricultural policy planners deciding import quotas · district agricultural officers · farmers making pricing and resource decisions.

## The value chain of a good forecast

Early forecast → government sizes onion imports correctly → farmers aren't undercut by a glut of cheap imports, and consumers aren't hit by a shortage → prices stabilise → foreign exchange saved.

---

# PART 3 — The data (the most important part of this guide)

**Every hard question you get will trace back to the data. Know these numbers cold.**

## What you actually have

```
28 rows × 32 features + 1 target
```

| Property | Value |
|---|---|
| Observations (rows) | **28** |
| Districts | **4** — Anuradhapura, Kurunegala, Matale, Polonnaruwa |
| Years | **7** — 2019 to 2025 |
| Seasons | **Yala only** (Maha absent) |
| Structure | 4 districts × 7 years = 28 |
| Target | `Avg_Yield_MT_per_Ha` |
| Target mean / std | **16.39 / 4.09 MT/Ha** |
| Target range | 8.50 → 24.06 MT/Ha |
| Features | **32** |

Read that again: **32 features, 28 rows.** In statistics this is called the **p > n regime** — more predictors than observations. It is the single hardest setting in supervised learning. Any model can fit 28 points perfectly with 32 knobs and learn nothing real. This one fact explains essentially every result you got.

## Where the data came from (Sharuja's pipeline — know it)

| Data type | Source | What it gives |
|---|---|---|
| Historical yield | **DCS** Big Onion Survey Reports | District-level extent, production, yield by season |
| National production | **FAOSTAT** | Country-level onion production from 1961 |
| Daily weather | **NASA POWER API** | Rainfall, min/max temperature, solar radiation, humidity |
| Gridded rainfall | **CHIRPS** via Google Earth Engine | 5 km resolution rainfall |
| Vegetation indices | **MODIS MOD13Q1** via GEE | NDVI, EVI at 250 m, 16-day composites |
| High-res imagery | **Sentinel-2** via GEE | 10 m multispectral → NDVI, NDWI |
| Land surface temp | **MODIS LST** | Day/night surface temperature |
| Soil | **SoilGrids** | pH, organic carbon, clay %, sand % at 250 m |

Raw files live in `data/collected/`. The daily weather file alone has ~9,500 rows; NDVI/EVI ~3,570; Sentinel ~2,930. These get **aggregated to the seasonal grain** — one row per district-season-year — which is how 22,000 raw rows collapse into 28 modelling rows.

**Anticipate this question:** *"You have 9,500 weather rows, why only 28 samples?"*
**Answer:** *"Because the target variable is only observed once per district per season. Yield is a seasonal aggregate. The 9,500 daily weather records are compressed into nine seasonal weather features per row — they increase feature quality, not sample count. My sample size is bounded by the number of yield observations DCS publishes, which is four districts over seven years."*

## The 32 features, grouped

Defined in [src/config.py:36-61](src/config.py#L36-L61).

**Weather (9)** — `season_avg_temp`, `season_total_rainfall`, `season_avg_humidity`, `season_avg_solar_rad`, `growing_degree_days`, `heat_stress_days`, `drought_index_spi`, `temp_range`, `max_daily_rainfall`

**Satellite (11)** — `season_mean_ndvi`, `season_max_ndvi`, `season_min_ndvi`, `ndvi_std`, `ndvi_anomaly`, `time_to_peak_ndvi`, `ndvi_growth_rate`, `season_mean_evi`, `season_mean_ndwi`, `season_mean_lst_day`, `season_mean_lst_night`

**Historical (5)** — `prev_season_yield`, `prev_year_yield`, `yield_3yr_avg`, `season_indicator`, `extent_prev_season`

**Soil (4)** — `soil_ph`, `organic_carbon`, `clay_pct`, `sand_pct`

**Interaction (3)** — `rainfall_x_ndvi`, `temp_x_humidity`, `ndvi_x_lst`

### Terms you must be able to define on the spot

- **NDVI** (Normalised Difference Vegetation Index) = (NIR − Red)/(NIR + Red). Healthy green vegetation reflects near-infrared strongly and absorbs red. Ranges −1 to +1; dense healthy crop ≈ 0.6–0.9. It is a **greenness proxy** — more green biomass usually means more yield.
- **EVI** (Enhanced Vegetation Index) — like NDVI but corrected for atmospheric effects and soil background; doesn't saturate as fast over dense canopy.
- **NDWI** (Normalised Difference Water Index) — water content of vegetation.
- **LST** (Land Surface Temperature) — skin temperature of the ground from satellite thermal bands, day and night.
- **GDD** (Growing Degree Days) = Σ over days of max(0, (Tmax+Tmin)/2 − T_base). Accumulated **thermal time** — how much heat the crop has banked. Crops develop on thermal time, not calendar time.
- **SPI** (Standardised Precipitation Index) — a drought index. Rainfall expressed as a standard-normal anomaly. **Negative = drier than normal**, positive = wetter. SPI < −1 is a meaningful drought.
- **Heat stress days** — count of days above a crop-damaging threshold (>34 °C here).
- **Interaction feature** — a feature made by multiplying two others, e.g. `temp_x_humidity`. Tree models can approximate interactions but explicitly supplying them helps when data is tiny.

### ⚠️ The data problem you must disclose yourself

I checked your real dataset. **Six of your 32 features are constant** — they have exactly one unique value across all 28 rows, so they carry **zero information**:

| Feature | Unique values | Consequence |
|---|---|---|
| `season_indicator` | 1 (always Yala) | **Kills the season-injection novelty on real data** |
| `heat_stress_days` | 1 (always 0) | The heat-stress term in your physics backbone is inert |
| `organic_carbon` | 1 | Dead |
| `season_avg_solar_rad` | 1 | Dead |
| `season_mean_ndwi` | 1 | Dead |
| `extent_prev_season` | 1 | Dead |

Plus `soil_ph` has 3 unique values and `clay_pct`/`sand_pct` have 4 — i.e. soil is essentially a **district ID in disguise** (one soil profile per district), not a real varying covariate.

**Say this first, before anyone finds it.** Framed correctly it is a *finding*, not a failure:

> *"A feature audit showed six of my 32 features are constant on the real data — most importantly the season indicator, because we only obtained Yala records. That means the seasonal-injection mechanism in my hybrid architecture is inert on real data and can only be validated on the synthetic benchmark. I report this explicitly rather than letting the architecture take credit for a mechanism it never exercised. The soil block is also effectively a district identifier at one profile per district, so its apparent predictive value in the ablation is really district-level information, not soil chemistry."*

That sentence, delivered voluntarily, will move you up a grade band. It is exactly what a careful researcher does.

---

# PART 4 — Machine learning from zero

Skip nothing here. You will be asked to define these.

## 4.1 What supervised learning is

You have a table. Each row is an example. Some columns are **features** (inputs, `X`) — weather, NDVI, soil. One column is the **target** (output, `y`) — yield.

A model is a function `f` such that `f(X) ≈ y`. **Training** = automatically adjusting the model's internal numbers (**parameters**) so its predictions on examples where you know the answer are as close as possible to the truth. **Prediction** = applying the trained `f` to a new row where you don't know `y`.

Because your target is a **continuous number** (16.4 MT/Ha), this is **regression**, not classification.

## 4.2 The loss function

The model needs a score for "how wrong am I". Standard for regression is **Mean Squared Error**:

```
MSE = (1/n) · Σ (actual − predicted)²
```

Squaring makes errors positive and punishes big misses disproportionately. Training = finding parameters that minimise this.

## 4.3 Overfitting — the concept your whole project revolves around

**Overfitting** = the model memorises the training examples, including their noise, instead of learning the underlying rule. It looks brilliant on data it has seen and fails on data it hasn't.

Analogy: a student who memorises past exam papers word-for-word scores 100% on those papers and fails a new paper with the same syllabus.

**Overfitting risk scales with (model complexity) ÷ (amount of data).** You have 28 rows. Your CNN-LSTM hybrid has **44,929 parameters**. That is roughly **1,600 tunable numbers per training example**. It can memorise the 28 rows perfectly and has essentially no pressure to learn anything general. **This is why your deep models scored worst.** That is not a bug in your code — it is a textbook, predictable, and *reportable* consequence of the data regime, and it is literally the thing your research question asked about.

**Defences against overfitting used in this project:**
- **Regularisation** — penalties on large parameter values (XGBoost's `reg_alpha`, `reg_lambda`).
- **Dropout** — during training, randomly switch off 20% of neurons each step so the network can't rely on any single path. Set at `DROPOUT_RATE = 0.2`.
- **Early stopping** — stop training as soon as validation error stops improving (`EARLY_STOPPING_PATIENCE = 20`).
- **Constraints** — the convex stacking weights are forced to be non-negative and sum to 1, which is a very strong regulariser.
- **Injecting prior knowledge** — the physics backbone. This is the big one; see Part 7.

## 4.4 How you measure success

All computed in [src/ml_models.py:78-92](src/ml_models.py#L78-L92).

| Metric | Formula | Meaning | Good |
|---|---|---|---|
| **RMSE** | √(mean of squared errors) | Typical error, in MT/Ha. Punishes large misses. | Lower |
| **MAE** | mean of \|errors\| | Typical error, in MT/Ha. Treats all misses equally. | Lower |
| **MAPE** | mean of \|error/actual\| × 100 | Typical error as a **percentage** | Lower |
| **R²** | 1 − (SS_residual / SS_total) | Fraction of variance explained | Higher, max 1 |

**R² is the one they'll grill you on.** Understand it precisely:

- **R² = 1.0** → perfect prediction.
- **R² = 0.0** → your model is exactly as good as always guessing the average yield (16.39).
- **R² < 0** → **your model is worse than guessing the average.** Negative R² is legal and it means the model is actively harmful.

For your data, the mean-predictor has RMSE = **4.092**. So R² = 1 − (your_RMSE / 4.092)².

## 4.5 Cross-validation, and why yours is special

**Naive approach:** shuffle rows randomly, train on 80%, test on 20%.

**Why that is WRONG for your project:** your data is a **time series**. A random split can put 2024 in the training set and 2021 in the test set — the model would be using the *future* to predict the *past*. That is **data leakage**, and it inflates results dishonestly. A large fraction of published agricultural-ML papers do exactly this, which is why their reported R² values are unrealistically high.

**Your approach: Leave-One-Year-Out Cross-Validation (LOYO-CV).** Implemented at [src/ml_models.py:44-58](src/ml_models.py#L44-L58).

```
for each year Y in {2019 … 2025}:
    train the model on ALL OTHER years
    predict the 4 district rows belonging to year Y
```

Seven folds. Every row eventually gets one prediction made by a model that **never saw that year**. Those are called **out-of-fold (OOF) predictions**, saved to `outputs/results_real/oof_*.json`. All reported metrics are computed on OOF predictions — never on training data.

**This is a genuine methodological strength and you should say so out loud:**

> *"Every number I report is out-of-fold under Leave-One-Year-Out cross-validation. No model ever sees the year it is scored on. This is a stricter protocol than the random train/test splits used in most of the crop-yield literature, and it is part of why my R² values look modest next to published figures — I'm reporting honest generalisation error, not in-sample fit."*

**Nested CV** — for hyperparameter tuning there's an *inner* loop (`GridSearchCV` with `TimeSeriesSplit`) inside the *outer* LOYO loop, so tuning decisions also don't leak. Same principle applied to the stacking weights ([src/stacking.py:113-133](src/stacking.py#L113-L133)): for each held-out year, blend weights are fitted **only on the other years**.

## 4.6 Deep learning specifics

- **Neural network** — layers of simple units. Each unit computes a weighted sum of its inputs, adds a bias, and applies a non-linear **activation function** (e.g. ReLU: `max(0, x)`). Stacking layers lets the network represent complex functions.
- **Backpropagation** — the algorithm that computes how much each parameter contributed to the error, so it can be nudged in the right direction.
- **Epoch** — one complete pass through the training data. You cap at `MAX_EPOCHS = 200` with early stopping.
- **Batch size** — how many examples are processed before parameters update. Yours is 16 — on 24 training rows that's essentially two batches per epoch.
- **Learning rate** — step size for each update. Yours is 0.001.
- **LSTM** (Long Short-Term Memory) — a recurrent layer built for **sequences**. It keeps an internal memory ("cell state") and has learned **gates** deciding what to remember, forget, and output. Designed to capture long-range temporal dependence — e.g. "drought in month 2 damaged the bulb even though month 4 looked fine."
- **CNN** (Convolutional Neural Network) — slides small learned filters across the input to detect **local patterns** regardless of position. In 1D over a season, a filter might learn "a sharp NDVI drop over three consecutive timesteps."
- **Bidirectional LSTM** — runs an LSTM forwards and backwards over the sequence and concatenates. Useful when the whole sequence is available at once (which it is — you're forecasting after the season's observations, not streaming live).

---

# PART 5 — The twelve models, in plain English

Your leaderboard has 12 entries. Be able to give one sentence on each.

## Classical machine learning (3)

**1. Random Forest** ([src/ml_models.py](src/ml_models.py))
Builds hundreds of decision trees, each on a random subset of rows and columns, and averages their predictions. A decision tree asks nested yes/no questions ("is NDVI > 0.55?") and outputs the average yield of the training examples that land in each leaf. Individually trees overfit badly; averaging many decorrelated trees cancels most of that. **Robust on small data — which is why it's your best pure-ML model.**

**2. XGBoost** (Extreme Gradient Boosting)
Builds trees **sequentially**, where each new tree is trained to fix the errors the current ensemble makes. Adds explicit L1/L2 regularisation. Usually the strongest tabular model in competitions — but boosting is *greedier* than bagging, so on 28 rows it has slightly more room to overfit than RF, which is what you observe.

**3. SVR** (Support Vector Regression)
Fits a function that keeps all training points within an **ε-tube**, penalising only points outside it, while keeping the function as flat as possible. The **kernel trick** (RBF kernel) lets it fit non-linear relationships without explicitly building high-dimensional features. Needs feature scaling — hence `svr_scaler.pkl`.

## Deep learning (4)

**4. LSTM** — takes the 5-timestep monthly weather sequence, two stacked LSTM layers (64 then 32 units), dropout, dense output. 30,625 parameters.

**5. BiLSTM** — same but bidirectional. 77,601 parameters.

**6. 1D-CNN** — convolutional filters over the feature/time axis. 8,577 parameters — the smallest DL model.

**7. Hybrid CNN-LSTM with season indicator** ([src/dl_models.py:79-101](src/dl_models.py#L79-L101)) — **the architecture you designed.** 44,929 parameters.

```
Satellite features ──→ Conv1D(32) → Conv1D(64) → pool ──┐
                                                         │
Weather sequence   ──→ LSTM(64) → LSTM(32) ─────────────┼──→ Concatenate → Dense → Yield
                                                         │
Season indicator (Yala=1 / Maha=0) ─────────────────────┘
```

The three design ideas:
1. **Modality-appropriate encoders.** Satellite data has spatial/local structure → CNN. Weather has temporal structure → LSTM. Most multi-source yield models just concatenate everything into one flat vector and lose both structures.
2. **Late season injection.** The season flag is concatenated **after** feature extraction, immediately before the dense head. Intent: the CNN/LSTM branches learn *season-agnostic* extractors (better data efficiency, both seasons share them), while the final dense layers learn *season-specific* yield baselines. This is a soft form of multi-task learning in a single model.
3. **Deliberately small.** ~45k parameters with 20% dropout and early stopping, engineered for scarcity rather than borrowed from a vision backbone with millions of parameters.

> **You must volunteer the caveat:** on the real Yala-only dataset the season indicator is constant, so mechanism (2) is inert and the hybrid reduces to a two-branch multi-input network. Its real-data score reflects only mechanisms (1) and (3), on 24 training rows.

## Interpretable model (1)

**8. Symbolic Regression** ([src/symbolic.py](src/symbolic.py))
Instead of fitting parameters to a fixed structure, it **searches over the space of mathematical formulas** using genetic programming — mutating and recombining candidate equations, selecting for accuracy with a **parsimony penalty** so short formulas win ties. The output is a human-readable equation. It's given only the SHAP top-5 features so the equation stays legible.

Yours (`outputs/results_real/symbolic_equation.txt`):

```
Yield ≈ ⁴√(temp_x_humidity × prev_year_yield) + 3.251 − drought_index_spi
```

Read it out loud in the viva — it's memorable and it's agronomically sensible: **yield rises with the heat-humidity product and with last year's yield, and falls as drought deepens** (SPI negative → subtracting a negative → yield goes up in wet years). An agronomist can sanity-check this. No neural network gives you that.

## Physics-informed hybrid (1) — **your best model**

**9. PhysResidual** ([src/physics_residual.py](src/physics_residual.py))

Two stages.

**Stage 1 — a hand-coded agronomic formula with no learning at all.** It computes a dimensionless crop-suitability index from published crop-science relationships:

```
suitability = f_water × f_heat × f_gdd

f_gdd   = 1 − exp(−GDD / 1500)                        thermal time, saturating
f_water = clip(1 − 1.1 × clip(−SPI/2, 0, 1), 0, 1)    FAO-33 water response, Ky_onion ≈ 1.1
f_heat  = clip(1 − 0.03 × heat_stress_days, 0, 1)     linear heat penalty
```

This is the **multiplicative stress form** from FAO Irrigation & Drainage Paper 33 (Doorenbos & Kassam, 1979): potential yield is scaled *down* by each limiting factor independently. The constant **Ky ≈ 1.1** for onion/bulb crops is straight from that FAO paper — it is not a number you invented, and you should cite it. Only **two** parameters are then fitted, a linear calibration `yield ≈ a + b·suitability` mapping the index onto MT/Ha. On your data: **a = 18.98, b = −4.36**.

**Stage 2 — a Random Forest learns only the leftover error** `(actual − backbone)`, and the two are added back together.

**Why this is the right idea for 28 rows:** the backbone supplies structure *for free* — it costs 2 fitted parameters instead of thousands. The ML then has a smaller, better-behaved quantity to fit, so it overfits less. It is the cheapest possible way to buy prior knowledge.

## Ensemble combiners (3) — [src/stacking.py](src/stacking.py)

All three read the OOF predictions the pipeline already wrote and blend them. **No new base model is trained.** Weights are fitted under nested LOYO — fitted on training years only, applied to the held-out year.

**10. StackMean** — equal weights (1/9 each). **Zero fitted parameters, cannot overfit.** This is the anchor.
**11. StackInvRMSE** — weight each model by 1/RMSE, normalised. Better models count more.
**12. StackConvex** — solve for weights that minimise squared error **subject to wᵢ ≥ 0 and Σwᵢ = 1** (SLSQP on the simplex). The simplex constraint is a strong regulariser versus unconstrained least squares, and it can drive useless members to exactly zero.

This setup lets you test a **named result from the forecasting literature**: the **forecast-combination puzzle** (Stock & Watson 2004; Claeskens et al. 2016) — the repeated empirical finding that a simple equal-weight average often beats a cleverly-optimised blend on small samples. **Your finding: the puzzle does NOT hold here.** The learned convex blend (R² = −0.116) clearly beat the equal-weight mean (R² = −0.530), because the mean was dragged down by three catastrophically bad deep models that the convex solver correctly zeroed out (CNN weight = 0.000, hybrid = 0.005, LSTM = 0.015). That is a clean, publishable, defensible negative-of-a-negative result.

---

# PART 6 — How the system was built

## The pipeline, in execution order

Run with `python main.py --real`. Orchestrated by [main.py](main.py).

```
 1. data_loader.py        load raw CSVs → aggregate daily/16-day records to the seasonal grain
 2. preprocessor.py       clean, handle missing values, temporally align to season windows
 3. feature_engineer.py   build the 32 features + the sequence tensors for the DL models
 4. eda.py                exploratory plots (distributions, time series, correlations)
 5. ml_models.py          RF, XGBoost, SVR  — inner GridSearchCV, outer LOYO, save OOF
 6. symbolic.py           genetic-programming search for a closed-form equation
 7. physics_residual.py   FAO-33 backbone + RF on residual   ← runs after RF so it can compare
 8. dl_models.py          LSTM, BiLSTM, CNN, Hybrid CNN-LSTM — LOYO, save learning curves
 9. ablation.py           6 feature-subset experiments
10. explainer.py          SHAP attributions on the best model
11. stacking.py           3 combiners over all OOF predictions, nested LOYO
12. evaluator.py          leaderboard, Wilcoxon/paired-t tests, final_summary.txt
13. conformal.py          calibrated prediction intervals from OOF residuals
```

**Key architectural decision to point out:** every model writes its out-of-fold predictions to a shared JSON schema (`oof_<model>.json`) via `_save_oof`. That single convention is what lets stacking, conformal intervals, statistical tests and the leaderboard all be computed **once, consistently, downstream** — instead of each model reporting its own metrics its own way. Say this if asked about software design; it shows engineering judgement, not just script-writing.

## The dual-variant design

[src/config.py:12-20](src/config.py#L12-L20). A `DATA_VARIANT` environment variable switches all input/output paths:

- `python main.py` → synthetic data → `outputs/results/`, `outputs/models/`
- `python main.py --real` → real collected data → `outputs/results_real/`, `outputs/models_real/`

**Why this exists, and how to justify it:** the pipeline was developed and validated end-to-end against a synthetic generator *before* the real data was fully collected. That let the 13-stage pipeline, the LOYO protocol, and all the plotting be debugged against data with a *known* signal — if the pipeline can't recover a signal you deliberately planted, the pipeline is broken. Once real data arrived, the same code ran on it with one flag. **Frame it as a software-verification strategy, not as "we made up data."** That distinction matters enormously.

## Reproducibility

`RANDOM_STATE = 42` fixed throughout. Every artefact persisted — models (`.pkl`, `.keras`), OOF JSONs, plots, CSVs. Anyone can re-run and get identical numbers.

## Serving

`src/api.py` — a Flask REST API that loads the best saved model and serves it to Shathurya's dashboard.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check |
| `POST /predict` | Yield prediction from a feature payload |
| `GET /models/compare` | The leaderboard |
| `GET /feature-importance` | Top-15 SHAP features |
| `GET /context` | Prefill values for the form (`?district=&season=&year=`) |
| `GET /districts` | Dropdown options |

Runs on port 5050 (macOS occupies 5000 with AirPlay).

---

# PART 7 — Research gaps and novelty

**This section is where your marks live.** Examiners assess *contribution*, not accuracy.

## The gaps in the literature

| # | Gap | Evidence |
|---|---|---|
| 1 | **No ML/DL yield-prediction system exists for big onion in Sri Lanka.** | Published Sri Lankan crop-ML work is on **paddy** (Amarasinghe et al. 2024). Rice has crop-cutting surveys and thousands of records. |
| 2 | **No published treatment of vegetable yield prediction under this level of data scarcity.** | The DL-in-agriculture literature (Kamilaris & Prenafeta-Boldú 2018) is dominated by studies with hundreds-to-thousands of samples. n = 28 is a different regime and nobody has characterised it for this crop. |
| 3 | **No architecture designed for bimodal Yala/Maha seasonality.** | Most yield architectures target single-season cash crops in the US/EU. |
| 4 | **No quantitative decomposition of data-source value for Sri Lankan vegetables.** | Nobody has asked "if you can only afford one data stream, which one?" for this crop. |
| 5 | **No mechanistic/statistical hybrid for tropical bulb crops.** | Physics-residual hybrids exist for maize with APSIM (Shahhosseini et al. 2021); none for onion, none for Sri Lanka. |

## Your four novelty claims — with honest strength ratings

**Be precise about what is *invented* versus what is *first-applied*.** Claiming to invent something the literature already has is the classic FYP failure mode. Claiming a first application, with citations showing you know the parent work, is respected.

### Novelty 1 — Physics-residual hybrid for tropical bulb crops ⭐ **STRONGEST**

| | |
|---|---|
| **What's genuinely new** | First application of a mechanistic-backbone + ML-residual architecture to **Sri Lankan big onion**; a novel *in-pipeline* integration where the backbone is a lightweight closed-form FAO-33 formula rather than a full process model like APSIM. |
| **What's NOT new** | The residual-hybrid idea itself. Cite **Shahhosseini et al. (2021), Scientific Reports** — APSIM + ML residual for maize. Say this yourself. |
| **The empirical result that makes it a contribution** | Adding the two-parameter physics backbone lifted R² from **0.020 → 0.091** — a **+0.071 improvement, roughly 4.5× the plain Random Forest**, at a cost of two fitted parameters. It is the best model in the study. |
| **Why it matters** | It's a concrete, quantified demonstration that under extreme scarcity, **encoded domain knowledge buys more predictive skill than model capacity does.** That is a transferable methodological lesson for any data-scarce agricultural context. |

There's a second, subtler finding here worth stating: the **backbone alone scored R² = −0.222** — *worse than the mean*. So the mechanistic model is not a good predictor by itself; its value is entirely in **reshaping the learning problem** for the ML stage. That is a genuinely interesting result and shows you understand your own model.

### Novelty 2 — ML vs DL under extreme scarcity, rigorously tested ⭐ **STRONG**

The comparison *is* the contribution. Seven models, one protocol (LOYO), one statistical test (Wilcoxon signed-rank on paired absolute residuals).

**Result: classical ML decisively beats deep learning, Wilcoxon p < 0.0001.** Every DL model scored negative R²; the best DL model (BiLSTM, −0.219) is beaten by every ML model.

A **negative result reported with statistical support is a real contribution.** It tells practitioners in similar contexts not to burn effort on deep architectures. Present it with confidence, not apology.

### Novelty 3 — Data-source ablation ⭐ **MODERATE**

Six configurations, same LOYO protocol ([src/ablation.py](src/ablation.py), results in `outputs/results_real/ablation_results.csv`):

| Experiment | Features | R² |
|---|---|---|
| A — Weather only | 9 | −0.804 |
| B — Satellite only | 11 | −0.666 |
| C — Historical only | 5 | −0.874 |
| D — Soil only | 4 | **−0.257** ← best single source |
| E — Weather + Satellite | 20 | −0.916 |
| F — All features | 32 | **−0.082** ← best overall |

Read these honestly: **every single-source configuration is worse than predicting the mean.** The finding is *not* "satellite is the best data stream." The finding is:

> **No individual data source carries usable standalone signal at this sample size; predictive skill only emerges from the full multi-source feature set, and even then only marginally.** Note also that Weather+Satellite (E, −0.916) is *worse* than either alone — adding features without adding rows degrades performance. That is a textbook demonstration of the **curse of dimensionality**, and it directly motivates the physics-backbone approach.

And the caveat you must state: **"Soil only" scoring best among single sources is an artefact** — soil has one profile per district, so that experiment is effectively "predict yield from district identity." It is measuring between-district differences, not soil chemistry.

### Novelty 4 — Constrained stacking + forecast-combination-puzzle test ⭐ **MODERATE**

First test of the forecast-combination puzzle on Sri Lankan crop-yield data, evaluated leak-aware under nested LOYO.

**Result: the puzzle does not hold.** Learned convex blend (−0.116) beat the equal-weight mean (−0.530), because the convex solver zeroed out the catastrophic deep models. Mean weights it chose: **PhysResidual 0.399, XGBoost 0.271, BiLSTM 0.199, RF 0.045, SVR 0.039, Symbolic 0.027, LSTM 0.015, Hybrid 0.005, CNN 0.000.**

That weight vector is itself a nice result — **the constrained optimiser independently rediscovered your model ranking**, putting 67% of its mass on the top two models and ~2% on the three worst. Show this slide.

### Supporting rigour (not "novelty", but marks nonetheless)

- **Leave-One-Year-Out CV** — time-series-correct evaluation; addresses a known methodological flaw in the agricultural ML literature.
- **Wilcoxon signed-rank testing** — turns leaderboard reporting into scientific comparison.
- **SHAP** — per-feature attribution; addresses the black-box critique that routinely hits ML-in-agriculture work.
- **Conformal prediction** ([src/conformal.py](src/conformal.py)) — distribution-free calibrated intervals with a finite-sample coverage guarantee, instead of the naive ±1.96×RMSE band. **Decision-makers need an interval, not a point estimate**, and this gives one with a guarantee that holds without assuming normality.
- **Full reproducibility** — fixed seeds, every artefact persisted.

---

# PART 8 — Results, and how to present them honestly

## The leaderboard (`outputs/results_real/model_comparison.csv`)

| Rank | Model | RMSE | MAE | R² | MAPE | Params |
|---|---|---|---|---|---|---|
| **1** | **PhysResidual** | **3.902** | **3.350** | **+0.091** | **23.3%** | 2 + RF |
| 2 | RandomForest | 4.051 | 3.393 | +0.020 | 23.4% | — |
| 3 | XGBoost | 4.068 | 3.439 | +0.012 | 23.8% | — |
| 4 | SVR | 4.168 | 3.484 | −0.038 | 24.6% | — |
| 5 | StackConvex | 4.324 | 3.622 | −0.116 | 24.4% | 9 weights |
| 6 | StackInvRMSE | 4.326 | 3.669 | −0.118 | 23.3% | — |
| 7 | BiLSTM | 4.519 | 3.626 | −0.219 | 23.3% | 77,601 |
| 8 | SymbolicRegression | 4.582 | 3.913 | −0.254 | 27.2% | — |
| 9 | StackMean | 5.062 | 4.296 | −0.530 | 25.4% | 0 |
| 10 | LSTM | 7.313 | 5.709 | −2.194 | 33.3% | 30,625 |
| 11 | CNN_LSTM_Hybrid | 11.613 | 10.852 | −7.052 | 64.5% | 44,929 |
| 12 | CNN | 11.697 | 10.771 | −7.170 | 62.9% | 8,577 |

**Look at the shape of that table and say what it shows:** performance is almost perfectly **inversely ordered by parameter count.** The 2-parameter physics backbone wins; the 45,000-parameter hybrid is near-last. That is your headline finding, and it is a real one.

## The nine research findings (`final_summary.txt`)

1. Best model: **PhysResidual**, R² = 0.091, RMSE = 3.902 MT/Ha
2. Does DL outperform ML? **NO** (Wilcoxon p < 0.0001)
3. Does the CNN-LSTM hybrid beat standalone CNN/LSTM? **NO**
4. Top 3 SHAP features: **temp_x_humidity, season_mean_evi, drought_index_spi**
5. Ablation Δ R² (Weather → Weather+Satellite): **−11.1 percentage points** (adding satellite features *hurt*)
6. RMSE Yala = 3.902; **Maha = not evaluable (no Maha data)**
7. Easiest district: **Anuradhapura (R² = 0.361)**
8. Hardest district: **Kurunegala (R² = −1.183)**
9. Target R² > 0.75 reached? **NO**

## 🔴 The hard question, and your answer

They *will* ask: **"Your R² is 0.09 and your proposal targeted 0.75. Hasn't your project failed?"**

**Do not apologise. Do not mumble. Deliver this, and have the numbers ready:**

> *"The 0.75 target was set in the proposal on the assumption of a DCS-survey-scale dataset comparable to paddy. What we obtained is 28 seasonal observations — four districts over seven years, Yala only. With 32 features on 28 rows, we are in the p > n regime, and no model can reliably explain 75% of variance from 28 points. So the honest answer is: the accuracy target was not met, and I can show you exactly why.*
>
> *But 'failed' depends on the benchmark. Here are the three baselines an agronomist would actually use today:*
>
> | Baseline | RMSE | R² |
> |---|---|---|
> | Always predict the national mean | 4.092 | 0.000 |
> | Predict last year's district yield (persistence) | 4.666 | −0.300 |
> | Predict this district's historical average | 4.558 | −0.241 |
> | **My PhysResidual model** | **3.902** | **+0.091** |
>
> *My model beats all three. It is the only method in the study with positive R² — the only one that outperforms guessing. It is a 4.6% RMSE improvement over the mean and 16% over persistence, which is the method closest to current practice.*
>
> *And the research contribution was never the accuracy number. My research question was whether deep learning beats classical ML under scarcity, and whether domain knowledge can substitute for data. I answered both with statistical support: DL loses decisively at p < 0.0001, and a two-parameter FAO-33 physics backbone quadrupled R² over the same Random Forest without it. Those findings are valid regardless of the absolute accuracy level — and they're the findings a practitioner in a similar data-scarce context actually needs."*

**Then immediately pivot to what would fix it** (Part 9, "what I would do next"). Never end on the limitation.

## SHAP interpretability

`outputs/plots_real/results/shap_summary.png`, `shap_importance.png`, `shap_dependence_temp_x_humidity.png`.

**SHAP** (SHapley Additive exPlanations) comes from cooperative game theory. It answers: for *this specific prediction*, how much did each feature push the output up or down relative to the average prediction? The Shapley value averages a feature's marginal contribution over all possible orderings of features — which is why it's fair and why it's expensive to compute.

Your top features by mean |SHAP|:

| Rank | Feature | Mean \|SHAP\| |
|---|---|---|
| 1 | `temp_x_humidity` | 1.404 |
| 2 | `season_mean_evi` | 0.484 |
| 3 | `drought_index_spi` | 0.148 |

**Interpret it agronomically, don't just read the list:** the dominant driver is the **temperature × humidity interaction**, which is agronomically coherent — onion bulbs are highly sensitive to combined heat-and-humidity stress, which drives both bulb development and fungal disease pressure. Second is **EVI**, a canopy-vigour proxy. Third is the **drought index**. So the model is leaning on heat-moisture stress and canopy vigour — exactly the drivers HORDI cultivation guidelines emphasise. **This independent agreement between a data-driven attribution and published agronomy is a validity check**, and it's a good line to deliver.

Also note the concentration: feature 1 is ~3× feature 2 and ~10× feature 3. On 28 rows, the model effectively found one usable signal.

## Conformal prediction intervals

`outputs/results_real/conformal.json`. For PhysResidual at 90% target coverage: **q = ±6.85 MT/Ha**.

So the deployed forecast is *"18.2 MT/Ha, 90% interval [11.4, 25.1]"*. That's wide — about ±42% of mean yield. **Say so.** The honest framing:

> *"Conformal calibration gives me an interval with a finite-sample coverage guarantee that doesn't assume normal residuals. For my best model that interval is ±6.85 MT/Ha at 90% — which is wide, and that width is the honest quantification of how much uncertainty 28 training rows leaves. I'd argue that a decision-maker is better served by a wide honest interval than by a narrow point estimate with no uncertainty attached at all."*

**Have this caveat ready too**, because a sharp examiner will spot it: empirical coverage reports 1.00 for every model. That's because the interval width is calibrated on the same out-of-fold residuals it's then evaluated against — so coverage is optimistic by construction. With n = 28 and α = 0.1 the required quantile level is ⌈29×0.9⌉/28 = 27/28 = 0.964, which nearly saturates the sample. **The correct fix is a held-out calibration split, which 28 rows cannot afford.** Saying this before they ask it is worth real credit.

## Per-district results

| District | R² | Interpretation |
|---|---|---|
| Anuradhapura | **+0.361** | Best. Largest, most consistent producer — cultivation practice is more uniform, so environmental signal isn't swamped by management noise. |
| Kurunegala | **−1.183** | Worst. Kurunegala isn't in the original proposal's core district list — it was added later, has the shortest effective history, and its yield series (17.9 → 10.1 → 15.2 → 13.8 → 12.2 → 18.1 → 15.8) is the most erratic. |

Useful conclusion to state: **model skill varies by an order of magnitude across districts, so any deployment must report per-district confidence rather than a single national accuracy figure.**

---

# PART 9 — Advantages and disadvantages

Have these as two clean lists. Examiners frequently ask for them directly.

## Advantages / strengths

**Methodological**
1. **Leave-One-Year-Out CV** — time-series-correct, no temporal leakage. Stricter than most published work in this area.
2. **Nested CV** for both hyperparameters and stacking weights — tuning decisions don't leak either.
3. **Statistical testing** (Wilcoxon signed-rank, paired t) rather than raw leaderboard comparison.
4. **Calibrated uncertainty** via conformal prediction, not a naive normal-theory band.
5. **Full reproducibility** — fixed seeds, every artefact persisted, one command re-runs everything.
6. **Honest reporting** — negative R² values are published, not hidden. Failed novelties are reported as findings.

**Scientific**
7. **First ML/DL yield prediction system for big onion in Sri Lanka.**
8. **A quantified, transferable finding**: domain knowledge (2 parameters) beat model capacity (45,000 parameters) — R² 0.020 → 0.091.
9. **A statistically supported negative result** on DL vs ML under scarcity, which saves other practitioners effort.
10. **An interpretable closed-form equation** from symbolic regression that an agronomist can audit.
11. **SHAP attributions that independently agree with published agronomy**, which is external validity evidence.

**Engineering**
12. **Twelve models under one evaluation protocol** — a genuinely fair comparison.
13. **Shared OOF schema** — stacking, conformal, statistics and the leaderboard all derive from one consistent source.
14. **Dual-variant design** — pipeline verified on synthetic data with known signal before real data arrived.
15. **Deployed end-to-end** — trained model served over REST and consumed by a working dashboard.

## Disadvantages / limitations (state these yourself, with the fix)

| # | Limitation | Impact | What would fix it |
|---|---|---|---|
| 1 | **n = 28.** Four districts × seven years. | Dominates everything. Explains all weak results. | More years (DCS archives pre-2019); more districts (Puttalam, Jaffna, Hambantota); sub-district/DS-division granularity would multiply rows by 5–10×. |
| 2 | **32 features on 28 rows (p > n).** | Curse of dimensionality; ablation experiment E is direct evidence. | Feature selection / dimensionality reduction; or the physics-backbone approach, which is what I did. |
| 3 | **Yala only — no Maha data.** | The season-injection novelty is unvalidatable on real data; the model cannot forecast off-season. | Acquire DCS Maha records for the same districts. |
| 4 | **Six constant features.** | Wasted dimensions, inert physics term, inert season branch. | Feature audit + removal before retraining. |
| 5 | **Soil is a district proxy.** | One profile per district → "soil only" ablation measures district identity, not soil chemistry. | Sub-district soil sampling from SoilGrids at finer resolution. |
| 6 | **Conformal coverage is optimistic.** | Calibrated on the same residuals it's evaluated on; reports 1.00. | Held-out calibration split — needs more rows. |
| 7 | **No management/agronomic covariates.** | Fertiliser, irrigation, variety, planting date, pest/disease pressure, labour — all unobserved. These plausibly drive more yield variance than weather does. | Farmer surveys or DOA extension records. |
| 8 | **Satellite indices are district-averaged.** | Averaging NDVI over a whole district dilutes the onion-field signal with forest, water, and other crops. | Crop-mask the imagery to onion parcels before aggregating. |
| 9 | **Yield labels are themselves estimates.** | DCS vegetable yields come from officer consultation, not crop cutting — so the *target* has measurement error. You cannot predict better than your labels. | This is the fundamental ceiling; it's the problem the project exists to address. |
| 10 | **DL models are undertrained by necessity.** | 24 training rows, batch size 16 — roughly two gradient steps per epoch. | Not fixable without more data; transfer learning or data augmentation would be the research direction. |
| 11 | **Target R² = 0.75 not met.** | 0.091 achieved. | See rows 1–3. The target was set assuming paddy-scale data. |
| 12 | **No external validation set.** | All 28 rows used in LOYO. No truly untouched holdout. | 2026 season data as a genuine prospective test. |

**Limitation 9 deserves a spoken sentence** — it's sophisticated and most students miss it: *"There's a ceiling I should name. Our target variable is itself an estimate produced by officer consultation rather than crop cutting. A model cannot be more accurate than the labels it learns from, so part of my irreducible error is measurement error in the ground truth — which is precisely the problem this project was proposed to solve."*

---

# PART 10 — The presentation: slide-by-slide

Assumes a **15-minute talk + 10-minute Q&A**. Adjust proportionally.

| # | Slide | Time | Content | What you SAY |
|---|---|---|---|---|
| 1 | **Title** | 0:15 | Project title, group AgroAI, your name + index, supervisor Dr. Firdhous M.F.M., University of Moratuwa FIT 2026 | "Good morning. I'm Arkam, index 214019K. I'll present the machine learning and deep learning modelling component of our big onion yield prediction system." |
| 2 | **The problem** | 1:15 | 200,000 MT annual consumption · import dependence · **no crop-cutting survey for vegetables** · estimates only available post-harvest | Land the contrast with paddy hard. That contrast IS your problem statement. |
| 3 | **Research gap** | 1:00 | The 5-row gap table from Part 7 | "No ML yield-prediction system exists for big onion in Sri Lanka, and no study has characterised this data-scarcity regime for vegetables." |
| 4 | **My research question** | 0:45 | The formal question from Part 1 | "Two parts: does DL beat ML under scarcity, and can domain knowledge substitute for data?" |
| 5 | **Scope** | 0:30 | The three-member table, your row highlighted | "Sharuja owns data acquisition, Shathurya owns the dashboard, I own everything from feature matrix to served prediction." |
| 6 | **The data — honestly** | 1:30 | 28 rows · 4 districts · 7 years · **Yala only** · 32 features · the p>n callout · the six-constant-features audit | **This is your credibility slide.** Deliver the limitations proactively and calmly. |
| 7 | **Methodology: LOYO-CV** | 1:30 | The 7-fold diagram; why random splits leak; nested CV | "Every number I report is out-of-fold. No model ever sees the year it's scored on." |
| 8 | **The 12 models** | 1:00 | Grouped: 3 ML · 4 DL · symbolic · physics-hybrid · 3 stackers | One line each. Don't over-explain — you'll get asked. |
| 9 | **Novelty 1: physics-residual** | 2:00 | The two-stage diagram · the FAO-33 formula · **R² 0.020 → 0.091** · cite Shahhosseini 2021 | **Your best slide. Spend the time.** "Two fitted parameters bought more skill than 45,000 did." |
| 10 | **Novelty 2: hybrid CNN-LSTM** | 1:00 | The architecture diagram + the honest caveat about the inert season indicator | Present the design, then own that it underperformed and why. |
| 11 | **Results: leaderboard** | 1:30 | The 12-row table, sorted; annotate the inverse relationship between parameter count and rank | "Performance is almost perfectly inversely ordered by parameter count." |
| 12 | **Results vs baselines** | 1:15 | The four-row baseline table from Part 8 | "The only method in the study that beats guessing the average." |
| 13 | **Ablation + SHAP** | 1:15 | Ablation table + SHAP top-3 with agronomic interpretation | "The data-driven attribution independently agrees with published HORDI agronomy." |
| 14 | **Uncertainty** | 0:45 | Conformal ±6.85 MT/Ha + the optimistic-coverage caveat | "A wide honest interval beats a narrow unjustified point estimate." |
| 15 | **Findings** | 1:00 | The nine findings, condensed | Read them as answers to questions, not as bullets. |
| 16 | **Limitations + future work** | 1:00 | Top 5 limitations, each paired with its fix | Never end on a limitation without its remedy. |
| 17 | **Conclusion** | 0:45 | Three contributions restated + one forward-looking line | Land it. Don't trail off. |

## Delivery rules

- **Front-load the limitations (slide 6).** A weakness you disclose is methodological maturity. A weakness they uncover is a gap in your understanding. Same fact, opposite grade.
- **Never say "only" about your own work.** Not "we only got 28 rows" — say "the dataset comprises 28 seasonal observations, which places this squarely in the small-sample regime."
- **Numbers, not adjectives.** Not "much better" — "R² improved from 0.020 to 0.091, a 4.5× increase."
- **Cite when you name a technique.** FAO-33 → Doorenbos & Kassam 1979. Residual hybrid → Shahhosseini et al. 2021. Stacking → Wolpert 1992. Non-negative weights → Breiman 1996. Combination puzzle → Stock & Watson 2004. SHAP → Lundberg & Lee 2017. GDD → McMaster & Wilhelm 1997. This is the single clearest signal that you read rather than just coded.
- **Rehearse aloud, timed, three times.** Silent reading does not build fluency under pressure.
- **If you don't know something, say so and bound it:** *"I haven't tested that. My expectation is X because Y, but I'd need to run it to confirm."* Never invent a number. Examiners forgive gaps; they do not forgive fabrication.

## Your closing line

> *"To conclude: this is the first machine learning system for big onion yield prediction in Sri Lanka. Under 28 observations, I've shown with statistical support that deep learning does not beat classical machine learning, and that a two-parameter physics-informed backbone derived from FAO crop-water relations quadruples predictive skill over the same model without it. The accuracy target of 0.75 was not met, and I've been explicit about why — the sample size makes it unreachable. But the methodological finding transfers directly to any data-scarce agricultural forecasting problem: when you cannot get more data, encode what agronomy already knows. Thank you — I'm happy to take questions."*

---

# PART 11 — Demo script

Rehearse this until it runs without you thinking. **Have a screen recording as backup** — live demos fail at exactly the wrong moment.

### Before the room

```bash
cd /Users/arqm7/Documents/FYP/Model
source .venv/bin/activate
PORT=5050 python src/api.py          # terminal 1 — leave running
cd dashboard && npm run dev          # terminal 2 — leave running
```

Open in browser tabs, pre-loaded: dashboard `localhost:3000`, and the plots folder.

### The five-minute demo

**1. Show the pipeline exists (30s)** — `main.py`, then `src/`. *"Thirteen stages, one command. Every model writes out-of-fold predictions to a shared schema, which is what lets stacking, conformal intervals and the statistical tests all derive from one consistent source."*

**2. Show the leaderboard (60s)** — open `outputs/results_real/model_comparison.csv`. Walk down it. Point at the parameter-count column.

**3. Show the plots (60s)** — `outputs/plots_real/results/`:
- `model_comparison_bar.png` — the leaderboard visually
- `actual_vs_pred_rf.png` — scatter with the 45° line; **be ready to say the points cluster near the mean, which is exactly what an R² near zero looks like**
- `shap_summary.png` — feature attributions
- `ablation_comparison.png` — data-source decomposition

**4. Show a learning curve (45s)** — `outputs/plots_real/training/cnn_lstm_learning_curve.png`. *"Training loss falls, validation loss doesn't follow. That's overfitting made visible — 45,000 parameters against 24 training rows."* **This slide makes your DL-loses finding tangible rather than asserted.**

**5. Live prediction (90s)** — dashboard `/predict`, choose Anuradhapura / Yala / 2025, submit. Show the number *and the confidence interval.* Then `/explainability` for SHAP, then `/admin` for the comparison table. *"The dashboard consumes the same model artefact the research pipeline produced — the results you just saw and the prediction you're looking at come from one pipeline."*

### If it breaks

Say calmly: *"The service isn't starting — let me show the recorded run and I'll debug it after."* Switch to the recording. **Do not debug live.** It burns your time and their patience.

---

# PART 12 — Q&A bank

Drill these **out loud**. Written answers you've only read do not survive contact with a nervous room.

### On results

**1. Why is your R² only 0.09?**
28 observations, 32 features. p > n. No model reliably explains 75% of variance from 28 points. But 0.09 is positive, and it's the only model in the study that beats predicting the mean — it also beats persistence forecasting (−0.30) and district-average (−0.24), the two methods closest to current practice.

**2. What does negative R² mean?**
Worse than always predicting the average. It's legal and informative — it tells you a model is actively harmful, not merely weak. Eight of my twelve models are negative, and that's a reportable finding about this data regime.

**3. Is your project a failure?**
The accuracy target wasn't met and I state that plainly. The research questions were both answered with statistical support. The contribution is the methodological finding — domain knowledge beats model capacity under scarcity — which holds regardless of the absolute accuracy level.

**4. Which model would you actually deploy?**
PhysResidual. Best R², best RMSE, tightest conformal interval (±6.85 vs ±19.1 for CNN), and it's partly interpretable because the backbone is a published closed-form agronomic relation. If robustness mattered more than peak accuracy I'd deploy StackConvex, since blending reduces the risk of any single model failing on a new year.

**5. Why did the deep learning models fail so badly?**
Parameter-to-sample ratio. The hybrid has 44,929 parameters and 24 training rows per fold — about 1,600 parameters per example. It memorises rather than generalises. The learning curves show it directly: training loss falls, validation loss doesn't follow.

**6. Why did your own hybrid architecture lose?**
Two reasons, and I'll give both. First, capacity — 45,000 parameters on 24 rows. Second, and more specific: its key mechanism, the season-indicator injection, is inert on this dataset because we only obtained Yala records, so the indicator is constant. The architecture was designed for bimodal data and evaluated on unimodal data. That's an honest limitation of the evaluation, not evidence the design is wrong — but I can't claim it's right either, because I couldn't test it.

**7. Your ablation shows Weather+Satellite is worse than either alone. Explain.**
Curse of dimensionality. Going from 9 or 11 features to 20 on 28 rows adds parameters without adding information — the model fits noise in the extra dimensions. It's direct empirical evidence for the constraint that motivated the physics-backbone approach.

**8. Soil-only was your best single source. Is soil the most important factor?**
No, and I'd be misreading my own experiment if I said yes. Soil has one profile per district, so "soil only" is effectively "district identity only." It's capturing between-district yield differences, not soil chemistry. I flag this in the report.

**9. Why is Kurunegala so much harder than Anuradhapura?**
Anuradhapura R² = 0.361, Kurunegala −1.183. Anuradhapura is a larger, more established producer with more uniform cultivation practice, so the environmental signal isn't swamped by management variation. Kurunegala wasn't in the original proposal's core district set, and its yield series is the most volatile — 17.9 down to 10.1 and back to 18.1 within six years. The practical implication is that deployment must report per-district confidence, not one national figure.

**10. Your conformal intervals report 100% coverage. Isn't that suspicious?**
Yes, and I'll explain why. The interval is calibrated on the same out-of-fold residuals it's then evaluated against, so coverage is optimistic by construction. With n=28 and α=0.1 the required quantile level is 27/28, which nearly saturates the sample. The correct fix is a separate held-out calibration split, which 28 rows can't afford. I report the empirical coverage with that caveat attached rather than presenting it as a validated guarantee.

**11. Why does StackMean do so badly when the literature says equal weighting usually wins?**
Because the equal-weight mean assigns 11% to CNN and 11% to the hybrid, which have R² around −7. Averaging in two catastrophically bad forecasts destroys the blend. The convex-constrained solver correctly assigned them 0.000 and 0.005. So my finding is that the forecast-combination puzzle does not hold here — and the reason is instructive: equal weighting is only robust when the member models are of broadly comparable quality, which mine are emphatically not.

### On methodology

**12. Why Leave-One-Year-Out instead of a normal train/test split?**
Random splits leak future information into training, which inflates results. LOYO is the time-series-correct protocol. It's stricter than what most crop-yield papers do, which is part of why my numbers look modest against published figures — I'm reporting honest generalisation error.

**13. Why not k-fold cross-validation?**
Standard k-fold shuffles rows, so it has the same leakage problem. LOYO is a structured k-fold where the grouping variable is the year — it respects the temporal structure.

**14. How did you tune hyperparameters without leaking?**
Nested CV. GridSearchCV with TimeSeriesSplit runs *inside* each outer LOYO fold, so tuning only ever sees training years. Same principle for the stacking weights — fitted on training years, applied to the held-out year.

**15. Why did you use synthetic data at all?**
To verify the pipeline before real data was available. If a pipeline can't recover a signal you deliberately planted, the pipeline is broken. It's a software-verification strategy. All reported results are from the real data variant in `outputs/results_real/` — the two are kept in separate directories precisely so they can never be confused.

**16. Why these four metrics?**
RMSE for typical error in the target's own units, penalising large misses. MAE for a median-robust view of typical error. MAPE for a scale-free percentage that stakeholders understand. R² for variance explained, which lets me compare against the do-nothing baseline. Reporting all four prevents cherry-picking.

**17. Why Wilcoxon signed-rank rather than a t-test?**
It's non-parametric — it doesn't assume normally distributed errors, which I can't verify on 28 samples. It's paired, so it compares the two model families on the *same* rows. I compute a paired t-test alongside it, but I report Wilcoxon as primary because its assumptions are the ones I can defend.

**18. What is SHAP and why should I trust it?**
SHAP assigns each feature a contribution to each individual prediction, computed as the feature's average marginal contribution over all possible feature orderings — the Shapley value from cooperative game theory. It's the unique attribution satisfying local accuracy, missingness and consistency. Its trustworthiness here is supported externally: the top features it identified — heat-humidity interaction, canopy vigour, drought — match the drivers published HORDI cultivation guidelines emphasise.

**19. What is conformal prediction?**
A distribution-free method for turning point predictions into intervals with a finite-sample coverage guarantee. I take the absolute out-of-fold residuals, find their (1−α) quantile with the finite-sample correction, and that becomes the half-width. It needs no normality assumption — unlike the ±1.96×RMSE band most papers use.

### On novelty

**20. What is genuinely novel here?**
Four things, and I'll be precise about which are inventions versus first applications. The strongest is the physics-residual hybrid for a tropical bulb crop — the residual-hybrid *idea* is Shahhosseini et al. 2021 for maize with APSIM; my contributions are the first application to Sri Lankan big onion, a lightweight closed-form FAO-33 backbone rather than a full process model, and the empirical result that it quadruples R². Second, the first statistically-tested ML-vs-DL comparison for vegetable yield at this sample size. Third, the first data-source ablation for this crop and region. Fourth, the first test of the forecast-combination puzzle on Sri Lankan crop-yield data.

**21. Isn't the physics-residual hybrid just an existing technique?**
The technique is established and I cite it. What is new is the crop, the region, the lightweight backbone formulation, and the empirical finding. Novelty in applied ML research is usually a new application with a new empirical result, not a new algorithm — and claiming otherwise would be dishonest.

**22. Where did the constant 1.1 come from?**
FAO Irrigation and Drainage Paper 33, Doorenbos and Kassam 1979. It's the seasonal yield-response-to-water factor Ky for onion and bulb crops. Ky > 1 means the crop is *more* than proportionally sensitive to water deficit — a 10% water shortfall costs more than 10% of yield. Every constant in my backbone comes from published crop science: GDD from McMaster and Wilhelm 1997, the multiplicative stress form from FAO-33.

**23. You said the backbone alone has R² = −0.222. So the physics is wrong?**
The backbone alone is a poor *predictor*, yes. But that's not its job in the hybrid. Its job is to reshape the learning problem — to remove a structured, agronomically-grounded component of the signal so the ML stage has a smaller and better-behaved residual to fit. The evidence that it works is the comparison against the identical Random Forest without it: 0.020 versus 0.091. The value is in the decomposition, not in the backbone's standalone accuracy. I think that's actually one of the more interesting findings in the study.

**24. Why does the fitted calibration have b = −4.36? Isn't a negative slope backwards?**
It is counter-intuitive and I won't pretend otherwise — a higher suitability index maps to *lower* predicted yield. With only Yala data, `heat_stress_days` is uniformly zero so the heat term is inert, and the index is driven by GDD and SPI. On 28 rows a two-parameter least-squares fit can easily land on a negative slope if the sampled range of the index is narrow and confounded with district effects. My honest reading is that the backbone here functions more as a structured basis function than as a correctly-signed physical law, and validating the sign properly needs data spanning genuine drought and heat-stress years. It's the first thing I'd check with more data.

*(That's a hard question. If you get it, this answer — which concedes the oddity and proposes a test — is far stronger than a confident wrong explanation.)*

**25. What is symbolic regression and what did it find?**
Genetic programming over the space of mathematical expressions, with a parsimony penalty so short formulas win ties. It found: yield ≈ fourth-root of (temp_x_humidity × prev_year_yield) + 3.251 − drought_index_spi. It's agronomically readable — yield rises with heat-humidity and with last year's yield, and falls as drought deepens. Its R² is −0.254, so it's not the best predictor, but it's the only model whose entire logic an agronomist can audit in one line.

### On the domain

**26. Why big onion specifically?**
Strategic importance — roughly 200,000 MT annual consumption, heavy import dependence costing foreign exchange, and a government self-sufficiency objective. And methodologically it's the interesting case: unlike paddy there's no crop-cutting survey, so it's exactly the data-scarce regime nobody has characterised.

**27. What are Yala and Maha?**
The two monsoon-driven agricultural seasons. Yala runs April to August and is the main onion season — drier conditions in the dry and intermediate zones suit bulb formation. Maha runs October to March and is off-season for onion, with substantially lower yields.

**28. Your novelty claims bimodal seasonality but you only have Yala. How do you defend that?**
I don't defend it — I qualify it. The architecture was designed for bimodal data, and on the real dataset the season indicator is constant, so that mechanism is untested. I state this explicitly rather than letting the architecture take credit for something it never exercised. Acquiring DCS Maha records for the same districts is the first item in my future work, and it's the experiment that would actually validate or refute the design.

**29. What is NDVI and why does it predict yield?**
Normalised Difference Vegetation Index — (NIR − Red)/(NIR + Red) from satellite reflectance. Healthy vegetation strongly reflects near-infrared and absorbs red, so NDVI rises with green biomass. More biomass through the season generally means more photosynthesis and more assimilate to fill the bulb. It's a canopy-vigour proxy, not a yield measurement.

**30. Why did satellite features not help more?**
Two reasons. Sample size — 11 satellite features on 28 rows is more dimensions than data can support, and the ablation shows adding them to weather makes things worse. And spatial aggregation — the indices are averaged over whole districts, so the onion-field signal is diluted by forest, water and other crops. Crop-masking the imagery to onion parcels before aggregating would be the fix, and I'd expect it to matter more than any modelling change.

### On engineering

**31. Walk me through your pipeline.**
Thirteen stages: load, preprocess, feature-engineer, EDA, then three ML models, symbolic regression, the physics hybrid, four DL models, the ablation study, SHAP, stacking, final evaluation with statistical tests, and conformal intervals. One command. Every model writes out-of-fold predictions to a shared JSON schema, so stacking, conformal, statistics and the leaderboard all derive from one consistent source rather than each model reporting its own numbers its own way.

**32. How is the model deployed?**
Flask REST API on port 5050. Six endpoints — health, predict, model comparison, feature importance, context prefill, and district options. It loads the serialised best model and serves it to the Next.js dashboard. Same artefact the research pipeline produced, so what the dashboard shows and what I report are guaranteed consistent.

**33. Is this reproducible?**
Yes. `RANDOM_STATE = 42` fixed everywhere, every artefact persisted — model files, out-of-fold JSONs, plots, CSVs — and one command re-runs the whole thing to identical numbers.

**34. Why Python and these libraries?**
scikit-learn for classical ML and the CV machinery, XGBoost for gradient boosting, TensorFlow/Keras for the deep models, SHAP for attribution, SciPy for the optimisation in convex stacking and the statistical tests, pandas/NumPy throughout. Standard, well-tested, and reproducible on a laptop.

### The hardest ones

**35. If you started over, what would you change?**
Three things, in order of expected impact. First, I'd fix the sample size before touching modelling — go to sub-district granularity and extend the year range backwards through the DCS archive, which could plausibly get me to 200–500 rows. Second, I'd start from the physics-informed approach rather than arriving at it late; the whole study points to constrained, knowledge-encoded models being the right family for this regime. Third, I'd run a feature audit up front — I have six constant features that should never have reached training.

**36. What did you learn?**
The specific lesson is that under scarcity, the constraint you impose matters more than the capacity you add. Two FAO-derived parameters bought more predictive skill than 45,000 learned ones. The broader lesson is that a rigorous protocol produces uncomfortable numbers, and the discipline is to report them — my R² would look much better under a random train/test split, and it would be wrong.

**37. What's the practical value if accuracy is this low?**
Three things that survive the accuracy limitation. The system produces calibrated intervals, so a planner gets a quantified uncertainty range rather than an officer's point guess. It's automated and early — available before harvest rather than after. And it beats the naive baselines that approximate current practice. I'd position it as decision support that improves on guessing, not as a replacement for measurement — and I'd say the honest recommendation to DCS is that establishing a crop-cutting methodology for vegetables would improve forecasts more than any modelling work I could do.

**38. What's your future work?**
In priority order: acquire Maha records to actually test the seasonal mechanism; extend to sub-district granularity for sample size; crop-mask the satellite imagery; add management covariates — fertiliser, irrigation, variety, planting date; test transfer learning from data-rich crops like paddy or from onion in Indian states with larger datasets; and run a genuine prospective test on the 2026 season.

**39. How does this compare to published work?**
Published crop-yield papers routinely report R² of 0.7 to 0.9 — but typically on thousands of samples with random train/test splits. My sample is 28 and my protocol is Leave-One-Year-Out with no temporal leakage. The comparison isn't like-for-like, and I'd argue the more honest reading is that the field's headline numbers are partly a protocol artefact. The closest methodological comparator is Shahhosseini et al. 2021, who also found a mechanistic backbone improved ML yield prediction — my result is consistent with theirs in a much harsher data regime.

**40. Convince me this deserves to pass.**
It's the first ML system for this crop in this country. It answers two well-posed research questions with statistical support. It reports negative results and failed novelties honestly rather than hiding them. The evaluation protocol is stricter than most published work in the area. And it produces one transferable finding — that a two-parameter agronomic backbone quadruples predictive skill over the same model without it — that applies to any data-scarce agricultural forecasting problem, not just onions in Sri Lanka. The accuracy target wasn't met, and I've been explicit about exactly why and exactly what would fix it.

---

# PART 13 — Optional strengthening (only if you have time)

Ranked by marks-per-hour. Each is a small, safe change.

1. **⭐ Add the naive baselines to the leaderboard** (~1 hour). Add mean-predictor, persistence, and district-mean as rows in `model_comparison.csv`. Right now your best model looks weak in isolation; against baselines it looks like the only thing that works. The numbers are already computed in Part 8 — just wire them into `evaluator.py`. **Highest return of anything on this list.**

2. **⭐ Run the feature audit in code** (~30 min). A short script that prints `nunique()` per feature and flags constants. Put the table on slide 6. Turns a weakness into evidence of diligence.

3. **Retrain without the 6 constant features** (~1 hour). 26 features on 28 rows instead of 32. Results will likely improve slightly, and either way "I audited and retrained" is a strong sentence.

4. **Fill the empty EDA folder** (~20 min). `outputs/plots_real/eda/` is empty — run `python main.py --real --skip-ml --skip-dl --skip-shap`. A yield time-series plot and a correlation heatmap are easy, expected slides.

5. **Add a per-district results table to the summary** (~45 min). You currently only report best and worst. All four would strengthen the deployment-confidence argument.

6. **Recompute the ablation with a consistent estimator** (~30 min). Your ablation "all features" row is −0.082 while the tuned RF on the same features is +0.020. Explain or reconcile the difference before someone asks. It's likely a tuning difference — check `src/ablation.py`.

**Do not** attempt architecture changes, new models, or a hyperparameter re-sweep this close to the presentation. Nothing you'd gain outweighs the risk of breaking a working pipeline.

---

# PART 14 — Cheat sheet

## Commands

```bash
cd /Users/arqm7/Documents/FYP/Model
source .venv/bin/activate

python main.py --real                      # full real-data pipeline
python main.py --real --skip-dl --skip-shap  # fast ML-only run (~1 min)
python main.py                             # synthetic variant (separate outputs)

PORT=5050 python src/api.py                # serve the model
cd dashboard && npm run dev                # dashboard on :3000
```

**Artefacts to have open:** `outputs/results_real/model_comparison.csv` · `final_summary.txt` · `physics_residual.json` · `stacking_summary.json` · `conformal.json` · `ablation_results.csv` · `symbolic_equation.txt` · `outputs/plots_real/results/*.png`

## Numbers to memorise

| | |
|---|---|
| Rows / features / districts / years | 28 / 32 / 4 / 7 (2019–2025), Yala only |
| Yield mean / std / range | 16.39 / 4.09 / 8.50–24.06 MT/Ha |
| Best model | PhysResidual — R² 0.091, RMSE 3.902, MAE 3.350, MAPE 23.3% |
| Physics gain | RF 0.020 → hybrid 0.091 (backbone alone: −0.222) |
| Worst model | CNN, R² −7.17 |
| Hybrid CNN-LSTM | R² −7.05, 44,929 parameters |
| ML vs DL | ML wins, Wilcoxon p < 0.0001 |
| Baselines beaten | mean 4.092 · persistence 4.666 · district-mean 4.558 → yours 3.902 |
| Conformal (90%) | ±6.85 MT/Ha |
| Best / worst district | Anuradhapura +0.361 / Kurunegala −1.183 |
| Top SHAP features | temp_x_humidity, season_mean_evi, drought_index_spi |
| Convex stack top weights | PhysResidual 0.399, XGBoost 0.271, BiLSTM 0.199 |

## Citations to have ready

- **Doorenbos & Kassam (1979)** — FAO Irrigation & Drainage Paper 33. Ky_onion ≈ 1.1.
- **Shahhosseini, Hu, Archontoulis et al. (2021)**, *Scientific Reports* — process model + ML residual for maize.
- **McMaster & Wilhelm (1997)** — growing degree days.
- **Wolpert (1992)** — stacked generalisation.
- **Breiman (1996)** — non-negative stacking weights.
- **Stock & Watson (2004); Claeskens et al. (2016)** — forecast-combination puzzle.
- **Lundberg & Lee (2017)** — SHAP.
- **Amarasinghe et al. (2024)**, *Discover Applied Sciences* — rice yield prediction in Sri Lanka.
- **Kamilaris & Prenafeta-Boldú (2018)** — deep learning in agriculture survey.

## The one thing to remember

Your project's grade will be decided by **how you frame 0.09**, not by the fact that it is 0.09. A student who reports a weak number, explains exactly why it is weak, shows it still beats every alternative, and extracts a transferable finding from it, is doing research. A student who hides it is not. **You are in the first category — present like it.**

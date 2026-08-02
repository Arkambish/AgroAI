# Poster Content — Arkam B.H.M. (214019K)
## ML, Deep Learning & Modelling Research + Serving Layer

Group: **Agro AI** · Project: *An Explainable AI-Driven Decision Support System for
Big Onion Yield Prediction Using Multi-Source Climate, Soil and Yield Data in Sri Lanka*

All figures below are taken from `outputs/results_real/` and match the Final Report.
Paste blocks verbatim; they are already sized for poster bullet points.

---

## 1. MY CONTRIBUTION — one-line positioning

> **Design, train and honestly evaluate the prediction engine** — nine models across four
> modelling families under one identical protocol — and establish *how much of the target
> this panel can actually support* before ranking any of them.

---

## 2. OBJECTIVES (my slice)

- Implement a comparative model family: classical ML, deep sequence learning, symbolic
  regression, and a physics-informed response model — one protocol, one seed.
- Audit the data pipeline end-to-end so every target value traces to a real source record.
- Quantify the **attainable accuracy ceiling** of the panel before comparing models.
- Attach distribution-free, correctly-blocked uncertainty to every forecast.
- Expose the trained system through a documented REST serving layer.

---

## 3. KEY MODULES / COMPONENTS

| Module | Source file | Responsibility |
|---|---|---|
| Classical models | `src/ml_models.py` | RF, XGBoost, SVR under LOYO-CV + nested tuning |
| Deep models | `src/dl_models.py` | LSTM, BiLSTM, 1D-CNN, hybrid CNN-LSTM |
| Symbolic regression | `src/symbolic.py` | Genetic-programming closed-form equation |
| **PADR** | `src/padr.py`, `src/phenology.py` | Phenology-aligned differentiable response model |
| Stacking | `src/stacking.py` | Simplex-constrained convex blend of 9 base learners |
| Uncertainty | `src/conformal_blocked.py` | Year-blocked cross-conformal intervals |
| Integrity audit | `src/integrity_audit.py` | Provenance, leakage and plausibility gate |
| Attainability | `src/variance_decomposition.py` | Variance decomposition + ceiling derivation |
| Ablations / power | `src/ablation_padr.py`, `src/identifiability.py` | Falsification arms, detection power |
| Serving | `src/api.py` | Flask REST layer, 8 endpoints, no training at serve time |

---

## 4. METHODOLOGY

**Figure:** `outputs/poster/arkam_methodology.png` (300 dpi, also supplied as PDF/vector)

Five-stage pipeline: **Data Foundation → Integrity Gate → Attainability → Model Family →
Honest Evaluation.**

Caption (short version for under the figure):

> Integrity-first modelling pipeline. No model is ranked until every target value traces to
> a genuine DCS record and the panel's attainable R² ceiling has been derived. All nine
> predictors are trained under a single Leave-One-Year-Out protocol with nested inner
> tuning; every fitted quantity — scaling, mechanistic calibration, augmentation — is
> re-estimated inside each fold.

---

## 5. THE PADR MODEL (headline technical contribution)

**Phenology-Aligned Differentiable Response** — replaces the fixed-coefficient
physics-residual hybrid.

- Weather enters on a **thermal phenological axis**, not a calendar one. Harvest date is
  the extent-weighted mean of the DCS monthly production distribution; planting is located
  by accumulating growing degree-days backwards. **All 28 district-years anchored, no
  fallbacks.**
- Agronomic constants are **estimated, not assumed** — fitted jointly with the response
  under agronomic box constraints and a penalty shrinking each toward its literature value.
- **17 parameters** vs the hybrid CNN-LSTM's **44,929**.
- Season lengths recovered are agronomically coherent: hotter Anuradhapura completes a
  season in 78–86 days, cooler Matale/Kurunegala need 90–99 days for the same heat.

**Estimated constants (mean ± sd across 7 LOYO folds):**

| Parameter | Estimated | Literature | Identifiable? |
|---|---|---|---|
| Optimum temperature | 28.95 ± 0.95 °C | 24 | Yes (2.9 %) |
| Soil water capacity | 147.1 ± 6.2 mm | 100 | Yes (1.0 %) |
| Base temperature | 10.24 ± 0.13 °C | 10 | Yes (9.1 %) |
| Waterlogging severity | 0.006 ± 0.001 | none | Yes (0.4 %) |
| Waterlogging threshold | 96.0 ± 5.2 mm/7d | none | Yes (1.4 %) |
| Critical temperature | 35.58 ± 0.71 °C | 35 | **No (16.2 %)** |
| Yield response factor Ky | 0.97 ± 0.05 | 1.1 (FAO-33) | **No (12.8 %)** |

> Only 5 of 7 constants survive the recovery experiment. Given data generated with
> Ky = 0.966 the estimator returns 1.108 — its literature prior. **A tight interval on a
> shrunk parameter is not evidence the parameter was learned.**

---

## 6. KEY RESULTS / OUTCOMES

### 6.1 The attainable ceiling (reframes everything else)

| Component | Share of total variance |
|---|---|
| Between years | **63.6 %** — removed by LOYO by construction |
| Between districts | 2.2 % |
| Residual | 34.2 % |
| Measurement error in target | 53.6 % of within-year variance |

> **Implied attainable LOYO R² = 0.162.** The proposal-stage target of 0.75 was not merely
> unmet — it was **unattainable by any model** on this panel under this protocol.

### 6.2 Model comparison (LOYO-CV, corrected target, n = 28)

| Model | RMSE | MAE | R² |
|---|---|---|---|
| Oracle year-mean *(not achievable)* | 3.775 | 3.238 | 0.636 |
| **Train mean (baseline)** | **6.938** | **5.457** | **−0.230** |
| District historical mean | 7.218 | 5.419 | −0.331 |
| XGBoost | 7.296 | 5.456 | −0.360 |
| PADR | 7.333 | 6.016 | −0.374 |
| Random Forest | 7.803 | 5.826 | −0.556 |
| SVR (RBF) | 7.847 | 6.008 | −0.573 |
| Persistence | 9.033 | 7.327 | −1.085 |

> Every feature-based model performs worse than predicting the training mean. Read against
> the ceiling this is the *expected* result, not a modelling failure.

### 6.3 Mechanism ablations — 2 of 4 design claims supported

| Arm | R² | Stress CV |
|---|---|---|
| Full PADR | −0.374 | 8.14 % |
| Fixed physics (literature constants) | −0.940 | 22.39 % |
| Heavy shrinkage (pinned to literature) | −1.540 | 35.33 % |
| Calendar time (not thermal) | −0.385 | 8.31 % |
| No waterlogging term | −0.370 | 8.04 % |

- **Supported:** learning the agronomic coefficients (**ΔR² = +0.566**); moderate shrinkage
  over heavy shrinkage (**ΔR² = +1.166**).
- **Not supported:** thermal-time indexing (+0.011); waterlogging term (−0.004).
  *Reported as null results — an ablation where every component helps is not credible.*

### 6.4 The diagnosis (principal scientific result)

- PADR's stress index varies at **CV = 8.1 %**; observed yield varies at **CV = 35.0 %**.
  A quantity varying by eight per cent cannot explain one varying by thirty-five.
- Thermal response stays in 0.86–0.91 (tropical temperatures barely vary year to year).
- Water-deficit factor is exactly 1 in most intervals — season rainfall averages 1,043 mm
  and the crop is tank-irrigated, so **drought effectively does not occur**.
- Removing the anomalous years (2022, 2024) makes the model *relatively worse*, not better
  → the signal is **absent from ordinary years**, not masked in extraordinary ones.
- **Detection power:** on simulated panels PADR recovers a weather signal driving as little
  as **6 % of yield variance** at n = 28. It recovered none. The agro-climatic signal here
  is therefore **below 6 % of variance** — a far stronger statement than "R² came out
  negative".

> **Conclusion:** Big onion yield in Sri Lanka's dry zone is **not agro-climatically limited
> at district-season resolution.** The binding constraints lie in inputs, management and
> policy — variables not available to this project.

### 6.5 Calibrated uncertainty

| | Naïve (in-sample) | Year-blocked cross-conformal |
|---|---|---|
| Coverage | 1.000 *(artefact)* | **0.911** vs nominal 0.90 |
| PADR half-width | — | **± 15.29 MT/ha** |

> On a target whose mean is 17.89 MT/ha this is roughly ± 85 %. The interval is correctly
> calibrated — and it is the evidence that these predictions are **not usable for import
> planning**. A system reporting a point forecast without it would mislead its user.

### 6.6 Forecast skill under unknown weather

Only 9 of 32 features are knowable before a season begins. Propagating unknown weather via
Monte Carlo over a 45-year NASA POWER analogue pool (200 samples/cell):

- Weather band contracts monotonically **± 1.32 → 0.00 MT/ha** as months are observed —
  the uncertainty machinery behaves correctly.
- **Skill does not.** ρ is **negative at every issue point** (−0.247 pre-season →
  −0.191 hindcast); climatology R² = −0.215 is never beaten.
- Sensitivity decomposition: weather features move the prediction by only 0.35–0.76 MT/ha —
  **the weakest of the unknown inputs.**

### 6.7 Decision value

- Curing-window humidity drives both yield *and* storage survival, so the newsvendor
  critical fractile is a **function of the model's own covariates**: it ranges
  **0.649 – 0.960** (a cereal cannot exhibit this coupling).
- Required skill to beat climatology: **0.00 – 0.22 recalibrated**, **0.39 – 0.48 raw**.
- The same forecast **reduces** expected decision loss by 3.9 % recalibrated and
  **increases** it by ~53 % used raw. *The difference between a useful and a harmful
  forecast is a one-line recalibration, not a different architecture.*

---

## 7. CONCLUSION (poster-ready, ~60 words)

> The project set out to reach R² > 0.75 and instead demonstrated it **could not have been
> reached**: with 63.6 % of variance between years and measurement error consuming over half
> the remainder, the attainable ceiling is 0.162. PADR delivers the value anyway — by making
> its agronomic constants estimable it shows FAO-33 coefficients **overstate weather
> sensitivity** for this crop under tank irrigation, and it localises *which* mechanisms are
> inactive and by how much. A well-diagnosed negative result, with the errors that preceded
> it stated openly, is of more use than a favourable number that cannot be defended.

---

## 8. FOOTER ENTRY

**Faculty:** Faculty of Information Technology
**Department:** Department of Information Technology
**Degree Programme:** BSc (Hons) in Information Technology
**Module:** IN4911 — Comprehensive Group Project
**Supervisor:** Dr. Firdhous M.F.M.

| Index No. | Name | Component |
|---|---|---|
| **214019K** | **Arkam B.H.M.** | **ML / DL & Modelling Research, Serving Layer** |
| 214192G | Sharuja B. | Data Engineering & Synthetic Augmentation |
| 214193K | Shathurya P. | Explainability & Decision Support System |

---

## 9. FIGURES YOU CAN PULL FOR YOUR PANEL

| Figure | Path |
|---|---|
| **Methodology flow (new)** | `outputs/poster/arkam_methodology.png` |
| Variance / attainable ceiling | `outputs/plots_real/results/` |
| PADR scoreboard | `outputs/plots_real/results/padr_scoreboard.png` |
| Stress vs yield | `outputs/plots_real/results/stress_vs_yield.png` |
| Hybrid CNN-LSTM learning curve | `outputs/plots/figures_final/figure_6_1_hybrid_learning_curve.png` |

**Suggested panel order:** Objectives → Methodology figure → PADR box → Model comparison
table → Ceiling callout → Diagnosis callout → Conclusion.

**Design note:** the methodology figure uses green `#0F5F4C` / amber `#D08A0B` /
blue `#1D5478`. Reuse those three as the poster's accent set so the panel reads as one system.

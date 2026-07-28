# PADR — findings of record

**Authoritative results document.** Supersedes the numbers in `00_OVERVIEW.md`,
`03`–`06`, and `FINAL_PRESENTATION_GUIDE.md`, all of which describe either the synthetic
variant or the contaminated-target real variant. Every figure here is reproducible from
`src/` against the files in `data/collected/`.

---

## 1. What changed in the data, and why

### 1.1 The target variable was approximately 40% fabricated

The previous modelling input, `FYP data(manual) - onion_unique_per_key.csv`, contained
124 month-rows of which **50 are marked `source=synthetic`**. The fabrication reached the
**target**, not merely the covariates: yield varies month-to-month within every one of the
28 district-year cells, and `Avg_Yield_MT_per_Ha` was their unweighted mean.

Cross-referencing against `FYP data(manual) - real all datas.csv`, which holds 87 month
records with genuine DCS `Extent (hectares)` and `Yield (MT)`:

| | count |
|---|---|
| month-cells with a real DCS record | 87 |
| `source=real` rows, all of which map to a DCS record | 74 |
| `source=synthetic` rows with **no** DCS record at all | 39 |
| `source=synthetic` rows that **did** have a real record, discarded and replaced | 11 |
| real DCS records never used | 13 |

A cell-level real-only filter is not viable — only **4 of 28** cells are 100% real.

### 1.2 The corrected target

`src/dcs_panel.py` rebuilds the panel from the 87 real records using the standard
agronomic definition:

```
yield(district, year) = Σ production_MT ⁄ Σ extent_ha      over the season's months
```

All 28 cells survive. Correlation with the old target is only **0.68**, and the standard
deviation more than doubles (4.17 → 6.37 MT/ha): averaging in fabricated values was
compressing the very variance the models were asked to predict.

Two parsing traps handled explicitly, either of which silently corrupts the panel:
- `Yield (MT)` uses thousands separators (`"3,091"`). Without `thousands=','` these
  become `NaN` — that alone turned Matale 2020 into 0.53 MT/ha instead of 12.16.
- `0` is a **missing** code for `EVI - II`, `NDVI - II` (20 each) and all three soil
  columns (40 — Kurunegala and Matale have no SoilGrids export). It is a **genuine**
  zero for extent and production (7 month-cells with no harvest).

### 1.3 Six physically impossible month-records excluded

| record | extent | production | implied yield |
|---|---|---|---|
| Matale, Oct 2025 | 30.0 ha | 13,271.7 MT | **442 MT/ha** |
| Polonnaruwa, Oct 2025 | 16.7 ha | 2,419.5 MT | 145 MT/ha |
| Anuradhapura, Oct 2025 | 156.9 ha | 10,698.6 MT | 68 MT/ha |
| Anuradhapura, Aug 2021 | 7.8 ha | 856.4 MT | 110 MT/ha |
| Polonnaruwa, Nov 2019 | 1.4 ha | 274.0 MT | 192 MT/ha |
| Polonnaruwa, Oct 2019 | 2.8 ha | 240.0 MT | 84 MT/ha |

The world record for onion is roughly 100 MT/ha under intensive irrigation; Sri Lanka
averages 15–20. Excluding these six (cells survive on their remaining months) makes 2025
coherent — **21.07 / 21.95 / 22.85** across three districts, where it had read 35.96 /
42.72 / 42.11. Full audit trail in `outputs/results_real/data_quality_report.csv`.

**Action for Arkam:** verify these six against the original DCS publication.

### 1.4 Observation weights

District-years span **4 ha to 1,765 ha**. A 4 ha cell gives a far noisier yield estimate
than a 1,765 ha one, so observations are weighted by `sqrt(extent)`, normalised to mean 1
(`OBS_WEIGHT_MODE` in `src/config.py`). Plain area weighting spans 440× and would erase
Kurunegala entirely. Both weighted and unweighted metrics are reported throughout.

### 1.5 Real district-level inputs, and their limits

`src/data_collection/nasa_power.py` pulls **37,988 daily records** (4 district centroids,
2000–2025, zero missing), including real `ALLSKY_SFC_SW_DWN` — the solar radiation
feature previously hard-coded to the constant 18.0 (real values run 9.6–19.3 MJ/m²/day).

Two limitations to state openly in the report:

- **Kurunegala and Matale receive byte-identical daily weather** (r = 1.0000). Their
  centroids fall inside one NASA POWER grid cell. There are 3 distinct weather series
  for 4 districts.
- **District-mean MODIS NDVI cannot see onion.** Onion occupies **0.002%–0.89%** of any
  district's land area. A district-mean composite measures paddy, forest and scrub.
  Phenological anchoring on the NDVI curve was attempted and **25 of 28** district-years
  failed to anchor. This also retro-explains the original project's satellite-only
  ablation result of R² = −0.67. Evidence figure:
  `outputs/plots_real/results/ndvi_not_crop_specific.png`.

### 1.6 Leaks removed

| leak | previous behaviour | fix |
|---|---|---|
| `ndvi_anomaly` | z-scored over the full 2019–2025 panel | standardised against the **2000–2018** climatology, which no fold ever tests on |
| `drought_index_spi` | same | same |
| median fill of first-year lags | global median over all years | yield lags **dropped entirely** (see below) |
| target winsorisation | full-sample percentiles | removed; outliers handled by the explicit physical-plausibility filter |

**Yield lags were dropped**, not repaired. Under leave-one-year-out with year *k* held
out, the training row for year *k+1* carries year *k*'s observed yield as a feature.
They also buy nothing here: only 2.2% of variance is between-district, which is all a
persistence term can capture. (`prev_season_yield` and `prev_year_yield` were identical
columns anyway, the panel being Yala-only.)

Seven features were constants or exact linear transforms of others and are gone:
`season_avg_solar_rad`(=18.0), `season_mean_ndwi`(=0.1), `organic_carbon`(=1.8),
`extent_prev_season`(=400.0), `heat_stress_days`(=0), `season_indicator`(=1), and
`season_mean_lst_day/night` (= `season_avg_temp` ± 6).

With real daily weather, `heat_stress_days` now ranges **33–116** instead of being
identically zero — the old code compared *monthly mean* temperature to 32 °C.

---

## 2. The structural result

### 2.1 Variance decomposition

`src/variance_decomposition.py` → `outputs/results_real/variance_decomposition.json`

| component | sum of squares | share |
|---|---|---|
| between **YEAR** | 696.89 | **63.6%** |
| between **DISTRICT** | 24.09 | 2.2% |
| residual | 374.97 | 34.2% |

**Leave-one-year-out removes the dominant component by construction.** This is why every
model in this project — the original twelve and PADR alike — scores near or below zero.
It is arithmetic, not a modelling failure.

### 2.2 Measurement error in the target

Each cell's yield is an extent-weighted mean over 2–5 month-records, so the weighted
spread of those months divided by Kish's effective sample size estimates the variance of
that mean directly:

```
mean standard error per cell = 2.81 MT/ha
                             = 19.5% of TOTAL variance
                             = 53.6% of WITHIN-YEAR variance
```

More than half of the between-district variation within a year is measurement noise.

### 2.3 The attainable ceiling

Subtracting the year component (unavailable under LOYO) and measurement error (unlearnable
by anything):

```
implied LOYO R² ceiling = 0.162
```

> **The project's original target of R² > 0.75 was not difficult. It was unattainable.**
> No model, however sophisticated, could have reached it on this panel under this
> validation protocol.

Figure: `outputs/plots_real/results/variance_ceiling.png`

---

## 3. Honest baselines on the corrected target

`src/baselines.py` → `outputs/results_real/baseline_comparison.csv`.
Leave-one-year-out, 7 folds, all scaling fitted inside the fold, 22 real features.

| model | RMSE | MAE | R² | R² (area-weighted) |
|---|---|---|---|---|
| *Oracle: true year mean* | *3.775* | *3.238* | *+0.636* | *+0.716* |
| TrainMean | 6.938 | 5.457 | **−0.230** | −0.236 |
| DistrictMean | 7.218 | 5.419 | −0.331 | −0.396 |
| XGBoost | 7.296 | 5.456 | −0.360 | −0.217 |
| PADR | 7.333 | 6.016 | −0.374 | −0.455 |
| RandomForest | 7.803 | 5.826 | −0.556 | −0.328 |
| SVR (RBF) | 7.847 | 6.008 | −0.573 | −0.549 |
| Persistence | 9.033 | 7.327 | −1.085 | −1.013 |

**Every feature-based model loses to predicting the training mean.** The oracle row is
not achievable — it uses the held-out year's own mean — and is shown to bound what
perfect year-effect knowledge would buy.

### Per-fold RMSE

| year | actual mean | PADR | TrainMean | XGBoost |
|---|---|---|---|---|
| 2019 | 17.97 | **4.19** | 5.01 | 4.79 |
| 2020 | 13.85 | 5.82 | 5.22 | **4.95** |
| 2021 | 18.98 | 3.87 | **2.64** | 4.14 |
| **2022** | **9.42** | 11.12 | 10.61 | **8.34** |
| 2023 | 18.33 | 4.54 | **2.67** | 3.08 |
| **2024** | **26.90** | **11.50** | 11.76 | 14.25 |
| 2025 | 19.78 | 5.79 | **4.41** | 5.09 |

2022 and 2024 dominate the total error for every model.

### 2022 is a policy shock, not weather

| year | 2019 | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| mean MT/ha | 17.97 | 13.85 | 18.98 | **9.42** | 18.33 | 26.90 | 19.78 |

2022 collapsed across **all four districts** (Matale to 3.63 MT/ha, consistently low
across all three of its month-records — so it is a real crop failure, not a transcription
error). The timing matches Sri Lanka's April-2021 chemical fertilizer import ban and the
2022 economic crisis. **Cite this from the policy literature — do not infer it from the
panel.** No weather-driven model can predict it, and it will remain the worst fold.

---

## 4. PADR

`src/padr.py`. Seventeen parameters, against 44,929 in the CNN-LSTM it replaces.

```
S(d,y) = ∫₀¹ β(τ) · f_T(τ) · f_W(τ) · f_WL(τ) dτ
ŷ      = (Y₀ + u_d) · S(d,y)
```

Fitted by multi-start L-BFGS-B under agronomic box bounds, staged (β-only with physics
frozen, then unfrozen from that warm start), refit from scratch for each held-out year.

### 4.1 Thermal phenological time (N2)

`src/phenology.py`. With satellite anchoring ruled out (§1.5), the axis is built from two
real, crop-specific signals:

1. **Harvest date** — the extent-weighted mean of the DCS monthly production
   distribution. Genuinely crop-specific, and it moves: **DOY 228–279**, a 51-day span.
2. **Thermal time backwards from harvest** — planting is located by accumulating growing
   degree-days back from harvest until `GDD_REQUIRED` is met, so
   `τ = GDD accumulated ⁄ GDD required`.

**28 of 28 district-years anchored, zero fallbacks.** The result is agronomically
coherent: planting DOY 138–200, season length **76–99 days**. Critically, hot Anuradhapura
(27.9 °C) runs 78–86 day seasons while cooler Matale and Kurunegala (25.1 °C) need 90–99
days to accumulate the same heat. Calendar duration varies because thermal time does not.

### 4.2 Learned agronomic constants

Mean ± sd across the 7 LOYO folds. **This is the scientific output of the model, and it
stands independently of predictive accuracy.**

| parameter | learned | literature | identifiable at n=28? | reading |
|---|---|---|---|---|
| `T_opt` | **28.95 ± 0.95** | 24.0 | ✅ 2.9% | pulled well up — adaptation to a hot dry zone |
| `W_max` | **147.1 ± 6.2 mm** | 100 | ✅ 1.0% | deeper effective store than assumed |
| `T_base` | **10.24 ± 0.13** | 10.0 (McMaster & Wilhelm 1997) | ✅ 9.1% | confirms the standard base temperature |
| `γ` (waterlogging) | 0.006 ± 0.001 | — | ✅ 0.4% | newly estimated; no prior exists |
| `P_crit` | 96.0 ± 5.2 mm/7d | — | ✅ 1.4% | newly estimated |
| `T_crit` | 35.58 ± 0.71 | 35.0 | ❌ **16.2%** | **do not report as a finding** |
| `Ky` | 0.97 ± 0.05 | 1.1 (FAO-33) | ❌ **12.8%** | **do not report as a finding** — see below |
| `Y₀` | 20.45 ± 1.14 | — | — | attainable yield |

District offsets are tiny (−0.14 to +0.20 MT/ha), exactly as the 2.2% between-district
variance share predicts.

### ⚠️ Tight fold spread is not evidence — the Ky correction

The parameters look tight across folds, and on that basis an earlier draft of this
document reported `Ky = 0.97` as showing big onion to be less water-sensitive than
FAO-33's generic 1.1. **The recovery experiment (§4.6) withdraws that claim.**

Fitting PADR to data *generated* with `Ky = 0.966`, the estimator returns **1.108** — it
reproduces the literature prior rather than the truth. The shrinkage penalty that makes
the model estimable at n=28 also pins any parameter the data cannot constrain to its
prior, and the resulting low fold-to-fold variance is the *prior's* stability, not
evidence from the data. Precision without accuracy.

Two claims survive this and one does not:

- ❌ **Withdrawn:** any statement about `Ky` or `T_crit` as estimated quantities.
- ✅ **Stands:** `T_opt = 28.95` and `W_max = 147 mm`, both recovered to within 3% of range.
- ✅ **Stands, and does not depend on any single parameter:** the finding that FAO-33
  coefficients overstate weather sensitivity. That rests on the `strong_shrinkage`
  *ablation* (R² = −1.540 with a stress CV of 35.3%), not on a point estimate.

### 4.3 Why PADR does not beat the mean

The stress index cannot move far enough:

```
stress index S : CV =  7.95%   (range 0.69 – 0.94)
observed yield : CV = 34.97%   (range 3.63 – 33.58)
```

Component by component, β-weighted over the season:

| component | behaviour | binds |
|---|---|---|
| thermal `f_T` | near-constant 0.86–0.91 | tropical temperatures barely vary year to year |
| water deficit `f_W` | mostly exactly 1.0 | 0–31% of bins, usually **0** — 1,043 mm rain plus tank irrigation |
| waterlogging `f_WL` | 1.0 except 2022 | 3.5% of bins in 2022 only; highest correlation with yield (r = +0.53) precisely because 2022 is the crash year |

**A model whose output varies 8% cannot explain a target that varies 35%.** No tuning
fixes this — it is structural.

And it is not merely the anomalous years:

| subset | PADR | TrainMean | Oracle |
|---|---|---|---|
| all 7 years (n=28) | −0.374 | **−0.230** | +0.636 |
| excluding 2022 (n=24) | −0.442 | **−0.279** | +0.516 |
| excluding 2022 & 2024 (n=20) | −0.542 | **−0.099** | +0.272 |

PADR gets *relatively worse* on the normal years. The agro-climatic signal is genuinely
absent, not merely masked by a policy shock.

Figure: `outputs/plots_real/results/stress_vs_yield.png`

### 4.4 Mechanism ablations

`src/ablation_padr.py` → `outputs/results_real/padr_ablation.csv`. Seven arms, each
switching one mechanism off, 12 multi-starts per fold. Alongside R², the column that
matters is `stress_cv` — how much variation each configuration is *capable* of
generating, against the 35.0% CV of observed yield.

| arm | R² | stress CV | what it isolates |
|---|---|---|---|
| **full** | **−0.374** | 8.14% | PADR as specified |
| fixed_physics | −0.940 | 22.39% | constants frozen at literature (N1 control) |
| calendar_time | −0.385 | 8.31% | τ spaced in days, not heat (N2 control) |
| no_waterlogging | −0.370 | 8.04% | γ pinned to 0 (N3 control) |
| flat_beta | −0.429 | 9.78% | β(τ) forced uniform |
| no_shrinkage | −0.373 | 11.57% | λ_phys = 0 (N4 control) |
| strong_shrinkage | −1.540 | 35.33% | λ_phys = 100, constants effectively pinned |

**Each novelty claim, judged honestly:**

| claim | Δ R² vs control | verdict |
|---|---|---|
| **N1** — learned vs fixed physics | **+0.566** | **strongly supported** |
| **N4** — moderate vs heavy shrinkage | **+1.166** | **strongly supported** |
| β(τ) learned vs flat | +0.055 | modest but positive |
| **N2** — thermal vs calendar time | +0.011 | **negligible on this panel** |
| N4 — moderate vs no shrinkage | −0.002 | neutral at λ = 1 |
| **N3** — waterlogging term | −0.004 | **inert, marginally harmful** |

Two of the four claims survive; two do not. Report it that way — a paper in which every
proposed component happens to help is not a credible ablation.

**Why N2 is negligible here.** Thermal time and calendar time nearly coincide when
temperature barely varies, which is precisely the tropical regime documented in §4.3.
The method is not wrong; the panel simply offers it nothing to correct.

**Why N3 is inert.** Waterlogging binds in 3.5% of bins, in one year only. There is not
enough exceedance of the estimated 96 mm/7-day threshold for the term to earn its two
parameters.

**The most interesting row is `strong_shrinkage`.** Pinning the constants to their FAO-33
and literature values produces a stress CV of **35.33%** — almost exactly matching the
35.0% CV of observed yield — yet scores **R² = −1.540**, by far the worst arm. The
generic constants imply an onion crop far *more* weather-sensitive than the Sri Lankan
dry-zone data support, and they place that sensitivity in the wrong years. Learning the
constants (N1) does not add explanatory power so much as **remove spurious sensitivity**:
stress CV falls 22.4% → 8.1% while R² improves by 0.57.

> Standard FAO-33 crop coefficients materially overstate weather sensitivity for big
> onion under Sri Lankan dry-zone tank irrigation. This is an argument for local
> calibration of mechanistic crop models, and it is only visible because the constants
> were made estimable.

### 4.6 Detection power and identifiability

`src/identifiability.py` → `padr_power_analysis.csv`, `padr_parameter_recovery.csv`

This is what makes the negative result defensible. "We found no agro-climatic signal" is
worthless unless the model would have found one had it been there.

**Power.** Yields were simulated in which a known share of the variance is genuinely
driven by PADR's own stress index, plus noise matched to the observed within-year scale
(3.84 MT/ha), then refitted under the identical LOYO protocol.

| weather share of variance | LOYO R² | detected? |
|---|---|---|
| 0% (pure-noise control) | −0.497 ± 0.202 | — |
| **6%** | **+0.222 ± 0.038** | ✅ |
| 25% | +0.080 ± 0.115 | ✅ |
| 100% | +0.354 ± 0.013 | ✅ |

> **PADR detects a weather signal driving as little as 6% of yield variance at n = 28.
> It found none in the real panel. The true agro-climatic signal is therefore below 6%
> of variance.**

That is the quantitative form of the negative result, and it is far stronger than
"our R² was negative."

Two honesty notes. The curve is **non-monotonic** — the 25% point sits below the 6%
point — which reflects only two replicates per amplitude, not a real effect; the ±0.115
spread at 25% covers the gap. And the study used a single optimiser start from the
literature values rather than the headline fit's twenty. That is deliberately
*optimistic*: it hands the optimiser the answer's neighbourhood, so a failure to detect
under those conditions is the conservative direction for a power claim.

Figure: `outputs/plots_real/results/power_curve.png`

**Identifiability.** Fitting to data generated from known constants, error expressed as a
share of each parameter's admissible range (<10% counts as recovered):

| parameter | true | recovered | error | verdict |
|---|---|---|---|---|
| `γ` | 0.0060 | 0.0058 | 0.4% | ✅ |
| `W_max` | 147.10 | 145.37 | 1.0% | ✅ |
| `P_crit` | 96.01 | 99.18 | 1.4% | ✅ |
| `T_opt` | 28.95 | 28.60 | 2.9% | ✅ |
| `T_base` | 10.24 | 11.15 | 9.1% | ✅ |
| `Ky` | 0.966 | **1.108** | **12.8%** | ❌ returns the prior |
| `T_crit` | 35.58 | 33.64 | **16.2%** | ❌ |

"Five of seven agronomic constants are identifiable at n = 28; the FAO-33 yield response
factor and the critical temperature are not" is itself a reportable finding about
small-sample crop-model calibration — and it is exactly the kind of thing that a tight
confidence interval would otherwise have hidden.

---

## 5. Uncertainty

`src/conformal_blocked.py` → `outputs/results_real/conformal_blocked.csv`

The previous `src/conformal.py` reported `empirical_coverage = 1.000` for all twelve
models because calibration set and evaluation set were the same 28 residuals — a
tautology, not a result. Replaced with **year-blocked cross-conformal** (Barber et al.
2021): the interval for held-out year *k* is calibrated on every other year's residuals,
so no observation ever calibrates its own interval. Blocking by year rather than by row
is required because the four districts within a year share a year effect.

| model | blocked coverage | half-width (MT/ha) |
|---|---|---|
| Oracle_YearMean | 0.929 | 6.70 |
| TrainMean | 0.893 | 14.90 |
| PADR | 0.893 | 15.29 |
| DistrictMean | 0.893 | 15.84 |
| XGBoost | 0.929 | 16.42 |
| RandomForest | 0.929 | 17.63 |

Mean coverage **0.911** against a nominal 0.90 — properly calibrated. But the intervals
are ±15.3 MT/ha on a target whose mean is 17.9, i.e. roughly ±85%. **These predictions are
not decision-useful, and the honest interval is the evidence for that.**

---

## 6. The claim to defend

> Sixty-four percent of big onion yield variance in this panel is between-year and 2.2%
> between-district. Under leave-one-year-out validation the dominant component is removed
> by construction, and measurement error accounts for 54% of what remains within a year,
> capping attainable R² at 0.162. A phenology-aligned mechanistic model, fitted under
> agronomic bounds, produces a stress index varying 8% against 35% variation in observed
> yield: thermal stress is near-constant, water deficit almost never binds under tank
> irrigation, and waterlogging binds only in the 2022 crisis year. **Big onion yield in
> Sri Lanka's dry zone is not agro-climatically limited at district-season resolution.**

PADR is the instrument that establishes this. A random forest scoring −0.56 tells an
examiner nothing. A model that reports *which* mechanisms are inactive, *by how much*,
with agronomic constants estimated to plausible values and tight confidence across folds,
is a scientific finding. That is what a mechanistic model buys and a black box cannot.

### Limitations, stated plainly

1. n = 28 (4 districts × 7 years × Yala only). There is no Maha data.
2. Kurunegala and Matale are meteorologically indistinguishable at NASA POWER resolution,
   and Kurunegala's NDVI is a Matale proxy.
3. Soil is missing for Kurunegala and Matale (no SoilGrids export).
4. Six month-records were excluded as physically impossible and need DCS verification.
5. The 2022 attribution to the fertilizer import ban is consistent with the data and the
   documented timeline but is **not** established by this analysis.
6. No fertilizer, irrigation, input-cost or price data was available. Given the finding,
   these are the variables that matter most and are the obvious next data collection.

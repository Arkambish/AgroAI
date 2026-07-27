# 05 — Novelty and Research Contribution

> **Rewritten.** The previous version of this file claimed three novelties — an ML-vs-DL
> comparison, a season-injecting CNN-LSTM hybrid, and a data-source ablation — using
> synthetic-data numbers. All three have since been falsified on real data:
>
> * the season indicator is **constant** (the real panel is Yala-only), so the hybrid's
>   season-injection is inert by construction;
> * the DL models were fed a **fabricated** weather sequence, a deterministic function of
>   their own tabular inputs, so the ML-vs-DL comparison measured nothing;
> * the ablation's headline ("satellite explains 80% of variance") was a synthetic
>   artifact — on real data, district-mean NDVI cannot see a crop occupying 0.002–0.89%
>   of a district's land area.
>
> Results of record: **[PADR_FINDINGS.md](PADR_FINDINGS.md)**.

---

## The problem with the old framing

The supervisor's objection was correct and worth restating precisely. Every model in the
original project was a known method transplanted to a new crop:

| what was built | prior art it reproduces |
|---|---|
| RF / XGBoost / SVR under LOYO-CV | standard county-yield ML since ~2016 |
| CNN-LSTM hybrid | You et al., Huang et al. — maize, wheat, soybean |
| physics-residual (FAO backbone + ML on residual) | **Shahhosseini et al. 2021**, cited in the code itself |
| stacking / inverse-RMSE / convex weights | forecast-combination literature, 1969 onward |
| split conformal | Vovk et al.; already applied to yield prediction |
| SHAP + ablation | reporting practice, not contribution |

Novelty in each case reduced to *"first applied to onion"*. That is a **domain** claim.
A thesis needs a **method** claim.

## The gap that is actually here

The research problem is not "predict onion yield". It is:

> **How do you learn a crop-yield model when labels are extremely scarce (n = 28), the
> covariates are abundant (≈38,000 daily weather records), and the validation protocol
> removes the dominant source of variance by construction?**

That is not onion-specific. It describes crop forecasting across most of South Asia and
Africa, wherever crop-cutting surveys do not exist. Every method in the original project
assumed labels were scarce-but-adequate and covariates arrived pre-summarised. Here the
asymmetry is inverted, and that asymmetry is the contribution.

---

## The method: PADR

**Phenology-Aligned Differentiable Response** — a smooth, 17-parameter agronomic response
model whose crop constants are *estimated from data under agronomic bounds*, applied to
daily weather re-indexed onto thermal phenological time, fitted by gradient-based
optimisation with shrinkage toward literature values.

```
S(d,y) = ∫₀¹ β(τ) · f_T(τ) · f_W(τ) · f_WL(τ) dτ
ŷ      = (Y₀ + u_d) · S(d,y)
```

Seventeen parameters, against 44,929 in the CNN-LSTM it replaces. Implementation:
[src/padr.py](../src/padr.py), [src/phenology.py](../src/phenology.py).

### The four claims, and how each was tested

Every claim is an *arm* in [src/ablation_padr.py](../src/ablation_padr.py), so each can be
falsified independently. Two survived; two did not.

| # | claim | distinguished from | Δ R² vs control | verdict |
|---|---|---|---|---|
| **N1** | The FAO-33 and thermal constants (Ky, T_base, T_opt, T_crit, W_max) are **learned end-to-end** | Shahhosseini 2021 and the repo's own `physics_residual.py` freeze the crop model and fit ML on its *residual* — a two-stage hybrid. PADR estimates the physics itself. | **+0.566** | **supported** |
| **N4** | **Shrinkage-to-physics**: an L2 penalty pulls each constant toward its textbook value, so it moves only when the data pay for it | the statistical answer to calibrating a mechanistic model on 28 observations | **+1.166** vs heavy shrinkage | **supported** |
| **N2** | Weather integrated over **thermal phenological time**, anchored on the DCS-reported harvest date | distributed-lag yield regression uses calendar time or fixed stage windows | +0.011 | **negligible here** |
| **N3** | An explicit **waterlogging penalty**, absent from FAO-33 | a domain-driven model-structure extension for tropical wet-season onion | −0.004 | **inert** |

**Report it this way.** An ablation in which every proposed component helps is not a
credible ablation. N2 is negligible because thermal and calendar time nearly coincide when
temperature barely varies — the method is not wrong, the panel simply offers it nothing to
correct. N3 is inert because waterlogging exceeds its estimated 96 mm/7-day threshold in
3.5% of bins, in one year only.

---

## The headline result

PADR does **not** beat predicting the training mean (R² = −0.374 against −0.230). That is
the finding, not a failure, and it is defensible in three linked steps.

### 1. The target was largely fabricated, and has been rebuilt

50 of 124 month-rows were `source=synthetic`, and the fabrication reached the **target**.
Rebuilt from 87 real DCS extent/production records as Σ(MT)/Σ(ha); correlation with the
old target is only **0.68**. Six physically impossible records (up to **442 MT/ha**) were
excluded. See [PADR_FINDINGS.md §1](PADR_FINDINGS.md).

### 2. The target R² was mathematically unattainable

```
between YEAR      63.6%     ← leave-one-year-out removes this by construction
between DISTRICT   2.2%
residual          34.2%     ← 54% of which is measurement error (2.81 MT/ha per cell)

implied LOYO R² ceiling = 0.162
```

> The project's original target of **R² > 0.75 was not difficult — it was unattainable.**
> No model could have reached it on this panel under this protocol.

### 3. The agro-climatic channel is inactive, and PADR is what shows it

```
stress index S : CV =  7.95%
observed yield : CV = 34.97%
```

Thermal response is near-constant (0.86–0.91 — tropical temperatures barely move); water
deficit binds in 0–31% of bins and usually **0** (1,043 mm of rain plus tank irrigation);
waterlogging binds only in 2022. A model whose output varies 8% cannot explain a target
that varies 35%. Excluding the anomalous years makes PADR *relatively worse*, so this is
not "right model, foiled by a policy shock" — the signal is genuinely absent.

> **Big onion yield in Sri Lanka's dry zone is not agro-climatically limited at
> district-season resolution.**

**Why the mechanistic model is essential to this claim.** A random forest scoring −0.56
tells an examiner nothing. PADR reports *which* mechanisms are inactive, *by how much*,
with agronomic constants estimated to plausible values and tight across all seven folds
(Ky = 0.97 ± 0.05, T_base = 10.24 ± 0.13). That is what a mechanistic model buys and a
black box cannot.

### A secondary finding worth its own paragraph

Pinning the constants to their FAO-33 literature values (`strong_shrinkage`) produces a
stress CV of **35.3%** — almost exactly the observed yield CV — yet scores the *worst*
R² of any arm at −1.540. Learning the constants does not add explanatory power so much as
**remove spurious sensitivity**: stress CV falls 22.4% → 8.1% while R² improves by 0.57.

> Standard FAO-33 crop coefficients materially overstate weather sensitivity for big onion
> under Sri Lankan dry-zone tank irrigation. This is a direct argument for local
> calibration of mechanistic crop models — visible only because the constants were made
> estimable.

---

## Methodological corrections that stand on their own

Each of these is independently reportable, and each corrects a real defect.

| correction | before | after |
|---|---|---|
| Target definition | mean of monthly yields, ~40% fabricated | Σ(MT)/Σ(ha) from 87 real DCS records |
| Look-ahead leaks | 4 (anomalies z-scored on the full panel, global median fill, full-sample winsorisation) | anomalies standardised against the **2000–2018** pre-sample climatology; yield lags dropped as unfixable under LOYO |
| DL sequence inputs | **fabricated** from seasonal aggregates via a fixed sine curve | real daily NASA POWER series, 37,988 records |
| Dead features | 7 constants or exact linear transforms (`solar_rad`=18.0, `heat_stress_days`=0, …) | removed; `heat_stress_days` now ranges 33–116 from real daily maxima |
| Conformal coverage | `1.000` for all models — calibration set == evaluation set | year-blocked cross-conformal, coverage **0.911** vs 0.90 nominal |
| Observation weighting | none, despite extents spanning 4–1,765 ha | `sqrt(extent)`, reported weighted and unweighted |

---

## Talking points for the viva

**"What is novel about your research?"**

1. *"I make the agronomic constants of a FAO-33-style crop model estimable rather than
   assumed, and fit them under agronomic bounds with shrinkage toward literature values.
   Existing hybrids freeze the crop model and fit machine learning on its residual — I
   estimate the physics itself. Learning the constants improves R² by 0.57."*
2. *"I show that the standard FAO coefficients overstate weather sensitivity for big onion
   under Sri Lankan tank irrigation by roughly a factor of four in stress variability."*
3. *"I decompose yield variance and show the R² > 0.75 target was unattainable: 64% of
   variance is between-year and removed by leave-one-year-out, and measurement error is
   54% of what remains, capping attainable R² at 0.162."*
4. *"I demonstrate that the agro-climatic channel is inactive in this system — the stress
   index varies 8% against 35% in observed yield — and identify inputs and policy, not
   weather, as the binding constraint."*

**"Why is your R² negative?"**

*"Because leave-one-year-out removes 64% of the variance by construction and measurement
error accounts for half of the rest. The attainable ceiling is 0.162, and every model
including the naive mean sits below zero. The contribution is not the score — it is
establishing why no score was available, and which mechanisms are responsible."*

**"How is this different from existing work?"**

- Shahhosseini et al. (2021) run a crop model with fixed coefficients and fit ML on the
  residual. PADR estimates the coefficients, which is what makes them reportable as a
  scientific result.
- Distributed-lag and functional yield regressions index weather by calendar time or fixed
  growth-stage windows. PADR derives its axis from the DCS-reported harvest distribution
  and accumulated heat — though on this panel that refinement proves negligible, which is
  itself reported.
- Yield-prediction papers routinely report R² without establishing whether their
  validation protocol permits it. The variance decomposition and the attainable ceiling
  are, as far as this review found, not standard practice.

## Honest limitations

1. n = 28 (4 districts × 7 years, Yala only). No Maha data exists.
2. Kurunegala and Matale fall in one NASA POWER grid cell — byte-identical weather. Three
   distinct weather series for four districts, and Kurunegala's NDVI is a Matale proxy.
3. Soil is missing for Kurunegala and Matale (no SoilGrids export).
4. Six month-records were excluded as physically impossible and need DCS verification.
5. The 2022 collapse (9.42 vs 19.30 MT/ha, all four districts) is *consistent* with the
   April-2021 fertilizer import ban and the 2022 economic crisis, but this analysis does
   not establish that attribution — cite the policy literature.
6. No fertilizer, irrigation, input-cost or price data was available. Given the finding,
   these are the variables that matter most and are the obvious next collection effort.

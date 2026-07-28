# START HERE — Arkam's complete guide to this project

Written for someone who has never used Python, never trained a model, and has not yet
read any of the other docs. Everything is in simple English. Nothing is assumed.

Read this file top to bottom once. Then use it as a lookup.

---

## Part 0 — Read this warning first

There are **8 older explainer docs** in this folder (`00_OVERVIEW.md` … `07_HOW_TO_RUN.md`).
They were written early in the project. **Large parts of them are now wrong.** They describe
results from *fake data* and from a *broken version of the real data*.

| Document | Trust it? |
|---|---|
| **START_HERE.md** (this file) | ✅ Current |
| **PADR_FINDINGS.md** | ✅ Current — the authoritative results |
| **05_NOVELTY_AND_RESEARCH.md** | ✅ Rewritten, current |
| `02_ML_DL_FUNDAMENTALS.md` | ⚠️ Concepts are fine; the *numbers* in it are fake-data numbers |
| `00`, `01`, `03`, `04`, `06`, `07` | ❌ Numbers are stale. Read for background only |
| `FINAL_PRESENTATION_GUIDE.md` | ❌ Stale numbers |

If a number in this file disagrees with a number in an old doc, **this file and
`PADR_FINDINGS.md` are right.**

One more trap: the main `README.md` tells you to `cd frontend`. **There is no `frontend/`
folder.** It is called `dashboard/`. Use `cd dashboard`.

---

## Part 1 — What this project actually is

### The one-sentence version

You are trying to predict **how many tonnes of big onion each hectare of farmland will
produce**, in four Sri Lankan districts, *before* the harvest happens — using weather,
satellite images, and soil data.

### Why anyone would want that

Sri Lanka imports onions when local production falls short. If the government knows in
June that the September harvest will be bad, it can order imports early instead of panicking
in September when prices have already spiked. Farmers can decide what to plant. That is the
practical motivation in your proposal.

### The jargon, decoded

| Term | What it means |
|---|---|
| **Yield** | Tonnes of onion harvested per hectare of land. Written `MT/ha` (metric tonnes per hectare). This is the number you predict. |
| **Big onion** | *Allium cepa* — the normal large onion. Sri Lanka also grows "red onion" (shallot); that's a different crop, not in this project. |
| **Yala** | The growing season roughly May–August (driven by the southwest monsoon). |
| **Maha** | The growing season roughly October–March (northeast monsoon). |
| **District** | Sri Lankan administrative area. You use four: Matale, Anuradhapura, Polonnaruwa, Kurunegala. |
| **DCS** | Department of Census and Statistics — the Sri Lankan government body that publishes actual harvest figures. Your ground truth. |
| **NDVI** | "Normalised Difference Vegetation Index" — a number from 0 to 1 computed from satellite images. High = lots of green healthy plants. Low = bare soil. |
| **EVI** | Same idea as NDVI, slightly different formula, better in dense vegetation. |
| **NASA POWER** | A free NASA service that gives daily weather (temperature, rain, humidity, sunlight) anywhere on Earth. |
| **MODIS** | A NASA satellite instrument. It's where your NDVI/EVI comes from. |
| **SoilGrids** | A free global soil-property map (pH, clay %, sand %). |
| **MT/ha** | Metric tonnes per hectare. Sri Lankan big onion is normally 15–20 MT/ha. |

### The actual size of your dataset — this is the whole story

Your real data is:

```
4 districts  ×  7 years (2019–2025)  ×  Yala season only  =  28 rows
```

**Twenty-eight rows.** That is it. Not 28,000. Not 2,800. Twenty-eight.

Every strange thing about this project — every negative R², every unusual modelling
decision, the entire research contribution — flows from that number. Hold onto it.

(You *also* have 37,988 rows of daily weather and 595 satellite images per district. So you
have *mountains* of input data and *28* answers to learn from. That mismatch is literally
what your thesis is about. More in Part 6.)

---

## Part 2 — The data: where every number comes from

### 2.1 The files on disk

```
data/collected/
  FYP data(manual) - real all datas.csv        ← ⭐ THE IMPORTANT ONE (87 real DCS records)
  FYP data(manual) - onion_unique_per_key.csv  ← ☠️ CONTAMINATED, do not use as target
  FYP data(manual) - NDVI-EVI.csv              ← real MODIS satellite, 595/district
  daily_weather_by_district.csv                ← 37,988 daily NASA POWER rows
  FYP data(manual) - soil.csv                  ← SoilGrids
  FYP data(manual) - Daily weather data.csv    ← older single-point weather
  ... etc

data/synthetic/synthetic_dataset.csv           ← 100% FAKE, computer-generated
```

### 2.2 The contamination problem (you must understand this)

The file `onion_unique_per_key.csv` was the original modelling input. It has 124 monthly
rows. **50 of them are marked `source=synthetic`** — meaning somebody generated them, they
are not real measurements.

Worse: the fabrication reached **the target itself** — the yield number you are trying to
predict. So the model was being trained to predict partly-invented answers.

**The fix** (in `src/dcs_panel.py`): rebuild everything from
`FYP data(manual) - real all datas.csv`, which contains 87 genuinely-real DCS month-records
where *extent* (hectares planted) and *production* (tonnes harvested) are reported
separately. Then define yield the standard agronomic way:

```
yield(district, year)  =  total tonnes harvested  ÷  total hectares planted
                       =  Σ production_MT  ÷  Σ extent_ha
```

The corrected target correlates only **0.68** with the old one, and its standard deviation
more than doubles (4.17 → 6.37). Averaging in fake values had been flattening exactly the
variation the models were supposed to explain.

### 2.3 Three other traps that were found and fixed

1. **Thousands separators.** `Yield (MT)` contains values written `"3,091"`. Python reads
   that as text, not a number, and turns it into "missing". That single bug had turned
   Matale 2020 into 0.53 MT/ha instead of 12.16. Fixed with `pd.read_csv(..., thousands=',')`.

2. **Zero means two different things.** In the NDVI and soil columns, `0` means "we have no
   measurement". In the extent and production columns, `0` genuinely means "no harvest".
   Treating them the same corrupts everything. `src/dcs_panel.py` handles each separately.

3. **Six physically impossible records.** One row claims Matale harvested 13,271 tonnes from
   30 hectares — that is **442 MT/ha**. The onion world record is about 100 MT/ha under
   intensive irrigation. Sri Lanka averages 15–20. These are transcription errors. They are
   **excluded and logged**, never silently corrected. Full audit trail:
   `outputs/results_real/data_quality_report.csv`.

   > **Action item for you:** verify those six against the original DCS publication before
   > your viva. An examiner may ask.

### 2.4 Known limitations you must state openly

These are not embarrassments — stating them is what makes the work credible.

| Limitation | Detail |
|---|---|
| **Kurunegala = Matale, weather-wise** | Their centroids fall inside one NASA POWER grid cell. The daily weather is *byte-identical* (correlation 1.0000). You have **3 distinct weather series for 4 districts**. |
| **Kurunegala NDVI is borrowed** | No MODIS export exists for it, so it uses Matale's. Flagged per-row as `ndvi_is_proxy`. |
| **Satellite cannot see onion** | Onion covers **0.002%–0.89%** of any district's land. A district-average NDVI is measuring paddy, forest and scrub — not onion. Evidence figure: `outputs/plots_real/results/ndvi_not_crop_specific.png`. |
| **No soil for 2 districts** | SoilGrids has no export for Kurunegala or Matale. Left as missing, not faked. |
| **No Maha data** | The panel is Yala-only. |
| **No fertiliser / irrigation / price data** | And given what you found, these are probably the variables that actually matter. |

### 2.5 Observation weights — why some rows count more

District-years range from **4 hectares to 1,765 hectares**. A yield figure measured over
4 ha is far noisier than one over 1,765 ha. So each row gets a weight.

Plain area weighting spans 440×, which would effectively delete Kurunegala from the study.
So the compromise is `sqrt(extent)`, set by `OBS_WEIGHT_MODE` in `src/config.py`. Both
weighted and unweighted results are reported everywhere.

---

## Part 3 — Machine learning from absolute zero

### 3.1 What a model is

Look at a small table:

| rainfall (mm) | NDVI | yield (MT/ha) |
|---|---|---|
| 800 | 0.65 | 17 |
| 600 | 0.45 | 11 |
| 950 | 0.72 | 19 |
| 700 | 0.55 | 14 |

If I now say "rainfall 850, NDVI 0.68", you would guess about 18. You just did machine
learning in your head — you spotted a pattern and extended it.

A **model** is a mathematical function that does this automatically:
`f(rainfall, NDVI, temperature, soil_pH, …) → yield`.

**Training** = the computer searching for the version of `f` that best matches the rows it
has been shown. **Prediction** = running that `f` on a new row.

### 3.2 Vocabulary

| Word | Meaning |
|---|---|
| **Feature** (or input, or X) | One input column — rainfall, NDVI, soil pH… |
| **Target** (or label, or y) | The thing being predicted — `Avg_Yield_MT_per_Ha` |
| **Row / observation / sample** | One district in one year. You have 28. |
| **Regression** | Predicting a *number*. That's this project. |
| **Classification** | Predicting a *category* (spam / not spam). Not this project. |
| **Parameter** | A number the model *learns* by itself during training |
| **Hyperparameter** | A setting *you* choose before training (e.g. "use 500 trees") |
| **Loss** | A number measuring how wrong the model currently is. Training = making loss small. |
| **Epoch** | One complete pass through all the training rows (deep learning only) |
| **Overfitting** | The model memorises the training rows instead of learning a real pattern. It looks brilliant on data it has seen and useless on anything new. **With 28 rows this is the constant enemy.** |

### 3.3 Why you cannot just split the data randomly

The obvious way to test a model is: train on 80% of rows, test on the other 20%.

That is **wrong here**, because your rows are years. If you train on 2019, 2021, 2023, 2025
and test on 2022, the model has partly seen the future. Worse, districts within the same
year share weather — so a 2022 Matale row leaks information about the 2022 Anuradhapura row.

### 3.4 Leave-One-Year-Out cross-validation (LOYO) — the single most important idea

This is how *every* score in this project is produced.

```
For each year Y in 2019 … 2025:
    Hide every row where Year == Y                 ← the test set (4 rows)
    Train a fresh model on the other 6 years       ← the training set (24 rows)
    Predict the 4 hidden rows
    Save those predictions

Stack all 28 saved predictions together → compute RMSE, MAE, R² once.
```

The saved predictions are called **out-of-fold (OOF)** predictions. Every row gets predicted
exactly once, by a model that had never seen that row's year. That is an honest score.

You'll see files named `outputs/results_real/oof_*.json` — those are exactly this.

**The model is thrown away and rebuilt from scratch every fold.** That matters. It means
seven completely separate models are trained, and their held-out predictions are pooled.

### 3.5 The scores, and what they mean

| Metric | Plain English | Better when |
|---|---|---|
| **RMSE** | Typical size of your error, in MT/ha. Punishes big misses hard. | smaller |
| **MAE** | Average error, in MT/ha. Simpler, gentler. | smaller |
| **MAPE** | Average error as a percentage. | smaller |
| **R²** | See below. | larger, max 1.0 |

**R² is the one people misread, so get it exactly right:**

- `R² = 1.0` → perfect prediction.
- `R² = 0.0` → your model is exactly as good as **just always guessing the average**.
- `R² < 0` → your model is **worse than always guessing the average**.

R² is not a percentage score out of 100. It compares you against one specific dumb
competitor: the mean. Negative R² means the dumb competitor won.

Your models mostly have **negative R²**. Part 6 explains why that is an arithmetic fact
about your data, not a bug in your code — and why it became your research finding.

### 3.6 Data leakage — the sin that invalidates results

**Leakage** is when information from the test set sneaks into training. It makes scores look
great and the model useless in reality. Four leaks were found and fixed in this project:

| Leak | What was happening | Fix |
|---|---|---|
| `ndvi_anomaly`, `drought_index_spi` | These are "how unusual was this year", computed by comparing against the average of **all** years 2019–2025 — including the held-out one. | Compare against **2000–2018** instead, which no fold ever tests on. Leak removed by construction. |
| Median-filling missing values | Median computed over the whole dataset, including test rows. | Removed. |
| Winsorising outliers | Percentile cutoffs computed over the whole dataset. | Removed; replaced by an explicit physical-plausibility filter. |
| Yield lag features (`prev_year_yield`) | With 2022 held out, the 2023 training row carries 2022's observed yield as an input. Direct leak. | **Dropped entirely.** They also buy nothing — only 2.2% of variance is between-district, which is all a "last year was similar" feature can capture. |

### 3.7 Feature scaling

Rainfall is in the hundreds (850). NDVI is between 0 and 1 (0.65). Some models see "850" as
inherently more important than "0.65" purely because it's a bigger number.

**StandardScaler** fixes this: subtract the mean, divide by the standard deviation, so every
feature ends up centred at 0 with spread 1.

- **Tree models** (Random Forest, XGBoost) don't need it — a tree just asks "is rainfall
  above 800?" and units are irrelevant.
- **SVR and all neural networks** need it badly.

**Critical rule:** fit the scaler on the *training* rows only, then apply it to the test
rows. Fitting on everything is leakage. Look at `src/baselines.py:106-111` — the scaler is
created *inside* the fold loop. That's deliberate.

---

## Part 4 — ⚠️ The three pipelines in this repo (the most confusing thing)

This repo contains **three different experiments** that write to different folders. Mixing
up their numbers is the easiest mistake to make.

### Pipeline A — Synthetic (fake data)

```
Command:  python main.py
Data:     data/synthetic/synthetic_dataset.csv   ← generated by a random-number formula
Outputs:  outputs/models/  outputs/results/  outputs/plots/
Scores:   Random Forest R² = 0.84   ← GORGEOUS AND MEANINGLESS
```

This exists so the code can be developed and demoed before real data arrived. The 0.84 is
the computer successfully learning a formula that the computer itself invented. **Never put
this number in your report as a result.** It is a software test, not science.

### Pipeline B — "Real", old version ⚠️ contaminated

```
Command:  python main.py --real
Data:     onion_unique_per_key.csv   ← ~40% fabricated, INCLUDING the target
Outputs:  outputs/models_real/  outputs/results_real/model_comparison.csv
Scores:   PhysResidual R² = 0.09,  RMSE ≈ 4.0
```

This is the trap. It *looks* like the real pipeline, and its output file sits right next to
the good ones. **Its target variable is 40% invented**, and its RMSE of ~4.0 looks better
than the corrected pipeline's ~7.3 only because the fake data was artificially smooth.

The file `outputs/results_real/model_comparison.csv` comes from here. Treat it as historical.

### Pipeline C — Real, corrected ✅ this is your thesis

```
Commands: python src/baselines.py, src/run_padr.py, src/ablation_padr.py, …
Data:     87 real DCS records + 37,988 daily weather rows + real MODIS
Outputs:  outputs/results_real/baseline_comparison.csv
          outputs/results_real/padr_comparison.csv
          outputs/results_real/padr_ablation.csv
          outputs/results_real/variance_decomposition.json
          outputs/plots_real/
Scores:   best achievable R² = −0.23 (TrainMean),  PADR = −0.374,  RMSE ≈ 7.3
```

**This is what `PADR_FINDINGS.md` documents and what you defend at viva.**

### The cheat sheet

| If you see… | It came from | Use it? |
|---|---|---|
| R² ≈ 0.84, RMSE ≈ 2.1 | Pipeline A (fake) | ❌ Never as a result |
| R² ≈ 0.09, RMSE ≈ 4.0 | Pipeline B (contaminated) | ❌ Historical only |
| R² ≈ −0.23 … −0.37, RMSE ≈ 7–8 | Pipeline C (corrected) | ✅ **Yes** |

The two "real" numbers aren't comparable at all — **they are predicting two different
target variables.** RMSE 4.0 on a target with sd 4.17 is worse than RMSE 7.3 on a target
with sd 6.37, once you account for what each was measuring.

---

## Part 5 — Every model, explained simply

You built twelve. Here is each one, what it does, and how it did.

### The baselines — the honest competition (`src/baselines.py`)

These use no cleverness at all. Any real model must beat them, or it has earned nothing.

| Baseline | Rule |
|---|---|
| **TrainMean** | "Predict the average of every year I was trained on." Uses zero features. |
| **DistrictMean** | "Predict this district's historical average." |
| **Persistence** | "Predict whatever this district got last year." |
| **Oracle_YearMean** | *Cheating on purpose:* predict the held-out year's own true average. Impossible in reality. Included to show the ceiling that perfect knowledge of the year effect would buy. |

**TrainMean beat every feature-based model you built.** That is the headline. It's not a
coding failure — Part 6 shows it is arithmetic.

### The classical ML models

**1. Random Forest** (`src/ml_models.py:95`)
Imagine 500 people each shown a random subset of your rows and a random subset of your
columns, each drawing a simple flowchart of yes/no questions ("Is rainfall > 800? → Is NDVI
> 0.6? → predict 18"). Then average all 500 answers. Averaging many slightly-wrong opinions
cancels out individual mistakes. That is a random forest; each flowchart is a *decision tree*.
Robust, hard to break, needs no scaling.
→ **R² = −0.556**

**2. XGBoost** (`src/ml_models.py:127`)
Instead of 500 independent trees, build them *one after another*, where each new tree is
trained specifically on the mistakes the previous trees made. This is called **gradient
boosting**. Usually the strongest model on tabular data.

Your version has a nice touch: **monotone constraints**. You told XGBoost that predicted
yield must never *decrease* when greenness (NDVI/EVI) increases. That's crop science
hard-wired into the model so it can't learn something biologically absurd from 28 noisy rows.
→ **R² = −0.360** (the best of the ML models)

**3. SVR — Support Vector Regression** (`src/ml_models.py:169`)
Fit a tube of a given width through the data points, as flat as possible, ignoring any point
that already falls inside the tube. Only the points on or outside the tube edges ("support
vectors") shape the answer. The `rbf` kernel lets the tube bend. Needs scaling.
→ **R² = −0.573**

### The deep learning models (`src/dl_models.py`)

A **neural network** is layers of simple multiply-and-add units. Each layer transforms
numbers into other numbers; stacking layers lets it represent complicated shapes. It learns
by: guess → measure error → nudge every internal weight slightly in the direction that
reduces error → repeat thousands of times. One full pass over the data is an **epoch**.

**4. LSTM** — "Long Short-Term Memory". Designed for *sequences*. It reads month 1, then
month 2, … keeping an internal memory, and can learn things like "rain in month 3 matters
more than rain in month 1". `SEQUENCE_LENGTH = 5` months, 4 weather variables per month.
30,625 parameters.

**5. BiLSTM** — the same, but reading the sequence forwards *and* backwards, then combining.
77,601 parameters.

**6. 1D-CNN** — a **convolution** is a small sliding window that scans the input looking for
local patterns (in images: edges and corners). Here it slides over your feature list looking
for useful *combinations* of adjacent features. 8,577 parameters.

**7. Hybrid CNN-LSTM** — your original proposed novelty. A CNN branch reads satellite
features, an LSTM branch reads the weather sequence, and a `season_indicator` (Yala=1,
Maha=0) is glued on before the final layer so the model can behave differently per season.
44,929 parameters.

> **⚠️ Be honest about the hybrid in your report.** Two things killed it:
> 1. **The season indicator is constant.** Your real panel is Yala-only, so it is 1 for every
>    single row. A constant input carries zero information. The novelty is inert *by
>    construction*.
> 2. **The weather sequences were fabricated.** `src/feature_engineer.py` invented monthly
>    trajectories from seasonal averages using a fixed sine curve. So the LSTM's "time
>    series" was a deterministic function of the very numbers the tabular models already had.
>    It contained no new information at all.
>
> This is why the hybrid scores **R² = −7.05** — the worst of everything. 44,929 parameters
> fitted to 24 training rows. Report this as a finding about deep learning under data
> scarcity, which is genuinely interesting, rather than pretending it worked.

### The hybrid / combination models

**8. Symbolic Regression** (`src/symbolic.py`) — instead of a black box, search over actual
algebraic formulas (`+`, `−`, `×`, `÷`, `sqrt`) to find a short human-readable equation that
fits. Output: `outputs/results_real/symbolic_equation.txt`. Value is interpretability, not
accuracy.

**9. Physics-Residual Hybrid** (`src/physics_residual.py`) — two stages:
   - **Stage 1:** a hand-written agronomy formula with *no learning at all*, computing a
     crop-suitability score from growing-degree-days, water stress (FAO-33) and heat stress.
   - **Stage 2:** a Random Forest learns *only the leftover error* (actual − stage 1), then
     the two are added back together.

   The logic: the physics already explains part of the signal, so the ML has less left to
   fit on 28 rows, so it overfits less. Honest framing — this is an established idea
   (Shahhosseini et al. 2021, APSIM + ML residual); your contribution is applying it here.

**10–12. Stacking** (`src/stacking.py`) — don't train anything new; just *combine* the
predictions the other models already made.
   - `StackMean` — plain average. Zero fitted parameters, so it cannot overfit.
   - `StackInvRMSE` — weighted average, better models get bigger weight.
   - `StackConvex` — learn optimal weights, forced to be non-negative and sum to 1.

   The known research question here is the **"forecast combination puzzle"** (Stock & Watson
   2004): on small samples the dumb equal-weight average often beats the cleverly learned
   blend. Your pipeline tests whether that holds on your data. Weights are fitted using only
   training years — nested LOYO, no leakage.

**13. PADR** — your actual research contribution. Part 6.

---

## Part 6 — PADR, and the real research story

### 6.1 The problem PADR solves

Your supervisor's objection was correct, and worth restating: every model above is a known
method applied to a new crop. "First applied to onion" is a **domain** claim. A thesis needs
a **method** claim.

The genuine research question here is:

> **How do you learn a crop-yield model when the labels are extremely scarce (n = 28), the
> covariates are abundant (≈38,000 daily weather records), and the validation protocol
> deliberately removes the dominant source of variance?**

That is not about onions. It describes crop forecasting across most of South Asia and Africa,
anywhere without crop-cutting surveys.

### 6.2 What PADR is

**PADR = Phenology-Aligned Differentiable Response** (`src/padr.py`, `src/phenology.py`).

```
S(d,y) = ∫₀¹ β(τ) · f_T(τ) · f_W(τ) · f_WL(τ) dτ
ŷ      = (Y₀ + u_d) · S(d,y)
```

In English: walk through the growing season from planting (τ=0) to harvest (τ=1). At each
moment compute three stress factors, each between 0 and 1:

- `f_T` — **thermal stress.** 0 if it's too cold or too hot, 1 at the optimum temperature.
- `f_W` — **water stress.** A simple soil-water bucket: rain fills it, evaporation drains it.
  1 if there is enough water, dropping as the bucket empties.
- `f_WL` — **waterlogging.** 1 normally; drops when 7-day rainfall exceeds a threshold and
  the roots drown. *This term does not exist in the standard FAO-33 model.*

Multiply the three together, weight by `β(τ)` (a learned curve saying which part of the
season the crop is most sensitive during), and integrate over the whole season. You get a
single **stress index S** between 0 and 1. Multiply by the district's attainable yield.

**17 parameters total. The CNN-LSTM it replaces has 44,929.**

### 6.3 Phenological time — why not calendar time

Crops don't develop by the calendar; they develop by **accumulated heat**. This is measured
in **growing degree-days (GDD)**: each day contributes `(average temperature − 10°C)`, and
the crop matures once it has banked enough total heat.

So instead of "month 3 of the season", PADR uses `τ = heat accumulated so far ÷ heat
required`. A hot spell pushes the crop further along; a cool one slows it.

Planting date is found by walking heat units *backwards* from the harvest date, which comes
from the DCS records themselves (production is reported by month, so the extent-weighted
average of that distribution is the harvest date — genuinely crop-specific, and it moves
across a 51-day span, DOY 228–279).

**Result: 28 of 28 district-years anchored, zero fallbacks.** And the output is
agronomically sensible: hot Anuradhapura (27.9 °C) runs 78–86 day seasons, while cooler
Matale and Kurunegala (25.1 °C) need 90–99 days to bank the same heat. *The calendar
duration varies precisely because thermal time doesn't.*

> **Why not anchor on the satellite green-up curve?** That's the obvious approach and it was
> tried. It failed on **25 of 28** district-years, because onion occupies under 1% of any
> district's land — the satellite is looking at paddy and forest. That failure is documented
> as evidence (`outputs/plots_real/results/ndvi_not_crop_specific.png`), not hidden.

### 6.4 The four novelty claims — and the two that failed

Each claim is an *arm* in `src/ablation_padr.py`, meaning each can be independently
disproved. **An ablation where every proposed component turns out to help is not a credible
ablation.** Two of yours survived; two did not. Report it exactly that way.

| # | Claim | Δ R² vs its control | Verdict |
|---|---|---|---|
| **N1** | The crop constants (`Ky`, `T_base`, `T_opt`, `T_crit`, `W_max`) are **learned from data**, not fixed at textbook values | **+0.566** | ✅ **strongly supported** |
| **N4** | **Shrinkage to physics** — a penalty pulls each constant toward its textbook value, so it only moves when the data pay for it | **+1.166** vs heavy shrinkage | ✅ **strongly supported** |
| — | `β(τ)` learned vs forced flat | +0.055 | 🟡 modest but positive |
| **N2** | Weather integrated over **thermal** time rather than calendar time | +0.011 | ❌ **negligible on this panel** |
| **N3** | An explicit **waterlogging** penalty | −0.004 | ❌ **inert, marginally harmful** |

**Why N2 came out negligible:** thermal time and calendar time nearly coincide when
temperature barely varies — which is exactly the tropical regime here. The method isn't
wrong; the panel offers it nothing to correct.

**Why N3 is inert:** waterlogging exceeds its 96 mm/7-day threshold in 3.5% of bins, in one
year only. Not enough exceedance to earn its two parameters.

### 6.5 The most interesting result in your whole project

Look at the `strong_shrinkage` arm — the one where the constants are pinned hard to their
FAO-33 textbook values:

| arm | R² | stress CV |
|---|---|---|
| **full PADR** (learned constants) | **−0.374** | **8.14%** |
| `fixed_physics` (frozen at literature) | −0.940 | 22.39% |
| `strong_shrinkage` (pinned to literature) | **−1.540** | **35.33%** |
| *(observed yield, for reference)* | — | *34.97%* |

Pinning the constants to FAO-33 produces a stress index varying **35.33%** — almost exactly
matching the 34.97% variation in real yield. And it scores the **worst R² of any arm**.

Read that carefully. The textbook constants generate roughly the right *amount* of
variability, but place it in the **wrong years**. Learning the constants doesn't add
explanatory power so much as **remove spurious sensitivity** — stress CV falls from 22.4% to
8.1% while R² improves by 0.57.

> **The claim:** standard FAO-33 crop coefficients materially overstate weather sensitivity
> for big onion under Sri Lankan dry-zone tank irrigation. That is a direct argument for
> locally calibrating mechanistic crop models — and it is only visible because the constants
> were made estimable in the first place.

### 6.6 The learned constants — the scientific output

Mean ± sd across the 7 LOYO folds:

| parameter | learned | literature | identifiable at n=28? | reading |
|---|---|---|---|---|
| `T_opt` | **28.95 ± 0.95** | 24.0 | ✅ 2.9% | pulled well up — adaptation to a hot dry zone |
| `W_max` | **147.1 ± 6.2 mm** | 100 | ✅ 1.0% | deeper effective water store than assumed |
| `T_base` | **10.24 ± 0.13** | 10.0 | ✅ 9.1% | confirms the standard base temperature |
| `γ` (waterlogging) | 0.006 ± 0.001 | — | ✅ 0.4% | newly estimated, no prior exists |
| `P_crit` | 96.0 ± 5.2 mm/7d | — | ✅ 1.4% | newly estimated |
| `T_crit` | 35.58 ± 0.71 | 35.0 | ❌ **16.2%** | **do not report as a finding** |
| `Ky` | 0.97 ± 0.05 | 1.1 (FAO-33) | ❌ **12.8%** | **do not report as a finding** |

### 6.7 ⚠️ The `Ky` correction — a lesson worth learning properly

An earlier draft looked at `Ky = 0.97 ± 0.05` — beautifully tight across all seven folds —
and concluded that big onion is less water-sensitive than FAO-33's generic 1.1.

**That claim was withdrawn.** Here's why, and it's the most important methodological lesson
in your project.

`src/identifiability.py` runs a **parameter recovery experiment**: generate fake yield data
using a *known* `Ky = 0.966`, then ask PADR to recover it. It returns **1.108** — it
reproduces the literature prior, not the truth.

The shrinkage penalty that makes the model estimable at n=28 also *pins* any parameter the
data cannot constrain to its prior value. The resulting tight fold-to-fold spread is the
**prior's** stability, not evidence from your data.

> **Precision is not accuracy.** A tight confidence interval can be measuring your own
> assumption. Five of seven constants recover correctly; `Ky` and `T_crit` do not. Saying so
> is itself a reportable finding about small-sample crop-model calibration.

---

## Part 7 — The results, and exactly what to say about them

### 7.1 The scoreboard (Pipeline C, corrected data, LOYO, n=28)

| model | RMSE | MAE | R² |
|---|---|---|---|
| *Oracle: true year mean (cheating)* | *3.775* | *3.238* | *+0.636* |
| **TrainMean** | **6.938** | 5.457 | **−0.230** |
| DistrictMean | 7.218 | 5.419 | −0.331 |
| XGBoost | 7.296 | 5.456 | −0.360 |
| PADR | 7.333 | 6.016 | −0.374 |
| RandomForest | 7.803 | 5.826 | −0.556 |
| SVR (RBF) | 7.847 | 6.008 | −0.573 |
| Persistence | 9.033 | 7.327 | −1.085 |

**Every feature-based model loses to predicting the training mean.**

### 7.2 Why — the variance decomposition (`src/variance_decomposition.py`)

Split the total variation in yield into three buckets:

| component | share |
|---|---|
| between **YEAR** | **63.6%** |
| between **DISTRICT** | 2.2% |
| residual | 34.2% |

Now notice: **leave-one-year-out deletes the year component by construction.** You hold out
2022 entirely, so nothing in your training data can tell you 2022 was a bad year. You have
thrown away 63.6% of the signal on purpose — because that's what honest validation requires.

That leaves 2.2% + 34.2% to work with. And of the within-year variation, **53.6% is
measurement error** — each cell's yield is an average over only 2–5 monthly records, giving
a standard error of 2.81 MT/ha per cell.

Subtract both:

```
implied LOYO R² ceiling = 0.162
```

> **Your proposal's target of R² > 0.75 was not difficult. It was unattainable.** No model,
> however sophisticated, could have reached it on this panel under this protocol.

This is arithmetic, not a modelling failure. It is also, by a distance, the strongest thing
you can say at viva.

### 7.3 Why PADR specifically cannot win

```
stress index S : CV =  7.95%    (range 0.69 – 0.94)
observed yield : CV = 34.97%    (range 3.63 – 33.58)
```

**A model whose output varies 8% cannot explain a target that varies 35%.** No amount of
tuning fixes that — it is structural. Component by component:

| component | behaviour |
|---|---|
| thermal `f_T` | near-constant 0.86–0.91 — tropical temperatures barely move year to year |
| water deficit `f_W` | mostly *exactly* 1.0 — 1,043 mm of rain plus tank irrigation means drought rarely binds |
| waterlogging `f_WL` | 1.0 except in 2022 |

And this isn't just the weird years. Excluding 2022 and 2024, PADR gets **relatively worse**
(−0.542 vs TrainMean's −0.099). The agro-climatic signal is genuinely absent, not merely
masked by a shock.

### 7.4 The 2022 collapse

| year | 2019 | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| mean MT/ha | 17.97 | 13.85 | 18.98 | **9.42** | 18.33 | 26.90 | 19.78 |

2022 collapsed across all four districts (Matale down to 3.63 MT/ha, consistently low across
all three of its month-records — so a real crop failure, not a transcription error). The
timing matches Sri Lanka's April-2021 chemical fertiliser import ban and the 2022 economic
crisis.

> **Cite this from the policy literature. Do not infer it from your panel.** Your analysis is
> *consistent* with that explanation; it does not establish it. No weather-driven model can
> predict a policy decision, and 2022 will remain the worst fold for everything.

### 7.5 Detection power — what makes the negative result defensible

"We found no weather signal" is worthless unless you can show you *would have found one had
it been there*. `src/identifiability.py` proves exactly that.

Simulate yields where a known share of variance is genuinely driven by PADR's own stress
index, add realistic noise, refit under identical LOYO:

| weather share of variance | LOYO R² | detected? |
|---|---|---|
| 0% (pure noise control) | −0.497 ± 0.202 | — |
| **6%** | **+0.222 ± 0.038** | ✅ |
| 25% | +0.080 ± 0.115 | ✅ |
| 100% | +0.354 ± 0.013 | ✅ |

> **PADR detects a weather signal driving as little as 6% of yield variance at n = 28. It
> found none in the real panel. Therefore the true agro-climatic signal is below 6% of
> variance.**

That is the quantitative form of your negative result, and it is enormously stronger than
"our R² was negative."

*(Two honesty notes to keep in the report: the curve is non-monotonic — the 25% point sits
below the 6% point — which reflects only two replicates per amplitude, not a real effect;
the ±0.115 spread covers the gap. And the study used a single optimiser start from the
literature values rather than twenty, which is deliberately optimistic and therefore the
conservative direction for a power claim.)*

### 7.6 Uncertainty intervals (`src/conformal_blocked.py`)

The old `src/conformal.py` reported `empirical_coverage = 1.000` for every model — because
the calibration set and the evaluation set were the same 28 residuals. That's a tautology,
not a result.

Replaced with **year-blocked cross-conformal** (Barber et al. 2021): the interval for
held-out year *k* is calibrated on every *other* year's residuals, so no observation ever
calibrates its own interval. Blocking by year rather than by row is required because the
four districts within a year share a year effect.

Mean coverage **0.911** against a nominal 0.90 — properly calibrated. **But** the intervals
are ±15.3 MT/ha on a target averaging 17.9 — roughly ±85%.

> **These predictions are not decision-useful, and the honest interval is the evidence for
> that.** Say this plainly. It's far better than shipping a dashboard that implies precision
> you don't have.

### 7.7 The claim you defend

> Sixty-four percent of big onion yield variance in this panel is between-year and 2.2%
> between-district. Under leave-one-year-out validation the dominant component is removed by
> construction, and measurement error accounts for 54% of what remains within a year, capping
> attainable R² at 0.162. A phenology-aligned mechanistic model, fitted under agronomic
> bounds, produces a stress index varying 8% against 35% variation in observed yield: thermal
> stress is near-constant, water deficit almost never binds under tank irrigation, and
> waterlogging binds only in the 2022 crisis year. **Big onion yield in Sri Lanka's dry zone
> is not agro-climatically limited at district-season resolution.**

PADR is the *instrument* that establishes this. A random forest scoring −0.56 tells an
examiner nothing. A model that reports **which** mechanisms are inactive, **by how much**,
with agronomic constants estimated to plausible values and a power analysis bounding what it
could have detected — that is a scientific finding. That is what a mechanistic model buys
and a black box cannot.

---

## Part 8 — How to run everything (verified commands)

All commands assume you start here:

```bash
cd /Users/arqm7/Documents/FYP/Model
```

### 8.0 One-time setup (already done on your machine)

```bash
python3.12 -m venv .venv          # TensorFlow does not support 3.13/3.14
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt   # ~2 GB, mostly TensorFlow
```

Your `.venv` already exists with Python 3.12.9, TensorFlow 2.17.1, scikit-learn 1.5.2,
XGBoost 3.2.0, Flask 3.1.3. Nothing to reinstall.

### 8.1 Activate the environment — every new terminal

```bash
source .venv/bin/activate
```

Your prompt changes to start with `(.venv)`. **If you forget this, you get
`ModuleNotFoundError` on everything.** That single mistake causes about 90% of "it's broken"
moments.

### 8.2 The corrected real pipeline (Pipeline C) — what your thesis uses

These scripts live in `src/` and import each other by bare name, so they need two things
set: `DATA_VARIANT=real` (so outputs go to `outputs/*_real/`) and `PYTHONPATH=src` (so the
imports resolve).

```bash
# Step 1 — build and audit the real data panel. Fast. Start here.
DATA_VARIANT=real PYTHONPATH=src python src/dcs_panel.py

# Step 2 — the phenological (thermal-time) alignment
DATA_VARIANT=real PYTHONPATH=src python src/phenology.py

# Step 3 — honest baselines: TrainMean, DistrictMean, Persistence, RF, XGB, SVR, Oracle
DATA_VARIANT=real PYTHONPATH=src python src/baselines.py

# Step 4 — variance decomposition and the attainable R² ceiling
DATA_VARIANT=real PYTHONPATH=src python src/variance_decomposition.py

# Step 5 — ⭐ fit PADR under LOYO and score it against the baselines
DATA_VARIANT=real PYTHONPATH=src python src/run_padr.py

# Step 6 — the 7-arm ablation that tests each novelty claim (slowest, several minutes)
DATA_VARIANT=real PYTHONPATH=src python src/ablation_padr.py

# Step 7 — power analysis + parameter recovery (this is what withdrew the Ky claim)
DATA_VARIANT=real PYTHONPATH=src python src/identifiability.py

# Step 8 — year-blocked conformal prediction intervals
DATA_VARIANT=real PYTHONPATH=src python src/conformal_blocked.py

# Step 9 — regenerate every PADR figure
DATA_VARIANT=real PYTHONPATH=src python src/figures_padr.py
```

Run them in that order the first time — later steps read files earlier ones write.

**Typing that prefix every time is tedious. Make an alias once per terminal:**

```bash
alias fyp='DATA_VARIANT=real PYTHONPATH=src python'
# then simply:
fyp src/run_padr.py
```

### 8.3 The old pipelines (for reference / regenerating the demo)

```bash
python main.py                      # Pipeline A — synthetic. ~6 min. Trains all 12 models.
python main.py --skip-dl --skip-shap   # ~1 min, ML only
python main.py --real               # Pipeline B — ⚠️ contaminated target. Historical only.
```

`main.py` flags: `--skip-eda --skip-ml --skip-dl --skip-symbolic --skip-physics
--skip-stacking --skip-ablation --skip-shap`

`main.py` handles `sys.path` itself, so it does **not** need the `PYTHONPATH=src` prefix.

### 8.4 Reading your results

```bash
cat outputs/results_real/baseline_comparison.csv   # ✅ the real scoreboard
cat outputs/results_real/padr_comparison.csv       # ✅ PADR vs baselines
cat outputs/results_real/padr_ablation.csv         # ✅ the 7 ablation arms
cat outputs/results_real/variance_decomposition.json  # ✅ the 0.162 ceiling
cat outputs/results_real/padr_power_analysis.csv   # ✅ detection power
cat outputs/results_real/data_quality_report.csv   # ✅ every flagged record

open outputs/plots_real/results/       # all figures (macOS)
```

---

## Part 9 — The backend and the dashboard

### 9.1 What "the backend" is

`src/api.py` is a **Flask** web server. Flask turns Python functions into web addresses.
When something sends an HTTP request to `http://localhost:5050/predict`, Flask runs your
`predict()` function and sends back the answer as JSON.

The point: your trained model lives as a file on disk (`outputs/models/rf_best.pkl`). The
dashboard is a website written in TypeScript that cannot open a Python model file. The API
sits in between — it loads the model once at startup, and answers questions over HTTP.

### 9.2 Starting it

```bash
source .venv/bin/activate
PORT=5050 python src/api.py
```

**Use port 5050, not 5000.** macOS runs AirPlay Receiver on 5000, and you'll get
"Address already in use".

You should see:

```
[api] Initialized SHAP TreeExplainer for RandomForest
[api] Loaded RandomForest (metrics={...})
[api] Loaded context dataset (136 rows, 4 districts) + default cascade
 * Running on http://127.0.0.1:5050
```

Leave that terminal running. Open a **second** terminal for anything else.

To serve the real-data models instead of the synthetic ones:

```bash
DATA_VARIANT=real PORT=5050 python src/api.py
```

### 9.3 The endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/health` | GET | Is the server alive, and which model is loaded |
| `/predict` | POST | Send field conditions as JSON → get predicted yield + interval + SHAP |
| `/models/compare` | GET | The model comparison table |
| `/feature-importance` | GET | Top-15 SHAP features |
| `/equation` | GET | The symbolic-regression equation |
| `/context` | GET | Pre-fill values for the form (`?district=&season=&year=`) |
| `/baseline` | GET | Historical yield stats for a district+season |
| `/districts` | GET | Districts / seasons / years available in the loaded dataset |

### 9.4 Testing it (second terminal)

```bash
curl http://localhost:5050/health

curl -X POST http://localhost:5050/predict \
  -H 'Content-Type: application/json' \
  -d '{"district":"Matale","season":"Yala","season_total_rainfall":850,
       "season_avg_temp":28.5,"season_mean_ndvi":0.65,"soil_ph":6.2}'
```

`curl` is just a command-line tool for sending web requests. `-X POST` = "this is a submit,
not a fetch". `-H` sets a header saying the body is JSON. `-d` is the data.

### 9.5 One genuinely nice design detail in the API

The model needs **32 features**, but the farmer form asks for maybe 6. What fills the other 26?

Look at `_resolve_features()` in [src/api.py:140](../src/api.py#L140). Each missing feature is
resolved through a cascade:

```
user's value → (district, season) mean → district mean → season mean → global mean → 0.0
```

And critically, the response reports **where every single value came from**:

```json
"data_completeness": {"n_features": 32, "n_user_supplied": 2,
                      "n_grounded": 32, "n_zero_filled": 0}
```

Before this, missing features were silently zero-filled — so the API would return a
confident-looking number built from `soil_ph = 0` and `prev_year_yield = 0`. Provenance
tracking is the honest fix, and it's worth mentioning in your report.

### 9.6 The dashboard (Shathurya's component)

```bash
cd dashboard        # ⚠️ NOT "frontend" — the README is out of date
npm install         # first time only; node_modules is not currently installed
npm run dev         # → http://localhost:3000
```

Needs Node ≥ 20 (you have v24.18.0 ✓). It reads `dashboard/.env.local`, which already
points at `http://localhost:5050`. Set `NEXT_PUBLIC_USE_MOCK=true` in that file to run the
UI with bundled sample data when the Flask API isn't running.

Run the Flask API and the dashboard in **two separate terminals**, both open at once.

---

## Part 10 — What every file does

### The corrected real pipeline (Pipeline C) — read these first

| File | Purpose |
|---|---|
| [src/dcs_panel.py](../src/dcs_panel.py) | Builds the authoritative 28-row panel from 87 real DCS records. Handles the thousands separators, the zero-means-missing columns, the six impossible records, and the observation weights. **Start reading here.** |
| [src/features_real.py](../src/features_real.py) | Joins the panel to real daily weather and real MODIS NDVI. Computes leak-free anomalies against the 2000–2018 climatology. |
| [src/phenology.py](../src/phenology.py) | The thermal-time axis (novelty N2). Locates planting by walking growing-degree-days backwards from the DCS harvest date. |
| [src/padr.py](../src/padr.py) | ⭐ The PADR model itself. 17 parameters, fitted with `scipy` L-BFGS-B under agronomic box bounds. |
| [src/run_padr.py](../src/run_padr.py) | Runs PADR under LOYO and scores it against the baselines. |
| [src/baselines.py](../src/baselines.py) | TrainMean / DistrictMean / Persistence / RF / XGB / SVR / Oracle. The honest scoreboard. |
| [src/variance_decomposition.py](../src/variance_decomposition.py) | Computes the 63.6% / 2.2% / 34.2% split and the 0.162 ceiling. |
| [src/ablation_padr.py](../src/ablation_padr.py) | The 7 arms that test each novelty claim independently. |
| [src/identifiability.py](../src/identifiability.py) | Power analysis + parameter recovery. **The most important methodological file in the project.** |
| [src/conformal_blocked.py](../src/conformal_blocked.py) | Year-blocked cross-conformal prediction intervals. |
| [src/data_collection/nasa_power.py](../src/data_collection/nasa_power.py) | Downloads 37,988 daily weather rows from NASA POWER (4 district centroids, 2000–2025). |

### The original pipeline (A and B)

| File | Purpose |
|---|---|
| [main.py](../main.py) | Orchestrator. Reads the `--skip-*` flags and calls each stage in order. |
| [src/config.py](../src/config.py) | **All settings live here.** Hyperparameter grids, feature lists, file paths, agronomic constants. Change knobs here, never inside model files. |
| [src/data_loader.py](../src/data_loader.py) | Loads real CSVs, or generates the synthetic dataset if they're missing. |
| [src/preprocessor.py](../src/preprocessor.py) | Cleaning: dedupe, type coercion, missing values. |
| [src/feature_engineer.py](../src/feature_engineer.py) | Builds the feature matrix + the (fabricated) monthly sequences the DL models consume. |
| [src/ml_models.py](../src/ml_models.py) | Random Forest, XGBoost, SVR + the shared LOYO machinery. |
| [src/dl_models.py](../src/dl_models.py) | LSTM, BiLSTM, CNN, Hybrid CNN-LSTM (Keras/TensorFlow). |
| [src/symbolic.py](../src/symbolic.py) | Symbolic regression — evolves a readable equation. |
| [src/physics_residual.py](../src/physics_residual.py) | FAO-33 backbone + Random Forest on the residual. |
| [src/stacking.py](../src/stacking.py) | Three combiners + the forecast-combination-puzzle test. |
| [src/ablation.py](../src/ablation.py) | The 6-experiment data-source ablation. |
| [src/explainer.py](../src/explainer.py) | SHAP feature attributions. |
| [src/evaluator.py](../src/evaluator.py) | Builds `model_comparison.csv` and `final_summary.txt`. |
| [src/eda.py](../src/eda.py) | Exploratory plots: distributions, correlations, time series. |
| [src/visualizer.py](../src/visualizer.py) | Shared plotting helpers. |
| [src/api.py](../src/api.py) | The Flask REST API. |

### Report and figure generation

`generate_figures.py`, `figures_padr.py`, `generate_poster_figures.py`,
`generate_poster_pdf.py`, `generate_deck_figures.py`, `generate_deck_pptx.py`,
`generate_interim_docx.py`, `generate_final_docx.py`, `final_report_content.py`

These produce `outputs/Final_Report_AgroAI.docx`, `outputs/Final_Presentation_AgroAI.pptx`,
`outputs/Final_Poster_AgroAI.pdf`.

> ⚠️ Some of these were written against the **old** numbers. Check any figure or table they
> generate against `PADR_FINDINGS.md` before it goes in your submission.

---

## Part 11 — Your learning path

You don't need to understand everything at once. Do it in this order.

**Day 1 — Get oriented, touch nothing**
1. Read Parts 1, 2 and 4 of this file again.
2. Open `data/collected/FYP data(manual) - real all datas.csv` in Excel or Numbers. Look at
   actual rows. Find the `"3,091"` with the comma. Find a month where extent is 30 and
   production is 13,271 (the 442 MT/ha record).
3. Run `DATA_VARIANT=real PYTHONPATH=src python src/dcs_panel.py` and read every line it
   prints. You'll see all 28 rows of your entire real dataset. Sit with how small that is.

**Day 2 — Understand LOYO**
1. Re-read Part 3.4 until leave-one-year-out is obvious.
2. Run `DATA_VARIANT=real PYTHONPATH=src python src/baselines.py`.
3. Open `src/baselines.py` and find the loop at line 106: `for held in sorted(set(years))`.
   That loop *is* LOYO. Everything else is bookkeeping.
4. Open `outputs/results_real/baseline_oof.json`. Every row is one district-year with each
   model's held-out prediction next to the truth.

**Day 3 — Understand why R² is negative**
1. Run `src/variance_decomposition.py`.
2. Get to where you can explain, without notes: *"64% of the variance is between years, LOYO
   removes that by construction, measurement error takes half of what's left, ceiling is
   0.162."* This is your single most valuable sentence.

**Day 4 — Understand PADR**
1. Read Part 6 of this file.
2. Open `src/padr.py`. Read only lines 107–137 — the three stress functions `f_thermal`,
   `f_water`, `f_waterlog`. Each is about five lines of arithmetic. That's the model's core.
3. Run `src/run_padr.py` and watch the learned constants print.

**Day 5 — The ablation and the power analysis**
1. Run `src/ablation_padr.py` and `src/identifiability.py`.
2. Understand Part 6.7 — the `Ky` withdrawal. If you can explain *why* a tight confidence
   interval was not evidence, you will handle any methods question in your viva.

**Day 6 — The backend and dashboard**
1. Start the API, curl it, see JSON come back.
2. `cd dashboard && npm install && npm run dev`. Click around.

**Day 7 — Write**
Use `PADR_FINDINGS.md` as your results chapter skeleton and
`05_NOVELTY_AND_RESEARCH.md` as your contribution chapter skeleton.

---

## Part 12 — Viva questions and how to answer them

**"Why is your R² negative?"**
> "Because leave-one-year-out removes 64% of the variance by construction, and measurement
> error accounts for over half of what remains within a year. The attainable ceiling is
> 0.162, and every model including the naive mean sits below zero. The contribution is not
> the score — it's establishing why no score was available, and which mechanisms are
> responsible."

**"So your project failed?"**
> "The prediction target failed; the research succeeded. I established that the original
> R² > 0.75 target was mathematically unattainable on this panel, quantified the ceiling at
> 0.162, showed via a power analysis that my model would have detected a weather signal
> driving as little as 6% of variance, and found none. That bounds the true agro-climatic
> signal below 6%. That is a result, and it redirects the next data collection toward
> fertiliser, irrigation and price — which is where the signal actually is."

**"What is novel? Isn't this all standard methods?"**
> "The standard methods were the starting point and I report them honestly as prior art. The
> method claim is PADR: I make the agronomic constants of an FAO-33-style crop model
> *estimable* rather than assumed, and fit them under agronomic bounds with shrinkage toward
> literature values. Existing hybrids like Shahhosseini et al. 2021 freeze the crop model and
> fit ML on its residual — I estimate the physics itself. Learning the constants improves R²
> by 0.57 over freezing them at literature values."

**"Your hybrid CNN-LSTM was supposed to be the novelty. What happened?"**
> "It was falsified, and I report that. The season indicator is constant because the real
> panel is Yala-only, so the season-injection is inert by construction. And the weather
> sequences the LSTM consumed were fabricated from seasonal aggregates by a fixed sine curve
> — a deterministic function of the tabular inputs, carrying no new information. It scored
> R² = −7.05 with 44,929 parameters on 24 training rows. That's a finding about deep learning
> under data scarcity, and it's why PADR uses 17 parameters."

**"Two of your four novelty claims didn't work. Isn't that a problem?"**
> "It's the opposite. An ablation where every proposed component happens to help is not a
> credible ablation. N1 and N4 are strongly supported at +0.566 and +1.166. N2 is negligible
> because thermal and calendar time nearly coincide when tropical temperature barely varies —
> the method isn't wrong, the panel offers it nothing to correct. N3 is inert because
> waterlogging binds in 3.5% of bins in a single year."

**"How do I know your model would have found a signal if there was one?"**
> "I ran a power analysis. I simulated yields where a known share of variance is genuinely
> driven by the stress index, with noise matched to the observed within-year scale, and
> refitted under identical LOYO. The model detects a signal at 6% of variance. It found none
> in the real panel."

**"Why should I believe your learned constants?"**
> "For five of the seven, because I ran a parameter recovery experiment — fit to data
> generated from known constants and checked the error as a share of each parameter's
> admissible range. T_opt, W_max, T_base, gamma and P_crit all recover to within 10%. Ky and
> T_crit do not — Ky returns 1.108 when the truth is 0.966, reproducing the prior rather than
> the data. I withdraw any claim about those two. The tight fold spread on Ky was the prior's
> stability, not evidence."

**"Can a farmer use this?"**
> "Not for a decision, and the uncertainty quantification is how I show that rather than hide
> it. Year-blocked conformal intervals are properly calibrated at 0.911 against a nominal
> 0.90, but they are ±15.3 MT/ha on a mean of 17.9 — roughly ±85%. The honest interval is the
> evidence that these predictions aren't decision-useful."

**"What would you do with more time / data?"**
> "Collect fertiliser application, irrigation-release records, input costs and farmgate
> prices. The variance decomposition says 64% of the variance is a year effect that weather
> cannot explain, and the 2022 collapse across all four districts lines up with the fertiliser
> import ban. Those are the variables that carry the signal. Field-level rather than
> district-level data would also cut the measurement error, which currently consumes over half
> of what LOYO leaves behind."

---

## Part 13 — Fixing things when they break

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | venv not activated | `source .venv/bin/activate` |
| `ModuleNotFoundError: No module named 'config'` | running a `src/` script without `PYTHONPATH=src` | prefix with `PYTHONPATH=src` |
| Results land in `outputs/results/` instead of `results_real/` | forgot `DATA_VARIANT=real` | prefix with `DATA_VARIANT=real` |
| `Address already in use` on port 5000 | macOS AirPlay Receiver | `PORT=5050 python src/api.py` |
| `cd frontend` → no such directory | README is out of date | `cd dashboard` |
| API returns `503 Model not loaded` | no trained model on disk | run `python main.py` first |
| Walls of TensorFlow warnings | normal (oneDNN/XLA notices) | ignore |
| TensorFlow won't install | Python 3.13/3.14 | `python3.12 -m venv .venv` |
| Pipeline crashes mid-run | — | models save after each stage; resume with `--skip-ml` etc. |

**Never edit** anything inside `outputs/` or `.venv/` — both are regenerated.
**Do edit** `src/config.py` — that's where all the knobs live.

---

## Part 14 — The 60-second summary

- You predict big onion yield in 4 Sri Lankan districts. Real dataset: **28 rows.**
- The original target was ~40% fabricated. It was rebuilt from 87 real DCS records as
  Σ(tonnes)/Σ(hectares). Everything correct lives in **Pipeline C**.
- Everything is scored under **leave-one-year-out** — train on 6 years, predict the 7th,
  repeat.
- **64% of yield variance is between years, and LOYO removes that on purpose.** Measurement
  error eats half of what's left. Attainable R² ceiling: **0.162**. The proposal's target of
  0.75 was never reachable.
- You built 12 models. **All of them lose to predicting the training average.**
- **PADR** is the real contribution: a 17-parameter mechanistic crop model whose agronomic
  constants are learned rather than assumed. It doesn't win on score — it *diagnoses* why no
  model can, by reporting which biological mechanisms are inactive and by how much.
- A **power analysis** proves PADR would have detected a weather signal at 6% of variance.
  It found none. So the agro-climatic signal is below 6%.
- **The conclusion:** big onion yield in Sri Lanka's dry zone is not limited by weather at
  district-season resolution. It's limited by inputs and policy — which nobody measured.
- Backend: `PORT=5050 python src/api.py`. Dashboard: `cd dashboard && npm run dev`.

---

*Authoritative companion document: [PADR_FINDINGS.md](PADR_FINDINGS.md).
Contribution framing: [05_NOVELTY_AND_RESEARCH.md](05_NOVELTY_AND_RESEARCH.md).*

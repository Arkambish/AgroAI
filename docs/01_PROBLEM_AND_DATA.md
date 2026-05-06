# 01 — The Problem and the Data

## The agricultural problem

Sri Lanka eats roughly **200,000 tons of big onion per year**, but local farmers only produce a fraction of that. The rest comes from imports (mostly from India), and those imports cost foreign exchange. The government wants to be self-sufficient. To plan that, they need to know *in advance* how much the local crop will yield — too high and they over-import (hurts farmers); too low and they under-import (prices spike).

Right now, big onion yield is estimated by **agricultural officers walking through fields and guessing**. That's slow, subjective, and only happens after harvest. There's no systematic survey methodology like there is for paddy (rice). This research replaces the guess with a model that uses satellite images and weather data to forecast yield months in advance.

## Why this is hard

1. **Tiny dataset.** Big onion is a "non-cash crop" (not strategic enough to get heavy government tracking). The Department of Census and Statistics has data going back ~20 years for ~4 districts × 2 seasons each — that's about 160 records total. In ML terms, **160 rows is almost nothing**. You normally train a deep learning model on millions of examples.
2. **Two completely different growing seasons.** Sri Lanka has two monsoons:
   - **Yala** (April–August): main growing season, drier, sunnier, in the dry zone. Yields are high (12–24 MT/Ha in Matale).
   - **Maha** (October–March): off-season, wetter, cooler. Yields drop a lot (6–15 MT/Ha).
   - A model that lumps them together averages out the patterns. We need it to know which season we're in.
3. **Yield depends on dozens of factors.** Rainfall, temperature, sunlight, soil pH, vegetation health (measured from satellites), pest pressure, last year's yield, and more. None alone explains everything.

## The four districts

| District | Why it's important |
|---|---|
| **Matale** | The Dambulla region produces ~50% of national big onion supply. The big one. |
| **Anuradhapura** | Major dry-zone producer, similar climate to Matale. |
| **Polonnaruwa** | Adjacent dry zone, slightly wetter. |
| **Jaffna** | Northern peninsula, very different climate (drier, sandier soil, higher pH). Tests if the model generalises across Sri Lanka. |

## The data sources

The project uses **seven different data sources** that feed into one unified table. Here's what each one contributes:

### 1. DCS Yield Data (the target — what we're trying to predict)

- **Source**: Department of Census and Statistics Sri Lanka, "Big Onion Survey Reports" 2004–2023.
- **What it gives us**: For each (district, year, season), the **average yield in metric tons per hectare** (MT/Ha). This is the *ground truth*.
- **File**: `data/raw/dcs_yield.csv` (when collected)

### 2. NASA POWER Weather Data

- **Source**: NASA's POWER project — a free API serving daily weather for any latitude/longitude.
- **What it gives us**: Daily rainfall, temperature (min/max), solar radiation, humidity. We aggregate these to seasonal averages and totals.
- **Engineered features**: `season_avg_temp`, `season_total_rainfall`, `season_avg_humidity`, `growing_degree_days` (a heat-accumulation metric crops respond to), `heat_stress_days` (days above a threshold), `drought_index_spi` (Standardized Precipitation Index — how dry was this season vs. normal).

### 3. MODIS Satellite — Vegetation Indices

- **Source**: NASA MODIS satellite (MOD13Q1 product), accessed via Google Earth Engine.
- **What it gives us**: NDVI (Normalized Difference Vegetation Index) and EVI (Enhanced Vegetation Index) at 250m resolution every 16 days.
- **What NDVI is**: A number between -1 and +1 that tells you **how green a patch of land is**. Healthy growing crops reflect a lot of near-infrared light and absorb red light, so NDVI ≈ 0.6–0.9. Bare soil is ≈ 0.1. Water is negative. **High NDVI during the growing season → likely high yield.**
- **Engineered features**: `season_mean_ndvi`, `season_max_ndvi`, `time_to_peak_ndvi` (how many days into the season vegetation peaked — earlier peak often means stress), `ndvi_growth_rate`.

### 4. Sentinel-2 Satellite — Higher-resolution indices

- **Source**: ESA Sentinel-2 satellite, 10m resolution, accessed via Google Earth Engine.
- **What it gives us**: NDVI, NDWI (Normalized Difference Water Index — how wet/dry vegetation is) at much finer detail than MODIS.
- **Why both**: MODIS is daily-ish but coarse (250m). Sentinel-2 is sharper (10m) but less frequent. Together they're complementary.

### 5. CHIRPS Rainfall

- **Source**: Climate Hazards Group InfraRed Precipitation with Stations — gridded rainfall at 5km resolution.
- **What it gives us**: A second, independent rainfall measurement. (NASA POWER is point-based interpolation; CHIRPS is gridded with station correction.)
- **Why two rainfall sources?** Rainfall is the single most important variable for non-irrigated onion. Cross-validating two sources catches errors.

### 6. MODIS LST (Land Surface Temperature)

- **Source**: MODIS satellite again, but a different product — actual measured ground temperature.
- **What it gives us**: `season_mean_lst_day`, `season_mean_lst_night`. Different from air temperature (NASA POWER) — surface temperature can be 5–10°C hotter than air on sunny days, which matters for crop stress.

### 7. SoilGrids — Soil Properties

- **Source**: ISRIC SoilGrids — global soil property maps at 250m.
- **What it gives us**: Static features per district: `soil_ph`, `organic_carbon`, `clay_pct`, `sand_pct`. Onions prefer pH 6.0–7.0; outside that range, yield drops.

### Combining everything

All seven sources are merged on `(District, Year, Season)`. The result is one big table:

```
District   Year  Season  Yield  rainfall  temp  ndvi  evi  ...  soil_ph  ...
Matale     2004  Yala    16.2   840       28.1  0.68  0.58 ...  6.2      ...
Matale     2004  Maha    8.1    1100      26.0  0.55  0.47 ...  6.2      ...
...
Jaffna     2023  Yala    11.8   590       28.5  0.51  0.43 ...  7.1      ...
```

That's about 160 rows × 32 columns. Each row is one (district, year, season) observation. The model's job: given the 31 input columns, predict the `Yield` column.

## Why we're using synthetic data right now

The real CSVs from DCS, NASA POWER, Google Earth Engine, etc. require:
- Filing requests with DCS for survey data
- Setting up NASA POWER API credentials
- Setting up Google Earth Engine and writing extraction scripts (Sharuja's job per the proposal)
- Cleaning, geo-aligning, time-aligning everything

That takes weeks. Meanwhile, you (Arkam) need to build, debug, and validate the *modelling pipeline*. The solution: **generate fake data that has the same statistical shape as the real data**, train the entire pipeline on it, and verify everything works. When the real CSVs arrive, you drop them into `data/raw/` and re-run.

The synthetic data generator in `src/data_loader.py` is calibrated to published DCS ranges:
- Matale Yala yield: mean 16, std 4 (matches reported 12–24 MT/Ha)
- Jaffna Yala yield: mean 12, std 4 (lower, drier district)
- All seasons get a shared "climate shock" that year (so wet/dry years affect all districts together — a real-world correlation)
- NDVI is correlated with yield (`ndvi_base = 0.3 + yield/30`), so a good model will learn that relationship

The generator is **deterministic** (`np.random.default_rng(42)`) — it produces the same dataset every time, so results are reproducible.

## Yala vs Maha — why the model needs to know

Compare Matale Yala (mean ~16 MT/Ha) to Matale Maha (mean ~8 MT/Ha). That's a **2× yield difference** for the same district. If you don't tell the model the season, it has to guess from rainfall and NDVI alone — possible but harder. By including a `season_indicator` column (Yala=1, Maha=0) and feeding it explicitly into the hybrid model's final layer, we let the model learn season-specific patterns. This is part of the novelty.

## What you'll see in the data after running

After `python main.py`, look at:

- `data/synthetic/synthetic_dataset.csv` — the raw generated data (152 rows after dropping incomplete first-year records)
- `data/processed/integrated_dataset.csv` — same data, cleaned and validated
- `data/processed/features_tabular.csv` — the matrix the ML models actually see (one row per observation, all numeric features)
- `data/processed/features_sequential.pkl` — a Python "pickle" file containing the time-series tensors the DL models need (more on this in [02_ML_DL_FUNDAMENTALS.md](02_ML_DL_FUNDAMENTALS.md))
- `outputs/plots/eda/yield_distribution.png` — histograms showing how yield is distributed across districts and seasons. Open it in any image viewer.

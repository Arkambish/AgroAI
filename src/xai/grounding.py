"""Feature grounding registry — how "real" each of the 32 features actually is.

FLAGGED FOR REMOVAL: this was previously one of three inputs to the old
per-feature ERI formula (see eri.py's module docstring for the report-driven
rewrite that dropped it). No live endpoint reads feature_grounding.json and
nothing else in the codebase imports GROUNDING_REGISTRY, so this module and
`run_xai.py`'s (now-removed) call to `get_grounding_scores()` are dead code
kept only for reference — delete both this file and any lingering
feature_grounding.json output once that's confirmed safe.

Grounding answers a different question than SHAP or stability: not "does the
model lean on this feature" but "if it leans on it, is that signal coming from
a genuine measurement, or from filler the pipeline invented because the real
value wasn't collected?" A SHAP explanation that hangs on a constant proxy
(e.g. `season_avg_solar_rad`, hardcoded to 18.0 for every real-data row) should
be trusted less than one that hangs on directly measured rainfall, even if
SHAP itself has no way to tell the two apart.

Tiers (see task spec / data_loader.py for the source of truth on each feature):
    1.00  directly measured in the source CSV (a per-row aggregate — mean/
          sum/max/min/range — of genuinely measured monthly values, no proxy
          substitution or cross-row imputation involved)
    0.70  district+season derived (a group-level statistic — mean, std, or a
          lag — computed from real per-row data grouped by district+season;
          reliable but one step removed from a raw single-row measurement)
    0.50  district mean or season mean only
    0.30  global mean
    0.15  algebraically derived from another feature — either a fixed-offset
          physical proxy standing in for a variable that was never actually
          measured (`season_mean_lst_day/night` ≈ air temperature ± 6°C,
          since satellite LST isn't in the collected dataset), or an
          engineered interaction term (`ndvi_x_lst`, `rainfall_x_ndvi`,
          `temp_x_humidity`) that is a pure product of other features
    0.05  constant proxy / zero variance in the dataset
    0.00  zero fallback

This module inspects `data_loader.load_collected_data()` (the real-data path;
`DATA_VARIANT=real`) to assign each feature's tier, since that function is the
one that actually decides, per feature, whether a value is a real measurement,
a group-derived statistic, a fixed-offset proxy, or a hardcoded constant:

  - season_avg_temp, season_total_rainfall, season_avg_humidity, temp_range,
    max_daily_rainfall, growing_degree_days, heat_stress_days: row-level
    aggregates (mean/sum/max/min/range/threshold-count/degree-day formula) of
    genuinely measured monthly temperature_c / rainfall / humidity_pct → 1.00
  - season_mean_ndvi, season_max_ndvi, season_min_ndvi, ndvi_std,
    time_to_peak_ndvi, ndvi_growth_rate, season_mean_evi: same, from measured
    ndvi_i / evi_i → 1.00
  - soil_ph, clay_pct, sand_pct: measured SoilGrids columns (ph_0_5cm,
    clay_0_5cm, sand_0_5cm), unit-rescaled only → 1.00
  - season_indicator: derived from the Season label itself, always known
    exactly (not filler) → 1.00
  - drought_index_spi, ndvi_anomaly: z-score / anomaly of a measured column
    against its own district+season group mean (and std, for SPI) → 0.70
  - prev_season_yield, prev_year_yield, yield_3yr_avg: shift/rolling-mean of
    the real measured target within each district+season group (mostly real
    historical yield; edge rows at the start of a group's series fall back to
    a global median in the final ALL_FEATURES fill loop) → 0.70
  - season_mean_lst_day, season_mean_lst_night: fixed offset from measured
    temperature (avg_temp ± 6°C) standing in for unmeasured satellite LST →
    0.15
  - rainfall_x_ndvi, temp_x_humidity, ndvi_x_lst: engineered interaction
    terms, pure products of other features → 0.15
  - season_avg_solar_rad (18.0), season_mean_ndwi (0.1), organic_carbon
    (fillna(1.8)), extent_prev_season (fillna(400.0)): hardcoded constants —
    zero variance across every real-data row → 0.05

No feature in the collected-data pipeline is filled from a district-only mean,
a season-only mean, a global mean, or a bare zero-fallback, so tiers 0.50,
0.30 and 0.00 are unused today; they are kept in the registry's vocabulary
(and in `TIER_LABELS` below) since `_resolve_features` in api.py *does* fall
back through exactly that district/season/global/zero cascade for
user-supplied prediction requests, so a future data source that actually hits
those tiers should slot in without inventing new constants.
"""

import json
import os
import sys

_XAI_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_XAI_DIR)
for _p in (_SRC_DIR, _XAI_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import ALL_FEATURES, RESULTS_DIR  # noqa: E402  (path bootstrap above)

TIER_LABELS = {
    1.00: 'measured',
    0.70: 'district_season_derived',
    0.50: 'district_or_season_mean',
    0.30: 'global_mean',
    0.15: 'algebraic_proxy',
    0.05: 'constant_proxy',
    0.00: 'zero_fallback',
}

# Static per-feature grounding weight — see module docstring for the
# data_loader.py-derived justification of every entry.
GROUNDING_REGISTRY: dict[str, float] = {
    # --- weather (9) ---
    'season_avg_temp': 1.00,
    'season_total_rainfall': 1.00,
    'season_avg_humidity': 1.00,
    'season_avg_solar_rad': 0.05,      # constant 18.0 (data_loader.load_collected_data)
    'growing_degree_days': 1.00,
    'heat_stress_days': 1.00,
    'drought_index_spi': 0.70,         # district+season z-score of rainfall
    'temp_range': 1.00,
    'max_daily_rainfall': 1.00,

    # --- satellite (11) ---
    'season_mean_ndvi': 1.00,
    'season_max_ndvi': 1.00,
    'season_min_ndvi': 1.00,
    'ndvi_std': 1.00,
    'ndvi_anomaly': 0.70,              # district+season anomaly of NDVI
    'time_to_peak_ndvi': 1.00,
    'ndvi_growth_rate': 1.00,
    'season_mean_evi': 1.00,
    'season_mean_ndwi': 0.05,          # constant 0.1
    'season_mean_lst_day': 0.15,       # proxy: avg_temp + 6.0
    'season_mean_lst_night': 0.15,     # proxy: avg_temp - 6.0

    # --- historical (5) ---
    'prev_season_yield': 0.70,         # district+season shift(1) of real yield
    'prev_year_yield': 0.70,
    'yield_3yr_avg': 0.70,             # district+season rolling(3) of real yield
    'season_indicator': 1.00,          # derived from the Season label itself
    'extent_prev_season': 0.05,        # constant 400.0 — not in collected data

    # --- soil (4) ---
    'soil_ph': 1.00,
    'organic_carbon': 0.05,            # constant 1.8 — not in collected data
    'clay_pct': 1.00,
    'sand_pct': 1.00,

    # --- interaction (3) ---
    'rainfall_x_ndvi': 0.15,
    'temp_x_humidity': 0.15,
    'ndvi_x_lst': 0.15,
}

# Features with zero (or effectively zero) variance across the real collected
# dataset — hardcoded constants substituted for data that was never measured.
ZERO_VARIANCE_FEATURES = (
    'season_avg_solar_rad', 'season_mean_ndwi', 'organic_carbon', 'extent_prev_season',
)

_missing = set(ALL_FEATURES) - set(GROUNDING_REGISTRY)
if _missing:
    raise RuntimeError(f'GROUNDING_REGISTRY is missing tiers for: {sorted(_missing)}')


def get_grounding_scores() -> dict:
    """Return {feature: grounding_weight} for every feature in config.ALL_FEATURES
    and persist it to outputs/results_{variant}/feature_grounding.json."""
    scores = {feature: GROUNDING_REGISTRY[feature] for feature in ALL_FEATURES}

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, 'feature_grounding.json')
    with open(out_path, 'w') as fh:
        json.dump(scores, fh, indent=2)
    print(f'  Saved -> {out_path}')
    return scores


if __name__ == '__main__':
    result = get_grounding_scores()
    print(json.dumps(result, indent=2))

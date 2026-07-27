"""Modelling frame built entirely from real observations.

Replaces the seasonal-aggregate path in `data_loader.load_collected_data()`, which
derived features from a month table that was 40% fabricated and hard-coded six of them
to constants (`season_avg_solar_rad=18.0`, `heat_stress_days=0`, `season_mean_ndwi=0.1`,
`organic_carbon=1.8`, `extent_prev_season=400.0`, `season_indicator=1`).

Sources, all real:
  * target + observation weights  -> src/dcs_panel.py (87 DCS extent/production records)
  * daily weather 2000-2025       -> src/data_collection/nasa_power.py (37,988 rows)
  * 16-day NDVI/EVI 2000-2025     -> FYP data(manual) - NDVI-EVI.csv (595 composites/district)

Two design decisions worth defending at viva
--------------------------------------------
1. ANOMALIES USE A PRE-SAMPLE CLIMATOLOGY. `drought_index_spi` and `ndvi_anomaly` are
   standardised against CLIMATOLOGY_YEARS (2000-2018), which no fold ever tests on. The
   original code z-scored against the full 2019-2025 panel, so every fold saw statistics
   computed from its own held-out year. Using pre-sample years removes that leak by
   construction rather than by fold bookkeeping — only possible now that 26 years of
   daily weather and NDVI are actually loaded.

2. YIELD LAGS ARE DROPPED. `prev_season_yield`, `prev_year_yield` and `yield_3yr_avg`
   leak under leave-one-year-out: with year k held out, the training row for year k+1
   carries year k's observed yield as a feature. They also buy almost nothing here —
   only 2% of target variance is between-district, which is all a persistence term can
   capture. (`prev_season_yield` and `prev_year_yield` were identical columns anyway,
   the data being Yala-only.)
"""

import numpy as np
import pandas as pd

from config import (
    CLIMATOLOGY_YEARS, GROWING_SEASON_MONTHS, NDVI_FILE, NDVI_PROXY_DISTRICTS,
    TARGET_COLUMN,
)
from data_collection.nasa_power import fetch_all
from dcs_panel import build_seasonal_panel

# Onion base temperature for growing-degree-days (McMaster & Wilhelm 1997).
GDD_BASE = 10.0
# A day above this counts as heat stress. Real daily maxima make this measurable;
# the old code compared MONTHLY MEAN temperature to 32C, so it was always exactly 0.
HEAT_STRESS_C = 32.0
# Below this a day counts as dry, for spell-length features.
DRY_DAY_MM = 1.0


def _load_ndvi():
    """Real MODIS composites for the modelled districts, with proxy substitution."""
    ndvi = pd.read_csv(NDVI_FILE)
    ndvi['Date'] = pd.to_datetime(ndvi['Date'])
    ndvi['District'] = ndvi['District'].astype(str).str.strip().str.title()
    ndvi = ndvi.dropna(subset=['NDVI', 'EVI'])

    # Districts with no MODIS export of their own borrow their nearest neighbour's.
    # Kurunegala also shares a NASA POWER grid cell with Matale, so this makes its
    # inputs identical to Matale's — flagged per row so the report can state it.
    ndvi['ndvi_is_proxy'] = False
    for district, source in NDVI_PROXY_DISTRICTS.items():
        if district in set(ndvi['District']):
            continue
        borrowed = ndvi[ndvi['District'] == source].copy()
        borrowed['District'] = district
        borrowed['ndvi_is_proxy'] = True
        ndvi = pd.concat([ndvi, borrowed], ignore_index=True)

    ndvi['Year'] = ndvi['Date'].dt.year
    ndvi['Month'] = ndvi['Date'].dt.month
    return ndvi


def _weather_season_features(daily):
    """Per district-year growing-season weather, computed from DAILY records.

    Everything here was previously either a constant or a monthly-mean stand-in.
    Daily resolution is what makes GDD, heat-stress counts, diurnal range, true daily
    rainfall maxima and spell lengths meaningful at all.
    """
    season = daily[daily['date'].dt.month.isin(GROWING_SEASON_MONTHS)].copy()
    season['year'] = season['date'].dt.year

    rows = []
    for (year, district), g in season.groupby(['year', 'district']):
        g = g.sort_values('date')
        tmean, tmax, tmin = g['T2M'], g['T2M_MAX'], g['T2M_MIN']
        rain = g['PRECTOTCORR']

        dry = (rain < DRY_DAY_MM).to_numpy()
        rows.append({
            'Year': int(year), 'District': district,
            'season_avg_temp': round(float(tmean.mean()), 3),
            'season_total_rainfall': round(float(rain.sum()), 2),
            'season_avg_humidity': round(float(g['RH2M'].mean()), 3),
            'season_avg_solar_rad': round(float(g['ALLSKY_SFC_SW_DWN'].mean()), 3),
            'growing_degree_days': round(float(np.clip(tmean - GDD_BASE, 0, None).sum()), 1),
            'heat_stress_days': int((tmax > HEAT_STRESS_C).sum()),
            'temp_range': round(float((tmax - tmin).mean()), 3),
            'max_daily_rainfall': round(float(rain.max()), 2),
            'rain_days': int((rain >= DRY_DAY_MM).sum()),
            'max_dry_spell': int(_longest_run(dry)),
            'max_7day_rainfall': round(float(rain.rolling(7, min_periods=1).sum().max()), 2),
        })
    return pd.DataFrame(rows)


def _longest_run(flags):
    """Length of the longest consecutive True run — used for dry-spell duration."""
    best = run = 0
    for flag in flags:
        run = run + 1 if flag else 0
        best = max(best, run)
    return best


def _ndvi_season_features(ndvi):
    """Per district-year growing-season vegetation-index summaries."""
    season = ndvi[ndvi['Month'].isin(GROWING_SEASON_MONTHS)]

    rows = []
    for (year, district), g in season.groupby(['Year', 'District']):
        g = g.sort_values('Date')
        values = g['NDVI'].to_numpy(dtype=float)
        doy = g['Date'].dt.dayofyear.to_numpy(dtype=float)
        peak = int(np.argmax(values))

        rows.append({
            'Year': int(year), 'District': district,
            'season_mean_ndvi': round(float(values.mean()), 4),
            'season_max_ndvi': round(float(values.max()), 4),
            'season_min_ndvi': round(float(values.min()), 4),
            'ndvi_std': round(float(values.std(ddof=0)), 4),
            'time_to_peak_ndvi': round(float(doy[peak] - doy[0]), 1),
            'ndvi_growth_rate': round(float(np.polyfit(doy, values, 1)[0]), 6)
                                if len(values) > 1 else 0.0,
            'season_mean_evi': round(float(g['EVI'].mean()), 4),
            'n_ndvi_composites': int(len(g)),
            'ndvi_is_proxy': bool(g['ndvi_is_proxy'].iloc[0]),
        })
    return pd.DataFrame(rows)


def _climatology_anomalies(frame, weather_season, ndvi_season):
    """Standardise rainfall and NDVI against the PRE-SAMPLE climatology.

    CLIMATOLOGY_YEARS never appears in any LOYO fold's test set, so these are leak-free
    without any fold bookkeeping. Returns SPI-style z-scores per district.
    """
    lo, hi = CLIMATOLOGY_YEARS
    out = frame.copy()

    for source, value_col, out_col in [
        (weather_season, 'season_total_rainfall', 'drought_index_spi'),
        (ndvi_season, 'season_mean_ndvi', 'ndvi_anomaly'),
    ]:
        base = source[source['Year'].between(lo, hi)]
        stats = base.groupby('District')[value_col].agg(['mean', 'std'])
        merged = out.merge(stats, left_on='District', right_index=True, how='left')
        out[out_col] = ((merged[value_col].to_numpy() - merged['mean'].to_numpy())
                        / merged['std'].replace(0, np.nan).to_numpy()).round(4)
    return out


def build_modelling_frame(verbose=True):
    """One row per (Year, Season, District) with the corrected target and real features."""
    panel = build_seasonal_panel(verbose=verbose)
    daily = fetch_all()
    daily['date'] = pd.to_datetime(daily['date'])
    ndvi = _load_ndvi()

    weather_season = _weather_season_features(daily)
    ndvi_season = _ndvi_season_features(ndvi)

    keep = ['Year', 'Season', 'District', TARGET_COLUMN,
            'extent_ha', 'production_mt', 'n_months', 'obs_weight']
    frame = (panel[keep]
             .merge(weather_season, on=['Year', 'District'], how='left')
             .merge(ndvi_season, on=['Year', 'District'], how='left'))

    frame = _climatology_anomalies(frame, weather_season, ndvi_season)

    # Interactions kept from the original schema — cheap, and SHAP ranked
    # temp_x_humidity top-1 on the old target, so it stays comparable.
    frame['rainfall_x_ndvi'] = (frame['season_total_rainfall'] * frame['season_mean_ndvi']).round(3)
    frame['temp_x_humidity'] = (frame['season_avg_temp'] * frame['season_avg_humidity']).round(3)

    frame = frame.sort_values(['District', 'Year']).reset_index(drop=True)

    if verbose:
        _describe(frame)
    return frame


def _describe(frame):
    missing = frame.isna().sum()
    missing = missing[missing > 0]
    print(f'\n→ Modelling frame: {len(frame)} rows x {frame.shape[1]} columns')
    print(f'  districts={sorted(frame.District.unique())} '
          f'years={int(frame.Year.min())}-{int(frame.Year.max())}')
    if len(missing):
        print(f'  ⚠ columns with missing values: {missing.to_dict()}')
    else:
        print('  ✓ no missing values')
    if frame['ndvi_is_proxy'].any():
        proxied = sorted(frame.loc[frame['ndvi_is_proxy'], 'District'].unique())
        print(f'  ⚠ NDVI is a neighbour proxy for: {", ".join(proxied)}')

    constant = [c for c in frame.columns
                if frame[c].dtype.kind in 'fi' and frame[c].nunique(dropna=False) <= 1]
    print(f'  constant columns: {constant if constant else "none"}')


if __name__ == '__main__':
    df = build_modelling_frame()
    pd.set_option('display.width', 250)
    print()
    print(df.head(8).to_string(index=False))

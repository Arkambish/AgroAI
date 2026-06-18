"""Data loading layer.

Tries to load real CSVs from data/raw/. If any required file is missing,
generates a calibrated synthetic dataset so the rest of the pipeline can run
end-to-end. Distributions match published DCS Big Onion Survey ranges:
- Matale Yala: 12-24 MT/Ha; Maha off-season: 6-15 MT/Ha
- National avg: 9.9-19.7 MT/Ha
"""

import os
import numpy as np
import pandas as pd

from config import (
    DISTRICTS, SEASONS, RANDOM_STATE, TARGET_COLUMN,
    DATA_VARIANT, COLLECTED_FILE, ALL_FEATURES,
)

REQUIRED_FILES = {
    'dcs_yield': 'data/raw/dcs_yield.csv',
    'nasa_power': 'data/raw/nasa_power_weather.csv',
    'modis_ndvi': 'data/raw/modis_ndvi_evi.csv',
    'sentinel2': 'data/raw/sentinel2_indices.csv',
    'chirps': 'data/raw/chirps_rainfall.csv',
    'modis_lst': 'data/raw/modis_lst.csv',
    'soil': 'data/raw/soil_data.csv',
}


def check_data_availability():
    available = {}
    for key, path in REQUIRED_FILES.items():
        available[key] = os.path.exists(path)
        status = '✓ Found' if available[key] else '✗ Missing'
        print(f'  {status}: {path}')
    return available


def generate_synthetic_data():
    rng = np.random.default_rng(RANDOM_STATE)
    rows = []

    district_params = {
        'Matale':       {'yala_yield': (16, 4), 'maha_yield': (8, 3), 'rainfall': (850, 150)},
        'Anuradhapura': {'yala_yield': (15, 4), 'maha_yield': (7, 3), 'rainfall': (900, 180)},
        'Polonnaruwa':  {'yala_yield': (14, 3), 'maha_yield': (6, 2), 'rainfall': (1100, 200)},
        'Jaffna':       {'yala_yield': (12, 4), 'maha_yield': (5, 2), 'rainfall': (600, 120)},
    }
    soil_ph_base = {'Matale': 6.2, 'Anuradhapura': 6.5, 'Polonnaruwa': 6.8, 'Jaffna': 7.1}

    # Iterate the generator's OWN districts (not config.DISTRICTS, which is a
    # superset that also includes real-only districts like Kurunegala).
    synth_districts = list(district_params.keys())
    for year in range(2004, 2024):
        for district in synth_districts:
            params = district_params[district]
            climate_shock = rng.normal(0, 0.5)
            for season in SEASONS:
                is_yala = 1 if season == 'Yala' else 0
                mu, sigma = params['yala_yield'] if season == 'Yala' else params['maha_yield']
                yield_val = max(2.0, rng.normal(mu, sigma) + climate_shock)

                base_rain = params['rainfall'][0] if season == 'Yala' else params['rainfall'][0] * 1.3
                rainfall = max(100.0, rng.normal(base_rain, params['rainfall'][1]))

                ndvi_base = 0.3 + (yield_val / 30)
                ndvi = float(np.clip(ndvi_base + rng.normal(0, 0.08), 0.1, 0.85))
                evi_base = ndvi * 0.85
                ndwi = float(np.clip(-0.1 + (rainfall / 2000), -0.2, 0.4))

                rows.append({
                    'Year': year, 'Season': season, 'District': district,
                    TARGET_COLUMN: round(yield_val, 2),
                    'season_indicator': is_yala,
                    # Weather
                    'season_total_rainfall': round(rainfall, 1),
                    'season_avg_temp': round(rng.normal(28 if season == 'Yala' else 26, 1.5), 1),
                    'season_avg_humidity': round(rng.normal(72, 8), 1),
                    'season_avg_solar_rad': round(rng.normal(18, 2), 2),
                    'growing_degree_days': round(max(200, rng.normal(650 if season == 'Yala' else 580, 50)), 1),
                    'heat_stress_days': max(0, int(rng.normal(8 if season == 'Yala' else 3, 3))),
                    'drought_index_spi': round(rng.normal(0, 1), 3),
                    'temp_range': round(rng.normal(10, 2), 1),
                    'max_daily_rainfall': round(rng.normal(65, 20), 1),
                    # Satellite
                    'season_mean_ndvi': round(ndvi, 4),
                    'season_max_ndvi': round(min(0.9, ndvi + 0.1), 4),
                    'season_min_ndvi': round(max(0.05, ndvi - 0.15), 4),
                    'ndvi_std': round(rng.uniform(0.02, 0.08), 4),
                    'ndvi_anomaly': round(rng.normal(0, 0.06), 4),
                    'time_to_peak_ndvi': round(rng.normal(65, 12), 1),
                    'ndvi_growth_rate': round(rng.uniform(0.003, 0.01), 5),
                    'season_mean_evi': round(evi_base + rng.normal(0, 0.05), 4),
                    'season_mean_ndwi': round(ndwi, 4),
                    'season_mean_lst_day': round(rng.normal(34 if season == 'Yala' else 30, 2), 1),
                    'season_mean_lst_night': round(rng.normal(22 if season == 'Yala' else 19, 2), 1),
                    # Soil (slowly varying per district)
                    'soil_ph': round(soil_ph_base[district] + rng.normal(0, 0.1), 2),
                    'organic_carbon': round(rng.normal(1.8, 0.4), 3),
                    'clay_pct': round(rng.normal(28, 5), 1),
                    'sand_pct': round(rng.normal(45, 8), 1),
                    # Historical (filled below)
                    'prev_season_yield': np.nan,
                    'prev_year_yield': np.nan,
                    'yield_3yr_avg': np.nan,
                    'extent_prev_season': round(rng.normal(400, 120), 0),
                })

    df = pd.DataFrame(rows).sort_values(['District', 'Season', 'Year']).reset_index(drop=True)

    # Historical yield features per (district, season)
    for district in synth_districts:
        for season in SEASONS:
            mask = (df['District'] == district) & (df['Season'] == season)
            yields = df.loc[mask, TARGET_COLUMN]
            df.loc[mask, 'prev_season_yield'] = yields.shift(1)
            df.loc[mask, 'prev_year_yield'] = yields.shift(1)
            df.loc[mask, 'yield_3yr_avg'] = yields.shift(1).rolling(3).mean()

    df['rainfall_x_ndvi'] = df['season_total_rainfall'] * df['season_mean_ndvi']
    df['temp_x_humidity'] = df['season_avg_temp'] * df['season_avg_humidity']
    df['ndvi_x_lst'] = df['season_mean_ndvi'] * df['season_mean_lst_day']

    df = df.dropna().reset_index(drop=True)

    os.makedirs('data/synthetic', exist_ok=True)
    out_path = 'data/synthetic/synthetic_dataset.csv'
    df.to_csv(out_path, index=False)
    print(f'  ✓ Synthetic dataset: {len(df)} observations, {len(df.columns)} features → {out_path}')
    return df


def load_real_data():
    dcs = pd.read_csv(REQUIRED_FILES['dcs_yield'])
    sources = [
        pd.read_csv(REQUIRED_FILES['nasa_power']),
        pd.read_csv(REQUIRED_FILES['modis_ndvi']),
        pd.read_csv(REQUIRED_FILES['sentinel2']),
        pd.read_csv(REQUIRED_FILES['chirps']),
        pd.read_csv(REQUIRED_FILES['modis_lst']),
        pd.read_csv(REQUIRED_FILES['soil']),
    ]
    df = dcs.copy()
    for source in sources:
        merge_keys = [c for c in ('District', 'Year', 'Season') if c in source.columns]
        if not merge_keys:
            print(f'  ⚠ Skipping source with no shared keys: cols={list(source.columns)[:5]}...')
            continue
        df = df.merge(source, on=merge_keys, how='left')
    print(f'  ✓ Real data merged: {len(df)} observations, {len(df.columns)} features')
    return df


MONTH_TO_NUM = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12,
}
DISTRICT_FIXES = {'Polannaruwa': 'Polonnaruwa'}


def load_collected_data():
    """Adapter for the real collected dataset.

    The collected CSV is MONTHLY (one row per year-month-district), Yala-only,
    with ~8 measured columns. We aggregate it to the seasonal (Year, District,
    Season) grain and map/derive everything into the canonical 32-feature schema
    (config.ALL_FEATURES) so the rest of the pipeline runs unchanged. Genuinely
    unmeasured features are derived from physical proxies where sensible, else
    median/neutral-filled (these show ~0 SHAP importance — honest by design).
    """
    print(f'\n→ DATA_VARIANT=real → loading collected real dataset:\n  {COLLECTED_FILE}')
    raw = pd.read_csv(COLLECTED_FILE)
    raw['district'] = raw['district'].astype(str).str.strip().str.title().replace(DISTRICT_FIXES)
    raw['season'] = raw['season'].astype(str).str.strip().str.title()
    raw['month_num'] = raw['month'].astype(str).str.strip().str.title().map(MONTH_TO_NUM)
    raw = raw.sort_values(['district', 'season', 'year', 'month_num'])
    if 'source' in raw.columns:
        print(f'  rows: {len(raw)} (source mix: {raw["source"].value_counts().to_dict()})')

    rows = []
    for (year, district, season), g in raw.groupby(['year', 'district', 'season']):
        g = g.sort_values('month_num')
        temp = g['temperature_c'].astype(float)
        rain = g['rainfall'].astype(float)
        hum = g['humidity_pct'].astype(float)
        ndvi = g['ndvi_i'].astype(float)
        evi = g['evi_i'].astype(float)
        n = len(g)

        order = np.arange(n)
        ndvi_growth = float(np.polyfit(order, ndvi.values, 1)[0]) if n > 1 else 0.0
        peak_pos = int(np.argmax(ndvi.values))
        time_to_peak = float((g['month_num'].values[peak_pos] - g['month_num'].min()) * 30)
        avg_temp = float(temp.mean())

        rows.append({
            'Year': int(year), 'Season': season, 'District': district,
            TARGET_COLUMN: float(g['yield_mt_per_ha'].astype(float).mean()),
            'season_indicator': 1 if season == 'Yala' else 0,
            # Weather — measured + physically derived
            'season_avg_temp': round(avg_temp, 3),
            'season_total_rainfall': round(float(rain.sum()), 3),
            'season_avg_humidity': round(float(hum.mean()), 3),
            'season_avg_solar_rad': 18.0,                       # not measured → constant
            'growing_degree_days': round(float(np.clip(temp - 10.0, 0, None).sum() * 30.0), 1),
            'heat_stress_days': int((temp > 32.0).sum()),
            'drought_index_spi': np.nan,                        # standardised below
            'temp_range': round(float(temp.max() - temp.min()), 3),
            'max_daily_rainfall': round(float(rain.max()), 3),
            # Satellite — measured + derived
            'season_mean_ndvi': round(float(ndvi.mean()), 4),
            'season_max_ndvi': round(float(ndvi.max()), 4),
            'season_min_ndvi': round(float(ndvi.min()), 4),
            'ndvi_std': round(float(ndvi.std(ddof=0)), 4),
            'ndvi_anomaly': np.nan,                             # vs district mean below
            'time_to_peak_ndvi': round(time_to_peak, 1),
            'ndvi_growth_rate': round(ndvi_growth, 5),
            'season_mean_evi': round(float(evi.mean()), 4),
            'season_mean_ndwi': 0.1,                            # not measured → constant
            'season_mean_lst_day': round(avg_temp + 6.0, 2),    # LST ≈ air temp + ~6°C
            'season_mean_lst_night': round(avg_temp - 6.0, 2),
            # Soil — SoilGrids stores ×10 (ph 58→5.8, clay 276→27.6%)
            'soil_ph': round(float(g['ph_0_5cm'].astype(float).mean()) / 10.0, 3),
            'organic_carbon': np.nan,                           # filled below
            'clay_pct': round(float(g['clay_0_5cm'].astype(float).mean()) / 10.0, 2),
            'sand_pct': round(float(g['sand_0_5cm'].astype(float).mean()) / 10.0, 2),
            # Historical — filled below
            'prev_season_yield': np.nan, 'prev_year_yield': np.nan,
            'yield_3yr_avg': np.nan, 'extent_prev_season': np.nan,
        })

    df = pd.DataFrame(rows).sort_values(['District', 'Season', 'Year']).reset_index(drop=True)

    # NDVI anomaly + standardised drought index vs each district-season climatology.
    df['ndvi_anomaly'] = (df['season_mean_ndvi']
                          - df.groupby(['District', 'Season'])['season_mean_ndvi'].transform('mean')).round(4)
    grp = df.groupby(['District', 'Season'])['season_total_rainfall']
    df['drought_index_spi'] = ((df['season_total_rainfall'] - grp.transform('mean'))
                               / grp.transform('std').replace(0, np.nan)).fillna(0.0).round(3)

    # Historical yield lags per (district, season), ordered by year (df already sorted).
    for district in df['District'].unique():
        for season in df['Season'].unique():
            mask = (df['District'] == district) & (df['Season'] == season)
            yields = df.loc[mask, TARGET_COLUMN]
            df.loc[mask, 'prev_season_yield'] = yields.shift(1)
            df.loc[mask, 'prev_year_yield'] = yields.shift(1)
            df.loc[mask, 'yield_3yr_avg'] = yields.shift(1).rolling(3, min_periods=1).mean()

    df['organic_carbon'] = df['organic_carbon'].fillna(1.8)             # SoilGrids soc not in file
    df['extent_prev_season'] = df['extent_prev_season'].fillna(400.0)   # DCS extent not in file

    df['rainfall_x_ndvi'] = df['season_total_rainfall'] * df['season_mean_ndvi']
    df['temp_x_humidity'] = df['season_avg_temp'] * df['season_avg_humidity']
    df['ndvi_x_lst'] = df['season_mean_ndvi'] * df['season_mean_lst_day']

    # Guarantee the full canonical schema; median-fill residual gaps (e.g. first-year lags).
    for col in ALL_FEATURES:
        if col not in df.columns:
            df[col] = np.nan
        if df[col].isna().any():
            med = df[col].median()
            df[col] = df[col].fillna(med if pd.notna(med) else 0.0)

    df = df[['Year', 'Season', 'District', TARGET_COLUMN] + ALL_FEATURES].reset_index(drop=True)

    out_path = 'data/collected/processed_real_seasonal.csv'
    df.to_csv(out_path, index=False)
    print(f'  ✓ Real seasonal dataset: {len(df)} observations, {len(ALL_FEATURES)} features → {out_path}')
    print(f'    districts={sorted(df.District.unique())} | seasons={sorted(df.Season.unique())} '
          f'| years={int(df.Year.min())}-{int(df.Year.max())}')
    return df


def load_data():
    print('\n' + '=' * 60)
    print('STEP 1: DATA LOADING')
    print('=' * 60)
    if DATA_VARIANT == 'real':
        return load_collected_data(), 'real'
    print('Checking data availability...')
    available = check_data_availability()
    if all(available.values()):
        print('\n✓ All real data files found. Loading real data...')
        return load_real_data(), 'real'
    missing = [k for k, v in available.items() if not v]
    print(f'\n⚠ Missing files: {missing}')
    print('→ Generating synthetic data for pipeline testing.')
    print('→ Replace with real CSVs when collected.\n')
    return generate_synthetic_data(), 'synthetic'

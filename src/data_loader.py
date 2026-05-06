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

    for year in range(2004, 2024):
        for district in DISTRICTS:
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
    for district in DISTRICTS:
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


def load_data():
    print('\n' + '=' * 60)
    print('STEP 1: DATA LOADING')
    print('=' * 60)
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

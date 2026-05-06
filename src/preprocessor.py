"""Cleaning, alignment, normalisation. Sits between the loader and feature engineering."""

import os
import numpy as np
import pandas as pd

from config import ALL_FEATURES, DISTRICTS, SEASONS, TARGET_COLUMN


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    print('\n' + '=' * 60)
    print('STEP 2: PREPROCESSING')
    print('=' * 60)

    # Required columns sanity check.
    required_keys = {'Year', 'Season', 'District', TARGET_COLUMN}
    missing_keys = required_keys - set(df.columns)
    if missing_keys:
        raise ValueError(f'Dataset missing required columns: {missing_keys}')

    n0 = len(df)

    # Drop rows with no target.
    df = df.dropna(subset=[TARGET_COLUMN]).copy()

    # Drop rows with negative or zero yield (sanity).
    df = df[df[TARGET_COLUMN] > 0].reset_index(drop=True)

    # Validate districts and seasons.
    bad_districts = set(df['District'].unique()) - set(DISTRICTS)
    if bad_districts:
        print(f'  ⚠ Filtering out unknown districts: {bad_districts}')
        df = df[df['District'].isin(DISTRICTS)].reset_index(drop=True)
    bad_seasons = set(df['Season'].unique()) - set(SEASONS)
    if bad_seasons:
        print(f'  ⚠ Filtering out unknown seasons: {bad_seasons}')
        df = df[df['Season'].isin(SEASONS)].reset_index(drop=True)

    # Forward-fill historical-yield style features per (district, season) — handles
    # the first-year edge case in the synthetic generator if dropna didn't remove it.
    historical_cols = ['prev_season_yield', 'prev_year_yield', 'yield_3yr_avg']
    for col in historical_cols:
        if col in df.columns:
            df[col] = df.groupby(['District', 'Season'])[col].ffill().bfill()

    # Backfill any remaining NaNs in numeric features with column median.
    feat_cols = [c for c in ALL_FEATURES if c in df.columns]
    for col in feat_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())

    # Winsorise extreme yield outliers (1st / 99th percentile).
    lo, hi = df[TARGET_COLUMN].quantile([0.01, 0.99])
    n_clipped = ((df[TARGET_COLUMN] < lo) | (df[TARGET_COLUMN] > hi)).sum()
    df[TARGET_COLUMN] = df[TARGET_COLUMN].clip(lo, hi)

    # Persist.
    os.makedirs('data/processed', exist_ok=True)
    out_path = 'data/processed/integrated_dataset.csv'
    df.to_csv(out_path, index=False)

    print(f'  Rows in: {n0} → Rows out: {len(df)}')
    print(f'  Target winsorised (clipped {n_clipped} outliers to [{lo:.2f}, {hi:.2f}])')
    print(f'  Saved → {out_path}')
    return df

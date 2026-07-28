"""Daily weather from NASA POWER, pulled per district centroid.

Why this exists
---------------
`data/collected/FYP data(manual) - Daily weather data.csv` holds 9,497 daily rows but
for a SINGLE point (7.8731, 80.7718). It therefore cannot distinguish the four modelled
districts, and no code path reads it anyway. It also lacks ALLSKY_SFC_SW_DWN, which is
why `season_avg_solar_rad` was hard-coded to the constant 18.0.

This module pulls the full 2000-2025 daily record for each district centroid and caches
it to one tidy CSV. PADR consumes these daily series directly — they are the substrate
for the thermal, water-balance and waterlogging terms.

Honest caveat for the report: NASA POWER's grid is ~0.5deg x 0.625deg. Matale and
Kurunegala centroids are ~29 km apart and may land in the same grid cell; the returned
coordinates are recorded per district in the output so this is checkable, not assumed.
"""

import os
import time

import numpy as np
import pandas as pd
import requests

from config import DISTRICT_CENTROIDS

API = 'https://power.larc.nasa.gov/api/temporal/daily/point'

PARAMETERS = [
    'T2M',                  # mean air temp at 2 m (degC)
    'T2M_MIN',              # daily min (degC) — frost/chill and diurnal range
    'T2M_MAX',              # daily max (degC) — heat stress
    'PRECTOTCORR',          # bias-corrected precipitation (mm/day)
    'RH2M',                 # relative humidity at 2 m (%)
    'ALLSKY_SFC_SW_DWN',    # surface shortwave down (MJ/m2/day) — drives ET0
]

START, END = '20000101', '20251231'
CACHE = 'data/collected/daily_weather_by_district.csv'

# NASA POWER writes this where a value is unavailable.
_FILL = -999.0


def _request(lat, lon, start=START, end=END, retries=3, timeout=120):
    params = {
        'parameters': ','.join(PARAMETERS), 'community': 'AG',
        'latitude': lat, 'longitude': lon,
        'start': start, 'end': end, 'format': 'JSON',
    }
    last = None
    for attempt in range(retries):
        try:
            resp = requests.get(API, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f'NASA POWER request failed after {retries} attempts: {last}')


def fetch_district(district, lat, lon, start=START, end=END):
    """One district's full daily record as a tidy DataFrame."""
    payload = _request(lat, lon, start, end)
    block = payload['properties']['parameter']
    grid_lon, grid_lat = payload['geometry']['coordinates'][:2]

    df = pd.DataFrame({p: pd.Series(block[p]) for p in PARAMETERS})
    df.index = pd.to_datetime(df.index, format='%Y%m%d')
    # np.nan, not pd.NA: pd.NA has no float representation, so .astype(float) raises
    # TypeError as soon as a request actually contains a -999 fill. That never fired for
    # the shipped 2000-2025 window but does for earlier years, where ALLSKY_SFC_SW_DWN
    # predates the satellite record.
    df = df.replace(_FILL, np.nan).astype(float)

    df.insert(0, 'district', district)
    df['grid_lat'] = grid_lat
    df['grid_lon'] = grid_lon
    return df.rename_axis('date').reset_index()


def fetch_all(force=False, cache=CACHE, centroids=None):
    """Pull every district (or reuse the cache) and write one tidy CSV."""
    if os.path.exists(cache) and not force:
        df = pd.read_csv(cache, parse_dates=['date'])
        print(f'→ Using cached daily weather: {cache} ({len(df):,} rows)')
        return df

    centroids = centroids or DISTRICT_CENTROIDS
    print(f'→ Fetching NASA POWER daily {START}-{END} for {len(centroids)} districts')
    frames = []
    for district, (lat, lon) in centroids.items():
        got = fetch_district(district, lat, lon)
        frames.append(got)
        print(f'  ✓ {district:14s} {len(got):,} days  '
              f'requested ({lat:.4f}, {lon:.4f}) → grid '
              f'({got["grid_lat"].iloc[0]:.3f}, {got["grid_lon"].iloc[0]:.3f})')

    df = pd.concat(frames, ignore_index=True).sort_values(['district', 'date'])
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    df.to_csv(cache, index=False)
    print(f'  ✓ {len(df):,} rows → {cache}')

    _report_grid_collisions(df)
    _report_missing(df)
    return df


def _report_grid_collisions(df):
    """Warn when two districts got the same weather.

    Compare the SERIES, not the returned coordinates — POWER echoes back whatever
    lat/lon you asked for, so identical grid cells are invisible in the geometry.
    Two centroids inside one ~0.5deg cell yield byte-identical daily records.
    """
    series = {d: g.sort_values('date')[PARAMETERS].to_numpy(dtype=float)
              for d, g in df.groupby('district')}
    names = sorted(series)
    collisions = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
                  if series[a].shape == series[b].shape and (series[a] == series[b]).all()]

    if collisions:
        for a, b in collisions:
            print(f'  ⚠ {a} and {b} received IDENTICAL daily weather — they fall in one '
                  f'POWER grid cell. Weather alone cannot separate them; district '
                  f'differences must come from NDVI (250 m) or soil. State this openly.')
    else:
        print('  ✓ every district received a distinct weather series')
    return collisions


def _report_missing(df):
    missing = df[PARAMETERS].isna().sum()
    flagged = missing[missing > 0]
    if len(flagged):
        print('  ⚠ missing values after -999 handling:')
        for param, n in flagged.items():
            print(f'      {param:20s} {n:,} ({100 * n / len(df):.2f}%)')
    else:
        print('  ✓ no missing values')


if __name__ == '__main__':
    frame = fetch_all(force=True)
    print()
    print(frame.groupby('district')[PARAMETERS].mean().round(2).to_string())

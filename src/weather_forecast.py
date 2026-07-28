"""Treat next season's weather as unknown, because it is.

The problem this fixes
----------------------
The dashboard predicts a future season by substituting the (district, season) historical
MEAN weather and then treating that mean as a known fact. Two things go wrong:

  1. BIAS. The model is nonlinear, so predicting at average weather is not the same as the
     average prediction across possible weathers -- f(E[w]) != E[f(w)], Jensen's inequality.
     Measured on this project: up to 1.48 MT/ha of bias per district.
  2. UNDERSTATED UNCERTAINTY. The conformal band measures model error GIVEN the features.
     It contains no allowance for not knowing the weather at all. Measured: the weather-driven
     spread alone is +/- 3.97 MT/ha, so the honest 90% band is about +/- 10.35 rather than
     the +/- 8.03 displayed -- the shown interval is ~78% of the width it should be.

What this module does instead
-----------------------------
Monte Carlo over the weather that has not happened yet. Given a forecast issue point, the
season splits in two: months already observed use their real values; months still in the
future are resampled from history many times. Each sample gives a feature vector, each
vector gives a prediction, and the spread of those predictions IS the weather uncertainty.

Two design choices that decide whether this is correct
------------------------------------------------------
* WHOLE YEARS ARE RESAMPLED, never individual features. Drawing rainfall from one year and
  temperature from another manufactures weather that cannot occur (hot AND wet AND
  low-NDVI). Sampling complete analogue years preserves the natural covariance.
* THE CLIMATOLOGY POOL IS ~45 YEARS, not 7. The yield model is stuck with 7 years of DCS
  records, but NASA POWER daily data runs from 1981, so the weather DISTRIBUTION can be
  estimated from far more data than the yield relationship. The two sources of uncertainty
  are estimated from different amounts of data, and each uses the best available.

Feature construction deliberately mirrors src/data_loader.py:201-209 exactly, including its
quirks (`max_daily_rainfall` is really the max MONTHLY total; `heat_stress_days` counts
months whose MEAN exceeds 32 C and is therefore 0 everywhere). Reproducing the quirks is
required: the model was trained on them, so sampled vectors must live on the same scale or
the predictions are out-of-distribution nonsense.

Run:  DATA_VARIANT=real PYTHONPATH=src python src/weather_forecast.py
"""

import os

import numpy as np
import pandas as pd

from config import DISTRICT_CENTROIDS, PROCESSED_DIR, WEATHER_FEATURES

DAILY_CACHE = 'data/collected/daily_weather_by_district.csv'
CLIMATOLOGY_START = 1981

# Yala runs roughly June-November; the DCS panel only ever records harvests in these months.
YALA_MONTHS = (6, 7, 8, 9, 10, 11)

_cache = {}


def ensure_daily_history(start_year=CLIMATOLOGY_START, verbose=True):
    """The cached daily record, extended backwards to `start_year` on first use.

    data/collected/daily_weather_by_district.csv ships with 2000-2025. Extending to 1981
    roughly doubles the analogue pool and costs one request per district, once.
    """
    daily = pd.read_csv(DAILY_CACHE, parse_dates=['date'])
    have_from = daily['date'].dt.year.min()
    if have_from <= start_year:
        return daily

    from data_collection.nasa_power import fetch_district  # local: avoids a hard dep at import

    extra = []
    for district, (lat, lon) in DISTRICT_CENTROIDS.items():
        if verbose:
            print(f'[weather] extending {district} back to {start_year} ...')
        extra.append(fetch_district(
            district, lat, lon,
            start=f'{start_year}0101', end=f'{have_from - 1}1231',
        ))
    daily = pd.concat([pd.concat(extra, ignore_index=True), daily], ignore_index=True)
    daily = daily.drop_duplicates(subset=['date', 'district']).sort_values(['district', 'date'])
    daily.to_csv(DAILY_CACHE, index=False)
    if verbose:
        print(f'[weather] cache now covers {daily["date"].dt.year.min()}-'
              f'{daily["date"].dt.year.max()} ({len(daily)} rows)')
    return daily


def monthly_history(daily=None):
    """Daily -> one row per (district, year, month) on the same scale the model was trained on."""
    daily = ensure_daily_history() if daily is None else daily
    d = daily.copy()
    d['year'] = d['date'].dt.year
    d['month'] = d['date'].dt.month
    d = d[d['month'].isin(YALA_MONTHS)]
    monthly = d.groupby(['district', 'year', 'month']).agg(
        temperature_c=('T2M', 'mean'),
        rainfall=('PRECTOTCORR', 'sum'),
        humidity_pct=('RH2M', 'mean'),
    ).reset_index()
    return monthly


def season_features(months_frame):
    """The 9 WEATHER_FEATURES from a set of monthly rows.

    Mirrors src/data_loader.py:201-209 term for term. `drought_index_spi` is left at NaN
    here because it is standardised against a district climatology, which only the caller
    knows; `_finalise_spi` fills it.
    """
    temp = months_frame['temperature_c'].astype(float)
    rain = months_frame['rainfall'].astype(float)
    hum = months_frame['humidity_pct'].astype(float)
    return {
        'season_avg_temp': float(temp.mean()),
        'season_total_rainfall': float(rain.sum()),
        'season_avg_humidity': float(hum.mean()),
        'season_avg_solar_rad': 18.0,                                  # constant in training
        'growing_degree_days': float(np.clip(temp - 10.0, 0, None).sum() * 30.0),
        'heat_stress_days': float((temp > 32.0).sum()),                # 0 everywhere, kept for parity
        'drought_index_spi': np.nan,
        'temp_range': float(temp.max() - temp.min()),
        'max_daily_rainfall': float(rain.max()),                       # really max MONTHLY total
    }


def climatology(district, monthly=None):
    """Per-year season features for one district across the whole analogue pool."""
    key = ('clim', district)
    if key in _cache:
        return _cache[key]
    monthly = monthly_history() if monthly is None else monthly
    sub = monthly[monthly.district == district]
    rows = []
    for year, grp in sub.groupby('year'):
        if len(grp) < len(YALA_MONTHS):        # partial year at the edge of the record
            continue
        feats = season_features(grp)
        feats['year'] = int(year)
        rows.append(feats)
    frame = pd.DataFrame(rows).set_index('year').sort_index()
    _cache[key] = frame
    return frame


def _training_stats(district):
    """Mean and sd of each weather feature for this district in the panel the model saw."""
    key = ('train', district)
    if key in _cache:
        return _cache[key]
    panel = pd.read_csv(os.path.join(PROCESSED_DIR, 'integrated_dataset.csv'))
    sub = panel[panel.District == district]
    stats = (sub[WEATHER_FEATURES].mean(), sub[WEATHER_FEATURES].std(ddof=0))
    _cache[key] = stats
    return stats


def observed_months_for(district, year, months, monthly=None):
    """That year's ACTUAL monthly weather for `months` — the forecaster's known past."""
    monthly = monthly_history() if monthly is None else monthly
    sub = monthly[(monthly.district == district) & (monthly.year == year)].set_index('month')
    return {
        int(m): {
            'temperature_c': float(sub.loc[m, 'temperature_c']),
            'rainfall': float(sub.loc[m, 'rainfall']),
            'humidity_pct': float(sub.loc[m, 'humidity_pct']),
        }
        for m in months if m in sub.index
    }


def sample_weather_features(district, n_samples, observed=None, rng=None):
    """`n_samples` plausible weather-feature vectors for one district-season.

    `observed` maps month number -> that month's actual measured weather, for the months
    already past at the forecast issue point. Those months are pinned to their real values
    and only the rest are resampled, so this one argument IS the lead time: pass nothing for
    a pre-season forecast (full spread), pass every month for a hindcast (spread collapses
    to zero). Pinning to the real values rather than to a monthly average matters — using
    the average would throw away exactly the information the forecaster has.

    Vectors are returned on the TRAINING scale: a whole analogue year supplies the shape of
    the anomaly (preserving cross-feature covariance), which is then expressed in the
    panel's own mean and sd. Without that rescaling the sampled vectors would sit off the
    distribution the model was fitted on, and the predictions would be meaningless.
    """
    rng = np.random.default_rng(0) if rng is None else rng
    observed = dict(observed or {})
    monthly = monthly_history()
    sub = monthly[monthly.district == district]
    pool_years = sorted(climatology(district, monthly).index)

    clim = climatology(district, monthly)
    clim_mu, clim_sd = clim[WEATHER_FEATURES].mean(), clim[WEATHER_FEATURES].std(ddof=0)
    train_mu, train_sd = _training_stats(district)

    drawn = rng.choice(pool_years, size=n_samples, replace=True)
    out = np.empty((n_samples, len(WEATHER_FEATURES)), dtype=np.float64)
    for i, year in enumerate(drawn):
        year_rows = sub[sub.year == year].set_index('month')
        blended = []
        for month in YALA_MONTHS:
            if month in observed:
                blended.append(observed[month])
                continue
            src = year_rows.loc[month]
            blended.append({
                'temperature_c': float(src['temperature_c']),
                'rainfall': float(src['rainfall']),
                'humidity_pct': float(src['humidity_pct']),
            })
        feats = season_features(pd.DataFrame(blended))
        vec = pd.Series(feats)[WEATHER_FEATURES]
        # Express this year's anomaly on the training panel's scale.
        z = (vec - clim_mu) / clim_sd.replace(0, np.nan)
        out[i] = (train_mu + z.fillna(0.0) * train_sd).values

    frame = pd.DataFrame(out, columns=WEATHER_FEATURES)
    # SPI is standardised rainfall within the district — recompute it on the sample itself.
    rain = frame['season_total_rainfall']
    spread = rain.std(ddof=0)
    frame['drought_index_spi'] = 0.0 if spread == 0 else ((rain - rain.mean()) / spread)
    return frame


def main():
    daily = ensure_daily_history()
    monthly = monthly_history(daily)
    print(f'\nAnalogue pool: {daily["date"].dt.year.min()}-{daily["date"].dt.year.max()}')
    for district in sorted(monthly.district.unique()):
        clim = climatology(district, monthly)
        seen = observed_months_for(district, 2024, YALA_MONTHS, monthly)
        full = sample_weather_features(district, 400, observed=seen)
        none = sample_weather_features(district, 400)
        print(f'  {district:14s} {len(clim):3d} complete seasons | rainfall sd: '
              f'pre-season {none.season_total_rainfall.std():7.1f}, '
              f'fully observed {full.season_total_rainfall.std():7.1f}')
    print()


if __name__ == '__main__':
    main()

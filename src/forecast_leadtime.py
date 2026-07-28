"""How early can anything useful be said about Big Onion yield?

This is the question the project should be answering, and it is one that survives a poor R2.
Rather than reporting a single accuracy number computed with the whole season's weather
already in hand — which no forecaster ever has — we issue a forecast at a series of points
during the season and measure what skill is available at each.

Protocol
--------
Leave-one-year-out over the 7 DCS years. At each issue point, the months already past use
that year's REAL measured weather; every remaining month is resampled from the 45-year
NASA POWER analogue pool (src/weather_forecast.py), 200 times. Each sample gives a feature
vector, each vector a prediction, and the mean of those predictions is the point forecast —
E[f(weather)], not the biased f(E[weather]) the dashboard currently reports.

Everything that is not weather (satellite, soil, historical yields) is held at the
district's mean over the TRAINING years only, at every lead. That is deliberate: it is a
weather-only lead-time curve. The 11 satellite features cannot be forecast — NDVI depends on
the crop that actually got planted — so including them would smuggle end-of-season
information into a forecast that claims to be issued months earlier.

What to expect
--------------
Given the measured signal on this panel (best |r| = 0.145, honest LOYO R2 = 0.044) the curve
will be low and probably close to flat. That is the finding, not a failure: it says weather
observed during the season carries little information about the recorded yield, which is
consistent with the target being a ratio of two small administrative numbers. Report the
curve, and read it against the break-even skill frontier from src/decision_loss.py — the
crossing point, or its absence, is the result.

Run:  DATA_VARIANT=real PYTHONPATH=src python src/forecast_leadtime.py   (~2 min)
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

from config import ALL_FEATURES, PROCESSED_DIR, RESULTS_DIR, TARGET_COLUMN, WEATHER_FEATURES
from weather_forecast import YALA_MONTHS, monthly_history, observed_months_for, sample_weather_features

N_SAMPLES = 200
NON_WEATHER = [f for f in ALL_FEATURES if f not in WEATHER_FEATURES]

# Issue points, expressed as how much of the June-November season is already observed.
ISSUE_POINTS = [
    ('pre-season', ()),
    ('after Jun', (6,)),
    ('after Jul', (6, 7)),
    ('after Aug', (6, 7, 8)),
    ('after Sep', (6, 7, 8, 9)),
    ('after Oct', (6, 7, 8, 9, 10)),
    ('after Nov (hindcast)', YALA_MONTHS),
]


def _forest():
    return RandomForestRegressor(n_estimators=400, random_state=0, min_samples_leaf=2)


def run():
    panel = pd.read_csv(os.path.join(PROCESSED_DIR, 'integrated_dataset.csv'))
    monthly = monthly_history()
    rng = np.random.default_rng(0)

    results = {}
    for label, months in ISSUE_POINTS:
        truth, point, widths = [], [], []
        for year in sorted(panel.Year.unique()):
            train = panel[panel.Year != year]
            test = panel[panel.Year == year]
            if len(test) < 2:
                continue
            model = _forest().fit(train[ALL_FEATURES], train[TARGET_COLUMN])
            # Non-weather context from the TRAINING years only — no peeking at the test year.
            ctx = train.groupby('District')[NON_WEATHER].mean()

            for _, row in test.iterrows():
                district = row['District']
                if district not in ctx.index:
                    continue
                seen = observed_months_for(district, int(year), months, monthly)
                weather = sample_weather_features(district, N_SAMPLES, observed=seen, rng=rng)

                block = pd.DataFrame(
                    np.repeat(ctx.loc[district].values[None, :], N_SAMPLES, axis=0),
                    columns=NON_WEATHER,
                )
                for col in WEATHER_FEATURES:
                    block[col] = weather[col].values
                preds = model.predict(block[ALL_FEATURES].astype(np.float32).values)

                truth.append(float(row[TARGET_COLUMN]))
                point.append(float(preds.mean()))          # E[f(w)], not f(E[w])
                widths.append(float(np.percentile(preds, 95) - np.percentile(preds, 5)))

        truth, point = np.array(truth), np.array(point)
        rho = float(np.corrcoef(truth, point)[0, 1]) if truth.std() and point.std() else 0.0
        results[label] = {
            'n_months_observed': len(months),
            'n': int(len(truth)),
            'r2': round(float(r2_score(truth, point)), 3),
            'rmse': round(float(np.sqrt(np.mean((truth - point) ** 2))), 2),
            'rho': round(rho, 3),
            'mean_weather_band_90pct': round(float(np.mean(widths)), 2),
        }
        r = results[label]
        print(f'  {label:24s} obs={r["n_months_observed"]}/6  R2={r["r2"]:+.3f}  '
              f'RMSE={r["rmse"]:5.2f}  rho={r["rho"]:+.3f}  '
              f'weather band (90%) ±{r["mean_weather_band_90pct"] / 2:.2f}')

    # The honest floor: predict the training-year mean, using no features at all.
    truth, point = [], []
    for year in sorted(panel.Year.unique()):
        train, test = panel[panel.Year != year], panel[panel.Year == year]
        if len(test) < 2:
            continue
        truth += list(test[TARGET_COLUMN])
        point += [train[TARGET_COLUMN].mean()] * len(test)
    results['climatology (no features)'] = {
        'n_months_observed': None,
        'n': len(truth),
        'r2': round(float(r2_score(truth, point)), 3),
        'rmse': round(float(np.sqrt(np.mean((np.array(truth) - np.array(point)) ** 2))), 2),
        'rho': 0.0,
        'mean_weather_band_90pct': None,
    }
    return results


def main():
    print(f'\n{"=" * 78}\nSKILL VS FORECAST LEAD TIME — weather-only, LOYO, '
          f'{N_SAMPLES} weather samples per cell\n{"=" * 78}\n')
    results = run()

    base = results['climatology (no features)']
    print(f'\n  {"climatology (no features)":24s}        R2={base["r2"]:+.3f}  '
          f'RMSE={base["rmse"]:5.2f}   <- the floor to beat')

    best = max(
        (k for k in results if k != 'climatology (no features)'),
        key=lambda k: results[k]['r2'],
    )
    print(f'\n  Best issue point: {best} (R2={results[best]["r2"]:+.3f}, '
          f'rho={results[best]["rho"]:+.3f})')
    print(f'  Beats climatology: {results[best]["rmse"] < base["rmse"]}')

    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, 'forecast_leadtime.json')
    with open(path, 'w') as fh:
        json.dump(results, fh, indent=2)
    print(f'\nWritten to {path}\n')


if __name__ == '__main__':
    main()

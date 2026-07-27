"""Year-blocked cross-conformal prediction intervals.

WHAT WAS WRONG BEFORE
---------------------
`src/conformal.py` computes a split-conformal quantile from the LOYO residuals and then
measures coverage on those same residuals. Calibration set == evaluation set, so it
reports `empirical_coverage = 1.000` for all twelve models. That is not 100% coverage,
it is a tautology: the 90th percentile of a sample always covers 90% of that sample, and
with n=28 the ceil((n+1)(1-alpha))/n adjustment pushes it to 100%.

WHAT THIS DOES INSTEAD
----------------------
Cross-conformal with the YEAR as the exchangeability block (Barber et al. 2021, "Predictive
inference with the jackknife+"). To build the interval for held-out year k, the quantile
is taken from residuals of every OTHER year. No observation ever calibrates its own
interval, so the reported coverage is a genuine out-of-block estimate.

Blocking by year rather than by row is what the panel demands: the four districts within
a year share a year effect, so row-wise exchangeability is violated and row-wise conformal
would be anti-conservative.
"""

import json
import os

import numpy as np
import pandas as pd

from config import RESULTS_DIR

DEFAULT_ALPHA = 0.1


def blocked_conformal(y, pred, years, alpha=DEFAULT_ALPHA):
    """Per-year intervals calibrated on the other years' residuals.

    Returns half-widths per observation plus the achieved coverage.
    """
    y, pred, years = np.asarray(y, float), np.asarray(pred, float), np.asarray(years)
    residuals = np.abs(y - pred)
    half_width = np.empty(len(y), float)

    for held in np.unique(years):
        calibration = residuals[years != held]
        n = len(calibration)
        if n == 0:
            half_width[years == held] = np.nan
            continue
        # Finite-sample conformal level; capped at 1.0 when n is small.
        level = min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0)
        half_width[years == held] = np.quantile(calibration, level)

    covered = residuals <= half_width
    return {
        'half_width': half_width,
        'coverage': float(np.mean(covered)),
        'mean_half_width': float(np.mean(half_width)),
        'median_half_width': float(np.median(half_width)),
        'nominal': 1 - alpha,
    }


def naive_split_conformal(y, pred, alpha=DEFAULT_ALPHA):
    """The old approach, kept only so the report can show the difference."""
    residuals = np.abs(np.asarray(y, float) - np.asarray(pred, float))
    n = len(residuals)
    level = min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0)
    q = float(np.quantile(residuals, level))
    return {'half_width': np.full(n, q), 'coverage': float(np.mean(residuals <= q)),
            'mean_half_width': q, 'median_half_width': q, 'nominal': 1 - alpha}


def run(alpha=DEFAULT_ALPHA, out_dir=None, verbose=True):
    """Score every model that has out-of-fold predictions on disk."""
    out_dir = out_dir or RESULTS_DIR
    baseline_path = os.path.join(out_dir, 'baseline_oof.json')
    padr_path = os.path.join(out_dir, 'oof_padr.json')

    with open(baseline_path) as fh:
        rows = json.load(fh)['rows']
    frame = pd.DataFrame(rows)

    if os.path.exists(padr_path):
        padr = {(r['Year'], r['District']): r['predicted']
                for r in json.load(open(padr_path))['rows']}
        frame['PADR'] = [padr[(r.Year, r.District)] for r in frame.itertuples()]

    y = frame['actual'].to_numpy(float)
    years = frame['Year'].to_numpy()
    skip = {'Year', 'District', 'actual', 'obs_weight'}
    models = [c for c in frame.columns if c not in skip]

    records = []
    for model in models:
        pred = frame[model].to_numpy(float)
        blocked = blocked_conformal(y, pred, years, alpha)
        naive = naive_split_conformal(y, pred, alpha)
        records.append({
            'Model': model,
            'blocked_coverage': round(blocked['coverage'], 4),
            'blocked_half_width': round(blocked['mean_half_width'], 4),
            'naive_coverage': round(naive['coverage'], 4),
            'naive_half_width': round(naive['mean_half_width'], 4),
            'nominal': blocked['nominal'],
        })

    table = (pd.DataFrame(records)
             .sort_values('blocked_half_width').reset_index(drop=True))

    if verbose:
        print(f'\n=== year-blocked cross-conformal intervals (alpha={alpha}, '
              f'nominal {100 * (1 - alpha):.0f}%) ===')
        print(table.to_string(index=False))
        print('\n  naive_coverage is the old same-set calculation — it reads 1.000 by')
        print('  construction and is shown only to document why it was replaced.')
        gap = table['blocked_coverage'].mean() - (1 - alpha)
        print(f'  mean blocked coverage {table["blocked_coverage"].mean():.3f} '
              f'vs nominal {1 - alpha:.2f} (gap {gap:+.3f})')

    os.makedirs(out_dir, exist_ok=True)
    table.to_csv(os.path.join(out_dir, 'conformal_blocked.csv'), index=False)
    print(f'  ✓ {out_dir}/conformal_blocked.csv')
    return table


if __name__ == '__main__':
    run()

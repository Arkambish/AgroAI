"""Leak-free LOYO baselines on the corrected target.

This is the scoreboard PADR has to beat. Nothing here is novel — that is the point.
Every number is produced under leave-one-year-out with all scaling fitted inside the
fold, on the DCS area-weighted target, using only real observations.

Two reference points frame every result:
  * TrainMean      — the best you can do knowing nothing about the held-out year
  * Oracle_YearMean — perfect knowledge of the held-out year's mean, assigned to every
                      district. NOT achievable; it is the ceiling implied by the fact
                      that 64% of target variance is between-year and 2% between-district.

Any model landing between those two is recovering some of the year effect. That is the
only thing worth measuring on this panel.
"""

import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from config import RANDOM_STATE, RESULTS_DIR, TARGET_COLUMN
from features_real import build_modelling_frame

# Columns that are keys, provenance or metadata rather than predictors.
NON_FEATURES = {
    'Year', 'Season', 'District', TARGET_COLUMN,
    'extent_ha', 'production_mt', 'n_months', 'obs_weight',
    'n_ndvi_composites', 'ndvi_is_proxy',
}


def feature_columns(frame):
    """Numeric predictors, excluding keys, provenance and any constant column."""
    cols = [c for c in frame.columns
            if c not in NON_FEATURES and frame[c].dtype.kind in 'fi']
    return [c for c in cols if frame[c].nunique(dropna=False) > 1]


def weighted_metrics(y, pred, weights=None):
    """RMSE / MAE / R2, optionally weighted by harvested area.

    The weighted R2 compares against a weighted mean, so it stays the standard
    'fraction of variance explained' quantity under the same weighting.
    """
    y, pred = np.asarray(y, float), np.asarray(pred, float)
    w = np.ones_like(y) if weights is None else np.asarray(weights, float)
    ss_res = float((w * (y - pred) ** 2).sum())
    ss_tot = float((w * (y - np.average(y, weights=w)) ** 2).sum())
    return {
        'RMSE': float(np.sqrt(ss_res / w.sum())),
        'MAE': float(np.average(np.abs(y - pred), weights=w)),
        'R2': float(1 - ss_res / ss_tot) if ss_tot > 0 else float('nan'),
    }


# --------------------------------------------------------------------------- naive


def _loyo_naive(frame, kind):
    """Predictions from a rule that uses no features at all."""
    y = frame[TARGET_COLUMN].to_numpy(float)
    years, districts = frame['Year'].to_numpy(), frame['District'].to_numpy()
    pred = np.empty(len(y), float)

    for held in sorted(set(years)):
        train, test = years != held, years == held
        if kind == 'TrainMean':
            pred[test] = y[train].mean()
        elif kind == 'DistrictMean':
            for d in set(districts[test]):
                seen = train & (districts == d)
                pred[test & (districts == d)] = y[seen].mean() if seen.any() else y[train].mean()
        elif kind == 'Persistence':
            for i in np.flatnonzero(test):
                prior = (districts == districts[i]) & (years == years[i] - 1)
                pred[i] = y[prior][0] if prior.any() else y[train].mean()
        else:
            raise ValueError(f'unknown naive baseline {kind!r}')
    return pred


def _oracle_year_mean(frame):
    """Ceiling reference — uses the held-out year's own mean. Never achievable."""
    y = frame[TARGET_COLUMN].to_numpy(float)
    years = frame['Year'].to_numpy()
    return np.array([y[years == k].mean() for k in years])


# ------------------------------------------------------------------------------ ml


def _loyo_model(frame, features, factory, scale=False, weighted=False):
    """Refit `factory()` from scratch for each held-out year; scaler fitted in-fold."""
    X = frame[features].to_numpy(float)
    y = frame[TARGET_COLUMN].to_numpy(float)
    w = frame['obs_weight'].to_numpy(float)
    years = frame['Year'].to_numpy()
    pred = np.empty(len(y), float)

    for held in sorted(set(years)):
        train, test = years != held, years == held
        X_tr, X_te = X[train], X[test]
        if scale:
            scaler = StandardScaler().fit(X_tr)
            X_tr, X_te = scaler.transform(X_tr), scaler.transform(X_te)
        model = factory()
        if weighted:
            model.fit(X_tr, y[train], sample_weight=w[train])
        else:
            model.fit(X_tr, y[train])
        pred[test] = model.predict(X_te)
    return pred


def _model_factories():
    """Deliberately modest capacity — 24 training rows per fold, 20-ish features."""
    factories = {
        'RandomForest': (lambda: RandomForestRegressor(
            n_estimators=500, max_depth=4, min_samples_leaf=3,
            random_state=RANDOM_STATE, n_jobs=-1), False, True),
        'SVR_rbf': (lambda: SVR(kernel='rbf', C=10.0, gamma='scale', epsilon=0.5), True, False),
    }
    try:
        from xgboost import XGBRegressor
        factories['XGBoost'] = (lambda: XGBRegressor(
            n_estimators=300, learning_rate=0.03, max_depth=2, subsample=0.8,
            colsample_bytree=0.8, reg_lambda=2.0, random_state=RANDOM_STATE,
            verbosity=0), False, True)
    except ImportError:
        print('  ⚠ xgboost unavailable — skipping')
    return factories


# --------------------------------------------------------------------------- driver


def run(frame=None, out_dir=None, verbose=True):
    frame = build_modelling_frame(verbose=verbose) if frame is None else frame
    features = feature_columns(frame)
    y = frame[TARGET_COLUMN].to_numpy(float)
    w = frame['obs_weight'].to_numpy(float)

    if verbose:
        print(f'\n→ LOYO baselines on {len(frame)} rows, {len(features)} features, '
              f'{frame["Year"].nunique()} folds')

    preds = {k: _loyo_naive(frame, k) for k in ['TrainMean', 'DistrictMean', 'Persistence']}
    for name, (factory, scale, weighted) in _model_factories().items():
        started = time.time()
        preds[name] = _loyo_model(frame, features, factory, scale=scale, weighted=weighted)
        if verbose:
            print(f'  ✓ {name:14s} {time.time() - started:5.2f}s')
    preds['Oracle_YearMean'] = _oracle_year_mean(frame)

    rows = []
    for name, pred in preds.items():
        plain, wtd = weighted_metrics(y, pred), weighted_metrics(y, pred, w)
        rows.append({
            'Model': name,
            'RMSE': round(plain['RMSE'], 4), 'MAE': round(plain['MAE'], 4),
            'R2': round(plain['R2'], 4),
            'RMSE_wt': round(wtd['RMSE'], 4), 'R2_wt': round(wtd['R2'], 4),
            'achievable': name != 'Oracle_YearMean',
        })
    table = pd.DataFrame(rows).sort_values('R2', ascending=False).reset_index(drop=True)

    out_dir = out_dir or RESULTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    table.to_csv(os.path.join(out_dir, 'baseline_comparison.csv'), index=False)
    with open(os.path.join(out_dir, 'baseline_oof.json'), 'w') as fh:
        json.dump({
            'features': features,
            'rows': [{'Year': int(frame['Year'].iloc[i]), 'District': str(frame['District'].iloc[i]),
                      'actual': float(y[i]), 'obs_weight': float(w[i]),
                      **{n: float(p[i]) for n, p in preds.items()}}
                     for i in range(len(y))],
        }, fh, indent=2)

    if verbose:
        print()
        print(table.to_string(index=False))
        _per_year(frame, preds, y)
        print(f'\n  ✓ {out_dir}/baseline_comparison.csv')
    return table, preds


def _per_year(frame, preds, y):
    """Fold-by-fold RMSE — shows which years are structurally unpredictable."""
    years = frame['Year'].to_numpy()
    best = max((k for k in preds if k != 'Oracle_YearMean'),
               key=lambda k: weighted_metrics(y, preds[k])['R2'])
    print(f'\n=== per-fold RMSE ({best} vs TrainMean) ===')
    print(f'{"year":>6} {"n":>3} {"actual_mean":>12} {best:>14} {"TrainMean":>12}')
    for k in sorted(set(years)):
        m = years == k
        rmse = {n: float(np.sqrt(((y[m] - preds[n][m]) ** 2).mean())) for n in (best, 'TrainMean')}
        print(f'{k:>6} {m.sum():>3} {y[m].mean():>12.2f} {rmse[best]:>14.3f} {rmse["TrainMean"]:>12.3f}')


if __name__ == '__main__':
    run()

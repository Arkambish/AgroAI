"""Fit PADR under leave-one-year-out and score it against the honest baselines."""

import json
import os
import time

import numpy as np
import pandas as pd

from baselines import feature_columns, run as run_baselines, weighted_metrics
from config import RESULTS_DIR, TARGET_COLUMN
from data_collection.nasa_power import fetch_all
from dcs_panel import load_dcs_records
from features_real import build_modelling_frame
from padr import PARAM_NAMES, prepare_cells, run_loyo
from phenology import build_phenology


def main(n_starts=20, verbose=True):
    frame = build_modelling_frame(verbose=verbose)
    _, warped = build_phenology(fetch_all(), load_dcs_records(), verbose=verbose)

    keys = list(zip(frame['Year'].astype(int), frame['District']))
    missing = [k for k in keys if k not in warped]
    if missing:
        raise RuntimeError(f'no phenology for {missing}')

    districts = sorted(frame['District'].unique())
    cells = prepare_cells(warped, districts, keys)
    y = frame[TARGET_COLUMN].to_numpy(float)
    weights = frame['obs_weight'].to_numpy(float)
    years = frame['Year'].to_numpy()

    print(f'\n→ PADR: {len(cells)} cells, {len(PARAM_NAMES) + len(districts)} parameters, '
          f'{len(set(years))} LOYO folds, {n_starts} starts/fold')
    started = time.time()
    oof, fold_params = run_loyo(cells, y, weights, years, districts, n_starts=n_starts)
    print(f'  fitted in {time.time() - started:.1f}s')

    plain = weighted_metrics(y, oof)
    wtd = weighted_metrics(y, oof, weights)
    print(f'\nPADR   RMSE {plain["RMSE"]:.4f}  MAE {plain["MAE"]:.4f}  R2 {plain["R2"]:.4f}'
          f'   |  weighted RMSE {wtd["RMSE"]:.4f}  R2 {wtd["R2"]:.4f}')

    table, preds = run_baselines(frame=frame, verbose=False)
    preds['PADR'] = oof
    comparison = _comparison_table(y, weights, preds)
    print()
    print(comparison.to_string(index=False))

    _report_parameters(fold_params, districts)
    _persist(frame, comparison, fold_params, oof, preds)
    return comparison, fold_params


def _comparison_table(y, weights, preds):
    rows = []
    for name, pred in preds.items():
        plain, wtd = weighted_metrics(y, pred), weighted_metrics(y, pred, weights)
        rows.append({'Model': name, 'RMSE': round(plain['RMSE'], 4),
                     'MAE': round(plain['MAE'], 4), 'R2': round(plain['R2'], 4),
                     'RMSE_wt': round(wtd['RMSE'], 4), 'R2_wt': round(wtd['R2'], 4),
                     'achievable': name != 'Oracle_YearMean'})
    return pd.DataFrame(rows).sort_values('R2', ascending=False).reset_index(drop=True)


def _report_parameters(fold_params, districts):
    """Learned constants across folds — this is the scientific output, not the score."""
    frame = pd.DataFrame(fold_params).T
    physics = [n for n in PARAM_NAMES if not n.startswith('beta_')][:7]
    print('\n=== learned agronomic constants (mean +/- sd across LOYO folds) ===')
    for name in physics + ['Y0']:
        if name in frame:
            col = frame[name]
            print(f'  {name:10s} {col.mean():9.3f} +/- {col.std():6.3f}   '
                  f'[{col.min():.3f}, {col.max():.3f}]')
    print('\n=== district offsets u_d ===')
    for i, district in enumerate(districts):
        key = f'u_{i}'
        if key in frame:
            print(f'  {district:14s} {frame[key].mean():+7.3f} +/- {frame[key].std():.3f}')


def _persist(frame, comparison, fold_params, oof, preds):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    comparison.to_csv(os.path.join(RESULTS_DIR, 'padr_comparison.csv'), index=False)
    with open(os.path.join(RESULTS_DIR, 'padr_params.json'), 'w') as fh:
        json.dump({str(k): {p: float(v) for p, v in params.items()}
                   for k, params in fold_params.items()}, fh, indent=2)
    with open(os.path.join(RESULTS_DIR, 'oof_padr.json'), 'w') as fh:
        json.dump({'model_name': 'PADR', 'rows': [
            {'Year': int(frame['Year'].iloc[i]), 'District': str(frame['District'].iloc[i]),
             'actual': float(frame[TARGET_COLUMN].iloc[i]),
             'predicted': float(oof[i]), 'obs_weight': float(frame['obs_weight'].iloc[i])}
            for i in range(len(oof))]}, fh, indent=2)
    print(f'\n  ✓ {RESULTS_DIR}/padr_comparison.csv, padr_params.json, oof_padr.json')


if __name__ == '__main__':
    main()

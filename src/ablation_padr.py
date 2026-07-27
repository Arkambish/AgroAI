"""Mechanism ablations for PADR — one arm per novelty claim, each falsifiable.

Given the headline finding (the agro-climatic channel is inactive on this panel), the
column that matters most here is NOT R2. It is `stress_cv`: the coefficient of variation
of the stress index S across district-years. That number says how much explainable
variation each mechanism is capable of generating in the first place.

Observed yield has a CV of about 35%. Any arm whose stress_cv sits far below that cannot
explain the target no matter how its constants are tuned, and reading the arms against
each other localises exactly which mechanism is inert and why.
"""

import json
import os

import numpy as np
import pandas as pd

from baselines import weighted_metrics
from config import RESULTS_DIR, TARGET_COLUMN
from padr import N_BETA, PARAM_SPEC, prepare_cells, run_loyo, stress_index

# name -> (description, kwargs for run_loyo, needs_calendar_axis)
ARMS = {
    'full': (
        'PADR as specified: learned physics, thermal time, waterlogging, learned beta',
        {}, False),
    'fixed_physics': (
        'N1 control — FAO/thermal constants frozen at literature values',
        {'freeze_physics': True}, False),
    'calendar_time': (
        'N2 control — same season, tau spaced in days instead of accumulated heat',
        {}, True),
    'no_waterlogging': (
        'N3 control — gamma pinned to 0, excess-water penalty switched off',
        {'pin': {'gamma': 0.0}}, False),
    'flat_beta': (
        'beta(tau) forced uniform — no phenological weighting at all',
        {'pin': {f'beta_{i}': 0.0 for i in range(N_BETA)}}, False),
    'no_shrinkage': (
        'N4 control — lambda_phys = 0, constants free to chase noise',
        {'penalties': {'lambda_phys': 0.0}}, False),
    'strong_shrinkage': (
        'N4 control — lambda_phys = 100, constants effectively pinned to literature',
        {'penalties': {'lambda_phys': 100.0}}, False),
}


def _stress_spread(fold_params, cells, n_districts):
    """CV of the stress index under each fold's fitted parameters, averaged over folds."""
    spreads = []
    for params in fold_params.values():
        vector = np.array(list(params.values()))
        stress = np.array([stress_index(vector, c) for c in cells])
        if stress.mean() > 0:
            spreads.append(stress.std() / stress.mean())
    return float(np.mean(spreads)) if spreads else float('nan')


def run(n_starts=12, verbose=True):
    from data_collection.nasa_power import fetch_all
    from dcs_panel import load_dcs_records
    from features_real import build_modelling_frame
    from phenology import build_phenology

    frame = build_modelling_frame(verbose=False)
    daily, dcs = fetch_all(), load_dcs_records()
    keys = list(zip(frame['Year'].astype(int), frame['District']))
    districts = sorted(frame['District'].unique())

    axes = {
        False: build_phenology(daily, dcs, time_axis='thermal', verbose=False)[1],
        True: build_phenology(daily, dcs, time_axis='calendar', verbose=False)[1],
    }
    cell_sets = {k: prepare_cells(v, districts, keys) for k, v in axes.items()}

    y = frame[TARGET_COLUMN].to_numpy(float)
    weights = frame['obs_weight'].to_numpy(float)
    years = frame['Year'].to_numpy()
    target_cv = float(y.std() / y.mean())

    print(f'\n→ PADR ablations: {len(ARMS)} arms, {n_starts} starts/fold')
    print(f'  observed yield CV = {100 * target_cv:.1f}% — the bar stress_cv must reach\n')

    rows = {}
    for name, (description, kwargs, calendar) in ARMS.items():
        cells = cell_sets[calendar]
        oof, fold_params = run_loyo(cells, y, weights, years, districts,
                                    n_starts=n_starts, verbose=False, **kwargs)
        plain = weighted_metrics(y, oof)
        wtd = weighted_metrics(y, oof, weights)
        rows[name] = {
            'arm': name, 'description': description,
            'RMSE': round(plain['RMSE'], 4), 'R2': round(plain['R2'], 4),
            'R2_wt': round(wtd['R2'], 4),
            'stress_cv_pct': round(100 * _stress_spread(fold_params, cells, len(districts)), 2),
            'target_cv_pct': round(100 * target_cv, 2),
        }
        if verbose:
            r = rows[name]
            print(f'  {name:18s} R2 {r["R2"]:+.4f}  RMSE {r["RMSE"]:6.3f}  '
                  f'stress_cv {r["stress_cv_pct"]:5.2f}%')

    table = pd.DataFrame(rows.values())
    deltas = _deltas(rows)

    if verbose:
        print('\n=== novelty claims, each as a delta against its control ===')
        for claim, detail in deltas.items():
            print(f'  {claim}: {detail}')

    os.makedirs(RESULTS_DIR, exist_ok=True)
    table.to_csv(os.path.join(RESULTS_DIR, 'padr_ablation.csv'), index=False)
    with open(os.path.join(RESULTS_DIR, 'padr_ablation_claims.json'), 'w') as fh:
        json.dump(deltas, fh, indent=2)
    print(f'\n  ✓ {RESULTS_DIR}/padr_ablation.csv')
    return table, deltas


def _deltas(rows):
    """Turn arm pairs into the sentence each novelty claim has to earn."""
    def compare(claim, treatment, control):
        if treatment not in rows or control not in rows:
            return f'{claim}: arms missing'
        t, c = rows[treatment], rows[control]
        return (f'dR2 = {t["R2"] - c["R2"]:+.4f} '
                f'({control} {c["R2"]:+.4f} -> {treatment} {t["R2"]:+.4f}), '
                f'stress_cv {c["stress_cv_pct"]:.2f}% -> {t["stress_cv_pct"]:.2f}%')

    return {
        'N1 learned physics vs fixed': compare('N1', 'full', 'fixed_physics'),
        'N2 thermal time vs calendar': compare('N2', 'full', 'calendar_time'),
        'N3 waterlogging term': compare('N3', 'full', 'no_waterlogging'),
        'beta(tau) learned vs flat': compare('beta', 'full', 'flat_beta'),
        'N4 shrinkage vs none': compare('N4', 'full', 'no_shrinkage'),
        'N4 shrinkage vs pinned': compare('N4', 'full', 'strong_shrinkage'),
    }


if __name__ == '__main__':
    run()

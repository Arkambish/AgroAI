"""Symbolic Regression — discovers an interpretable closed-form yield equation.

Novelty note: symbolic regression is rarely applied to crop-yield prediction. Unlike the
black-box models, it outputs a *human-readable formula* (e.g. ``yield ≈ 3.2·NDVI + 0.01·rainfall``),
which is a decision-support-friendly artifact, and its parsimony pressure resists overfitting on
the small dataset. It is trained on a few agronomically-core features so the equation stays
readable, and evaluated with the same Leave-One-Year-Out protocol as the other models so it
appears fairly in ``model_comparison.csv``.
"""

import json
import os
import re
import time

import joblib
import numpy as np
import pandas as pd

from config import RANDOM_STATE, MODELS_DIR, RESULTS_DIR
from ml_models import _loyo_predictions, _metrics, _save_oof

# Small, agronomically-core subset — keeps the discovered equation interpretable.
PREFERRED_FEATURES = [
    'season_mean_ndvi', 'season_mean_evi', 'season_total_rainfall',
    'season_avg_temp', 'soil_ph',
]


def _select_features(feature_names: list) -> list:
    """Prefer the SHAP top-5 if a feature_importance.json exists; else the agronomic subset."""
    fi_path = os.path.join(RESULTS_DIR, 'feature_importance.json')
    chosen = []
    if os.path.exists(fi_path):
        try:
            with open(fi_path) as f:
                fi = json.load(f)
            chosen = [d['name'] for d in fi if d.get('name') in feature_names][:5]
        except (ValueError, KeyError, TypeError):
            chosen = []
    if len(chosen) < 3:
        chosen = [c for c in PREFERRED_FEATURES if c in feature_names]
    return chosen[:5]


def _readable_equation(program, names: list) -> str:
    """Replace gplearn's X0/X1/... placeholders (feature order) with real feature names."""
    expr = str(program)
    for i in reversed(range(len(names))):   # reverse so X1 isn't hit by the X1x replace of X11
        expr = re.sub(rf'\bX{i}\b', names[i], expr)
    return expr


def train_symbolic_regression(X, y, feature_names, df: pd.DataFrame) -> dict | None:
    try:
        from gplearn.genetic import SymbolicRegressor
    except ImportError:
        print('  ⚠ gplearn not installed — skipping symbolic regression (pip install gplearn==0.4.2).')
        return None

    print('\n--- Symbolic Regression (interpretable equation) ---')
    t0 = time.time()
    sel = _select_features(feature_names)
    idx = [feature_names.index(c) for c in sel]
    X_sel = X[:, idx]

    def factory():
        return SymbolicRegressor(
            population_size=1000, generations=20,
            # Bounded operators only (no div/log) — these keep the equation stable and prevent
            # blow-ups when extrapolating on the small, held-out folds.
            function_set=('add', 'sub', 'mul', 'sqrt'),
            metric='rmse', parsimony_coefficient=0.02,
            p_crossover=0.7, p_subtree_mutation=0.1,
            p_hoist_mutation=0.05, p_point_mutation=0.1,
            max_samples=0.9, const_range=(-5.0, 5.0),
            random_state=RANDOM_STATE, n_jobs=1, verbose=0,
        )

    # Honest LOYO out-of-fold metrics (same protocol as the other models).
    oof = _loyo_predictions(factory, X_sel, y, df['Year'].values)

    final = factory()
    final.fit(X_sel, y)
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(final, os.path.join(MODELS_DIR, 'symbolic_best.pkl'))

    equation = _readable_equation(final._program, sel)
    elapsed = time.time() - t0
    metrics = _metrics(y, oof, 'SymbolicRegression', elapsed, {'features': sel})
    _save_oof('SymbolicRegression', oof, y, df, metrics)

    # The novel artifact: a human-readable yield equation.
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, 'symbolic_equation.txt'), 'w') as f:
        f.write(f'Avg_Yield_MT_per_Ha ≈ {equation}\n\n'
                f'Features: {sel}\nRMSE={metrics["RMSE"]}  R2={metrics["R2"]}  '
                f'MAPE={metrics["MAPE"]}%\n')
    with open(os.path.join(RESULTS_DIR, 'symbolic_equation.json'), 'w') as f:
        json.dump({'equation': equation, 'raw_program': str(final._program),
                   'features': sel, 'metrics': metrics}, f, indent=2)

    print(f'  Features used: {sel}')
    print(f'  Equation: yield ≈ {equation}')
    print(f'  RMSE={metrics["RMSE"]} MAE={metrics["MAE"]} R²={metrics["R2"]} '
          f'MAPE={metrics["MAPE"]}% ({elapsed:.1f}s)')
    print(f'  Saved → {os.path.join(RESULTS_DIR, "symbolic_equation.txt")}')
    return metrics

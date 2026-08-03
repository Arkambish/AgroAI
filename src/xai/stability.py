"""Explanation stability — does a feature's SHAP importance survive a LOYO refit?

A SHAP importance computed once, on one fit of one model, can look decisive
purely by chance on a training set this small (28 real rows / 136 synthetic
rows). Stability asks the same question the rest of the pipeline already asks
of *predictions* — "does this hold up under Leave-One-Year-Out?" — but of the
*explanation* instead: refit per LOYO fold, and see how much each feature's
SHAP importance rank/magnitude moves around across folds' models.

Each fold's SHAP is computed over the *entire* dataset (not just that fold's
handful of held-out rows) so every fold is explained against the same,
reasonably large evaluation set. That isolates the thing this metric is
actually meant to measure — how much the fitted model's explanation changes
when its *training* data changes under LOYO — from pure small-sample noise in
the SHAP estimate itself: a 4-row held-out fold (real data, n=28 over 7
years) gives a far noisier mean(|SHAP|) than an 8-row one (synthetic, n=136
over 17 years) even if the two models were equally stable, which would wash
out the very n=28-vs-n=136 gap this metric exists to surface. Permutation
importance (used by consensus.py, sharing this same LOYO pass) is kept on the
held-out fold, per its own out-of-fold definition.

`ml_models._loyo_predictions` already owns the canonical train/test split and
refit loop and is reused as-is (not reimplemented here). It only returns the
OOF prediction array though, and this module needs the *fitted model* and
*held-out rows* for every fold to compute per-fold SHAP (and, for
`consensus.py`, permutation importance). `_FoldCapture` gets both without
touching `ml_models.py`: it's a thin proxy that `_loyo_predictions` fits and
predicts with exactly like a normal estimator, and it captures fold
diagnostics as a side effect of the very `.fit()`/`.predict()` calls
`_loyo_predictions` already makes.
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import shap
from scipy.stats import spearmanr
from sklearn.inspection import permutation_importance

_XAI_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_XAI_DIR)
for _p in (_SRC_DIR, _XAI_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import ALL_FEATURES, PROCESSED_DIR, RESULTS_DIR, TARGET_COLUMN, RANDOM_STATE  # noqa: E402
from ml_models import _loyo_predictions  # noqa: E402
from explainer import _load_best_tree_model  # noqa: E402


def _load_xai_dataset():
    """Read the tabular features this DATA_VARIANT's pipeline already wrote
    (feature_engineer.engineer_features -> features_tabular.csv), rather than
    re-running data_loader/preprocessor/feature_engineer here."""
    path = os.path.join(PROCESSED_DIR, 'features_tabular.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(
            f'{path} not found — run `python main.py` '
            f'(or `python main.py --real` for DATA_VARIANT=real) first.'
        )
    df = pd.read_csv(path)
    feature_names = [f for f in ALL_FEATURES if f in df.columns]
    X = df[feature_names].astype(np.float32).values
    y = df[TARGET_COLUMN].astype(np.float32).values
    years = df['Year'].values
    return X, y, feature_names, years


class _FoldCapture:
    """Proxy estimator handed to `_loyo_predictions` in place of the real
    model. `_loyo_predictions` calls `.fit(X_tr, y_tr)` then `.predict(X_te)`
    on whatever `estimator_factory()` returns — this records the fold's SHAP
    mean(|value|) (over the full dataset — see module docstring) and
    permutation importance (over the held-out fold) at the point `.predict`
    is called, since neither is available from `_loyo_predictions` itself,
    then delegates to the real model for the actual prediction."""

    def __init__(self, base, feature_names, X_full, y_full, test_idx, sink,
                 n_repeats, random_state):
        self._base = base
        self._feature_names = feature_names
        self._X_full = X_full
        self._y_full = y_full
        self._test_idx = test_idx
        self._sink = sink
        self._n_repeats = n_repeats
        self._random_state = random_state

    def fit(self, X, y):
        self._base.fit(X, y)
        return self

    def predict(self, X):
        preds = self._base.predict(X)
        self._record(X)
        return preds

    def _record(self, X_te) -> None:
        # SHAP: explained over the FULL dataset for a consistent, larger
        # evaluation set across every fold (see module docstring).
        explainer = shap.TreeExplainer(self._base)
        sv = explainer.shap_values(self._X_full)
        if isinstance(sv, list):
            sv = sv[0]
        mean_abs_shap = np.mean(np.abs(sv), axis=0)

        # Permutation importance: on the held-out fold, per its own
        # out-of-fold definition (used by consensus.py).
        y_te = self._y_full[self._test_idx]
        perm = permutation_importance(
            self._base, X_te, y_te, n_repeats=self._n_repeats,
            random_state=self._random_state, scoring='neg_mean_squared_error',
        )

        self._sink.append({
            'n_test': int(len(self._test_idx)),
            'shap_mean_abs': {f: float(v) for f, v in zip(self._feature_names, mean_abs_shap)},
            'perm_importance_mean': {
                f: float(v) for f, v in zip(self._feature_names, perm.importances_mean)
            },
        })


def run_loyo_fold_diagnostics(X, y, feature_names, years, model=None,
                               n_repeats: int = 10, random_state: int = RANDOM_STATE) -> dict:
    """Run one LOYO pass (via `ml_models._loyo_predictions`) and return, per
    fold: the held-out year, SHAP mean(|value|) per feature, and permutation
    importance per feature. Shared by `stability.py` (SHAP) and
    `consensus.py` (permutation importance) so LOYO only runs once."""
    if model is None:
        model_name, model = _load_best_tree_model()
    else:
        model_name = type(model).__name__

    unique_years = sorted(set(years))
    sink: list = []
    fold_state = {'i': -1}

    def factory():
        fold_state['i'] += 1
        held = unique_years[fold_state['i']]
        test_idx = np.where(years == held)[0]
        base = type(model)(**model.get_params())
        return _FoldCapture(base, feature_names, X, y, test_idx, sink, n_repeats, random_state)

    oof = _loyo_predictions(factory, X, y, years)

    folds = [
        {'held_year': int(held_year), **record}
        for held_year, record in zip(unique_years, sink)
    ]
    return {
        'model_name': model_name,
        'oof': [float(v) for v in oof],
        'unique_years': [int(v) for v in unique_years],
        'folds': folds,
    }


def _load_full_data_shap_importance() -> dict | None:
    """mean(|SHAP|) per feature from the production model's own full-dataset
    SHAP pass (`explainer.run_shap_analysis` -> feature_importance.json) —
    the "full-data attribution" each LOYO fold's SHAP is compared against for
    `cross_fold_shap_consistency`. That file only ever persists the top 15
    features by design (explainer.py's own API/dashboard artefact, not
    something to change here), so this returns whatever subset it has;
    callers correlate over the intersection rather than requiring all of
    `feature_names`. None if the file doesn't exist yet."""
    path = os.path.join(RESULTS_DIR, 'feature_importance.json')
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        payload = json.load(fh)
    return {entry['name']: entry['mean_abs_shap'] for entry in payload}


def get_stability_scores(diagnostics: dict | None = None) -> dict:
    """Per-feature stability_j = 1 - normalised IQR of that feature's LOYO-fold
    SHAP importance, the global Explanation Stability Coefficient (mean
    pairwise Spearman rho between fold importance vectors), and
    cross_fold_shap_consistency — mean Spearman rho between each fold's SHAP
    attribution and the production model's full-data SHAP attribution
    (feature_importance.json). The last of these is the SHAP-consistency term
    the ERI badge (src/xai/eri.py) is built from. Writes
    outputs/results_{variant}/explanation_stability.json.

    `diagnostics`: pass in an already-computed `run_loyo_fold_diagnostics(...)`
    result (as `run_xai.py` does) to avoid re-running the LOYO pass that
    `consensus.py`'s `get_consensus_scores` also needs; computed here if
    omitted, so this still works standalone (`python -m src.xai.stability`).
    """
    X, y, feature_names, years = _load_xai_dataset()
    if diagnostics is None:
        diagnostics = run_loyo_fold_diagnostics(X, y, feature_names, years)
    folds = diagnostics['folds']

    importance_matrix = np.array([
        [fold['shap_mean_abs'][f] for f in feature_names] for fold in folds
    ])  # (n_folds, n_features)

    per_feature_stability = {}
    for j, feature in enumerate(feature_names):
        values = importance_matrix[:, j]
        q75, q25 = np.percentile(values, [75, 25])
        iqr = q75 - q25
        median = np.median(values)
        norm_iqr = 0.0 if (median == 0 and iqr == 0) else iqr / (abs(median) + 1e-8)
        per_feature_stability[feature] = float(np.clip(1.0 - norm_iqr, 0.0, 1.0))

    # Explanation Stability Coefficient: mean pairwise Spearman rho between
    # every pair of fold importance vectors — how consistently folds agree on
    # which features matter, independent of any single feature's own value.
    n_folds = importance_matrix.shape[0]
    rhos = []
    for a in range(n_folds):
        for b in range(a + 1, n_folds):
            rho, _ = spearmanr(importance_matrix[a], importance_matrix[b])
            if not np.isnan(rho):
                rhos.append(rho)
    explanation_stability_coefficient = float(np.mean(rhos)) if rhos else 0.0

    # Cross-fold SHAP consistency (the ERI badge's SHAP-consistency term):
    # mean Spearman rho between each fold's SHAP attribution and the
    # production model's full-data attribution — a different comparison than
    # the fold-vs-fold coefficient above (fold vs. the *deployed* model, not
    # fold vs. other folds). Correlated over feature_importance.json's top-15
    # subset (its own persisted shape) intersected with this dataset's
    # features, since that's the full-data ranking that actually exists. If
    # feature_importance.json isn't available yet, or the intersection is too
    # small for a meaningful rank correlation, this stays None and the ERI
    # badge falls back to a neutral score (see eri.py).
    full_data_shap = _load_full_data_shap_importance()
    common_features = (
        [f for f in feature_names if f in full_data_shap] if full_data_shap else []
    )
    cross_fold_rhos = []
    if len(common_features) >= 3:
        full_vector = [full_data_shap[f] for f in common_features]
        for fold in folds:
            fold_vector = [fold['shap_mean_abs'][f] for f in common_features]
            rho, _ = spearmanr(fold_vector, full_vector)
            if not np.isnan(rho):
                cross_fold_rhos.append(float(rho))
    cross_fold_shap_consistency = (
        float(np.clip(np.mean(cross_fold_rhos), 0.0, 1.0)) if cross_fold_rhos else None
    )

    payload = {
        'model_name': diagnostics['model_name'],
        'n_folds': n_folds,
        'per_feature_stability': per_feature_stability,
        'explanation_stability_coefficient': round(explanation_stability_coefficient, 4),
        'cross_fold_shap_consistency': (
            round(cross_fold_shap_consistency, 4) if cross_fold_shap_consistency is not None else None
        ),
        'cross_fold_shap_consistency_per_fold': [round(r, 4) for r in cross_fold_rhos],
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, 'explanation_stability.json')
    with open(out_path, 'w') as fh:
        json.dump(payload, fh, indent=2)
    print(f'  Saved -> {out_path}')
    print(f'  Explanation Stability Coefficient = {payload["explanation_stability_coefficient"]} '
          f'({n_folds} LOYO folds, model={diagnostics["model_name"]})')
    print(f'  Cross-Fold SHAP Consistency = {payload["cross_fold_shap_consistency"]} '
          f'(ERI SHAP-consistency term)')
    return per_feature_stability


if __name__ == '__main__':
    print(json.dumps(get_stability_scores(), indent=2))

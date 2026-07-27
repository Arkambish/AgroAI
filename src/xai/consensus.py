"""Explanation consensus — do SHAP, permutation importance, and the symbolic
regression equation agree on which features matter?

Three independent methods, three different failure modes:
  - SHAP (TreeExplainer) can overweight features the tree happens to split on
    early, even if that split is close to noise on a 28-136 row dataset.
  - Permutation importance measures something different (drop in held-out
    score when a feature is shuffled) and is comparatively robust to how the
    tree happened to be built, but is noisy on tiny LOYO test folds.
  - The symbolic-regression equation (src/symbolic.py) is deliberately
    restricted to ~5 agronomically-core features for readability, so it
    encodes a strong, human-curated prior on what *should* matter rather than
    a data-driven ranking.
A feature that all three point to is far more trustworthy than one that only
SHAP likes.

`consensus_j` uses top-k-membership agreement: SHAP and permutation
importance are each ranked (aggregated as the mean of their per-fold LOYO
values from `stability.run_loyo_fold_diagnostics`, reusing that one LOYO pass
rather than running it again), and a feature counts as "flagged" by a method
if it falls in that method's top `TOP_K` (default 10, roughly the top third
of the 32 features). The symbolic equation flags a feature simply by its
presence in `symbolic_equation.json`'s feature list (it never has more than
~5 features, so top-k membership doesn't apply the same way). consensus_j is
then the fraction of the three methods (0/3, 1/3, 2/3, 3/3) that flag the
feature — a simple, explainable agreement score, not a rank-correlation
blend, since with only 3 "voters" a rank-correlation metric would be both
harder to interpret and no more informative than a vote count.
"""

import json
import os
import sys

import numpy as np

_XAI_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_XAI_DIR)
for _p in (_SRC_DIR, _XAI_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import ALL_FEATURES, RESULTS_DIR  # noqa: E402
from stability import _load_xai_dataset, run_loyo_fold_diagnostics  # noqa: E402

TOP_K = 10  # ~ top third of the 32 features


def _load_symbolic_features() -> list:
    path = os.path.join(RESULTS_DIR, 'symbolic_equation.json')
    if not os.path.exists(path):
        print(f'  ⚠ {path} not found — symbolic vote treated as empty '
              f'(run `python main.py` / `python -m symbolic` first for a real vote).')
        return []
    with open(path) as fh:
        payload = json.load(fh)
    return [f for f in payload.get('features', []) if f in ALL_FEATURES]


def get_consensus_scores(diagnostics: dict | None = None) -> dict:
    """Per-feature consensus_j in [0,1]: fraction of {SHAP top-k, permutation
    top-k, symbolic-equation membership} that flag the feature. Writes
    outputs/results_{variant}/explanation_consensus.json.

    `diagnostics`: pass in an already-computed `run_loyo_fold_diagnostics(...)`
    result (as `run_xai.py` does, sharing it with `stability.get_stability_scores`)
    to avoid a second LOYO pass; computed here if omitted, so this still works
    standalone (`python -m src.xai.consensus`).
    """
    X, y, feature_names, years = _load_xai_dataset()
    if diagnostics is None:
        diagnostics = run_loyo_fold_diagnostics(X, y, feature_names, years)
    folds = diagnostics['folds']

    mean_shap = {
        f: float(np.mean([fold['shap_mean_abs'][f] for fold in folds]))
        for f in feature_names
    }
    mean_perm = {
        f: float(np.mean([fold['perm_importance_mean'][f] for fold in folds]))
        for f in feature_names
    }

    shap_top_k = set(sorted(mean_shap, key=mean_shap.get, reverse=True)[:TOP_K])
    perm_top_k = set(sorted(mean_perm, key=mean_perm.get, reverse=True)[:TOP_K])
    symbolic_features = set(_load_symbolic_features())

    per_feature_consensus = {}
    for f in ALL_FEATURES:
        votes = int(f in shap_top_k) + int(f in perm_top_k) + int(f in symbolic_features)
        per_feature_consensus[f] = round(votes / 3.0, 4)

    payload = {
        'model_name': diagnostics['model_name'],
        'top_k': TOP_K,
        'shap_top_k': sorted(shap_top_k, key=mean_shap.get, reverse=True),
        'permutation_top_k': sorted(perm_top_k, key=mean_perm.get, reverse=True),
        'symbolic_features': sorted(symbolic_features),
        'mean_shap_importance': mean_shap,
        'mean_permutation_importance': mean_perm,
        'per_feature_consensus': per_feature_consensus,
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, 'explanation_consensus.json')
    with open(out_path, 'w') as fh:
        json.dump(payload, fh, indent=2)
    print(f'  Saved -> {out_path}')
    return per_feature_consensus


if __name__ == '__main__':
    print(json.dumps(get_consensus_scores(), indent=2))

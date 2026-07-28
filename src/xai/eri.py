"""Explanation Reliability Index (ERI) — composes grounding, stability, and
consensus into one per-feature and one per-prediction trust score.

    ERI_j          = (stability_j + grounding_j + consensus_j) / 3
    ERI_prediction = sum(|SHAP_j| * ERI_j) / sum(|SHAP_j|)   over that
                     prediction's features

`compute_eri` is called from two places with two different weight vectors:
  - the live API (src/api.py), on every /predict, with that specific
    prediction's own SHAP values — so `eri`/`per_feature_eri` reflect the
    actual features driving *this* prediction;
  - `run_xai.py`, once per pipeline run, with the dataset-level mean(|SHAP|)
    from `feature_importance.json` as a representative weighting, so
    outputs/results_{variant}/eri.json captures an overall reliability
    picture rather than a single request's.

Grounding is read from `grounding.GROUNDING_REGISTRY` directly (an in-memory
constant — recomputing/rewriting feature_grounding.json on every API request
would be pure overhead). Stability and consensus are read from the JSON files
`stability.get_stability_scores()` / `consensus.get_consensus_scores()` wrote
— both require a full LOYO refit + SHAP + permutation-importance pass, which
is `run_xai.py`'s job, not something to redo inside a prediction request. If
those files don't exist yet (pipeline not run for this DATA_VARIANT), a
feature's stability/consensus falls back to a neutral 0.5 rather than
raising, since grounding alone is still a meaningful partial signal.
"""

import itertools
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
from grounding import GROUNDING_REGISTRY  # noqa: E402

_NEUTRAL_SCORE = 0.5  # used when stability/consensus haven't been computed yet


def _load_per_feature(filename: str, key: str) -> dict:
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        print(f'  ⚠ {path} not found — {key} defaulting to {_NEUTRAL_SCORE} for all features '
              f'(run `python -m src.xai.run_xai` first for real values).')
        return {}
    with open(path) as fh:
        payload = json.load(fh)
    return payload.get(key, {})


def compute_eri(shap_values: dict) -> dict:
    """Compose per-feature ERI_j and the SHAP-weighted prediction-level ERI.

    `shap_values`: {feature: signed SHAP value} for one prediction (or, when
    called from run_xai.py, the dataset-level mean(|SHAP|) as a stand-in).
    """
    stability_scores = _load_per_feature('explanation_stability.json', 'per_feature_stability')
    consensus_scores = _load_per_feature('explanation_consensus.json', 'per_feature_consensus')

    per_feature_eri = {}
    for feature in ALL_FEATURES:
        grounding_j = GROUNDING_REGISTRY.get(feature, 0.0)
        stability_j = stability_scores.get(feature, _NEUTRAL_SCORE)
        consensus_j = consensus_scores.get(feature, _NEUTRAL_SCORE)
        per_feature_eri[feature] = round((stability_j + grounding_j + consensus_j) / 3.0, 4)

    abs_shap = {
        f: abs(v) for f, v in shap_values.items()
        if f in per_feature_eri and np.isfinite(v)
    }
    total_abs_shap = sum(abs_shap.values())
    if total_abs_shap > 0:
        eri = sum(abs_shap[f] * per_feature_eri[f] for f in abs_shap) / total_abs_shap
    else:
        # No usable SHAP signal for this prediction — fall back to the
        # unweighted mean per-feature ERI rather than dividing by zero.
        eri = float(np.mean(list(per_feature_eri.values()))) if per_feature_eri else 0.0

    return {
        'eri': round(float(eri), 4),
        'per_feature_eri': per_feature_eri,
    }


def weight_sensitivity_sweep(per_feature_scores: dict, n_steps: int = 10) -> dict:
    """Vary (w_stability, w_grounding, w_consensus) over the simplex
    (w1+w2+w3=1, grid resolution 1/n_steps) and report how much the top-5
    feature ranking (by raw ERI_j = w1*stability_j + w2*grounding_j +
    w3*consensus_j, NOT SHAP-weighted — this sweep is about which features
    the composite score itself trusts most, independent of any one
    prediction) changes relative to the equal-weight (1/3, 1/3, 1/3)
    baseline.

    `per_feature_scores`: {feature: {'stability':.., 'grounding':..,
    'consensus':..}} for every feature.
    """
    features = list(per_feature_scores.keys())

    def top5_for(w1: float, w2: float, w3: float) -> tuple:
        eri_j = {
            f: w1 * per_feature_scores[f]['stability']
            + w2 * per_feature_scores[f]['grounding']
            + w3 * per_feature_scores[f]['consensus']
            for f in features
        }
        return tuple(sorted(eri_j, key=eri_j.get, reverse=True)[:5])

    baseline_top5 = top5_for(1 / 3, 1 / 3, 1 / 3)

    sweep = []
    distinct_top5_sets = set()
    n_diff = 0
    for i, j in itertools.product(range(n_steps + 1), repeat=2):
        if i + j > n_steps:
            continue
        k = n_steps - i - j
        w1, w2, w3 = i / n_steps, j / n_steps, k / n_steps
        top5 = top5_for(w1, w2, w3)
        distinct_top5_sets.add(top5)
        changed = top5 != baseline_top5
        n_diff += int(changed)
        sweep.append({
            'w_stability': round(w1, 3), 'w_grounding': round(w2, 3), 'w_consensus': round(w3, 3),
            'top5': list(top5), 'differs_from_baseline': changed,
        })

    n_total = len(sweep)
    return {
        'baseline_top5': list(baseline_top5),
        'n_weight_combinations': n_total,
        'n_diff_from_baseline': n_diff,
        'fraction_ranking_changed': round(n_diff / n_total, 4) if n_total else 0.0,
        'n_distinct_top5_sets': len(distinct_top5_sets),
        'sweep': sweep,
    }


if __name__ == '__main__':
    print(json.dumps(compute_eri({f: 1.0 for f in ALL_FEATURES}), indent=2))

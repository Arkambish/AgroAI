"""Explainability Reliability Index (ERI) — a single per-prediction trust
badge built from exactly two published, auditable signals (report §5.9.2,
§6.13):

  1. Cross-fold SHAP consistency — mean Spearman rank correlation between
     each LOYO fold's SHAP attribution and the production model's full-data
     SHAP attribution. Computed and persisted by `stability.py` (as
     `cross_fold_shap_consistency` in explanation_stability.json) since it
     already runs the LOYO refit + per-fold SHAP pass this needs; read from
     there rather than recomputed here.
  2. Conformal interval reliability — the conformal prediction interval's
     width (`2 * q` from conformal.json), expressed relative to the target
     district's historical yield range (max - min recorded yield for that
     district), so a wide interval on a low-yield district isn't scored the
     same as an equally wide one on a high-yield district. Narrower
     (relative to that range) -> higher reliability.

    ERI = W_SHAP_CONSISTENCY * cross_fold_shap_consistency
        + W_INTERVAL_RELIABILITY * interval_reliability

Deliberately NOT a black-box model trained to predict reliability — scoring
one model's reliability with a second uninspectable model would defeat the
purpose of the index. Both terms are direct, already-published quantities
(explanation_stability.json, conformal.json, the district's own historical
yield range), so the badge can be recomputed by hand for any prediction.

Grounding (per-feature "how real is this feature's data" tiers) and
consensus (SHAP/permutation/symbolic agreement) are NOT part of ERI. They
remain independently useful diagnostics — grounding.py backs no live
endpoint and consensus.py backs GET /consensus — but neither feeds this
score; see `grounding.py` / `consensus.py` module docstrings.

`compute_eri` is called from two places:
  - the live API (src/api.py), on every /predict, with that specific
    prediction's own conformal interval width and target district — so
    `eri` reflects the reliability of *this* prediction's own explanation
    and interval;
  - `run_xai.py`, once per pipeline run, via `compute_dataset_level_eri`,
    which averages interval reliability across every district in the
    dataset (there being no single prediction/district at that point) to
    produce outputs/results_{variant}/eri.json's dataset-level badge.

`per_feature_eri`: kept in the return payload only for API-shape
compatibility with the dashboard (Explain/Recommend tabs read `eri` and
`per_feature_eri` straight off the stored prediction). Since ERI is no
longer computed per-feature, every feature is reported with the same
aggregate `eri` value. The dashboard's own per-row aggregation
(SHAP-|value|-weighted mean of `per_feature_eri` across a row's underlying
raw features) then trivially collapses to that same constant for every row,
which is the correct behaviour for a score that is a single composite badge
for the prediction as a whole, not a per-feature quantity.
"""

import json
import os
import sys

import numpy as np
import pandas as pd

_XAI_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_XAI_DIR)
for _p in (_SRC_DIR, _XAI_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import ALL_FEATURES, PROCESSED_DIR, RESULTS_DIR, TARGET_COLUMN  # noqa: E402

_NEUTRAL_SCORE = 0.5  # used when a component hasn't been computed yet

# Equal-weighted per the report ("a composite ... equal-weighted combination
# ... unless an existing config file specifies different weights"); no such
# config exists in this project, so these are the working defaults.
W_SHAP_CONSISTENCY = 0.5
W_INTERVAL_RELIABILITY = 0.5


def _load_cross_fold_consistency() -> float:
    """Cross-fold SHAP consistency term, read from
    explanation_stability.json (written by `stability.get_stability_scores`).
    Falls back to the neutral score if that file — or the field itself,
    which needs feature_importance.json to have existed at the time
    stability.py ran — isn't there yet."""
    path = os.path.join(RESULTS_DIR, 'explanation_stability.json')
    if not os.path.exists(path):
        print(f'  ⚠ {path} not found — cross-fold SHAP consistency defaulting to '
              f'{_NEUTRAL_SCORE} (run `python -m src.xai.run_xai` first for a real value).')
        return _NEUTRAL_SCORE
    with open(path) as fh:
        payload = json.load(fh)
    value = payload.get('cross_fold_shap_consistency')
    if value is None:
        print(f'  ⚠ cross_fold_shap_consistency missing from {path} — defaulting to '
              f'{_NEUTRAL_SCORE} (needs feature_importance.json; run the full pipeline first).')
        return _NEUTRAL_SCORE
    return float(np.clip(value, 0.0, 1.0))


def resolve_district_yield_ranges(df: pd.DataFrame | None = None) -> dict:
    """{district: historical (max - min) recorded yield}, from the processed
    integrated dataset — the denominator that normalises a conformal
    interval's width against how much a given district's yield actually
    varies.

    Pass an already-loaded `df` (e.g. api.py's cached context dataset) to
    avoid a second CSV read on every request; loads
    PROCESSED_DIR/integrated_dataset.csv itself otherwise (dataset-level /
    standalone use, e.g. from `run_xai.py`).
    """
    if df is None:
        path = os.path.join(PROCESSED_DIR, 'integrated_dataset.csv')
        if not os.path.exists(path):
            return {}
        df = pd.read_csv(path)
    if 'District' not in df.columns or TARGET_COLUMN not in df.columns:
        return {}

    ranges = {}
    for district, grp in df.groupby('District'):
        yields = pd.to_numeric(grp[TARGET_COLUMN], errors='coerce').dropna()
        if not yields.empty:
            ranges[str(district)] = float(yields.max() - yields.min())
    return ranges


def _load_conformal_q(model_name: str | None) -> float | None:
    """Conformal half-width `q` for `model_name` from conformal.json
    (src/conformal.py). Falls back to the first available model's `q` if
    `model_name` isn't in there (or wasn't given) — used only by the
    dataset-level badge, which isn't tied to one served model's own
    prediction the way POST /predict is."""
    path = os.path.join(RESULTS_DIR, 'conformal.json')
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        payload = json.load(fh)
    if model_name and model_name in payload:
        return float(payload[model_name]['q'])
    if payload:
        return float(next(iter(payload.values()))['q'])
    return None


def interval_reliability(interval_width: float | None, district_yield_range: float | None) -> float:
    """1 - (interval_width / district_yield_range), clipped to [0, 1]: a
    conformal interval as wide as (or wider than) the district's entire
    historical yield range scores 0; a vanishingly narrow one scores ~1.
    Falls back to the neutral score when either input is missing or the
    range isn't usable (e.g. a district with only one recorded yield, or no
    conformal interval computed yet for the served model)."""
    if interval_width is None or district_yield_range is None or district_yield_range <= 0:
        return _NEUTRAL_SCORE
    normalized_width = interval_width / district_yield_range
    return float(np.clip(1.0 - normalized_width, 0.0, 1.0))


def _combine(cross_fold_shap_consistency: float, interval_reliability_score: float) -> float:
    return round(
        float(
            W_SHAP_CONSISTENCY * cross_fold_shap_consistency
            + W_INTERVAL_RELIABILITY * interval_reliability_score
        ),
        4,
    )


def compute_eri(interval_width: float | None, district_yield_range: float | None) -> dict:
    """Compute the ERI badge for one prediction.

    `interval_width`: this prediction's conformal interval width (`2 * q`
    from conformal.json for the served model), or None if no conformal
    calibration exists yet for it.
    `district_yield_range`: the target district's historical (max - min)
    recorded yield (see `resolve_district_yield_ranges`), or None if the
    district isn't in the processed dataset.
    """
    cross_fold_shap_consistency = _load_cross_fold_consistency()
    interval_reliability_score = interval_reliability(interval_width, district_yield_range)
    eri = _combine(cross_fold_shap_consistency, interval_reliability_score)

    return {
        'eri': eri,
        'per_feature_eri': dict.fromkeys(ALL_FEATURES, eri),
        'cross_fold_shap_consistency': round(cross_fold_shap_consistency, 4),
        'interval_reliability': round(interval_reliability_score, 4),
        'conformal_interval_width': interval_width,
        'district_yield_range': district_yield_range,
    }


def compute_dataset_level_eri(model_name: str | None = None) -> dict:
    """Dataset-level ERI badge for outputs/results_{variant}/eri.json
    (`run_xai.py`, once per pipeline run). Reuses the same
    cross_fold_shap_consistency term as every /predict response; the
    interval term is the mean interval_reliability across every district in
    the processed dataset (there's no single prediction/district to
    normalise against at this level).
    """
    cross_fold_shap_consistency = _load_cross_fold_consistency()

    q = _load_conformal_q(model_name)
    ranges = resolve_district_yield_ranges()
    if q is not None and ranges:
        per_district_reliability = {
            district: interval_reliability(2 * q, r) for district, r in ranges.items()
        }
        mean_interval_reliability = float(np.mean(list(per_district_reliability.values())))
    else:
        per_district_reliability = {}
        mean_interval_reliability = _NEUTRAL_SCORE

    eri = _combine(cross_fold_shap_consistency, mean_interval_reliability)

    return {
        'eri': eri,
        'per_feature_eri': dict.fromkeys(ALL_FEATURES, eri),
        'cross_fold_shap_consistency': round(cross_fold_shap_consistency, 4),
        'interval_reliability': round(mean_interval_reliability, 4),
        'conformal_q': q,
        'per_district_interval_reliability': {
            d: round(v, 4) for d, v in per_district_reliability.items()
        },
    }


if __name__ == '__main__':
    print(json.dumps(compute_dataset_level_eri(), indent=2))

"""Entry point for the Explanation Reliability Index pipeline.

Runs grounding -> stability -> consensus -> eri in sequence for whichever
DATA_VARIANT is selected (`real` or `synthetic`, via the DATA_VARIANT env
var — same convention as main.py / config.py), writing all four JSON files
into that variant's outputs/results*/ directory.

Usage:
    DATA_VARIANT=real python -m src.xai.run_xai
    DATA_VARIANT=synthetic python -m src.xai.run_xai

Requires that variant's pipeline (`python main.py` / `python main.py --real`)
to have already been run at least once, since this reads that pipeline's
persisted features_tabular.csv, trained model artefacts, feature_importance.json
and symbolic_equation.json rather than regenerating them.
"""

import json
import os
import sys

_XAI_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_XAI_DIR)
for _p in (_SRC_DIR, _XAI_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import DATA_VARIANT, RESULTS_DIR  # noqa: E402
from grounding import get_grounding_scores  # noqa: E402
from stability import _load_xai_dataset, run_loyo_fold_diagnostics, get_stability_scores  # noqa: E402
from consensus import get_consensus_scores  # noqa: E402
from eri import compute_eri, weight_sensitivity_sweep  # noqa: E402


def main() -> None:
    print('\n' + '=' * 60)
    print(f'  EXPLANATION RELIABILITY INDEX  (DATA_VARIANT={DATA_VARIANT})')
    print(f'  -> {RESULTS_DIR}')
    print('=' * 60)

    print('\n--- Grounding ---')
    grounding_scores = get_grounding_scores()

    # One LOYO pass (refit + SHAP + permutation importance per fold), shared
    # by both stability and consensus so it doesn't run twice.
    print('\n--- LOYO fold diagnostics (refit + SHAP + permutation importance) ---')
    X, y, feature_names, years = _load_xai_dataset()
    diagnostics = run_loyo_fold_diagnostics(X, y, feature_names, years)

    print('\n--- Stability ---')
    stability_scores = get_stability_scores(diagnostics=diagnostics)

    print('\n--- Consensus (SHAP + permutation importance + symbolic equation) ---')
    consensus_scores = get_consensus_scores(diagnostics=diagnostics)

    print('\n--- ERI ---')
    fi_path = os.path.join(RESULTS_DIR, 'feature_importance.json')
    if os.path.exists(fi_path):
        with open(fi_path) as fh:
            feature_importance = json.load(fh)
        shap_values = {entry['name']: entry['mean_abs_shap'] for entry in feature_importance}
    else:
        print(f'  ⚠ {fi_path} not found — run explainer.run_shap_analysis first for a real '
              f'SHAP weighting; using an equal weighting for now.')
        shap_values = {f: 1.0 for f in grounding_scores}

    result = compute_eri(shap_values)

    per_feature_scores = {
        f: {
            'stability': stability_scores.get(f, 0.5),
            'grounding': grounding_scores.get(f, 0.0),
            'consensus': consensus_scores.get(f, 0.5),
        }
        for f in grounding_scores
    }
    result['weight_sensitivity'] = weight_sensitivity_sweep(per_feature_scores)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, 'eri.json')
    with open(out_path, 'w') as fh:
        json.dump(result, fh, indent=2)
    print(f'  Saved -> {out_path}')
    print(f'  Aggregate ERI (dataset-level SHAP weighting) = {result["eri"]}')
    print(f'  Top-5 ranking changes across the weight-sensitivity sweep: '
          f'{result["weight_sensitivity"]["fraction_ranking_changed"] * 100:.1f}% of '
          f'{result["weight_sensitivity"]["n_weight_combinations"]} weight combinations')

    print('\n' + '=' * 60)
    print('  ERI PIPELINE COMPLETE')
    print(f'    {RESULTS_DIR}/feature_grounding.json')
    print(f'    {RESULTS_DIR}/explanation_stability.json')
    print(f'    {RESULTS_DIR}/explanation_consensus.json')
    print(f'    {RESULTS_DIR}/eri.json')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()

"""Entry point for the Explanation Reliability Index pipeline.

Runs stability -> consensus -> eri in sequence for whichever DATA_VARIANT is
selected (`real` or `synthetic`, via the DATA_VARIANT env var — same
convention as main.py / config.py), writing JSON artefacts into that
variant's outputs/results*/ directory.

Usage:
    DATA_VARIANT=real python -m src.xai.run_xai
    DATA_VARIANT=synthetic python -m src.xai.run_xai

Requires that variant's pipeline (`python main.py` / `python main.py --real`)
to have already been run at least once, since this reads that pipeline's
persisted features_tabular.csv, trained model artefacts, feature_importance.json
and symbolic_equation.json rather than regenerating them.

`grounding.py` is intentionally not run here: it backs no live endpoint and
its only former consumer was the old per-feature ERI formula (removed — see
eri.py's module docstring). It's flagged for deletion rather than removed
outright; see that flag before deleting it. `consensus.py` IS still run —
GET /consensus (src/api.py) serves its output directly — even though its
scores no longer feed into ERI.
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
from stability import _load_xai_dataset, run_loyo_fold_diagnostics, get_stability_scores  # noqa: E402
from consensus import get_consensus_scores  # noqa: E402
from eri import compute_dataset_level_eri  # noqa: E402


def main() -> None:
    print('\n' + '=' * 60)
    print(f'  EXPLANATION RELIABILITY INDEX  (DATA_VARIANT={DATA_VARIANT})')
    print(f'  -> {RESULTS_DIR}')
    print('=' * 60)

    # One LOYO pass (refit + SHAP + permutation importance per fold), shared
    # by both stability and consensus so it doesn't run twice.
    print('\n--- LOYO fold diagnostics (refit + SHAP + permutation importance) ---')
    X, y, feature_names, years = _load_xai_dataset()
    diagnostics = run_loyo_fold_diagnostics(X, y, feature_names, years)

    print('\n--- Stability (+ cross-fold SHAP consistency, the ERI SHAP term) ---')
    get_stability_scores(diagnostics=diagnostics)

    print('\n--- Consensus (SHAP + permutation importance + symbolic equation) ---')
    get_consensus_scores(diagnostics=diagnostics)

    print('\n--- ERI ---')
    result = compute_dataset_level_eri(model_name=diagnostics['model_name'])

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, 'eri.json')
    with open(out_path, 'w') as fh:
        json.dump(result, fh, indent=2)
    print(f'  Saved -> {out_path}')
    print(f'  Dataset-level ERI = {result["eri"]} '
          f'(SHAP consistency={result["cross_fold_shap_consistency"]}, '
          f'interval reliability={result["interval_reliability"]} '
          f'across {len(result["per_district_interval_reliability"])} districts)')

    print('\n' + '=' * 60)
    print('  ERI PIPELINE COMPLETE')
    print(f'    {RESULTS_DIR}/explanation_stability.json')
    print(f'    {RESULTS_DIR}/explanation_consensus.json')
    print(f'    {RESULTS_DIR}/eri.json')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()

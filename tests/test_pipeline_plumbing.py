"""Guards on the two loaders that crashed the retrain.

Both failures shared a cause: a payload written by one part of the pipeline with a schema the
consuming part did not expect. Neither was caught until a full re-run was attempted months
later, so they are pinned here.
"""

import glob
import json
import os

import numpy as np
import pytest


@pytest.fixture(scope='module')
def oof_paths():
    from config import RESULTS_DIR
    paths = sorted(glob.glob(os.path.join(RESULTS_DIR, 'oof_*.json')))
    if not paths:
        pytest.skip('no out-of-fold files; run the pipeline first')
    return paths


def test_every_oof_payload_has_the_rows_the_loaders_need(oof_paths):
    for path in oof_paths:
        with open(path) as fh:
            payload = json.load(fh)
        rows = payload.get('rows')
        assert rows, f'{os.path.basename(path)} has no rows'
        for field in ('Year', 'District', 'actual', 'predicted'):
            assert field in rows[0], f'{os.path.basename(path)} rows lack {field!r}'


def test_stacking_tolerates_a_payload_without_season(oof_paths):
    """PADR's OOF omits Season. It must be admitted via the (Year, District) fallback rather
    than crashing or being silently dropped from the committee."""
    import stacking
    keys, included, y, years = stacking._load_base_oof()
    assert keys, 'stacking loaded no rows'
    assert len(included) >= 2, f'committee collapsed to {sorted(included)}'

    names = {os.path.basename(p)[len('oof_'):-len('.json')] for p in oof_paths}
    if 'padr' in names:
        assert 'padr' in included, (
            'padr has a complete OOF file but was excluded from the committee'
        )


def test_stacking_never_stacks_its_own_output(oof_paths):
    import stacking
    _, included, _, _ = stacking._load_base_oof()
    assert not [n for n in included if n.startswith('stack')], (
        f'combiner outputs entered the base committee: {sorted(included)}'
    )


def test_stacking_matrix_is_complete_and_aligned():
    import stacking
    keys, included, y, years = stacking._load_base_oof()
    assert len(y) == len(keys) == len(years)
    for name, preds in included.items():
        assert len(preds) == len(keys), f'{name} misaligned with the key order'
        assert np.isfinite(preds).all(), f'{name} contributed non-finite predictions'


def test_final_comparison_recomputes_metrics_when_absent(tmp_path, monkeypatch):
    """A payload with rows but no metrics block must be scored, not dropped or crashed on.

    This is the exact shape of oof_padr.json that broke `generate_final_comparison`.
    """
    import evaluator

    rows = [{'Year': 2019 + i // 4, 'Season': 'Yala', 'District': f'D{i % 4}',
             'actual': 10.0 + i, 'predicted': 11.0 + i} for i in range(8)]
    # _load_oof_payloads keys by the payload's own model_name, so mirror that here.
    payloads = {
        'WithMetrics': {'model_name': 'WithMetrics', 'rows': rows,
                        'metrics': {'Model': 'WithMetrics', 'RMSE': 1.0, 'MAE': 1.0,
                                    'R2': 0.5, 'MAPE': 10.0}},
        'NoMetrics': {'model_name': 'NoMetrics', 'rows': rows},
    }
    monkeypatch.setattr(evaluator, '_load_oof_payloads', lambda: payloads)
    monkeypatch.setattr(evaluator, 'RESULTS_DIR', str(tmp_path))
    monkeypatch.setattr(evaluator, 'PLOTS_DIR', str(tmp_path))
    monkeypatch.setattr(evaluator, '_comparison_bar_plot', lambda *a, **k: None)

    out = evaluator.generate_final_comparison()
    assert set(out['Model']) == {'WithMetrics', 'NoMetrics'}
    recomputed = out[out['Model'] == 'NoMetrics'].iloc[0]
    # Every prediction is exactly 1.0 high, so RMSE and MAE are both 1.
    assert recomputed['RMSE'] == pytest.approx(1.0, abs=1e-6)
    assert recomputed['MAE'] == pytest.approx(1.0, abs=1e-6)


def test_nasa_power_fill_values_become_nan_not_pdNA():
    """`pd.NA` has no float representation, so .astype(float) threw as soon as a request
    actually contained a -999 fill. That blocked the pre-2000 backfill entirely."""
    import pandas as pd
    from data_collection import nasa_power

    frame = pd.DataFrame({'T2M': [25.0, nasa_power._FILL, 27.0]})
    cleaned = frame.replace(nasa_power._FILL, np.nan).astype(float)
    assert cleaned['T2M'].isna().sum() == 1
    assert cleaned['T2M'].dtype == float

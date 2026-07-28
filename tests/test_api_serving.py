"""Guards on the serving layer.

Each test corresponds to a defect that shipped: reporting one model's accuracy while serving
another, selecting the served model by source-code ordering rather than merit, and presenting
a climatological average as a year-specific forecast.
"""

import os

import numpy as np
import pytest


def test_reported_metrics_belong_to_the_served_model(loaded_api, comparison):
    """The API once reported PhysResidual's R2 while serving XGBoost."""
    served = loaded_api._state['model_name']
    metrics = loaded_api._state['metrics'] or {}
    assert metrics, 'no metrics loaded for the served model'
    assert metrics.get('Model') == served, (
        f'serving {served} but reporting metrics for {metrics.get("Model")}'
    )

    row = comparison[comparison['Model'] == served]
    if not row.empty:
        assert abs(float(metrics['R2']) - float(row.iloc[0]['R2'])) < 1e-6


def test_served_model_is_the_best_available_not_the_first_listed(loaded_api, comparison):
    """The fallback used to pick whichever candidate was typed first in a dict literal."""
    from config import MODELS_DIR
    candidates = {'XGBoost': 'xgb_best.pkl', 'RandomForest': 'rf_best.pkl',
                  'SVR': 'svr_best.pkl'}
    available = [n for n, f in candidates.items()
                 if os.path.exists(os.path.join(MODELS_DIR, f))]
    if len(available) < 2:
        pytest.skip('need at least two servable artefacts to test ranking')

    scored = comparison[comparison['Model'].isin(available)]
    if scored.empty:
        pytest.skip('no scores on disk for the servable candidates')

    best = scored.sort_values('R2', ascending=False).iloc[0]['Model']
    assert loaded_api._state['model_name'] == best, (
        f'serving {loaded_api._state["model_name"]} but {best} scores higher among '
        f'servable candidates'
    )


def test_prediction_without_observations_is_labelled_climatological(loaded_api):
    payload, status = loaded_api.run_prediction(
        {'district': 'Anuradhapura', 'season': 'Yala', 'year': 2026})
    assert status == 200
    basis = payload['forecast_basis']
    assert basis['basis'] == 'climatological'
    assert basis['year_affects_prediction'] is False
    assert basis['n_observed_inputs'] == 0


def test_supplying_an_observation_switches_the_basis(loaded_api):
    payload, _ = loaded_api.run_prediction({
        'district': 'Anuradhapura', 'season': 'Yala', 'year': 2026,
        'season_total_rainfall': 320.0,
    })
    basis = payload['forecast_basis']
    assert basis['basis'] == 'conditioned'
    assert basis['n_observed_inputs'] >= 1
    assert basis['year_affects_prediction'] is True


def test_year_alone_does_not_change_the_prediction(loaded_api):
    """Documents a real limitation: `year` is not a feature and the default cascade keys on
    (district, season). The banner in the UI depends on this staying true."""
    base = {'district': 'Anuradhapura', 'season': 'Yala'}
    a, _ = loaded_api.run_prediction({**base, 'year': 2019})
    b, _ = loaded_api.run_prediction({**base, 'year': 2040})
    assert a['predicted_yield_MT_per_Ha'] == b['predicted_yield_MT_per_Ha']
    assert a['forecast_basis']['year_affects_prediction'] is False


def test_supplied_weather_actually_moves_the_prediction(loaded_api):
    """If this fails the model is ignoring its inputs and the form is decorative."""
    base = {'district': 'Anuradhapura', 'season': 'Yala', 'year': 2026}
    dry, _ = loaded_api.run_prediction({**base, 'season_total_rainfall': 20.0,
                                        'season_avg_temp': 30.5})
    wet, _ = loaded_api.run_prediction({**base, 'season_total_rainfall': 400.0,
                                        'season_avg_temp': 26.0})
    assert dry['predicted_yield_MT_per_Ha'] != wet['predicted_yield_MT_per_Ha']


def test_feature_resolution_fills_every_feature_and_records_provenance(loaded_api):
    from config import ALL_FEATURES
    values, sources = loaded_api._resolve_features(
        {'district': 'Anuradhapura', 'season': 'Yala', 'year': 2026})
    assert set(values) == set(ALL_FEATURES)
    assert set(sources) == set(ALL_FEATURES)
    assert all(np.isfinite(v) for v in values.values()), 'non-finite feature reached the model'
    assert 'zero_fallback' not in sources.values(), (
        'a feature fell through to the zero fallback; the model is being fed 0.0 for it'
    )


def test_user_supplied_values_win_over_defaults(loaded_api):
    values, sources = loaded_api._resolve_features({
        'district': 'Anuradhapura', 'season': 'Yala', 'year': 2026,
        'season_total_rainfall': 123.456,
    })
    assert values['season_total_rainfall'] == pytest.approx(123.456)
    assert sources['season_total_rainfall'] == 'user'


def test_interaction_terms_are_derived_not_defaulted(loaded_api):
    """Interactions must equal the product of the resolved parents, or the vector is
    internally inconsistent with what the model was trained on."""
    values, sources = loaded_api._resolve_features({
        'district': 'Anuradhapura', 'season': 'Yala', 'year': 2026,
        'season_total_rainfall': 200.0, 'season_mean_ndvi': 0.5,
    })
    assert sources['rainfall_x_ndvi'] == 'derived'
    assert values['rainfall_x_ndvi'] == pytest.approx(
        values['season_total_rainfall'] * values['season_mean_ndvi'])


def test_prediction_interval_brackets_the_point_estimate(loaded_api):
    payload, _ = loaded_api.run_prediction(
        {'district': 'Matale', 'season': 'Yala', 'year': 2026})
    lo = payload['confidence_lower']
    hi = payload['confidence_upper']
    point = payload['predicted_yield_MT_per_Ha']
    assert lo <= point <= hi, f'point {point} outside its own interval [{lo}, {hi}]'
    assert lo >= 0.0, 'negative yield reported as a lower bound'


def test_unknown_district_does_not_crash_or_invent_a_confident_number(loaded_api):
    payload, status = loaded_api.run_prediction(
        {'district': 'Atlantis', 'season': 'Yala', 'year': 2026})
    assert status == 200
    # It must fall back to wider tiers rather than zero-filling into a confident answer.
    assert payload['data_completeness']['n_zero_filled'] == 0

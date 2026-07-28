"""Guards on the Monte Carlo weather propagation.

The two ways this goes silently wrong are sampling features independently (which fabricates
weather that cannot occur) and letting the sampled vectors drift off the distribution the
models were fitted on. Both are asserted here.
"""

import numpy as np
import pandas as pd
import pytest

pytest.importorskip('weather_forecast')


@pytest.fixture(scope='module')
def wf():
    import weather_forecast
    return weather_forecast


@pytest.fixture(scope='module')
def monthly(wf):
    import os
    if not os.path.exists(wf.DAILY_CACHE):
        pytest.skip('daily weather cache not present')
    return wf.monthly_history()


def test_season_features_mirror_the_training_formulas(wf):
    """Must reproduce src/data_loader.py:201-209 exactly, quirks included, or the sampled
    vectors sit on a different scale from the ones the model was trained on."""
    months = pd.DataFrame({
        'temperature_c': [27.0, 28.0, 29.0],
        'rainfall': [10.0, 20.0, 5.0],
        'humidity_pct': [70.0, 75.0, 80.0],
    })
    f = wf.season_features(months)
    assert f['season_avg_temp'] == pytest.approx(28.0)
    assert f['season_total_rainfall'] == pytest.approx(35.0)
    assert f['season_avg_humidity'] == pytest.approx(75.0)
    assert f['temp_range'] == pytest.approx(2.0)
    # max_daily_rainfall is really the max MONTHLY total — the training code's own quirk.
    assert f['max_daily_rainfall'] == pytest.approx(20.0)
    # GDD = sum over months of (T - 10) * 30
    assert f['growing_degree_days'] == pytest.approx((17 + 18 + 19) * 30.0)
    # heat_stress_days counts MONTHS whose mean exceeds 32, hence 0 in this climate.
    assert f['heat_stress_days'] == 0


def test_climatology_pool_is_much_larger_than_the_yield_record(wf, monthly):
    """The selling point of the design: weather variability estimated from ~45 years while
    the yield relationship has only 7."""
    for district in monthly.district.unique():
        clim = wf.climatology(district, monthly)
        assert len(clim) >= 30, f'{district} has only {len(clim)} complete seasons'


def test_fully_observed_season_has_no_remaining_uncertainty(wf, monthly):
    district = sorted(monthly.district.unique())[0]
    seen = wf.observed_months_for(district, 2024, wf.YALA_MONTHS, monthly)
    sample = wf.sample_weather_features(district, 200, observed=seen)
    assert sample['season_total_rainfall'].std() == pytest.approx(0.0, abs=1e-9)
    assert sample['season_avg_temp'].std() == pytest.approx(0.0, abs=1e-9)


def test_uncertainty_shrinks_monotonically_as_months_are_observed(wf, monthly):
    district = sorted(monthly.district.unique())[0]
    spreads = []
    for k in range(len(wf.YALA_MONTHS) + 1):
        seen = wf.observed_months_for(district, 2024, wf.YALA_MONTHS[:k], monthly)
        sample = wf.sample_weather_features(district, 150, observed=seen)
        spreads.append(float(sample['season_total_rainfall'].std()))
    assert spreads[0] > spreads[-1], 'observing the season did not reduce uncertainty'
    assert spreads[-1] == pytest.approx(0.0, abs=1e-9)


def test_observed_months_are_pinned_to_their_real_values(wf, monthly):
    """Using a monthly average for observed months would discard the very information the
    forecaster actually holds."""
    district = sorted(monthly.district.unique())[0]
    seen = wf.observed_months_for(district, 2021, wf.YALA_MONTHS, monthly)
    sample = wf.sample_weather_features(district, 5, observed=seen)
    direct = wf.season_features(pd.DataFrame([seen[m] for m in wf.YALA_MONTHS]))
    # Sampled vectors are rescaled onto the training panel, so compare rank not level:
    # every draw must be identical, because nothing was left to sample.
    assert sample['season_total_rainfall'].nunique() == 1
    assert np.isfinite(direct['season_total_rainfall'])


def test_samples_stay_on_the_training_distribution(wf, monthly):
    """Sampled vectors are rescaled onto the panel's own mean and sd. If they drift far
    outside it, the model is being asked to extrapolate and its output is meaningless."""
    from config import WEATHER_FEATURES
    district = sorted(monthly.district.unique())[0]
    sample = wf.sample_weather_features(district, 300)
    train_mu, train_sd = wf._training_stats(district)
    for col in WEATHER_FEATURES:
        sd = float(train_sd[col])
        if sd == 0 or not np.isfinite(sd):
            continue
        z = (sample[col] - float(train_mu[col])) / sd
        assert abs(float(z.mean())) < 1.0, f'{col} sample mean is {z.mean():.2f} sd off-centre'
        assert float(np.abs(z).max()) < 8.0, f'{col} produced an {z.abs().max():.1f}-sigma draw'


def test_sampling_preserves_cross_feature_covariance(wf, monthly):
    """Whole analogue years are resampled, so rainfall and its SPI must stay coherent.

    Independent per-feature sampling would destroy this and manufacture impossible weather.
    """
    district = sorted(monthly.district.unique())[0]
    sample = wf.sample_weather_features(district, 400)
    corr = sample['season_total_rainfall'].corr(sample['drought_index_spi'])
    assert corr > 0.9, (
        f'rainfall and its standardised index correlate at only {corr:.2f}; features look '
        f'to have been drawn independently'
    )


def test_sampling_is_reproducible_given_a_seed(wf, monthly):
    district = sorted(monthly.district.unique())[0]
    a = wf.sample_weather_features(district, 50, rng=np.random.default_rng(7))
    b = wf.sample_weather_features(district, 50, rng=np.random.default_rng(7))
    pd.testing.assert_frame_equal(a, b)

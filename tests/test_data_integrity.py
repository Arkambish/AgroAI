"""Guards on data provenance.

These encode the integrity findings so they cannot silently regress. The project has twice
shipped results computed against a partly fabricated target; each test here is a tripwire on
one of the ways that happened.
"""

import numpy as np
import pandas as pd


def test_collected_file_still_declares_provenance(collected):
    """The `source` column is what makes filtering possible. Losing it re-opens the hole."""
    assert 'source' in collected.columns
    assert set(collected['source'].unique()) <= {'real', 'synthetic'}


def test_synthetic_rows_never_reach_the_trained_panel(collected, panel):
    """The panel target must match a real-only aggregation, not an all-rows one.

    Before the fix, 26 of 28 cells matched the all-rows aggregation and only 4 matched
    real-only. This asserts the reverse.
    """
    real = collected[collected['source'] == 'real']
    fixes = {'Polannaruwa': 'Polonnaruwa'}
    real = real.assign(district=real['district'].replace(fixes))

    real_only = real.groupby(['district', 'year'])['yield_mt_per_ha'].mean()
    all_rows = (collected.assign(district=collected['district'].replace(fixes))
                .groupby(['district', 'year'])['yield_mt_per_ha'].mean())

    matches_real = matches_all = 0
    for _, row in panel.iterrows():
        cell = (row['District'], row['Year'])
        if cell not in real_only.index:
            continue
        target = float(row['Avg_Yield_MT_per_Ha'])
        matches_real += abs(target - real_only[cell]) < 0.01
        matches_all += cell in all_rows.index and abs(target - all_rows[cell]) < 0.01

    assert matches_real > matches_all, (
        f'panel matches the all-rows aggregation ({matches_all} cells) more closely than the '
        f'real-only one ({matches_real}); synthetic rows are leaking into the target'
    )


def test_panel_has_one_row_per_district_year(panel):
    assert not panel.duplicated(subset=['District', 'Year', 'Season']).any()


def test_target_is_physically_plausible(panel):
    """Onion tops out near 100 t/ha under intensive irrigation; Sri Lanka averages 15-20."""
    y = panel['Avg_Yield_MT_per_Ha']
    assert y.gt(0).all(), 'non-positive yields present'
    assert y.max() < 100, f'implausible yield {y.max()} MT/ha survived the quality filter'


def test_soil_columns_are_constant_within_district(panel):
    """Soil is a district fingerprint, not a time-varying predictor.

    Not a defect to fix — a property to remember. If it ever stops holding, the feature
    means the pipeline computes per district change meaning.
    """
    soil = [c for c in ('soil_ph', 'clay_pct', 'sand_pct') if c in panel.columns]
    for col in soil:
        spread = panel.groupby('District')[col].nunique()
        assert (spread == 1).all(), f'{col} varies within a district'


def test_constant_features_are_known_and_declared():
    """Several 'features' carry no information. Assert the list is exactly what we think.

    If a genuinely varying feature ever collapses to a constant, this catches it; if one of
    these is fixed with real data, this test should be updated to drop it.
    """
    from config import ALL_FEATURES, PROCESSED_DIR
    import os
    frame = pd.read_csv(os.path.join(PROCESSED_DIR, 'integrated_dataset.csv'))
    present = [f for f in ALL_FEATURES if f in frame.columns]
    constant = {f for f in present if frame[f].nunique(dropna=False) == 1}
    known = {'season_avg_solar_rad', 'heat_stress_days', 'organic_carbon',
             'extent_prev_season', 'season_mean_ndwi', 'season_indicator'}
    assert constant <= known, f'new constant feature(s) appeared: {sorted(constant - known)}'


def test_augmentation_does_not_help_honest_scores():
    """Jittered copies cannot create information — only leak it across folds.

    A compressed version of src/integrity_audit.py: augment the TRAINING fold only and
    confirm honest LOYO does not improve. If someone reintroduces augmentation and this
    starts passing trivially, the assertion below will still hold them to a real test fold.
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score
    from config import ALL_FEATURES, PROCESSED_DIR
    import os

    frame = pd.read_csv(os.path.join(PROCESSED_DIR, 'integrated_dataset.csv'))
    feats = [f for f in ALL_FEATURES if f in frame.columns]
    rng = np.random.default_rng(0)

    def loyo(augment_multiple):
        truth, pred = [], []
        for year in sorted(frame.Year.unique()):
            train = frame[frame.Year != year]
            test = frame[frame.Year == year]
            if len(test) < 2:
                continue
            if augment_multiple:
                copies = [train]
                for _ in range(augment_multiple):
                    c = train.copy()
                    for col in feats + ['Avg_Yield_MT_per_Ha']:
                        c[col] = c[col] * (1 + rng.normal(0, 0.05, len(c)))
                    copies.append(c)
                train = pd.concat(copies, ignore_index=True)
            model = RandomForestRegressor(n_estimators=120, random_state=0,
                                          min_samples_leaf=2)
            model.fit(train[feats], train['Avg_Yield_MT_per_Ha'])
            truth += list(test['Avg_Yield_MT_per_Ha'])
            pred += list(model.predict(test[feats]))
        return r2_score(truth, pred)

    assert loyo(5) <= loyo(0) + 1e-9, (
        'training-set augmentation improved honest LOYO R2, which should be impossible; '
        'check that the test folds are genuinely held out'
    )

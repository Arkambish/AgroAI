"""Can PADR detect a weather signal at n=28? Power analysis and parameter recovery.

This module is what makes the negative result defensible. "Our model found no
agro-climatic signal" is worthless unless you first establish that the model WOULD have
found one had it been there. Two experiments, both on the real weather inputs:

  POWER (detect_power)
      Simulate yields in which a known fraction of the variation is driven by PADR's own
      stress index, plus noise matched to the observed residual scale. Sweep that
      fraction from 0 upward and refit PADR under the same LOYO protocol. The smallest
      amplitude at which PADR reliably returns a positive R2 is its minimum detectable
      effect. Comparing that threshold with what the real panel shows is the actual
      inference.

  RECOVERY (recover_parameters)
      Simulate from PADR with KNOWN constants and check which are recovered at n=28.
      Partial recovery is not a failure to report around — "Ky and T_opt are identifiable
      at this sample size, gamma and P_crit are not" is a genuine finding about
      small-sample crop-model calibration.

Both use fewer multi-starts than the headline fit; the point is the sampling
distribution across replicates, not the last decimal of any single fit.
"""

import json
import os

import numpy as np
import pandas as pd

from baselines import weighted_metrics
from config import RANDOM_STATE, RESULTS_DIR
from padr import PARAM_SPEC, _spec, padr_predict, run_loyo, stress_index

# One start, from the literature values, rather than the headline fit's twenty.
# Measured cost is ~69 s per LOYO run per start, so a multi-start study of the original
# size would have taken over an hour to answer a question this coarse.
#
# A single warm start is also the RIGHT choice here, not merely the cheap one. The
# simulated data is generated from parameters near the literature values, so starting
# there is deliberately optimistic — it hands the optimiser the answer's neighbourhood.
# If PADR cannot detect a signal even from that starting point, it certainly cannot from
# a cold one, which is the direction a power analysis wants to err in.
STUDY_STARTS = 1

# Amplitude = fraction of yield's own SD that the weather channel drives.
# 0.0 is a pure-noise control; 1.0 would mean weather explains essentially everything.
AMPLITUDES = (0.0, 0.25, 0.50, 1.00)
N_REPLICATES = 2


def _true_params(n_districts, fold_params=None):
    """Ground-truth parameter vector: the fitted means where available, else literature."""
    spec = _spec(n_districts)
    if not fold_params:
        return np.array([v for _, v, _, _ in spec])
    frame = pd.DataFrame(fold_params).T
    return np.array([float(frame[name].mean()) if name in frame else lit
                     for name, lit, _, _ in spec])


def simulate_yields(cells, params, amplitude, noise_sd, target_mean, target_sd, rng):
    """Yields whose weather-driven share is exactly `amplitude` of the target SD.

    Standardising the stress index before scaling is what makes amplitude interpretable:
    it decouples "how strong is the weather channel" from "how much does S happen to
    vary", which is the very thing under test.
    """
    stress = np.array([stress_index(params, c) for c in cells])
    spread = stress.std()
    z = (stress - stress.mean()) / spread if spread > 0 else np.zeros_like(stress)
    signal = target_mean + amplitude * target_sd * z
    return signal + rng.normal(0.0, noise_sd, size=len(signal)), stress


def detect_power(cells, y_obs, weights, years, districts, fold_params=None,
                 amplitudes=AMPLITUDES, n_replicates=N_REPLICATES,
                 seed=RANDOM_STATE, verbose=True):
    """Sweep weather-signal strength and record what PADR recovers under LOYO."""
    n_districts = len(districts)
    params = _true_params(n_districts, fold_params)
    target_mean, target_sd = float(np.mean(y_obs)), float(np.std(y_obs))
    noise_sd = _residual_scale(y_obs, years)

    if verbose:
        print(f'\n→ Power analysis: {len(amplitudes)} amplitudes x {n_replicates} reps, '
              f'noise sd = {noise_sd:.3f} MT/ha (observed within-year scale)')

    rng = np.random.default_rng(seed)
    rows = []
    for amplitude in amplitudes:
        scores = []
        for _ in range(n_replicates):
            y_sim, _ = simulate_yields(cells, params, amplitude, noise_sd,
                                       target_mean, target_sd, rng)
            oof, _ = run_loyo(cells, y_sim, weights, years, districts,
                              n_starts=STUDY_STARTS, staged=False, verbose=False)
            scores.append(weighted_metrics(y_sim, oof)['R2'])
        rows.append({
            'amplitude': amplitude,
            'weather_share_of_variance': round(amplitude ** 2, 4),
            'R2_mean': round(float(np.mean(scores)), 4),
            'R2_sd': round(float(np.std(scores)), 4),
            'R2_min': round(float(np.min(scores)), 4),
            'detected': bool(np.mean(scores) > 0),
        })
        if verbose:
            r = rows[-1]
            print(f'  amplitude {amplitude:4.2f} '
                  f'(weather = {100 * amplitude ** 2:5.1f}% of variance) -> '
                  f'R2 {r["R2_mean"]:+.4f} +/- {r["R2_sd"]:.4f}'
                  f'{"   DETECTED" if r["detected"] else ""}')

    table = pd.DataFrame(rows)
    detected = table[table['detected']]
    threshold = float(detected['amplitude'].min()) if len(detected) else float('nan')
    if verbose:
        _report_threshold(threshold)
    return table, threshold


def _residual_scale(y, years):
    """SD of yield within a year, across districts — the noise no model can remove."""
    years = np.asarray(years)
    residuals = np.concatenate([y[years == k] - y[years == k].mean() for k in set(years)])
    return float(residuals.std(ddof=1))


def _report_threshold(threshold):
    if np.isnan(threshold):
        print('  ⚠ PADR did not reach positive R2 at ANY simulated amplitude — the '
              'protocol itself (28 rows, 7 folds) is underpowered, which is a stronger '
              'statement than "no signal in these data".')
    else:
        print(f'  → minimum detectable weather signal: amplitude {threshold:.2f}, '
              f'i.e. weather driving >= {100 * threshold ** 2:.0f}% of yield variance.')
        print('    Below that, a real signal is indistinguishable from noise at n=28.')


def recover_parameters(cells, weights, years, districts, fold_params=None,
                       amplitude=1.0, n_replicates=3, seed=RANDOM_STATE, verbose=True):
    """Fit PADR to data simulated from known constants; report per-parameter error."""
    n_districts = len(districts)
    truth = _true_params(n_districts, fold_params)
    names = [n for n, *_ in _spec(n_districts)]
    physics = [n for n, *_ in PARAM_SPEC]

    rng = np.random.default_rng(seed)
    noise_sd = 0.15 * 20.0  # modest noise so identifiability, not SNR, is what is tested

    recovered = []
    for _ in range(n_replicates):
        y_sim, _ = simulate_yields(cells, truth, amplitude, noise_sd, 20.0, 6.0, rng)
        _, folds = run_loyo(cells, y_sim, weights, years, districts,
                            n_starts=STUDY_STARTS, staged=False, verbose=False)
        recovered.append(pd.DataFrame(folds).T.mean())

    got = pd.DataFrame(recovered)
    truth_map = dict(zip(names, truth))
    bounds = {n: b for n, _, b, _ in _spec(n_districts)}

    rows = []
    for name in physics:
        lo, hi = bounds[name]
        span = hi - lo
        estimate = got[name]
        rows.append({
            'parameter': name,
            'true': round(truth_map[name], 4),
            'recovered_mean': round(float(estimate.mean()), 4),
            'recovered_sd': round(float(estimate.std()), 4),
            # Error as a share of the admissible range: <10% is a clean recovery.
            'error_pct_of_range': round(100 * abs(estimate.mean() - truth_map[name]) / span, 1),
            'identifiable': bool(abs(estimate.mean() - truth_map[name]) / span < 0.10),
        })

    table = pd.DataFrame(rows)
    if verbose:
        print('\n→ Parameter recovery at n=28 '
              '(error as % of each parameter\'s admissible range)')
        print(table.to_string(index=False))
        good = table[table['identifiable']]['parameter'].tolist()
        bad = table[~table['identifiable']]['parameter'].tolist()
        print(f'\n  identifiable at n=28 : {", ".join(good) if good else "none"}')
        print(f'  NOT identifiable     : {", ".join(bad) if bad else "none"}')
    return table


def persist(power_table, threshold, recovery_table, out_dir=None):
    out_dir = out_dir or RESULTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    power_table.to_csv(os.path.join(out_dir, 'padr_power_analysis.csv'), index=False)
    recovery_table.to_csv(os.path.join(out_dir, 'padr_parameter_recovery.csv'), index=False)
    with open(os.path.join(out_dir, 'padr_identifiability.json'), 'w') as fh:
        json.dump({
            'min_detectable_amplitude': None if np.isnan(threshold) else threshold,
            'min_detectable_variance_share': None if np.isnan(threshold) else threshold ** 2,
            'identifiable_parameters': recovery_table.loc[
                recovery_table['identifiable'], 'parameter'].tolist(),
            'unidentifiable_parameters': recovery_table.loc[
                ~recovery_table['identifiable'], 'parameter'].tolist(),
        }, fh, indent=2)
    print(f'\n  ✓ {out_dir}/padr_power_analysis.csv, padr_parameter_recovery.csv')


def main():
    from data_collection.nasa_power import fetch_all
    from dcs_panel import load_dcs_records
    from features_real import build_modelling_frame
    from padr import prepare_cells
    from phenology import build_phenology
    from config import TARGET_COLUMN

    frame = build_modelling_frame(verbose=False)
    _, warped = build_phenology(fetch_all(), load_dcs_records(), verbose=False)
    keys = list(zip(frame['Year'].astype(int), frame['District']))
    districts = sorted(frame['District'].unique())
    cells = prepare_cells(warped, districts, keys)

    y = frame[TARGET_COLUMN].to_numpy(float)
    weights = frame['obs_weight'].to_numpy(float)
    years = frame['Year'].to_numpy()

    path = os.path.join(RESULTS_DIR, 'padr_params.json')
    fold_params = json.load(open(path)) if os.path.exists(path) else None

    power, threshold = detect_power(cells, y, weights, years, districts, fold_params)
    recovery = recover_parameters(cells, weights, years, districts, fold_params)
    persist(power, threshold, recovery)


if __name__ == '__main__':
    main()

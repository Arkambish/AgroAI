"""PADR — Phenology-Aligned Differentiable Response model for big onion yield.

A smooth, low-parameter agronomic response model whose crop constants are ESTIMATED
from data under agronomic bounds, applied to daily weather re-indexed onto thermal
phenological time, and fitted by gradient-based optimisation with shrinkage toward
literature values.

    S(d,y) = INTEGRAL_0^1  beta(tau) . f_T(tau) . f_W(tau) . f_WL(tau)  dtau
    yhat   = (Y0 + u_d) . S(d,y)

Seventeen parameters, against 44,929 in the CNN-LSTM this replaces.

The four novelty claims, each independently falsifiable by an arm in src/ablation_padr.py
-----------------------------------------------------------------------------------------
N1  The FAO-33 and thermal constants (Ky, T_base, T_opt, T_crit) are LEARNED end-to-end.
    Shahhosseini et al. 2021 — and this repo's own physics_residual.py — freeze the crop
    model and fit ML on its residual. That is a two-stage hybrid. PADR estimates the
    physics itself, so the fitted constants are the scientific output.

N2  Weather is integrated over THERMAL phenological time, anchored on the DCS-reported
    harvest date, not calendar months. Distributed-lag yield regressions use calendar
    time or fixed stage windows. See src/phenology.py for why the satellite route is
    unavailable on this panel.

N3  An explicit WATERLOGGING penalty, absent from FAO-33, motivated by tropical
    wet-season onion. The growing seasons here average 1043 mm against a 747 mm
    pre-2019 climatology, so excess water binds more often than drought does.

N4  SHRINKAGE-TO-PHYSICS: an L2 penalty pulls every parameter toward its textbook value,
    so a constant only moves when the data demand it. This is the statistical answer to
    calibrating a mechanistic model on 28 observations.

Fitting uses scipy L-BFGS-B with explicit box bounds and multi-start. Seventeen bounded
parameters on a smooth objective is exactly that algorithm's use case; there is no need
for autodiff, and it keeps the model reproducible from a fixed seed.
"""

import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import minimize

from config import RANDOM_STATE

# --------------------------------------------------------------------------- constants

# FAO-56 depletion fraction for onion — shallow-rooted and drought-sensitive.
# Fixed rather than fitted: it trades off almost exactly against W_max, so estimating
# both makes the pair unidentifiable at n=28 (see src/identifiability.py).
DEPLETION_FRACTION = 0.30

# FAO-56 single crop coefficients for onion, as a piecewise-linear curve over tau.
KC_STAGES = [(0.00, 0.70), (0.20, 0.70), (0.45, 1.05), (0.80, 1.05), (1.00, 0.75)]

# Priestley-Taylor coefficient and latent heat of vaporisation (MJ/kg).
PT_ALPHA, LATENT_HEAT = 1.26, 2.45
PSYCHROMETRIC = 0.066  # kPa/degC at ~100 kPa

# Number of B-spline basis functions for beta(tau).
N_BETA = 5

# name, literature value, (lower, upper), prior scale for the shrinkage penalty
PARAM_SPEC = [
    ('T_base',  10.0, (4.0, 14.0),    2.0),    # McMaster & Wilhelm 1997
    ('T_opt',   24.0, (18.0, 30.0),   3.0),    # onion thermal optimum
    ('T_crit',  35.0, (30.0, 42.0),   3.0),    # heat-stress ceiling
    ('Ky',       1.1, (0.5, 1.6),     0.3),    # FAO-33 Doorenbos & Kassam 1979
    ('W_max',  100.0, (30.0, 200.0),  40.0),   # bucket capacity, mm
    ('gamma',  0.005, (0.0, 0.05),    0.01),   # waterlogging severity — N3, no prior
    ('P_crit', 100.0, (20.0, 250.0),  60.0),   # 7-day rainfall threshold — N3, no prior
]
BETA_SPEC = [(f'beta_{i}', 0.0, (-3.0, 3.0), 1.5) for i in range(N_BETA)]
SCALE_SPEC = [('Y0', 20.0, (5.0, 45.0), 10.0)]

PARAM_NAMES = [n for n, *_ in PARAM_SPEC + BETA_SPEC + SCALE_SPEC]
N_CORE = len(PARAM_NAMES)


# ------------------------------------------------------------------------- components


def _kc_curve(tau):
    """FAO-56 crop coefficient over phenological time."""
    points = np.array(KC_STAGES)
    return np.interp(tau, points[:, 0], points[:, 1])


def _beta_basis(tau):
    """Cubic B-spline design matrix for beta(tau), built once per tau grid."""
    interior = np.linspace(0, 1, N_BETA - 2)
    knots = np.concatenate([[0, 0, 0], interior, [1, 1, 1]])
    return BSpline.design_matrix(np.clip(tau, 0, 1 - 1e-9), knots, 3).toarray()


def et0_priestley_taylor(temp_c, solar_mj):
    """Reference evapotranspiration (mm/day) from measured temperature and radiation.

    Radiation-driven rather than temperature-extrapolated, because NASA POWER gives us
    real ALLSKY_SFC_SW_DWN. Net radiation is approximated as 0.6 x incoming shortwave,
    the usual value for a well-watered green canopy.
    """
    slope = (4098 * 0.6108 * np.exp(17.27 * temp_c / (temp_c + 237.3))
             / (temp_c + 237.3) ** 2)
    net = 0.6 * solar_mj
    return np.clip(PT_ALPHA * (slope / (slope + PSYCHROMETRIC)) * net / LATENT_HEAT, 0, None)


def f_thermal(temp_c, t_base, t_opt, t_crit):
    """Trapezoidal thermal response in [0, 1]: 0 below base, 1 at optimum, 0 above critical."""
    rising = (temp_c - t_base) / max(t_opt - t_base, 1e-6)
    falling = (t_crit - temp_c) / max(t_crit - t_opt, 1e-6)
    return np.clip(np.minimum(rising, falling), 0.0, 1.0)


def water_balance(rain_mm, et0_mm, kc, w_max):
    """Single-bucket soil water store, run forward over the tau grid.

    Starts full: Yala planting follows the first inter-monsoon rains, so an empty
    profile at tau=0 would manufacture stress that is not there.
    """
    store = np.empty_like(rain_mm)
    level = w_max
    for i in range(len(rain_mm)):
        level = min(max(level + rain_mm[i] - kc[i] * et0_mm[i], 0.0), w_max)
        store[i] = level
    return store


def f_water(store, w_max, ky):
    """FAO-33 water-stress factor. Yield loss is Ky times the relative water deficit."""
    threshold = max(DEPLETION_FRACTION * w_max, 1e-6)
    deficit = np.clip(1.0 - store / threshold, 0.0, 1.0)
    return np.clip(1.0 - ky * deficit, 0.0, 1.0)


def f_waterlog(rain_7day, gamma, p_crit):
    """Excess-water penalty — novelty N3, no FAO-33 counterpart."""
    return np.clip(1.0 - gamma * np.clip(rain_7day - p_crit, 0.0, None), 0.0, 1.0)


def beta_weights(coefs, basis, dtau):
    """Non-negative phenological sensitivity weights integrating to 1."""
    raw = basis @ np.exp(np.clip(coefs, -20, 20))
    total = raw.sum() * dtau
    return raw / total if total > 0 else np.full(len(raw), 1.0)


# ------------------------------------------------------------------------- prediction


def prepare_cells(warped, districts, keys):
    """Precompute the per-cell arrays that do not depend on fitted parameters.

    `keys` fixes the order to match the panel's rows — never rely on dict ordering to
    line predictions up with targets.
    """
    cells = []
    for key in keys:
        grid = warped[key]
        tau = grid['tau']
        dtau = float(tau[1] - tau[0])
        days = np.maximum(grid['days_per_bin'], 1)

        rain = grid['PRECTOTCORR']
        # Daily-equivalent rates, so ET0 and rainfall are on the same footing per bin.
        rain_rate = rain / days
        et0 = et0_priestley_taylor(grid['T2M'], grid['ALLSKY_SFC_SW_DWN'])

        # Rolling 7-day-equivalent accumulation for the waterlogging term.
        span = max(int(round(7 / max(days.mean(), 1e-6))), 1)
        kernel = np.ones(span)
        rain_7day = np.convolve(rain, kernel, mode='same')

        cells.append({
            'key': key, 'tau': tau, 'dtau': dtau, 'basis': _beta_basis(tau),
            'kc': _kc_curve(tau), 'temp': grid['T2M'], 'tmax': grid['T2M_MAX'],
            'rain': rain_rate, 'et0': et0, 'rain_7day': rain_7day,
            'days': days, 'district_idx': districts.index(key[1]),
        })
    return cells


def stress_index(params, cell):
    """The phenologically weighted stress integral S in [0, 1]."""
    t_base, t_opt, t_crit, ky, w_max, gamma, p_crit = params[:7]
    beta_coefs = params[7:7 + N_BETA]

    thermal = f_thermal(cell['temp'], t_base, t_opt, t_crit)
    store = water_balance(cell['rain'], cell['et0'], cell['kc'], w_max)
    water = f_water(store, w_max, ky)
    waterlog = f_waterlog(cell['rain_7day'], gamma, p_crit)

    beta = beta_weights(beta_coefs, cell['basis'], cell['dtau'])
    return float((beta * thermal * water * waterlog).sum() * cell['dtau'])


def padr_predict(params, cells, n_districts):
    """Predicted yield for every cell."""
    y0 = params[7 + N_BETA]
    offsets = params[N_CORE:N_CORE + n_districts]
    return np.array([(y0 + offsets[c['district_idx']]) * stress_index(params, c) for c in cells])


# ---------------------------------------------------------------------------- fitting


def _spec(n_districts):
    """Full parameter specification including the district offsets."""
    return (PARAM_SPEC + BETA_SPEC + SCALE_SPEC
            + [(f'u_{i}', 0.0, (-12.0, 12.0), 3.0) for i in range(n_districts)])


def padr_objective(params, cells, y, weights, n_districts, spec,
                   lambda_phys=1.0, lambda_rough=1.0, lambda_district=1.0):
    """Weighted squared error plus the three regularisers.

    lambda_phys is N4: without it, 17 parameters on 24 training rows drift to whatever
    fits the noise. With it, a constant only leaves its textbook value when the data pay
    for the move.
    """
    pred = padr_predict(params, cells, n_districts)
    residual = float((weights * (y - pred) ** 2).sum() / weights.sum())

    lit = np.array([v for _, v, _, _ in spec])
    scale = np.array([s for *_, s in spec])
    shrink = float((((params - lit) / scale) ** 2).sum())

    beta_coefs = params[7:7 + N_BETA]
    rough = float((np.diff(beta_coefs, 2) ** 2).sum())

    offsets = params[N_CORE:N_CORE + n_districts]
    district = float((offsets ** 2).sum())

    return (residual + lambda_phys * shrink + lambda_rough * rough
            + lambda_district * district)


DEFAULT_PENALTIES = {'lambda_phys': 1.0, 'lambda_rough': 1.0, 'lambda_district': 1.0}


def _objective_args(cells, y, weights, n_districts, spec, penalties):
    """scipy passes `args` positionally, so the penalties are packed in order."""
    p = {**DEFAULT_PENALTIES, **(penalties or {})}
    return (cells, y, weights, n_districts, spec,
            p['lambda_phys'], p['lambda_rough'], p['lambda_district'])


def build_bounds(spec, freeze_physics=False, pin=None):
    """Box bounds, collapsing any pinned parameter to a single point.

    Pinning is how the ablation arms disable a mechanism: `pin={'gamma': 0.0}` switches
    waterlogging off exactly, and pinning every beta coefficient to 0 makes beta(tau)
    exactly uniform, because cubic B-splines form a partition of unity.
    """
    bounds = []
    for i, (name, lit, box, _) in enumerate(spec):
        if pin and name in pin:
            bounds.append((float(pin[name]), float(pin[name])))
        elif freeze_physics and i < len(PARAM_SPEC):
            bounds.append((lit, lit))
        else:
            bounds.append(box)
    return bounds


def fit_padr(cells, y, weights, n_districts, n_starts=20, seed=RANDOM_STATE,
             freeze_physics=False, penalties=None, pin=None):
    """Multi-start L-BFGS-B fit.

    Staged by default in run_loyo: beta(tau) alone first with the physics frozen at its
    literature values, then everything unfrozen from that warm start. The staging both
    stabilises the fit and gives the N2-only ablation arm for free.
    """
    spec = _spec(n_districts)
    lit = np.array([v for _, v, _, _ in spec])
    bounds = build_bounds(spec, freeze_physics, pin)
    lows = np.array([lo for lo, _ in bounds])
    highs = np.array([hi for _, hi in bounds])

    rng = np.random.default_rng(seed)
    args = _objective_args(cells, y, weights, n_districts, spec, penalties)

    best = None
    for start in range(n_starts):
        x0 = lit.copy() if start == 0 else rng.uniform(lows, highs)
        result = minimize(padr_objective, np.clip(x0, lows, highs), args=args,
                          method='L-BFGS-B', bounds=bounds,
                          options={'maxiter': 500, 'ftol': 1e-10})
        if best is None or result.fun < best.fun:
            best = result
    return best.x, float(best.fun)


def run_loyo(cells, y, weights, years, districts, n_starts=20, staged=True,
             freeze_physics=False, penalties=None, pin=None, verbose=True):
    """Leave-one-year-out predictions, refitting PADR from scratch for each held-out year."""
    n_districts = len(districts)
    years = np.asarray(years)
    names = [n for n, *_ in _spec(n_districts)]
    oof = np.full(len(y), np.nan)
    fold_params = {}

    for held in sorted(set(years)):
        train, test = years != held, years == held
        train_cells = [c for c, keep in zip(cells, train) if keep]
        test_cells = [c for c, keep in zip(cells, test) if keep]

        if staged and not freeze_physics:
            warm, _ = fit_padr(train_cells, y[train], weights[train], n_districts,
                               n_starts=max(n_starts // 2, 4), freeze_physics=True,
                               penalties=penalties, pin=pin)
            params, _ = _refine(warm, train_cells, y[train], weights[train],
                                n_districts, penalties, pin)
        else:
            params, _ = fit_padr(train_cells, y[train], weights[train], n_districts,
                                 n_starts=n_starts, freeze_physics=freeze_physics,
                                 penalties=penalties, pin=pin)

        oof[test] = padr_predict(params, test_cells, n_districts)
        fold_params[int(held)] = dict(zip(names, params))
        if verbose:
            print(f'  fold {held}: RMSE {np.sqrt(np.mean((y[test] - oof[test]) ** 2)):6.3f}')

    return oof, fold_params


def _refine(warm_start, cells, y, weights, n_districts, penalties=None, pin=None):
    """Unfreeze the physics and continue from the beta-only solution."""
    spec = _spec(n_districts)
    result = minimize(padr_objective, warm_start,
                      args=_objective_args(cells, y, weights, n_districts, spec, penalties),
                      method='L-BFGS-B', bounds=build_bounds(spec, pin=pin),
                      options={'maxiter': 800, 'ftol': 1e-10})
    return result.x, float(result.fun)

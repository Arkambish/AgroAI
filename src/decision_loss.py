"""Storage-coupled decision loss and the break-even skill frontier for Big Onion.

The contribution this file implements
-------------------------------------
Every published crop-forecast-value study assumes the cost of being wrong is *exogenous*: a
fixed under/over ratio, so a fixed newsvendor critical fractile tau. For a perishable bulb crop
that assumption is false. Curing-window humidity drives both the yield we are predicting and the
fraction of the harvest that survives ambient storage (tropical onion loses 20-40%). So the cost
of over-procuring is a function of the model's own covariates, and tau moves with the weather.

Paddy cannot pose this question: dry grain keeps at ~95% regardless of growing-season weather,
and Sri Lanka's Guaranteed Price Scheme truncates the downside, pinning it near tau = 0.5. The
coupling term is identically zero for a cereal. That is the answer to "already done in paddy".

From the coupling we get a *design-level* object: the break-even skill frontier rho*(tau), the
minimum forecast-truth correlation at which acting on the forecast beats acting on climatology.
It is computable without a good model, which is why it survives this project's R2 of 0.04.

Honesty note on the mechanism
-----------------------------
Under an ideal, perfectly-calibrated Gaussian predictive distribution the expected pinball loss
scales as sqrt(1 - rho^2) at EVERY tau, so tau would not matter and any rho > 0 would pay. The
tau-dependence is a *finite-sample* effect: acting at an extreme tau requires estimating a far
tail quantile, and with ~63 training points per LOYO fold that estimate is badly noisy, while the
climatological quantile is estimated from the same small sample but without conditioning error.
This script therefore simulates the estimation explicitly rather than using the closed form. If
the effect is not there, the numbers below will say so.

Run:  DATA_VARIANT=real PYTHONPATH=src python src/decision_loss.py   (~75s, Monte Carlo)
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

AUGMENTED_CSV = os.environ.get(
    "AUDIT_CSV", os.path.expanduser("~/Downloads/dataset_D_stat.csv")
)
OUT_DIR = "outputs/results_real"
FEATURES = [
    "temperature_c", "rainfall", "humidity_pct", "evi_i", "ndvi_i",
    "clay_0_5cm", "ph_0_5cm", "sand_0_5cm",
]
TARGET = "yield_mt_per_ha"

# Storage survival band. FAO post-harvest compendium and the tropical curing literature put
# ambient-storage losses for onion at 20-40%, worse at high curing humidity. We never claim a
# point value -- lambda is reported as a band and every result is swept across it.
LAMBDA_BEST, LAMBDA_WORST = 0.90, 0.40
HUMIDITY_REF = 75.0      # below this, curing is clean
HUMIDITY_SPAN = 12.0     # pct points from clean curing to worst-case rot

# Cost primitives, expressed as ratios to farmgate price so no fake LKR precision is implied.
PRICE = 1.0
HOLDING = 0.05           # storage/handling per unit held
SHORTAGE_BASE = 1.20     # cost of being short by one unit, no export ban
BAN_MULTIPLIER = 3.0     # India DGFT export restriction in force -> imports scarce and dear

RNG = np.random.default_rng(0)


def genuine_rows(df):
    integer_soil = (
        (df.clay_0_5cm % 1 == 0) & (df.ph_0_5cm % 1 == 0) & (df.sand_0_5cm % 1 == 0)
    )
    return df[integer_soil].reset_index(drop=True)


def storage_survival(humidity_pct, lambda_best=LAMBDA_BEST, lambda_worst=LAMBDA_WORST):
    """Fraction of harvested bulbs surviving ambient storage, decreasing in curing humidity."""
    stress = np.clip((humidity_pct - HUMIDITY_REF) / HUMIDITY_SPAN, 0.0, 1.0)
    return lambda_best - stress * (lambda_best - lambda_worst)


def critical_fractile(humidity_pct, ban_in_force, **kw):
    """tau = c_u / (c_u + c_o). Depends on humidity -- that is the whole point."""
    survival = storage_survival(humidity_pct, **kw)
    overage = PRICE * (1.0 - survival) + HOLDING
    underage = SHORTAGE_BASE * (BAN_MULTIPLIER if ban_in_force else 1.0)
    return underage / (underage + overage)


def pinball(actual, act, tau):
    diff = actual - act
    return np.where(diff >= 0, tau * diff, (tau - 1.0) * diff)


def honest_loyo(real):
    """Leave-one-year-out predictions on the 74 genuine rows. Returns (truth, pred)."""
    truth, pred = [], []
    for year in sorted(real.year.unique()):
        train, test = real[real.year != year], real[real.year == year]
        if len(test) < 2:
            continue
        model = RandomForestRegressor(
            n_estimators=500, random_state=0, min_samples_leaf=2
        ).fit(train[FEATURES], train[TARGET])
        truth += list(test[TARGET])
        pred += list(model.predict(test[FEATURES]))
    return np.array(truth), np.array(pred)


def decision_skill(rho, tau, pool, n_train=63, n_test=11, n_sim=4000, calibrate=True):
    """Relative decision skill of a forecast of skill `rho` versus climatology, at level `tau`.

    Both acts are estimated from a finite training sample, which is the point: the forecast act
    needs a conditional tail quantile, and that estimate is noisy at small n.

    `calibrate` controls whether the raw forecast is regressed onto the truth on the training
    fold before being used as the act's location. This is not a detail. The project's actual RF
    predictions are OVER-dispersed -- sd(pred)/sd(truth) = 0.407 against rho = 0.258, implying a
    shrink slope of 0.634 -- so an uncalibrated act carries pure noise into the decision. With
    calibration the theoretical loss ratio is sqrt(1 - rho^2), so any rho > 0 pays in the limit
    and the break-even is driven purely by finite-sample error. Reporting both is the honest
    thing to do, because the gap between them is a free improvement the project can actually make.

    `pool` is the empirical target pool, giving the simulation the real right-skewed shape.

    Returns (loss_climatology - loss_forecast) / loss_climatology. Positive = forecast helps.
    """
    sigma = pool.std()
    mu = pool.mean()
    # Reproduce the observed over-dispersion: a raw forecast whose spread exceeds rho * sigma.
    raw_spread = 0.407 / max(rho, 1e-9) if rho > 0 else 1.0
    loss_clim, loss_fc = np.empty(n_sim), np.empty(n_sim)
    for s in range(n_sim):
        truth_tr = RNG.choice(pool, n_train, replace=True)
        truth_te = RNG.choice(pool, n_test, replace=True)

        def make_forecast(y):
            signal = rho * (y - mu)
            noise = RNG.normal(0, sigma * np.sqrt(max(1 - rho ** 2, 0.0)), len(y))
            return mu + (signal + noise) * (raw_spread if not calibrate else 1.0)

        fc_tr, fc_te = make_forecast(truth_tr), make_forecast(truth_te)

        if calibrate:
            # What any sane pipeline does: regress truth on the forecast, in-fold.
            slope, intercept = np.polyfit(fc_tr, truth_tr, 1)
            loc_tr, loc_te = intercept + slope * fc_tr, intercept + slope * fc_te
        else:
            loc_tr, loc_te = fc_tr, fc_te

        # Climatological act: the tau-quantile of the training targets. No conditioning.
        act_clim = np.quantile(truth_tr, tau)
        # Forecast act: the conditional location plus the tau-quantile of in-fold residuals.
        act_fc = loc_te + np.quantile(truth_tr - loc_tr, tau)

        loss_clim[s] = pinball(truth_te, act_clim, tau).mean()
        loss_fc[s] = pinball(truth_te, act_fc, tau).mean()
    return float((loss_clim.mean() - loss_fc.mean()) / loss_clim.mean())


def main():
    real = genuine_rows(pd.read_csv(AUGMENTED_CSV))
    truth, pred = honest_loyo(real)

    attainable_rho = float(np.corrcoef(truth, pred)[0, 1])
    report = {
        "attainable_skill": {
            "loyo_r2": round(float(r2_score(truth, pred)), 3),
            "loyo_correlation_rho": round(attainable_rho, 3),
            "n": int(len(truth)),
        }
    }

    # --- Where does tau actually sit for this crop? ---
    humidity = real.humidity_pct.values
    tau_states = {}
    for ban in (False, True):
        for name, (lb, lw) in {
            "optimistic_storage": (0.95, 0.70),
            "central_storage": (LAMBDA_BEST, LAMBDA_WORST),
            "pessimistic_storage": (0.80, 0.25),
        }.items():
            taus = critical_fractile(humidity, ban, lambda_best=lb, lambda_worst=lw)
            tau_states[f"{'ban' if ban else 'no_ban'}__{name}"] = {
                "tau_min": round(float(taus.min()), 3),
                "tau_median": round(float(np.median(taus)), 3),
                "tau_max": round(float(taus.max()), 3),
            }
    report["critical_fractile_states"] = tau_states

    all_taus = np.concatenate(
        [critical_fractile(humidity, b) for b in (False, True)]
    )
    report["critical_fractile_overall"] = {
        "min": round(float(all_taus.min()), 3),
        "max": round(float(all_taus.max()), 3),
        "spread": round(float(all_taus.max() - all_taus.min()), 3),
    }

    # --- The frontier: does required skill rise with tau? ---
    pool = real[TARGET].values.astype(float)
    report["target_shape"] = {
        "sd": round(float(pool.std()), 2),
        "skew": round(float(pd.Series(pool).skew()), 3),
    }

    tau_grid = [0.50, 0.55, 0.65, 0.75, 0.80, 0.85, 0.90, 0.94]
    rho_grid = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    def break_even_from(row):
        """Smallest rho whose skill turns positive, linearly interpolated on the grid."""
        prev_rho, prev_val = None, None
        for rho in rho_grid:
            val = row[str(rho)]
            if val > 0:
                if prev_rho is None:
                    return 0.0
                if prev_val <= 0:
                    return round(
                        float(prev_rho + (rho - prev_rho) * (-prev_val) / (val - prev_val)), 3
                    )
            prev_rho, prev_val = rho, val
        return None

    for mode, calibrate in (("calibrated", True), ("uncalibrated", False)):
        surface, frontier = {}, {}
        for tau in tau_grid:
            row = {
                str(rho): round(decision_skill(rho, tau, pool, calibrate=calibrate), 4)
                for rho in rho_grid
            }
            surface[str(tau)] = row
            frontier[str(tau)] = break_even_from(row)
        report[f"decision_skill_surface__{mode}"] = surface
        report[f"break_even_frontier_rho_star__{mode}"] = frontier

    cal_frontier = report["break_even_frontier_rho_star__calibrated"]
    required = [v for v in cal_frontier.values() if v is not None]
    report["verdict"] = {
        "attainable_rho": round(attainable_rho, 3),
        "required_rho_range_calibrated": [min(required), max(required)] if required else None,
        "forecast_pays_at_current_skill": bool(
            required and attainable_rho > max(required)
        ),
        "skill_gain_at_current_rho_tau085": round(
            decision_skill(attainable_rho, 0.85, pool, calibrate=True), 4
        ),
        "skill_gain_uncalibrated_at_current_rho_tau085": round(
            decision_skill(attainable_rho, 0.85, pool, calibrate=False), 4
        ),
        "rho_star_rises_with_tau": bool(
            required and cal_frontier["0.94"] is not None
            and cal_frontier["0.55"] is not None
            and cal_frontier["0.94"] > cal_frontier["0.55"]
        ),
    }
    surface = report["decision_skill_surface__calibrated"]
    frontier = cal_frontier

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "decision_loss.json")
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"\n{'=' * 74}\nSTORAGE-COUPLED DECISION LOSS — BREAK-EVEN SKILL FRONTIER\n{'=' * 74}")
    a = report["attainable_skill"]
    print(f"\nAttainable skill (honest LOYO): R2 = {a['loyo_r2']:+.3f}, rho = {a['loyo_correlation_rho']:+.3f}, n = {a['n']}")
    print(f"Target shape: sd = {report['target_shape']['sd']}, skew = {report['target_shape']['skew']}")

    o = report["critical_fractile_overall"]
    print("\nCritical fractile tau moves with curing humidity and export-ban state:")
    print(f"  overall range {o['min']} -> {o['max']}  (spread {o['spread']})")
    for k, v in tau_states.items():
        print(f"    {k:34s} tau median {v['tau_median']:.3f}  [{v['tau_min']:.3f}, {v['tau_max']:.3f}]")

    print("\nRelative decision skill (positive = forecast beats climatology):")
    header = "  tau   " + "".join(f"{r:>8.1f}" for r in rho_grid)
    print(header)
    for tau in tau_grid:
        cells = "".join(f"{surface[str(tau)][str(r)]:>8.3f}" for r in rho_grid)
        print(f"  {tau:<5.2f} {cells}")

    print("\nBreak-even skill frontier rho*(tau):")
    uncal = report["break_even_frontier_rho_star__uncalibrated"]
    print(f"  {'tau':<6} {'calibrated':>12} {'uncalibrated':>14}")
    for tau in tau_grid:
        c, u = frontier[str(tau)], uncal[str(tau)]
        cs = "never pays" if c is None else f"{c:.3f}"
        us = "never pays" if u is None else f"{u:.3f}"
        print(f"  {tau:<6.2f} {cs:>12} {us:>14}")

    v = report["verdict"]
    print("\n--- VERDICT ---")
    print(f"  attainable rho (this project, honest LOYO) : {v['attainable_rho']:.3f}")
    if v["required_rho_range_calibrated"]:
        lo, hi = v["required_rho_range_calibrated"]
        print(f"  required rho* across decision states      : {lo:.3f} - {hi:.3f}")
    print(f"  forecast pays at current skill?           : {v['forecast_pays_at_current_skill']}")
    print(f"  decision-loss reduction at tau=0.85, calibrated   : {v['skill_gain_at_current_rho_tau085']:+.1%}")
    print(f"  ... same forecast left uncalibrated               : {v['skill_gain_uncalibrated_at_current_rho_tau085']:+.1%}")
    print(f"  does rho* RISE with tau (audit's hypothesis)?     : {v['rho_star_rises_with_tau']}")

    print(f"\nWritten to {path}\n")


if __name__ == "__main__":
    main()

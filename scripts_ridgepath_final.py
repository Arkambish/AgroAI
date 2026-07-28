"""
FINAL: Ridge-path ensembling with honest (nested) selection.  Big Onion, 28 rows, LOYO.

Idea (this is the "ensemble-and-selection" strategy, taken seriously):
  * The previous stacking failed because it ESTIMATED weights over 10 heterogeneous base models
    from ~24 noisy points. With n=28 and 63.6% of the variance sitting between years, any weight
    (or hyper-parameter) estimated from the training years is almost pure noise.
  * So: ensemble over a *continuum* with EQUAL weights and estimate nothing. Concretely, average
    the predictions of Ridge along its whole regularisation path (a log-alpha grid) instead of
    picking one alpha. MSE(mean of members) <= mean of member MSEs always, and when the members'
    errors are anti-correlated along the path the average beats every single member -- which is
    what happens here.
  * Two aggregation levels are ensembled as well: the raw district-year panel (24 training rows)
    and the year-aggregated panel (6 training rows, which averages away ~3/4 of the measurement
    noise that is 53.6% of the within-year variance).

Honest protocol:
  L1 outer  7 folds : leave-one-YEAR-out; every one of the 4 rows of the held-out year is unseen.
                      Reported R2 is sklearn r2_score on the pooled 28 out-of-fold predictions.
  L2 inner  6 folds : anything a strategy needs to estimate.
  L3 inner2 5 folds : used ONLY to choose between strategies, so the choice is out-of-sample too.
  Standardisation (mean/sd), the year aggregation, and every ridge coefficient are refitted from
  scratch inside each fold. No full-data statistic is ever touched.

Run: DATA_VARIANT=real PYTHONPATH=src .venv/bin/python scripts_ridgepath_final.py
"""
import json
import warnings
from functools import lru_cache

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

warnings.filterwarnings("ignore")
ROOT = "/Users/arqm7/Documents/FYP/Model"

df = pd.read_csv(f"{ROOT}/data/processed_real/integrated_dataset.csv")
df = df.sort_values(["Year", "District"]).reset_index(drop=True)

import config  # noqa: E402

FEATURES = [f for f in config.ALL_FEATURES if f in df.columns]
assert len(FEATURES) == 32
X_ALL = df[FEATURES].to_numpy(float)
Y_ALL = df["Avg_Yield_MT_per_Ha"].to_numpy(float)
YEAR_ALL = df["Year"].to_numpy()
DIST_ALL = df["District"].to_numpy()
YEARS = tuple(sorted(np.unique(YEAR_ALL).tolist()))

GRIDS = {
    "g1": (-3.0, 3.0, 25),
    "g2": (-2.0, 4.0, 25),
    "g3": (-1.0, 5.0, 25),
    "g4": (-3.0, 5.0, 33),
}
LEVELS = ("district", "year", "both")
STRATS = ["climatology"] + [f"ridgepath_{lv}_{g}" for lv in LEVELS for g in GRIDS]


def _rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


@lru_cache(maxsize=None)
def _path(tr_years, te_year, level, gkey):
    """Equal-weight average of Ridge predictions along the alpha path.
    Standardisation and coefficients fitted on tr_years only."""
    lo, hi, n = GRIDS[gkey]
    alphas = np.logspace(lo, hi, n)
    te = YEAR_ALL == te_year
    if level == "year":
        z = np.array([X_ALL[YEAR_ALL == v].mean(0) for v in tr_years])
        t = np.array([Y_ALL[YEAR_ALL == v].mean() for v in tr_years])
        zt = X_ALL[te].mean(0)[None, :]
    else:
        m = np.isin(YEAR_ALL, list(tr_years))
        z, t, zt = X_ALL[m], Y_ALL[m], X_ALL[te]
    mu, sd = z.mean(0), z.std(0)
    sd[sd < 1e-12] = 1.0
    a, b = (z - mu) / sd, (zt - mu) / sd
    p = np.mean([Ridge(alpha=al).fit(a, t).predict(b) for al in alphas], axis=0)
    p = np.asarray(p).ravel()
    return np.full(int(te.sum()), float(p[0])) if level == "year" else p


def strat(name, tr_years, te_year):
    tr_years = tuple(sorted(tr_years))
    n_te = int((YEAR_ALL == te_year).sum())
    if name == "climatology":
        return np.full(n_te, float(Y_ALL[np.isin(YEAR_ALL, list(tr_years))].mean()))
    _, lv, gk = name.split("_")
    if lv == "both":
        return 0.5 * (_path(tr_years, te_year, "district", gk)
                      + _path(tr_years, te_year, "year", gk))
    return _path(tr_years, te_year, lv, gk)


def loyo(name):
    p = np.zeros(len(Y_ALL))
    for te in YEARS:
        p[YEAR_ALL == te] = strat(name, tuple(v for v in YEARS if v != te), te)
    return r2_score(Y_ALL, p), _rmse(p, Y_ALL), p


def nested_autoselect(pool):
    """Pick the strategy inside every outer fold with an L3 LOYO over the 6 training years."""
    pred = np.zeros(len(Y_ALL))
    picked = {}
    for te in YEARS:
        t6 = tuple(v for v in YEARS if v != te)
        acc = {s: [] for s in pool}
        truth = []
        for hi in t6:
            t5 = tuple(v for v in t6 if v != hi)
            truth.append(Y_ALL[YEAR_ALL == hi])
            for s in pool:
                acc[s].append(strat(s, t5, hi))
        truth = np.concatenate(truth)
        sc = {s: _rmse(np.concatenate(v), truth) for s, v in acc.items()}
        best = min(sc, key=sc.get)
        picked[int(te)] = [best, round(sc[best], 4)]
        pred[YEAR_ALL == te] = strat(best, t6, te)
    return r2_score(Y_ALL, pred), _rmse(pred, Y_ALL), picked, pred


def nested_average(pool):
    """No selection at all: equal-weight average of every strategy in the pool.
    Included because in-fold selection is itself a variance source at n=28."""
    pred = np.zeros(len(Y_ALL))
    for te in YEARS:
        t6 = tuple(v for v in YEARS if v != te)
        pred[YEAR_ALL == te] = np.mean([strat(s, t6, te) for s in pool], axis=0)
    return r2_score(Y_ALL, pred), _rmse(pred, Y_ALL), pred


if __name__ == "__main__":
    fixed = {}
    for s in STRATS:
        r2, rm, _ = loyo(s)
        fixed[s] = [round(r2, 4), round(rm, 4)]

    pool = [s for s in STRATS if s != "climatology"]
    a_r2, a_rm, picks, apred = nested_autoselect(STRATS)
    b_r2, b_rm, bpred = nested_average(pool)
    c_r2, c_rm, cpred = nested_average([s for s in STRATS if s.startswith("ridgepath_both")])

    out = {
        "fixed_strategies": dict(sorted(fixed.items(), key=lambda kv: -kv[1][0])),
        "NESTED_AUTOSELECT_over_13": {"R2": round(a_r2, 4), "RMSE": round(a_rm, 4),
                                      "picks": picks},
        "GRAND_ENSEMBLE_all_12_no_selection": {"R2": round(b_r2, 4), "RMSE": round(b_rm, 4)},
        "ENSEMBLE_both_level_4_grids": {"R2": round(c_r2, 4), "RMSE": round(c_rm, 4)},
    }
    print(json.dumps(out, indent=2))
    with open(f"{ROOT}/outputs/ridgepath_final.json", "w") as f:
        json.dump({**out,
                   "grand_ensemble_predictions": bpred.tolist(),
                   "autoselect_predictions": apred.tolist(),
                   "actual": Y_ALL.tolist(), "year": YEAR_ALL.tolist(),
                   "district": DIST_ALL.tolist()}, f, indent=2)

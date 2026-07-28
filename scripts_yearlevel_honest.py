"""
Year-aggregated ensemble + honest selection, nested LOYO.

Motivation from the variance decomposition supplied with the task: 63.6% of target variance is
BETWEEN YEARS, only 2.2% between districts, and measurement error is 53.6% of the WITHIN-year
variance. So the only learnable signal is the year effect, and the 4 districts of a year are 4
noisy replicates of it. Averaging them before fitting removes ~3/4 of the measurement noise from
both X and y. Everything below therefore fits at the YEAR level (6 training rows per outer fold)
with heavy regularisation, and ensembles over the regularisation strength instead of picking one.

Nesting:
  L1 outer  (7 folds) : reported pooled OOF R2 over 28 rows.
  L2 inner  (6 folds) : alpha selection / blend weights / shrinkage, fitted on training years only.
  L3 inner2 (5 folds) : used only to choose among strategies, so that choice is out-of-sample too.

Run: DATA_VARIANT=real PYTHONPATH=src .venv/bin/python scripts_yearlevel_honest.py
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
TARGET = "Avg_Yield_MT_per_Ha"

df = pd.read_csv(f"{ROOT}/data/processed_real/integrated_dataset.csv")
df = df.sort_values(["Year", "District"]).reset_index(drop=True)

import config  # noqa: E402

FEATURES = [f for f in config.ALL_FEATURES if f in df.columns]
X_ALL = df[FEATURES].to_numpy(float)
Y_ALL = df[TARGET].to_numpy(float)
YEAR_ALL = df["Year"].to_numpy()
DIST_ALL = df["District"].to_numpy()
YEARS = tuple(sorted(np.unique(YEAR_ALL).tolist()))

# standard, not hand-picked: the usual log grid a RidgeCV would be given
ALPHAS = tuple(np.logspace(-2, 4, 13).tolist())


def _rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def _year_mat(years):
    z = np.array([X_ALL[YEAR_ALL == y].mean(0) for y in years])
    t = np.array([Y_ALL[YEAR_ALL == y].mean() for y in years])
    return z, t


@lru_cache(maxsize=None)
def year_ridge_preds(tr_years, te_year):
    """Vector of year-mean predictions for te_year, one per alpha in ALPHAS.
    Standardisation and coefficients fitted on tr_years only."""
    z, t = _year_mat(tr_years)
    zt = X_ALL[YEAR_ALL == te_year].mean(0)[None, :]
    mu, sd = z.mean(0), z.std(0)
    sd[sd < 1e-12] = 1.0
    a, b = (z - mu) / sd, (zt - mu) / sd
    return np.array([float(Ridge(alpha=al).fit(a, t).predict(b)[0]) for al in ALPHAS])


def alpha_oof(tr_years):
    """(n_years, n_alphas) inner-LOYO OOF predictions of the year mean, plus the truth."""
    tr_years = tuple(sorted(tr_years))
    p, t = [], []
    for h in tr_years:
        p.append(year_ridge_preds(tuple(v for v in tr_years if v != h), h))
        t.append(Y_ALL[YEAR_ALL == h].mean())
    return np.array(p), np.array(t)


def js_district_dev(tr_years):
    """James-Stein shrunk district deviations, estimated on tr_years only."""
    m = np.isin(YEAR_ALL, list(tr_years))
    ytr, dtr = Y_ALL[m], DIST_ALL[m]
    mu = ytr.mean()
    ks = np.unique(dtr)
    devs = {k: ytr[dtr == k].mean() - mu for k in ks}
    within = float(np.mean([ytr[dtr == k].var(ddof=1) for k in ks]))
    nbar = float(np.mean([np.sum(dtr == k) for k in ks]))
    tau2 = max(float(np.var(list(devs.values()), ddof=1)) - within / nbar, 0.0)
    den = tau2 + within / nbar
    k = tau2 / den if den > 0 else 0.0
    return {d: k * v for d, v in devs.items()}


# ------------------------------------------------------------------ pre-registered strategies
def strat(name, tr_years, te_year):
    tr_years = tuple(sorted(tr_years))
    mu = float(Y_ALL[np.isin(YEAR_ALL, list(tr_years))].mean())
    n_te = int((YEAR_ALL == te_year).sum())
    if name == "climatology":
        return np.full(n_te, mu)

    p, t = alpha_oof(tr_years)                      # inner-LOYO OOF, training years only
    r = np.array([_rmse(p[:, j], t) for j in range(p.shape[1])])
    q = year_ridge_preds(tr_years, te_year)         # models refit on all training years

    if name == "yr_cv":                             # select alpha on inner OOF
        pred = q[int(np.argmin(r))]
    elif name == "yr_avg":                          # equal-weight ensemble over the alpha grid
        pred = float(q.mean())
    elif name == "yr_invrmse":                      # inverse-inner-RMSE weights over the grid
        w = 1.0 / np.maximum(r, 1e-9) ** 2
        pred = float(q @ (w / w.sum()))
    elif name == "yr_top3":                         # mean of the 3 best alphas on inner OOF
        pred = float(q[np.argsort(r)[:3]].mean())
    elif name == "yr_cv_shrunk":                    # yr_cv, shrinkage lambda also from inner OOF
        j = int(np.argmin(r))
        lam_grid = (0.0, 0.25, 0.5, 0.75, 1.0)
        lam = min(lam_grid, key=lambda L: _rmse(mu + L * (p[:, j] - mu), t))
        pred = mu + lam * (q[j] - mu)
    elif name == "yr_invrmse_shrunk":
        w = 1.0 / np.maximum(r, 1e-9) ** 2
        w = w / w.sum()
        blend_oof = p @ w
        lam_grid = (0.0, 0.25, 0.5, 0.75, 1.0)
        lam = min(lam_grid, key=lambda L: _rmse(mu + L * (blend_oof - mu), t))
        pred = mu + lam * (float(q @ w) - mu)
    else:
        raise ValueError(name)

    out = np.full(n_te, pred)
    if name.endswith("_js"):
        dev = js_district_dev(tr_years)
        out = out + np.array([dev.get(d, 0.0) for d in DIST_ALL[YEAR_ALL == te_year]])
    return out


STRATS = ["climatology", "yr_cv", "yr_avg", "yr_invrmse", "yr_top3",
          "yr_cv_shrunk", "yr_invrmse_shrunk"]


def loyo(name):
    p = np.zeros(len(Y_ALL))
    for te in YEARS:
        p[YEAR_ALL == te] = strat(name, tuple(v for v in YEARS if v != te), te)
    return r2_score(Y_ALL, p), _rmse(p, Y_ALL), p


def nested_autoselect():
    """Choose the strategy inside each outer fold using an L3 leave-one-year-out over the
    6 training years. Nothing about the outer test year is used."""
    pred = np.zeros(len(Y_ALL))
    picked = {}
    for te in YEARS:
        t6 = tuple(v for v in YEARS if v != te)
        acc = {s: [] for s in STRATS}
        truth = []
        for hi in t6:
            t5 = tuple(v for v in t6 if v != hi)
            truth.append(Y_ALL[YEAR_ALL == hi])
            for s in STRATS:
                acc[s].append(strat(s, t5, hi))
        truth = np.concatenate(truth)
        sc = {s: _rmse(np.concatenate(v), truth) for s, v in acc.items()}
        best = min(sc, key=sc.get)
        picked[int(te)] = [best, round(sc[best], 4)]
        pred[YEAR_ALL == te] = strat(best, t6, te)
    return r2_score(Y_ALL, pred), _rmse(pred, Y_ALL), picked, pred


if __name__ == "__main__":
    res = {}
    preds = {}
    for s in STRATS:
        r2, rm, p = loyo(s)
        res[s] = [round(r2, 4), round(rm, 4)]
        preds[s] = p.tolist()
    ar2, arm, picked, apred = nested_autoselect()
    res["NESTED_AUTOSELECT"] = [round(ar2, 4), round(arm, 4)]
    out = {"fixed_strategies_loyo_R2_RMSE": res,
           "nested_autoselect_picks": picked,
           "alphas": [round(a, 4) for a in ALPHAS],
           "predictions": preds,
           "nested_autoselect_predictions": apred.tolist(),
           "actual": Y_ALL.tolist(), "year": YEAR_ALL.tolist(),
           "district": DIST_ALL.tolist()}
    print(json.dumps({k: v for k, v in out.items() if k != "predictions"}, indent=2))
    with open(f"{ROOT}/outputs/yearlevel_honest.json", "w") as f:
        json.dump(out, f, indent=2)

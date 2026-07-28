"""
Honest ensemble-and-selection study for the Big Onion LOYO problem.

Protocol -- three nested levels of leave-one-YEAR-out:
  L1 (outer, 7 folds) : the reported number. Pooled OOF R2 over all 28 rows.
  L2 (inner, 6 folds) : produces OOF predictions of the BASE models on the outer-training
                        years. These are the ONLY data a meta-strategy may use to choose its
                        members, fit its blend weights and fit its shrinkage coefficient.
  L3 (inner-inner, 5) : used ONLY to score the meta-strategies against each other, so the
                        choice of meta-strategy is itself made out-of-sample.

Every imputer, scaler, feature ranking, model, blend weight and shrinkage coefficient is fitted
strictly on the years available at its own level. The outer test year is never touched.

Run: DATA_VARIANT=real PYTHONPATH=src .venv/bin/python scripts_ensemble_honest.py
"""
import json
import warnings
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.optimize import nnls
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.metrics import r2_score
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR

warnings.filterwarnings("ignore")
RNG = 0
ROOT = "/Users/arqm7/Documents/FYP/Model"
TARGET = "Avg_Yield_MT_per_Ha"

df = pd.read_csv(f"{ROOT}/data/processed_real/integrated_dataset.csv")
df = df.sort_values(["Year", "District"]).reset_index(drop=True)

import config  # noqa: E402

FEATURES = [f for f in config.ALL_FEATURES if f in df.columns]
assert len(FEATURES) == 32, len(FEATURES)

X_ALL = df[FEATURES].to_numpy(float)
Y_ALL = df[TARGET].to_numpy(float)
YEAR_ALL = df["Year"].to_numpy()
DIST_ALL = df["District"].to_numpy()
YEARS = tuple(sorted(np.unique(YEAR_ALL).tolist()))
PREV_IDX = FEATURES.index("prev_year_yield")
Y3_IDX = FEATURES.index("yield_3yr_avg")


# --------------------------------------------------------------------------------- helpers
def _prep(a, b):
    """median-impute + standardise; both statistics fitted on `a` (training rows) only."""
    med = np.nanmedian(a, axis=0)
    a = np.where(np.isnan(a), med, a)
    b = np.where(np.isnan(b), med, b)
    mu, sd = a.mean(0), a.std(0)
    sd[sd < 1e-12] = 1.0
    return (a - mu) / sd, (b - mu) / sd


def _rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


# --------------------------------------------------------------------------- base models
# Signature: f(tr_years: tuple, te_year: int) -> np.ndarray of length 4
def _rows(years):
    return np.isin(YEAR_ALL, list(years))


def b_clim(tr, te):
    return np.full(4, Y_ALL[_rows(tr)].mean())


def b_district(tr, te):
    m, d, y = _rows(tr), DIST_ALL, Y_ALL
    g = {k: y[m & (d == k)].mean() for k in np.unique(d[m])}
    gm = y[m].mean()
    return np.array([g.get(k, gm) for k in d[YEAR_ALL == te]])


def b_js_district(tr, te):
    """Train mean + James-Stein shrunk district deviations (shrinkage estimated in-fold)."""
    m = _rows(tr)
    ytr, dtr = Y_ALL[m], DIST_ALL[m]
    mu = ytr.mean()
    ks = np.unique(dtr)
    devs = {k: ytr[dtr == k].mean() - mu for k in ks}
    within = float(np.mean([ytr[dtr == k].var(ddof=1) for k in ks]))
    nbar = float(np.mean([np.sum(dtr == k) for k in ks]))
    between = float(np.var(list(devs.values()), ddof=1))
    tau2 = max(between - within / nbar, 0.0)
    denom = tau2 + within / nbar
    shrink = tau2 / denom if denom > 0 else 0.0
    return np.array([mu + shrink * devs.get(k, 0.0) for k in DIST_ALL[YEAR_ALL == te]])


def b_persist(tr, te):
    return X_ALL[YEAR_ALL == te, PREV_IDX]


def b_y3(tr, te):
    return X_ALL[YEAR_ALL == te, Y3_IDX]


def _sk(make):
    def f(tr, te):
        m, t = _rows(tr), YEAR_ALL == te
        a, b = _prep(X_ALL[m], X_ALL[t])
        e = make()
        e.fit(a, Y_ALL[m])
        return np.asarray(e.predict(b)).ravel()

    return f


def b_uni(tr, te):
    """OLS on the one feature most correlated with y among the TRAINING years."""
    m, t = _rows(tr), YEAR_ALL == te
    a, b = _prep(X_ALL[m], X_ALL[t])
    ytr = Y_ALL[m]
    c = np.nan_to_num([abs(np.corrcoef(a[:, j], ytr)[0, 1]) if a[:, j].std() > 0 else 0.0
                       for j in range(a.shape[1])])
    j = int(np.argmax(c))
    coef = np.polyfit(a[:, j], ytr, 1)
    return np.polyval(coef, b[:, j])


def b_pcr1(tr, te):
    m, t = _rows(tr), YEAR_ALL == te
    a, b = _prep(X_ALL[m], X_ALL[t])
    p = PCA(n_components=1, random_state=RNG).fit(a)
    lr = LinearRegression().fit(p.transform(a), Y_ALL[m])
    return lr.predict(p.transform(b)).ravel()


def _year_level(tr):
    """Year-aggregated design matrix and year-mean yields for the training years."""
    z = np.array([X_ALL[YEAR_ALL == y].mean(0) for y in tr])
    t = np.array([Y_ALL[YEAR_ALL == y].mean() for y in tr])
    return z, t


def b_year_uni(tr, te):
    """Predict the YEAR mean from the single best year-level feature; same value for all
    4 districts. Feature chosen from training years only."""
    z, t = _year_level(tr)
    zt = X_ALL[YEAR_ALL == te].mean(0)[None, :]
    a, b = _prep(z, zt)
    c = np.nan_to_num([abs(np.corrcoef(a[:, j], t)[0, 1]) if a[:, j].std() > 0 else 0.0
                       for j in range(a.shape[1])])
    j = int(np.argmax(c))
    coef = np.polyfit(a[:, j], t, 1)
    return np.full(4, float(np.polyval(coef, b[0, j])))


def b_year_ridge(tr, te):
    z, t = _year_level(tr)
    zt = X_ALL[YEAR_ALL == te].mean(0)[None, :]
    a, b = _prep(z, zt)
    e = Ridge(alpha=100.0).fit(a, t)
    return np.full(4, float(e.predict(b)[0]))


def b_year_uni_plus_js(tr, te):
    """Year-level signal for the year effect + in-fold shrunk district deviation."""
    return b_year_uni(tr, te) + (b_js_district(tr, te) - Y_ALL[_rows(tr)].mean())


BASE = {
    "clim": b_clim,
    "district": b_district,
    "js_district": b_js_district,
    "persist": b_persist,
    "y3avg": b_y3,
    "ridge100": _sk(lambda: Ridge(alpha=100.0)),
    "ridge1000": _sk(lambda: Ridge(alpha=1000.0)),
    "lasso1": _sk(lambda: Lasso(alpha=1.0, max_iter=50000)),
    "lasso3": _sk(lambda: Lasso(alpha=3.0, max_iter=50000)),
    "enet": _sk(lambda: ElasticNet(alpha=1.0, l1_ratio=0.5, max_iter=50000)),
    "pls1": _sk(lambda: PLSRegression(n_components=1)),
    "pls2": _sk(lambda: PLSRegression(n_components=2)),
    "pcr1": b_pcr1,
    "knn5": _sk(lambda: KNeighborsRegressor(n_neighbors=5)),
    "svr": _sk(lambda: SVR(kernel="rbf", C=10.0, gamma="scale", epsilon=0.1)),
    "rf": _sk(lambda: RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                                            random_state=RNG, n_jobs=1)),
    "gbm": _sk(lambda: GradientBoostingRegressor(n_estimators=150, max_depth=2,
                                                 learning_rate=0.05, random_state=RNG)),
    "uni": b_uni,
    "year_uni": b_year_uni,
    "year_ridge": b_year_ridge,
    "year_uni_js": b_year_uni_plus_js,
}
MNAMES = list(BASE)


@lru_cache(maxsize=None)
def base_preds(tr_years, te_year):
    """(4, M) base-model predictions for te_year, every model fitted ONLY on tr_years."""
    return np.column_stack([BASE[n](tr_years, te_year) for n in MNAMES])


def oof_matrix(years):
    """Leave-one-year-out OOF base predictions strictly within the year set `years`."""
    years = tuple(sorted(years))
    p, y = [], []
    for h in years:
        p.append(base_preds(tuple(v for v in years if v != h), h))
        y.append(Y_ALL[YEAR_ALL == h])
    return np.vstack(p), np.concatenate(y)


# --------------------------------------------------------------------------- meta strategies
def _weights(p, y, kind, topk):
    r = np.array([_rmse(p[:, j], y) for j in range(p.shape[1])])
    sel = np.argsort(r)[:topk]
    w = np.zeros(p.shape[1])
    if kind == "avg":
        w[sel] = 1.0 / len(sel)
    elif kind == "invrmse":
        v = 1.0 / np.maximum(r[sel], 1e-9)
        w[sel] = v / v.sum()
    elif kind == "nnls":
        coef, _ = nnls(p[:, sel], y)
        if coef.sum() <= 1e-9:
            coef = np.full(len(sel), 1.0 / len(sel))
        w[sel] = coef / coef.sum()
    return w


LAMBDAS = (1.0, 0.75, 0.5, 0.35, 0.25, 0.15, 0.1, 0.05)
STRATS = [("climatology", None)]
for _kind in ("avg", "invrmse", "nnls"):
    for _k in (1, 2, 3, 5, 8):
        if _kind != "avg" and _k == 1:
            continue
        for _lam in LAMBDAS:
            STRATS.append((f"{_kind}{_k}_shrink{_lam}", (_kind, _k, _lam)))
SMAP = dict(STRATS)
SNAMES = [s for s, _ in STRATS]


def apply_strategy(spec, tr_years, te_year):
    """Fit the strategy on tr_years (weights come from an inner LOYO inside tr_years) and
    predict te_year."""
    mu = float(Y_ALL[_rows(tr_years)].mean())
    if spec is None:
        return np.full(4, mu)
    kind, topk, lam = spec
    p, y = oof_matrix(tr_years)
    w = _weights(p, y, kind, topk)
    raw = base_preds(tuple(sorted(tr_years)), te_year) @ w
    return mu + lam * (raw - mu)


# --------------------------------------------------------------------------------- run
def run():
    pfull, yfull = oof_matrix(YEARS)
    base_scores = {n: (r2_score(yfull, pfull[:, j]), _rmse(pfull[:, j], yfull))
                   for j, n in enumerate(MNAMES)}

    strat_oof = {n: np.zeros(len(Y_ALL)) for n in SNAMES}
    for yt in YEARS:
        tr = tuple(v for v in YEARS if v != yt)
        m = YEAR_ALL == yt
        for name, spec in STRATS:
            strat_oof[name][m] = apply_strategy(spec, tr, yt)
    strat_scores = {n: (r2_score(Y_ALL, p), _rmse(p, Y_ALL)) for n, p in strat_oof.items()}

    # fully nested: the meta-strategy itself is chosen by L3 inside each outer fold
    auto = np.zeros(len(Y_ALL))
    picked = {}
    for yt in YEARS:
        t6 = tuple(v for v in YEARS if v != yt)
        acc = {n: [] for n in SNAMES}
        truth = []
        for yi in t6:
            t5 = tuple(v for v in t6 if v != yi)
            truth.append(Y_ALL[YEAR_ALL == yi])
            for name, spec in STRATS:
                acc[name].append(apply_strategy(spec, t5, yi))
        truth = np.concatenate(truth)
        sc = {n: _rmse(np.concatenate(v), truth) for n, v in acc.items()}
        best = min(sc, key=sc.get)
        picked[int(yt)] = [best, round(sc[best], 4)]
        auto[YEAR_ALL == yt] = apply_strategy(SMAP[best], t6, yt)
    auto_r2, auto_rmse = r2_score(Y_ALL, auto), _rmse(auto, Y_ALL)

    out = {
        "base_models_loyo": {k: [round(a, 4), round(b, 4)] for k, (a, b) in
                             sorted(base_scores.items(), key=lambda kv: -kv[1][0])},
        "top_fixed_strategies_loyo": {k: [round(a, 4), round(b, 4)] for k, (a, b) in
                                      sorted(strat_scores.items(), key=lambda kv: -kv[1][0])[:15]},
        "worst_fixed_strategy": min(strat_scores.items(), key=lambda kv: kv[1][0])[0],
        "nested_autoselect": {"R2": round(auto_r2, 4), "RMSE": round(auto_rmse, 4),
                              "picked_per_fold": picked},
        "n_base_models": len(MNAMES),
        "n_strategies": len(STRATS),
        "n_configurations": len(MNAMES) + len(STRATS),
    }
    print(json.dumps(out, indent=2, default=str))
    with open(f"{ROOT}/outputs/ensemble_honest.json", "w") as f:
        json.dump({**out,
                   "all_fixed_strategies": {k: [round(a, 4), round(b, 4)]
                                            for k, (a, b) in strat_scores.items()},
                   "auto_predictions": auto.tolist(), "actual": Y_ALL.tolist(),
                   "year": YEAR_ALL.tolist(), "district": DIST_ALL.tolist()},
                  f, indent=2, default=str)
    return out


if __name__ == "__main__":
    run()

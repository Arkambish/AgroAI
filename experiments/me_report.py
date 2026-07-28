"""
Self-contained, single-file reproduction of the measurement-error LOYO experiment.

    DATA_VARIANT=real PYTHONPATH=src .venv/bin/python experiments/me_report.py

WHAT IS BEING EXPLOITED
-----------------------
The target Avg_Yield_MT_per_Ha of cell (district, year) is -- verified numerically
against the raw DCS month-records -- the UNWEIGHTED MEAN of that cell's monthly
implied yields production_m / extent_m. Two consequences:

  1. If monthly production behaves like a count, var(yield_i) = phi / E_i with the
     harmonic EFFECTIVE EXTENT  E_i = n_i^2 / sum_m (1/extent_m).
  2. Better still, the measurement variance is DIRECTLY estimable with no model at
     all, from the cell's own month-to-month scatter:  se_i^2 = s_i^2 / n_i.

Both are functions of extents and month counts of TRAINING rows only.

PROTOCOL
--------
Outer leave-one-year-out over 2019..2025; all 4 rows of the held-out year are
removed. Every scaler, feature ranking, variance-component estimate, weight vector,
target transform and hyper-parameter is fitted inside the 24 training rows. The
reported configuration is re-selected by a NESTED inner LOYO on the 6 training years
in every outer fold, so no test year influences which model is used. Reported R2 is
sklearn.metrics.r2_score on the pooled 28 out-of-fold predictions, UNWEIGHTED --
identical to how the published baselines were computed. The harness reproduces the
published climatology baseline exactly (-0.2150 / 6.733), which is the check that it
is scoring the same way.
"""
import json, os, sys
import numpy as np, pandas as pd
from sklearn.metrics import r2_score, mean_squared_error

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
from config import ALL_FEATURES, TARGET_COLUMN            # noqa: E402
from dcs_panel import load_dcs_records                     # noqa: E402

META = ['Year', 'District', 'extent_ha', 'eff_extent', 'n_months', 'se2_raw']


# ------------------------------------------------------------------------ data
def load_panel():
    df = pd.read_csv(os.path.join(ROOT, 'data/processed_real/integrated_dataset.csv'))
    raw = load_dcs_records()
    raw = raw[(raw.Season == 'Yala') & (~raw.impossible) & (raw.extent_ha > 0)]
    rows = []
    for (yr, d), g in raw.groupby(['year', 'District']):
        ext = g['extent_ha'].astype(float).values
        v = g['implied_mt_per_ha'].astype(float).values
        n = len(ext)
        rows.append({'Year': int(yr), 'District': d, 'extent_ha': ext.sum(), 'n_months': n,
                     'eff_extent': n ** 2 / np.sum(1.0 / ext),
                     'se2_raw': float(np.var(v, ddof=1) / n) if n > 1 else np.nan})
    df = df.merge(pd.DataFrame(rows), on=['Year', 'District'], how='left', validate='one_to_one')
    assert df['eff_extent'].notna().all()
    return df.sort_values(['Year', 'District']).reset_index(drop=True)


def weights_from(eff, scheme):
    e = np.asarray(eff, float)
    if scheme == 'equal':   w = np.ones_like(e)
    elif scheme == 'sqrt':  w = np.sqrt(e)
    elif scheme == 'lin':   w = e.copy()
    elif scheme == 'log':   w = np.log1p(e)
    elif scheme.startswith('sat'):
        k = float(scheme[3:]); w = e / (e + k)
    else: raise ValueError(scheme)
    w = np.clip(w, 1e-9, None)
    return w * (len(w) / w.sum())


def _wmean(y, w):
    return float(np.sum(w * y) / np.sum(w))


def _se2(meta):
    s = meta['se2_raw'].values.astype(float)
    k = np.isfinite(s)
    return np.where(k, s, np.median(s[k])) if k.any() else np.ones_like(s)


# ---------------------------------------------------------------------- models
class GrandMean:
    def __init__(s, ws='equal'): s.ws = ws
    def fit(s, X, y, m):
        s.mu_ = _wmean(y, weights_from(m['eff_extent'].values, s.ws)); return s
    def predict(s, X, m): return np.full(len(m), s.mu_)


class RawExtentMean:
    """w ~ extent_ha**p on the raw seasonal extent (repo OBS_WEIGHT_MODE convention)."""
    def __init__(s, p=0.5): s.p = p
    def fit(s, X, y, m):
        w = np.clip(m['extent_ha'].values.astype(float), 0, None) ** s.p
        s.mu_ = _wmean(y, w / w.mean()); return s
    def predict(s, X, m): return np.full(len(m), s.mu_)


class MEWeightedMean:
    """Exact inverse-variance mean using the DIRECT month-level measurement error.
    tau^2 (real signal variance) by method of moments, training rows only."""
    def __init__(s, power=1.0, tau_mode='mom'): s.power, s.tau_mode = power, tau_mode
    def _w(s, y, m):
        se2 = _se2(m)
        tau2 = max(float(np.var(y, ddof=1) - np.mean(se2)), 0.0) if s.tau_mode == 'mom' else 0.0
        w = (1.0 / (tau2 + se2)) ** s.power
        return w / w.mean()
    def fit(s, X, y, m): s.mu_ = _wmean(y, s._w(y, m)); return s
    def predict(s, X, m): return np.full(len(m), s.mu_)


class WGeoMean:
    def __init__(s, ws='sqrt', smear=True): s.ws, s.smear = ws, smear
    def fit(s, X, y, m):
        w = weights_from(m['eff_extent'].values, s.ws); lm = _wmean(np.log(y), w)
        sm = float(np.sum(w * np.exp(np.log(y) - lm)) / np.sum(w)) if s.smear else 1.0
        s.mu_ = np.exp(lm) * sm; return s
    def predict(s, X, m): return np.full(len(m), s.mu_)


class WHuber:
    def __init__(s, ws='sqrt', c=1.345): s.ws, s.c = ws, c
    def fit(s, X, y, m):
        w = weights_from(m['eff_extent'].values, s.ws)
        mu = _wmean(y, w); sc = 1.4826 * np.median(np.abs(y - np.median(y))) + 1e-9
        for _ in range(300):
            nw = mu + sc * np.sum(w * np.clip((y - mu) / sc, -s.c, s.c)) / np.sum(w)
            if abs(nw - mu) < 1e-10: mu = nw; break
            mu = nw
        s.mu_ = mu; return s
    def predict(s, X, m): return np.full(len(m), s.mu_)


class EBDistrict:
    """Empirical-Bayes district effects shrunk by their own measurement precision."""
    def __init__(s, ws='lin', phi_scale=1.0): s.ws, s.ps = ws, phi_scale
    def fit(s, X, y, m):
        e = m['eff_extent'].values.astype(float); d = m['District'].values
        w = weights_from(e, s.ws); s.mu_ = _wmean(y, w)
        num = den = 0.0
        for dd in np.unique(d):
            k = d == dd
            if k.sum() < 2: continue
            num += np.sum(((y[k] - _wmean(y[k], w[k])) ** 2) * e[k]); den += k.sum() - 1
        phi = s.ps * (num / den if den > 0 else np.var(y) * np.mean(e))
        raw, prec = {}, {}
        for dd in np.unique(d):
            k = d == dd; raw[dd] = _wmean(y[k], w[k])
            ww = w[k] / w[k].sum(); prec[dd] = float(np.sum((ww ** 2) * phi / e[k]))
        tau2 = max((np.var(list(raw.values()), ddof=1) if len(raw) > 1 else 0.) - np.mean(list(prec.values())), 0.)
        s.b_ = {dd: (tau2 / (tau2 + prec[dd]) if tau2 + prec[dd] > 0 else 0.) * (raw[dd] - s.mu_) for dd in raw}
        return s
    def predict(s, X, m):
        return np.array([s.mu_ + s.b_.get(dd, 0.) for dd in m['District'].values])


class PartialPool:
    def __init__(s, ws='sqrt', lam=0.3): s.ws, s.lam = ws, lam
    def fit(s, X, y, m):
        w = weights_from(m['eff_extent'].values, s.ws); s.mu_ = _wmean(y, w)
        d = m['District'].values
        s.b_ = {dd: _wmean(y[d == dd], w[d == dd]) - s.mu_ for dd in np.unique(d)}; return s
    def predict(s, X, m):
        return np.array([s.mu_ + s.lam * s.b_.get(dd, 0.) for dd in m['District'].values])


class WRidge:
    """GLS ridge: weights, standardisation, feature ranking all fitted in-fold."""
    def __init__(s, ws='lin', k=3, lam=10., log_target=False, me_weight=False):
        s.ws, s.k, s.lam, s.lg, s.me = ws, k, lam, log_target, me_weight
    def _weights(s, y, m):
        if s.me:
            se2 = _se2(m); tau2 = max(float(np.var(y, ddof=1) - np.mean(se2)), 0.)
            w = 1. / (tau2 + se2); return w / w.mean()
        return weights_from(m['eff_extent'].values, s.ws)
    def fit(s, X, y, m):
        w = s._weights(y, m); Xa = X[ALL_FEATURES].values.astype(float)
        t = np.log(y) if s.lg else y.copy(); sw = np.sqrt(w)
        s.mx_ = np.average(Xa, 0, weights=w)
        s.sx_ = np.sqrt(np.average((Xa - s.mx_) ** 2, 0, weights=w)); s.sx_[s.sx_ < 1e-12] = 1.
        Z = (Xa - s.mx_) / s.sx_
        s.mt_ = _wmean(t, w); tc = t - s.mt_
        den = np.sqrt(np.average(tc ** 2, weights=w))
        c = np.abs((sw[:, None] * Z).T @ (sw * tc)) / np.sum(w) / max(den, 1e-12)
        s.idx_ = np.argsort(-c)[:s.k]
        A = sw[:, None] * Z[:, s.idx_]; b = sw * tc
        s.co_ = np.linalg.solve(A.T @ A + s.lam * np.eye(s.k), A.T @ b)
        if s.lg:
            r = tc - Z[:, s.idx_] @ s.co_
            s.sm_ = float(np.sum(w * np.exp(r)) / np.sum(w))
        return s
    def predict(s, X, m):
        Z = (X[ALL_FEATURES].values.astype(float) - s.mx_) / s.sx_
        p = s.mt_ + Z[:, s.idx_] @ s.co_
        return np.exp(p) * s.sm_ if s.lg else p


class GammaOffset:
    """log E[production] = log(extent) + b0 + z'b  -- models the ratio without dividing."""
    def __init__(s, k=2, lam=10., pw=True): s.k, s.lam, s.pw = k, lam, pw
    def fit(s, X, y, m):
        ext = m['extent_ha'].values.astype(float); prod = y * ext
        pw = m['n_months'].values.astype(float) if s.pw else np.ones(len(y))
        Xa = X[ALL_FEATURES].values.astype(float)
        s.mx_, s.sx_ = Xa.mean(0), Xa.std(0); s.sx_[s.sx_ < 1e-12] = 1.
        Z = (Xa - s.mx_) / s.sx_
        c = np.nan_to_num(np.abs(np.corrcoef(np.column_stack([Z, np.log(y)]), rowvar=False)[-1, :-1]))
        s.idx_ = np.argsort(-c)[:s.k]
        Zs = np.column_stack([np.ones(len(y)), Z[:, s.idx_]])
        beta = np.zeros(Zs.shape[1]); beta[0] = np.log(np.average(y, weights=pw))
        off = np.log(ext); P = s.lam * np.eye(Zs.shape[1]); P[0, 0] = 0.
        for _ in range(80):
            mu = np.exp(np.clip(off + Zs @ beta, -20, 20))
            z = Zs @ beta + (prod - mu) / np.maximum(mu, 1e-9)
            A = Zs * pw[:, None]
            new = np.linalg.solve(Zs.T @ A + P, A.T @ z)
            if np.max(np.abs(new - beta)) < 1e-9: beta = new; break
            beta = new
        s.b_ = beta; return s
    def predict(s, X, m):
        Z = (X[ALL_FEATURES].values.astype(float) - s.mx_) / s.sx_
        return np.exp(np.clip(np.column_stack([np.ones(len(Z)), Z[:, s.idx_]]) @ s.b_, -20, 20))


class FERidge:
    """Within-training-year fixed effects: strip the between-year variance LOYO cannot
    reward, fit the district-year deviation, add back the training grand mean."""
    def __init__(s, ws='sqrt', k=3, lam=30., shrink=1., use_test_mean=False):
        s.ws, s.k, s.lam, s.sh, s.tm = ws, k, lam, shrink, use_test_mean
    def fit(s, X, y, m):
        w = weights_from(m['eff_extent'].values, s.ws); yrs = m['Year'].values
        Xa = X[ALL_FEATURES].values.astype(float)
        yd = np.empty_like(y); Xd = np.empty_like(Xa); xbs = []
        for u in np.unique(yrs):
            k = yrs == u
            yd[k] = y[k] - _wmean(y[k], w[k])
            xb = np.average(Xa[k], 0, weights=w[k]); xbs.append(xb); Xd[k] = Xa[k] - xb
        s.gm_ = _wmean(y, w); s.xc_ = np.mean(xbs, 0)
        s.sd_ = np.sqrt(np.average(Xd ** 2, 0, weights=w)); s.sd_[s.sd_ < 1e-12] = 1.
        Z = Xd / s.sd_; sw = np.sqrt(w)
        den = np.sqrt(np.average(yd ** 2, weights=w))
        c = np.abs((sw[:, None] * Z).T @ (sw * yd)) / np.sum(w) / max(den, 1e-12)
        s.idx_ = np.argsort(-c)[:s.k]
        A = sw[:, None] * Z[:, s.idx_]
        s.co_ = np.linalg.solve(A.T @ A + s.lam * np.eye(s.k), A.T @ (sw * yd)); return s
    def predict(s, X, m):
        Xa = X[ALL_FEATURES].values.astype(float)
        # use_test_mean centres on the held-out rows' own PREDICTOR mean (never y)
        Z = ((Xa - Xa.mean(0)) if s.tm else (Xa - s.xc_)) / s.sd_
        return s.gm_ + s.sh * (Z[:, s.idx_] @ s.co_)


class Trimmed:
    """Drop the q noisiest training cells (smallest effective extent)."""
    def __init__(s, base, q=2): s.base, s.q = base, q
    def fit(s, X, y, m):
        o = np.argsort(m['eff_extent'].values)
        k = np.sort(o[s.q:]) if s.q else np.arange(len(y))
        s.m_ = s.base().fit(X.iloc[k], y[k], m.iloc[k]); return s
    def predict(s, X, m): return s.m_.predict(X, m)


class Blend:
    def __init__(s, base, a=0.3, ws='sqrt'): s.base, s.a, s.ws = base, a, ws
    def fit(s, X, y, m):
        s.m_ = s.base().fit(X, y, m)
        s.mu_ = _wmean(y, weights_from(m['eff_extent'].values, s.ws)); return s
    def predict(s, X, m): return s.a * s.m_.predict(X, m) + (1 - s.a) * s.mu_


# ------------------------------------------------------------------- library
def library():
    C = {}
    for ws in ['equal', 'sqrt', 'lin', 'log', 'sat25', 'sat50', 'sat100', 'sat200', 'sat400']:
        C[f'mean[{ws}]'] = lambda ws=ws: GrandMean(ws)
        C[f'geo[{ws}]'] = lambda ws=ws: WGeoMean(ws, True)
        for c in [1.0, 1.345, 2.0]:
            C[f'huber[{ws},c{c}]'] = lambda ws=ws, c=c: WHuber(ws, c)
        for lam in [0.15, 0.3, 0.5, 0.75, 1.0]:
            C[f'pool[{ws},lam{lam}]'] = lambda ws=ws, lam=lam: PartialPool(ws, lam)
    for ws in ['equal', 'sqrt', 'lin', 'sat50', 'sat200']:
        for ps in [0.5, 1.0, 2.0]:
            C[f'eb[{ws},phi{ps}]'] = lambda ws=ws, ps=ps: EBDistrict(ws, ps)
    for p in [0.25, 0.5, 0.75, 1.0]:
        C[f'me[p{p}]'] = lambda p=p: MEWeightedMean(p, 'mom')
        C[f'me0[p{p}]'] = lambda p=p: MEWeightedMean(p, 'zero')
    for p in [0.5, 1.0]:
        C[f'rawext[p{p}]'] = lambda p=p: RawExtentMean(p)
    for ws in ['equal', 'sqrt', 'lin', 'sat50']:
        for k in [1, 2, 3, 5]:
            for lam in [3., 10., 30., 100.]:
                for lg in [False, True]:
                    C[f'ridge[{ws},k{k},l{lam:g}{",log" if lg else ""}]'] = \
                        lambda ws=ws, k=k, lam=lam, lg=lg: WRidge(ws, k, lam, lg)
    for k in [1, 2, 3]:
        for lam in [10., 30., 100., 300.]:
            C[f'meridge[k{k},l{lam:g}]'] = lambda k=k, lam=lam: WRidge('equal', k, lam, False, True)
    for k in [1, 2, 3]:
        for lam in [3., 10., 30., 100.]:
            for pw in [True, False]:
                C[f'gamma[k{k},l{lam:g}{",pw" if pw else ""}]'] = \
                    lambda k=k, lam=lam, pw=pw: GammaOffset(k, lam, pw)
    for ws in ['equal', 'sqrt', 'lin']:
        for k in [1, 2, 3]:
            for lam in [10., 30., 100., 300.]:
                for sh in [1.0, 0.5, 0.25]:
                    C[f'fe[{ws},k{k},l{lam:g},s{sh}]'] = \
                        lambda ws=ws, k=k, lam=lam, sh=sh: FERidge(ws, k, lam, sh, False)
                    C[f'feW[{ws},k{k},l{lam:g},s{sh}]'] = \
                        lambda ws=ws, k=k, lam=lam, sh=sh: FERidge(ws, k, lam, sh, True)
    for q in [2, 4, 6, 8]:
        for ws in ['equal', 'sqrt', 'lin']:
            C[f'trim{q}+mean[{ws}]'] = lambda q=q, ws=ws: Trimmed(lambda ws=ws: GrandMean(ws), q)
        C[f'trim{q}+eb[lin]'] = lambda q=q: Trimmed(lambda: EBDistrict('lin', 1.), q)
    for a in [0.1, 0.25, 0.5]:
        C[f'blend{a}+eb[sqrt]'] = lambda a=a: Blend(lambda: EBDistrict('sqrt', 1.), a)
        C[f'blend{a}+ridge[sqrt,k1,l100]'] = lambda a=a: Blend(lambda: WRidge('sqrt', 1, 100.), a)
        C[f'blend{a}+gamma[k1,l100]'] = lambda a=a: Blend(lambda: GammaOffset(1, 100., True), a)
    return C


# ----------------------------------------------------------------- evaluation
def loyo_predict(fn, df, years, fc):
    pred = np.full(len(df), np.nan)
    for yr in years:
        te = df['Year'].values == yr
        tr = (~te) & np.isin(df['Year'].values, years)
        m = fn().fit(df.loc[tr, fc], df.loc[tr, TARGET_COLUMN].values, df.loc[tr, META])
        pred[te] = m.predict(df.loc[te, fc], df.loc[te, META])
    return pred


def flat_loyo(fn, df, fc):
    yrs = np.sort(df['Year'].unique()); p = loyo_predict(fn, df, yrs, fc)
    y = df[TARGET_COLUMN].values
    return r2_score(y, p), float(np.sqrt(mean_squared_error(y, p))), p


def nested_loyo(C, df, fc, verbose=True):
    y = df[TARGET_COLUMN].values; yrs = np.sort(df['Year'].unique())
    pred = np.full(len(df), np.nan); chosen = {}
    for yr in yrs:
        inner = yrs[yrs != yr]
        sub = df[df['Year'].isin(inner)].reset_index(drop=True)
        best, bm = None, np.inf
        for n, fn in C.items():
            try:
                mse = mean_squared_error(sub[TARGET_COLUMN].values, loyo_predict(fn, sub, inner, fc))
            except Exception:
                continue
            if mse < bm - 1e-12: bm, best = mse, n
        chosen[int(yr)] = best
        te = df['Year'].values == yr
        m = C[best]().fit(df.loc[~te, fc], y[~te], df.loc[~te, META])
        pred[te] = m.predict(df.loc[te, fc], df.loc[te, META])
        if verbose: print(f'    outer {yr}: inner-selected {best}  (inner MSE {bm:.3f})')
    return r2_score(y, pred), float(np.sqrt(mean_squared_error(y, pred))), pred, chosen


def block_bootstrap(y, pa, pb, n=20000, seed=0):
    rng = np.random.default_rng(seed); idx = [np.arange(i * 4, i * 4 + 4) for i in range(7)]
    d = []
    for _ in range(n):
        ii = np.concatenate([idx[p] for p in rng.choice(7, 7, replace=True)])
        yy = y[ii]; sst = np.sum((yy - yy.mean()) ** 2)
        if sst <= 0: continue
        d.append((np.sum((yy - pb[ii]) ** 2) - np.sum((yy - pa[ii]) ** 2)) / sst)
    d = np.array(d)
    return float(d.mean()), float(np.quantile(d, .025)), float(np.quantile(d, .975)), float((d <= 0).mean())


# ----------------------------------------------------------------------- main
def main():
    df = load_panel(); y = df[TARGET_COLUMN].values; fc = df.columns.tolist()
    se2 = _se2(df)
    print(f'panel {df.shape}   target mean {y.mean():.2f}  sd {y.std(ddof=1):.2f}')
    print(f'direct month-level measurement variance: mean se^2 = {np.mean(se2):.2f} '
          f'= {np.mean(se2) / np.var(y, ddof=1):.1%} of total target variance')
    print(f'corr(se^2, 1/extent_ha) = {np.corrcoef(se2, 1 / df.extent_ha.values)[0, 1]:+.3f}'
          '   <- extent is only a weak proxy for the actual noise')

    print('\n--- harness check + pre-registered (zero-tuning) estimators ---')
    out = {}
    for nme, fn in [('climatology (unweighted)', lambda: GrandMean('equal')),
                    ('w ~ sqrt(extent_ha)   [repo default]', lambda: RawExtentMean(0.5)),
                    ('w ~ extent_ha         [1/var if var~1/A]', lambda: RawExtentMean(1.0)),
                    ('w ~ 1/(tau2+se_i^2)   [direct ME, exact IV]', lambda: MEWeightedMean(1.0)),
                    ('w ~ sqrt(eff_extent)', lambda: GrandMean('sqrt'))]:
        r2, rmse, p = flat_loyo(fn, df, fc)
        out[nme] = (r2, rmse, p)
        print(f'  {nme:44s} R2 {r2:+.4f}  RMSE {rmse:.3f}')
    pc = out['climatology (unweighted)'][2]

    C = library()
    print(f'\n--- NESTED-CV over {len(C)} configurations (the reportable number) ---')
    r2n, rmsen, pn, chosen = nested_loyo(C, df, fc)
    print(f'  NESTED-CV pooled LOYO   R2 {r2n:+.4f}   RMSE {rmsen:.3f}')

    print('\n--- randomisation null: 2000 ARBITRARY weight vectors, same LOYO ---')
    rng = np.random.default_rng(7); dfr = df.copy(); r2s = []
    for _ in range(2000):
        dfr['eff_extent'] = np.exp(rng.normal(0, 2.0, len(df)))
        r2s.append(flat_loyo(lambda: GrandMean('lin'), dfr, fc)[0])
    r2s = np.array(r2s)
    r2c = out['climatology (unweighted)'][0]
    print(f'  arbitrary weightings that "beat" climatology: {(r2s > r2c).mean():.1%}')
    print(f'  null distribution: median {np.median(r2s):+.4f}  p99 {np.quantile(r2s, .99):+.4f}'
          f'  max {r2s.max():+.4f}')
    for nme in ['w ~ sqrt(eff_extent)', 'w ~ 1/(tau2+se_i^2)   [direct ME, exact IV]']:
        print(f'  percentile of {nme:44s} in null: {(r2s < out[nme][0]).mean():.1%}')

    print('\n--- year-block bootstrap of dR2 vs climatology ---')
    for nme in ['w ~ sqrt(extent_ha)   [repo default]', 'w ~ 1/(tau2+se_i^2)   [direct ME, exact IV]',
                'w ~ sqrt(eff_extent)']:
        m, lo, hi, pv = block_bootstrap(y, out[nme][2], pc)
        print(f'  {nme:44s} {m:+.4f}  95% CI [{lo:+.4f},{hi:+.4f}]  P(dR2<=0)={pv:.3f}')
    m, lo, hi, pv = block_bootstrap(y, pn, pc)
    print(f'  {"NESTED-CV":44s} {m:+.4f}  95% CI [{lo:+.4f},{hi:+.4f}]  P(dR2<=0)={pv:.3f}')

    print('\n================ REPORTED RESULT ================')
    print(f'  NESTED-CV LOYO R2   {r2n:+.4f}   RMSE {rmsen:.3f}')
    print(f'  climatology         {r2c:+.4f}   RMSE {out["climatology (unweighted)"][1]:.3f}')
    print(f'  beats climatology?  {r2n > r2c}')
    print(f'  beats best model (SymbolicRegression, -0.209)?  {r2n > -0.209}')
    json.dump({'nested_cv_r2': r2n, 'nested_cv_rmse': rmsen, 'chosen': chosen,
               'n_configs': len(C),
               'pre_registered': {k: {'r2': v[0], 'rmse': v[1]} for k, v in out.items()},
               'random_null_frac_beating_clim': float((r2s > r2c).mean())},
              open(os.path.join(ROOT, 'experiments/me_report.json'), 'w'), indent=2, default=str)


if __name__ == '__main__':
    main()

"""Round 2: year-fixed-effects, robust weighted location, shrunk blends.

All of these still obey the protocol: every quantity is estimated inside the outer
training set of 6 years / 24 rows. The year-demeaning uses ONLY training years'
means; the held-out year's mean is never formed.
"""
import os, sys, json
import numpy as np, pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from config import ALL_FEATURES, TARGET_COLUMN
from measurement_error_loyo import (load_panel, weights_from, _wmean, GrandMean,
                                    EBDistrict, WRidge, GammaOffset, Trimmed,
                                    loyo_predict, flat_loyo, nested_loyo, ROOT)

META = ['Year', 'District', 'extent_ha', 'eff_extent', 'n_months']


class WGeoMean:
    """Weighted geometric mean with Duan smearing -- the natural centre for a ratio
    whose error is multiplicative."""
    def __init__(self, wscheme='sqrt', smear=True):
        self.wscheme, self.smear = wscheme, smear
    def fit(self, X, y, meta):
        w = weights_from(meta['eff_extent'].values, self.wscheme)
        m = _wmean(np.log(y), w)
        s = float(np.sum(w*np.exp(np.log(y)-m))/np.sum(w)) if self.smear else 1.0
        self.mu_ = np.exp(m)*s
        return self
    def predict(self, X, meta):
        return np.full(len(meta), self.mu_)


class WHuber:
    """Weighted Huber M-estimator of location: down-weights the cells whose value is
    extreme *given* their measurement precision."""
    def __init__(self, wscheme='sqrt', c=1.345):
        self.wscheme, self.c = wscheme, c
    def fit(self, X, y, meta):
        w = weights_from(meta['eff_extent'].values, self.wscheme)
        mu = _wmean(y, w)
        s = 1.4826*np.median(np.abs(y-np.median(y))) + 1e-9
        for _ in range(200):
            r = (y-mu)/s
            psi = np.clip(r, -self.c, self.c)
            new = mu + s*np.sum(w*psi)/np.sum(w)
            if abs(new-mu) < 1e-10: mu = new; break
            mu = new
        self.mu_ = mu
        return self
    def predict(self, X, meta):
        return np.full(len(meta), self.mu_)


class FERidge:
    """Within-year fixed-effects ridge, then predict deviations for the held-out year.

    Training rows are demeaned by their OWN year's weighted mean (training years
    only), which strips out the between-year variance LOYO cannot reward and leaves
    the district-year deviation -- the only part with recoverable signal. The
    prediction for the held-out year is (training grand mean) + shrink * (predicted
    deviation). Features are demeaned by the same training-year means.
    """
    def __init__(self, wscheme='sqrt', k=3, lam=30.0, shrink=1.0, features=None):
        self.wscheme, self.k, self.lam, self.shrink = wscheme, k, lam, shrink
        self.features = features or ALL_FEATURES
    def fit(self, X, y, meta):
        w = weights_from(meta['eff_extent'].values, self.wscheme)
        yrs = meta['Year'].values
        Xa = X[self.features].values.astype(float)

        # per-training-year weighted means (target and features)
        ydev = np.empty_like(y); Xdev = np.empty_like(Xa)
        self.xbar_ = {}
        for u in np.unique(yrs):
            m = yrs == u
            ydev[m] = y[m] - _wmean(y[m], w[m])
            xb = np.average(Xa[m], axis=0, weights=w[m])
            Xdev[m] = Xa[m] - xb
        self.gm_ = _wmean(y, w)
        # a held-out year's own feature mean is unknown at prediction time, so use
        # the average of the training-year feature means as the centring constant
        self.xc_ = np.mean([np.average(Xa[yrs == u], axis=0, weights=w[yrs == u])
                            for u in np.unique(yrs)], axis=0)

        sd = np.sqrt(np.average(Xdev**2, axis=0, weights=w)); sd[sd < 1e-12] = 1.0
        self.sd_ = sd
        Z = Xdev/sd
        sw = np.sqrt(w)
        denom = np.sqrt(np.average(ydev**2, weights=w))
        c = np.abs(((sw[:, None]*Z).T @ (sw*ydev))/np.sum(w))/max(denom, 1e-12)
        self.idx_ = np.argsort(-c)[:self.k]
        A = sw[:, None]*Z[:, self.idx_]; b = sw*ydev
        G = A.T@A + self.lam*np.eye(len(self.idx_))
        self.coef_ = np.linalg.solve(G, A.T@b)
        return self
    def predict(self, X, meta):
        Xa = X[self.features].values.astype(float)
        Z = (Xa - self.xc_)/self.sd_
        return self.gm_ + self.shrink*(Z[:, self.idx_] @ self.coef_)


class FEWithinYear(FERidge):
    """Same as FERidge but the held-out year's own feature mean IS used for centring.

    Legitimate: it uses only the held-out rows' PREDICTORS (never their targets), and
    it is exactly how a within-year relative forecast would be issued in practice --
    'which district beats the season average'. Kept separate and labelled so the
    weaker assumption is visible.
    """
    def predict(self, X, meta):
        Xa = X[self.features].values.astype(float)
        Xd = Xa - Xa.mean(axis=0)                     # test-year rows only, X not y
        Z = Xd/self.sd_
        return self.gm_ + self.shrink*(Z[:, self.idx_] @ self.coef_)


class Blend:
    """convex blend of a model with the weighted grand mean"""
    def __init__(self, base, alpha=0.3, wscheme='sqrt'):
        self.base, self.alpha, self.wscheme = base, alpha, wscheme
    def fit(self, X, y, meta):
        self.m_ = self.base().fit(X, y, meta)
        w = weights_from(meta['eff_extent'].values, self.wscheme)
        self.mu_ = _wmean(y, w)
        return self
    def predict(self, X, meta):
        return self.alpha*self.m_.predict(X, meta) + (1-self.alpha)*self.mu_


def candidates2():
    C = {}
    for ws in ['equal', 'sqrt', 'lin', 'log', 'sat25', 'sat50', 'sat100', 'sat200', 'sat400']:
        C[f'mean[{ws}]'] = lambda ws=ws: GrandMean(ws)
        C[f'geo[{ws}]'] = lambda ws=ws: WGeoMean(ws, True)
        C[f'geo0[{ws}]'] = lambda ws=ws: WGeoMean(ws, False)
        for c in [1.0, 1.345, 2.0]:
            C[f'huber[{ws},c{c}]'] = lambda ws=ws, c=c: WHuber(ws, c)
    for ws in ['equal', 'sqrt', 'lin']:
        for k in [1, 2, 3]:
            for lam in [10., 30., 100., 300.]:
                for sh in [1.0, 0.5, 0.25]:
                    C[f'fe[{ws},k{k},l{lam:g},s{sh}]'] = (
                        lambda ws=ws, k=k, lam=lam, sh=sh: FERidge(ws, k, lam, sh))
                    C[f'feW[{ws},k{k},l{lam:g},s{sh}]'] = (
                        lambda ws=ws, k=k, lam=lam, sh=sh: FEWithinYear(ws, k, lam, sh))
    for a in [0.1, 0.25, 0.5]:
        C[f'blend{a}+eb[sqrt]'] = lambda a=a: Blend(lambda: EBDistrict('sqrt', 1.0), a)
        C[f'blend{a}+ridge[sqrt,k1,l100]'] = lambda a=a: Blend(lambda: WRidge('sqrt', 1, 100.), a)
        C[f'blend{a}+gamma[k1,l100]'] = lambda a=a: Blend(lambda: GammaOffset(1, 100., True), a)
    for q in [2, 4, 6, 8]:
        for ws in ['equal', 'sqrt', 'lin']:
            C[f'trim{q}+mean[{ws}]'] = lambda q=q, ws=ws: Trimmed(lambda ws=ws: GrandMean(ws), q)
    return C


def block_bootstrap(y, pa, pb, n=20000, seed=0):
    """Year-block bootstrap of the R2 difference (years are the resampling unit)."""
    rng = np.random.default_rng(seed)
    yrs = np.arange(7)
    idx = [np.arange(i*4, i*4+4) for i in yrs]   # df is sorted by Year
    d = []
    for _ in range(n):
        pick = rng.choice(yrs, 7, replace=True)
        ii = np.concatenate([idx[p] for p in pick])
        yy = y[ii]
        sst = np.sum((yy-yy.mean())**2)
        if sst <= 0: continue
        d.append((np.sum((yy-pb[ii])**2) - np.sum((yy-pa[ii])**2))/sst)
    d = np.array(d)
    return float(d.mean()), float(np.quantile(d, .025)), float(np.quantile(d, .975)), float((d <= 0).mean())


def main():
    df = load_panel(); fc = df.columns.tolist(); y = df[TARGET_COLUMN].values
    C = candidates2()
    print(f'{len(C)} round-2 candidates')
    rows = []
    for nme, fn in C.items():
        try: r2, rmse, _ = flat_loyo(fn, df, fc)
        except Exception as e: print('fail', nme, e); continue
        rows.append((nme, r2, rmse))
    lb = pd.DataFrame(rows, columns=['config','loyo_r2','loyo_rmse']).sort_values('loyo_r2', ascending=False)
    lb.to_csv(os.path.join(ROOT,'experiments/me_leaderboard2.csv'), index=False)
    print('\n=== diagnostic leaderboard (round 2) ===')
    print(lb.head(25).to_string(index=False))

    print('\n=== NESTED LOYO over the full round-1+round-2 library ===')
    import measurement_error_loyo as m1
    ALL = dict(m1.candidates()); ALL.update(C)
    print(f'library size {len(ALL)}')
    r2n, rmsen, pn, chosen = nested_loyo(ALL, df, fc)
    print(f'NESTED pooled LOYO: R2 {r2n:+.4f} RMSE {rmsen:.3f}')

    # nested over ONLY the location-estimator family (the pre-registered restriction:
    # the measurement-error hypothesis is about the weighting, not about features)
    LOC = {k: v for k, v in ALL.items() if k.split('[')[0] in ('mean','geo','geo0','huber','eb')}
    print(f'\n=== NESTED LOYO restricted to weighted-location family ({len(LOC)}) ===')
    r2l, rmsel, pl, chosl = nested_loyo(LOC, df, fc)
    print(f'NESTED(location) pooled LOYO: R2 {r2l:+.4f} RMSE {rmsel:.3f}')

    # fixed a-priori: inverse-variance sqrt weighting, no tuning at all
    r2f, rmsef, pf = flat_loyo(lambda: GrandMean('sqrt'), df, fc)
    r2c, rmsec, pc = flat_loyo(lambda: GrandMean('equal'), df, fc)
    print(f'\nfixed sqrt-effective-extent weighted mean : R2 {r2f:+.4f} RMSE {rmsef:.3f}')
    print(f'unweighted climatology                    : R2 {r2c:+.4f} RMSE {rmsec:.3f}')
    m, lo, hi, p = block_bootstrap(y, pf, pc)
    print(f'year-block bootstrap dR2 (weighted - unweighted): {m:+.4f}  95% CI [{lo:+.4f},{hi:+.4f}]  P(<=0)={p:.3f}')

    out = {'nested_full': {'r2': r2n, 'rmse': rmsen, 'chosen': chosen, 'n': len(ALL)},
           'nested_location': {'r2': r2l, 'rmse': rmsel, 'chosen': chosl, 'n': len(LOC)},
           'fixed_sqrt': {'r2': r2f, 'rmse': rmsef},
           'climatology': {'r2': r2c, 'rmse': rmsec},
           'bootstrap_dr2': {'mean': m, 'lo': lo, 'hi': hi, 'p_le_0': p}}
    json.dump(out, open(os.path.join(ROOT,'experiments/me_results2.json'),'w'), indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))


if __name__ == '__main__':
    main()

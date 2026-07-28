"""Round 3: the fully-specified measurement-error variance model, estimated in-fold.

Diagnostics showed the pure inverse-variance weight w ~ E is too aggressive: a single
phi fitted to the within-district scatter implies per-cell noise sd up to 60 MT/ha,
far above the 6.2 MT/ha spread of the target. The correct model has a NUGGET -- real
district-year variation that no amount of area removes:

    var(y_i) = sigma0^2 + phi / E_i        =>     w_i ~ 1 / (sigma0^2 + phi/E_i)

which is the sat-k family with k = phi/sigma0^2. IVFitMean estimates (sigma0^2, phi)
by weighted least squares on the squared within-district residuals of the TRAINING
rows only, so the resulting weights carry no free parameter and no test information.
"""
import os, sys, json
import numpy as np, pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from config import TARGET_COLUMN
from measurement_error_loyo import (load_panel, weights_from, _wmean, GrandMean,
                                    flat_loyo, nested_loyo, loyo_predict, ROOT)
from me_round2 import WGeoMean, WHuber, block_bootstrap


def _fit_variance_model(y, e, d):
    """(sigma0^2, phi) from within-district squared residuals vs 1/E. Training only."""
    r2s, inv = [], []
    for dd in np.unique(d):
        m = d == dd
        if m.sum() < 2:
            continue
        c = y[m].mean()
        # unbiased-ish: scale residuals by n/(n-1)
        f = m.sum() / (m.sum() - 1)
        r2s.extend(f * (y[m] - c) ** 2)
        inv.extend(1.0 / e[m])
    r2s, inv = np.array(r2s), np.array(inv)
    A = np.column_stack([np.ones_like(inv), inv])
    # non-negative LS by simple projection (2 params)
    coef, *_ = np.linalg.lstsq(A, r2s, rcond=None)
    s0, phi = float(coef[0]), float(coef[1])
    if s0 <= 0 or phi <= 0:                     # fall back to the constrained fits
        phi_only = float(np.sum(inv * r2s) / np.sum(inv ** 2))
        s0_only = float(r2s.mean())
        if s0 <= 0:
            s0, phi = 1e-9, max(phi_only, 1e-9)
        else:
            s0, phi = max(s0_only, 1e-9), 1e-9
    return s0, phi


class IVFitMean:
    """Inverse-variance weighted mean, variance model estimated inside the fold."""
    def __init__(self, cap=None):
        self.cap = cap
    def fit(self, X, y, meta):
        e = meta['eff_extent'].values.astype(float)
        d = meta['District'].values
        s0, phi = _fit_variance_model(y, e, d)
        self.s0_, self.phi_ = s0, phi
        w = 1.0 / (s0 + phi / e)
        w = w / w.mean()
        if self.cap:
            w = np.clip(w, 1.0 / self.cap, self.cap)
        self.w_ = w
        self.mu_ = _wmean(y, w)
        return self
    def predict(self, X, meta):
        return np.full(len(meta), self.mu_)


class IVFitPower(IVFitMean):
    """Same variance model but the weight is raised to a power p (p=1 is exact IV,
    p=0.5 is the variance-stabilised compromise the panel builder already uses)."""
    def __init__(self, p=0.5):
        self.p = p
    def fit(self, X, y, meta):
        e = meta['eff_extent'].values.astype(float)
        s0, phi = _fit_variance_model(y, e, meta['District'].values)
        w = (1.0 / (s0 + phi / e)) ** self.p
        w = w / w.mean()
        self.mu_ = _wmean(y, w); self.s0_, self.phi_ = s0, phi
        return self


class PartialPool:
    """Weighted grand mean + lambda * (weighted district deviation), lambda fixed."""
    def __init__(self, wscheme='sqrt', lam=0.3):
        self.wscheme, self.lam = wscheme, lam
    def fit(self, X, y, meta):
        w = weights_from(meta['eff_extent'].values, self.wscheme)
        self.mu_ = _wmean(y, w)
        d = meta['District'].values
        self.b_ = {dd: _wmean(y[d == dd], w[d == dd]) - self.mu_ for dd in np.unique(d)}
        return self
    def predict(self, X, meta):
        return np.array([self.mu_ + self.lam * self.b_.get(dd, 0.0)
                         for dd in meta['District'].values])


def main():
    df = load_panel(); fc = df.columns.tolist(); y = df[TARGET_COLUMN].values

    print('=== variance model on all 28 (diagnostic only) ===')
    s0, phi = _fit_variance_model(y, df.eff_extent.values, df.District.values)
    print(f'  sigma0^2 = {s0:.2f}  (sd {np.sqrt(s0):.2f} MT/ha, irreducible)')
    print(f'  phi      = {phi:.2f}  -> k = phi/sigma0^2 = {phi/max(s0,1e-9):.1f} ha')

    C = {}
    C['ivfit'] = lambda: IVFitMean()
    for cap in [2., 3., 5., 10.]:
        C[f'ivfit[cap{cap:g}]'] = lambda cap=cap: IVFitMean(cap)
    for p in [0.25, 0.5, 0.75, 1.0]:
        C[f'ivpow[p{p}]'] = lambda p=p: IVFitPower(p)
    for ws in ['equal', 'sqrt', 'lin', 'sat25', 'sat50', 'sat100']:
        C[f'mean[{ws}]'] = lambda ws=ws: GrandMean(ws)
        C[f'geo[{ws}]'] = lambda ws=ws: WGeoMean(ws, True)
        for c in [1.0, 1.345, 2.0]:
            C[f'huber[{ws},c{c}]'] = lambda ws=ws, c=c: WHuber(ws, c)
        for lam in [0.15, 0.3, 0.5, 0.75, 1.0]:
            C[f'pool[{ws},lam{lam}]'] = lambda ws=ws, lam=lam: PartialPool(ws, lam)

    rows = []
    for n, fn in C.items():
        r2, rmse, _ = flat_loyo(fn, df, fc)
        rows.append((n, r2, rmse))
    lb = pd.DataFrame(rows, columns=['config', 'loyo_r2', 'loyo_rmse']).sort_values('loyo_r2', ascending=False)
    lb.to_csv(os.path.join(ROOT, 'experiments/me_leaderboard3.csv'), index=False)
    print('\n=== round-3 diagnostic leaderboard (top 20) ===')
    print(lb.head(20).to_string(index=False))
    print('\n--- bottom 5 ---'); print(lb.tail(5).to_string(index=False))

    print(f'\n=== NESTED LOYO over the round-3 location library ({len(C)}) ===')
    r2n, rmsen, pn, ch = nested_loyo(C, df, fc)
    print(f'NESTED: R2 {r2n:+.4f} RMSE {rmsen:.3f}')

    print('\n=== pre-registered, ZERO-TUNING estimator: ivfit ===')
    r2i, rmsei, pi = flat_loyo(lambda: IVFitMean(), df, fc)
    r2s, rmses, ps = flat_loyo(lambda: GrandMean('sqrt'), df, fc)
    r2c, rmsec, pc = flat_loyo(lambda: GrandMean('equal'), df, fc)
    print(f'  ivfit          R2 {r2i:+.4f} RMSE {rmsei:.3f}')
    print(f'  mean[sqrt]     R2 {r2s:+.4f} RMSE {rmses:.3f}')
    print(f'  climatology    R2 {r2c:+.4f} RMSE {rmsec:.3f}')

    print('\n=== year-block bootstrap of dR2 vs unweighted climatology ===')
    for nme, p in [('ivfit', pi), ('mean[sqrt]', ps), ('nested', pn)]:
        m, lo, hi, pv = block_bootstrap(y, p, pc)
        print(f'  {nme:12s} dR2 {m:+.4f}  95% CI [{lo:+.4f},{hi:+.4f}]  P(dR2<=0)={pv:.3f}')
    # paired sign/Wilcoxon on the 28 squared errors, and on the 7 year-level MSEs
    from scipy.stats import wilcoxon
    sa, sb = (y - ps) ** 2, (y - pc) ** 2
    print('  wilcoxon on 28 squared errors (sqrt vs equal): p =',
          f'{wilcoxon(sa, sb).pvalue:.4f}')
    ya = pd.Series(sa).groupby(df.Year.values).mean(); yb = pd.Series(sb).groupby(df.Year.values).mean()
    print('  per-year MSE  weighted:', np.round(ya.values, 2))
    print('  per-year MSE  unweight:', np.round(yb.values, 2))
    print('  years improved:', int((ya < yb).sum()), '/ 7')

    json.dump({'ivfit': {'r2': r2i, 'rmse': rmsei},
               'mean_sqrt': {'r2': r2s, 'rmse': rmses},
               'climatology': {'r2': r2c, 'rmse': rmsec},
               'nested3': {'r2': r2n, 'rmse': rmsen, 'chosen': ch},
               'sigma0_sq': s0, 'phi': phi},
              open(os.path.join(ROOT, 'experiments/me_results3.json'), 'w'), indent=2, default=str)
    np.save(os.path.join(ROOT, 'experiments/preds_ivfit.npy'), pi)
    np.save(os.path.join(ROOT, 'experiments/preds_sqrt.npy'), ps)


if __name__ == '__main__':
    main()

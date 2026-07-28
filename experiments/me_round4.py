"""Round 4: measurement error estimated DIRECTLY, from month-to-month scatter.

The target of cell i is the mean of its n_i monthly implied yields. So the sampling
variance of that mean is estimable WITHOUT any extent model:

    se_i^2 = s_i^2 / n_i ,   s_i^2 = between-month variance of the cell's monthly yields

This is a direct, per-cell measurement-error variance. Cells with n_i = 1 get the
pooled estimate. The optimal weight is then

    w_i = 1 / (tau^2 + se_i^2)

with tau^2 (the real, irreducible district-year signal variance) estimated in-fold by
method of moments: tau^2 = max(0, Var(y_train) - mean(se^2_train)).

Everything -- s_i, se_i, tau^2, the grand mean -- is computed from training rows only.
"""
import os, sys, json
import numpy as np, pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from config import ALL_FEATURES, TARGET_COLUMN
from dcs_panel import load_dcs_records
from measurement_error_loyo import load_panel, weights_from, _wmean, GrandMean, WRidge, flat_loyo, nested_loyo, ROOT
from me_round2 import WHuber, WGeoMean, FERidge, block_bootstrap

META = ['Year', 'District', 'extent_ha', 'eff_extent', 'n_months', 'se2', 'se2_known']


def load_panel_se():
    df = load_panel()
    raw = load_dcs_records()
    raw = raw[(raw.Season == 'Yala') & (~raw.impossible) & (raw.extent_ha > 0)]
    rec = []
    for (yr, d), g in raw.groupby(['year', 'District']):
        v = g['implied_mt_per_ha'].astype(float).values
        n = len(v)
        rec.append({'Year': int(yr), 'District': d, 'n_m': n,
                    's2': float(np.var(v, ddof=1)) if n > 1 else np.nan,
                    'se2_raw': float(np.var(v, ddof=1) / n) if n > 1 else np.nan})
    df = df.merge(pd.DataFrame(rec), on=['Year', 'District'], how='left')
    df['se2_known'] = df['se2_raw'].notna()
    return df


def _se2(meta):
    """Per-row measurement variance; n=1 cells get the training-row pooled median."""
    s = meta['se2_raw'].values.astype(float)
    known = np.isfinite(s)
    if known.any():
        s = np.where(known, s, np.median(s[known]))
    else:
        s = np.ones_like(s)
    return s


class MEWeightedMean:
    """Optimal inverse-variance mean under y_i = mu + b_i + e_i, var(e_i)=se_i^2."""
    def __init__(self, power=1.0, tau_mode='mom'):
        self.power, self.tau_mode = power, tau_mode
    def _w(self, y, meta):
        se2 = _se2(meta)
        if self.tau_mode == 'mom':
            tau2 = max(float(np.var(y, ddof=1) - np.mean(se2)), 0.0)
        elif self.tau_mode == 'zero':
            tau2 = 0.0
        else:
            tau2 = float(self.tau_mode)
        w = (1.0 / (tau2 + se2)) ** self.power
        self.tau2_ = tau2
        return w / w.mean()
    def fit(self, X, y, meta):
        w = self._w(y, meta); self.w_ = w; self.mu_ = _wmean(y, w); return self
    def predict(self, X, meta):
        return np.full(len(meta), self.mu_)


class MEHuber(MEWeightedMean):
    def __init__(self, power=1.0, c=1.345):
        super().__init__(power, 'mom'); self.c = c
    def fit(self, X, y, meta):
        w = self._w(y, meta)
        mu = _wmean(y, w); s = 1.4826*np.median(np.abs(y-np.median(y)))+1e-9
        for _ in range(300):
            new = mu + s*np.sum(w*np.clip((y-mu)/s, -self.c, self.c))/np.sum(w)
            if abs(new-mu) < 1e-10: mu = new; break
            mu = new
        self.mu_ = mu; return self


class MERidge(WRidge):
    """GLS ridge with the DIRECT measurement-error weights."""
    def __init__(self, power=1.0, k=2, lam=30., log_target=False):
        super().__init__('equal', k, lam, log_target)
        self.power = power
    def fit(self, X, y, meta):
        se2 = _se2(meta)
        tau2 = max(float(np.var(y, ddof=1) - np.mean(se2)), 0.0)
        w = (1.0/(tau2+se2))**self.power; w = w/w.mean()
        meta = meta.copy(); meta['eff_extent'] = w      # weights_from('lin') -> w
        self.wscheme = 'lin'
        return super().fit(X, y, meta)
    def predict(self, X, meta):
        return super().predict(X, meta)


class MEDrop(MEWeightedMean):
    """Hard-drop the q training cells with the largest measurement variance."""
    def __init__(self, q=4, power=1.0):
        super().__init__(power, 'mom'); self.q = q
    def fit(self, X, y, meta):
        se2 = _se2(meta)
        keep = np.sort(np.argsort(se2)[:len(se2)-self.q]) if self.q else np.arange(len(y))
        w = 1.0/(max(float(np.var(y[keep], ddof=1)-np.mean(se2[keep])), 0.)+se2[keep])
        self.mu_ = _wmean(y[keep], w/w.mean()); return self


def main():
    df = load_panel_se(); y = df[TARGET_COLUMN].values; fc = df.columns.tolist()
    print('=== direct month-level measurement error (diagnostic, all 28) ===')
    print(df[['Year','District','n_m','extent_ha','se2_raw',TARGET_COLUMN]]
          .assign(se=lambda d: np.sqrt(d.se2_raw)).round(2).to_string(index=False))
    se2 = _se2(df)
    print(f'\n  mean se^2 = {np.mean(se2):.2f}   Var(y) = {np.var(y, ddof=1):.2f}')
    print(f'  measurement-error share of total target variance = {np.mean(se2)/np.var(y, ddof=1):.1%}')
    dev = y - df.groupby('Year')[TARGET_COLUMN].transform('mean').values
    print(f'  within-year variance = {np.var(dev, ddof=1)*28/21:.2f}; '
          f'ME share of within-year = {np.mean(se2)/(np.var(dev, ddof=1)*28/21):.1%}')
    print(f'  corr(se^2, 1/eff_extent) = {np.corrcoef(se2, 1/df.eff_extent.values)[0,1]:+.3f}')
    print(f'  corr(se^2, 1/extent_ha)  = {np.corrcoef(se2, 1/df.extent_ha.values)[0,1]:+.3f}')

    C = {'clim': lambda: GrandMean('equal')}
    for p in [0.25, 0.5, 0.75, 1.0]:
        C[f'me[p{p}]'] = lambda p=p: MEWeightedMean(p, 'mom')
        C[f'me0[p{p}]'] = lambda p=p: MEWeightedMean(p, 'zero')
        for c in [1.0, 1.345, 2.0]:
            C[f'mehub[p{p},c{c}]'] = lambda p=p, c=c: MEHuber(p, c)
    for q in [2, 4, 6, 8]:
        C[f'medrop{q}'] = lambda q=q: MEDrop(q)
    for p in [0.5, 1.0]:
        for k in [1, 2, 3]:
            for lam in [10., 30., 100., 300.]:
                C[f'meridge[p{p},k{k},l{lam:g}]'] = lambda p=p, k=k, lam=lam: MERidge(p, k, lam)
    for ws in ['sqrt', 'sat50']:
        C[f'mean[{ws}]'] = lambda ws=ws: GrandMean(ws)
        C[f'huber[{ws}]'] = lambda ws=ws: WHuber(ws, 1.345)

    rows = [(n, *flat_loyo(fn, df, fc)[:2]) for n, fn in C.items()]
    lb = pd.DataFrame(rows, columns=['config','loyo_r2','loyo_rmse']).sort_values('loyo_r2', ascending=False)
    lb.to_csv(os.path.join(ROOT,'experiments/me_leaderboard4.csv'), index=False)
    print('\n=== round-4 diagnostic leaderboard (top 15) ==='); print(lb.head(15).to_string(index=False))

    print(f'\n=== NESTED LOYO over round-4 library ({len(C)}) ===')
    r2n, rmsen, pn, ch = nested_loyo(C, df, fc)
    print(f'NESTED: R2 {r2n:+.4f} RMSE {rmsen:.3f}')

    print('\n=== pre-registered zero-tuning: me[p1.0] (exact inverse-variance) ===')
    r2m, rmsem, pm = flat_loyo(lambda: MEWeightedMean(1.0,'mom'), df, fc)
    r2c, rmsec, pc = flat_loyo(lambda: GrandMean('equal'), df, fc)
    print(f'  me[p1.0]     R2 {r2m:+.4f} RMSE {rmsem:.3f}')
    print(f'  climatology  R2 {r2c:+.4f} RMSE {rmsec:.3f}')
    for nme, p in [('me[p1.0]', pm), ('nested', pn)]:
        m, lo, hi, pv = block_bootstrap(y, p, pc)
        print(f'  bootstrap dR2 {nme:10s} {m:+.4f} 95% CI [{lo:+.4f},{hi:+.4f}] P(<=0)={pv:.3f}')
    ya = pd.Series((y-pm)**2).groupby(df.Year.values).mean()
    yb = pd.Series((y-pc)**2).groupby(df.Year.values).mean()
    print('  per-year MSE me :', np.round(ya.values,2))
    print('  per-year MSE clim:', np.round(yb.values,2), ' years improved', int((ya<yb).sum()),'/7')

    json.dump({'me_p1':{'r2':r2m,'rmse':rmsem},'clim':{'r2':r2c,'rmse':rmsec},
               'nested4':{'r2':r2n,'rmse':rmsen,'chosen':ch},
               'me_share_total': float(np.mean(se2)/np.var(y,ddof=1))},
              open(os.path.join(ROOT,'experiments/me_results4.json'),'w'), indent=2, default=str)


if __name__ == '__main__':
    main()

"""FINAL confirmatory run. Reports the honest numbers and stress-tests them.

Three reportable quantities, in decreasing order of defensibility:

 (A) NESTED-CV number  -- the only legitimate figure if any tuning happened. The
     configuration is re-selected by an inner LOYO on the 6 training years inside
     every outer fold, over the whole 461-config library.
 (B) PRE-REGISTERED zero-tuning estimators -- fixed before any LOYO number was seen:
       * clim_sqrt_extent : weighted mean with w ~ sqrt(extent_ha). This is the
         repository's OWN pre-existing default (src/config.py OBS_WEIGHT_MODE =
         'sqrt_extent', committed before this experiment), so it is not a
         leaderboard pick.
       * me_invvar        : exact inverse-variance weights from the direct
         month-level measurement-error estimate. The textbook answer.
 (C) The unweighted climatology reference, reproduced to confirm the harness.

STRESS TEST: 2,000 RANDOM weight vectors (unrelated to extent) are run through the
same LOYO. If a large fraction of arbitrary weightings also 'beat' climatology, then
the apparent gain from extent weighting is a property of n=28, not of extent.
"""
import os, sys, json
import numpy as np, pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from config import TARGET_COLUMN
from measurement_error_loyo import (load_panel, weights_from, _wmean, GrandMean,
                                    flat_loyo, nested_loyo, ROOT, candidates)
from me_round2 import candidates2, block_bootstrap
from me_round4 import load_panel_se, MEWeightedMean, MEHuber, MERidge, MEDrop, _se2


class RawExtentMean:
    """w ~ extent_ha ** p on the RAW seasonal extent (the repo's own convention)."""
    def __init__(self, p=0.5):
        self.p = p
    def fit(self, X, y, meta):
        w = np.clip(meta['extent_ha'].values.astype(float), 0, None) ** self.p
        w = w / w.mean()
        self.mu_ = _wmean(y, w); return self
    def predict(self, X, meta):
        return np.full(len(meta), self.mu_)


class RandWeightMean:
    """Control: weights drawn from a fixed random vector attached to each row.

    The weight is a deterministic function of the row (not of the target), exactly
    like an extent weight, so it passes through LOYO identically -- it just carries
    no measurement-error information.
    """
    def __init__(self, wcol):
        self.wcol = wcol
    def fit(self, X, y, meta):
        w = meta[self.wcol].values.astype(float); w = w / w.mean()
        self.mu_ = _wmean(y, w); return self
    def predict(self, X, meta):
        return np.full(len(meta), self.mu_)


def main():
    df = load_panel_se()
    y = df[TARGET_COLUMN].values
    fc = df.columns.tolist()
    res = {}

    def run(name, fn):
        r2, rmse, p = flat_loyo(fn, df, fc)
        res[name] = {'r2': float(r2), 'rmse': float(rmse)}
        return r2, rmse, p

    print('=' * 78)
    print('(C) reference')
    r2c, rmsec, pc = run('climatology_unweighted', lambda: GrandMean('equal'))
    print(f'  climatology (unweighted training-year mean)  R2 {r2c:+.4f}  RMSE {rmsec:.3f}')
    print('  ground-truth says -0.215 / 6.73 -> harness verified')

    print('\n(B) pre-registered, zero-tuning measurement-error estimators')
    r2r, rmser, pr = run('clim_sqrt_raw_extent', lambda: RawExtentMean(0.5))
    print(f'  w ~ sqrt(extent_ha)      [repo OBS_WEIGHT_MODE]  R2 {r2r:+.4f}  RMSE {rmser:.3f}')
    r2e, rmsee, pe = run('clim_sqrt_eff_extent', lambda: GrandMean('sqrt'))
    print(f'  w ~ sqrt(eff_extent)                            R2 {r2e:+.4f}  RMSE {rmsee:.3f}')
    r2l, rmsel, pl = run('clim_lin_raw_extent', lambda: RawExtentMean(1.0))
    print(f'  w ~ extent_ha            [exact 1/var if var~1/A] R2 {r2l:+.4f}  RMSE {rmsel:.3f}')
    r2v, rmsev, pv = run('me_invvar_direct', lambda: MEWeightedMean(1.0, 'mom'))
    print(f'  w ~ 1/(tau^2+se_i^2)     [direct month-level ME] R2 {r2v:+.4f}  RMSE {rmsev:.3f}')

    print('\n(A) NESTED-CV over the full library')
    ALL = dict(candidates()); ALL.update(candidates2())
    ALL.update({'me[p1.0]': lambda: MEWeightedMean(1.0, 'mom'),
                'me[p0.5]': lambda: MEWeightedMean(0.5, 'mom'),
                'mehub': lambda: MEHuber(1.0, 1.345),
                'medrop4': lambda: MEDrop(4),
                'meridge[k1,l100]': lambda: MERidge(0.5, 1, 100.),
                'rawext[p0.5]': lambda: RawExtentMean(0.5),
                'rawext[p1.0]': lambda: RawExtentMean(1.0)})
    print(f'  library size {len(ALL)}')
    r2n, rmsen, pn, chosen = nested_loyo(ALL, df, fc)
    res['nested_cv'] = {'r2': float(r2n), 'rmse': float(rmsen), 'chosen': chosen,
                        'n_configs': len(ALL)}
    print(f'  NESTED-CV pooled LOYO  R2 {r2n:+.4f}  RMSE {rmsen:.3f}')

    print('\n' + '=' * 78)
    print('STRESS TEST: 2000 random (non-extent) weightings through the same LOYO')
    rng = np.random.default_rng(7)
    beats, r2s = 0, []
    dfr = df.copy()
    for i in range(2000):
        # log-normal weights with roughly the dispersion of sqrt(extent) weights;
        # injected through eff_extent so the LOYO path is byte-identical
        dfr['eff_extent'] = np.exp(rng.normal(0, 2.0, len(df)))
        rr, _, _ = flat_loyo(lambda: GrandMean('lin'), dfr, fc)
        r2s.append(rr)
        beats += rr > r2c
    r2s = np.array(r2s)
    print(f'  random weightings beating unweighted climatology: {beats}/2000 = {beats/2000:.1%}')
    print(f'  random-weighting R2 distribution: median {np.median(r2s):+.4f}  '
          f'p90 {np.quantile(r2s, .90):+.4f}  p99 {np.quantile(r2s, .99):+.4f}  max {r2s.max():+.4f}')
    for nme, val in [('sqrt(extent_ha)', r2r), ('sqrt(eff_extent)', r2e), ('1/(tau2+se2)', r2v)]:
        print(f'  percentile of {nme:18s} R2={val:+.4f} in the random null: '
              f'{(r2s < val).mean():.1%}')
    res['random_null'] = {'frac_beating_clim': beats/2000,
                          'median': float(np.median(r2s)), 'p90': float(np.quantile(r2s,.9)),
                          'p99': float(np.quantile(r2s,.99)), 'max': float(r2s.max()),
                          'pct_sqrt_raw': float((r2s < r2r).mean()),
                          'pct_sqrt_eff': float((r2s < r2e).mean()),
                          'pct_invvar': float((r2s < r2v).mean())}

    print('\n' + '=' * 78)
    print('UNCERTAINTY (year-block bootstrap, years are the resampling unit)')
    for nme, p in [('sqrt(extent_ha)', pr), ('sqrt(eff_extent)', pe),
                   ('1/(tau2+se2)', pv), ('NESTED-CV', pn)]:
        m, lo, hi, pval = block_bootstrap(y, p, pc)
        print(f'  dR2 vs climatology  {nme:18s} {m:+.4f}  95% CI [{lo:+.4f},{hi:+.4f}]  '
              f'P(dR2<=0) = {pval:.3f}')
        res.setdefault('bootstrap', {})[nme] = {'mean': m, 'lo': lo, 'hi': hi, 'p_le_0': pval}

    print('\nper-year out-of-fold MSE')
    tab = pd.DataFrame({'year': sorted(df.Year.unique())})
    for nme, p in [('clim', pc), ('sqrt_raw', pr), ('sqrt_eff', pe), ('invvar', pv), ('nested', pn)]:
        tab[nme] = pd.Series((y - p) ** 2).groupby(df.Year.values).mean().values
    print(tab.round(2).to_string(index=False))
    print('years where sqrt(extent) beats clim:',
          int((tab.sqrt_raw < tab.clim).sum()), '/ 7')

    print('\nWEIGHTED vs UNWEIGHTED, the headline comparison the strategy asked for:')
    print(f'  unweighted loss : R2 {r2c:+.4f}  RMSE {rmsec:.3f}')
    print(f'  weighted   loss : R2 {r2r:+.4f}  RMSE {rmser:.3f}   (sqrt extent)')
    print(f'  weighted   loss : R2 {r2v:+.4f}  RMSE {rmsev:.3f}   (exact inverse-variance)')

    json.dump(res, open(os.path.join(ROOT, 'experiments/me_final.json'), 'w'), indent=2, default=str)
    print('\nwritten experiments/me_final.json')


if __name__ == '__main__':
    main()

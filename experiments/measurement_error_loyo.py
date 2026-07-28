"""
Measurement-error-aware LOYO experiment for the 28-cell big-onion Yala panel.

The target Avg_Yield_MT_per_Ha for cell i is the UNWEIGHTED MEAN of that cell's
monthly implied yields (production_m / extent_m), verified numerically against the
raw DCS month-records. If monthly production behaves like a count with
var(production_m) ~ phi * extent_m, then

    var(yield_i) = (phi / n_i^2) * sum_m (1 / extent_m)   ==   phi / E_i

with the EFFECTIVE EXTENT

    E_i = n_i^2 / sum_m (1 / extent_m)      (harmonic effective area, ha)

E_i is the natural inverse-variance weight. It is computed only from extents and
month counts -- never from the target -- so it is a pure covariate and carries no
information about the held-out yields.

PROTOCOL: outer leave-one-year-out over 2019..2025 (4 rows held out each fold).
Every scaler, every feature ranking, every weight normalisation, every
hyper-parameter is fitted inside the outer training set. The reported
configuration is chosen by a NESTED inner LOYO run on the 6 training years only,
independently in each outer fold. Reported R2 is sklearn r2_score on the pooled
28 out-of-fold predictions, unweighted, identical to how the published baselines
were computed.
"""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import ALL_FEATURES, TARGET_COLUMN            # noqa: E402
from dcs_panel import load_dcs_records                     # noqa: E402

RNG = np.random.default_rng(0)
ROOT = os.path.join(os.path.dirname(__file__), '..')


# --------------------------------------------------------------------------- data
def load_panel():
    df = pd.read_csv(os.path.join(ROOT, 'data/processed_real/integrated_dataset.csv'))
    raw = load_dcs_records()
    raw = raw[(raw.Season == 'Yala') & (~raw.impossible) & (raw.extent_ha > 0)]

    rows = []
    for (yr, dist), g in raw.groupby(['year', 'District']):
        ext = g['extent_ha'].astype(float).values
        n = len(ext)
        rows.append({
            'Year': int(yr), 'District': dist,
            'extent_ha': ext.sum(),
            'n_months': n,
            # harmonic effective extent -> inverse-variance scale of the target
            'eff_extent': n ** 2 / np.sum(1.0 / ext),
        })
    ext_df = pd.DataFrame(rows)
    df = df.merge(ext_df, on=['Year', 'District'], how='left', validate='one_to_one')
    assert df['eff_extent'].notna().all(), 'missing extents'
    return df.sort_values(['Year', 'District']).reset_index(drop=True)


# ------------------------------------------------------------------- weight schemes
def weights_from(eff, scheme):
    """Observation weights from effective extent. Never touches the target."""
    e = np.asarray(eff, float)
    if scheme == 'equal':
        w = np.ones_like(e)
    elif scheme == 'sqrt':
        w = np.sqrt(e)
    elif scheme == 'lin':
        w = e.copy()
    elif scheme == 'log':
        w = np.log1p(e)
    elif scheme.startswith('sat'):        # w = e / (e + k): inverse-variance with a
        k = float(scheme[3:])             # variance floor (nugget) of phi/k
        w = e / (e + k)
    else:
        raise ValueError(scheme)
    w = np.clip(w, 1e-9, None)
    return w * (len(w) / w.sum())


# ------------------------------------------------------------------------- models
def _wmean(y, w):
    return float(np.sum(w * y) / np.sum(w))


class GrandMean:
    """Weighted climatology: the training-years' inverse-variance-weighted mean."""
    def __init__(self, wscheme='equal'):
        self.wscheme = wscheme

    def fit(self, X, y, meta):
        w = weights_from(meta['eff_extent'].values, self.wscheme)
        self.mu_ = _wmean(y, w)
        return self

    def predict(self, X, meta):
        return np.full(len(meta), self.mu_)


class EBDistrict:
    """Empirical-Bayes district effects, shrunk by their own measurement precision.

    y_id = mu + b_d + e_id,  var(e_id) = phi / E_id,  b_d ~ N(0, tau2).
    Every component (phi, tau2, mu) is estimated by weighted method of moments on
    the training rows only; the held-out year contributes nothing.
    """
    def __init__(self, wscheme='lin', phi_scale=1.0):
        self.wscheme = wscheme
        self.phi_scale = phi_scale

    def fit(self, X, y, meta):
        e = meta['eff_extent'].values.astype(float)
        d = meta['District'].values
        w = weights_from(e, self.wscheme)
        self.mu_ = _wmean(y, w)

        # phi: measurement scale, from within-district scatter deflated by 1/E
        num, den = 0.0, 0.0
        for dd in np.unique(d):
            m = d == dd
            if m.sum() < 2:
                continue
            md = _wmean(y[m], w[m])
            num += np.sum(((y[m] - md) ** 2) * e[m])
            den += m.sum() - 1
        phi = self.phi_scale * (num / den if den > 0 else np.var(y) * np.mean(e))

        # tau2: between-district variance net of the sampling noise in each mean
        eff_d, raw_d, prec_d = {}, {}, {}
        for dd in np.unique(d):
            m = d == dd
            raw_d[dd] = _wmean(y[m], w[m])
            # effective precision of that district mean under the weights used
            ww = w[m] / w[m].sum()
            var_mean = np.sum((ww ** 2) * phi / e[m])
            prec_d[dd] = var_mean
        between = np.var(list(raw_d.values()), ddof=1) if len(raw_d) > 1 else 0.0
        tau2 = max(between - np.mean(list(prec_d.values())), 0.0)

        for dd in raw_d:
            lam = tau2 / (tau2 + prec_d[dd]) if (tau2 + prec_d[dd]) > 0 else 0.0
            eff_d[dd] = lam * (raw_d[dd] - self.mu_)
        self.b_ = eff_d
        return self

    def predict(self, X, meta):
        return np.array([self.mu_ + self.b_.get(dd, 0.0) for dd in meta['District'].values])


class WRidge:
    """Weighted ridge on the k features ranked highest inside the fold.

    Feature ranking, standardisation, target centring and the ridge solve all use
    training rows only. Weights enter through sqrt(w) row scaling (GLS), which is
    exactly the inverse-variance correction the measurement-error model implies.
    """
    def __init__(self, wscheme='lin', k=3, lam=10.0, log_target=False, features=None):
        self.wscheme, self.k, self.lam = wscheme, k, lam
        self.log_target = log_target
        self.features = features or ALL_FEATURES

    def fit(self, X, y, meta):
        w = weights_from(meta['eff_extent'].values, self.wscheme)
        Xa = X[self.features].values.astype(float)
        t = np.log(y) if self.log_target else y.copy()

        sw = np.sqrt(w)
        mu_x = np.average(Xa, axis=0, weights=w)
        sd_x = np.sqrt(np.average((Xa - mu_x) ** 2, axis=0, weights=w))
        sd_x[sd_x < 1e-12] = 1.0
        Z = (Xa - mu_x) / sd_x
        self.mu_x_, self.sd_x_ = mu_x, sd_x

        mu_t = _wmean(t, w)
        tc = t - mu_t
        self.mu_t_ = mu_t

        # weighted correlation ranking, training rows only
        cw = np.abs((sw[:, None] * Z).T @ (sw * tc)) / np.sum(w)
        denom = np.sqrt(np.average(tc ** 2, weights=w))
        cw = cw / max(denom, 1e-12)
        self.idx_ = np.argsort(-cw)[:self.k]

        Zs = Z[:, self.idx_]
        A = sw[:, None] * Zs
        b = sw * tc
        G = A.T @ A + self.lam * np.eye(len(self.idx_))
        self.coef_ = np.linalg.solve(G, A.T @ b)

        # Duan smearing factor for the log back-transform (training residuals only)
        if self.log_target:
            res = tc - Zs @ self.coef_
            self.smear_ = float(np.sum(w * np.exp(res)) / np.sum(w))
        return self

    def predict(self, X, meta):
        Xa = X[self.features].values.astype(float)
        Z = (Xa - self.mu_x_) / self.sd_x_
        p = self.mu_t_ + Z[:, self.idx_] @ self.coef_
        if self.log_target:
            p = np.exp(p) * self.smear_
        return p


class GammaOffset:
    """Predict PRODUCTION with log(extent) as an offset -- IRLS Gamma GLM, log link.

    log(E[production_i]) = log(extent_i) + beta0 + z_i' beta
    so E[yield_i] = exp(beta0 + z_i'beta): the ratio is modelled without ever
    dividing by a small, noisy extent. Gamma's constant coefficient of variation is
    the multiplicative-error assumption; the prior weight n_months accounts for the
    averaging already done inside a cell.
    """
    def __init__(self, k=2, lam=10.0, use_prior_w=True, features=None):
        self.k, self.lam, self.use_prior_w = k, lam, use_prior_w
        self.features = features or ALL_FEATURES

    def fit(self, X, y, meta):
        ext = meta['extent_ha'].values.astype(float)
        prod = y * ext                      # reconstructed production scale
        pw = meta['n_months'].values.astype(float) if self.use_prior_w else np.ones(len(y))
        Xa = X[self.features].values.astype(float)

        mu_x, sd_x = Xa.mean(0), Xa.std(0)
        sd_x[sd_x < 1e-12] = 1.0
        Z = (Xa - mu_x) / sd_x
        self.mu_x_, self.sd_x_ = mu_x, sd_x

        ly = np.log(y)
        c = np.abs(np.corrcoef(np.column_stack([Z, ly]), rowvar=False)[-1, :-1])
        c = np.nan_to_num(c)
        self.idx_ = np.argsort(-c)[:self.k]
        Zs = np.column_stack([np.ones(len(y)), Z[:, self.idx_]])

        beta = np.zeros(Zs.shape[1])
        beta[0] = np.log(np.average(y, weights=pw))
        off = np.log(ext)
        P = self.lam * np.eye(Zs.shape[1]); P[0, 0] = 0.0
        for _ in range(80):
            eta = off + Zs @ beta
            mu = np.exp(np.clip(eta, -20, 20))
            # Gamma/log: W = pw, z = eta - off + (prod - mu)/mu
            z = (Zs @ beta) + (prod - mu) / np.maximum(mu, 1e-9)
            W = pw
            A = Zs * W[:, None]
            new = np.linalg.solve(Zs.T @ A + P, A.T @ z)
            if np.max(np.abs(new - beta)) < 1e-9:
                beta = new
                break
            beta = new
        self.beta_ = beta
        return self

    def predict(self, X, meta):
        Xa = X[self.features].values.astype(float)
        Z = (Xa - self.mu_x_) / self.sd_x_
        Zs = np.column_stack([np.ones(len(Xa)), Z[:, self.idx_]])
        return np.exp(np.clip(Zs @ self.beta_, -20, 20))


class Trimmed:
    """Drop the q noisiest training cells (smallest effective extent), then inner model."""
    def __init__(self, base, q=2):
        self.base, self.q = base, q

    def fit(self, X, y, meta):
        order = np.argsort(meta['eff_extent'].values)
        keep = np.sort(order[self.q:]) if self.q > 0 else np.arange(len(y))
        self.m_ = self.base().fit(X.iloc[keep], y[keep], meta.iloc[keep])
        return self

    def predict(self, X, meta):
        return self.m_.predict(X, meta)


# --------------------------------------------------------------- candidate library
def candidates():
    C = {}
    for ws in ['equal', 'sqrt', 'lin', 'log', 'sat50', 'sat200']:
        C[f'mean[{ws}]'] = lambda ws=ws: GrandMean(ws)
    for ws in ['equal', 'sqrt', 'lin', 'sat50', 'sat200']:
        for ps in [0.5, 1.0, 2.0]:
            C[f'eb[{ws},phi{ps}]'] = lambda ws=ws, ps=ps: EBDistrict(ws, ps)
    for ws in ['equal', 'sqrt', 'lin', 'sat50']:
        for k in [1, 2, 3, 5]:
            for lam in [3.0, 10.0, 30.0, 100.0]:
                for lg in [False, True]:
                    C[f'ridge[{ws},k{k},l{lam:g}{",log" if lg else ""}]'] = (
                        lambda ws=ws, k=k, lam=lam, lg=lg: WRidge(ws, k, lam, lg))
    for k in [1, 2, 3]:
        for lam in [3.0, 10.0, 30.0, 100.0]:
            for pw in [True, False]:
                C[f'gamma[k{k},l{lam:g}{",pw" if pw else ""}]'] = (
                    lambda k=k, lam=lam, pw=pw: GammaOffset(k, lam, pw))
    for q in [2, 4, 6]:
        C[f'trim{q}+mean[lin]'] = lambda q=q: Trimmed(lambda: GrandMean('lin'), q)
        C[f'trim{q}+mean[equal]'] = lambda q=q: Trimmed(lambda: GrandMean('equal'), q)
        C[f'trim{q}+eb[lin]'] = lambda q=q: Trimmed(lambda: EBDistrict('lin', 1.0), q)
    return C


# --------------------------------------------------------------------- evaluation
META_BASE = ['Year', 'District', 'extent_ha', 'eff_extent', 'n_months']
META_OPT = ['se2_raw', 'n_m', 's2']


def _meta_cols(df):
    return META_BASE + [c for c in META_OPT if c in df.columns]


def loyo_predict(model_fn, df, years, feat_cols):
    """Pooled out-of-fold predictions over `years`, everything fitted per fold."""
    pred = np.full(len(df), np.nan)
    mc = _meta_cols(df)
    for yr in years:
        te = df['Year'].values == yr
        tr = (~te) & np.isin(df['Year'].values, years)
        m = model_fn().fit(df.loc[tr, feat_cols], df.loc[tr, TARGET_COLUMN].values,
                           df.loc[tr, mc])
        pred[te] = m.predict(df.loc[te, feat_cols], df.loc[te, mc])
    return pred


def flat_loyo(model_fn, df, feat_cols):
    years = np.sort(df['Year'].unique())
    p = loyo_predict(model_fn, df, years, feat_cols)
    y = df[TARGET_COLUMN].values
    return r2_score(y, p), float(np.sqrt(mean_squared_error(y, p))), p


def nested_loyo(C, df, feat_cols, verbose=True):
    """Honest nested selection: the winner is re-chosen on the inner folds of each
    outer training set, so the held-out year never influences which model is used."""
    y = df[TARGET_COLUMN].values
    years = np.sort(df['Year'].unique())
    pred = np.full(len(df), np.nan)
    chosen = {}
    for yr in years:
        inner_years = years[years != yr]
        best, best_mse = None, np.inf
        for name, fn in C.items():
            try:
                sub = df[df['Year'].isin(inner_years)].reset_index(drop=True)
                p = loyo_predict(fn, sub, inner_years, feat_cols)
                mse = mean_squared_error(sub[TARGET_COLUMN].values, p)
            except Exception:
                continue
            if mse < best_mse - 1e-12:
                best_mse, best = mse, name
        chosen[int(yr)] = best
        te = df['Year'].values == yr
        tr = ~te
        mc = _meta_cols(df)
        m = C[best]().fit(df.loc[tr, feat_cols], y[tr], df.loc[tr, mc])
        pred[te] = m.predict(df.loc[te, feat_cols], df.loc[te, mc])
        if verbose:
            print(f'  outer {yr}: inner-selected {best}  (inner MSE {best_mse:.3f})')
    return r2_score(y, pred), float(np.sqrt(mean_squared_error(y, pred))), pred, chosen


def main():
    df = load_panel()
    feat_cols = df.columns.tolist()
    y = df[TARGET_COLUMN].values
    print(f'panel {df.shape}  target mean {y.mean():.2f} sd {y.std(ddof=1):.2f}')
    print('effective extent (ha): ' +
          ', '.join(f'{r.District[:4]}{r.Year % 100:02d}={r.eff_extent:.0f}'
                    for r in df.itertuples()))

    C = candidates()
    print(f'\n{len(C)} candidate configurations\n')

    # ---- diagnostic leaderboard (NOT the reported number: selecting on this is void)
    rows = []
    for name, fn in C.items():
        try:
            r2, rmse, _ = flat_loyo(fn, df, feat_cols)
        except Exception as e:
            print('fail', name, e); continue
        rows.append((name, r2, rmse))
    lb = pd.DataFrame(rows, columns=['config', 'loyo_r2', 'loyo_rmse']).sort_values('loyo_r2', ascending=False)
    print('=== diagnostic single-loop LOYO leaderboard (selection on this would be leakage) ===')
    print(lb.head(20).to_string(index=False))
    print('...'); print(lb.tail(5).to_string(index=False))
    lb.to_csv(os.path.join(ROOT, 'experiments/me_leaderboard.csv'), index=False)

    # ---- weighted vs unweighted, matched pairs
    print('\n=== weighting effect, matched pairs ===')
    for base in ['mean', 'eb']:
        sel = lb[lb.config.str.startswith(base + '[')]
        print(sel.to_string(index=False))

    # ---- the a-priori configuration, fixed BEFORE seeing the leaderboard
    print('\n=== pre-registered a-priori configuration ===')
    ap = lambda: EBDistrict('lin', 1.0)
    r2a, rmsea, pa = flat_loyo(ap, df, feat_cols)
    print(f'  eb[lin,phi1]  (inverse-variance weighted EB district shrinkage): '
          f'R2 {r2a:+.4f}  RMSE {rmsea:.3f}')
    r2u, rmseu, _ = flat_loyo(lambda: EBDistrict('equal', 1.0), df, feat_cols)
    print(f'  eb[equal,phi1] (same model, UNWEIGHTED):                         '
          f'R2 {r2u:+.4f}  RMSE {rmseu:.3f}')
    r2c, rmsec, _ = flat_loyo(lambda: GrandMean('equal'), df, feat_cols)
    print(f'  climatology reproduction:                                        '
          f'R2 {r2c:+.4f}  RMSE {rmsec:.3f}')
    r2w, rmsew, _ = flat_loyo(lambda: GrandMean('lin'), df, feat_cols)
    print(f'  weighted climatology:                                            '
          f'R2 {r2w:+.4f}  RMSE {rmsew:.3f}')

    # ---- the honest headline: nested LOYO selection
    print('\n=== NESTED LOYO (the reportable number) ===')
    r2n, rmsen, pn, chosen = nested_loyo(C, df, feat_cols)
    print(f'\nNESTED pooled LOYO: R2 {r2n:+.4f}  RMSE {rmsen:.3f}')

    out = {
        'nested': {'r2': r2n, 'rmse': rmsen, 'chosen': chosen},
        'apriori_eb_lin': {'r2': r2a, 'rmse': rmsea},
        'apriori_eb_equal': {'r2': r2u, 'rmse': rmseu},
        'climatology': {'r2': r2c, 'rmse': rmsec},
        'weighted_climatology': {'r2': r2w, 'rmse': rmsew},
        'n_configs': len(C),
    }
    with open(os.path.join(ROOT, 'experiments/me_results.json'), 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))


if __name__ == '__main__':
    main()

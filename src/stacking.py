"""Leak-aware constrained stacking + the forecast-combination-puzzle benchmark.

Novelty note (honest framing): stacking is Wolpert (1992); non-negative sum-to-one ("convex")
combination weights and the observation that a simple equal-weight mean often beats a learned
blend on small samples (the "forecast-combination puzzle", Stock & Watson 2004; Claeskens et al.
2016) are named, textbook results. Our contribution is a *first-for-crop/region application* to
Sri Lankan Big Onion yield over this specific model roster, evaluated leak-aware under nested
Leave-One-Year-Out and judged not only on RMSE/R² but on conformal interval coverage.

Why this is safe on ~28 rows:
  - The equal-weight mean has ZERO fitted parameters — it cannot overfit; it is the anchor and
    the literature's expected winner.
  - The convex simplex constraint (wᵢ ≥ 0, Σwᵢ = 1) strongly regularises the learned blend vs
    an unconstrained OLS stack, and it can zero-out badly-miscalibrated members.
  - It trains NO new base model: it only reads the out-of-fold predictions the pipeline already
    wrote (`oof_*.json`). Its honest, examinable finding: does the simple average beat the
    learned blend on 28 rows?

Nested LOYO: for each held-out year, combination weights are fit ONLY on the other years, then
applied to the held year — so no held-year information leaks into the weights.
"""

import glob
import json
import os

import numpy as np
from scipy.optimize import minimize

from config import RESULTS_DIR
from ml_models import _metrics

# Combiner outputs are themselves oof_*.json; never stack a stack.
_STACK_PREFIX = 'stack'


def _load_base_oof() -> tuple[list, dict, np.ndarray, np.ndarray]:
    """Return (ordered keys, {model: preds_aligned}, y_aligned, years) over base learners.

    Only base models with a COMPLETE (no-NaN) prediction on every shared row are kept, so the
    combination matrix has no gaps. Excluded models are logged honestly.
    """
    payloads = {}
    for path in sorted(glob.glob(os.path.join(RESULTS_DIR, 'oof_*.json'))):
        name = os.path.basename(path)[len('oof_'):-len('.json')]
        if name.startswith(_STACK_PREFIX):
            continue
        with open(path) as f:
            payloads[name] = json.load(f)
    if not payloads:
        return [], {}, np.array([]), np.array([])

    # Common row order taken from the first payload; key = (Year, Season, District).
    def key(r):
        return (int(r['Year']), str(r['Season']), str(r['District']))

    first = next(iter(payloads.values()))
    keys = [key(r) for r in first['rows']]
    y = np.array([float(r['actual']) for r in first['rows']], dtype=float)
    years = np.array([k[0] for k in keys])

    included, excluded = {}, []
    for name, p in payloads.items():
        lut = {key(r): r['predicted'] for r in p['rows']}
        preds = np.array([lut.get(k, np.nan) for k in keys], dtype=float)
        if len(lut) < len(keys) or np.isnan(preds).any():
            excluded.append(name)
        else:
            included[name] = preds

    if excluded:
        print(f'  ⚠ Excluded base models with missing/NaN OOF predictions: {sorted(excluded)}')
    print(f'  Base learners in the committee ({len(included)}): {sorted(included)}')
    return keys, included, y, years


# --- Three combiners: each returns weights given a train slice of (P, y) ------------------
def _w_equal(P, y):
    m = P.shape[1]
    return np.full(m, 1.0 / m)


def _w_inv_rmse(P, y):
    rmse = np.sqrt(np.mean((P - y[:, None]) ** 2, axis=0))
    w = 1.0 / (rmse + 1e-9)
    return w / w.sum()


def _w_convex(P, y):
    """Non-negative, sum-to-one least-squares weights (SLSQP on the simplex)."""
    m = P.shape[1]
    w0 = np.full(m, 1.0 / m)
    obj = lambda w: float(np.mean((P @ w - y) ** 2))
    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},)
    bounds = [(0.0, 1.0)] * m
    try:
        res = minimize(obj, w0, method='SLSQP', bounds=bounds, constraints=cons,
                       options={'maxiter': 500, 'ftol': 1e-9})
        w = np.clip(res.x, 0.0, None)
        s = w.sum()
        return w / s if s > 0 else w0
    except Exception:
        return w0


COMBINERS = {
    'StackMean': _w_equal,
    'StackInvRMSE': _w_inv_rmse,
    'StackConvex': _w_convex,
}


def _nested_loyo(keys, included, y, years):
    """Return {combiner: oof_predictions} plus mean weights per combiner (fit on train folds)."""
    names = sorted(included)
    P = np.column_stack([included[n] for n in names])   # (n_rows, n_models)
    oof = {c: np.full(len(y), np.nan) for c in COMBINERS}
    weight_acc = {c: np.zeros(len(names)) for c in COMBINERS}
    n_folds = 0

    for held in sorted(set(years)):
        tr, te = years != held, years == held
        if tr.sum() < 2:
            continue
        n_folds += 1
        for cname, wfun in COMBINERS.items():
            w = wfun(P[tr], y[tr])
            oof[cname][te] = P[te] @ w
            weight_acc[cname] += w

    mean_weights = {c: dict(zip(names, (weight_acc[c] / max(n_folds, 1)).round(4).tolist()))
                    for c in COMBINERS}
    return oof, mean_weights, names


def _save_stack_oof(cname, preds, keys, y, metrics):
    rows = [{'Year': k[0], 'Season': k[1], 'District': k[2],
             'actual': float(y[i]), 'predicted': float(preds[i])}
            for i, k in enumerate(keys)]
    payload = {'model_name': cname, 'metrics': metrics, 'rows': rows}
    with open(os.path.join(RESULTS_DIR, f'oof_{cname.lower()}.json'), 'w') as f:
        json.dump(payload, f, indent=2)


def run_stacking() -> dict | None:
    print('\n' + '=' * 60)
    print('STACKING — constrained convex blend + forecast-combination-puzzle benchmark')
    print('=' * 60)
    keys, included, y, years = _load_base_oof()
    if len(included) < 2:
        print('  ⚠ Need ≥2 base models with complete OOF predictions — skipping stacking.')
        return None

    oof, mean_weights, names = _nested_loyo(keys, included, y, years)

    combiner_metrics = {}
    for cname, preds in oof.items():
        mask = ~np.isnan(preds)
        metrics = _metrics(y[mask], preds[mask], cname, 0.0, {'weights': mean_weights[cname]})
        combiner_metrics[cname] = metrics
        _save_stack_oof(cname, preds, keys, y, metrics)   # flows into comparison + conformal
        print(f'  {cname:14s} RMSE={metrics["RMSE"]:7.4f}  R²={metrics["R2"]:8.4f}  '
              f'MAE={metrics["MAE"]:.4f}')

    # The forecast-combination-puzzle verdict: does the simple mean beat the learned convex blend?
    mean_r2 = combiner_metrics['StackMean']['R2']
    convex_r2 = combiner_metrics['StackConvex']['R2']
    puzzle = ('equal-weight mean BEATS the learned convex blend (classic forecast-combination '
              'puzzle holds)' if mean_r2 >= convex_r2 else
              'learned convex blend beats the equal-weight mean (puzzle does NOT hold here)')

    summary = {
        'base_models': names,
        'n_rows': int(len(y)),
        'protocol': 'nested Leave-One-Year-Out; weights fit on train years only',
        'combiners': combiner_metrics,
        'mean_weights': mean_weights,
        'forecast_combination_puzzle': puzzle,
        'references': ['Wolpert 1992 (stacked generalization)',
                       'Stock & Watson 2004; Claeskens et al. 2016 (forecast-combination puzzle)',
                       'Breiman 1996 (non-negative stacking weights)'],
    }
    with open(os.path.join(RESULTS_DIR, 'stacking_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'  Forecast-combination puzzle: {puzzle}')
    print(f'  Saved → {os.path.join(RESULTS_DIR, "stacking_summary.json")}')
    return summary


if __name__ == '__main__':
    run_stacking()

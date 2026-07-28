"""Where does big onion yield variance actually live?

Three questions, answered from the corrected panel:

  1. How does total variance split between YEAR, DISTRICT and the rest?
     This is why leave-one-year-out validation destroys every model: it removes the
     dominant component by construction.

  2. How much of the residual is MEASUREMENT ERROR rather than signal anything could
     learn? Each cell's yield is a weighted mean over its month-records, so the spread of
     those months gives a direct estimate of the aggregate's own sampling variance.

  3. What is the implied CEILING on R2 under LOYO once measurement error is subtracted?

Together with the PADR power analysis, this is what turns "our R2 is negative" into a
quantified statement about what the data can and cannot support.
"""

import json
import os

import numpy as np
import pandas as pd

from config import EXCLUDE_IMPOSSIBLE_RECORDS, RESULTS_DIR, TARGET_COLUMN


def _sum_squares(values, groups, grand_mean):
    """Between-group sum of squares for a single factor."""
    total = 0.0
    for level in pd.unique(groups):
        member = groups == level
        total += member.sum() * (values[member].mean() - grand_mean) ** 2
    return float(total)


def decompose(panel):
    """Split total variance into year, district and residual components."""
    y = panel[TARGET_COLUMN].to_numpy(float)
    grand = y.mean()
    total = float(((y - grand) ** 2).sum())

    year_ss = _sum_squares(y, panel['Year'].to_numpy(), grand)
    district_ss = _sum_squares(y, panel['District'].to_numpy(), grand)

    # Two-way additive fit, so the residual is what neither factor explains.
    fitted = (panel.groupby('Year')[TARGET_COLUMN].transform('mean')
              + panel.groupby('District')[TARGET_COLUMN].transform('mean') - grand)
    residual_ss = float(((y - fitted) ** 2).sum())

    return {
        'total_ss': round(total, 2),
        'year_ss': round(year_ss, 2),
        'district_ss': round(district_ss, 2),
        'residual_ss': round(residual_ss, 2),
        'year_pct': round(100 * year_ss / total, 1),
        'district_pct': round(100 * district_ss / total, 1),
        'residual_pct': round(100 * residual_ss / total, 1),
        'target_sd': round(float(y.std(ddof=1)), 3),
    }


def measurement_error(dcs_records, exclude_impossible=None):
    """Estimate each cell's own sampling variance from its month-records.

    A cell's yield is sum(MT)/sum(ha), i.e. an extent-weighted mean of monthly implied
    yields. The weighted spread of those months, divided by Kish's effective sample size,
    estimates the variance of that mean — the irreducible noise in the target itself.

    Must apply the SAME impossible-record filter as the panel, or a single 442 MT/ha
    transcription error dominates the whole estimate.
    """
    exclude = EXCLUDE_IMPOSSIBLE_RECORDS if exclude_impossible is None else exclude_impossible
    if exclude and 'impossible' in dcs_records:
        dcs_records = dcs_records[~dcs_records['impossible']]

    rows = []
    for (year, district), g in dcs_records.groupby(['year', 'District']):
        weights = g['extent_ha'].to_numpy(float)
        monthly = g['implied_mt_per_ha'].to_numpy(float)
        keep = np.isfinite(monthly) & (weights > 0)
        if keep.sum() < 2:
            continue
        weights, monthly = weights[keep], monthly[keep]

        mean = np.average(monthly, weights=weights)
        spread = np.average((monthly - mean) ** 2, weights=weights)
        n_eff = weights.sum() ** 2 / (weights ** 2).sum()
        rows.append({
            'Year': int(year), 'District': district,
            'n_months': int(keep.sum()), 'n_effective': round(float(n_eff), 2),
            'monthly_sd': round(float(np.sqrt(spread)), 3),
            'cell_se': round(float(np.sqrt(spread / n_eff)), 3),
        })

    table = pd.DataFrame(rows)
    mean_var = float((table['cell_se'] ** 2).mean()) if len(table) else float('nan')
    return table, mean_var


def report(panel=None, dcs_records=None, out_dir=None, verbose=True):
    from dcs_panel import build_seasonal_panel, load_dcs_records

    panel = build_seasonal_panel(verbose=False) if panel is None else panel
    dcs_records = load_dcs_records() if dcs_records is None else dcs_records

    split = decompose(panel)
    cells, mean_error_var = measurement_error(dcs_records)

    y = panel[TARGET_COLUMN].to_numpy(float)
    years = panel['Year'].to_numpy()
    total_var = float(y.var(ddof=1))
    within_year = float(np.concatenate(
        [y[years == k] - y[years == k].mean() for k in pd.unique(years)]).var(ddof=1))

    noise_share = mean_error_var / total_var if total_var > 0 else float('nan')
    # Best achievable R2 under LOYO: the year component is unavailable by construction,
    # and measurement error is unlearnable, so both come off the top.
    ceiling = max(0.0, 1 - (split['year_ss'] + mean_error_var * len(y)) / split['total_ss'])

    summary = {
        **split,
        'measurement_error_var': round(mean_error_var, 3),
        'measurement_error_sd': round(float(np.sqrt(mean_error_var)), 3),
        'measurement_share_of_total_var': round(noise_share, 4),
        'within_year_var': round(within_year, 3),
        'measurement_share_of_within_year_var': (
            round(mean_error_var / within_year, 4) if within_year > 0 else None),
        'implied_loyo_r2_ceiling': round(ceiling, 4),
        'n_cells_with_error_estimate': int(len(cells)),
    }

    if verbose:
        _print(summary, cells)

    out_dir = out_dir or RESULTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    cells.to_csv(os.path.join(out_dir, 'measurement_error_by_cell.csv'), index=False)
    with open(os.path.join(out_dir, 'variance_decomposition.json'), 'w') as fh:
        json.dump(summary, fh, indent=2)
    print(f'  ✓ {out_dir}/variance_decomposition.json')
    return summary, cells


def _print(s, cells):
    print('\n=== variance decomposition of the corrected target ===')
    print(f'  total SS            {s["total_ss"]:10.2f}   (sd {s["target_sd"]} MT/ha)')
    print(f'  between YEAR        {s["year_ss"]:10.2f}   {s["year_pct"]:5.1f}%')
    print(f'  between DISTRICT    {s["district_ss"]:10.2f}   {s["district_pct"]:5.1f}%')
    print(f'  residual            {s["residual_ss"]:10.2f}   {s["residual_pct"]:5.1f}%')

    print('\n=== measurement error in the target itself ===')
    print(f'  cells with >=2 month-records : {s["n_cells_with_error_estimate"]}')
    print(f'  mean standard error per cell : {s["measurement_error_sd"]} MT/ha')
    print(f'  share of TOTAL variance      : {100 * s["measurement_share_of_total_var"]:.1f}%')
    if s['measurement_share_of_within_year_var'] is not None:
        print(f'  share of WITHIN-YEAR variance: '
              f'{100 * s["measurement_share_of_within_year_var"]:.1f}%')
    worst = cells.nlargest(4, 'cell_se')[['Year', 'District', 'n_months', 'cell_se']]
    print(f'  noisiest cells:\n{worst.to_string(index=False)}')

    print('\n=== implication for LOYO ===')
    print(f'  Leave-one-year-out removes the {s["year_pct"]:.0f}% year component by design.')
    print(f'  Subtracting measurement error leaves an implied R2 ceiling of '
          f'{s["implied_loyo_r2_ceiling"]:.3f}.')


if __name__ == '__main__':
    report()

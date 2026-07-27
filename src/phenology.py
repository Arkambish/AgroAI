"""Phenological time axis for the onion crop — novelty claim N2.

WHY NOT NDVI
------------
The obvious approach — anchor the season on the satellite green-up curve — cannot work
on this panel, and it is worth stating why rather than quietly failing. Onion occupies
between 0.002% and 0.89% of any district's land area (4 to 1,765 ha inside districts of
199,000-718,000 ha). A district-mean MODIS composite is therefore a measurement of
paddy, forest and scrub. Anchoring was attempted and 25 of 28 district-years fell back
to a calendar window; `plot_ndvi_diagnostic()` renders the evidence. This also explains
the original project's satellite-only ablation result of R2 = -0.67.

WHAT REPLACES IT
----------------
Two real, crop-specific signals:

  1. HARVEST DATE from the DCS records themselves. Production is reported by month, so
     the extent-weighted mean of that distribution is the district-year's harvest date.
     It is genuinely crop-specific and it moves: DOY 228-279, a 51-day span.

  2. THERMAL TIME backwards from harvest. Crop development tracks accumulated heat, not
     calendar days, so the axis is

         tau(t) = (GDD accumulated from planting to t) / GDD_REQUIRED

     with planting located by walking back from harvest until GDD_REQUIRED is met.
     tau = 0 at planting, 1 at harvest, and a hot spell advances the crop faster than a
     cool one — which is the actual physics of phenology.

GDD_REQUIRED is a LEARNABLE PADR parameter, so the alignment itself is estimated from
data rather than assumed. That is what folds N2 into N1: the phenological axis and the
agronomic constants are fitted jointly.
"""

import os

import numpy as np
import pandas as pd

from config import (
    GDD_BASE_TEMP, GDD_REQUIRED_LIT, MONTH_MID_DOY, PHENOLOGY_WINDOW, PLOTS_DIR,
)

# Resolution of the thermal grid weather is resampled onto.
N_TAU = 50

# Hard floor/ceiling on the back-walk so a pathological fit cannot run off the calendar.
MIN_SEASON_DAYS, MAX_SEASON_DAYS = 45, 240


def harvest_dates(dcs_records):
    """Extent-weighted harvest day-of-year per district-year, from the DCS month table.

    Weighted by harvested extent rather than production so a single freak yield figure
    cannot drag the date; months with no harvested area drop out naturally.
    """
    records = dcs_records.copy()
    records['doy'] = records['Month'].astype(str).str.strip().str.title().map(MONTH_MID_DOY)

    rows = []
    for (year, district), g in records.groupby(['year', 'District']):
        weights = g['extent_ha'].to_numpy(float)
        doy = g['doy'].to_numpy(float)
        if weights.sum() <= 0:
            weights = np.ones_like(weights)
        centre = float(np.average(doy, weights=weights))
        rows.append({
            'Year': int(year), 'District': district,
            'harvest_doy': centre,
            'harvest_spread_days': float(np.sqrt(np.average((doy - centre) ** 2, weights=weights))),
            'n_harvest_months': int(len(g)),
        })
    return pd.DataFrame(rows).sort_values(['District', 'Year']).reset_index(drop=True)


def _cell_daily(daily, district, harvest_date, lookback_days=MAX_SEASON_DAYS):
    """Daily weather for the window ending at harvest, allowing a cross-year back-walk."""
    start = harvest_date - pd.Timedelta(days=lookback_days)
    sel = daily[(daily['district'] == district)
                & (daily['date'] > start) & (daily['date'] <= harvest_date)]
    return sel.sort_values('date')


def thermal_tau(cell_daily, gdd_required=GDD_REQUIRED_LIT, base_temp=GDD_BASE_TEMP,
                time_axis='thermal'):
    """Locate planting by walking heat units back from harvest, and build tau.

    `time_axis='calendar'` keeps the same season window but spaces tau evenly in days
    instead of in accumulated heat. That is the control arm for novelty N2: identical
    inputs, identical season, only the developmental clock differs.

    Returns None when the window holds too little heat to reach `gdd_required` — the
    caller then falls back to a fixed-duration season.
    """
    temps = cell_daily['T2M'].to_numpy(float)
    daily_gdd = np.clip(temps - base_temp, 0.0, None)

    # Cumulative heat looking BACKWARDS from harvest.
    back = np.cumsum(daily_gdd[::-1])[::-1]
    reached = np.flatnonzero(back <= gdd_required)
    if not len(reached):
        return None

    start = int(reached[0])
    season = cell_daily.iloc[start:]
    if len(season) < MIN_SEASON_DAYS:
        return None

    gdd = np.clip(season['T2M'].to_numpy(float) - base_temp, 0.0, None)
    accumulated = np.cumsum(gdd)
    total = accumulated[-1]
    if total <= 0:
        return None

    tau = (np.arange(1, len(season) + 1) / len(season) if time_axis == 'calendar'
           else accumulated / total)
    return {
        'season': season,
        'tau': tau,
        'gdd_total': float(total),
        'season_days': int(len(season)),
        'plant_date': season['date'].iloc[0],
    }


def _fixed_duration_fallback(cell_daily, days=110):
    """Calendar-duration season used when the thermal back-walk cannot be satisfied."""
    season = cell_daily.iloc[-days:]
    if len(season) < MIN_SEASON_DAYS:
        return None
    gdd = np.clip(season['T2M'].to_numpy(float) - GDD_BASE_TEMP, 0.0, None)
    accumulated = np.cumsum(gdd)
    total = accumulated[-1] if accumulated[-1] > 0 else 1.0
    return {
        'season': season, 'tau': accumulated / total, 'gdd_total': float(total),
        'season_days': int(len(season)), 'plant_date': season['date'].iloc[0],
    }


def warp_to_thermal_grid(warp, n_tau=N_TAU):
    """Resample a season's daily weather onto a uniform tau grid.

    Rainfall is a FLUX — it is accumulated per bin so total depth is conserved.
    Temperature, humidity and radiation are states, so they are averaged.
    """
    tau, season = warp['tau'], warp['season']
    edges = np.linspace(0.0, 1.0, n_tau + 1)
    idx = np.clip(np.digitize(tau, edges) - 1, 0, n_tau - 1)
    counts = np.bincount(idx, minlength=n_tau)

    grid = {'tau': 0.5 * (edges[:-1] + edges[1:]), 'days_per_bin': counts}
    for col, how in [('T2M', 'mean'), ('T2M_MAX', 'mean'), ('T2M_MIN', 'mean'),
                     ('RH2M', 'mean'), ('ALLSKY_SFC_SW_DWN', 'mean'),
                     ('PRECTOTCORR', 'sum')]:
        totals = np.bincount(idx, weights=season[col].to_numpy(float), minlength=n_tau)
        if how == 'sum':
            grid[col] = totals
        else:
            grid[col] = np.divide(totals, counts, out=np.full(n_tau, np.nan), where=counts > 0)
            grid[col] = pd.Series(grid[col]).interpolate(limit_direction='both').to_numpy()
    return grid


def build_phenology(daily, dcs_records, gdd_required=GDD_REQUIRED_LIT,
                    time_axis='thermal', verbose=True):
    """Thermal-time alignment for every district-year.

    Returns (table, warped) where `warped[(Year, District)]` holds the tau-grid arrays
    that PADR integrates over.
    """
    daily = daily.copy()
    daily['date'] = pd.to_datetime(daily['date'])
    harvests = harvest_dates(dcs_records)

    rows, warped = [], {}
    for _, h in harvests.iterrows():
        harvest_date = (pd.Timestamp(year=int(h['Year']), month=1, day=1)
                        + pd.Timedelta(days=float(h['harvest_doy']) - 1))
        cell = _cell_daily(daily, h['District'], harvest_date)
        if cell.empty:
            continue

        warp = thermal_tau(cell, gdd_required=gdd_required, time_axis=time_axis)
        thermal_ok = warp is not None
        if not thermal_ok:
            warp = _fixed_duration_fallback(cell)
        if warp is None:
            continue

        warped[(int(h['Year']), h['District'])] = warp_to_thermal_grid(warp)
        rows.append({
            'Year': int(h['Year']), 'District': h['District'],
            'harvest_doy': round(float(h['harvest_doy']), 1),
            'harvest_spread_days': round(float(h['harvest_spread_days']), 1),
            'plant_doy': float(warp['plant_date'].dayofyear),
            'season_days': warp['season_days'],
            'gdd_total': round(warp['gdd_total'], 1),
            'thermal_ok': thermal_ok,
        })

    table = pd.DataFrame(rows).sort_values(['District', 'Year']).reset_index(drop=True)
    if verbose:
        _describe(table, gdd_required)
    return table, warped


def _describe(table, gdd_required):
    ok = int(table['thermal_ok'].sum())
    print(f'\n→ Thermal-time phenology at GDD_REQUIRED={gdd_required:.0f} °C-days: '
          f'{len(table)} district-years, {ok} anchored, {len(table) - ok} on fallback')
    print(f'  harvest DOY  {table.harvest_doy.min():.0f}-{table.harvest_doy.max():.0f} '
          f'(median {table.harvest_doy.median():.0f})')
    print(f'  planting DOY {table.plant_doy.min():.0f}-{table.plant_doy.max():.0f} '
          f'(median {table.plant_doy.median():.0f})')
    print(f'  season length {table.season_days.min()}-{table.season_days.max()} days '
          f'(median {table.season_days.median():.0f}) '
          f'— calendar duration VARIES because thermal time does not')


def plot_ndvi_diagnostic(out_path=None):
    """Evidence figure: why the satellite curve was rejected as the phenological anchor.

    Plots district-mean NDVI against the onion share of district area. Belongs in the
    report as justification for the thermal-time design, not as a failure.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    from features_real import _load_ndvi

    ndvi = _load_ndvi()
    districts = ['Anuradhapura', 'Kurunegala', 'Matale', 'Polonnaruwa']
    area_ha = {'Anuradhapura': 717900, 'Kurunegala': 481600,
               'Matale': 199300, 'Polonnaruwa': 329300}

    from dcs_panel import load_dcs_records
    extent = load_dcs_records().groupby(['year', 'District'])['extent_ha'].sum()

    lo, hi = PHENOLOGY_WINDOW
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.5), sharex=True, sharey=True)
    for ax, district in zip(axes.ravel(), districts):
        for year in range(2019, 2026):
            sel = ndvi[(ndvi['District'] == district) & (ndvi['Year'] == year)
                       & (ndvi['Month'].between(lo, hi))].sort_values('Date')
            if sel.empty:
                continue
            ax.plot(sel['Date'].dt.dayofyear, sel['NDVI'], lw=1.2, alpha=0.75, label=str(year))
        share = 100 * extent.get((2021, district), 0) / area_ha[district]
        ax.set_title(f'{district} — onion is {share:.3f}% of district area', fontsize=9)
        ax.grid(alpha=0.25)
        ax.set_ylabel('district-mean NDVI')
    axes[0, 0].legend(ncol=4, fontsize=7, frameon=False)
    for ax in axes[1]:
        ax.set_xlabel('day of year')
    fig.suptitle('District-mean MODIS NDVI cannot resolve a crop on <1% of the land area',
                 fontsize=11)
    fig.tight_layout()

    out_path = out_path or os.path.join(PLOTS_DIR, 'ndvi_not_crop_specific.png')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'  ✓ {out_path}')
    return out_path


if __name__ == '__main__':
    from data_collection.nasa_power import fetch_all
    from dcs_panel import load_dcs_records

    table, grids = build_phenology(fetch_all(), load_dcs_records())
    pd.set_option('display.width', 220)
    print()
    print(table.to_string(index=False))
    plot_ndvi_diagnostic()

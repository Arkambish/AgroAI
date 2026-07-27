"""Authoritative seasonal panel built from the real DCS extent/production records.

Why this module exists
----------------------
The previous modelling input (`onion_unique_per_key.csv`) mixed 74 real month-records
with 50 fabricated ones (`source=synthetic`), and the fabrication reached the TARGET:
`Avg_Yield_MT_per_Ha` was the unweighted mean of monthly yields, ~40% of which were
invented. That target correlates only 0.68 with the properly-defined agronomic yield.

This module rebuilds the panel from `FYP data(manual) - real all datas.csv`, which holds
87 real month-records with `Extent (hectares)` and `Yield (MT)` reported separately, and
defines the target the standard way:

    yield(district, year) = sum(production_MT) / sum(extent_ha)     over the season's months

Every value in the resulting panel traces to a real record. All 28 district-year cells
survive, because the aggregation is over the real months a cell actually has.

Gotchas this module handles (each one silently corrupts the panel otherwise):
  * `Yield (MT)` contains thousands separators ("3,091"), which parse to NaN without
    `thousands=','` — that alone turned Matale 2020 into 0.53 MT/ha.
  * Zero is a MISSING code for `EVI - II`, `NDVI - II` (20 each) and all three soil
    columns (40 — Kurunegala and Matale have no SoilGrids export at all). It is a
    GENUINE zero for `Extent (hectares)` / `Yield (MT)` (7 month-cells with no harvest).
  * District is spelt `Polannaruwa` in this file.
"""

import os

import numpy as np
import pandas as pd

from config import (
    DCS_FILE, DISTRICT_FIXES, EXCLUDE_IMPOSSIBLE_RECORDS, IMPLAUSIBLE_YIELD_RANGE,
    MAX_PHYSICAL_YIELD, MONTH_TO_NUM, OBS_WEIGHT_MODE, TARGET_COLUMN,
)

# Panel column -> raw CSV column, with the rounding each one gets.
_SOIL_COLS = {
    'soil_ph': ('mean pH - 0-5cm', 3),
    'clay_pct': ('mean clay - 0-5cm', 2),
    'sand_pct': ('mean Sand', 2),
}

# Columns where 0 means "not measured", not "measured as zero".
_ZERO_IS_MISSING = ['EVI - II', 'NDVI - II'] + [src for src, _ in _SOIL_COLS.values()]

# SoilGrids exports are stored x10 (ph 58 -> 5.8, clay 276 -> 27.6%).
_SOIL_SCALE = 10.0


def _soil_values(g):
    """Scaled soil means for one cell; NaN where SoilGrids has no export."""
    out = {}
    for name, (src, places) in _SOIL_COLS.items():
        out[name] = round(float(g[src].mean()) / _SOIL_SCALE, places) if g[src].notna().any() else np.nan
    return out


def _index_stats(ndvi, evi):
    """Vegetation-index summaries for one cell, tolerant of missing composites."""
    return {
        'season_mean_ndvi': round(float(ndvi.mean()), 4) if len(ndvi) else np.nan,
        'season_max_ndvi': round(float(ndvi.max()), 4) if len(ndvi) else np.nan,
        'season_min_ndvi': round(float(ndvi.min()), 4) if len(ndvi) else np.nan,
        'ndvi_std': round(float(ndvi.std(ddof=0)), 4) if len(ndvi) > 1 else 0.0,
        'season_mean_evi': round(float(evi.mean()), 4) if len(evi) else np.nan,
    }


def load_dcs_records():
    """Read the raw DCS month-records with correct parsing and missing-value handling."""
    raw = pd.read_csv(DCS_FILE, thousands=',')
    raw.columns = [c.strip() for c in raw.columns]

    raw['District'] = raw['District'].astype(str).str.strip().str.title().replace(DISTRICT_FIXES)
    raw['Season'] = raw['Season'].astype(str).str.strip().str.title()
    raw['month_num'] = raw['Month'].astype(str).str.strip().str.title().map(MONTH_TO_NUM)

    raw['extent_ha'] = pd.to_numeric(raw['Extent (hectares)'], errors='coerce')
    raw['production_mt'] = pd.to_numeric(raw['Yield (MT)'], errors='coerce')

    for col in _ZERO_IS_MISSING:
        raw[col] = pd.to_numeric(raw[col], errors='coerce').replace(0.0, np.nan)
    for col in ['Temperature', 'Rainfall', 'Humidity', 'EVI - I', 'NDVI - I']:
        raw[col] = pd.to_numeric(raw[col], errors='coerce')

    unparsed = raw['extent_ha'].isna().sum() + raw['production_mt'].isna().sum()
    if unparsed:
        raise ValueError(f'{unparsed} extent/production values failed to parse — check the CSV')

    # Implied yield of the individual month-record — the diagnostic that exposes
    # transcription errors, e.g. Matale October 2025 at 30 ha / 13,271.7 MT = 442 MT/ha.
    raw['implied_mt_per_ha'] = np.where(
        raw['extent_ha'] > 0, raw['production_mt'] / raw['extent_ha'].replace(0, np.nan), np.nan)
    raw['impossible'] = raw['implied_mt_per_ha'] > MAX_PHYSICAL_YIELD

    return raw.sort_values(['District', 'Season', 'year', 'month_num']).reset_index(drop=True)


def _observation_weights(extent_ha, mode=None):
    """Relative trust in each cell's yield estimate, normalised to mean 1.

    A district-year covering 4 ha gives a far noisier yield estimate than one covering
    1,765 ha. Weighting by extent is standard in crop-yield econometrics. Plain area is
    too aggressive here (a 440x span would erase Kurunegala entirely, losing a district),
    so `sqrt_extent` is the default compromise.
    """
    mode = mode or OBS_WEIGHT_MODE
    area = np.asarray(extent_ha, dtype=float)
    if mode == 'equal':
        w = np.ones_like(area)
    elif mode == 'sqrt_extent':
        w = np.sqrt(np.clip(area, 0.0, None))
    elif mode == 'extent':
        w = np.clip(area, 0.0, None)
    else:
        raise ValueError(f'unknown OBS_WEIGHT_MODE: {mode!r}')
    total = w.sum()
    if total <= 0:
        return np.ones_like(area)
    return w * (len(w) / total)


def build_seasonal_panel(verbose=True, exclude_impossible=None):
    """Aggregate the DCS month-records to one row per (Year, Season, District).

    Returns a DataFrame with the area-weighted target, provenance columns
    (extent_ha, production_mt, n_months, months), observation weights, and the
    real monthly covariates aggregated to the seasonal grain. Soil columns stay
    NaN where SoilGrids has no export — they are NOT back-filled with fake values.

    Month-records implying more than MAX_PHYSICAL_YIELD are dropped by default; the
    cell survives on its remaining months. Pass exclude_impossible=False for the
    uncleaned sensitivity arm.
    """
    raw = load_dcs_records()

    exclude = EXCLUDE_IMPOSSIBLE_RECORDS if exclude_impossible is None else exclude_impossible
    n_bad = int(raw['impossible'].sum())
    if exclude and n_bad:
        if verbose:
            worst = raw.loc[raw['impossible']].nlargest(1, 'implied_mt_per_ha').iloc[0]
            print(f'\n→ Excluding {n_bad} month-record(s) above {MAX_PHYSICAL_YIELD:.0f} MT/ha '
                  f'(worst: {worst["District"]} {worst["Month"]} {int(worst["year"])} = '
                  f'{worst["implied_mt_per_ha"]:.0f} MT/ha)')
        raw = raw[~raw['impossible']].reset_index(drop=True)

    rows = []
    for (year, district, season), g in raw.groupby(['year', 'District', 'Season']):
        g = g.sort_values('month_num')
        extent = float(g['extent_ha'].sum())
        production = float(g['production_mt'].sum())

        # Both NDVI/EVI composites per month are real observations; stack them.
        ndvi = pd.concat([g['NDVI - I'], g['NDVI - II']]).dropna().astype(float)
        evi = pd.concat([g['EVI - I'], g['EVI - II']]).dropna().astype(float)
        temp, rain, hum = g['Temperature'], g['Rainfall'], g['Humidity']

        rows.append({
            'Year': int(year), 'Season': season, 'District': district,
            TARGET_COLUMN: production / extent if extent > 0 else np.nan,
            # Provenance — every downstream claim can be traced back through these.
            'extent_ha': round(extent, 2),
            'production_mt': round(production, 2),
            'n_months': int(len(g)),
            'months': ','.join(g['Month'].astype(str)),
            'n_ndvi_obs': int(len(ndvi)),
            # Real seasonal covariates
            'season_avg_temp': round(float(temp.mean()), 3),
            'season_total_rainfall': round(float(rain.sum()), 3),
            'season_avg_humidity': round(float(hum.mean()), 3),
            'temp_range': round(float(temp.max() - temp.min()), 3),
            'max_monthly_rainfall': round(float(rain.max()), 3),
            **_index_stats(ndvi, evi),
            # Soil — NaN where SoilGrids has no export (Kurunegala, Matale)
            **_soil_values(g),
        })

    panel = pd.DataFrame(rows).sort_values(['District', 'Season', 'Year']).reset_index(drop=True)
    panel['obs_weight'] = _observation_weights(panel['extent_ha'].values).round(4)

    if verbose:
        print(f'\n→ DCS seasonal panel: {len(panel)} cells from {len(raw)} real month-records')
        print('  target = sum(production_MT) / sum(extent_ha)')
        print(f'  {TARGET_COLUMN}: mean {panel[TARGET_COLUMN].mean():.2f} '
              f'sd {panel[TARGET_COLUMN].std():.2f} '
              f'range {panel[TARGET_COLUMN].min():.2f}-{panel[TARGET_COLUMN].max():.2f}')
        print(f'  weights ({OBS_WEIGHT_MODE}): '
              f'{panel["obs_weight"].min():.3f}-{panel["obs_weight"].max():.3f}')
    return panel


def _cell_flags(r):
    """Everything questionable about one seasonal cell."""
    lo, hi = IMPLAUSIBLE_YIELD_RANGE
    cell = f"{int(r['Year'])} {r['District']}"
    provenance = f"{r['production_mt']:.1f} MT / {r['extent_ha']:.1f} ha"
    out = []

    if r[TARGET_COLUMN] > hi:
        out.append((cell, 'yield_above_plausible',
                    f'{r[TARGET_COLUMN]:.2f} MT/ha from {provenance} (plausible <= {hi})'))
    elif r[TARGET_COLUMN] < lo:
        out.append((cell, 'yield_below_plausible',
                    f'{r[TARGET_COLUMN]:.2f} MT/ha from {provenance} (plausible >= {lo})'))
    if r['extent_ha'] < 10:
        out.append((cell, 'tiny_extent',
                    f"{r['extent_ha']:.1f} ha — yield estimate is inherently noisy"))
    if r['n_months'] <= 2:
        out.append((cell, 'thin_month_coverage',
                    f"only {r['n_months']} month-record(s): {r['months']}"))
    out.extend((cell, 'missing_soil', f'{col} has no SoilGrids export')
               for col in _SOIL_COLS if pd.isna(r[col]))
    return out


def _record_flags(raw):
    """Month-records that are physically impossible — where transcription errors live."""
    return [(f"{int(r['year'])} {r['District']}", 'impossible_month_record',
             f"{r['Month']}: {r['production_mt']:.1f} MT / {r['extent_ha']:.1f} ha "
             f"= {r['implied_mt_per_ha']:.0f} MT/ha (max physical {MAX_PHYSICAL_YIELD:.0f}) "
             f'— verify against the DCS publication')
            for _, r in raw[raw['impossible']].iterrows()]


def data_quality_report(panel=None, out_path=None):
    """Flag everything an examiner could reasonably challenge, and write it to disk.

    Covers both grains: individual month-records that are physically impossible, and
    seasonal cells that are merely questionable. Nothing here is silently corrected —
    the report is the audit trail, and the flagged cells need checking against the
    original DCS publication.
    """
    panel = build_seasonal_panel(verbose=False) if panel is None else panel

    flags = _record_flags(load_dcs_records())
    for _, r in panel.iterrows():
        flags.extend(_cell_flags(r))

    report = (pd.DataFrame(flags, columns=['cell', 'flag', 'detail'])
              .sort_values(['flag', 'cell']).reset_index(drop=True))

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        report.to_csv(out_path, index=False)

    print(f'\n→ Data-quality report: {len(report)} flags across '
          f'{report["cell"].nunique()} of {len(panel)} cells')
    for flag, g in report.groupby('flag'):
        shown = sorted(g['cell'].unique())[:6]
        print(f'  {flag:24s} {len(g):3d}  ({", ".join(shown)}'
              f'{"..." if g["cell"].nunique() > 6 else ""})')
    if out_path:
        print(f'  ✓ written to {out_path}')
    return report


if __name__ == '__main__':
    p = build_seasonal_panel()
    print()
    print(p[['Year', 'District', TARGET_COLUMN, 'extent_ha', 'production_mt',
             'n_months', 'obs_weight']].to_string(index=False))
    data_quality_report(p, out_path='outputs/results_real/data_quality_report.csv')

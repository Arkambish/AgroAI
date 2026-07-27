"""Report figures for the PADR analysis.

Each figure carries one claim. In order of importance to the thesis:

  1. variance_ceiling   — why R2 > 0.75 was never attainable on this panel
  2. stress_vs_yield    — the stress index cannot move far enough to explain the target
  3. beta_curve         — the estimated phenological sensitivity, with fold spread
  4. power_curve        — the weather signal PADR would have detected, had one existed
  5. scoreboard         — every model against the achievable band

Palette is the validated 4-slot categorical set (blue/orange/aqua/yellow); aqua and
yellow sit below 3:1 on the light surface, so every mark using them is directly labelled.
"""

import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import PLOTS_DIR, RESULTS_DIR, TARGET_COLUMN

SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
INK, INK_2, MUTED = '#0b0b0b', '#52514e', '#898781'
GRID, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'
GOOD, CRITICAL = '#0ca30c', '#d03b3b'


def _style(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(BASELINE)
    ax.tick_params(colors=MUTED, labelsize=9)
    if title:
        ax.set_title(title, color=INK, fontsize=11, loc='left', pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK_2, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK_2, fontsize=9)
    return ax


def _save(fig, name, out_dir=None):
    out_dir = out_dir or PLOTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)
    print(f'  ✓ {path}')
    return path


def _load(name):
    path = os.path.join(RESULTS_DIR, name)
    if not os.path.exists(path):
        return None
    return json.load(open(path)) if name.endswith('.json') else pd.read_csv(path)


def variance_ceiling():
    """The headline: where the variance is, and what LOYO leaves behind."""
    summary = _load('variance_decomposition.json')
    if summary is None:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2),
                                   gridspec_kw={'width_ratios': [1.15, 1]})

    parts = ['between YEAR', 'between DISTRICT', 'residual']
    shares = [summary['year_pct'], summary['district_pct'], summary['residual_pct']]
    colours = [SERIES[0], SERIES[2], MUTED]
    bars = ax1.barh(parts, shares, color=colours, height=0.55, zorder=3)
    for bar, share in zip(bars, shares):
        ax1.text(share + 1.2, bar.get_y() + bar.get_height() / 2, f'{share:.1f}%',
                 va='center', color=INK, fontsize=10, fontweight='medium')
    ax1.set_xlim(0, max(shares) * 1.22)
    ax1.invert_yaxis()
    _style(ax1, 'Where yield variance lives', 'share of total variance (%)')
    ax1.annotate('leave-one-year-out\nremoves this by design',
                 xy=(shares[0] * 0.5, 0), xytext=(shares[0] * 0.42, 1.35),
                 color=CRITICAL, fontsize=8.5, ha='center',
                 arrowprops=dict(arrowstyle='->', color=CRITICAL, lw=1.2))

    ceiling = summary['implied_loyo_r2_ceiling']
    levels = ['original\ntarget', 'implied\nceiling', 'best model\nachieved']
    scoreboard = _load('padr_comparison.csv')
    best = float(scoreboard.loc[scoreboard['achievable'], 'R2'].max()) if scoreboard is not None else np.nan
    values = [0.75, ceiling, best]
    colours = [CRITICAL, SERIES[3], SERIES[0]]
    bars = ax2.bar(levels, values, color=colours, width=0.5, zorder=3)
    for bar, value in zip(bars, values):
        offset = 0.03 if value >= 0 else -0.06
        ax2.text(bar.get_x() + bar.get_width() / 2, value + offset, f'{value:.3f}',
                 ha='center', color=INK, fontsize=10, fontweight='medium')
    ax2.axhline(0, color=BASELINE, lw=1.2, zorder=2)
    _style(ax2, 'Attainable R² under LOYO', ylabel='R²')
    ax2.set_ylim(min(values) - 0.18, 1.02)
    # Sits above the two right-hand bars (ceiling 0.16, achieved negative), clear of the
    # 0.750 bar and its label on the left.
    ax2.text(0.98, 0.66,
             f'measurement error alone is\n'
             f'{100 * summary["measurement_share_of_within_year_var"]:.0f}% of within-year variance',
             transform=ax2.transAxes, fontsize=8.5, color=INK_2, va='top', ha='right')

    fig.suptitle('The R² > 0.75 target was not difficult — it was unattainable',
                 fontsize=12.5, color=INK, x=0.02, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, 'variance_ceiling.png')


def stress_vs_yield(stress_by_cell=None):
    """Proof the agro-climatic channel is inert: S barely moves, yield moves a lot."""
    ablation = _load('padr_ablation.csv')
    if ablation is None or stress_by_cell is None:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

    frame = stress_by_cell
    z_stress = (frame['S'] - frame['S'].mean()) / frame['S'].mean()
    z_yield = (frame['actual'] - frame['actual'].mean()) / frame['actual'].mean()
    for i, (district, g) in enumerate(frame.groupby('District')):
        idx = g.index
        ax1.scatter(100 * z_stress[idx], 100 * z_yield[idx], s=54, zorder=3,
                    color=SERIES[i % len(SERIES)], label=district,
                    edgecolor=SURFACE, linewidth=1.4)
    ax1.axhline(0, color=BASELINE, lw=1)
    ax1.axvline(0, color=BASELINE, lw=1)
    _style(ax1, 'Stress index vs observed yield',
           'stress index, % from mean', 'observed yield, % from mean')
    ax1.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc='upper left')
    ax1.set_xlim(-60, 60)

    arms = ablation.sort_values('stress_cv_pct')
    target_cv = float(ablation['target_cv_pct'].iloc[0])
    bars = ax2.barh(arms['arm'], arms['stress_cv_pct'], color=SERIES[0],
                    height=0.6, zorder=3)
    for bar, value in zip(bars, arms['stress_cv_pct']):
        ax2.text(value + 0.4, bar.get_y() + bar.get_height() / 2, f'{value:.1f}%',
                 va='center', color=INK, fontsize=9)
    ax2.axvline(target_cv, color=CRITICAL, lw=1.6, ls='--', zorder=4)
    ax2.text(target_cv - 0.8, -0.6, f'observed yield CV {target_cv:.0f}%',
             color=CRITICAL, fontsize=9, ha='right')
    ax2.set_xlim(0, target_cv * 1.12)
    _style(ax2, 'Variation each mechanism can generate',
           'coefficient of variation of the stress index (%)')

    fig.suptitle('A model whose output varies 8% cannot explain a target that varies 35%',
                 fontsize=12.5, color=INK, x=0.02, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, 'stress_vs_yield.png')


def beta_curve(fold_params=None, basis=None, tau=None):
    """Estimated phenological sensitivity beta(tau), with the spread across folds."""
    if fold_params is None or basis is None:
        return None
    from padr import N_BETA, beta_weights

    dtau = float(tau[1] - tau[0])
    curves = np.array([
        beta_weights(np.array([p[f'beta_{i}'] for i in range(N_BETA)]), basis, dtau)
        for p in fold_params.values()])

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.fill_between(tau, curves.min(0), curves.max(0), color=SERIES[0], alpha=0.16,
                    zorder=2, label='range across LOYO folds')
    ax.plot(tau, curves.mean(0), color=SERIES[0], lw=2.2, zorder=4, label='mean β(τ)')
    ax.axhline(1.0, color=MUTED, lw=1.2, ls=':', zorder=3)
    ax.text(0.99, 1.03, 'uniform weighting', color=MUTED, fontsize=8.5, ha='right')

    for position, label in [(0.0, 'planting'), (0.5, 'bulb initiation'), (1.0, 'harvest')]:
        ax.axvline(position, color=BASELINE, lw=1, zorder=1)
        ax.text(position, ax.get_ylim()[1] * 0.02, f' {label}', rotation=90,
                fontsize=8, color=MUTED, va='bottom')

    _style(ax, 'Estimated phenological sensitivity β(τ)',
           'thermal phenological time τ  (0 = planting, 1 = harvest)',
           'relative weight')
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2)
    ax.set_xlim(0, 1)
    fig.tight_layout()
    return _save(fig, 'beta_curve.png')


def power_curve():
    """Minimum weather signal PADR could have detected at n=28."""
    power = _load('padr_power_analysis.csv')
    if power is None:
        return None

    fig, ax = plt.subplots(figsize=(8, 4.2))
    share = 100 * power['weather_share_of_variance']
    ax.fill_between(share, power['R2_mean'] - power['R2_sd'],
                    power['R2_mean'] + power['R2_sd'],
                    color=SERIES[0], alpha=0.16, zorder=2)
    ax.plot(share, power['R2_mean'], color=SERIES[0], lw=2.2, marker='o', ms=7,
            zorder=4, label='PADR on simulated data')
    ax.axhline(0, color=BASELINE, lw=1.2, zorder=3)

    detected = power[power['detected']]
    if len(detected):
        threshold = 100 * float(detected['weather_share_of_variance'].min())
        ax.axvline(threshold, color=GOOD, lw=1.6, ls='--', zorder=3)
        ax.text(threshold + 1, ax.get_ylim()[0] * 0.85,
                f'  detectable from {threshold:.0f}% upward',
                color=GOOD, fontsize=9)

    observed = _load('padr_comparison.csv')
    if observed is not None:
        real = float(observed.loc[observed['Model'] == 'PADR', 'R2'].iloc[0])
        ax.axhline(real, color=CRITICAL, lw=1.6, ls=':', zorder=3)
        ax.text(share.max(), real - 0.06, f'PADR on the real panel: R² = {real:.3f}',
                color=CRITICAL, fontsize=9, ha='right')

    _style(ax, 'What weather signal would PADR have found?',
           'share of yield variance genuinely driven by weather (%)', 'LOYO R²')
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2, loc='upper left')
    fig.tight_layout()
    return _save(fig, 'power_curve.png')


def scoreboard():
    """Every model against the achievable band."""
    table = _load('padr_comparison.csv')
    summary = _load('variance_decomposition.json')
    if table is None:
        return None

    table = table.sort_values('R2')
    colours = [MUTED if not ok else (SERIES[1] if name == 'PADR' else SERIES[0])
               for name, ok in zip(table['Model'], table['achievable'])]

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    bars = ax.barh(table['Model'], table['R2'], color=colours, height=0.6, zorder=3)
    for bar, value in zip(bars, table['R2']):
        offset = 0.02 if value >= 0 else -0.02
        ax.text(value + offset, bar.get_y() + bar.get_height() / 2, f'{value:+.3f}',
                va='center', ha='left' if value >= 0 else 'right',
                color=INK, fontsize=9)
    ax.axvline(0, color=BASELINE, lw=1.2, zorder=2)

    if summary is not None:
        ceiling = summary['implied_loyo_r2_ceiling']
        ax.axvline(ceiling, color=GOOD, lw=1.6, ls='--', zorder=4)
        ax.text(ceiling, len(table) - 0.3, f' ceiling {ceiling:.3f}',
                color=GOOD, fontsize=9, va='top')

    _style(ax, 'LOYO R² — every model, on the corrected target', 'R²')
    ax.text(0.01, -0.16, 'grey = Oracle_YearMean, not achievable under LOYO',
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    fig.tight_layout()
    return _save(fig, 'padr_scoreboard.png')


def learned_constants(fold_params=None):
    """Estimated agronomic coefficients against their published values.

    The positive finding: the published coefficients imply a far more weather-sensitive
    crop than the data support, and estimating them locally is what reveals it.
    """
    if fold_params is None:
        path = os.path.join(RESULTS_DIR, 'padr_params.json')
        if not os.path.exists(path):
            return None
        fold_params = json.load(open(path))

    from padr import PARAM_SPEC
    frame = pd.DataFrame(fold_params).T
    shown = [(n, lit, lo, hi) for n, lit, (lo, hi), _ in PARAM_SPEC
             if n in frame and not n.startswith(('gamma', 'P_crit'))]

    fig, axes = plt.subplots(1, len(shown), figsize=(2.05 * len(shown), 4.0))
    for ax, (name, lit, lo, hi) in zip(np.atleast_1d(axes), shown):
        values = frame[name].astype(float)
        ax.axhspan(lo, hi, color=GRID, alpha=0.55, zorder=1)
        ax.errorbar([0], [values.mean()], yerr=[values.std()], fmt='o', ms=11,
                    color=SERIES[0], capsize=6, lw=2, zorder=4, label='estimated')
        ax.axhline(lit, color=SERIES[1], lw=2, ls='--', zorder=3, label='literature')
        ax.set_xlim(-0.6, 0.6)
        ax.set_ylim(lo - 0.05 * (hi - lo), hi + 0.05 * (hi - lo))
        ax.set_xticks([])
        ax.set_title(name, fontsize=10, color=INK)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.set_facecolor(SURFACE)
        for side in ('top', 'right', 'bottom'):
            ax.spines[side].set_visible(False)
        ax.spines['left'].set_color(BASELINE)
        # Bottom edge, clear of the marker and its error bar wherever they land.
        delta = values.mean() - lit
        ax.text(0, lo, f'{delta:+.2f}', ha='center', va='bottom', fontsize=9,
                color=INK_2)
    np.atleast_1d(axes)[-1].legend(frameon=False, fontsize=8.5, labelcolor=INK_2,
                                   loc='upper center')
    fig.suptitle('Agronomic coefficients: estimated vs published  '
                 '(shaded band = admissible range, bars = spread across folds)',
                 fontsize=11.5, color=INK, x=0.02, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return _save(fig, 'learned_constants.png')


def ablation_claims():
    """Each design claim as a delta against its own control — including the nulls."""
    table = _load('padr_ablation.csv')
    if table is None:
        return None

    rows = table.set_index('arm')['R2']
    claims = [
        ('N1  learn the physics', 'full', 'fixed_physics'),
        ('N4  moderate vs heavy shrinkage', 'full', 'strong_shrinkage'),
        ('β(τ) learned vs flat', 'full', 'flat_beta'),
        ('N2  thermal vs calendar time', 'full', 'calendar_time'),
        ('N4  moderate vs no shrinkage', 'full', 'no_shrinkage'),
        ('N3  waterlogging term', 'full', 'no_waterlogging'),
    ]
    labels, deltas = [], []
    for label, treatment, control in claims:
        if treatment in rows and control in rows:
            labels.append(label)
            deltas.append(float(rows[treatment] - rows[control]))

    order = np.argsort(deltas)
    labels = [labels[i] for i in order]
    deltas = [deltas[i] for i in order]
    colours = [GOOD if d > 0.05 else (CRITICAL if d < 0 else MUTED) for d in deltas]

    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    bars = ax.barh(labels, deltas, color=colours, height=0.6, zorder=3)
    for bar, value in zip(bars, deltas):
        ax.text(value + (0.03 if value >= 0 else -0.03),
                bar.get_y() + bar.get_height() / 2, f'{value:+.3f}',
                va='center', ha='left' if value >= 0 else 'right',
                color=INK, fontsize=9.5)
    ax.axvline(0, color=BASELINE, lw=1.2, zorder=2)
    _style(ax, 'Every design claim, against its own control', 'Δ R² vs control')
    ax.set_xlim(min(deltas) - 0.25, max(deltas) + 0.25)
    ax.text(0.01, -0.17, 'green = supported   ·   grey = neutral   ·   red = harmful',
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    fig.tight_layout()
    return _save(fig, 'ablation_claims.png')


def build_all():
    """Render everything that has data on disk."""
    print(f'\n→ Figures → {PLOTS_DIR}')
    made = [variance_ceiling(), scoreboard(), power_curve()]

    stress, folds, basis, tau = _stress_frame()
    if stress is not None:
        made.append(stress_vs_yield(stress))
        made.append(beta_curve(folds, basis, tau))
    return [m for m in made if m]


def _stress_frame():
    """Recompute the per-cell stress index using the mean fitted parameters."""
    params_path = os.path.join(RESULTS_DIR, 'padr_params.json')
    if not os.path.exists(params_path):
        return None, None, None, None

    from data_collection.nasa_power import fetch_all
    from dcs_panel import load_dcs_records
    from features_real import build_modelling_frame
    from padr import _spec, prepare_cells, stress_index
    from phenology import build_phenology

    frame = build_modelling_frame(verbose=False)
    _, warped = build_phenology(fetch_all(), load_dcs_records(), verbose=False)
    keys = list(zip(frame['Year'].astype(int), frame['District']))
    districts = sorted(frame['District'].unique())
    cells = prepare_cells(warped, districts, keys)

    folds = json.load(open(params_path))
    names = [n for n, *_ in _spec(len(districts))]
    mean_params = np.array([np.mean([folds[k][n] for k in folds]) for n in names])

    out = pd.DataFrame({
        'Year': frame['Year'], 'District': frame['District'],
        'actual': frame[TARGET_COLUMN],
        'S': [stress_index(mean_params, c) for c in cells],
    })
    return out, folds, cells[0]['basis'], cells[0]['tau']


if __name__ == '__main__':
    build_all()

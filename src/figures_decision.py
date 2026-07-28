"""The signature figure for the storage-coupled decision analysis.

One claim, two panels:

  Panel A — the scissors. Required forecast skill rho*(tau) against the skill this project
            actually attains. Calibrated, the requirement sits below what we have, so acting on
            the forecast pays. Uncalibrated, the requirement sits above it, so acting on the
            same forecast is worse than ignoring it.
  Panel B — the size of that gap in decision-loss terms at the project's real skill (rho = 0.258).

The point of the figure is that the difference between a useful forecast and a harmful one here
is a one-line in-fold recalibration, not a better architecture.

Run:  DATA_VARIANT=real PYTHONPATH=src python src/figures_decision.py
"""

import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from config import PLOTS_DIR, RESULTS_DIR
from figures_padr import _save, _style, BASELINE, CRITICAL, INK, INK_2, MUTED, SERIES

CALIBRATED, UNCALIBRATED = SERIES[0], SERIES[1]

# Where Big Onion's critical fractile actually lands, from decision_loss.py.
ONION_TAU_LO, ONION_TAU_HI = 0.649, 0.960


def _load():
    path = os.path.join(RESULTS_DIR, 'decision_loss.json')
    with open(path) as fh:
        return json.load(fh)


def _series(frontier, taus):
    """Frontier values as a float array, with 'never pays' lifted above the plotted range."""
    return np.array([1.05 if frontier[str(t)] is None else frontier[str(t)] for t in taus])


def scissors_figure(report):
    taus = [float(t) for t in report['break_even_frontier_rho_star__calibrated']]
    cal = _series(report['break_even_frontier_rho_star__calibrated'], taus)
    unc = _series(report['break_even_frontier_rho_star__uncalibrated'], taus)
    attainable = report['attainable_skill']['loyo_correlation_rho']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4))

    # --- Panel A: the scissors ---
    _style(ax1,
           title='A. Required forecast skill vs what this design attains',
           xlabel='Critical fractile τ  (set by curing humidity and export-ban state)',
           ylabel='Forecast–truth correlation ρ')
    ax1.axvspan(ONION_TAU_LO, min(ONION_TAU_HI, max(taus)), color='#f0efe8', zorder=1)
    ax1.text(max(taus) - 0.005, 0.55, 'where Big Onion actually sits',
             fontsize=8, color=MUTED, ha='right', va='center', zorder=4)

    ax1.plot(taus, unc, color=UNCALIBRATED, lw=2, marker='o', ms=5, zorder=5,
             label='required ρ*  —  forecast used raw')
    ax1.plot(taus, cal, color=CALIBRATED, lw=2, marker='o', ms=5, zorder=5,
             label='required ρ*  —  forecast recalibrated in-fold')
    ax1.axhline(attainable, color=CRITICAL, lw=1.8, ls='--', zorder=4)
    ax1.text(max(taus), attainable + 0.018, f'attainable ρ = {attainable:.3f}',
             color=CRITICAL, fontsize=8.5, ha='right', va='bottom', zorder=6)

    ax1.set_ylim(-0.03, 0.63)
    ax1.set_xlim(min(taus) - 0.01, max(taus) + 0.01)
    leg = ax1.legend(frameon=False, fontsize=8.5, loc='upper left')
    for txt in leg.get_texts():
        txt.set_color(INK_2)

    # --- Panel B: what that costs, at the project's real skill ---
    _style(ax2,
           title=f'B. Decision-loss change at the project’s actual skill (ρ = {attainable:.3f})',
           xlabel='Critical fractile τ',
           ylabel='Reduction in expected decision loss')
    cal_surface = report['decision_skill_surface__calibrated']
    unc_surface = report['decision_skill_surface__uncalibrated']

    def at_rho(surface):
        grid = sorted(float(r) for r in next(iter(surface.values())))
        return np.array([
            np.interp(attainable, grid, [surface[str(t)][str(r)] for r in grid])
            for t in taus
        ])

    cal_gain, unc_gain = at_rho(cal_surface), at_rho(unc_surface)
    ax2.axhline(0, color=BASELINE, lw=1.2, zorder=2)
    ax2.plot(taus, unc_gain, color=UNCALIBRATED, lw=2, marker='o', ms=5, zorder=5)
    ax2.plot(taus, cal_gain, color=CALIBRATED, lw=2, marker='o', ms=5, zorder=5)
    ax2.text(taus[-1], cal_gain[-1] + 0.03, f'recalibrated  {cal_gain[-1]:+.1%}',
             color=INK_2, fontsize=8.5, ha='right', va='bottom', zorder=6)
    ax2.text(taus[-1], unc_gain[-1] - 0.05, f'raw  {unc_gain[-1]:+.1%}',
             color=INK_2, fontsize=8.5, ha='right', va='top', zorder=6)
    ax2.yaxis.set_major_formatter(lambda v, _: f'{v:+.0%}')
    ax2.set_xlim(min(taus) - 0.01, max(taus) + 0.01)

    fig.suptitle(
        'A forecast this weak still pays — but only if it is recalibrated first',
        fontsize=12.5, color=INK, x=0.02, ha='left')
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return _save(fig, 'decision_skill_scissors.png')


def leadtime_figure():
    """Skill against forecast issue point, with the weather uncertainty that shrinks with it."""
    path = os.path.join(RESULTS_DIR, 'forecast_leadtime.json')
    if not os.path.exists(path):
        print('  (skipped lead-time figure — run src/forecast_leadtime.py first)')
        return None
    with open(path) as fh:
        res = json.load(fh)

    floor = res.pop('climatology (no features)', None)
    labels = list(res)
    x = [res[k]['n_months_observed'] for k in labels]
    r2 = [res[k]['r2'] for k in labels]
    band = [res[k]['mean_weather_band_90pct'] / 2 for k in labels]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4))

    _style(ax1,
           title='A. Does watching the season unfold help?',
           xlabel='Months of the season already observed when the forecast is issued',
           ylabel='Leave-one-year-out R²')
    if floor:
        ax1.axhline(floor['r2'], color=CRITICAL, lw=1.8, ls='--', zorder=4)
        ax1.text(min(x) + 0.1, floor['r2'] + 0.018,
                 f'climatology, using no features at all (R² = {floor["r2"]:+.3f})',
                 color=CRITICAL, fontsize=8.5, ha='left', va='bottom', zorder=6)
    ax1.axhline(0, color=BASELINE, lw=1.2, zorder=2)
    ax1.plot(x, r2, color=CALIBRATED, lw=2, marker='o', ms=6, zorder=5,
             label='weather-informed forecast')
    # Plotted on a scale that reaches R²=0, not zoomed to the spread. The whole curve moves
    # by 0.027 R², which is noise at n=28 — a tight axis would dramatise nothing.
    ax1.set_ylim(-0.32, 0.10)
    ax1.set_xticks(x)
    ax1.set_xticklabels([k.replace('after ', '').replace(' (hindcast)', '') for k in labels],
                        fontsize=8)
    leg = ax1.legend(frameon=False, fontsize=8.5, loc='lower left')
    for txt in leg.get_texts():
        txt.set_color(INK_2)

    _style(ax2,
           title='B. The weather uncertainty does shrink — it is just not worth much',
           xlabel='Months of the season already observed',
           ylabel='90% band from unknown weather (± MT/ha)')
    ax2.plot(x, band, color=UNCALIBRATED, lw=2, marker='o', ms=6, zorder=5)
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(v) for v in x], fontsize=8)
    ax2.set_ylim(bottom=0)

    fig.suptitle(
        'Watching the weather all season does not beat knowing nothing at all',
        fontsize=12.5, color=INK, x=0.02, ha='left')
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return _save(fig, 'forecast_leadtime.png')


def main():
    report = _load()
    print('\nBuilding decision-analysis figures:')
    scissors_figure(report)
    leadtime_figure()
    print()


if __name__ == '__main__':
    main()

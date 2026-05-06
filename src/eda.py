"""Exploratory data analysis: stats + six required plot files saved to outputs/plots/eda/."""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from config import (
    ALL_FEATURES, DISTRICTS, SEASONS, TARGET_COLUMN,
)

sns.set_theme(style='whitegrid', context='notebook')
DPI = 150
EDA_DIR = 'outputs/plots/eda'


def _save(path: str, fig) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def _yield_distribution(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    sns.histplot(df[TARGET_COLUMN], kde=True, ax=axes[0, 0], color='steelblue', bins=20)
    axes[0, 0].set_title('Yield distribution (all)')
    axes[0, 0].set_xlabel('Yield (MT/Ha)')

    for i, district in enumerate(DISTRICTS):
        ax = axes.flatten()[i + 1]
        sub = df[df['District'] == district]
        sns.histplot(sub, x=TARGET_COLUMN, hue='Season', kde=True,
                     ax=ax, palette={'Yala': 'tab:orange', 'Maha': 'tab:blue'})
        ax.set_title(f'{district}')
        ax.set_xlabel('Yield (MT/Ha)')

    sns.boxplot(data=df, x='Season', y=TARGET_COLUMN, hue='Season',
                ax=axes[1, 2], legend=False, palette={'Yala': 'tab:orange', 'Maha': 'tab:blue'})
    axes[1, 2].set_title('Yala vs Maha (overall)')

    fig.suptitle('Yield distribution by district and season', fontsize=14)
    _save(os.path.join(EDA_DIR, 'yield_distribution.png'), fig)


def _yield_timeseries(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharey=True)
    for ax, district in zip(axes.flatten(), DISTRICTS):
        sub = df[df['District'] == district].sort_values(['Year', 'Season'])
        for season, color in zip(SEASONS, ['tab:orange', 'tab:blue']):
            s = sub[sub['Season'] == season]
            ax.plot(s['Year'], s[TARGET_COLUMN], marker='o', label=season, color=color)
            if len(s) >= 3:
                z = np.polyfit(s['Year'], s[TARGET_COLUMN], 1)
                ax.plot(s['Year'], np.polyval(z, s['Year']),
                        linestyle='--', alpha=0.5, color=color)
        ax.set_title(district)
        ax.set_xlabel('Year')
        ax.set_ylabel('Yield (MT/Ha)')
        ax.legend()
    fig.suptitle('Yield over time by district (with linear trend)', fontsize=14)
    _save(os.path.join(EDA_DIR, 'yield_timeseries.png'), fig)


def _correlation_heatmap(df: pd.DataFrame) -> None:
    feat_cols = [c for c in ALL_FEATURES if c in df.columns]
    corr_with_y = df[feat_cols + [TARGET_COLUMN]].corr()[TARGET_COLUMN].drop(TARGET_COLUMN)
    top = corr_with_y.abs().sort_values(ascending=False).head(15).index.tolist()

    sub_corr = df[top + [TARGET_COLUMN]].corr()
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(sub_corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                vmin=-1, vmax=1, square=True, ax=ax, cbar_kws={'shrink': 0.7})
    ax.set_title('Top 15 features correlated with yield (Pearson)')
    _save(os.path.join(EDA_DIR, 'correlation_heatmap.png'), fig)


def _feature_distributions(df: pd.DataFrame) -> None:
    feat_cols = [c for c in ALL_FEATURES if c in df.columns]
    corr_with_y = df[feat_cols + [TARGET_COLUMN]].corr()[TARGET_COLUMN].drop(TARGET_COLUMN)
    top = corr_with_y.abs().sort_values(ascending=False).head(10).index.tolist()

    fig, axes = plt.subplots(2, 5, figsize=(18, 8))
    for ax, col in zip(axes.flatten(), top):
        sns.histplot(df[col], kde=True, ax=ax, color='steelblue', bins=20)
        ax.set_title(col)
    fig.suptitle('Top 10 feature distributions (by |corr| with yield)', fontsize=14)
    _save(os.path.join(EDA_DIR, 'feature_distributions.png'), fig)


def _seasonal_comparison(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x='District', y=TARGET_COLUMN, hue='Season', ax=ax,
                palette={'Yala': 'tab:orange', 'Maha': 'tab:blue'})
    ax.set_title('Yala vs Maha yield by district')
    ax.set_ylabel('Yield (MT/Ha)')

    # Significance markers (Mann-Whitney U).
    y_max = df[TARGET_COLUMN].max() * 1.05
    for i, district in enumerate(DISTRICTS):
        yala = df[(df['District'] == district) & (df['Season'] == 'Yala')][TARGET_COLUMN]
        maha = df[(df['District'] == district) & (df['Season'] == 'Maha')][TARGET_COLUMN]
        if len(yala) > 0 and len(maha) > 0:
            _, p = stats.mannwhitneyu(yala, maha, alternative='two-sided')
            marker = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
            ax.text(i, y_max, marker, ha='center', fontsize=12)
    _save(os.path.join(EDA_DIR, 'seasonal_comparison.png'), fig)


def _district_comparison(df: pd.DataFrame) -> None:
    agg = df.groupby(['District', 'Season'])[TARGET_COLUMN].agg(['mean', 'std']).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    seasons = ['Yala', 'Maha']
    width = 0.38
    x = np.arange(len(DISTRICTS))
    for i, season in enumerate(seasons):
        sub = agg[agg['Season'] == season].set_index('District').reindex(DISTRICTS)
        ax.bar(x + (i - 0.5) * width, sub['mean'], width, yerr=sub['std'],
               label=season, capsize=4,
               color='tab:orange' if season == 'Yala' else 'tab:blue')
    ax.set_xticks(x)
    ax.set_xticklabels(DISTRICTS)
    ax.set_ylabel('Mean yield (MT/Ha)')
    ax.set_title('Average yield by district and season (±1 SD)')
    ax.legend()
    _save(os.path.join(EDA_DIR, 'district_comparison.png'), fig)


def _print_stats(df: pd.DataFrame) -> None:
    print(f'\n  Total observations: {len(df)}')
    print(f'  Date range: {df["Year"].min()}–{df["Year"].max()}')
    print(f'  Yala records: {(df["Season"] == "Yala").sum()} | Maha records: {(df["Season"] == "Maha").sum()}')

    missing_pct = df.isna().mean().sort_values(ascending=False)
    nonzero = missing_pct[missing_pct > 0]
    if not nonzero.empty:
        print('\n  Missing values (% of rows):')
        for col, pct in nonzero.head(10).items():
            print(f'    {col}: {pct * 100:.1f}%')
    else:
        print('  No missing values in any column.')

    print('\n  Yield summary by district × season (mean ± std):')
    summary = df.groupby(['District', 'Season'])[TARGET_COLUMN].agg(['mean', 'std', 'min', 'max']).round(2)
    print(summary.to_string())

    feat_cols = [c for c in ALL_FEATURES if c in df.columns]
    corr = df[feat_cols + [TARGET_COLUMN]].corr()[TARGET_COLUMN].drop(TARGET_COLUMN)
    corr_sorted = corr.abs().sort_values(ascending=False)
    print('\n  Top 10 feature correlations with yield:')
    for col in corr_sorted.head(10).index:
        print(f'    {col}: {corr[col]:+.3f}')


def run_eda(df: pd.DataFrame) -> None:
    print('\n' + '=' * 60)
    print('STEP 4: EXPLORATORY DATA ANALYSIS')
    print('=' * 60)
    _print_stats(df)
    _yield_distribution(df)
    _yield_timeseries(df)
    _correlation_heatmap(df)
    _feature_distributions(df)
    _seasonal_comparison(df)
    _district_comparison(df)
    print(f'\n  ✓ EDA plots saved to {EDA_DIR}/')

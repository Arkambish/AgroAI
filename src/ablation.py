"""Ablation study quantifying contribution of each data source.

XGBoost is used as the base learner (robust on small tabular data, fast).
Same LOYO-CV protocol as the main ML training.
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor

from config import (
    RANDOM_STATE, TARGET_COLUMN,
    WEATHER_FEATURES, SATELLITE_FEATURES, HISTORICAL_FEATURES,
    SOIL_FEATURES, INTERACTION_FEATURES,
)

warnings.filterwarnings('ignore')

from config import RESULTS_DIR, PLOTS_DIR  # variant-aware (synthetic|real)

EXPERIMENTS = [
    ('A_Weather_only',     WEATHER_FEATURES),
    ('B_Satellite_only',   SATELLITE_FEATURES),
    ('C_Historical_only',  HISTORICAL_FEATURES),
    ('D_Soil_only',        SOIL_FEATURES),
    ('E_Weather+Satellite', WEATHER_FEATURES + SATELLITE_FEATURES),
    ('F_All_features', WEATHER_FEATURES + SATELLITE_FEATURES
                        + HISTORICAL_FEATURES + SOIL_FEATURES + INTERACTION_FEATURES),
]


def _loyo(X, y, years):
    unique_years = np.array(sorted(set(years)))
    oof = np.full(len(y), np.nan, dtype=np.float32)
    for held in unique_years:
        train_mask = years != held
        test_mask = years == held
        model = XGBRegressor(
            random_state=RANDOM_STATE, n_jobs=-1, verbosity=0,
            n_estimators=300, learning_rate=0.05, max_depth=5, subsample=0.8,
        )
        model.fit(X[train_mask], y[train_mask])
        oof[test_mask] = model.predict(X[test_mask])
    return oof


def run_ablation_study(df: pd.DataFrame) -> pd.DataFrame:
    print('\n' + '=' * 60)
    print('STEP 7: ABLATION STUDY')
    print('=' * 60)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)

    y = df[TARGET_COLUMN].astype(np.float32).values
    years = df['Year'].values

    rows = []
    for name, feature_set in EXPERIMENTS:
        cols = [c for c in feature_set if c in df.columns]
        if not cols:
            print(f'  ⚠ {name}: no features available, skipping.')
            continue
        X = df[cols].astype(np.float32).values
        oof = _loyo(X, y, years)
        rmse = float(np.sqrt(mean_squared_error(y, oof)))
        mae = float(mean_absolute_error(y, oof))
        r2 = float(r2_score(y, oof))
        rows.append({'Experiment': name, 'N_features': len(cols),
                     'RMSE': round(rmse, 4), 'MAE': round(mae, 4), 'R2': round(r2, 4)})
        print(f'  {name:<22} (n={len(cols)}): RMSE={rmse:.3f}  MAE={mae:.3f}  R²={r2:.3f}')

    out = pd.DataFrame(rows)
    csv_path = os.path.join(RESULTS_DIR, 'ablation_results.csv')
    out.to_csv(csv_path, index=False)
    print(f'\n  Saved → {csv_path}')

    # Plot.
    fig, ax = plt.subplots(figsize=(10, 6))
    palette = sns.color_palette('viridis', len(out))
    bars = ax.bar(out['Experiment'], out['R2'], color=palette)
    ax.axhline(0.75, color='red', linestyle='--', linewidth=1, label='Target R² = 0.75')
    ax.set_ylabel('R² (LOYO-CV)')
    ax.set_title('Ablation: feature-source contribution to yield prediction R²')
    ax.set_ylim(min(0.0, out['R2'].min() - 0.05), max(1.0, out['R2'].max() + 0.05))
    plt.xticks(rotation=20, ha='right')
    for bar, v in zip(bars, out['R2']):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.005, f'{v:.3f}', ha='center')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'ablation_comparison.png'), dpi=150)
    plt.close(fig)

    # Critical finding text.
    if {'A_Weather_only', 'E_Weather+Satellite'}.issubset(set(out['Experiment'])):
        a = out.loc[out['Experiment'] == 'A_Weather_only', 'R2'].iloc[0]
        e = out.loc[out['Experiment'] == 'E_Weather+Satellite', 'R2'].iloc[0]
        delta = (e - a) * 100
        print(f'  Δ R² adding satellite to weather: {delta:+.2f} pp')

    return out

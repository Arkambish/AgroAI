"""ML models: Random Forest, XGBoost, SVR.

Training protocol:
  - Inner: GridSearchCV with TimeSeriesSplit(5) on a fast grid for hyper-tuning.
  - Outer: Leave-One-Year-Out CV for honest test metrics.
  - Final: refit on all data with best params, save artefact + scaler if needed.

Out-of-fold predictions are persisted per-model (JSON) so the evaluator
can compute consistent metrics and run paired statistical tests.
"""

import json
import os
import time
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor

from config import (
    RANDOM_STATE, RF_PARAMS_FAST, XGB_PARAMS_FAST, SVR_PARAMS_FAST,
    TARGET_COLUMN,
)
from visualizer import actual_vs_predicted, residual_plot, feature_importance_plot

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

MODELS_DIR = 'outputs/models'
RESULTS_DIR = 'outputs/results'
PLOTS_DIR = 'outputs/plots/results'


def _tune_with_gridsearch(estimator_factory, param_grid, X, y):
    cv = TimeSeriesSplit(n_splits=min(5, len(X) // 8))
    gs = GridSearchCV(estimator_factory(), param_grid, cv=cv,
                      scoring='neg_mean_squared_error', n_jobs=-1)
    gs.fit(X, y)
    return gs.best_estimator_, gs.best_params_


def _loyo_predictions(estimator_factory, X, y, years, scale: bool = False):
    unique_years = np.array(sorted(set(years)))
    oof = np.full(len(y), np.nan, dtype=np.float32)
    for held in unique_years:
        train_mask = years != held
        test_mask = years == held
        X_tr, X_te = X[train_mask], X[test_mask]
        y_tr = y[train_mask]
        if scale:
            scaler = StandardScaler().fit(X_tr)
            X_tr, X_te = scaler.transform(X_tr), scaler.transform(X_te)
        model = estimator_factory()
        model.fit(X_tr, y_tr)
        oof[test_mask] = model.predict(X_te)
    return oof


def _save_oof(model_name: str, oof: np.ndarray, y: np.ndarray, df: pd.DataFrame,
              metrics: dict) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    payload = {
        'model_name': model_name,
        'metrics': metrics,
        'rows': [
            {'Year': int(df['Year'].iloc[i]), 'Season': str(df['Season'].iloc[i]),
             'District': str(df['District'].iloc[i]),
             'actual': float(y[i]), 'predicted': float(oof[i])}
            for i in range(len(y))
        ],
    }
    with open(os.path.join(RESULTS_DIR, f'oof_{model_name.lower()}.json'), 'w') as f:
        json.dump(payload, f, indent=2)


def _metrics(y_true, y_pred, name: str, train_time: float, params: dict | None,
             n_params: int | None = None) -> dict:
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
    return {
        'Model': name, 'RMSE': round(rmse, 4), 'MAE': round(mae, 4),
        'R2': round(r2, 4), 'MAPE': round(mape, 2),
        'Train_Time_s': round(train_time, 2),
        'Best_Params': params or {},
        'Parameters': n_params if n_params is not None else None,
    }


def train_random_forest(X, y, feature_names, df: pd.DataFrame) -> dict:
    print('\n--- Random Forest (1/3) ---')
    t0 = time.time()
    factory = lambda: RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1)
    best, params = _tune_with_gridsearch(factory, RF_PARAMS_FAST, X, y)
    print(f'  Tuned params: {params}')

    oof = _loyo_predictions(
        lambda: RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1, **params),
        X, y, df['Year'].values,
    )

    final = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1, **params)
    final.fit(X, y)
    joblib.dump(final, os.path.join(MODELS_DIR, 'rf_best.pkl'))

    elapsed = time.time() - t0
    metrics = _metrics(y, oof, 'RandomForest', elapsed, params)
    _save_oof('RandomForest', oof, y, df, metrics)
    print(f'  RMSE={metrics["RMSE"]} MAE={metrics["MAE"]} R²={metrics["R2"]} '
          f'MAPE={metrics["MAPE"]}% ({elapsed:.1f}s)')

    actual_vs_predicted(y, oof, 'Random Forest',
                        os.path.join(PLOTS_DIR, 'actual_vs_pred_rf.png'),
                        districts=df['District'].values)
    residual_plot(y, oof, 'Random Forest',
                  os.path.join(PLOTS_DIR, 'residuals_rf.png'))
    feature_importance_plot(final.feature_importances_, feature_names, 'Random Forest',
                             os.path.join(PLOTS_DIR, 'feature_importance_rf.png'))
    return metrics


def train_xgboost(X, y, feature_names, df: pd.DataFrame) -> dict:
    print('\n--- XGBoost (2/3) ---')
    t0 = time.time()
    factory = lambda: XGBRegressor(
        random_state=RANDOM_STATE, n_jobs=-1,
        objective='reg:squarederror', verbosity=0,
    )
    best, params = _tune_with_gridsearch(factory, XGB_PARAMS_FAST, X, y)
    print(f'  Tuned params: {params}')

    oof = _loyo_predictions(
        lambda: XGBRegressor(random_state=RANDOM_STATE, n_jobs=-1, verbosity=0, **params),
        X, y, df['Year'].values,
    )

    final = XGBRegressor(random_state=RANDOM_STATE, n_jobs=-1, verbosity=0, **params)
    final.fit(X, y)
    joblib.dump(final, os.path.join(MODELS_DIR, 'xgb_best.pkl'))

    elapsed = time.time() - t0
    metrics = _metrics(y, oof, 'XGBoost', elapsed, params)
    _save_oof('XGBoost', oof, y, df, metrics)
    print(f'  RMSE={metrics["RMSE"]} MAE={metrics["MAE"]} R²={metrics["R2"]} '
          f'MAPE={metrics["MAPE"]}% ({elapsed:.1f}s)')

    actual_vs_predicted(y, oof, 'XGBoost',
                        os.path.join(PLOTS_DIR, 'actual_vs_pred_xgb.png'),
                        districts=df['District'].values)
    residual_plot(y, oof, 'XGBoost',
                  os.path.join(PLOTS_DIR, 'residuals_xgb.png'))
    feature_importance_plot(final.feature_importances_, feature_names, 'XGBoost',
                             os.path.join(PLOTS_DIR, 'feature_importance_xgb.png'))
    return metrics


def train_svr(X, y, feature_names, df: pd.DataFrame) -> dict:
    print('\n--- SVR (3/3) ---')
    t0 = time.time()
    # Tune on scaled features.
    scaler = StandardScaler().fit(X)
    X_s = scaler.transform(X)

    factory = lambda: SVR()
    best, params = _tune_with_gridsearch(factory, SVR_PARAMS_FAST, X_s, y)
    print(f'  Tuned params: {params}')

    oof = _loyo_predictions(lambda: SVR(**params), X, y, df['Year'].values, scale=True)

    # Final refit on full scaled set.
    final_scaler = StandardScaler().fit(X)
    final = SVR(**params)
    final.fit(final_scaler.transform(X), y)
    joblib.dump(final, os.path.join(MODELS_DIR, 'svr_best.pkl'))
    joblib.dump(final_scaler, os.path.join(MODELS_DIR, 'svr_scaler.pkl'))

    elapsed = time.time() - t0
    metrics = _metrics(y, oof, 'SVR', elapsed, params)
    _save_oof('SVR', oof, y, df, metrics)
    print(f'  RMSE={metrics["RMSE"]} MAE={metrics["MAE"]} R²={metrics["R2"]} '
          f'MAPE={metrics["MAPE"]}% ({elapsed:.1f}s)')

    actual_vs_predicted(y, oof, 'SVR',
                        os.path.join(PLOTS_DIR, 'actual_vs_pred_svr.png'),
                        districts=df['District'].values)
    residual_plot(y, oof, 'SVR',
                  os.path.join(PLOTS_DIR, 'residuals_svr.png'))
    return metrics


def train_all_ml_models(X, y, feature_names, df: pd.DataFrame) -> list:
    print('\n' + '=' * 60)
    print('STEP 5: MACHINE LEARNING MODELS')
    print('=' * 60)
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)
    return [
        train_random_forest(X, y, feature_names, df),
        train_xgboost(X, y, feature_names, df),
        train_svr(X, y, feature_names, df),
    ]

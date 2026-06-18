"""SHAP feature-importance analysis on the best model."""

import json
import os
import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

import shap

from config import ALL_FEATURES
from config import RESULTS_DIR, PLOTS_DIR, MODELS_DIR  # variant-aware (synthetic|real)


def _load_best_tree_model():
    """SHAP TreeExplainer is dramatically faster on tree models. We pick the best tree
    model (RF or XGBoost) — even if a DL model has a better R², SHAP on KernelExplainer
    is too slow for the FYP report. The plot represents the strongest interpretable
    tabular learner."""
    best_path = os.path.join(RESULTS_DIR, 'best_model_metrics.json')
    candidate_models = {
        'RandomForest': os.path.join(MODELS_DIR, 'rf_best.pkl'),
        'XGBoost': os.path.join(MODELS_DIR, 'xgb_best.pkl'),
    }

    if os.path.exists(best_path):
        with open(best_path) as f:
            meta = json.load(f)
        if meta['Model'] in candidate_models and os.path.exists(candidate_models[meta['Model']]):
            return meta['Model'], joblib.load(candidate_models[meta['Model']])

    for name, p in candidate_models.items():
        if os.path.exists(p):
            return name, joblib.load(p)
    raise FileNotFoundError('No tree model artefact found for SHAP analysis.')


def run_shap_analysis(X: np.ndarray, feature_names: list) -> None:
    print('\n' + '=' * 60)
    print('STEP 9: SHAP FEATURE IMPORTANCE')
    print('=' * 60)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)

    model_name, model = _load_best_tree_model()
    print(f'  Using {model_name} for SHAP (fast TreeExplainer path).')

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    order = np.argsort(mean_abs_shap)[::-1]
    top_15 = order[:15]

    # ---- Beeswarm summary ----
    fig = plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'shap_summary.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ---- Mean |SHAP| bar chart ----
    fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * 15)))
    vals = mean_abs_shap[top_15][::-1]
    names = [feature_names[i] for i in top_15][::-1]
    ax.barh(np.arange(len(top_15)), vals, color='steelblue')
    ax.set_yticks(np.arange(len(top_15)))
    ax.set_yticklabels(names)
    ax.set_xlabel('Mean |SHAP value|')
    ax.set_title(f'Top 15 features by SHAP importance ({model_name})')
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'shap_importance.png'), dpi=150)
    plt.close(fig)

    # ---- Dependence plot for the top feature ----
    top_idx = int(order[0])
    top_name = feature_names[top_idx]
    fig = plt.figure(figsize=(8, 6))
    shap.dependence_plot(top_idx, shap_values, X, feature_names=feature_names, show=False)
    fig.tight_layout()
    safe_name = top_name.replace('/', '_')
    fig.savefig(os.path.join(PLOTS_DIR, f'shap_dependence_{safe_name}.png'),
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ---- Persist top-15 JSON for the API and final summary ----
    payload = [
        {'rank': i + 1, 'name': feature_names[idx],
         'mean_abs_shap': float(mean_abs_shap[idx])}
        for i, idx in enumerate(order[:15])
    ]
    with open(os.path.join(RESULTS_DIR, 'feature_importance.json'), 'w') as f:
        json.dump(payload, f, indent=2)

    print('  Top 5 features by SHAP:')
    for entry in payload[:5]:
        print(f'    {entry["rank"]}. {entry["name"]}: {entry["mean_abs_shap"]:.4f}')
    print(f'  Saved → {RESULTS_DIR}/feature_importance.json')
    print(f'  Plots → {PLOTS_DIR}/shap_*.png')

"""Shared plotting helpers used across the ML and DL training scripts."""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', context='notebook')
DPI = 150


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def actual_vs_predicted(y_true, y_pred, model_name: str, save_path: str,
                         districts=None) -> None:
    _ensure_dir(save_path)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    fig, ax = plt.subplots(figsize=(7, 6))
    if districts is not None:
        for d in sorted(set(districts)):
            mask = np.asarray(districts) == d
            ax.scatter(y_true[mask], y_pred[mask], alpha=0.7, label=d, s=40)
        ax.legend(title='District', loc='best')
    else:
        ax.scatter(y_true, y_pred, alpha=0.7, s=40)
    lo = float(min(y_true.min(), y_pred.min())) - 1
    hi = float(max(y_true.max(), y_pred.max())) + 1
    ax.plot([lo, hi], [lo, hi], 'k--', linewidth=1, label='y = x')
    from sklearn.metrics import r2_score
    r2 = r2_score(y_true, y_pred)
    ax.set_xlabel('Actual yield (MT/Ha)')
    ax.set_ylabel('Predicted yield (MT/Ha)')
    ax.set_title(f'{model_name} — Actual vs Predicted (R² = {r2:.3f})')
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    fig.tight_layout()
    fig.savefig(save_path, dpi=DPI)
    plt.close(fig)


def residual_plot(y_true, y_pred, model_name: str, save_path: str) -> None:
    _ensure_dir(save_path)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    residuals = y_true - y_pred
    threshold = 2 * residuals.std()
    fig, ax = plt.subplots(figsize=(7, 5))
    outliers = np.abs(residuals) > threshold
    ax.scatter(y_pred[~outliers], residuals[~outliers], alpha=0.7, s=40, label='Inlier')
    ax.scatter(y_pred[outliers], residuals[outliers], color='red', s=55, label=f'|res| > 2σ ({outliers.sum()})')
    ax.axhline(0, color='black', linewidth=1)
    ax.set_xlabel('Predicted yield (MT/Ha)')
    ax.set_ylabel('Residual (actual - predicted)')
    ax.set_title(f'{model_name} — Residuals')
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=DPI)
    plt.close(fig)


def feature_importance_plot(importances, feature_names, model_name: str, save_path: str,
                              top_k: int = 15) -> None:
    _ensure_dir(save_path)
    importances = np.asarray(importances)
    order = np.argsort(importances)[::-1][:top_k]
    fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * top_k)))
    ax.barh(np.arange(len(order)), importances[order][::-1], color='steelblue')
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels([feature_names[i] for i in order][::-1])
    ax.set_xlabel('Importance')
    ax.set_title(f'{model_name} — Top {top_k} feature importances')
    fig.tight_layout()
    fig.savefig(save_path, dpi=DPI)
    plt.close(fig)


def learning_curve_plot(history: dict, model_name: str, save_path: str) -> None:
    """history: dict with 'loss' and 'val_loss' arrays, plus optional 'best_epoch'."""
    _ensure_dir(save_path)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(history['loss'], label='Training loss')
    if 'val_loss' in history and history['val_loss']:
        ax.plot(history['val_loss'], label='Validation loss')
    if history.get('best_epoch') is not None:
        ax.axvline(history['best_epoch'], color='red', linestyle='--', label='Early stop')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss (MSE)')
    ax.set_title(f'{model_name} — Learning curve')
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=DPI)
    plt.close(fig)

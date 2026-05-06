"""Model evaluation, statistical comparison, and final summary writer."""

import glob
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from config import TARGET_R2, DISTRICTS, TARGET_COLUMN

RESULTS_DIR = 'outputs/results'
PLOTS_DIR = 'outputs/plots/results'

ML_NAMES = {'RandomForest', 'XGBoost', 'SVR'}
DL_NAMES = {'LSTM', 'BiLSTM', 'CNN', 'CNN_LSTM_Hybrid'}


def compute_metrics(y_true, y_pred, model_name: str) -> dict:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    safe = np.where(np.abs(y_true) > 1e-6, y_true, 1e-6)
    mape = float(np.mean(np.abs((y_true - y_pred) / safe)) * 100)
    return {'Model': model_name, 'RMSE': round(rmse, 4),
            'MAE': round(mae, 4), 'R2': round(r2, 4), 'MAPE': round(mape, 2)}


def compare_models_statistically(errors_a, errors_b, name_a: str, name_b: str) -> tuple:
    try:
        wstat, wp = stats.wilcoxon(errors_a, errors_b)
    except ValueError:
        wstat, wp = float('nan'), 1.0
    tstat, tp = stats.ttest_rel(errors_a, errors_b)
    print(f'\n  {name_a} vs {name_b}:')
    print(f'    Wilcoxon p={wp:.4f} {"(significant)" if wp < 0.05 else "(n.s.)"}')
    print(f'    Paired t   p={tp:.4f} {"(significant)" if tp < 0.05 else "(n.s.)"}')
    return wp, tp


def _load_oof_payloads() -> dict:
    payloads = {}
    for path in sorted(glob.glob(os.path.join(RESULTS_DIR, 'oof_*.json'))):
        with open(path) as f:
            data = json.load(f)
        payloads[data['model_name']] = data
    return payloads


def _comparison_bar_plot(comparison: pd.DataFrame, save_path: str) -> None:
    fig, ax1 = plt.subplots(figsize=(11, 6))
    x = np.arange(len(comparison))
    width = 0.4
    colors = []
    for m in comparison['Model']:
        if m in ML_NAMES:
            colors.append('tab:blue')
        elif m == 'CNN_LSTM_Hybrid':
            colors.append('tab:red')
        else:
            colors.append('tab:orange')

    ax1.bar(x - width / 2, comparison['RMSE'], width, color=colors, label='RMSE', alpha=0.85)
    ax1.set_ylabel('RMSE (MT/Ha)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(comparison['Model'], rotation=15, ha='right')

    ax2 = ax1.twinx()
    ax2.bar(x + width / 2, comparison['R2'], width, color=colors,
            edgecolor='black', linewidth=1.5, label='R²', alpha=0.85, hatch='//')
    ax2.axhline(TARGET_R2, color='red', linestyle='--', linewidth=1, label=f'Target R²={TARGET_R2}')
    ax2.set_ylabel('R²')
    ax2.set_ylim(min(0.0, comparison['R2'].min() - 0.05), max(1.0, comparison['R2'].max() + 0.1))

    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, color='tab:blue', label='ML model'),
        plt.Rectangle((0, 0), 1, 1, color='tab:orange', label='DL model'),
        plt.Rectangle((0, 0), 1, 1, color='tab:red', label='Hybrid CNN-LSTM (novel)'),
    ]
    ax1.legend(handles=legend_elements, loc='upper left')
    ax2.legend(loc='upper right')
    ax1.set_title('Model comparison: RMSE (solid) and R² (hatched)')
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def _summarise(comparison: pd.DataFrame, payloads: dict, ablation: pd.DataFrame | None) -> str:
    best = comparison.iloc[comparison['R2'].idxmax()]
    best_name = best['Model']
    best_r2 = best['R2']
    best_rmse = best['RMSE']

    # ML vs DL — pool all OOF errors per group.
    ml_errs, dl_errs = [], []
    for name, p in payloads.items():
        rows = p['rows']
        errs = [r['actual'] - r['predicted'] for r in rows]
        if name in ML_NAMES:
            ml_errs.extend(errs)
        elif name in DL_NAMES:
            dl_errs.extend(errs)
    dl_beats_ml = '?'
    p_value = float('nan')
    if ml_errs and dl_errs:
        m = min(len(ml_errs), len(dl_errs))
        try:
            _, p_value = stats.wilcoxon(np.abs(ml_errs[:m]), np.abs(dl_errs[:m]))
        except ValueError:
            p_value = 1.0
        dl_mean_abs = np.mean(np.abs(dl_errs))
        ml_mean_abs = np.mean(np.abs(ml_errs))
        dl_beats_ml = 'YES' if dl_mean_abs < ml_mean_abs else 'NO'

    # Hybrid vs standalone CNN/LSTM.
    hybrid_beats = '?'
    if 'CNN_LSTM_Hybrid' in comparison['Model'].values:
        hybrid_r2 = float(comparison.loc[comparison['Model'] == 'CNN_LSTM_Hybrid', 'R2'].iloc[0])
        std_models = comparison[comparison['Model'].isin(['CNN', 'LSTM'])]
        if len(std_models):
            hybrid_beats = 'YES' if hybrid_r2 > std_models['R2'].max() else 'NO'

    # Top features (best model).
    top_feats = '(see feature_importance.json)'
    fi_path = os.path.join(RESULTS_DIR, 'feature_importance.json')
    if os.path.exists(fi_path):
        with open(fi_path) as f:
            fi = json.load(f)
        top_feats = ', '.join([f['name'] for f in fi[:3]])

    # Ablation: weather-only vs weather+satellite.
    abl_text = '?'
    if ablation is not None and not ablation.empty:
        try:
            a = float(ablation.loc[ablation['Experiment'] == 'A_Weather_only', 'R2'].iloc[0])
            e = float(ablation.loc[ablation['Experiment'] == 'E_Weather+Satellite', 'R2'].iloc[0])
            abl_text = f'{(e - a) * 100:+.2f} percentage points'
        except (IndexError, KeyError):
            pass

    # Yala vs Maha accuracy.
    best_payload = payloads.get(best_name)
    yala_text = maha_text = '?'
    if best_payload:
        df_b = pd.DataFrame(best_payload['rows'])
        for season, target in (('Yala', 'yala'), ('Maha', 'maha')):
            sub = df_b[df_b['Season'] == season]
            if len(sub):
                rmse = float(np.sqrt(mean_squared_error(sub['actual'], sub['predicted'])))
                if season == 'Yala':
                    yala_text = f'{rmse:.3f}'
                else:
                    maha_text = f'{rmse:.3f}'

    # Per-district R² for best model.
    easiest = hardest = '?'
    if best_payload:
        df_b = pd.DataFrame(best_payload['rows'])
        per_dist = []
        for d in DISTRICTS:
            sub = df_b[df_b['District'] == d]
            if len(sub) > 1:
                per_dist.append((d, r2_score(sub['actual'], sub['predicted'])))
        if per_dist:
            per_dist.sort(key=lambda x: x[1], reverse=True)
            easiest = f'{per_dist[0][0]} (R²={per_dist[0][1]:.3f})'
            hardest = f'{per_dist[-1][0]} (R²={per_dist[-1][1]:.3f})'

    target_met = 'YES' if best_r2 > TARGET_R2 else 'NO'

    summary = (
        f'BIG ONION YIELD PREDICTION — RESEARCH FINDINGS\n'
        f'{"=" * 60}\n\n'
        f'1. Best performing model: {best_name} with R²={best_r2:.3f}, RMSE={best_rmse:.3f} MT/Ha\n'
        f'2. Does DL outperform ML? {dl_beats_ml} (Wilcoxon p={p_value:.4f})\n'
        f'3. Does CNN-LSTM hybrid beat standalone CNN/LSTM? {hybrid_beats}\n'
        f'4. Top 3 most important features: {top_feats}\n'
        f'5. Ablation Δ R² (Weather → Weather+Satellite): {abl_text}\n'
        f'6. RMSE Yala={yala_text}, Maha={maha_text}\n'
        f'7. Easiest district to predict: {easiest}\n'
        f'8. Hardest district to predict: {hardest}\n'
        f'9. Reaches target R² > {TARGET_R2}? {target_met}\n'
    )
    return summary


def generate_final_comparison(ablation: pd.DataFrame | None = None) -> pd.DataFrame:
    print('\n' + '=' * 60)
    print('STEP 8: FINAL COMPARISON')
    print('=' * 60)

    payloads = _load_oof_payloads()
    if not payloads:
        print('  ⚠ No oof_*.json files found — train models first.')
        return pd.DataFrame()

    rows = []
    for name, payload in payloads.items():
        m = payload['metrics']
        rows.append({
            'Model': m['Model'], 'RMSE': m['RMSE'], 'MAE': m['MAE'],
            'R2': m['R2'], 'MAPE': m['MAPE'],
            'Train_Time_s': m.get('Train_Time_s', None),
            'Parameters': m.get('Parameters', None),
        })
    comparison = pd.DataFrame(rows).sort_values('R2', ascending=False).reset_index(drop=True)
    csv_path = os.path.join(RESULTS_DIR, 'model_comparison.csv')
    comparison.to_csv(csv_path, index=False)
    print(f'  Saved → {csv_path}')
    print(comparison.to_string(index=False))

    _comparison_bar_plot(comparison, os.path.join(PLOTS_DIR, 'model_comparison_bar.png'))

    # Save best model metadata for the API.
    best = comparison.iloc[0]
    best_payload = payloads[best['Model']]
    best_meta = {
        'Model': best['Model'], 'RMSE': float(best['RMSE']),
        'MAE': float(best['MAE']), 'R2': float(best['R2']),
        'MAPE': float(best['MAPE']),
    }
    with open(os.path.join(RESULTS_DIR, 'best_model_metrics.json'), 'w') as f:
        json.dump(best_meta, f, indent=2)
    print(f'  Best model: {best["Model"]} (R²={best["R2"]})')

    # Summary text.
    summary = _summarise(comparison, payloads, ablation)
    with open(os.path.join(RESULTS_DIR, 'final_summary.txt'), 'w') as f:
        f.write(summary)
    print('\n' + summary)
    return comparison

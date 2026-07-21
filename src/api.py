"""Flask REST API serving the best big-onion-yield model.

Endpoints:
  GET  /health
  POST /predict
  GET  /models/compare
  GET  /feature-importance
  GET  /context
  GET  /districts
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import joblib
import shap
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ALL_FEATURES, DISTRICTS, SEASONS, DATA_VARIANT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Serve the variant selected by DATA_VARIANT (default 'synthetic'). Set
# DATA_VARIANT=real to serve the models trained on the real collected data.
_SUFFIX = '' if DATA_VARIANT == 'synthetic' else f'_{DATA_VARIANT}'
MODELS_DIR = os.path.join(ROOT, 'outputs', f'models{_SUFFIX}')
RESULTS_DIR = os.path.join(ROOT, 'outputs', f'results{_SUFFIX}')
PROCESSED_DIR = os.path.join(ROOT, 'data', f'processed{_SUFFIX}')

app = Flask(__name__)
CORS(app)

_state = {
    'model': None, 'metrics': None, 'model_name': None, 'scaler': None,
    'context_df': None, 'explainer': None,
}


def _load_state() -> None:
    """Load best tabular model. Prefer whichever the evaluator crowned;
    fall back to XGBoost."""
    metrics_path = os.path.join(RESULTS_DIR, 'best_model_metrics.json')
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)

    candidates = {
        'XGBoost': ('xgb_best.pkl', None),
        'RandomForest': ('rf_best.pkl', None),
        'SVR': ('svr_best.pkl', 'svr_scaler.pkl'),
    }
    name = metrics.get('Model') if metrics.get('Model') in candidates else None
    if name is None:
        for n in candidates:
            if os.path.exists(os.path.join(MODELS_DIR, candidates[n][0])):
                name = n
                break

    if name is None:
        raise FileNotFoundError(
            'No tabular model artefact found. Run `python main.py` first.'
        )

    if name is not None:
        artefact, scaler_file = candidates[name]
        _state['model'] = joblib.load(os.path.join(MODELS_DIR, artefact))
        _state['model_name'] = name
        _state['metrics'] = metrics
        _state['scaler'] = (
            joblib.load(os.path.join(MODELS_DIR, scaler_file)) if scaler_file else None
        )
        
        # Initialize SHAP explainer for tree-based models
        if name in ['RandomForest', 'XGBoost']:
            try:
                _state['explainer'] = shap.TreeExplainer(_state['model'])
                print(f'[api] Initialized SHAP TreeExplainer for {name}')
            except Exception as e:
                print(f'[api] Failed to initialize SHAP: {e}')
        
        print(f'[api] Loaded {name} (metrics={metrics or "n/a"})')

    # Optional: cache the processed dataset for the /context endpoint.
    integrated_csv = os.path.join(PROCESSED_DIR, 'integrated_dataset.csv')
    if os.path.exists(integrated_csv):
        _state['context_df'] = pd.read_csv(integrated_csv)
        print(f'[api] Loaded context dataset ({len(_state["context_df"])} rows)')
    else:
        print('[api] integrated_dataset.csv not found — /context will return 503.')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model': _state.get('model_name'),
        'service': 'BigOnion Yield Predictor',
    })


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(silent=True) or {}
    if _state['model'] is None:
        return jsonify({'error': 'Model not loaded'}), 503

    feature_vec = np.array([[float(data.get(f, 0.0)) for f in ALL_FEATURES]],
                           dtype=np.float32)
    if _state['scaler'] is not None:
        feature_vec = _state['scaler'].transform(feature_vec)
    prediction = float(_state['model'].predict(feature_vec)[0])

    rmse = float(_state['metrics'].get('RMSE', 0)) if _state['metrics'] else 0.0
    if rmse > 0:
        margin = 1.96 * rmse
    else:
        margin = prediction * 0.15

    # Calculate SHAP values for this prediction
    shap_dict = {}
    if _state['explainer'] is not None:
        try:
            # TreeExplainer expects a 2D array or similar. feature_vec is already (1, N)
            sv = _state['explainer'].shap_values(feature_vec)
            # For XGBoost/RF regression, sv is usually (1, N) or (N,)
            if isinstance(sv, list): sv = sv[0]
            if len(sv.shape) == 2: sv = sv[0]
            shap_dict = {f: float(sv[i]) for i, f in enumerate(ALL_FEATURES)}
        except Exception as e:
            print(f'[api] SHAP error: {e}')

    # Confidence Label for Farmer-friendly UI
    confidence_val = "High"
    if _state['metrics'] and _state['metrics'].get('R2', 0) < 0.7:
        confidence_val = "Medium"
    if _state['metrics'] and _state['metrics'].get('R2', 0) < 0.5:
        confidence_val = "Low"

    response = {
        'district': data.get('district'),
        'season': data.get('season'),
        'year': data.get('year'),
        'predicted_yield_MT_per_Ha': round(prediction, 2),
        'confidence_lower': round(max(0.0, prediction - margin), 2),
        'confidence_upper': round(prediction + margin, 2),
        'confidence': confidence_val,
        'shap_values': shap_dict,
        'model': _state.get('model_name'),
        'model_r2': _state['metrics'].get('R2', None) if _state['metrics'] else None,
    }

    # TODO: Implement PostgreSQL storage here
    # with db_session() as session:
    #     save_prediction(response)

    return jsonify(response)


@app.route('/models/compare', methods=['GET'])
def compare_models():
    csv_path = os.path.join(RESULTS_DIR, 'model_comparison.csv')
    if not os.path.exists(csv_path):
        return jsonify({'error': 'model_comparison.csv not found — run pipeline first.'}), 404
    df = pd.read_csv(csv_path)
    return jsonify(df.to_dict(orient='records'))


@app.route('/feature-importance', methods=['GET'])
def feature_importance():
    fi_path = os.path.join(RESULTS_DIR, 'feature_importance.json')
    if not os.path.exists(fi_path):
        return jsonify({'error': 'feature_importance.json not found — run SHAP step first.'}), 404
    with open(fi_path) as f:
        return jsonify(json.load(f))


@app.route('/context', methods=['GET'])
def context():
    """Return the 32 feature values for a given (district, season, year).

    Used by the dashboard to prefill the prediction form. Falls back to
    the (district, season) historical mean if the exact year is not in
    the dataset (e.g. user picks a future year).
    """
    df = _state.get('context_df')
    if df is None:
        return jsonify({'error': 'context dataset not loaded'}), 503

    district = request.args.get('district', type=str)
    season = request.args.get('season', type=str)
    year = request.args.get('year', type=int)

    if not district or not season or year is None:
        return jsonify({'error': 'query params district, season, year are required'}), 400

    feature_cols = [c for c in ALL_FEATURES if c in df.columns]
    sub = df[(df['District'] == district) & (df['Season'] == season)]
    if sub.empty:
        return jsonify({
            'error': f'no rows for district={district}, season={season}',
            'district': district, 'season': season, 'year': year,
        }), 404

    exact = sub[sub['Year'] == year]
    if not exact.empty:
        row = exact.iloc[0][feature_cols]
        source = 'exact'
    else:
        # Fall back to the (district, season) mean across all years.
        row = sub[feature_cols].mean(numeric_only=True)
        source = 'historical_mean'

    payload = {col: float(row[col]) for col in feature_cols}
    payload.update({
        'district': district,
        'season': season,
        'year': year,
        'source': source,
        'available_years': sorted(int(y) for y in sub['Year'].unique()),
    })
    return jsonify(payload)


@app.route('/districts', methods=['GET'])
def list_districts():
    """Return the four target districts and the two seasons. Lets the
    frontend keep its dropdowns in sync with backend config."""
    df = _state.get('context_df')
    years = (
        sorted(int(y) for y in df['Year'].unique())
        if df is not None else []
    )
    return jsonify({
        'districts': list(DISTRICTS),
        'seasons': list(SEASONS),
        'years': years,
    })


if __name__ == '__main__':
    _load_state()
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=False, host='0.0.0.0', port=port)

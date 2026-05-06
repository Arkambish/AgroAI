"""Flask REST API serving the best big-onion-yield model.

Endpoints:
  GET  /health
  POST /predict
  GET  /models/compare
  GET  /feature-importance
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ALL_FEATURES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, 'outputs', 'models')
RESULTS_DIR = os.path.join(ROOT, 'outputs', 'results')

app = Flask(__name__)
CORS(app)

_state = {'model': None, 'metrics': None, 'model_name': None, 'scaler': None}


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

    artefact, scaler_file = candidates[name]
    _state['model'] = joblib.load(os.path.join(MODELS_DIR, artefact))
    _state['model_name'] = name
    _state['metrics'] = metrics
    _state['scaler'] = (
        joblib.load(os.path.join(MODELS_DIR, scaler_file)) if scaler_file else None
    )
    print(f'[api] Loaded {name} (metrics={metrics or "n/a"})')


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

    return jsonify({
        'district': data.get('district'),
        'season': data.get('season'),
        'predicted_yield_MT_per_Ha': round(prediction, 2),
        'confidence_lower': round(max(0.0, prediction - margin), 2),
        'confidence_upper': round(prediction + margin, 2),
        'model': _state.get('model_name'),
        'model_r2': _state['metrics'].get('R2', None) if _state['metrics'] else None,
    })


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


if __name__ == '__main__':
    _load_state()
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=False, host='0.0.0.0', port=port)

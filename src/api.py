"""Flask REST API serving the best big-onion-yield model.

Endpoints:
  GET  /health
  POST /predict
  GET  /models/compare
  GET  /feature-importance
  GET  /context
  GET  /baseline
  GET  /districts
"""

import json
import math
import os
import sys
import numpy as np
import pandas as pd
import joblib
import shap
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    ALL_FEATURES, DISTRICTS, SEASONS, DATA_VARIANT, TARGET_COLUMN,
    INTERACTION_FEATURES,
)

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
    'context_df': None, 'explainer': None, 'conformal': None,
    'defaults': None, 'baselines': None, 'catalog': None,
}

# Where each feature group's values actually come from. Surfaced to the
# dashboard so the farmer can see the provenance of every auto-filled value
# instead of being asked to type numbers only a satellite could know.
FEATURE_SOURCE_LABELS = {
    'weather': 'NASA POWER',
    'satellite': 'MODIS / Sentinel-2',
    'historical': 'DCS records',
    'soil': 'SoilGrids',
    'interaction': 'Derived',
}


def _finite(value) -> bool:
    """True when a request value is a usable number (not None/''/NaN/inf)."""
    if value is None or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _build_defaults(df: pd.DataFrame) -> dict:
    """Precompute the district/season → district → season → global mean cascade.

    /predict used to zero-fill any feature missing from the payload. With 32
    features and a form that supplies at most 10, that meant a request for a
    district the context table doesn't cover produced a confident number built
    from soil_ph=0 and prev_year_yield=0. This table is the honest fallback.
    """
    feature_cols = [c for c in ALL_FEATURES if c in df.columns]
    numeric = df[feature_cols].apply(pd.to_numeric, errors='coerce')
    keyed = pd.concat([df[['District', 'Season']], numeric], axis=1)

    def _as_map(grouped) -> dict:
        return {
            key: {c: float(v) for c, v in row.items() if pd.notna(v)}
            for key, row in grouped.iterrows()
        }

    return {
        'district_season': _as_map(
            keyed.groupby(['District', 'Season'])[feature_cols].mean()
        ),
        'district': _as_map(keyed.groupby('District')[feature_cols].mean()),
        'season': _as_map(keyed.groupby('Season')[feature_cols].mean()),
        'global': {
            c: float(v) for c, v in numeric.mean().items() if pd.notna(v)
        },
    }


def _build_baselines(df: pd.DataFrame) -> dict:
    """Historical yield stats per (district, season) — replaces the hardcoded
    13.5 MT/Ha 'Historical Benchmark' the dashboard used to display."""
    if TARGET_COLUMN not in df.columns:
        return {}

    baselines = {}
    for (district, season), grp in df.groupby(['District', 'Season']):
        yields = pd.to_numeric(grp[TARGET_COLUMN], errors='coerce').dropna()
        if yields.empty:
            continue
        baselines[(district, season)] = {
            'district': district,
            'season': season,
            'mean': round(float(yields.mean()), 2),
            'min': round(float(yields.min()), 2),
            'max': round(float(yields.max()), 2),
            'n_years': int(len(yields)),
            'years': sorted(int(y) for y in grp['Year'].dropna().unique()),
        }
    return baselines


def _build_catalog(df: pd.DataFrame) -> list:
    """Districts actually present in the loaded dataset, with the seasons and
    years each one covers.

    config.DISTRICTS is a superset across variants (synthetic has Jaffna and no
    Kurunegala; real has Kurunegala, no Jaffna, and is Yala-only). Advertising
    all five made the dashboard offer combinations that 404.
    """
    catalog = []
    for district, grp in df.groupby('District'):
        catalog.append({
            'name': str(district),
            'seasons': sorted(str(s) for s in grp['Season'].dropna().unique()),
            'years': sorted(int(y) for y in grp['Year'].dropna().unique()),
        })
    return sorted(catalog, key=lambda d: d['name'])


def _resolve_features(data: dict):
    """Build the 32-feature vector, recording where every value came from.

    Resolution order per feature: request value → (district, season) mean →
    district mean → season mean → global mean → 0.0. The three interaction
    terms are always recomputed from the resolved inputs so they can never
    disagree with the features the model actually sees.
    """
    defaults = _state.get('defaults') or {}
    district = data.get('district')
    season = data.get('season')

    tiers = [
        ('district_season_mean', (defaults.get('district_season') or {}).get((district, season), {})),
        ('district_mean', (defaults.get('district') or {}).get(district, {})),
        ('season_mean', (defaults.get('season') or {}).get(season, {})),
        ('global_mean', defaults.get('global') or {}),
    ]

    values, sources = {}, {}
    for feature in ALL_FEATURES:
        if _finite(data.get(feature)):
            values[feature] = float(data[feature])
            sources[feature] = 'user'
            continue
        for tier_name, tier in tiers:
            if feature in tier and math.isfinite(tier[feature]):
                values[feature] = tier[feature]
                sources[feature] = tier_name
                break
        else:
            values[feature] = 0.0
            sources[feature] = 'zero_fallback'

    # Interaction terms are products of resolved inputs, never independent.
    derived = {
        'rainfall_x_ndvi': ('season_total_rainfall', 'season_mean_ndvi'),
        'temp_x_humidity': ('season_avg_temp', 'season_avg_humidity'),
        'ndvi_x_lst': ('season_mean_ndvi', 'season_mean_lst_day'),
    }
    for feature, (left, right) in derived.items():
        if feature in values:
            values[feature] = values[left] * values[right]
            sources[feature] = 'derived'

    return values, sources


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

    # Cache the processed dataset. It backs /context, the default cascade that
    # /predict uses instead of zero-filling, /baseline and /districts.
    integrated_csv = os.path.join(PROCESSED_DIR, 'integrated_dataset.csv')
    if os.path.exists(integrated_csv):
        df = pd.read_csv(integrated_csv)
        _state['context_df'] = df
        _state['defaults'] = _build_defaults(df)
        _state['baselines'] = _build_baselines(df)
        _state['catalog'] = _build_catalog(df)
        print(
            f'[api] Loaded context dataset ({len(df)} rows, '
            f'{len(_state["catalog"])} districts) + default cascade'
        )
    else:
        print('[api] integrated_dataset.csv not found — /context will return 503 '
              'and /predict will fall back to zero-fill.')

    # Optional: conformal (calibrated) interval half-widths per model.
    conf_path = os.path.join(RESULTS_DIR, 'conformal.json')
    if os.path.exists(conf_path):
        with open(conf_path) as f:
            _state['conformal'] = json.load(f)
        print('[api] Loaded conformal intervals')


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

    resolved, feature_sources = _resolve_features(data)
    feature_vec = np.array([[resolved[f] for f in ALL_FEATURES]],
                           dtype=np.float32)
    if _state['scaler'] is not None:
        feature_vec = _state['scaler'].transform(feature_vec)
    prediction = float(_state['model'].predict(feature_vec)[0])

    # Prefer conformal (calibrated) interval half-width; fall back to Gaussian ±1.96·RMSE.
    conf = (_state.get('conformal') or {}).get(_state.get('model_name'))
    rmse = float(_state['metrics'].get('RMSE', 0)) if _state['metrics'] else 0.0
    if conf and conf.get('q'):
        margin = float(conf['q'])
        interval_method = f'conformal_{int(round(conf.get("coverage_target", 0.9) * 100))}pct'
    elif rmse > 0:
        margin = 1.96 * rmse
        interval_method = 'gaussian_1.96rmse'
    else:
        margin = prediction * 0.15
        interval_method = 'heuristic_15pct'

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

    # How much of the vector is grounded in a real record vs a wider fallback.
    n_user = sum(1 for s in feature_sources.values() if s == 'user')
    n_grounded = sum(
        1 for s in feature_sources.values()
        if s in ('user', 'district_season_mean', 'district_mean', 'derived')
    )
    n_zero = sum(1 for s in feature_sources.values() if s == 'zero_fallback')

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
        'interval_method': interval_method,
        'interval_coverage': conf.get('empirical_coverage') if conf else None,
        'feature_sources': feature_sources,
        'resolved_features': {k: round(v, 4) for k, v in resolved.items()},
        'data_completeness': {
            'n_features': len(ALL_FEATURES),
            'n_user_supplied': n_user,
            'n_grounded': n_grounded,
            'n_zero_filled': n_zero,
            'fraction_grounded': round(n_grounded / len(ALL_FEATURES), 3),
        },
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


@app.route('/equation', methods=['GET'])
def equation():
    """The interpretable symbolic-regression yield equation (novelty artifact)."""
    eq_path = os.path.join(RESULTS_DIR, 'symbolic_equation.json')
    if not os.path.exists(eq_path):
        return jsonify({'error': 'symbolic_equation.json not found — run the pipeline first.'}), 404
    with open(eq_path) as f:
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
        'n_years': int(len(sub)),
        'available_years': sorted(int(y) for y in sub['Year'].unique()),
        'source_labels': FEATURE_SOURCE_LABELS,
    })
    return jsonify(payload)


@app.route('/baseline', methods=['GET'])
def baseline():
    """Historical yield stats for a (district, season).

    The dashboard used to compare every prediction against a hardcoded
    13.5 MT/Ha. This serves the real per-district figure instead.
    """
    baselines = _state.get('baselines')
    if not baselines:
        return jsonify({'error': 'baseline data not loaded'}), 503

    district = request.args.get('district', type=str)
    season = request.args.get('season', type=str)
    if not district or not season:
        return jsonify({'error': 'query params district and season are required'}), 400

    stats = baselines.get((district, season))
    if stats is None:
        # Fall back to the district across all seasons before giving up.
        across = [v for (d, _), v in baselines.items() if d == district]
        if not across:
            return jsonify({
                'error': f'no yield history for district={district}',
                'district': district, 'season': season,
            }), 404
        means = [v['mean'] for v in across]
        return jsonify({
            'district': district,
            'season': season,
            'mean': round(sum(means) / len(means), 2),
            'min': min(v['min'] for v in across),
            'max': max(v['max'] for v in across),
            'n_years': sum(v['n_years'] for v in across),
            'years': sorted({y for v in across for y in v['years']}),
            'source': 'district_all_seasons',
        }), 200

    return jsonify({**stats, 'source': 'district_season'})


@app.route('/districts', methods=['GET'])
def list_districts():
    """Districts, seasons and years actually present in the loaded dataset.

    Previously returned config.DISTRICTS unconditionally — a superset across
    data variants — so the dashboard offered Kurunegala under the synthetic
    model and Maha under the (Yala-only) real model, both of which 404.
    """
    catalog = _state.get('catalog')
    df = _state.get('context_df')

    if not catalog:
        # Dataset not loaded — fall back to config so the UI still renders.
        return jsonify({
            'districts': [{'name': d, 'seasons': list(SEASONS), 'years': []}
                          for d in DISTRICTS],
            'seasons': list(SEASONS),
            'years': [],
            'variant': DATA_VARIANT,
            'source': 'config_fallback',
        })

    return jsonify({
        'districts': catalog,
        'seasons': sorted({s for d in catalog for s in d['seasons']}),
        'years': sorted(int(y) for y in df['Year'].dropna().unique()),
        'variant': DATA_VARIANT,
        'source': 'dataset',
    })


# Load at import time so a WSGI/gunicorn server serves a ready model. Previously
# this only ran under __main__, so every /predict behind gunicorn returned 503.
try:
    _load_state()
except FileNotFoundError as exc:
    print(f'[api] Startup warning: {exc}')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=False, host='0.0.0.0', port=port)

"""Flask REST API serving the best big-onion-yield model.

Endpoints:
  GET  /health
  POST /predict
  GET  /models/compare
  GET  /feature-importance
  GET  /context
  GET  /baseline
  GET  /districts
  POST /api/chat
  POST /api/recommend
"""

import json
import math
import os
import re
import sys

# Non-ASCII (Sinhala/Tamil, plus whatever a free-tier LLM writes) now flows
# through this process's stdout/stderr regularly — a print() containing it
# raises UnicodeEncodeError and 500s the request on Windows, where console
# output defaults to the legacy codepage (cp1252) rather than UTF-8 even
# when redirected to a file. Reconfigure once at startup instead of hoping
# every deployment remembers PYTHONIOENCODING=utf-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

import numpy as np
import pandas as pd
import joblib
import shap
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    ALL_FEATURES, DISTRICTS, SEASONS, DATA_VARIANT, TARGET_COLUMN,
    INTERACTION_FEATURES,
)
import explanation_context

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Loads OPENROUTER_API_KEY (and anything else) from a git-ignored .env at the
# project root, if present. Real env vars set another way still win — this
# only fills in what's missing.
load_dotenv(os.path.join(ROOT, '.env'))

# Serve the variant selected by DATA_VARIANT (default 'synthetic'). Set
# DATA_VARIANT=real to serve the models trained on the real collected data.
_SUFFIX = '' if DATA_VARIANT == 'synthetic' else f'_{DATA_VARIANT}'
MODELS_DIR = os.path.join(ROOT, 'outputs', f'models{_SUFFIX}')
RESULTS_DIR = os.path.join(ROOT, 'outputs', f'results{_SUFFIX}')
PROCESSED_DIR = os.path.join(ROOT, 'data', f'processed{_SUFFIX}')

app = Flask(__name__)
CORS(app)

# Set in the environment (or .env) before starting the server, e.g.
#   OPENROUTER_API_KEY=sk-or-... python src/api.py
# /api/chat returns 503 until this is set — no key is bundled or defaulted.
# Uses OpenRouter (openrouter.ai) instead of a paid provider directly, so the
# chat assistant can run on a free-tier model. OPENROUTER_MODEL is
# overridable so a deprecated/rate-limited free model can be swapped without
# a code change — check https://openrouter.ai/models?max_price=0 for what's
# currently free; the list changes over time.
#
# Models tried and rejected:
#   openai/gpt-oss-20b:free    — reliably produced garbled tokens mid-sentence
#                                 (stray non-English characters spliced into
#                                 English words).
#   nvidia/nemotron-3-super-120b-a12b:free — clean for short English chat
#                                 replies, but for the (longer, non-English)
#                                 /api/recommend prompt its chain-of-thought
#                                 leaked directly into `content` ahead of the
#                                 real answer, with no distinct `reasoning`
#                                 field to exclude — so a small max_tokens
#                                 budget truncated the response mid-reasoning,
#                                 before the real answer was ever written.
#   nvidia/nemotron-3-nano-30b-a3b:free — same leakage, and the eventual
#                                 Sinhala text itself was incoherent.
#   nvidia/nemotron-3-ultra-550b-a55b:free — reasoning correctly separated
#                                 into its own field and content was clean,
#                                 fluent Sinhala, but its reasoning is long
#                                 enough that even 1800 max_tokens wasn't
#                                 enough budget to reach a complete answer.
# inclusionai/ling-3.0-flash:free correctly separates reasoning from content
# (so `message['content']` is just the answer) and reliably finishes within
# a ~1800-token budget. Every free model currently on OpenRouter declares
# reasoning support, so "avoid reasoning models" isn't an available option —
# picking one that puts reasoning in its own field, not inline in `content`,
# is what actually matters.
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL', 'inclusionai/ling-3.0-flash:free')
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
# OpenRouter attributes usage to a site for its public model rankings.
# Neither value needs to be publicly reachable.
OPENROUTER_SITE_URL = os.environ.get('OPENROUTER_SITE_URL', 'http://localhost:3000')
OPENROUTER_SITE_NAME = 'AgriSense'

OPENROUTER_FALLBACK_MESSAGE = (
    "I'm having trouble reaching the assistant right now. Please try again "
    "in a moment."
)
OPENROUTER_RATE_LIMIT_MESSAGE = (
    "The assistant is getting a lot of requests right now (it runs on a "
    "free model with limited capacity). Please try again in a minute."
)

CHAT_SYSTEM_PROMPT = """You are the assistant embedded in a crop yield prediction \
dashboard for Sri Lankan onion farmers. Your job is to explain the dashboard's \
own prediction, feature-importance, and historical-yield data in plain, \
farmer-friendly language.

Rules:
- Only use the structured data given to you in the user message. Never invent \
numbers, and never draw on general agricultural knowledge that isn't in that data.
- Avoid ML jargon (SHAP, model, feature, R2, conformal interval). Translate \
technical drivers into plain-language causes, e.g. "rainfall was lower than \
usual this season" rather than "season_total_rainfall had a negative SHAP \
contribution".
- Only state raw numbers (SHAP values, R2, exact interval bounds) if the \
farmer's question specifically asks for exact figures. Otherwise describe \
them qualitatively (e.g. "we're fairly confident" vs "the estimate could \
vary quite a bit").
- Keep answers short: 2-4 sentences, unless the question needs a year-by-year \
comparison.
- If the provided data contains an "error" key, say plainly that a prediction \
isn't available for that district/season/year rather than guessing."""

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


def run_prediction(data: dict):
    """Core prediction logic: resolve features, predict, SHAP, interval.

    `data` must contain 'district'/'season'/'year' and may contain any
    ALL_FEATURES overrides — the same shape POST /predict accepts. Extracted
    from the /predict route so the chat assistant (explanation_context.py)
    can reuse it without duplicating the model/SHAP/interval logic.

    Returns (payload: dict, status: int).
    """
    if _state['model'] is None:
        return {'error': 'Model not loaded'}, 503

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

    return response, 200


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(silent=True) or {}
    payload, status = run_prediction(data)
    return jsonify(payload), status


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


def get_district_baseline(district: str, season: str):
    """Historical yield stats for a (district, season).

    The dashboard used to compare every prediction against a hardcoded
    13.5 MT/Ha. This serves the real per-district figure instead. Extracted
    from the /baseline route so explanation_context.py can reuse it.

    Returns (payload: dict, status: int).
    """
    baselines = _state.get('baselines')
    if not baselines:
        return {'error': 'baseline data not loaded'}, 503

    stats = baselines.get((district, season))
    if stats is None:
        # Fall back to the district across all seasons before giving up.
        across = [v for (d, _), v in baselines.items() if d == district]
        if not across:
            return {
                'error': f'no yield history for district={district}',
                'district': district, 'season': season,
            }, 404
        means = [v['mean'] for v in across]
        return {
            'district': district,
            'season': season,
            'mean': round(sum(means) / len(means), 2),
            'min': min(v['min'] for v in across),
            'max': max(v['max'] for v in across),
            'n_years': sum(v['n_years'] for v in across),
            'years': sorted({y for v in across for y in v['years']}),
            'source': 'district_all_seasons',
        }, 200

    return {**stats, 'source': 'district_season'}, 200


def get_yield_history(district: str, season: str, years_back: int = 5) -> list:
    """Actual yield per year for a (district, season), most recent
    `years_back` years, ascending by year. Reads the same context_df that
    /context and /baseline already load — powers the chat assistant's
    historical-comparison answers.
    """
    df = _state.get('context_df')
    if df is None or TARGET_COLUMN not in df.columns:
        return []
    sub = df[(df['District'] == district) & (df['Season'] == season)]
    sub = sub[['Year', TARGET_COLUMN]].dropna().sort_values('Year')
    tail = sub.tail(years_back)
    return [
        {'year': int(row['Year']), 'yield_MT_per_Ha': round(float(row[TARGET_COLUMN]), 2)}
        for _, row in tail.iterrows()
    ]


@app.route('/baseline', methods=['GET'])
def baseline():
    """Historical yield stats for a (district, season)."""
    district = request.args.get('district', type=str)
    season = request.args.get('season', type=str)
    if not district or not season:
        return jsonify({'error': 'query params district and season are required'}), 400

    payload, status = get_district_baseline(district, season)
    return jsonify(payload), status


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


def _call_openrouter(
    system_prompt: str,
    user_message: str,
    fallback_message: str = OPENROUTER_FALLBACK_MESSAGE,
    rate_limit_message: str = OPENROUTER_RATE_LIMIT_MESSAGE,
    max_tokens: int = 1200,
) -> str:
    """POST to OpenRouter's OpenAI-compatible chat completions endpoint.

    Returns the assistant's reply text — or `fallback_message` /
    `rate_limit_message` if the free-tier model is rate-limited,
    unavailable, or the request fails outright. This is the only external
    network call /api/chat and /api/recommend make, so it's the one place
    that has to degrade gracefully (a busy free model is routine, not
    exceptional) rather than 500 the whole request. Callers whose response
    must be in a specific language (e.g. /api/recommend) pass their own
    localized fallback text; both default to English for /api/chat.
    """
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                # Required by OpenRouter to attribute free-tier usage.
                'HTTP-Referer': OPENROUTER_SITE_URL,
                'X-Title': OPENROUTER_SITE_NAME,
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message},
                ],
                'max_tokens': max_tokens,
                # nemotron-3-super is a reasoning model — without this, its
                # chain-of-thought (in English, regardless of the requested
                # output language) is spliced into `content` ahead of the
                # actual answer, and a small max_tokens budget can truncate
                # the response mid-reasoning before the real answer is ever
                # written. Excluding it keeps `content` to just the answer.
                'reasoning': {'exclude': True},
            },
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        print(f'[api] OpenRouter request failed: {e}')
        return fallback_message

    if resp.status_code == 429:
        print(f'[api] OpenRouter rate limited: {resp.text[:300]}')
        return rate_limit_message
    if resp.status_code != 200:
        print(f'[api] OpenRouter error {resp.status_code}: {resp.text[:300]}')
        return fallback_message

    try:
        body = resp.json()
        choices = body.get('choices') or []
        # For reasoning models, `content` can be None (not just absent) when
        # reasoning consumes the whole max_tokens budget before the model
        # reaches an actual answer — confirmed via direct testing. That's
        # not a parse error the except clause below would catch (.strip()
        # on None raises AttributeError, not KeyError/IndexError), so it's
        # checked explicitly rather than left to crash the request.
        content = (choices[0]['message'].get('content') if choices else None)
        if body.get('error') or not choices or not content:
            print(f'[api] OpenRouter returned no usable content: {body}')
            return fallback_message
        return content.strip()
    except (ValueError, KeyError, IndexError) as e:
        print(f'[api] OpenRouter response parsing failed: {e}')
        return fallback_message


@app.route('/api/chat', methods=['POST'])
def chat():
    """Context-Aware XAI RAG Assistant.

    Not a general agricultural chatbot: every answer is grounded in the
    structured prediction/SHAP/historical data assembled by
    explanation_context.get_prediction_context for the specific
    district/season/year in the request — no vector store, no document
    retrieval, no general-knowledge answers.
    """
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'OPENROUTER_API_KEY is not configured on the server'}), 503

    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()
    district = data.get('district')
    season = data.get('season')
    year = data.get('year')

    if not query or not district or not season or year is None:
        return jsonify({
            'error': 'query, district, season, and year are all required',
        }), 400

    intent = explanation_context.extract_intent(query)
    context_used = explanation_context.get_prediction_context(district, season, year)
    if intent == 'comparison':
        context_used['comparison'] = explanation_context.get_historical_comparison(
            district, season, years_back=5
        )
    context_used['intent'] = intent

    user_message = (
        f'Farmer\'s question: {query}\n\n'
        f'Structured data for {district}, {season} season, {year}:\n'
        f'{json.dumps(context_used, indent=2, default=str)}'
    )

    answer = _call_openrouter(CHAT_SYSTEM_PROMPT, user_message)
    return jsonify({'answer': answer, 'context_used': context_used})


RECOMMEND_LANGUAGE_NAMES = {'en': 'English', 'si': 'Sinhala', 'ta': 'Tamil'}

_SINHALA_SCRIPT_RE = re.compile(r'[඀-෿]')
_TAMIL_SCRIPT_RE = re.compile(r'[஀-௿]')


def _looks_like_target_language(text: str, locale: str) -> bool:
    """Sanity check, not a translator: free-tier reasoning models don't
    reliably keep their chain-of-thought out of `content` (confirmed via
    direct testing — the same model produced a clean Sinhala answer on one
    call and a raw, truncated English reasoning dump on the next, for an
    identical request). Rather than ever show a farmer that broken text,
    require the response to actually be in Sinhala/Tamil script before
    trusting it; fall back to a translated static message otherwise.

    Uses a proportion of script characters, not a raw count: a leaked
    English reasoning trace is long enough that it can rack up 40+
    incidental Sinhala/Tamil characters (measured directly — real leaks
    scored a 0.04-0.46 script ratio) while still being overwhelmingly
    English. A genuine short answer measured ~0.78.
    """
    if locale not in ('si', 'ta'):
        return True
    pattern = _SINHALA_SCRIPT_RE if locale == 'si' else _TAMIL_SCRIPT_RE
    non_space = text.replace(' ', '').replace('\n', '')
    if not non_space:
        return False
    script_chars = len(pattern.findall(text))
    return (script_chars / len(non_space)) >= 0.5

# The LLM call itself is asked to answer in the target language (rather than
# always generating English and translating client-side) — simpler, and
# avoids a second network call per request.
RECOMMEND_SYSTEM_PROMPT_TEMPLATE = """You are an agricultural advisor embedded in a crop \
yield prediction dashboard for Sri Lankan onion farmers. Given a yield \
prediction and its key contributing factors, write ONE short, actionable \
recommendation.

Rules:
- Only use the structured data given to you in the user message. Never invent \
numbers, and never draw on general agricultural knowledge that contradicts \
what the data shows.
- Avoid ML jargon (SHAP, model, feature, R2, conformal interval). Talk about \
plain-language causes, e.g. "rainfall was lower than usual" rather than \
"season_total_rainfall had a negative SHAP contribution".
- Be concrete and actionable: name a specific action the farmer can take this \
season, tied to the specific factor(s) pulling the prediction down. If nothing \
is pulling it down, recommend what to keep doing to maintain the yield.
- Keep it to 2-4 sentences. No headers, no bullet lists, no markdown.
- Respond entirely in {language}. Do not mix in English words, and do not \
mention or explain that you are responding in {language}.
- If the provided data contains an "error" key, say plainly (in {language}) \
that a recommendation isn't available for that district/season/year rather \
than guessing."""

# Backend-generated fallback text for when the LLM call itself fails — kept
# out of the dashboard's messages/*.json since it's server-rendered, not
# client i18n, but still needs to match whatever language the farmer is
# using rather than always falling back to English.
RECOMMEND_FALLBACK_MESSAGES = {
    'en': "We couldn't generate a recommendation right now. Please try again in a moment.",
    'si': "දැනට නිර්දේශයක් ජනනය කළ නොහැක. කරුණාකර මොහොතකින් නැවත උත්සාහ කරන්න.",
    'ta': "இப்போது பரிந்துரையை உருவாக்க முடியவில்லை. தயவுசெய்து சிறிது நேரத்தில் மீண்டும் முயற்சிக்கவும்.",
}
RECOMMEND_RATE_LIMIT_MESSAGES = {
    'en': (
        "The recommendation service is busy right now (it runs on a free "
        "model with limited capacity). Please try again in a minute."
    ),
    'si': (
        "නිර්දේශ සේවාව දැනට කාර්යබහුලයි (එය සීමිත ධාරිතාවකින් යුත් නොමිලේ "
        "ආකෘතියක් මත ක්‍රියාත්මක වේ). කරුණාකර මිනිත්තුවකින් නැවත උත්සාහ කරන්න."
    ),
    'ta': (
        "பரிந்துரை சேவை தற்போது பரபரப்பாக உள்ளது (இது வரம்புக்குட்பட்ட "
        "திறன் கொண்ட இலவச மாதிரியில் இயங்குகிறது). தயவுசெய்து ஒரு "
        "நிமிடத்தில் மீண்டும் முயற்சிக்கவும்."
    ),
}


@app.route('/api/recommend', methods=['POST'])
def recommend():
    """LLM-generated, SHAP-grounded farming recommendation for one
    (district, season, year), in the requested UI language.

    Reuses explanation_context.get_prediction_context — the same grounding
    data /api/chat uses — rather than a separate data path, so the
    recommendation can't drift from what the Predict/Explain tabs show.
    """
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'OPENROUTER_API_KEY is not configured on the server'}), 503

    data = request.get_json(silent=True) or {}
    district = data.get('district')
    season = data.get('season')
    year = data.get('year')
    locale = data.get('locale') if data.get('locale') in RECOMMEND_LANGUAGE_NAMES else 'en'

    if not district or not season or year is None:
        return jsonify({
            'error': 'district, season, and year are all required',
        }), 400

    context_used = explanation_context.get_prediction_context(district, season, year)

    user_message = (
        f'Structured data for {district}, {season} season, {year}:\n'
        f'{json.dumps(context_used, indent=2, default=str)}'
    )

    system_prompt = RECOMMEND_SYSTEM_PROMPT_TEMPLATE.format(
        language=RECOMMEND_LANGUAGE_NAMES[locale]
    )
    recommendation = _call_openrouter(
        system_prompt,
        user_message,
        fallback_message=RECOMMEND_FALLBACK_MESSAGES[locale],
        rate_limit_message=RECOMMEND_RATE_LIMIT_MESSAGES[locale],
        max_tokens=1800,
    )
    if not _looks_like_target_language(recommendation, locale):
        print(f'[api] Recommendation failed the {locale} script check, using fallback: {recommendation[:200]}')
        recommendation = RECOMMEND_FALLBACK_MESSAGES[locale]

    return jsonify({'recommendation': recommendation, 'context_used': context_used})


# Hand explanation_context.py the prediction/baseline/history functions it
# needs. Passed explicitly rather than `import api` from inside
# explanation_context.py — this file can run as module `api` (gunicorn) or as
# `__main__` (`python src/api.py`), and a self-import by name would load this
# module a second time under the other name, loading the model twice.
explanation_context.configure(
    run_prediction=run_prediction,
    get_district_baseline=get_district_baseline,
    get_yield_history=get_yield_history,
)


# Load at import time so a WSGI/gunicorn server serves a ready model. Previously
# this only ran under __main__, so every /predict behind gunicorn returned 503.
try:
    _load_state()
except FileNotFoundError as exc:
    print(f'[api] Startup warning: {exc}')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=False, host='0.0.0.0', port=port)

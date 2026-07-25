"""Structured context assembly + lightweight intent extraction for the
Context-Aware XAI RAG Assistant (POST /api/chat in api.py).

This is deliberately NOT a document/embedding retriever: the "knowledge
base" is the same structured prediction + SHAP + historical-yield data the
dashboard already serves, keyed by (district, season, year). Every function
here calls into api.py's existing prediction/SHAP/baseline logic via
`configure()` — nothing here recomputes a prediction or refits a model.

api.py cannot be imported directly (`import api`) from this module: api.py
is sometimes run as `__main__` (`python src/api.py`) and sometimes imported
as module `api` (gunicorn); a self-import by name would load api.py a
second time under whichever name it wasn't already loaded under, doubling
model load time and memory. `configure()` sidesteps that by having api.py
hand over the specific functions it needs once, at startup.
"""

TOP_N_SHAP_FEATURES = 5

_backend = {
    'run_prediction': None,
    'get_district_baseline': None,
    'get_yield_history': None,
}


def configure(run_prediction, get_district_baseline, get_yield_history) -> None:
    """Called once by api.py at startup with its own run_prediction /
    get_district_baseline / get_yield_history functions."""
    _backend['run_prediction'] = run_prediction
    _backend['get_district_baseline'] = get_district_baseline
    _backend['get_yield_history'] = get_yield_history


# --- Intent extraction ---------------------------------------------------
# Simple keyword matching — no NLU pipeline. Good enough to pick a
# farmer-friendly answer shape for an FYP-scoped assistant.

_INTENT_KEYWORDS = {
    'comparison': [
        'compare', 'comparison', 'vs', 'versus', 'better than', 'worse than',
        'last year', 'previous year', 'previous season', 'other district',
        'difference between', 'higher than', 'lower than', 'trend',
    ],
    'uncertainty': [
        'confidence', 'confident', 'sure', 'certain', 'accurate', 'accuracy',
        'range', 'reliable', 'reliability', 'trust', 'margin', 'error',
        'risk', 'precise',
    ],
    'explanation': [
        'why', 'because', 'reason', 'factor', 'cause', 'explain',
        'what affects', 'what influenced', 'due to', 'drove', 'driving',
    ],
}


def extract_intent(query: str) -> str:
    """Classify a farmer's question into comparison / uncertainty /
    explanation / general via keyword matching against the query text."""
    q = (query or '').lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return intent
    return 'general'


# --- Structured context assembly -----------------------------------------

def get_prediction_context(district: str, season: str, year: int) -> dict:
    """Everything the assistant needs to ground an answer for one
    (district, season, year): current prediction, top SHAP drivers,
    confidence interval, and recent yield history.
    """
    run_prediction = _backend['run_prediction']
    get_district_baseline = _backend['get_district_baseline']
    get_yield_history = _backend['get_yield_history']

    prediction, status = run_prediction({
        'district': district, 'season': season, 'year': year,
    })
    if status != 200:
        return {
            'error': prediction.get('error', 'prediction unavailable'),
            'district': district, 'season': season, 'year': year,
        }

    shap_values = prediction.get('shap_values') or {}
    top_shap = sorted(
        shap_values.items(), key=lambda kv: abs(kv[1]), reverse=True
    )[:TOP_N_SHAP_FEATURES]

    baseline_payload, baseline_status = get_district_baseline(district, season)
    baseline = baseline_payload if baseline_status == 200 else None

    history = get_yield_history(district, season, years_back=5)

    return {
        'district': district,
        'season': season,
        'year': year,
        'predicted_yield_MT_per_Ha': prediction.get('predicted_yield_MT_per_Ha'),
        'confidence_lower': prediction.get('confidence_lower'),
        'confidence_upper': prediction.get('confidence_upper'),
        'confidence': prediction.get('confidence'),
        'interval_method': prediction.get('interval_method'),
        'model_r2': prediction.get('model_r2'),
        'top_shap_features': [
            {'feature': name, 'shap_value': round(value, 4)}
            for name, value in top_shap
        ],
        'historical_baseline': baseline,
        'recent_yield_history': history,
    }


def get_historical_comparison(district: str, season: str, years_back: int = 5) -> dict:
    """Historical yield trend for a (district, season) — used when the
    farmer's question is a comparison ('how does this compare to last year?
    to other districts?')."""
    get_district_baseline = _backend['get_district_baseline']
    get_yield_history = _backend['get_yield_history']

    baseline_payload, status = get_district_baseline(district, season)
    history = get_yield_history(district, season, years_back=years_back)

    return {
        'district': district,
        'season': season,
        'baseline': baseline_payload if status == 200 else None,
        'recent_yield_history': history,
    }

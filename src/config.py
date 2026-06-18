"""Project-wide configuration. Tweak hyperparameters here, not inside model files."""

import os

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Data variant: 'synthetic' (default) or 'real'. Selected via the DATA_VARIANT
# env var (set automatically by `python main.py --real`). It only changes WHERE
# artifacts are read/written so the synthetic demo stays untouched as a fallback.
# ---------------------------------------------------------------------------
DATA_VARIANT = os.environ.get('DATA_VARIANT', 'synthetic')
_VARIANT_SUFFIX = '' if DATA_VARIANT == 'synthetic' else f'_{DATA_VARIANT}'

MODELS_DIR = f'outputs/models{_VARIANT_SUFFIX}'
RESULTS_DIR = f'outputs/results{_VARIANT_SUFFIX}'
PROCESSED_DIR = f'data/processed{_VARIANT_SUFFIX}'
PLOTS_DIR = f'outputs/plots{_VARIANT_SUFFIX}/results'
TRAIN_PLOTS_DIR = f'outputs/plots{_VARIANT_SUFFIX}/training'
EDA_PLOTS_DIR = f'outputs/plots{_VARIANT_SUFFIX}/eda'

# Real collected dataset (monthly, Yala-only). Aggregated to the seasonal grain
# by data_loader.load_collected_data().
COLLECTED_FILE = 'data/collected/FYP data(manual) - onion_unique_per_key.csv'

# Superset of districts across synthetic (Jaffna) and real (Kurunegala) data so
# the preprocessor accepts both. The synthetic generator iterates its own dict.
DISTRICTS = ['Matale', 'Anuradhapura', 'Polonnaruwa', 'Jaffna', 'Kurunegala']
SEASONS = ['Yala', 'Maha']
TARGET_COLUMN = 'Avg_Yield_MT_per_Ha'
YEAR_RANGE = (2004, 2025)

YALA_MONTHS = [4, 5, 6, 7, 8]
MAHA_MONTHS = [10, 11, 12, 1, 2, 3]

WEATHER_FEATURES = [
    'season_avg_temp', 'season_total_rainfall', 'season_avg_humidity',
    'season_avg_solar_rad', 'growing_degree_days', 'heat_stress_days',
    'drought_index_spi', 'temp_range', 'max_daily_rainfall',
]

SATELLITE_FEATURES = [
    'season_mean_ndvi', 'season_max_ndvi', 'season_min_ndvi',
    'ndvi_std', 'ndvi_anomaly', 'time_to_peak_ndvi', 'ndvi_growth_rate',
    'season_mean_evi', 'season_mean_ndwi', 'season_mean_lst_day',
    'season_mean_lst_night',
]

HISTORICAL_FEATURES = [
    'prev_season_yield', 'prev_year_yield', 'yield_3yr_avg',
    'season_indicator', 'extent_prev_season',
]

SOIL_FEATURES = ['soil_ph', 'organic_carbon', 'clay_pct', 'sand_pct']

INTERACTION_FEATURES = ['rainfall_x_ndvi', 'temp_x_humidity', 'ndvi_x_lst']

ALL_FEATURES = (
    WEATHER_FEATURES + SATELLITE_FEATURES
    + HISTORICAL_FEATURES + SOIL_FEATURES + INTERACTION_FEATURES
)

# ML hyperparameter search spaces
RF_PARAMS = {
    'n_estimators': [100, 200, 500],
    'max_depth': [5, 10, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
}

XGB_PARAMS = {
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 5, 7],
    'n_estimators': [100, 300, 500],
    'subsample': [0.7, 0.8, 1.0],
    'reg_alpha': [0, 0.1, 1.0],
    'reg_lambda': [1.0, 1.5, 2.0],
}

# 'auto' is deprecated for non-precomputed kernels in newer sklearn.
SVR_PARAMS = {
    'kernel': ['rbf', 'linear', 'poly'],
    'C': [0.1, 1, 10, 100],
    'gamma': ['scale', 0.01, 0.1],
    'epsilon': [0.01, 0.1, 0.5],
}

# Reduced grids used inside LOYO outer-CV inner search to keep runtime sane.
RF_PARAMS_FAST = {'n_estimators': [200], 'max_depth': [10, None], 'min_samples_leaf': [1, 2]}
XGB_PARAMS_FAST = {'learning_rate': [0.05], 'max_depth': [3, 5], 'n_estimators': [300], 'subsample': [0.8]}
SVR_PARAMS_FAST = {'kernel': ['rbf'], 'C': [1, 10], 'gamma': ['scale'], 'epsilon': [0.1]}

# DL architecture
LSTM_UNITS = [64, 32]
DROPOUT_RATE = 0.2
DENSE_UNITS = 16
LEARNING_RATE = 0.001
BATCH_SIZE = 16
MAX_EPOCHS = 200
EARLY_STOPPING_PATIENCE = 20
SEQUENCE_LENGTH = 5  # 5 monthly timesteps in growing season

# When generated/synthetic data is in use, cap DL epochs to keep LOYO runtime sane.
SYNTHETIC_MODE_DL_EPOCHS = 50

# Evaluation
TRAIN_YEARS = list(range(2004, 2020))
TEST_YEARS = list(range(2020, 2024))
TARGET_R2 = 0.75

# Number of weather variables emitted per monthly timestep in synthesised sequences.
N_WEATHER_PER_STEP = 4  # temp, rainfall, humidity, solar_rad

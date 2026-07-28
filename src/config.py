"""Project-wide configuration. Tweak hyperparameters here, not inside model files."""

import os

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Data variant: 'synthetic' (default) or 'real'. Selected via the DATA_VARIANT
# env var (set automatically by `python main.py --real`). It only changes WHERE
# artifacts are read/written so the synthetic demo stays untouched as a fallback.
# ---------------------------------------------------------------------------
VALID_DATA_VARIANTS = ('synthetic', 'real')
DATA_VARIANT = os.environ.get('DATA_VARIANT', 'synthetic')

# Fail loudly on a typo. The suffix below turns ANY string into a directory name, so
# `DATA_VARIANT=test` used to resolve to outputs/models_test — a directory that does not
# exist — and the API would still start, serve /districts from its hardcoded fallback, and
# then return 503 from every endpoint that needs a model or the panel. The startup warning
# said "run main.py first", which sends you off to retrain something that was never the
# problem. A typo must not be able to produce a half-running server.
if DATA_VARIANT not in VALID_DATA_VARIANTS:
    raise ValueError(
        f'DATA_VARIANT={DATA_VARIANT!r} is not valid. '
        f'Use one of {", ".join(VALID_DATA_VARIANTS)} — for example:\n'
        f'    DATA_VARIANT=real PORT=5050 python src/api.py'
    )

_VARIANT_SUFFIX = '' if DATA_VARIANT == 'synthetic' else f'_{DATA_VARIANT}'

MODELS_DIR = f'outputs/models{_VARIANT_SUFFIX}'
RESULTS_DIR = f'outputs/results{_VARIANT_SUFFIX}'
PROCESSED_DIR = f'data/processed{_VARIANT_SUFFIX}'
PLOTS_DIR = f'outputs/plots{_VARIANT_SUFFIX}/results'
TRAIN_PLOTS_DIR = f'outputs/plots{_VARIANT_SUFFIX}/training'
EDA_PLOTS_DIR = f'outputs/plots{_VARIANT_SUFFIX}/eda'

# Real collected dataset (monthly, Yala-only). Aggregated to the seasonal grain
# by data_loader.load_collected_data().
#
# SUPERSEDED as the target source: 40% of its month-rows are `source=synthetic`,
# and the fabrication reaches the target (yield varies month-to-month within every
# cell, and the target was their unweighted mean). Kept for covariate comparison only.
COLLECTED_FILE = 'data/collected/FYP data(manual) - onion_unique_per_key.csv'

# Authoritative source: 87 real DCS month-records with extent and production reported
# separately, so the target can use the standard definition sum(MT)/sum(ha).
# See src/dcs_panel.py. Parse with thousands=',' — some values are written "3,091".
DCS_FILE = 'data/collected/FYP data(manual) - real all datas.csv'

# How much each district-year counts in the loss. A 4 ha cell gives a far noisier
# yield estimate than a 1,765 ha one. 'extent' spans 440x here and would erase
# Kurunegala (losing a whole district), so sqrt is the default compromise.
# One of: 'equal' | 'sqrt_extent' | 'extent'.
OBS_WEIGHT_MODE = 'sqrt_extent'

# Agronomically plausible range for Sri Lankan big onion (MT/ha). Cells outside it are
# FLAGGED in the data-quality report, never silently dropped or corrected.
IMPLAUSIBLE_YIELD_RANGE = (5.0, 30.0)

# Separate, much harder threshold: a MONTH-record implying more than this is not an
# unusual harvest, it is a transcription/reporting error. The world record for onion is
# ~100 MT/ha under intensive irrigation; Sri Lanka averages 15-20. Six records breach it,
# topping out at 442 MT/ha (Matale, October 2025), and they distort two LOYO folds.
MAX_PHYSICAL_YIELD = 60.0

# Drop those month-records when aggregating. The cell survives on its remaining months.
# Set False to reproduce the uncleaned panel for the sensitivity table.
EXCLUDE_IMPOSSIBLE_RECORDS = True

MONTH_TO_NUM = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12,
}

DISTRICT_FIXES = {'Polannaruwa': 'Polonnaruwa'}

# District centroids for the NASA POWER daily pull (src/data_collection/nasa_power.py).
# The existing daily file is a SINGLE point (7.8731, 80.7718) and therefore cannot
# distinguish districts at all. Caveat to state in the report: NASA POWER's grid is
# ~0.5deg x 0.625deg, so Matale and Kurunegala (~29 km apart) may resolve to the same
# cell; Anuradhapura and Polonnaruwa are comfortably separated.
DISTRICT_CENTROIDS = {
    'Anuradhapura': (8.3114, 80.4037),
    'Kurunegala': (7.4863, 80.3647),
    'Matale': (7.4675, 80.6234),
    'Polonnaruwa': (7.9403, 81.0188),
}

# Superset of districts across synthetic (Jaffna) and real (Kurunegala) data so
# the preprocessor accepts both. The synthetic generator iterates its own dict.
DISTRICTS = ['Matale', 'Anuradhapura', 'Polonnaruwa', 'Jaffna', 'Kurunegala']
SEASONS = ['Yala', 'Maha']
TARGET_COLUMN = 'Avg_Yield_MT_per_Ha'
YEAR_RANGE = (2004, 2025)

YALA_MONTHS = [4, 5, 6, 7, 8]
MAHA_MONTHS = [10, 11, 12, 1, 2, 3]

# Months the DCS records actually span. Note this does NOT match YALA_MONTHS above,
# which was never checked against the data; every real extent/production record falls
# in June-November. Used as the outer envelope for seasonal aggregation, before
# phenology narrows it per district-year.
GROWING_SEASON_MONTHS = [6, 7, 8, 9, 10, 11]

# Real MODIS 16-day composites: 23/year/district, 595 per district back to 2000.
NDVI_FILE = 'data/collected/FYP data(manual) - NDVI-EVI.csv'

# Pre-sample years used to standardise rainfall (SPI) and NDVI anomalies. No LOYO fold
# ever tests on these, so the anomalies are leak-free by construction — the original
# code z-scored against the full 2019-2025 panel, leaking every fold's held-out year.
CLIMATOLOGY_YEARS = (2000, 2018)

# Month span searched for the NDVI green-up/senescence curve. Wider than
# GROWING_SEASON_MONTHS so the rising and falling limbs are both observed — anchoring
# needs to see the crop emerge and die back, not just the part DCS reports on.
PHENOLOGY_WINDOW = (4, 12)

# Mid-month day-of-year, used to place the DCS monthly harvest records on a calendar.
MONTH_MID_DOY = {
    'January': 16, 'February': 46, 'March': 75, 'April': 105, 'May': 136, 'June': 166,
    'July': 196, 'August': 227, 'September': 258, 'October': 288, 'November': 319,
    'December': 350,
}

# Thermal-time phenology (src/phenology.py). Onion development tracks accumulated heat,
# not calendar days, so the season is located by walking GDD back from the DCS harvest
# date. GDD_REQUIRED_LIT is the literature anchor PADR shrinks toward, not a fixed
# constant — it is a LEARNABLE parameter, which is what makes the alignment itself
# estimated rather than assumed.
GDD_BASE_TEMP = 10.0          # McMaster & Wilhelm 1997
GDD_REQUIRED_LIT = 1500.0     # °C-days, transplant to maturity for bulb onion
GDD_REQUIRED_BOUNDS = (900.0, 2200.0)

# Districts with no MODIS export of their own borrow their nearest neighbour's series.
# Kurunegala also shares a NASA POWER grid cell with Matale (byte-identical daily
# weather), so this leaves its inputs identical to Matale's — rows are flagged
# `ndvi_is_proxy` and the limitation must be stated in the report.
NDVI_PROXY_DISTRICTS = {'Kurunegala': 'Matale'}

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

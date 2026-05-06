# 🤖 Claude Code Agent Instructions
# Big Onion Yield Prediction — ML/DL Model Development
# Arkam B.H.M. (214019K) | Agro AI | University of Moratuwa FYP 2026

---

## 🎯 AGENT OVERVIEW

You are an expert ML/DL engineer building a complete yield prediction system
for big onion (Allium cepa) in Sri Lanka as part of a Final Year Project at
the University of Moratuwa. Your task is to build, train, evaluate, and
compare machine learning and deep learning models for predicting big onion
harvest yield across four districts: Matale, Anuradhapura, Polonnaruwa,
and Jaffna.

**This is Arkam's individual research component. The novelty is:**
1. First ML vs DL comparison for vegetable yield prediction with scarce data
2. Novel CNN-LSTM hybrid for bimodal monsoon (Maha/Yala) seasonal system
3. Multi-source ablation study quantifying each data source's contribution

---

## 📁 PROJECT STRUCTURE TO CREATE

```
big_onion_yield_prediction/
│
├── data/
│   ├── raw/                          # Place raw CSV files here
│   │   ├── dcs_yield.csv             # DCS historical yield data
│   │   ├── nasa_power_weather.csv    # NASA POWER daily weather
│   │   ├── modis_ndvi_evi.csv        # MODIS NDVI/EVI time series
│   │   ├── sentinel2_indices.csv     # Sentinel-2 monthly indices
│   │   ├── chirps_rainfall.csv       # CHIRPS monthly rainfall
│   │   ├── modis_lst.csv             # MODIS land surface temperature
│   │   └── soil_data.csv             # SoilGrids soil characteristics
│   │
│   ├── processed/                    # Cleaned and merged datasets
│   │   ├── integrated_dataset.csv    # Final merged training dataset
│   │   ├── features_tabular.csv      # ML-ready tabular features
│   │   └── features_sequential.pkl   # DL-ready sequential features
│   │
│   └── synthetic/                    # Synthetic data for testing
│       └── synthetic_dataset.csv     # Used if real data not available
│
├── src/
│   ├── config.py                     # All hyperparameters and settings
│   ├── data_loader.py                # Load and validate all data sources
│   ├── preprocessor.py               # Cleaning, alignment, normalization
│   ├── feature_engineer.py           # Feature engineering pipeline
│   ├── eda.py                        # Exploratory data analysis
│   ├── ml_models.py                  # Random Forest, XGBoost, SVR
│   ├── dl_models.py                  # LSTM, BiLSTM, CNN, CNN-LSTM hybrid
│   ├── evaluator.py                  # Metrics, LOYO-CV, statistical tests
│   ├── ablation.py                   # Ablation study across data sources
│   ├── explainer.py                  # SHAP feature importance
│   ├── visualizer.py                 # All plots and result charts
│   └── api.py                        # Flask/FastAPI model serving API
│
├── notebooks/
│   ├── 01_EDA.ipynb                  # Exploratory data analysis
│   ├── 02_ML_Models.ipynb            # ML model training and comparison
│   ├── 03_DL_Models.ipynb            # DL model training and comparison
│   ├── 04_Hybrid_CNN_LSTM.ipynb      # Novel hybrid architecture
│   ├── 05_Ablation_Study.ipynb       # Data source contribution study
│   └── 06_Final_Comparison.ipynb     # Complete results and SHAP
│
├── outputs/
│   ├── models/                       # Saved trained models (.pkl, .h5)
│   ├── plots/                        # All generated figures
│   │   ├── eda/                      # EDA plots
│   │   ├── training/                 # Learning curves
│   │   └── results/                  # Comparison charts, SHAP plots
│   └── results/                      # CSV result tables
│       ├── model_comparison.csv
│       ├── ablation_results.csv
│       └── final_summary.txt
│
├── main.py                           # Run complete pipeline
├── requirements.txt                  # All Python dependencies
└── README.md                         # Project documentation
```

---

## ⚙️ STEP 0: SETUP AND CONFIGURATION

### Step 0.1 — Create requirements.txt

```
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=2.0.0
tensorflow>=2.13.0
keras>=2.13.0
shap>=0.42.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0
scipy>=1.11.0
joblib>=1.3.0
flask>=3.0.0
flask-cors>=4.0.0
statsmodels>=0.14.0
tqdm>=4.65.0
```

### Step 0.2 — Create config.py

```python
# config.py — All hyperparameters and settings
# Change settings here, not inside model files

RANDOM_STATE = 42

# Project settings
DISTRICTS = ['Matale', 'Anuradhapura', 'Polonnaruwa', 'Jaffna']
SEASONS = ['Yala', 'Maha']
TARGET_COLUMN = 'Avg_Yield_MT_per_Ha'
YEAR_RANGE = (2004, 2023)

# Yala season: April–August (months 4–8)
# Maha season: October–March (months 10–3)
YALA_MONTHS = [4, 5, 6, 7, 8]
MAHA_MONTHS = [10, 11, 12, 1, 2, 3]

# Feature groups for ablation study
WEATHER_FEATURES = [
    'season_avg_temp', 'season_total_rainfall', 'season_avg_humidity',
    'season_avg_solar_rad', 'growing_degree_days', 'heat_stress_days',
    'drought_index_spi', 'temp_range', 'max_daily_rainfall'
]
SATELLITE_FEATURES = [
    'season_mean_ndvi', 'season_max_ndvi', 'season_min_ndvi',
    'ndvi_std', 'ndvi_anomaly', 'time_to_peak_ndvi', 'ndvi_growth_rate',
    'season_mean_evi', 'season_mean_ndwi', 'season_mean_lst_day',
    'season_mean_lst_night'
]
HISTORICAL_FEATURES = [
    'prev_season_yield', 'prev_year_yield', 'yield_3yr_avg',
    'season_indicator', 'extent_prev_season'
]
SOIL_FEATURES = [
    'soil_ph', 'organic_carbon', 'clay_pct', 'sand_pct'
]
INTERACTION_FEATURES = [
    'rainfall_x_ndvi', 'temp_x_humidity', 'ndvi_x_lst'
]

ALL_FEATURES = (WEATHER_FEATURES + SATELLITE_FEATURES +
                HISTORICAL_FEATURES + SOIL_FEATURES + INTERACTION_FEATURES)

# ML Hyperparameter search spaces
RF_PARAMS = {
    'n_estimators': [100, 200, 500],
    'max_depth': [5, 10, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

XGB_PARAMS = {
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 5, 7],
    'n_estimators': [100, 300, 500],
    'subsample': [0.7, 0.8, 1.0],
    'reg_alpha': [0, 0.1, 1.0],
    'reg_lambda': [1.0, 1.5, 2.0]
}

SVR_PARAMS = {
    'kernel': ['rbf', 'linear', 'poly'],
    'C': [0.1, 1, 10, 100],
    'gamma': ['scale', 'auto', 0.01, 0.1],
    'epsilon': [0.01, 0.1, 0.5]
}

# DL Architecture settings
LSTM_UNITS = [64, 32]
DROPOUT_RATE = 0.2
DENSE_UNITS = 16
LEARNING_RATE = 0.001
BATCH_SIZE = 16
MAX_EPOCHS = 200
EARLY_STOPPING_PATIENCE = 20
SEQUENCE_LENGTH = 5          # 5 months in growing season

# Evaluation
TRAIN_YEARS = list(range(2004, 2020))
TEST_YEARS = list(range(2020, 2024))
TARGET_R2 = 0.75
```

---

## 📋 STEP 1: DATA LOADING AND SYNTHETIC DATA GENERATION

### Instructions for Claude Code:

**Check if real data files exist in data/raw/. If ANY file is missing,
generate synthetic data for the ENTIRE pipeline so all steps can run.**

Create `src/data_loader.py`:

```python
"""
Data Loader — Loads all data sources and generates synthetic if needed.
Priority: Always try real data first. Fall back to synthetic if missing.
"""

import os
import pandas as pd
import numpy as np
from config import *

def check_data_availability():
    """Check which real data files are available."""
    required_files = {
        'dcs_yield': 'data/raw/dcs_yield.csv',
        'nasa_power': 'data/raw/nasa_power_weather.csv',
        'modis_ndvi': 'data/raw/modis_ndvi_evi.csv',
        'sentinel2': 'data/raw/sentinel2_indices.csv',
        'chirps': 'data/raw/chirps_rainfall.csv',
        'modis_lst': 'data/raw/modis_lst.csv',
        'soil': 'data/raw/soil_data.csv',
    }
    available = {}
    for key, path in required_files.items():
        available[key] = os.path.exists(path)
        status = "✓ Found" if available[key] else "✗ Missing"
        print(f"  {status}: {path}")
    return available

def generate_synthetic_data():
    """
    Generate realistic synthetic big onion data for pipeline testing.

    Distributions based on:
    - DCS Big Onion Survey Reports 2004-2023
    - Matale Yala avg yield: 12-24 MT/Ha
    - Maha off-season avg yield: 6-15 MT/Ha
    - National avg: 9.9-19.7 MT/Ha
    """
    np.random.seed(RANDOM_STATE)
    rows = []

    district_params = {
        'Matale':        {'yala_yield': (16, 4), 'maha_yield': (8, 3),  'rainfall': (850, 150)},
        'Anuradhapura':  {'yala_yield': (15, 4), 'maha_yield': (7, 3),  'rainfall': (900, 180)},
        'Polonnaruwa':   {'yala_yield': (14, 3), 'maha_yield': (6, 2),  'rainfall': (1100, 200)},
        'Jaffna':        {'yala_yield': (12, 4), 'maha_yield': (5, 2),  'rainfall': (600, 120)},
    }

    for year in range(2004, 2024):
        for district in DISTRICTS:
            params = district_params[district]
            climate_shock = np.random.normal(0, 0.5)

            for season in SEASONS:
                is_yala = 1 if season == 'Yala' else 0
                mu, sigma = (params['yala_yield'] if season == 'Yala'
                             else params['maha_yield'])
                yield_val = max(2, np.random.normal(mu, sigma) + climate_shock)

                rainfall = max(100, np.random.normal(
                    params['rainfall'][0] if season == 'Yala'
                    else params['rainfall'][0] * 1.3,
                    params['rainfall'][1]
                ))

                ndvi_base = 0.3 + (yield_val / 30)
                ndvi = min(0.85, max(0.1, ndvi_base + np.random.normal(0, 0.08)))
                evi_base = ndvi * 0.85
                ndwi = min(0.4, max(-0.2, -0.1 + (rainfall / 2000)))

                row = {
                    'Year': year, 'Season': season, 'District': district,
                    'Avg_Yield_MT_per_Ha': round(yield_val, 2),
                    'season_indicator': is_yala,
                    # Weather features
                    'season_total_rainfall': round(rainfall, 1),
                    'season_avg_temp': round(np.random.normal(
                        28 if season == 'Yala' else 26, 1.5), 1),
                    'season_avg_humidity': round(np.random.normal(72, 8), 1),
                    'season_avg_solar_rad': round(np.random.normal(18, 2), 2),
                    'growing_degree_days': round(max(200, np.random.normal(
                        650 if season == 'Yala' else 580, 50)), 1),
                    'heat_stress_days': max(0, int(np.random.normal(
                        8 if season == 'Yala' else 3, 3))),
                    'drought_index_spi': round(np.random.normal(0, 1), 3),
                    'temp_range': round(np.random.normal(10, 2), 1),
                    'max_daily_rainfall': round(np.random.normal(65, 20), 1),
                    # Satellite features
                    'season_mean_ndvi': round(ndvi, 4),
                    'season_max_ndvi': round(min(0.9, ndvi + 0.1), 4),
                    'season_min_ndvi': round(max(0.05, ndvi - 0.15), 4),
                    'ndvi_std': round(np.random.uniform(0.02, 0.08), 4),
                    'ndvi_anomaly': round(np.random.normal(0, 0.06), 4),
                    'time_to_peak_ndvi': round(np.random.normal(65, 12), 1),
                    'ndvi_growth_rate': round(np.random.uniform(0.003, 0.01), 5),
                    'season_mean_evi': round(evi_base + np.random.normal(0, 0.05), 4),
                    'season_mean_ndwi': round(ndwi, 4),
                    'season_mean_lst_day': round(np.random.normal(
                        34 if season == 'Yala' else 30, 2), 1),
                    'season_mean_lst_night': round(np.random.normal(
                        22 if season == 'Yala' else 19, 2), 1),
                    # Soil features (static per district, slight variation)
                    'soil_ph': round({'Matale': 6.2, 'Anuradhapura': 6.5,
                                      'Polonnaruwa': 6.8, 'Jaffna': 7.1
                                      }[district] + np.random.normal(0, 0.1), 2),
                    'organic_carbon': round(np.random.normal(1.8, 0.4), 3),
                    'clay_pct': round(np.random.normal(28, 5), 1),
                    'sand_pct': round(np.random.normal(45, 8), 1),
                    # Historical (computed after sorting)
                    'prev_season_yield': None,
                    'prev_year_yield': None,
                    'yield_3yr_avg': None,
                    'extent_prev_season': round(np.random.normal(400, 120), 0),
                }
                rows.append(row)

    df = pd.DataFrame(rows).sort_values(['District', 'Season', 'Year']).reset_index(drop=True)

    # Compute historical yield features
    for district in DISTRICTS:
        for season in SEASONS:
            mask = (df['District'] == district) & (df['Season'] == season)
            df.loc[mask, 'prev_season_yield'] = df.loc[mask, TARGET_COLUMN].shift(1)
            df.loc[mask, 'prev_year_yield'] = df.loc[mask, TARGET_COLUMN].shift(1)
            df.loc[mask, 'yield_3yr_avg'] = (df.loc[mask, TARGET_COLUMN]
                                              .shift(1).rolling(3).mean())

    # Interaction features
    df['rainfall_x_ndvi'] = df['season_total_rainfall'] * df['season_mean_ndvi']
    df['temp_x_humidity'] = df['season_avg_temp'] * df['season_avg_humidity']
    df['ndvi_x_lst'] = df['season_mean_ndvi'] * df['season_mean_lst_day']

    df = df.dropna().reset_index(drop=True)
    os.makedirs('data/synthetic', exist_ok=True)
    df.to_csv('data/synthetic/synthetic_dataset.csv', index=False)
    print(f"  ✓ Synthetic dataset: {len(df)} observations, {len(df.columns)} features")
    return df

def load_data():
    """Main data loading function. Uses real data if available, synthetic otherwise."""
    print("\n" + "="*60)
    print("STEP 1: DATA LOADING")
    print("="*60)
    print("Checking data availability...")
    available = check_data_availability()

    if all(available.values()):
        print("\n✓ All data files found. Loading real data...")
        return load_real_data()
    else:
        missing = [k for k, v in available.items() if not v]
        print(f"\n⚠ Missing files: {missing}")
        print("→ Generating synthetic data for pipeline testing...")
        print("→ Replace with real data when available\n")
        return generate_synthetic_data()

def load_real_data():
    """Load and merge all real data sources into unified dataset."""
    # Load each source
    dcs = pd.read_csv('data/raw/dcs_yield.csv')
    weather = pd.read_csv('data/raw/nasa_power_weather.csv')
    modis = pd.read_csv('data/raw/modis_ndvi_evi.csv')
    sentinel = pd.read_csv('data/raw/sentinel2_indices.csv')
    chirps = pd.read_csv('data/raw/chirps_rainfall.csv')
    lst = pd.read_csv('data/raw/modis_lst.csv')
    soil = pd.read_csv('data/raw/soil_data.csv')

    # Merge on District, Year, Season
    df = dcs.copy()
    for source in [weather, modis, sentinel, chirps, lst, soil]:
        merge_keys = [c for c in ['District', 'Year', 'Season'] if c in source.columns]
        df = df.merge(source, on=merge_keys, how='left')

    print(f"  ✓ Real data loaded: {len(df)} observations, {len(df.columns)} features")
    return df
```

---

## 📊 STEP 2: EXPLORATORY DATA ANALYSIS

Create `src/eda.py`. Generate and save these plots to `outputs/plots/eda/`:

```
REQUIRED EDA OUTPUTS:
│
├── yield_distribution.png
│   → Histogram + KDE of yield values overall
│   → Separate plots by district (4 subplots)
│   → Separate plots by season (Yala vs Maha)
│
├── yield_timeseries.png
│   → Line plot of yield over years for each district
│   → Mark Maha and Yala seasons differently
│   → Include trend line
│
├── correlation_heatmap.png
│   → Pearson correlation of all features vs yield
│   → Top 15 most correlated features highlighted
│
├── feature_distributions.png
│   → Distribution of top 10 features
│   → Show NDVI, rainfall, temperature, yield together
│
├── seasonal_comparison.png
│   → Box plots: Yala yield vs Maha yield per district
│   → Statistical significance markers
│
└── district_comparison.png
    → Bar chart: average yield by district and season
    → Error bars showing standard deviation
```

**Key statistics to PRINT during EDA:**
- Total observations, missing values per feature
- Mean, std, min, max yield by district and season
- Correlation coefficient of each feature with yield (ranked)
- Number of Yala vs Maha season records

---

## 🌲 STEP 3: MACHINE LEARNING MODELS

Create `src/ml_models.py`:

### 3.1 Leave-One-Year-Out Cross-Validation (REQUIRED)

```
LOYO-CV Logic:
For each year Y in YEAR_RANGE:
    Train = all data EXCEPT year Y
    Test  = all data FROM year Y
    Predict yield for year Y
    Record RMSE, MAE, R²

Final metrics = average across all held-out years
This preserves temporal order and prevents data leakage.
```

### 3.2 Models to Implement

**Model 1 — Random Forest:**
```
- GridSearchCV with RF_PARAMS from config.py
- CV strategy: TimeSeriesSplit(n_splits=5)
- Save best model to outputs/models/rf_best.pkl
- Extract and plot feature importance (MDI method)
```

**Model 2 — XGBoost:**
```
- GridSearchCV with XGB_PARAMS from config.py
- CV strategy: TimeSeriesSplit(n_splits=5)
- Save best model to outputs/models/xgb_best.pkl
- Extract and plot feature importance (gain method)
- Plot XGBoost training curve (loss vs iterations)
```

**Model 3 — SVR:**
```
- GridSearchCV with SVR_PARAMS from config.py
- IMPORTANT: Scale features with StandardScaler BEFORE SVR
- Save scaler to outputs/models/svr_scaler.pkl
- Save best model to outputs/models/svr_best.pkl
```

### 3.3 Required Outputs for Each ML Model

```
For each model (RF, XGBoost, SVR):
│
├── LOYO-CV results table:
│   Year | District | Actual_Yield | Predicted_Yield | Error
│
├── Metrics summary:
│   RMSE | MAE | R² | MAPE | Best_Params
│
├── Actual vs Predicted scatter plot
│   → Perfect prediction line (y=x)
│   → Color by district
│   → R² annotation
│
├── Residual plot
│   → Residuals vs predicted values
│   → Horizontal line at 0
│   → Highlight outliers > 2 std dev
│
└── Feature importance plot (RF and XGBoost only)
    → Top 15 features ranked
    → Horizontal bar chart
```

---

## 🧠 STEP 4: DEEP LEARNING MODELS

Create `src/dl_models.py`:

### 4.1 Data Preparation for DL

```
For LSTM/BiLSTM:
  Input shape: (samples, SEQUENCE_LENGTH, n_weather_features)
  SEQUENCE_LENGTH = 5 (5 monthly timesteps in growing season)
  Features per timestep: monthly weather variables (temp, rainfall, humidity, solar)
  
For CNN-LSTM Hybrid:
  Branch 1 (CNN): Input shape = (samples, n_satellite_features, 1)
  Branch 2 (LSTM): Input shape = (samples, SEQUENCE_LENGTH, n_weather_features)
  Output: Concatenated → Dense → single yield value

NOTE: Flatten time-series from monthly satellite/weather data.
If only seasonal features available (no monthly), reshape appropriately.
```

### 4.2 Model 4 — LSTM

```python
Architecture:
  Input(shape=(SEQUENCE_LENGTH, n_weather_features))
  → LSTM(64, return_sequences=True, name='lstm_1')
  → Dropout(0.2)
  → LSTM(32, return_sequences=False, name='lstm_2')
  → Dropout(0.2)
  → Dense(16, activation='relu')
  → Dense(1, activation='linear', name='yield_output')

Training:
  optimizer = Adam(learning_rate=0.001)
  loss = 'mse'
  metrics = ['mae']
  callbacks = [EarlyStopping(patience=20, restore_best_weights=True),
               ReduceLROnPlateau(factor=0.5, patience=10),
               ModelCheckpoint('outputs/models/lstm_best.h5')]
```

### 4.3 Model 5 — Bidirectional LSTM

```python
Architecture:
  Input(shape=(SEQUENCE_LENGTH, n_weather_features))
  → Bidirectional(LSTM(64, return_sequences=True))
  → Dropout(0.2)
  → Bidirectional(LSTM(32))
  → Dropout(0.2)
  → Dense(16, activation='relu')
  → Dense(1, activation='linear')

Same training config as LSTM above.
Save to: outputs/models/bilstm_best.h5
```

### 4.4 Model 6 — 1D CNN

```python
Architecture:
  Input(shape=(n_features, 1))
  → Conv1D(32, kernel_size=3, activation='relu', padding='same')
  → BatchNormalization()
  → MaxPooling1D(pool_size=2)
  → Conv1D(64, kernel_size=3, activation='relu', padding='same')
  → GlobalAveragePooling1D()
  → Dense(32, activation='relu')
  → Dropout(0.2)
  → Dense(1, activation='linear')

Input: Reshape tabular features to (n_features, 1) for 1D convolution.
Save to: outputs/models/cnn_best.h5
```

### 4.5 Model 7 — Hybrid CNN-LSTM (NOVEL ARCHITECTURE)

```
THIS IS ARKAM'S NOVEL CONTRIBUTION. Build carefully.

Architecture Design:
┌──────────────────────────────────────────────────────┐
│                  HYBRID CNN-LSTM                     │
│                                                      │
│  Satellite Branch (CNN)    Weather Branch (LSTM)     │
│  ┌─────────────────────┐  ┌───────────────────────┐ │
│  │ Input: (n_sat, 1)   │  │Input:(seq_len,n_wthr) │ │
│  │ Conv1D(32, k=3)     │  │ LSTM(64, ret_seq=T)   │ │
│  │ BatchNorm           │  │ Dropout(0.2)          │ │
│  │ Conv1D(64, k=3)     │  │ LSTM(32, ret_seq=F)   │ │
│  │ GlobalAvgPool1D     │  │ Dropout(0.2)          │ │
│  └──────────┬──────────┘  └──────────┬────────────┘ │
│             │                        │               │
│             └──────── Concatenate ───┘               │
│                            │                         │
│                      Dense(64, relu)                 │
│                      Dropout(0.3)                    │
│                      Dense(32, relu)                 │
│                      Dense(1, linear)  ← yield pred  │
└──────────────────────────────────────────────────────┘

Bimodal Season Handling (NOVELTY):
- Add 'season_indicator' (Yala=1, Maha=0) as explicit input
- Concatenate it with the merged CNN-LSTM output before final Dense
- This allows the model to learn season-specific patterns

Implementation:
  sat_input = Input(shape=(n_satellite_features, 1), name='satellite_input')
  weather_input = Input(shape=(SEQUENCE_LENGTH, n_weather_features), name='weather_input')
  season_input = Input(shape=(1,), name='season_input')

  cnn_branch = Conv1D(32, 3, activation='relu', padding='same')(sat_input)
  cnn_branch = BatchNormalization()(cnn_branch)
  cnn_branch = Conv1D(64, 3, activation='relu', padding='same')(cnn_branch)
  cnn_branch = GlobalAveragePooling1D()(cnn_branch)

  lstm_branch = LSTM(64, return_sequences=True)(weather_input)
  lstm_branch = Dropout(0.2)(lstm_branch)
  lstm_branch = LSTM(32)(lstm_branch)
  lstm_branch = Dropout(0.2)(lstm_branch)

  merged = Concatenate()([cnn_branch, lstm_branch, season_input])
  merged = Dense(64, activation='relu')(merged)
  merged = Dropout(0.3)(merged)
  merged = Dense(32, activation='relu')(merged)
  output = Dense(1, activation='linear', name='yield')(merged)

  model = Model(inputs=[sat_input, weather_input, season_input], outputs=output)

Save to: outputs/models/cnn_lstm_hybrid_best.h5
```

### 4.6 Required DL Outputs

```
For each DL model (LSTM, BiLSTM, CNN, CNN-LSTM):
│
├── Learning curve plot:
│   → Training loss vs Validation loss over epochs
│   → Mark early stopping point
│   → Save to outputs/plots/training/{model_name}_learning_curve.png
│
├── Actual vs Predicted scatter plot
│   → Same format as ML models
│
├── LOYO-CV results (same protocol as ML)
│
└── Model summary printout
    → Total trainable parameters
    → Architecture layers
```

---

## 🔬 STEP 5: ABLATION STUDY

Create `src/ablation.py`:

```
PURPOSE: Quantify how much each data source contributes to accuracy.
Use the BEST overall model for ablation (likely XGBoost or CNN-LSTM).

Run 6 experiments:

Experiment | Features Used                              | What It Tests
-----------|--------------------------------------------|--------------------------------
A          | WEATHER_FEATURES only                      | Weather-only baseline
B          | SATELLITE_FEATURES only                    | Satellite-only baseline
C          | HISTORICAL_FEATURES only                   | Historical yield only
D          | SOIL_FEATURES only                         | Soil-only baseline
E          | WEATHER + SATELLITE features               | Two-source combination
F          | ALL_FEATURES                               | Full multi-source model

For each experiment:
- Train best model with that feature subset
- Run LOYO-CV
- Record RMSE, MAE, R²

OUTPUT: outputs/results/ablation_results.csv
        outputs/plots/results/ablation_comparison.png
        → Bar chart showing R² improvement per feature set
        → Critical finding: "adding satellite to weather improves R² by X%"
```

---

## 📊 STEP 6: EVALUATION AND COMPARISON

Create `src/evaluator.py`:

### 6.1 Metrics Functions

```python
def compute_metrics(y_true, y_pred, model_name):
    """Compute all evaluation metrics."""
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import numpy as np

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return {'Model': model_name, 'RMSE': round(rmse, 4),
            'MAE': round(mae, 4), 'R2': round(r2, 4), 'MAPE': round(mape, 2)}
```

### 6.2 Statistical Significance Test

```python
def compare_models_statistically(errors_model1, errors_model2, name1, name2):
    """
    Wilcoxon signed-rank test to check if model difference is significant.
    Use when residuals are not normally distributed (common in agriculture).
    Also run paired t-test for comparison.
    """
    from scipy import stats
    wilcoxon_stat, wilcoxon_p = stats.wilcoxon(errors_model1, errors_model2)
    ttest_stat, ttest_p = stats.ttest_rel(errors_model1, errors_model2)
    print(f"\n{name1} vs {name2}:")
    print(f"  Wilcoxon p-value: {wilcoxon_p:.4f} {'(significant)' if wilcoxon_p < 0.05 else '(not significant)'}")
    print(f"  Paired t-test p-value: {ttest_p:.4f} {'(significant)' if ttest_p < 0.05 else '(not significant)'}")
    return wilcoxon_p, ttest_p
```

### 6.3 Final Comparison Table

```
Generate outputs/results/model_comparison.csv with:

Model       | RMSE  | MAE   | R²    | MAPE  | Train_Time | Parameters
------------|-------|-------|-------|-------|------------|----------
RandomForest| X.XXX | X.XXX | X.XXX | XX.X% | Xs         | -
XGBoost     | X.XXX | X.XXX | X.XXX | XX.X% | Xs         | -
SVR         | X.XXX | X.XXX | X.XXX | XX.X% | Xs         | -
LSTM        | X.XXX | X.XXX | X.XXX | XX.X% | Xs         | XX,XXX
BiLSTM      | X.XXX | X.XXX | X.XXX | XX.X% | Xs         | XX,XXX
CNN         | X.XXX | X.XXX | X.XXX | XX.X% | Xs         | XX,XXX
CNN-LSTM    | X.XXX | X.XXX | X.XXX | XX.X% | Xs         | XX,XXX

Also generate:
outputs/plots/results/model_comparison_bar.png
  → Grouped bar chart: RMSE and R² side by side for all 7 models
  → Target R² = 0.75 horizontal line
  → Color ML models blue, DL models orange, hybrid CNN-LSTM red
```

---

## 🔍 STEP 7: SHAP FEATURE IMPORTANCE

Create `src/explainer.py`:

```
Apply SHAP to the BEST performing model:

For tree-based models (RF, XGBoost):
  explainer = shap.TreeExplainer(best_model)
  shap_values = explainer.shap_values(X_test)

For DL models:
  explainer = shap.KernelExplainer(model.predict, X_background_sample)
  shap_values = explainer.shap_values(X_test)

Generate these SHAP plots:
├── outputs/plots/results/shap_summary.png
│   → Beeswarm plot: each feature's impact on predictions
│   → Color by feature value (high=red, low=blue)
│
├── outputs/plots/results/shap_importance.png
│   → Bar chart: mean |SHAP value| per feature
│   → Top 15 features ranked
│
└── outputs/plots/results/shap_dependence_{top_feature}.png
    → How top feature value relates to SHAP value
    → Reveals non-linear relationships

KEY FINDING TO REPORT:
Print top 5 most important features with their SHAP importance values.
Confirm whether NDVI/weather/historical yield are most important.
```

---

## 🌐 STEP 8: FLASK API FOR MODEL SERVING

Create `src/api.py`:

```python
"""
Flask REST API — Serves the best trained model for yield prediction.
Consumed by Shathurya's dashboard.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib, numpy as np, json

app = Flask(__name__)
CORS(app)

# Load best model on startup
best_model = joblib.load('outputs/models/xgb_best.pkl')
model_metrics = json.load(open('outputs/results/best_model_metrics.json'))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': 'BigOnion Yield Predictor'})

@app.route('/predict', methods=['POST'])
def predict():
    """
    Input JSON:
    {
      "district": "Matale",
      "season": "Yala",
      "year": 2024,
      "season_total_rainfall": 850,
      "season_avg_temp": 28.5,
      "season_mean_ndvi": 0.65,
      ... (all feature values)
    }
    Output JSON:
    {
      "district": "Matale",
      "season": "Yala",
      "predicted_yield_MT_per_Ha": 18.5,
      "confidence_lower": 15.2,
      "confidence_upper": 21.8,
      "model_r2": 0.78
    }
    """
    data = request.get_json()
    features = [data.get(f, 0) for f in ALL_FEATURES]
    prediction = float(best_model.predict([features])[0])
    # Simple confidence interval: ±15% based on model RMSE
    ci_margin = prediction * 0.15
    return jsonify({
        'district': data.get('district'),
        'season': data.get('season'),
        'predicted_yield_MT_per_Ha': round(prediction, 2),
        'confidence_lower': round(max(0, prediction - ci_margin), 2),
        'confidence_upper': round(prediction + ci_margin, 2),
        'model_r2': model_metrics.get('R2', 0)
    })

@app.route('/models/compare', methods=['GET'])
def compare_models():
    """Return all model comparison metrics."""
    import pandas as pd
    df = pd.read_csv('outputs/results/model_comparison.csv')
    return jsonify(df.to_dict(orient='records'))

@app.route('/feature-importance', methods=['GET'])
def feature_importance():
    """Return top 15 feature importance values."""
    import json
    fi = json.load(open('outputs/results/feature_importance.json'))
    return jsonify(fi)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## 🚀 STEP 9: MAIN PIPELINE RUNNER

Create `main.py`:

```python
"""
main.py — Run the complete ML/DL pipeline for big onion yield prediction.
Usage: python main.py [--skip-eda] [--skip-ml] [--skip-dl] [--skip-shap]
"""

import argparse, os, time
from src.data_loader import load_data
from src.preprocessor import preprocess
from src.feature_engineer import engineer_features
from src.eda import run_eda
from src.ml_models import train_all_ml_models
from src.dl_models import train_all_dl_models
from src.ablation import run_ablation_study
from src.evaluator import generate_final_comparison
from src.explainer import run_shap_analysis

def main(args):
    start = time.time()
    os.makedirs('outputs/models', exist_ok=True)
    os.makedirs('outputs/plots/eda', exist_ok=True)
    os.makedirs('outputs/plots/training', exist_ok=True)
    os.makedirs('outputs/plots/results', exist_ok=True)
    os.makedirs('outputs/results', exist_ok=True)

    print("\n" + "="*60)
    print("  AGRO AI — BIG ONION YIELD PREDICTION PIPELINE")
    print("  Arkam B.H.M. (214019K) | University of Moratuwa")
    print("="*60)

    # Step 1: Load data
    df = load_data()

    # Step 2: Preprocess
    df_clean = preprocess(df)

    # Step 3: Feature engineering
    X, y, feature_names = engineer_features(df_clean)

    # Step 4: EDA
    if not args.skip_eda:
        run_eda(df_clean, X, y)

    # Step 5: ML models
    if not args.skip_ml:
        ml_results = train_all_ml_models(X, y, feature_names)

    # Step 6: DL models
    if not args.skip_dl:
        dl_results = train_all_dl_models(X, y, df_clean)

    # Step 7: Ablation study
    run_ablation_study(df_clean)

    # Step 8: Final comparison
    generate_final_comparison()

    # Step 9: SHAP
    if not args.skip_shap:
        run_shap_analysis(X, feature_names)

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE in {elapsed/60:.1f} minutes")
    print(f"  Results saved to: outputs/")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-eda', action='store_true')
    parser.add_argument('--skip-ml', action='store_true')
    parser.add_argument('--skip-dl', action='store_true')
    parser.add_argument('--skip-shap', action='store_true')
    main(parser.parse_args())
```

---

## 📋 FINAL REQUIRED OUTPUTS CHECKLIST

When pipeline is complete, verify these exist:

```
outputs/
├── models/
│   ├── rf_best.pkl                   ✓ Random Forest best model
│   ├── xgb_best.pkl                  ✓ XGBoost best model
│   ├── svr_best.pkl                  ✓ SVR best model
│   ├── svr_scaler.pkl                ✓ StandardScaler for SVR
│   ├── lstm_best.h5                  ✓ LSTM best model
│   ├── bilstm_best.h5                ✓ BiLSTM best model
│   ├── cnn_best.h5                   ✓ CNN best model
│   └── cnn_lstm_hybrid_best.h5       ✓ Hybrid CNN-LSTM (NOVEL)
│
├── plots/
│   ├── eda/
│   │   ├── yield_distribution.png    ✓
│   │   ├── yield_timeseries.png      ✓
│   │   ├── correlation_heatmap.png   ✓
│   │   ├── seasonal_comparison.png   ✓
│   │   └── district_comparison.png   ✓
│   ├── training/
│   │   ├── lstm_learning_curve.png   ✓
│   │   ├── bilstm_learning_curve.png ✓
│   │   ├── cnn_learning_curve.png    ✓
│   │   └── cnn_lstm_learning_curve.png ✓
│   └── results/
│       ├── model_comparison_bar.png  ✓
│       ├── actual_vs_pred_rf.png     ✓
│       ├── actual_vs_pred_xgb.png    ✓
│       ├── actual_vs_pred_lstm.png   ✓
│       ├── actual_vs_pred_cnn_lstm.png ✓
│       ├── shap_summary.png          ✓
│       ├── shap_importance.png       ✓
│       └── ablation_comparison.png   ✓
│
└── results/
    ├── model_comparison.csv          ✓ All 7 models × 5 metrics
    ├── ablation_results.csv          ✓ 6 experiments × 3 metrics
    ├── feature_importance.json       ✓ Top 15 features + SHAP values
    ├── best_model_metrics.json       ✓ Best model name + all metrics
    └── final_summary.txt             ✓ Key findings paragraph
```

---

## 🎓 RESEARCH FINDINGS TO REPORT

After running, automatically generate `outputs/results/final_summary.txt` with:

```
1. Best performing model: [MODEL NAME] with R²=[X.XX], RMSE=[X.XX] MT/Ha
2. Does DL outperform ML? [YES/NO] — p-value=[X.XX] (Wilcoxon test)
3. Does CNN-LSTM hybrid beat standalone models? [YES/NO]
4. Top 3 most important features: [F1], [F2], [F3]
5. Ablation: Adding satellite to weather improves R² by [X]%
6. Yala predictions are [more/less] accurate than Maha (RMSE difference: [X])
7. Easiest district to predict: [DISTRICT] (R²=[X.XX])
8. Hardest district to predict: [DISTRICT] (R²=[X.XX])
9. Model reaches target R²>0.75: [YES/NO]
```

---

## ⚠️ IMPORTANT AGENT RULES

```
1. ALWAYS run with synthetic data first to test the pipeline end-to-end
   before waiting for real data files.

2. ALWAYS use random_state=42 for all models and splits.

3. NEVER use random train-test split for agricultural time-series data.
   ALWAYS use Leave-One-Year-Out or TimeSeriesSplit.

4. ALWAYS scale features before SVR and DL models using StandardScaler
   fitted ONLY on training data (prevent data leakage).

5. ALWAYS save every trained model immediately after training
   in case of crashes.

6. ALWAYS print progress messages:
   "Training Random Forest... (1/7 models)"
   "Fold 1/20: Year 2004 held out..."

7. For DL models, if training takes too long:
   Reduce MAX_EPOCHS to 50 for initial testing
   Use a subset of data for architecture validation

8. The CNN-LSTM hybrid is the NOVEL architecture.
   Spend extra time ensuring it trains correctly and report
   whether it improves over standalone CNN and LSTM.

9. Generate ALL required plots. These go directly into
   the interim and final reports.

10. When real data is loaded, validate it first:
    - Check district names match DISTRICTS list
    - Check year range matches YEAR_RANGE
    - Check no negative yield values
    - Report missing value percentages
```

---

## 🔧 QUICK START COMMANDS

```bash
# Install dependencies
pip install -r requirements.txt

# Run complete pipeline (uses synthetic data if real data missing)
python main.py

# Run without EDA (faster for model testing)
python main.py --skip-eda

# Run only ML models (skip DL for speed)
python main.py --skip-dl --skip-shap

# Start the prediction API
python src/api.py
# API available at http://localhost:5000

# Test API prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"district":"Matale","season":"Yala","season_total_rainfall":850}'
```

---

*Agro AI FYP 2026 | University of Moratuwa | Faculty of Information Technology*
*Arkam B.H.M. (214019K) — ML/DL Modeling Research Component*

"""Deep learning models: LSTM, BiLSTM, 1D-CNN, and the hybrid CNN-LSTM with season indicator.

LOYO-CV protocol with EarlyStopping + ReduceLROnPlateau. Per-fold best
weights are restored. Final refit on all data is then saved as the
deployable artefact (.keras format).
"""

import json
import os
import time
import warnings
import numpy as np
import pandas as pd

# Quiet TF logs.
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
warnings.filterwarnings('ignore')

import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, optimizers
from sklearn.preprocessing import StandardScaler

from config import (
    RANDOM_STATE, LSTM_UNITS, DROPOUT_RATE, DENSE_UNITS,
    LEARNING_RATE, BATCH_SIZE, MAX_EPOCHS, EARLY_STOPPING_PATIENCE,
    SYNTHETIC_MODE_DL_EPOCHS, SEQUENCE_LENGTH, N_WEATHER_PER_STEP,
)
from visualizer import actual_vs_predicted, learning_curve_plot

tf.random.set_seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)

from config import MODELS_DIR, RESULTS_DIR, PLOTS_DIR, TRAIN_PLOTS_DIR  # variant-aware


# ---------- Model builders ---------------------------------------------------

def build_lstm(n_weather: int) -> tf.keras.Model:
    inputs = layers.Input(shape=(SEQUENCE_LENGTH, n_weather), name='weather_seq')
    x = layers.LSTM(LSTM_UNITS[0], return_sequences=True)(inputs)
    x = layers.Dropout(DROPOUT_RATE)(x)
    x = layers.LSTM(LSTM_UNITS[1], return_sequences=False)(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    x = layers.Dense(DENSE_UNITS, activation='relu')(x)
    out = layers.Dense(1, activation='linear', name='yield_output')(x)
    model = models.Model(inputs, out, name='LSTM')
    model.compile(optimizer=optimizers.Adam(LEARNING_RATE), loss='mse', metrics=['mae'])
    return model


def build_bilstm(n_weather: int) -> tf.keras.Model:
    inputs = layers.Input(shape=(SEQUENCE_LENGTH, n_weather), name='weather_seq')
    x = layers.Bidirectional(layers.LSTM(LSTM_UNITS[0], return_sequences=True))(inputs)
    x = layers.Dropout(DROPOUT_RATE)(x)
    x = layers.Bidirectional(layers.LSTM(LSTM_UNITS[1]))(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    x = layers.Dense(DENSE_UNITS, activation='relu')(x)
    out = layers.Dense(1, activation='linear')(x)
    model = models.Model(inputs, out, name='BiLSTM')
    model.compile(optimizer=optimizers.Adam(LEARNING_RATE), loss='mse', metrics=['mae'])
    return model


def build_cnn(n_features: int) -> tf.keras.Model:
    inputs = layers.Input(shape=(n_features, 1), name='tabular_1d')
    x = layers.Conv1D(32, 3, activation='relu', padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=2)(x)
    x = layers.Conv1D(64, 3, activation='relu', padding='same')(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(32, activation='relu')(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    out = layers.Dense(1, activation='linear')(x)
    model = models.Model(inputs, out, name='CNN')
    model.compile(optimizer=optimizers.Adam(LEARNING_RATE), loss='mse', metrics=['mae'])
    return model


def build_cnn_lstm_hybrid(n_satellite: int, n_weather: int) -> tf.keras.Model:
    """Novel architecture: CNN(satellite) + LSTM(weather) + season indicator."""
    sat_input = layers.Input(shape=(n_satellite, 1), name='satellite_input')
    weather_input = layers.Input(shape=(SEQUENCE_LENGTH, n_weather), name='weather_input')
    season_input = layers.Input(shape=(1,), name='season_input')

    cnn = layers.Conv1D(32, 3, activation='relu', padding='same')(sat_input)
    cnn = layers.BatchNormalization()(cnn)
    cnn = layers.Conv1D(64, 3, activation='relu', padding='same')(cnn)
    cnn = layers.GlobalAveragePooling1D()(cnn)

    lstm = layers.LSTM(LSTM_UNITS[0], return_sequences=True)(weather_input)
    lstm = layers.Dropout(DROPOUT_RATE)(lstm)
    lstm = layers.LSTM(LSTM_UNITS[1])(lstm)
    lstm = layers.Dropout(DROPOUT_RATE)(lstm)

    merged = layers.Concatenate()([cnn, lstm, season_input])
    merged = layers.Dense(64, activation='relu')(merged)
    merged = layers.Dropout(0.3)(merged)
    merged = layers.Dense(32, activation='relu')(merged)
    out = layers.Dense(1, activation='linear', name='yield')(merged)

    model = models.Model([sat_input, weather_input, season_input], out, name='CNN_LSTM_Hybrid')
    model.compile(optimizer=optimizers.Adam(LEARNING_RATE), loss='mse', metrics=['mae'])
    return model


# ---------- Training utilities -----------------------------------------------

def _scale_seq(seq_train, seq_test):
    """Scale a (N, T, F) tensor using stats from the train split."""
    n_train, T, F = seq_train.shape
    flat = seq_train.reshape(-1, F)
    scaler = StandardScaler().fit(flat)
    return (scaler.transform(flat).reshape(n_train, T, F).astype(np.float32),
            scaler.transform(seq_test.reshape(-1, F)).reshape(seq_test.shape[0], T, F).astype(np.float32),
            scaler)


def _scale_2d(arr_train, arr_test):
    scaler = StandardScaler().fit(arr_train)
    return (scaler.transform(arr_train).astype(np.float32),
            scaler.transform(arr_test).astype(np.float32),
            scaler)


def _early_stop_callbacks(checkpoint_path: str | None = None):
    cbs = [
        callbacks.EarlyStopping(
            patience=EARLY_STOPPING_PATIENCE, restore_best_weights=True, monitor='val_loss',
        ),
        callbacks.ReduceLROnPlateau(factor=0.5, patience=10, monitor='val_loss', min_lr=1e-5),
    ]
    if checkpoint_path:
        cbs.append(callbacks.ModelCheckpoint(checkpoint_path, save_best_only=True, monitor='val_loss'))
    return cbs


def _save_oof(model_name: str, oof: np.ndarray, y: np.ndarray, df: pd.DataFrame,
              metrics: dict) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    payload = {
        'model_name': model_name,
        'metrics': metrics,
        'rows': [
            {'Year': int(df['Year'].iloc[i]), 'Season': str(df['Season'].iloc[i]),
             'District': str(df['District'].iloc[i]),
             'actual': float(y[i]), 'predicted': float(oof[i])}
            for i in range(len(y))
        ],
    }
    with open(os.path.join(RESULTS_DIR, f'oof_{model_name.lower()}.json'), 'w') as f:
        json.dump(payload, f, indent=2)


def _metrics(y_true, y_pred, name: str, train_time: float, n_params: int) -> dict:
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
    return {
        'Model': name, 'RMSE': round(rmse, 4), 'MAE': round(mae, 4),
        'R2': round(r2, 4), 'MAPE': round(mape, 2),
        'Train_Time_s': round(train_time, 2),
        'Best_Params': {'epochs_per_fold': SYNTHETIC_MODE_DL_EPOCHS,
                        'batch_size': BATCH_SIZE, 'lr': LEARNING_RATE},
        'Parameters': int(n_params),
    }


def _train_loyo_seq(model_factory, weather_seq, y, years, name: str,
                     epochs: int, df: pd.DataFrame) -> tuple:
    unique_years = np.array(sorted(set(years)))
    oof = np.full(len(y), np.nan, dtype=np.float32)
    last_history = None

    for i, held in enumerate(unique_years, 1):
        train_mask = years != held
        test_mask = years == held
        seq_tr, seq_te, _ = _scale_seq(weather_seq[train_mask], weather_seq[test_mask])
        y_tr = y[train_mask]
        model = model_factory()
        history = model.fit(
            seq_tr, y_tr,
            validation_split=0.15, epochs=epochs, batch_size=BATCH_SIZE,
            callbacks=_early_stop_callbacks(), verbose=0, shuffle=True,
        )
        oof[test_mask] = model.predict(seq_te, verbose=0).flatten()
        last_history = history.history
        if i % 5 == 0 or i == len(unique_years):
            print(f'  Fold {i}/{len(unique_years)}: held year {held}')
        tf.keras.backend.clear_session()

    return oof, last_history


def _train_loyo_cnn(model_factory, X, y, years, name: str,
                     epochs: int, df: pd.DataFrame) -> tuple:
    unique_years = np.array(sorted(set(years)))
    oof = np.full(len(y), np.nan, dtype=np.float32)
    last_history = None

    for i, held in enumerate(unique_years, 1):
        train_mask = years != held
        test_mask = years == held
        X_tr_2d, X_te_2d, _ = _scale_2d(X[train_mask], X[test_mask])
        X_tr = X_tr_2d[:, :, None]
        X_te = X_te_2d[:, :, None]
        y_tr = y[train_mask]
        model = model_factory()
        history = model.fit(
            X_tr, y_tr,
            validation_split=0.15, epochs=epochs, batch_size=BATCH_SIZE,
            callbacks=_early_stop_callbacks(), verbose=0, shuffle=True,
        )
        oof[test_mask] = model.predict(X_te, verbose=0).flatten()
        last_history = history.history
        if i % 5 == 0 or i == len(unique_years):
            print(f'  Fold {i}/{len(unique_years)}: held year {held}')
        tf.keras.backend.clear_session()

    return oof, last_history


def _train_loyo_hybrid(model_factory, satellite, weather_seq, season, y, years,
                        epochs: int) -> tuple:
    unique_years = np.array(sorted(set(years)))
    oof = np.full(len(y), np.nan, dtype=np.float32)
    last_history = None

    for i, held in enumerate(unique_years, 1):
        train_mask = years != held
        test_mask = years == held
        sat_tr_2d, sat_te_2d, _ = _scale_2d(satellite[train_mask, :, 0], satellite[test_mask, :, 0])
        sat_tr = sat_tr_2d[:, :, None]
        sat_te = sat_te_2d[:, :, None]
        seq_tr, seq_te, _ = _scale_seq(weather_seq[train_mask], weather_seq[test_mask])
        season_tr = season[train_mask]
        season_te = season[test_mask]
        y_tr = y[train_mask]
        model = model_factory()
        history = model.fit(
            [sat_tr, seq_tr, season_tr], y_tr,
            validation_split=0.15, epochs=epochs, batch_size=BATCH_SIZE,
            callbacks=_early_stop_callbacks(), verbose=0, shuffle=True,
        )
        oof[test_mask] = model.predict([sat_te, seq_te, season_te], verbose=0).flatten()
        last_history = history.history
        if i % 5 == 0 or i == len(unique_years):
            print(f'  Fold {i}/{len(unique_years)}: held year {held}')
        tf.keras.backend.clear_session()

    return oof, last_history


# ---------- Driver -----------------------------------------------------------

def train_all_dl_models(seq_payload: dict, df: pd.DataFrame) -> list:
    print('\n' + '=' * 60)
    print('STEP 6: DEEP LEARNING MODELS')
    print('=' * 60)

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(TRAIN_PLOTS_DIR, exist_ok=True)

    epochs = SYNTHETIC_MODE_DL_EPOCHS
    print(f'  Using {epochs} epochs/fold (synthetic-mode cap; raise for real data).')

    weather_seq = seq_payload['weather_seq']
    satellite = seq_payload['satellite']
    season = seq_payload['season']
    y = seq_payload['y']
    years = seq_payload['years']
    districts = seq_payload['districts']
    n_weather = weather_seq.shape[2]
    n_sat = satellite.shape[1]

    metrics_all = []

    # ---- LSTM ----
    print('\n--- LSTM (1/4) ---')
    t0 = time.time()
    oof, hist = _train_loyo_seq(lambda: build_lstm(n_weather), weather_seq, y, years, 'LSTM', epochs, df)
    final = build_lstm(n_weather)
    seq_scaler = StandardScaler().fit(weather_seq.reshape(-1, n_weather))
    seq_full = seq_scaler.transform(weather_seq.reshape(-1, n_weather)).reshape(weather_seq.shape).astype(np.float32)
    final.fit(seq_full, y, epochs=epochs, batch_size=BATCH_SIZE,
              callbacks=_early_stop_callbacks(), validation_split=0.15, verbose=0)
    final.save(os.path.join(MODELS_DIR, 'lstm_best.keras'))
    elapsed = time.time() - t0
    m = _metrics(y, oof, 'LSTM', elapsed, final.count_params())
    _save_oof('LSTM', oof, y, df, m)
    print(f'  RMSE={m["RMSE"]} MAE={m["MAE"]} R²={m["R2"]} MAPE={m["MAPE"]}% '
          f'params={m["Parameters"]:,} ({elapsed:.1f}s)')
    actual_vs_predicted(y, oof, 'LSTM', os.path.join(PLOTS_DIR, 'actual_vs_pred_lstm.png'),
                         districts=districts)
    learning_curve_plot(hist, 'LSTM', os.path.join(TRAIN_PLOTS_DIR, 'lstm_learning_curve.png'))
    metrics_all.append(m)

    # ---- BiLSTM ----
    print('\n--- BiLSTM (2/4) ---')
    t0 = time.time()
    oof, hist = _train_loyo_seq(lambda: build_bilstm(n_weather), weather_seq, y, years, 'BiLSTM', epochs, df)
    final = build_bilstm(n_weather)
    final.fit(seq_full, y, epochs=epochs, batch_size=BATCH_SIZE,
              callbacks=_early_stop_callbacks(), validation_split=0.15, verbose=0)
    final.save(os.path.join(MODELS_DIR, 'bilstm_best.keras'))
    elapsed = time.time() - t0
    m = _metrics(y, oof, 'BiLSTM', elapsed, final.count_params())
    _save_oof('BiLSTM', oof, y, df, m)
    print(f'  RMSE={m["RMSE"]} MAE={m["MAE"]} R²={m["R2"]} MAPE={m["MAPE"]}% '
          f'params={m["Parameters"]:,} ({elapsed:.1f}s)')
    actual_vs_predicted(y, oof, 'BiLSTM', os.path.join(PLOTS_DIR, 'actual_vs_pred_bilstm.png'),
                         districts=districts)
    learning_curve_plot(hist, 'BiLSTM', os.path.join(TRAIN_PLOTS_DIR, 'bilstm_learning_curve.png'))
    metrics_all.append(m)

    # ---- 1D CNN on tabular features ----
    print('\n--- CNN (3/4) ---')
    t0 = time.time()
    # Use the satellite 1D tensor (already (N, F, 1)). Use plain 2D underlying for scaling.
    X_cnn = satellite[:, :, 0]
    oof, hist = _train_loyo_cnn(lambda: build_cnn(X_cnn.shape[1]), X_cnn, y, years, 'CNN', epochs, df)
    final = build_cnn(X_cnn.shape[1])
    sc = StandardScaler().fit(X_cnn)
    X_full = sc.transform(X_cnn)[:, :, None].astype(np.float32)
    final.fit(X_full, y, epochs=epochs, batch_size=BATCH_SIZE,
              callbacks=_early_stop_callbacks(), validation_split=0.15, verbose=0)
    final.save(os.path.join(MODELS_DIR, 'cnn_best.keras'))
    elapsed = time.time() - t0
    m = _metrics(y, oof, 'CNN', elapsed, final.count_params())
    _save_oof('CNN', oof, y, df, m)
    print(f'  RMSE={m["RMSE"]} MAE={m["MAE"]} R²={m["R2"]} MAPE={m["MAPE"]}% '
          f'params={m["Parameters"]:,} ({elapsed:.1f}s)')
    actual_vs_predicted(y, oof, 'CNN', os.path.join(PLOTS_DIR, 'actual_vs_pred_cnn.png'),
                         districts=districts)
    learning_curve_plot(hist, 'CNN', os.path.join(TRAIN_PLOTS_DIR, 'cnn_learning_curve.png'))
    metrics_all.append(m)

    # ---- Hybrid CNN-LSTM (NOVEL) ----
    print('\n--- Hybrid CNN-LSTM (4/4) — NOVEL ---')
    t0 = time.time()
    oof, hist = _train_loyo_hybrid(
        lambda: build_cnn_lstm_hybrid(n_sat, n_weather),
        satellite, weather_seq, season, y, years, epochs,
    )
    final = build_cnn_lstm_hybrid(n_sat, n_weather)
    sat_sc = StandardScaler().fit(satellite[:, :, 0])
    sat_full = sat_sc.transform(satellite[:, :, 0])[:, :, None].astype(np.float32)
    final.fit([sat_full, seq_full, season], y,
              epochs=epochs, batch_size=BATCH_SIZE,
              callbacks=_early_stop_callbacks(), validation_split=0.15, verbose=0)
    final.save(os.path.join(MODELS_DIR, 'cnn_lstm_hybrid_best.keras'))
    elapsed = time.time() - t0
    m = _metrics(y, oof, 'CNN_LSTM_Hybrid', elapsed, final.count_params())
    _save_oof('CNN_LSTM_Hybrid', oof, y, df, m)
    print(f'  RMSE={m["RMSE"]} MAE={m["MAE"]} R²={m["R2"]} MAPE={m["MAPE"]}% '
          f'params={m["Parameters"]:,} ({elapsed:.1f}s)')
    actual_vs_predicted(y, oof, 'Hybrid CNN-LSTM',
                         os.path.join(PLOTS_DIR, 'actual_vs_pred_cnn_lstm.png'),
                         districts=districts)
    learning_curve_plot(hist, 'Hybrid CNN-LSTM',
                         os.path.join(TRAIN_PLOTS_DIR, 'cnn_lstm_learning_curve.png'))
    metrics_all.append(m)

    return metrics_all

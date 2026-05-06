# 04 — All 7 Models, Explained Simply

This project compares **3 ML models** + **4 DL models**. Below is each one in plain English with: what it is, how it works, why we chose it, and what its strengths and weaknesses are for our problem.

---

## 1. Random Forest (ML)

### What it is
A "forest" of many **decision trees**, each trained on a random subset of the data and a random subset of the features. Predictions are the average of all trees.

### How a single decision tree works
A decision tree is a series of yes/no questions. Like a flowchart:

```
Is season_mean_ndvi > 0.6?
├── YES → Is season_total_rainfall > 800?
│         ├── YES → predict 17.5 MT/Ha
│         └── NO  → predict 14.2 MT/Ha
└── NO  → Is season_indicator = 1?
          ├── YES → predict 11.8 MT/Ha
          └── NO  → predict 6.5 MT/Ha
```

The training algorithm picks the splits automatically, choosing whichever question reduces prediction error the most at each step.

### Why the "forest"?
A single tree memorises easily (high variance, overfits). 200 trees, each trained on slightly different data, average out their individual mistakes. This is **bagging** (bootstrap aggregating). Random Forest's defining feature is also picking a random subset of features at each split, which decorrelates the trees further.

### Strengths for this project
- **Works on small data.** Doesn't need millions of examples.
- **Robust to feature scales.** Doesn't care if rainfall is in mm and NDVI is in 0–1.
- **Interpretable.** You can extract feature importance directly.
- **Fast to train.** Seconds per fold.

### Weaknesses
- Can't extrapolate (predicts within the range of training data).
- Doesn't naturally handle time-series structure.

### In code
[src/ml_models.py:84-103](../src/ml_models.py#L84-L103). Hyperparameters tuned: `n_estimators` (number of trees), `max_depth` (tree depth), `min_samples_leaf` (regularisation).

### Result on synthetic data
**R² = 0.842** — winner of the leaderboard.

---

## 2. XGBoost (ML)

### What it is
**eXtreme Gradient Boosting.** Also a forest of trees, but built sequentially: each tree is trained to fix the mistakes of the previous one. This is **boosting**, the opposite philosophy of bagging.

### How it works
Round 1: Train a small tree, compute residuals (actual − predicted) for every row.
Round 2: Train a new small tree to predict those residuals.
Round 3: Train another tree on the new residuals.
...
Final prediction: sum of all trees' predictions, scaled by a learning rate.

Each tree only needs to be "slightly better than random" because hundreds of them stacked together produce a strong model.

### Why XGBoost specifically
"Gradient boosting" is the general technique. XGBoost is one of the most successful implementations — won countless Kaggle competitions, dominates tabular ML benchmarks. Key features:
- Built-in regularisation (`reg_alpha` for L1, `reg_lambda` for L2).
- Handles missing values automatically.
- Very fast (C++ under the hood, multi-threaded).

### Strengths for this project
- Often the **single strongest model** on tabular data.
- Comparable interpretability to RF (feature importance via "gain").
- Fast enough for LOYO with 20 folds.

### Weaknesses
- More hyperparameters than RF → easier to mis-tune.
- Slightly more prone to overfit on tiny datasets without careful tuning.

### In code
[src/ml_models.py:106-129](../src/ml_models.py#L106-L129). Tuned: `learning_rate`, `max_depth`, `n_estimators`, `subsample`.

### Result on synthetic data
**R² = 0.827** — second place.

---

## 3. Support Vector Regression / SVR (ML)

### What it is
A regression version of the **Support Vector Machine**. Tries to fit a function such that most predictions are within a tolerance band (`epsilon`) of the actual values, using only a subset of the training data (the "support vectors") to define the function.

### How it works
- Imagine your data plotted in N-dimensional feature space.
- SVR finds a hyperplane (in linear case) or a curved surface (with a kernel) that passes through as many points as possible within an `epsilon`-wide tube.
- Uses a **kernel** to handle non-linearity. We try `rbf` (Gaussian — most common), `linear`, and `poly`.

### Strengths
- Can capture non-linear relationships through kernels.
- Theoretically grounded.
- Effective when features are well-scaled.

### Weaknesses
- **Slow** with many features (kernel computation is `O(n²)`).
- **Requires careful feature scaling** — we explicitly fit a `StandardScaler` per fold.
- Less interpretable than tree models.

### In code
[src/ml_models.py:132-160](../src/ml_models.py#L132-L160). Tuned: `kernel`, `C` (regularisation strength), `gamma` (kernel width), `epsilon` (tolerance).

### Result on synthetic data
**R² = 0.696** — third place. Notably worse than tree models, which is typical on tabular data.

---

## 4. LSTM (DL)

### What it is
**Long Short-Term Memory** — a type of Recurrent Neural Network (RNN) designed to handle sequences while remembering important context from far back in time.

### How a regular RNN works
An RNN walks through a sequence step by step. At each step:
- Take the current input + the previous hidden state.
- Produce a new hidden state and (optionally) an output.
- Pass the new hidden state to the next step.

This is great in theory but in practice "vanilla" RNNs forget context after a few steps (the **vanishing gradient problem**).

### What LSTM adds
LSTM cells have **gates** that decide what to remember and what to forget:
- **Forget gate**: which parts of the previous memory to discard?
- **Input gate**: which parts of the current input to add to memory?
- **Output gate**: which parts of memory to expose as output?

These gates are little neural networks themselves, learned during training. The result: LSTMs can remember information across hundreds of timesteps.

### Architecture used here

```
Input: (batch, 5 timesteps, 4 weather variables)
   ↓
LSTM(64 units, return_sequences=True)    ← processes all 5 steps, outputs 5 vectors
   ↓
Dropout(0.2)                              ← regularisation
   ↓
LSTM(32 units, return_sequences=False)   ← processes the 5 vectors, outputs 1 vector
   ↓
Dropout(0.2)
   ↓
Dense(16 units, ReLU activation)         ← fully-connected layer
   ↓
Dense(1 unit, linear activation)         ← single yield value
```

### Strengths
- Naturally handles time-series.
- Can learn complex temporal patterns.

### Weaknesses
- **Needs lots of data** to shine. With 152 training rows, it underperforms.
- Slower than tree models.
- Less interpretable.

### In code
`build_lstm()` in [src/dl_models.py:33-44](../src/dl_models.py#L33-L44).

### Result on synthetic data
**R² = 0.021** — basically no better than predicting the mean. **Expected** — 152 rows is too few. With real monthly NASA POWER data over more years, this should improve.

---

## 5. BiLSTM (DL)

### What it is
**Bidirectional LSTM** — runs two LSTMs simultaneously: one reading the sequence forward (month 1 → 5), one backward (month 5 → 1). Their outputs are concatenated.

### Why bidirectional?
The forward LSTM at step 3 only knows about months 1–3. The backward LSTM at step 3 knows about months 3–5. Together, the model has full bi-directional context at every step.

### When it helps
For yield prediction, "what happens later in the season" actually informs "what happened earlier" — e.g. peak NDVI position tells you about early-season growth. So bidirectional context can help.

### Architecture used here

```
Input: (batch, 5, 4)
   ↓
Bidirectional(LSTM(64))    ← 64 forward + 64 backward = 128 output
   ↓
Dropout(0.2)
   ↓
Bidirectional(LSTM(32))    ← 32 + 32 = 64 output
   ↓
Dropout(0.2)
   ↓
Dense(16, ReLU)
   ↓
Dense(1, linear)
```

### Strengths
- Often better than vanilla LSTM on classification/sequence labelling.
- Can leverage future context (when allowed).

### Weaknesses
- 2× the parameters → more overfitting risk on small data.
- Doesn't make sense for *online forecasting* (you can't see future months when predicting yield mid-season).

### Result on synthetic data
**R² = 0.039** — slightly better than LSTM but still poor. Same data-scarcity issue.

---

## 6. 1D CNN (DL)

### What it is
**1D Convolutional Neural Network** — usually used for images (2D CNN) or signals/time-series (1D CNN). Here we apply it to the 11 satellite features treated as a 1D "image".

### How a 1D convolution works
Imagine a small filter — a 3-element window — that slides across your input vector. At each position, it computes a weighted sum of the 3 elements under it. Repeat with multiple different filters; each filter learns to detect a different pattern.

```
Input:    [ndvi_mean, ndvi_max, ndvi_min, evi_mean, ndwi, lst_day, lst_night, ...]
              │           │          │
              └─ filter 1 ──┘          ← detects "high NDVI cluster"
                       └─ filter 2 ──┘ ← detects "NDVI dropping into LST"
... etc, 32 filters in our network
```

### Architecture used here

```
Input: (batch, 11 satellite features, 1)
   ↓
Conv1D(32 filters, kernel=3, ReLU)   ← 32 different patterns detected
   ↓
BatchNormalization                    ← stabilises training
   ↓
MaxPooling1D(pool_size=2)             ← downsample by half
   ↓
Conv1D(64 filters, kernel=3, ReLU)    ← 64 higher-level patterns
   ↓
GlobalAveragePooling1D                ← collapse to a single vector
   ↓
Dense(32, ReLU)
   ↓
Dropout(0.2)
   ↓
Dense(1, linear)
```

### Why batch normalisation?
Each layer's input distribution can shift during training (the "internal covariate shift" problem). BatchNorm re-normalises the inputs to each layer to mean 0, std 1, accelerating training.

### Strengths
- Can detect local patterns / interactions between adjacent features.
- Translation-invariant (a pattern detected at position 1 is detected at position 5 too).

### Weaknesses
- For tabular data, the "spatial" assumption (adjacent features are related) is shaky — feature order is arbitrary.
- Still needs a fair bit of data.

### Result on synthetic data
**R² = 0.271** — best of the DL models, beating LSTM/BiLSTM. CNN's ability to find combinations of satellite features works even on small data.

---

## 7. Hybrid CNN-LSTM (the NOVEL architecture) ⭐

### What it is
**The novel architecture** that combines:
- A **CNN branch** processing satellite features (spatial information about vegetation).
- An **LSTM branch** processing weather time-series (temporal information).
- A **season indicator** (Yala=1, Maha=0) injected directly before the final prediction.

### Why combine all three?
Each modality captures different information:
- **Satellite** = where/how green the crop is right now.
- **Weather** = how conditions evolved over the season.
- **Season indicator** = which monsoon we're in (massive yield baseline shift).

A standard model would just concatenate everything and feed it through dense layers. That works, but the architecture below preserves each modality's *structure* before merging — which is the key idea.

### Architecture

```
                      ┌────────────────┐         ┌────────────────┐         ┌──────────┐
                      │  Satellite     │         │  Weather       │         │ Season   │
                      │  (11, 1)       │         │  (5, 4)        │         │ (1)      │
                      └────────┬───────┘         └────────┬───────┘         └────┬─────┘
                               │                          │                       │
                       Conv1D(32, k=3)             LSTM(64, ret_seq=T)            │
                               │                          │                       │
                       BatchNorm                       Dropout(0.2)               │
                               │                          │                       │
                       Conv1D(64, k=3)               LSTM(32)                     │
                               │                          │                       │
                       GlobalAvgPool1D                 Dropout(0.2)               │
                               │                          │                       │
                               └─────────┬───────┬────────┘                       │
                                         │       │                                │
                                         ▼       ▼                                │
                                       ┌──────────────────────────────────────────┘
                                       ▼
                                  Concatenate (cnn_out + lstm_out + season)
                                       │
                                  Dense(64, ReLU)
                                       │
                                  Dropout(0.3)
                                       │
                                  Dense(32, ReLU)
                                       │
                                  Dense(1, linear)
                                       │
                                       ▼
                                Predicted yield (MT/Ha)
```

### What makes this novel

Most yield-prediction papers either:
- Stack everything into a single feature vector → loses structure.
- Use two-modality fusion (e.g. RGB image + tabular) → no season handling.
- Build separate models per season → can't share learning across seasons.

This design **fuses three modalities** while explicitly preserving:
1. **Spatial structure** of satellite features (CNN).
2. **Temporal structure** of weather data (LSTM).
3. **Categorical context** of which monsoon we're in (concatenated indicator).

The season indicator goes in **after** the heavy feature extraction. That way:
- The CNN/LSTM branches learn season-agnostic feature extractors (more efficient use of data).
- The final dense layers learn season-specific yield baselines.
- Effectively a "soft" multi-task model in one architecture.

### In code
`build_cnn_lstm_hybrid()` in [src/dl_models.py:73-97](../src/dl_models.py#L73-L97).

### Result on synthetic data
**R² = 0.097** — better than LSTM/BiLSTM but worse than CNN alone. With 152 rows, the extra parameters in the hybrid (~45,000) overfit. With real data and more years, the architecture's advantages should emerge.

---

## Side-by-side comparison

| Model | Type | Parameters | Synthetic R² | Train time/fold | Best for |
|---|---|---|---|---|---|
| **Random Forest** | ML (bagging trees) | ~200 trees | **0.842** | ~0.3s | Small tabular data |
| XGBoost | ML (boosting trees) | ~300 trees | 0.827 | ~0.2s | Tabular, often strongest |
| SVR | ML (kernel) | n/a | 0.696 | <0.1s | Smooth non-linearities |
| LSTM | DL (recurrent) | 30,625 | 0.021 | ~3s | Long sequences with lots of data |
| BiLSTM | DL (recurrent) | 77,601 | 0.039 | ~4s | Same as LSTM, with future context |
| CNN | DL (convolutional) | 8,577 | 0.271 | ~3s | Local feature interactions |
| **Hybrid CNN-LSTM** | DL (multi-modal) ⭐ | 44,929 | 0.097 | ~5s | Multi-modal data with seasonality |

## Why all 7?

Because the **research question** is "ML vs DL with scarce data — and does the novel hybrid architecture beat its components?". You can only answer that question by comparing all of them on the same evaluation protocol (LOYO-CV) with the same data. Each model is a data point in the comparison — even the ones that lose are part of the result.

The synthetic-data finding "RF beats DL with 152 rows" is **itself a research finding**: it tells the field that vegetable-yield prediction in data-scarce contexts is currently better served by classical ML. With real data (more years, real monthly weather sequences), the verdict may flip — that's exactly what your supervisor will want you to investigate.

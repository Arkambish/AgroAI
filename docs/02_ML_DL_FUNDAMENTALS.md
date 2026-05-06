# 02 — Machine Learning and Deep Learning Fundamentals

This is a from-zero crash course on the concepts you'll see in the code and the report. Every term used in this project is explained here.

## What is "machine learning"?

Suppose I give you a table:

| rainfall | ndvi | yield |
|---|---|---|
| 800   | 0.65 | 17 |
| 600   | 0.45 | 11 |
| 950   | 0.72 | 19 |
| 700   | 0.55 | 14 |

Looking at this, you'd guess: more rainfall and higher NDVI → higher yield. If I gave you a new row with `rainfall=850, ndvi=0.68`, you'd probably say "around 18". You just did machine learning by eye.

Machine learning is the same thing, automated. A **model** is a mathematical function `f(rainfall, ndvi, ...) → yield`. **Training** is the process of finding the function that fits the historical data best. **Prediction** is using the trained function on new data.

Two big categories:

- **Classification**: predict a category (will it rain tomorrow? yes/no)
- **Regression**: predict a number (how much will it rain tomorrow? 12.4 mm)

This project is **regression** — we predict a continuous number (yield in MT/Ha).

## What is "deep learning"?

Deep learning is one *type* of machine learning that uses **neural networks** — stacks of mathematical layers, each layer transforming numbers into other numbers. The name "deep" comes from having many layers stacked. Deep learning is good at finding complex patterns in raw data (images, text, audio) but needs *lots* of data to work well.

For this project, we use both:
- **Classical ML** (Random Forest, XGBoost, SVR) — work well on small tabular datasets like ours.
- **Deep Learning** (LSTM, CNN, hybrid) — included so we can answer the research question *"is DL better than ML for this problem?"*

## Features and labels

- **Features** (also called "inputs", "predictors", "X"): the columns the model uses to predict — rainfall, NDVI, soil pH, etc.
- **Label** (also called "target", "y"): the column the model predicts — yield in MT/Ha.

In this project: 31 feature columns, 1 label column.

## Training, validation, and test data

When you build a model, you need to know if it's any good. You can't just check that it predicts the data it was trained on — that's like a student writing answers after reading the answer key. We split data into:

- **Training set**: the model learns from this.
- **Validation set**: used during training to tune choices (early stopping, hyperparameters).
- **Test set**: the model never sees this until the very end. Its score on the test set tells you how it would perform on truly new data.

For yield prediction, we **can't split randomly** — that would let the model "see the future". A model trained on 2020 data and tested on 2010 data is cheating, because in 2010 you wouldn't have known 2020. So we use **temporal splits** — see "Leave-One-Year-Out" below.

## Leave-One-Year-Out Cross-Validation (LOYO-CV) — the most important concept here

This is how we honestly score every model. Pseudocode:

```
For each year Y from 2004 to 2023:
    Hide all rows where Year == Y          (the test set)
    Train the model on every other year    (the training set)
    Predict yield for the hidden year      (out-of-fold predictions)
    Save those predictions

Combine all the saved predictions and compute final RMSE / R².
```

Why this is honest: when we predict 2015, the model has only seen 2004–2014 + 2016–2023, so the prediction is what it would have given **before** 2015 happened. We do this for every year, then concatenate all those held-out predictions to compute one set of metrics.

**This is the gold standard for evaluating time-series models with limited data.** It's slow (we train each model 20 times), but with only 152 rows, we can't afford to throw away a chunk for testing — LOYO uses every row as a test point exactly once.

## Evaluation metrics — what the numbers mean

After training, we compute four numbers for every model:

| Metric | Formula | What it means | Better when... |
|---|---|---|---|
| **RMSE** (Root Mean Squared Error) | √(mean((actual − predicted)²)) | Average prediction error in MT/Ha. Penalises big mistakes more. | Smaller |
| **MAE** (Mean Absolute Error) | mean(|actual − predicted|) | Average error in MT/Ha, plain and simple. | Smaller |
| **R²** (R-squared) | 1 − (sum of squared errors / total variance) | Fraction of yield variance the model explains. 1.0 = perfect, 0 = no better than predicting the mean, negative = worse than the mean. | Larger (max 1.0) |
| **MAPE** (Mean Absolute Percentage Error) | mean(|actual − predicted| / actual) × 100 | Average error as a percentage. Easier to communicate. | Smaller |

For this project, **R² > 0.75 is the success target** (per the proposal). Synthetic-data Random Forest hit R² = 0.84 — that's good. DL models hit R² ≈ 0.0–0.27 because they need more data.

## Overfitting — the main thing to avoid

**Overfitting** is when a model memorises the training data instead of learning general patterns. It scores great on training but terrible on new data. With 152 rows, overfitting is a constant threat.

How we fight it:

1. **LOYO-CV** — gives an honest score on data the model has never seen.
2. **Regularisation** — penalties built into the model's loss function that discourage memorisation. Examples in this project:
   - Random Forest: `max_depth` and `min_samples_leaf` limits stop trees from growing arbitrarily complex.
   - XGBoost: `reg_alpha` (L1) and `reg_lambda` (L2) penalty terms.
   - DL models: **Dropout** layers randomly zero out 20% of neurons during training, forcing the network to not depend on any single neuron.
3. **Early stopping** (DL only) — watch validation loss during training. If it stops improving for 20 epochs, stop training and roll back to the best-seen weights.

## Hyperparameters and how we tune them

A **parameter** is something the model learns from data (e.g. the weights inside a neural network).
A **hyperparameter** is a setting *you* choose before training (e.g. how many trees in the forest? what learning rate?).

We tune hyperparameters with **GridSearchCV** — try every combination from a small list and keep the best.

For example, Random Forest has these hyperparameters:
```python
{
    'n_estimators': [100, 200, 500],     # how many trees
    'max_depth':    [5, 10, 20, None],   # how deep each tree can grow
    'min_samples_leaf': [1, 2, 4],       # min rows in any leaf
}
```
GridSearch trains the model with every combination (3 × 4 × 3 = 36 versions) and picks the best.

For speed, this project uses a *fast* grid (`RF_PARAMS_FAST` in `src/config.py`) for the inner tuning loop and uses LOYO-CV for the outer evaluation.

## Feature scaling

Some models care about the *scale* of features, others don't:

- **Tree models** (Random Forest, XGBoost) don't care: a tree splits on "rainfall > 800" — the units don't matter.
- **SVR and neural networks** care a lot. If `rainfall` is in 100s and `ndvi` is in 0.0–1.0 range, the network sees rainfall as "much bigger" and gives it disproportionate influence.

Fix: **StandardScaler** subtracts the mean and divides by standard deviation, so every feature has mean 0 and std 1. We fit the scaler **only on training data** (never on test data — that's a leak) and apply it to both.

## Time-series and sequences (for the LSTM/CNN-LSTM)

A **sequence** is a list of measurements ordered in time. For this project, the LSTM doesn't see one row of seasonal averages — it sees a (5 × 4) matrix per observation:

```
Month 1:  temp=25.2  rainfall=180  humidity=72  solar=18.5
Month 2:  temp=27.8  rainfall=200  humidity=70  solar=19.2
Month 3:  temp=29.1  rainfall=170  humidity=68  solar=20.0
Month 4:  temp=28.5  rainfall=140  humidity=71  solar=19.8
Month 5:  temp=27.0  rainfall=110  humidity=74  solar=18.0
```

5 timesteps × 4 weather variables = the LSTM input shape `(5, 4)`. The LSTM walks through the sequence step by step, building up an internal "memory" of what happened earlier in the season. This lets it answer questions like *"did rainfall come at the right time relative to flowering?"* — questions a single seasonal average can't capture.

In this project, since real monthly data isn't yet collected, `src/feature_engineer.py` synthesises plausible monthly trajectories from the seasonal aggregates (with a bell-shaped temperature curve and front-loaded rainfall). When real monthly NASA POWER data arrives, that function gets replaced with a real reader.

## Convolutional layers (CNN)

A **convolution** is a small filter that slides across input data and extracts patterns. The classic case is image processing: a 3×3 filter detects edges, another detects circles, etc. The network learns the filter values automatically.

For this project, we use **1D convolutions** on the satellite features. The CNN treats the 11 satellite features as a "1D image" and learns which combinations of features (e.g. "high NDVI alongside low LST") predict yield. It's a different way of looking at tabular data than a tree or a dense network.

## SHAP — making the black box explain itself

A trained model gives you a prediction. **SHAP** (SHapley Additive exPlanations) tells you *why*. For each prediction, it assigns each feature a number called the SHAP value:

- Positive SHAP for `season_mean_ndvi` → that feature pushed the prediction higher.
- Negative SHAP for `soil_ph` → that feature pulled the prediction down.

Average the absolute SHAP values across all predictions and you get a **feature importance ranking**: the features the model relies on most. From the synthetic-data run:

```
1. ndvi_x_lst         (NDVI × Land Surface Temperature) — 2.18
2. season_min_ndvi    — 0.68
3. season_mean_ndvi   — 0.58
```

Translation: the model leans heavily on satellite vegetation health and on the interaction between greenness and surface temperature. Soil features barely register. This is a **research finding** you put in the report.

SHAP plots are saved to `outputs/plots/results/shap_*.png`.

## Statistical significance — Wilcoxon and paired t-test

When two models have R² = 0.84 and 0.83, is the second one really worse? Or is it just random noise? We use **statistical tests**:

- **Paired t-test**: assumes errors are normally distributed. Standard test.
- **Wilcoxon signed-rank test**: doesn't assume normality. Safer for ML errors, which often have fat tails. We treat this as primary.

Both return a **p-value**. If p < 0.05, the difference is "statistically significant" — unlikely to be due to chance.

## Glossary in 30 seconds

| Term | Meaning |
|---|---|
| Feature | An input column (rainfall, NDVI, etc.) |
| Label / target | The thing we predict (yield) |
| Model | A function that maps features to predictions |
| Training | Tuning the model so its predictions match the labels |
| Loss | A number that measures how wrong the model is. Lower = better. |
| Epoch | One full pass through the training data |
| Batch | A small chunk of training data processed at once |
| Learning rate | How big a step the optimiser takes when adjusting weights |
| Optimiser | Algorithm that updates weights (we use Adam) |
| Overfitting | Memorising training data instead of generalising |
| Dropout | Randomly zeroing neurons during training to prevent overfitting |
| Early stopping | Stopping training when validation loss stops improving |
| Cross-validation | Repeatedly training on subsets to get an honest score |
| Hyperparameter | A setting you choose, not learned from data |
| Tensor | A multi-dimensional array (1D=vector, 2D=matrix, 3D+=tensor) |
| Pipeline | The end-to-end sequence: load → preprocess → train → evaluate |

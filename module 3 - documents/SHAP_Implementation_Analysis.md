## SHAP (SHapley Additive exPlanations) Implementation Analysis

**System:** AgriSense / AgroAI — Big Onion Yield Prediction & Decision Support
**Scope:** How SHAP is implemented today, whether the approach should differ by model type, which explainer belongs to which model, whether the current wiring matches each model's architecture, how contributions are generated, and what should change.
**Sources examined:** `src/explainer.py`, `src/api.py`, `src/xai/stability.py`, `src/xai/consensus.py`, `src/xai/run_xai.py`, `src/ml_models.py`, `src/dl_models.py`, `src/symbolic.py`, `src/physics_residual.py`, `src/stacking.py`, `src/run_padr.py`, `AgriSense_System_Architecture_Analysis.txt` (Sections 5–6).

---

### 1. Executive Summary

AgroAI trains **eleven** candidate models (three tabular ML models, four deep-learning models, one symbolic-regression equation, one physics-residual hybrid, one standalone parametric model (PADR), and three stacking combiners) but computes SHAP for **only two model families** — tree ensembles (RandomForest, XGBoost) via `TreeExplainer`, and SVR via `KernelExplainer`. This split is *correct as far as it goes*: it is not a bug that DL models, the symbolic equation, the physics-residual hybrid, PADR, and the stacking combiners have no SHAP path, because SHAP was only ever wired up for whichever model the Flask API can actually serve (`src/api.py::_load_state`'s `candidates` dict only loads `.pkl` files for RandomForest/XGBoost/SVR). The gap is real, however, the moment any of the other eight models becomes servable — which the project's own model-comparison table shows happens routinely (the "crowned" best-R² model on both data variants is currently a *non-servable* model: SymbolicRegression on `real`, StackConvex on `synthetic`).

**Bottom line recommendation:** SHAP should **not** be implemented the same way for every model. The correct explainer is a function of model architecture (tree vs. kernel vs. differentiable vs. hybrid vs. linear-combination), and the system already partially demonstrates this (`_init_explainer` branches on tree vs. non-tree). The remaining work is to extend that same architecture-aware branching to the other model families instead of silently having no explanation for them once they get served.

---

### 2. Model Inventory (what `main.py` actually trains)

| # | Model | Library / form | Architecture class | Currently servable via `/predict`? | Currently has SHAP? |
|---|---|---|---|---|---|
| 1 | RandomForest | `sklearn.ensemble.RandomForestRegressor` | Tree ensemble (bagging) | Yes | Yes — `TreeExplainer` |
| 2 | XGBoost | `xgboost.XGBRegressor` (+ monotonicity constraint on NDVI/EVI) | Tree ensemble (boosting) | Yes | Yes — `TreeExplainer` |
| 3 | SVR | `sklearn.svm.SVR` (RBF kernel, `StandardScaler`-fit input) | Kernel machine | Yes | Yes — `KernelExplainer` |
| 4 | LSTM | `tf.keras` stacked LSTM | Recurrent NN (sequence input) | No | **No** |
| 5 | BiLSTM | `tf.keras` bidirectional stacked LSTM | Recurrent NN (sequence input) | No | **No** |
| 6 | CNN | `tf.keras` 1D-CNN over tabular features reshaped to `(F,1)` | Convolutional NN | No | **No** |
| 7 | CNN-LSTM Hybrid | `tf.keras` multi-input (satellite CNN + weather LSTM + season scalar) | Hybrid multi-branch NN | No | **No** |
| 8 | SymbolicRegression | `gplearn` genetic-programming closed-form equation (`src/symbolic.py`) | Explicit algebraic expression, ≤5 features | No | **No** (not needed — see §4.6) |
| 9 | PhysicsResidual (`ResidualHybrid`) | FAO-33 mechanistic index (closed form) + `RandomForestRegressor` on the residual (`src/physics_residual.py`) | Additive hybrid: interpretable backbone + tree ensemble | No | **No** |
| 10 | PADR | Standalone parametric model, fit per-district weights via nested LOYO (`src/run_padr.py`) | Small parametric/linear-ish form | No | **No** |
| 11 | StackMean / StackInvRMSE / StackConvex | Weighted linear combination of the OOF predictions of models 1–10 (`src/stacking.py`) | Linear combiner over base learners | No | **No** |

Only models 1–3 are loadable by the live API (`_load_state`'s `candidates` dict). Models 4–11 are trained, benchmarked, and ranked in `model_comparison.csv`, but if one of them is crowned best (which the project's own honest results show happens on **both** data variants), the API silently falls back to the best *servable* model instead — meaning the model actually explained to the farmer is not always the model the report calls "best."

---

### 3. Current SHAP Implementation — As-Built

There are **three independent SHAP call sites** in the codebase, each with a different purpose:

**(a) `src/explainer.py::run_shap_analysis()`** — offline, dataset-level artefact.
Picks whichever of RandomForest/XGBoost is the better tree model (`_load_best_tree_model`), runs `shap.TreeExplainer(model).shap_values(X)` once over the full dataset, and persists `outputs/results*/feature_importance.json` (top-15 mean |SHAP|) plus summary/dependence plots. Explicitly documents *why* it restricts itself to tree models: "SHAP TreeExplainer is dramatically faster on tree models... even if a DL model has a better R², SHAP on KernelExplainer is too slow for the FYP report" (`src/explainer.py:21-25`). This is a deliberate, documented scope decision, not an oversight — but it does mean this artefact represents "the strongest interpretable tabular learner," never the actual crowned or actual served model if that differs.

**(b) `src/api.py::_init_explainer()` / `run_prediction()`** — online, per-request explanation.
Built once at server startup, keyed off whichever model got loaded:
```
if name in ('RandomForest', 'XGBoost'):
    _state['explainer'] = shap.TreeExplainer(model)
else:
    _state['explainer'] = shap.KernelExplainer(predict_fn, background)   # SVR path
```
`shap.kmeans(background_raw, min(25, len(background_raw)))` supplies the KernelExplainer's background; `shap_values(feature_row, nsamples=100, l1_reg=0, silent=True)` is called per `/predict` request. The `l1_reg=0` override is a documented, already-fixed correctness bug: SHAP's default `l1_reg="num_features(10)"` LASSO feature selection was silently zeroing 22 of 32 features' contributions (`src/api.py:566-572`). This is the only SHAP computation the farmer-facing UI ever sees (Explain/Recommend tabs read `shap_values` straight out of this response).

**(c) `src/xai/stability.py` / `src/xai/consensus.py`** — offline, per-fold diagnostic SHAP.
Every Leave-One-Year-Out fold refits the best tree model and computes `shap.TreeExplainer(fold_model).shap_values(X_full)` (`stability.py:104-105`), feeding both the Explanation Stability Coefficient / cross-fold SHAP consistency (which is one of ERI's two components — see `src/xai/eri.py`) and the consensus vote against permutation importance and the symbolic equation. This path is **also tree-only**, for the same latency reason as (a).

All three call sites converge on the same conclusion: **SHAP in this system is currently a tree-ensemble-first, KernelExplainer-as-fallback design.** That is architecturally sound for models 1–3, but structurally silent for models 4–11.

---

### 4. Should the SHAP Approach Be the Same for Every Model?

**No.** SHAP is a framework (Shapley-value attribution), not a single algorithm — the *exact* computation differs by model class, and using the wrong explainer either produces mathematically incorrect attributions or is computationally infeasible. Concretely:

1. **Tree ensembles (RF, XGBoost)** admit an exact, polynomial-time algorithm (`TreeExplainer`, Lundberg et al. 2020, "Consistent Individualized Feature Attribution for Tree Ensembles") that recursively walks the tree structure. Using `KernelExplainer` on a tree model would be strictly worse: slower, and only approximate, for no benefit.
2. **Kernel machines (SVR/RBF)** have no closed-form structure `TreeExplainer` can exploit — there is no tree to walk. `KernelExplainer`'s model-agnostic, sampling-based Shapley-kernel regression is the only option that respects the model's actual decision function (short of a linear-kernel special case, which does not apply here since the SVR is RBF).
3. **Differentiable models (LSTM/BiLSTM/CNN/hybrid)** have gradients but no tree structure and non-trivial input distributions (sequences, multi-branch inputs) — `DeepExplainer`/`GradientExplainer` (DeepLIFT/Integrated-Gradients-style approximations) apply, `TreeExplainer` categorically does not, and `KernelExplainer` would be both slow and a poor approximation for high-dimensional sequence inputs.
4. **The symbolic equation and PADR** are already closed-form/parametric — their own coefficients ARE the explanation. Running any SHAP explainer over them is technically possible (treat as a black box) but adds a sampling-approximation layer on top of a model that is already exactly interpretable; it would answer a question ("what does Shapley attribution say") that a strictly better answer ("here is the literal formula") already answers directly.
5. **The physics-residual hybrid** is additively composed of an interpretable, non-learned formula (Stage 1) and a RandomForest fit only on the leftover residual (Stage 2). Treating the whole hybrid as one opaque function and running `KernelExplainer` over it would *discard* the one piece of free interpretability the architecture was specifically designed to provide.
6. **Stacking combiners** are literal weighted sums of other models' outputs, `ŷ = Σ wᵢ · modelᵢ(x)`. Because Shapley values are linear in the value function, the mathematically correct — and cheapest — attribution is `SHAP_stack(x) = Σ wᵢ · SHAPᵢ(x)`, reusing each base model's own (correctly-chosen) explainer rather than wrapping the whole ensemble in a new one.

So the governing principle is: **pick the explainer that matches how the model actually computes its output**, not one uniform default. The project's own code already states this principle for the tree/kernel split (`src/api.py:359-370`'s docstring); it simply has not been extended past those two families yet.

---

### 5. Recommended Explainer per Model

| Model | Recommended explainer | Why |
|---|---|---|
| RandomForest | `shap.TreeExplainer(model, feature_perturbation="tree_path_dependent")` | Exact, closed-form, fast; already correctly used. |
| XGBoost | `shap.TreeExplainer(model)` (XGBoost has native SHAP support via its own booster, which `TreeExplainer` calls into) | Exact, fast; monotonicity constraint does not affect SHAP correctness — it constrains training, not attribution. Already correctly used. |
| SVR (RBF) | `shap.KernelExplainer` (current) **or** `shap.explainers.Permutation` as a faster, less approximate-in-a-different-way alternative | No closed-form algorithm exists for an RBF kernel model; model-agnostic sampling is the only option. `Permutation` explainer is a reasonable modern alternative worth benchmarking — same generality, often better sample efficiency than classic Kernel SHAP. |
| LSTM / BiLSTM | `shap.DeepExplainer(model, background_seq)` (TF/Keras-native, DeepLIFT-style) — `shap.GradientExplainer` as a fallback if `DeepExplainer` has TF-version compatibility issues | Differentiable recurrent architecture; DeepExplainer is purpose-built for Keras/TF sequence models and is far cheaper than Kernel/Permutation on a 5-step × N-weather-feature input. |
| CNN (1D, tabular reshaped) | `shap.DeepExplainer` (or `shap.GradientExplainer`) over the `(F, 1)` input tensor | Same reasoning as above; convolutional layers are differentiable, gradient-based attribution is the natural fit. **Caveat:** this model's "sequence" is a documented synthetic sine-curve expansion of scalar features (`dl_models.py` module docstring / architecture doc §5.1), so any SHAP explanation of it would be attributing to an artefact of feature engineering, not a real temporal signal — flag this prominently if ever surfaced to a user. |
| CNN-LSTM Hybrid | `shap.DeepExplainer(model, [sat_background, seq_background, season_background])` | `DeepExplainer` and `GradientExplainer` both support multi-input Keras models by accepting a list of background arrays matching the model's input list — matches this model's 3-input signature directly. |
| SymbolicRegression | **No SHAP explainer** — expose the equation's own coefficients as the explanation (already available via `GET /equation`) | The model already provides better-than-SHAP transparency: the literal formula. Optionally, a `KernelExplainer` pass could be run purely as a *cross-check* against `src/xai/consensus.py`'s existing symbolic-vs-SHAP-vs-permutation agreement metric, but it should never replace showing the equation itself. |
| PhysicsResidual (`ResidualHybrid`) | **Decompose, don't wrap:** report the mechanistic-index contribution directly (it's a closed-form formula — no explainer needed) + `shap.TreeExplainer` on the Stage-2 `RandomForestRegressor` residual model only | Wrapping the whole hybrid in `KernelExplainer` would erase the one part of this architecture that's exactly interpretable by construction. The correct "SHAP" story here is *not full SHAP* — it's formula-term contribution + tree-SHAP on the residual, summed. |
| PADR | Inspect `src/run_padr.py`'s actual functional form before choosing; if it is linear/near-linear in its per-district weights, `shap.LinearExplainer` is exact and near-free; otherwise `shap.KernelExplainer` as the generic fallback | Parametric models with a linear or additive closed form should use `LinearExplainer`, not the slower Kernel path, whenever the linearity assumption actually holds. |
| StackMean / StackInvRMSE / StackConvex | **No new explainer** — compute `SHAP_stack = Σ wᵢ · SHAPᵢ(x)` using each base model's own recommended explainer above, weighted by the same convex/inverse-RMSE/equal weights the combiner already stores in `stacking_summary.json` | Exploits the linearity of Shapley values; mathematically exact, and reuses explainers already built for models 1–10 rather than adding a third computation. |

---

### 6. Does the Current Implementation Match Each Model's Architecture? (Gap Audit)

| Model | Ideal explainer | Actual | Match? |
|---|---|---|---|
| RandomForest | TreeExplainer | TreeExplainer | ✅ Exact match |
| XGBoost | TreeExplainer | TreeExplainer | ✅ Exact match |
| SVR | KernelExplainer (or Permutation) | KernelExplainer | ✅ Correct family; worth A/B-testing `Permutation` for speed |
| LSTM / BiLSTM | DeepExplainer / GradientExplainer | *None* | ❌ Gap — no explainer wired at all |
| CNN | DeepExplainer / GradientExplainer | *None* | ❌ Gap |
| CNN-LSTM Hybrid | DeepExplainer (multi-input) | *None* | ❌ Gap |
| SymbolicRegression | Equation itself (no SHAP needed) | *None* | ⚠️ Acceptable by design, but not explicit — `consensus.py` treats symbolic "votes" by feature membership, not SHAP, which is the right call but should be documented as intentional, not missing |
| PhysicsResidual | Formula term + TreeExplainer on residual | *None* | ❌ Gap — and the most valuable one to close, since this is the project's own "novel" hybrid architecture and currently the least explainable of the interpretable-by-design models |
| PADR | LinearExplainer or KernelExplainer (pending form check) | *None* | ❌ Gap |
| Stacking combiners | Weighted sum of base SHAP | *None* | ❌ Gap |

Net: **the two call sites that exist are internally correct** (right explainer for the right model family); **the failure mode is coverage, not correctness** — 8 of 11 trained models have no attribution path at all, and the project's own "crowned best model" is a non-servable, non-explained model on both data variants today.

---

### 7. How Feature Contributions Are Actually Generated, Per Explainer Type

- **`TreeExplainer` (RF, XGBoost):** exact Shapley values via a polynomial-time recursive algorithm that traverses every decision path in every tree, weighting each split by the fraction of training samples that reach it. No sampling, no background dataset required for the interventional-perturbation variant used here (fit directly on the model, `explainer.shap_values(model_input)`). Deterministic and reproducible given a fixed model.
- **`KernelExplainer` (SVR):** approximate Shapley values via weighted linear regression over a sample of feature "coalitions" (subsets of features fixed to background values vs. the query row), using the Shapley kernel weighting to make that regression's coefficients converge to true Shapley values. Cost scales with `nsamples` × background size × number of features — hence the `nsamples=100`, 25-row k-means background, and `l1_reg=0` tuning already present in `src/api.py`.
- **`DeepExplainer` (recommended for LSTM/BiLSTM/CNN/hybrid, not yet implemented):** approximates Shapley values via DeepLIFT-style backpropagation of contribution scores from output to input, using a background sample to define a "reference" activation at each layer. One forward+backward pass per background sample, much cheaper than Kernel SHAP for the same feature count, but requires the *fitted scaler* to be applied identically to both the background set and the query input.
- **`GradientExplainer` (fallback for the above):** uses expected gradients (a variant of Integrated Gradients) integrated over paths from background samples to the query input — a lighter-weight alternative when `DeepExplainer` hits TF-version incompatibilities.
- **`LinearExplainer` (candidate for PADR if linear):** exact, closed-form Shapley values computed directly from the model's coefficients and the background feature covariance — effectively free compared to any sampling-based method.
- **Formula-term contribution (symbolic equation, physics backbone):** not SHAP at all — the "contribution" of each term is just that term's literal numeric value in the equation/formula, already exact and requiring no approximation.
- **Linear combination (stacking):** `SHAP_stack,j(x) = Σᵢ wᵢ · SHAPᵢ,j(x)` for feature `j` — a weighted sum of each base learner's own per-feature SHAP value, using whichever explainer is correct for that base learner.

---

### 8. How SHAP Should Be Integrated Into the Prediction Pipeline

The system already gets the **offline vs. online split** right and this should be preserved:

- **Offline (training-time, `main.py` / `run_xai.py`):** dataset-level feature importance (`feature_importance.json`), LOYO-fold SHAP-consistency diagnostics (`explanation_stability.json`), and consensus voting (`explanation_consensus.json`) — all currently tree-only. **Recommendation:** extend `run_shap_analysis()` to *also* persist a DL-model SHAP artefact (via `DeepExplainer`) and a residual-model artefact (via `TreeExplainer` on the Stage-2 RF), gated behind an explicit flag/argument so the "fast tree-only" default documented in `explainer.py:21-25` is preserved for routine runs and the slower DL pass is opt-in.
- **Online (per-request, `src/api.py`):** SHAP computed fresh against the exact resolved feature vector for whichever model is currently loaded — this is the correct design (explanation must match the actual served prediction, not a cached generic one) and should be generalized, not replaced:
  1. `_init_explainer(name)` should grow additional branches — `DeepExplainer`/`GradientExplainer` for the four Keras models, `LinearExplainer` for PADR (pending its functional form), the formula+residual decomposition for the physics hybrid, and the weighted-sum trick for any stacking combiner that becomes servable.
  2. `_load_state()`'s `candidates` dict should be extended so these models are actually *loadable* in the first place — right now, adding an explainer branch for e.g. LSTM would be moot, since the API never loads a `.keras` artefact at all (Section 5.4 of the architecture analysis confirms "Deep-learning models are trained and benchmarked for the comparison table but are never loadable by the live API"). Explainer coverage and model-serving coverage need to be extended together.
  3. Whatever model is crowned by `evaluator.py::generate_final_comparison()` should either be made servable+explainable, or the API's fallback-to-best-servable-model behavior should be surfaced explicitly in the UI as "showing model X, not the top-ranked model Y" — currently this substitution happens silently (per architecture doc §5.4), which is a transparency gap independent of SHAP itself.
- **Consistency layer:** regardless of which explainer produced them, all per-feature SHAP values returned to the frontend must stay in the same units/sign convention (`positive = pushes yield up`) and the same 32-key `ALL_FEATURES` schema — this constraint is already respected today and should be treated as a hard invariant when adding new explainer branches, since `dashboard/lib/api.ts::convertSHAPToExplanation()` and `dashboard/lib/agronomy.ts`'s rule engine both assume that schema unconditionally.

---

### 9. Recommended Changes — Prioritized

**Correctness**
1. None found in the two existing explainer branches themselves — `TreeExplainer` and `KernelExplainer` are each the right choice for their model family, and the `l1_reg=0` fix already resolved the one known correctness bug (silent zeroing of 22/32 features).
2. If/when the physics-residual hybrid or a stacking combiner is wired for SHAP, do **not** wrap the whole composite model in a single black-box explainer — that would produce numerically "valid" but architecturally misleading attributions (crediting the mechanistic backbone's contribution to a generic feature-perturbation estimate instead of reporting its exact, already-known formula term).

**Consistency**
3. Extend `_init_explainer` with explicit branches for Keras models (`DeepExplainer`/`GradientExplainer`), the physics-residual hybrid (formula term + `TreeExplainer` on the residual RF), and PADR (`LinearExplainer` or `KernelExplainer` per its actual form) — otherwise every one of these models silently returns `shap_values: {}` the moment it becomes the loaded/servable model, exactly as SVR did before the KernelExplainer branch was added.
4. Extend `_load_state()`'s `candidates` dict in step with the above so newly-explainable models are also actually loadable — an explainer with nothing to explain is dead code.
5. Make the "crowned vs. served" substitution (Section 5.4 of the architecture analysis) visible in the API response (e.g. a `served_model_is_crowned: bool` + `crowned_model_name` field) so the UI/report can state plainly when the explained model is not the top-ranked one.
6. For the stacking combiners, persist SHAP as the documented weighted sum of base-model SHAP rather than treating them as unexplainable — this is a near-zero-cost addition since it only requires each base model's already-computed SHAP values and the weights `stacking_summary.json` already stores.

**Efficiency**
7. Benchmark `shap.explainers.Permutation` against the current `KernelExplainer` for SVR — modern SHAP releases often make Permutation the faster general-purpose default for kernel-machine-class models at comparable accuracy.
8. If a DL model's SHAP pass is added to the offline `run_shap_analysis()` artefact, gate it behind an explicit opt-in (e.g. a CLI flag) rather than making it part of the default `main.py` run — the existing "TreeExplainer is fast enough, KernelExplainer/DeepExplainer would slow down the FYP report generation" tradeoff documented in `explainer.py` is a legitimate constraint that should be preserved, not silently dropped, as coverage is extended.
9. Cache `DeepExplainer`/`GradientExplainer` background tensors at server startup (mirroring the existing `shap.kmeans(..., min(25, len(background_raw)))` pattern used for KernelExplainer) so per-request latency for any newly-explainable DL model stays bounded, the same way it is already bounded for SVR today.

---

### 10. Summary Table — Full Recommended Mapping

| Model | Type | Recommended SHAP mechanism | Status today |
|---|---|---|---|
| RandomForest | Tree ensemble | TreeExplainer | Implemented |
| XGBoost | Tree ensemble | TreeExplainer | Implemented |
| SVR | Kernel machine | KernelExplainer (or Permutation) | Implemented |
| LSTM | Recurrent NN | DeepExplainer / GradientExplainer | Not implemented |
| BiLSTM | Recurrent NN | DeepExplainer / GradientExplainer | Not implemented |
| CNN | Convolutional NN | DeepExplainer / GradientExplainer | Not implemented |
| CNN-LSTM Hybrid | Multi-input NN | DeepExplainer (multi-input) | Not implemented |
| SymbolicRegression | Closed-form equation | None needed — equation is the explanation | N/A by design |
| PhysicsResidual | Formula + tree residual | Formula term + TreeExplainer on residual | Not implemented |
| PADR | Parametric model | LinearExplainer (if linear) / KernelExplainer | Not implemented |
| Stacking (Mean/InvRMSE/Convex) | Linear combiner | Weighted sum of base-model SHAP | Not implemented |

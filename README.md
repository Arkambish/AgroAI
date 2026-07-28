# Big Onion Yield Prediction — Agro AI

End-to-end system for predicting big onion (*Allium cepa*) harvest yield across four Sri Lankan
districts (Matale, Anuradhapura, Polonnaruwa, Kurunegala).

University of Moratuwa, Faculty of Information Technology, FYP 2026.

| Member | Index | Component |
|---|---|---|
| Arkam B.H.M. | 214019K | ML/DL modelling pipeline, evaluation, Flask API |
| Sharuja B. | 214192G | Data engineering + feature engineering |
| Shathurya P. | 214193K | Dashboard, visualisation, explainability UX |

---

## Read this before quoting any number

This project reports a **negative result**, and that is the finding rather than a failure.

On the real data — 28 district-year rows, Yala only, 2019–2025 — **no model beats predicting the
training-year average.** The honest leave-one-year-out (LOYO) scoreboard:

| Model | R² | RMSE |
|---|---|---|
| *climatology (no features at all)* | *−0.215* | *6.73* |
| SymbolicRegression (best model) | −0.209 | 6.72 |
| SVR (served by the API) | −0.307 | 6.98 |
| PADR | −0.374 | 7.33 |
| RandomForest | −0.542 | 7.59 |
| XGBoost | −0.711 | 7.99 |
| CNN-LSTM hybrid | −3.635 | 13.15 |

This is explained, not hidden. 63.6% of the target's variance lies between years, and LOYO removes
exactly that; measurement error accounts for over half of what remains within a year. The attainable
R² ceiling on this panel is **+0.162**, so the proposal-stage target of 0.75 was never reachable.

**There are two data variants and they must never be confused.**

| | `DATA_VARIANT=real` | `DATA_VARIANT=synthetic` (default) |
|---|---|---|
| Rows | 28 (4 districts × 7 years, Yala) | 136 (incl. Jaffna, both seasons) |
| Best R² | **−0.209** | +0.848 |
| Outputs | `outputs/*_real/` | `outputs/*/` |
| Use it for | **every number in the report** | software demos, UI screenshots, tests |

The synthetic variant exists to demonstrate that the system works end to end. Its R² of 0.85 is
**not a result** and must never appear in the report or a viva without the variant named in the same
breath.

---

## Quick start

Requires **Python 3.12** (TensorFlow does not yet support 3.13+) and **Node ≥ 20**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
```

### 1 — Train

```bash
DATA_VARIANT=real python main.py --real     # honest pipeline,  ~3 min
python main.py                              # synthetic demo,   ~1 min
```

Useful flags: `--skip-eda`, `--skip-dl`, `--skip-symbolic`, `--skip-ablation`, `--skip-stacking`.

### 2 — Serve

macOS reserves port 5000 for AirPlay Receiver, so the API runs on **5050** — the dashboard's
`.env.local` already points there.

```bash
DATA_VARIANT=real PORT=5050 python src/api.py
```

An invalid `DATA_VARIANT` now fails immediately with the valid values rather than starting a
half-working server that returns 503 from every endpoint.

### 3 — Dashboard

```bash
cd dashboard && npm install && npm run dev     # → http://localhost:3000
```

| Route | Purpose |
|---|---|
| `/[locale]` | KPI cards, district choropleth, seasonal comparison |
| `/[locale]/predict` | Prediction form with auto-filled context |
| `/[locale]/explain` | SHAP attributions + explanation-reliability index |
| `/[locale]/recommend` | LLM-generated agronomic advice |

Trilingual: English, Sinhala (`si`), Tamil (`ta`).

### 4 — Tests

```bash
python -m pytest                # 37 backend tests
cd dashboard && npm test        # 30 frontend tests (vitest)
```

The backend suite is written as tripwires on defects this project has actually had: synthetic rows
reaching the trained panel, augmentation improving honest scores, the API reporting one model's
accuracy while serving another, and a climatological average being presented as a year-specific
forecast. `tests/test_frontend_backend_contract.py` also enforces that `dashboard/lib/features.ts`
mirrors `config.ALL_FEATURES` and that every locale defines every `en.json` key.

---

## What the pipeline does

1. **Load** the monthly DCS panel and aggregate to 28 district-year rows. Rows marked
   `source=synthetic` are filtered out — they previously reached the target and made ~40% of it
   fabricated.
2. **Engineer** 32 features in five groups: 9 weather, 11 satellite, 5 historical, 4 soil,
   3 interaction.
3. **Train 13 models** under leave-one-year-out CV: RandomForest, XGBoost, SVR, LSTM, BiLSTM, 1D-CNN,
   hybrid CNN-LSTM, SymbolicRegression, PhysResidual, PADR, and three stacking combiners.
4. **Calibrate** conformal prediction intervals, compute SHAP, run ablations.
5. **Serve** one model over Flask; the dashboard consumes it.

### Analyses beyond the model comparison

| Script | What it establishes |
|---|---|
| `src/integrity_audit.py` | Random 5-fold reports R² 0.552 where honest LOYO gives 0.044 — a 12× inflation. Also shows augmentation degrades honest scores monotonically. |
| `src/weather_forecast.py` | Monte Carlo over unknown future weather, resampling whole analogue years from a 45-year (1981–2025) NASA POWER pool. |
| `src/forecast_leadtime.py` | Skill against forecast issue date. Never beats climatology at any lead. |
| `src/decision_loss.py` | Storage-coupled decision loss and the break-even skill frontier. |
| `src/figures_decision.py` | Figures 7.6 and 7.7 of the final report. |

---

## Layout

```
src/                Python pipeline + Flask API   (see config.py for all knobs)
dashboard/          Next.js dashboard, App Router, TypeScript, Tailwind 4
tests/              pytest suite
data/collected/     source CSVs (only 4 of 10 files are actually read)
data/processed_real/  the 28-row panel the models train on
outputs/results_real/ honest metrics, JSON + CSV
outputs/models_real/  trained artefacts
docs/               explainers, findings, reports
main.py             run the whole pipeline
```

Trained models, plots and `node_modules/` are not version-controlled. Run the pipeline and
`npm install` once after cloning.

---

## Documentation

Start with **[docs/START_HERE.md](docs/START_HERE.md)** — a from-zero guide that also flags which of
the older explainers are stale.

| Doc | Contents |
|---|---|
| [PADR_FINDINGS.md](docs/PADR_FINDINGS.md) | Authoritative results for the corrected pipeline |
| [09_SYSTEM_AUDIT.md](docs/09_SYSTEM_AUDIT.md) | Known defects and inconsistencies |
| [05_NOVELTY_AND_RESEARCH.md](docs/05_NOVELTY_AND_RESEARCH.md) | Research contribution |
| [00–07_*.md](docs/) | Original explainer series (partly superseded) |

Final report: `outputs/Final_Report_AgroAI.docx`, generated by
`DATA_VARIANT=real python src/generate_final_docx.py`.

---

## Known issues

Recorded here rather than in a private list, because they affect how results should be read.

- **Two leaks remain in the panel.** `prev_year_yield` is literally the previous year's target
  (verified in 22 of 24 district-year pairs), and `ndvi_anomaly` / `drought_index_spi` are
  standardised against all 2019–2025 data ([`data_loader.py:244`](src/data_loader.py#L244)). Both
  inflate every model's score and must be fixed before submission.
- **Sequence models are fed manufactured input.** `feature_engineer.py:20` expands four seasonal
  averages into a 5-step "monthly" series with a fixed sine curve and fixed weights. Its own
  docstring says *"Synthetic-only"*. The LSTM/CNN-LSTM results therefore cannot support a claim
  about temporal modelling.
- **Six of the 32 features are constants** (`season_avg_solar_rad = 18.0`,
  `extent_prev_season = 400.0`, `organic_carbon = 1.8`, `heat_stress_days = 0`, …).
- **Kurunegala and Matale share a NASA POWER grid cell** — byte-identical daily weather on 100% of
  days, so the panel has three independent weather series, not four.
- **`data/raw/` is empty**; the `REQUIRED_FILES` path in `data_loader.py` is dead scaffolding.
- **Five files in `data/collected/` are unused**, two of which (`Sentinal.csv`,
  `Geospatial data.csv`) contain no measurement columns at all — the Earth Engine export ran without
  a band reduction.

## Notes

- All randomness is seeded (`RANDOM_STATE=42`); runs are reproducible.
- DL epochs per fold are set by `SYNTHETIC_MODE_DL_EPOCHS` in `src/config.py`.
- `src/data_collection/gee_ndvi_export.js` re-exports MODIS NDVI over district polygons including
  Kurunegala. It has never been run, and doing so is the highest-value data action available.

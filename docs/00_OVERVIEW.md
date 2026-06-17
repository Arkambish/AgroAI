# 00 — Overview

This is your project explained from the ground up. You said you don't know Python or ML/DL, so each doc starts at zero. Read them in order:

| # | File | What you'll learn |
|---|---|---|
| 0 | **00_OVERVIEW.md** (you are here) | Big picture in one page |
| 1 | [01_PROBLEM_AND_DATA.md](01_PROBLEM_AND_DATA.md) | The agricultural problem, the four districts, the data sources, and why we're using synthetic data right now |
| 2 | [02_ML_DL_FUNDAMENTALS.md](02_ML_DL_FUNDAMENTALS.md) | What machine learning and deep learning actually are, in plain English, with the concepts this project uses |
| 3 | [03_PIPELINE_WALKTHROUGH.md](03_PIPELINE_WALKTHROUGH.md) | Every file in the project, line by line, what it does and why |
| 4 | [04_MODELS_EXPLAINED.md](04_MODELS_EXPLAINED.md) | Each of the 7 models — Random Forest, XGBoost, SVR, LSTM, BiLSTM, CNN, Hybrid CNN-LSTM — explained simply |
| 5 | [05_NOVELTY_AND_RESEARCH.md](05_NOVELTY_AND_RESEARCH.md) | What's actually new about this research and why it counts as a Final Year Project contribution |
| 6 | [06_RESULTS_AND_INTERPRETATION.md](06_RESULTS_AND_INTERPRETATION.md) | What the numbers in `outputs/results/` mean and what they tell you |
| 7 | [07_HOW_TO_RUN.md](07_HOW_TO_RUN.md) | Exact commands to run the pipeline, the API, and individual steps |

---

## What this project does, in one paragraph

It predicts how much **big onion** (Allium cepa) will be harvested per hectare in four Sri Lankan districts (Matale, Anuradhapura, Polonnaruwa, Kurunegala) for both growing seasons (Yala and Maha). Instead of waiting for the harvest and counting tons, the model looks at *upstream signals* — rainfall, temperature, satellite vegetation greenness (NDVI), soil pH, and previous years' yields — and outputs a number like "**16.5 metric tons per hectare**" months before harvest. That early forecast helps the government plan onion imports, helps farmers price their crop, and helps researchers understand what drives yield.

## What's the research contribution?

Three things:

1. **First ML vs DL comparison for vegetable yield prediction in Sri Lanka under data scarcity.** Most existing crop-yield ML work is on rice (paddy) — that's a well-studied problem with thousands of data points. Big onions are harder: there's no systematic survey methodology, so we have only a few hundred data points across 20 years. This research asks: *with this little data, does deep learning still beat classical machine learning?*
2. **A novel hybrid CNN-LSTM architecture** that explicitly models the bimodal Yala/Maha monsoon system. It feeds satellite data into a CNN branch, weather time-series into an LSTM branch, and concatenates a **season indicator** (Yala=1, Maha=0) before the final prediction layer — so the model can learn season-specific patterns rather than averaging across seasons.
3. **A rigorous ablation study** that quantifies how much each data source (weather, satellite, historical, soil) contributes to prediction accuracy. The headline finding from synthetic data: *adding satellite imagery to weather data improves R² by 55 percentage points* — i.e., satellite data is doing most of the work.

## Where to find what

```
docs/         ← these explainer markdowns
src/          ← Python code (main pipeline)
data/         ← input data (raw CSVs go in raw/, synthetic generated to synthetic/)
outputs/      ← all results: model files, plots, CSVs
main.py       ← run the whole pipeline with one command
```

## What "results" means here

After running `python main.py`, look at:

- `outputs/results/final_summary.txt` — plain-English answers to the 9 research questions
- `outputs/results/model_comparison.csv` — the leaderboard: which model won, by how much
- `outputs/plots/results/model_comparison_bar.png` — the same as a chart
- `outputs/plots/results/shap_summary.png` — which features drove predictions
- `outputs/results/ablation_results.csv` — the data-source contribution study

These are exactly the artefacts you'd put into the FYP final report.

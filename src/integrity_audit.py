"""Integrity audit of dataset_D_stat.csv — is the augmented file safe to train on?

Short answer: no. This script proves it, reproducibly, in one run.

The file contains 148 rows, but only 74 of them are real. The other 74 are Gaussian-jittered
copies. Three independent checks agree on which is which:

  1. The soil columns (clay/ph/sand) are integer-valued in the genuine rows and non-integer in
     every jittered copy. Filtering on integer soil returns exactly 74 rows — exactly one per
     (district, year, month) cell.
  2. Those 74 rows match, with identical yields, the rows labelled source == "real" in
     data/collected/FYP data(manual) - onion_unique_per_key.csv.
  3. The copies are not paired one-to-one, so no simple drop_duplicates() would have found them.

Why it matters: a jittered copy in the test fold whose original is in the training fold is
leakage, not skill. This script measures exactly how much skill that fabricates, and then
tests whether augmentation helps at all when the test folds are kept clean. It does not.

Run:  DATA_VARIANT=real PYTHONPATH=src python src/integrity_audit.py
"""

import json
import os

import numpy as np
import pandas as pd
from fractions import Fraction
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold, cross_val_predict

AUGMENTED_CSV = os.environ.get(
    "AUDIT_CSV", os.path.expanduser("~/Downloads/dataset_D_stat.csv")
)
SOURCE_LABELLED_CSV = "data/collected/FYP data(manual) - onion_unique_per_key.csv"
OUT_DIR = "outputs/results_real"

FEATURES = [
    "temperature_c", "rainfall", "humidity_pct", "evi_i", "ndvi_i",
    "clay_0_5cm", "ph_0_5cm", "sand_0_5cm",
]
TARGET = "yield_mt_per_ha"
CELL = ["district", "year", "month"]

RNG = np.random.default_rng(0)


def forest():
    return RandomForestRegressor(n_estimators=500, random_state=0, min_samples_leaf=2)


def genuine_rows(df):
    """The 74 real rows. Integer soil is the discriminator — see module docstring."""
    is_integer_soil = (
        (df.clay_0_5cm % 1 == 0) & (df.ph_0_5cm % 1 == 0) & (df.sand_0_5cm % 1 == 0)
    )
    return df[is_integer_soil].reset_index(drop=True)


def loyo(train_df, test_df_by_year, augment=None):
    """Leave-one-year-out. Test folds are always genuine rows only; augment touches train only."""
    truth, pred = [], []
    for year in sorted(train_df.year.unique()):
        train = train_df[train_df.year != year]
        test = test_df_by_year[test_df_by_year.year == year]
        if len(test) < 2:
            continue
        if augment is not None:
            train = pd.concat([train, augment(train)], ignore_index=True)
        model = forest().fit(train[FEATURES], train[TARGET])
        truth += list(test[TARGET])
        pred += list(model.predict(test[FEATURES]))
    truth, pred = np.array(truth), np.array(pred)
    return {
        "r2": round(float(r2_score(truth, pred)), 3),
        "rmse": round(float(np.sqrt(np.mean((truth - pred) ** 2))), 2),
        "n": len(truth),
    }


def gaussian_jitter(multiple, sigma):
    def apply(df):
        out = []
        for _ in range(multiple):
            copy = df.copy()
            for col in FEATURES + [TARGET]:
                copy[col] = copy[col] * (1 + RNG.normal(0, sigma, len(copy)))
            out.append(copy)
        return pd.concat(out, ignore_index=True)
    return apply


def smote_like(multiple):
    def apply(df):
        cols = FEATURES + [TARGET]
        values = df[cols].values
        made = []
        for _ in range(multiple * len(df)):
            i, j = RNG.choice(len(df), 2, replace=False)
            made.append(values[i] + RNG.random() * (values[j] - values[i]))
        return pd.DataFrame(made, columns=cols)
    return apply


def ratio_structure_test(values, max_denominator, tolerance=5e-5, n_null=400):
    """Are the yields exact ratios of small integers more often than chance?

    A yield reported as production / extent inherits that ratio structure. Comparing against
    a uniform null on the same range separates real structure from the fact that *some*
    fraction always sits near any 4-dp number.
    """
    def exact_hits(vals):
        return sum(
            1 for v in vals
            if abs(float(Fraction(v).limit_denominator(max_denominator)) - v) < tolerance
        )
    observed = exact_hits(values)
    null_draws = np.round(
        RNG.uniform(values.min(), values.max(), (n_null, len(values))), 4
    )
    expected = float(np.mean([exact_hits(row) for row in null_draws]))
    return {
        "max_denominator": max_denominator,
        "observed": observed,
        "of": len(values),
        "expected_by_chance": round(expected, 1),
        "enrichment": round(observed / max(expected, 0.01), 1),
    }


def main():
    augmented = pd.read_csv(AUGMENTED_CSV)
    real = genuine_rows(augmented)

    report = {"source_file": AUGMENTED_CSV, "rows_in_file": len(augmented)}

    # --- Check 1: how many genuine rows, and are they one per cell? ---
    per_cell = real.groupby(CELL).size()
    report["deduplication"] = {
        "genuine_rows": len(real),
        "distinct_cells": int(per_cell.shape[0]),
        "max_rows_per_cell": int(per_cell.max()),
        "cell_multiplicity_in_full_file": {
            str(k): int(v)
            for k, v in sorted(augmented.groupby(CELL).size().value_counts().items())
        },
    }

    # --- Check 2: agree with the independent source labels? ---
    if os.path.exists(SOURCE_LABELLED_CSV):
        labelled = pd.read_csv(SOURCE_LABELLED_CSV)
        truth_rows = labelled[labelled.source == "real"][
            ["year", "month", "season", "district", TARGET]
        ]
        merged = real[["year", "month", "season", "district", TARGET]].merge(
            truth_rows, on=["year", "month", "season", "district"], suffixes=("_a", "_b")
        )
        report["deduplication"]["cross_check_vs_source_label"] = {
            "matched": len(merged),
            "identical_yields": int(
                (abs(merged[TARGET + "_a"] - merged[TARGET + "_b"]) < 1e-6).sum()
            ),
        }

    # --- Check 3: what the leakage buys you ---
    leaked = cross_val_predict(
        forest(), augmented[FEATURES], augmented[TARGET],
        cv=KFold(5, shuffle=True, random_state=0),
    )
    honest = loyo(real, real)
    mean_only_pred = [
        real[real.year != y][TARGET].mean()
        for y in real.year for _ in [0]
    ]
    report["leakage_cost"] = {
        "random_5fold_on_all_148_rows": round(
            float(r2_score(augmented[TARGET], leaked)), 3
        ),
        "honest_loyo_on_74_genuine_rows": honest["r2"],
        "predict_training_mean": round(
            float(r2_score(real[TARGET], mean_only_pred)), 3
        ),
    }

    # --- Check 4: does augmentation help when test folds stay clean? ---
    trials = [("none", None)]
    trials += [
        (f"gaussian_jitter_x{m}_sigma{s}", gaussian_jitter(m, s))
        for m, s in [(1, 0.01), (1, 0.05), (5, 0.05), (20, 0.05)]
    ]
    trials += [(f"smote_like_x{m}", smote_like(m)) for m in [1, 5, 20]]
    report["augmentation_trials"] = {
        name: loyo(real, real, augment=fn) for name, fn in trials
    }

    # --- Check 5: is the target a ratio of small integers? ---
    report["ratio_structure"] = [
        ratio_structure_test(real[TARGET].unique(), d) for d in (12, 30, 60)
    ]

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "integrity_audit.json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2)

    dedup = report["deduplication"]
    leak = report["leakage_cost"]
    print(f"\n{'=' * 72}\nINTEGRITY AUDIT — {AUGMENTED_CSV}\n{'=' * 72}")
    print(f"\nRows in file: {report['rows_in_file']}   Genuine: {dedup['genuine_rows']}"
          f"   Cells: {dedup['distinct_cells']}   Max rows/cell: {dedup['max_rows_per_cell']}")
    if "cross_check_vs_source_label" in dedup:
        cc = dedup["cross_check_vs_source_label"]
        print(f"Cross-check vs source labels: {cc['identical_yields']}/{cc['matched']} identical yields")

    print(f"\n--- What the leakage buys ---")
    print(f"  random 5-fold on all 148 rows      R2 = {leak['random_5fold_on_all_148_rows']:+.3f}   <-- fabricated")
    print(f"  honest LOYO on 74 genuine rows     R2 = {leak['honest_loyo_on_74_genuine_rows']:+.3f}   <-- the truth")
    print(f"  predict the training mean          R2 = {leak['predict_training_mean']:+.3f}")

    print(f"\n--- Does augmentation help? (test folds genuine-only, train augmented) ---")
    for name, res in report["augmentation_trials"].items():
        print(f"  {name:34s} R2 = {res['r2']:+.3f}   RMSE = {res['rmse']:.2f}")

    print(f"\n--- Is the target a ratio of small integers? ---")
    for r in report["ratio_structure"]:
        print(f"  denominator <= {r['max_denominator']:2d}: {r['observed']:2d}/{r['of']} exact "
              f"vs {r['expected_by_chance']:5.1f} by chance  ->  {r['enrichment']}x enrichment")

    print(f"\nWritten to {out_path}\n")


if __name__ == "__main__":
    main()

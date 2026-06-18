"""End-to-end runner for the Big Onion yield prediction pipeline.

Usage:
  python main.py
  python main.py --skip-eda --skip-shap
  python main.py --skip-dl
  python main.py --skip-ablation
"""

import argparse
import os
import sys
import time

# Make src/ importable for the bare `from config import *` style used inside.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Select the data variant BEFORE importing config-dependent modules so the
# variant-aware output dirs (outputs/*_real) resolve correctly.
if '--real' in sys.argv:
    os.environ['DATA_VARIANT'] = 'real'

from data_loader import load_data
from preprocessor import preprocess
from feature_engineer import engineer_features
import config


def main(args: argparse.Namespace) -> None:
    start = time.time()

    for d in (
        config.MODELS_DIR, config.EDA_PLOTS_DIR, config.TRAIN_PLOTS_DIR,
        config.PLOTS_DIR, config.RESULTS_DIR,
    ):
        os.makedirs(d, exist_ok=True)

    print('\n' + '=' * 60)
    print('  AGRO AI — BIG ONION YIELD PREDICTION PIPELINE')
    print('  Arkam B.H.M. (214019K) | University of Moratuwa')
    print(f'  DATA VARIANT: {config.DATA_VARIANT}  →  artifacts in {config.MODELS_DIR}, {config.RESULTS_DIR}')
    print('=' * 60)

    df = load_data()[0]
    df = preprocess(df)
    X, y, feature_names, seq_payload = engineer_features(df)

    if not args.skip_eda:
        from eda import run_eda
        run_eda(df)

    if not args.skip_ml:
        from ml_models import train_all_ml_models
        train_all_ml_models(X, y, feature_names, df)

    if not args.skip_dl:
        from dl_models import train_all_dl_models
        train_all_dl_models(seq_payload, df)

    ablation_df = None
    if not args.skip_ablation:
        from ablation import run_ablation_study
        ablation_df = run_ablation_study(df)

    # Run SHAP first so the final_summary.txt can include the top features.
    if not args.skip_shap:
        from explainer import run_shap_analysis
        run_shap_analysis(X, feature_names)

    from evaluator import generate_final_comparison
    generate_final_comparison(ablation=ablation_df)

    elapsed = time.time() - start
    print('\n' + '=' * 60)
    print(f'  PIPELINE COMPLETE in {elapsed / 60:.1f} minutes')
    print('  Results saved to: outputs/')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--real', action='store_true',
                        help='Train on the real collected dataset (data/collected/) and write '
                             'artifacts to outputs/*_real/. Without this flag the synthetic '
                             'pipeline runs and writes to outputs/* (unchanged).')
    parser.add_argument('--skip-eda', action='store_true')
    parser.add_argument('--skip-ml', action='store_true')
    parser.add_argument('--skip-dl', action='store_true')
    parser.add_argument('--skip-ablation', action='store_true')
    parser.add_argument('--skip-shap', action='store_true')
    main(parser.parse_args())

"""Shared fixtures. Every test runs against the real-data variant.

The pipeline modules use bare cross-imports (`from config import ...`) rather than a package,
so `src` has to be on sys.path before anything is imported. DATA_VARIANT must also be set
before `config` is first imported, because it decides which output directories the module
constants point at.
"""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

os.environ.setdefault('DATA_VARIANT', 'real')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
os.chdir(ROOT)          # the pipeline reads data/ and outputs/ by relative path


def _require(path):
    if not os.path.exists(path):
        pytest.skip(f'requires {path}; run the pipeline first')
    return path


@pytest.fixture(scope='session')
def repo_root():
    return ROOT


@pytest.fixture(scope='session')
def panel():
    """The 28-row district-year panel the models are trained on."""
    import pandas as pd
    from config import PROCESSED_DIR
    return pd.read_csv(_require(os.path.join(PROCESSED_DIR, 'integrated_dataset.csv')))


@pytest.fixture(scope='session')
def collected():
    """The monthly source file, including its `source` provenance column."""
    import pandas as pd
    from config import COLLECTED_FILE
    return pd.read_csv(_require(COLLECTED_FILE))


@pytest.fixture(scope='session')
def comparison():
    import pandas as pd
    from config import RESULTS_DIR
    return pd.read_csv(_require(os.path.join(RESULTS_DIR, 'model_comparison.csv')))


@pytest.fixture(scope='session')
def loaded_api():
    """The API module with its model state loaded, exactly as the server would have it."""
    import api
    if api._state.get('model') is None:
        api._load_state()
    return api

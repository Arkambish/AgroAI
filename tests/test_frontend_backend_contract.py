"""The dashboard hardcodes a copy of the backend's feature list. Keep them in step.

dashboard/lib/features.ts says its "Order and names mirror src/config.py ALL_FEATURES
exactly". Nothing enforced that. If a feature is renamed or added on either side the two
drift apart silently: the form collects a field the model never sees, or stops collecting one
it needs, and the API quietly substitutes a district mean instead.
"""

import os
import re

import pytest

DASHBOARD = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard')
FEATURES_TS = os.path.join(DASHBOARD, 'lib', 'features.ts')


def _names_declared_in_features_ts():
    if not os.path.exists(FEATURES_TS):
        pytest.skip('dashboard/lib/features.ts not present')
    with open(FEATURES_TS, encoding='utf-8') as fh:
        source = fh.read()
    # Entries look like: { name: "season_avg_temp", label: ..., ... }
    return re.findall(r'\bname:\s*"([a-zA-Z0-9_]+)"', source)


def test_dashboard_declares_every_backend_feature():
    from config import ALL_FEATURES
    declared = _names_declared_in_features_ts()
    missing = [f for f in ALL_FEATURES if f not in declared]
    assert not missing, (
        f'the dashboard does not declare {len(missing)} backend feature(s): {missing}'
    )


def test_dashboard_declares_no_features_the_backend_does_not_have():
    from config import ALL_FEATURES
    declared = _names_declared_in_features_ts()
    extra = [f for f in declared if f not in ALL_FEATURES]
    assert not extra, (
        f'the dashboard declares {len(extra)} feature(s) the model has no slot for: {extra}'
    )


def test_feature_names_are_declared_in_the_same_order():
    """Order is documented as mirroring the backend. Drift here is a latent trap for any
    future code that zips the two lists positionally."""
    from config import ALL_FEATURES
    declared = [f for f in _names_declared_in_features_ts() if f in set(ALL_FEATURES)]
    assert declared == list(ALL_FEATURES), (
        'feature order differs between src/config.py and dashboard/lib/features.ts'
    )


def test_every_locale_defines_the_same_message_keys():
    """A key present in en.json but missing from si/ta renders as a raw key string to the
    user in that language."""
    import json

    messages = os.path.join(DASHBOARD, 'messages')
    if not os.path.isdir(messages):
        pytest.skip('no messages directory')

    def flatten(node, prefix=''):
        out = set()
        for key, value in node.items():
            path = f'{prefix}{key}'
            if isinstance(value, dict):
                out |= flatten(value, f'{path}.')
            else:
                out.add(path)
        return out

    catalogues = {}
    for name in sorted(os.listdir(messages)):
        if name.endswith('.json'):
            with open(os.path.join(messages, name), encoding='utf-8') as fh:
                catalogues[name] = flatten(json.load(fh))

    assert 'en.json' in catalogues
    reference = catalogues['en.json']
    for name, keys in catalogues.items():
        if name == 'en.json':
            continue
        missing = sorted(reference - keys)
        assert not missing, f'{name} is missing {len(missing)} key(s), e.g. {missing[:5]}'

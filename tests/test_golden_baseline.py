""" """
import json
import os
import sys

import numpy as np

try:
    from tests.golden.capture_baseline import ARRAYS_PATH, META_PATH, compute_outputs
except ImportError:
    # Fallback for environments where "tests" isn't importable as a package
    # (this repo has no tests/__init__.py, only tests/golden/__init__.py).
    _GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
    if _GOLDEN_DIR not in sys.path:
        sys.path.insert(0, _GOLDEN_DIR)
    from capture_baseline import ARRAYS_PATH, META_PATH, compute_outputs

_BASELINE_ARRAYS = np.load(ARRAYS_PATH)
with open(META_PATH) as _f:
    _BASELINE_META = json.load(_f)

_CURRENT_ARRAYS, _CURRENT_META = compute_outputs()


def test_text_signals_match_golden_baseline():
    for name in ("a", "b", "c"):
        for signal in ("novelty", "transience", "resonance"):
            key = f"{name}_{signal}"
            assert np.allclose(
                _CURRENT_ARRAYS[key], _BASELINE_ARRAYS[key], rtol=1e-5, atol=1e-8
            ), f"{key} has drifted from the golden baseline"


def test_multiscale_structure_matches_golden_baseline():
    for name in ("a", "b", "c"):
        for signal in ("ssm", "scalogram", "novelty"):
            key = f"multiscale_{name}_{signal}"
            assert np.allclose(
                _CURRENT_ARRAYS[key], _BASELINE_ARRAYS[key], rtol=1e-5, atol=1e-8
            ), f"{key} has drifted from the golden baseline"

        current_descriptors = _CURRENT_META["fixtures"][name]["descriptors"]
        baseline_descriptors = _BASELINE_META["fixtures"][name]["descriptors"]
        for descriptor_key, baseline_value in baseline_descriptors.items():
            assert np.allclose(
                current_descriptors[descriptor_key], baseline_value, rtol=1e-5, atol=1e-8
            ), f"descriptor {descriptor_key!r} for fixture {name!r} has drifted"


def test_pure_numeric_estimators_match_golden_baseline():
    for key in (
        "numeric_wrd_N_hat",
        "numeric_wrd_T_hat",
        "numeric_wrd_R_hat",
        "numeric_scalogram_matrix",
        "numeric_foote_novelty",
        "numeric_foote_ssm",
    ):
        assert np.allclose(
            _CURRENT_ARRAYS[key], _BASELINE_ARRAYS[key], rtol=1e-5, atol=1e-8
        ), f"{key} has drifted from the golden baseline"

    current_descriptors = _CURRENT_META["numeric"]["descriptors"]
    baseline_descriptors = _BASELINE_META["numeric"]["descriptors"]
    for descriptor_key, baseline_value in baseline_descriptors.items():
        assert np.allclose(
            current_descriptors[descriptor_key], baseline_value, rtol=1e-5, atol=1e-8
        ), f"numeric descriptor {descriptor_key!r} has drifted"


def test_cluster_labels_and_barycenters_match_golden_baseline():
    assert np.array_equal(_CURRENT_ARRAYS["cluster_labels"], _BASELINE_ARRAYS["cluster_labels"])

    baseline_label_keys = _BASELINE_META["cluster"]["label_keys"]
    for label in baseline_label_keys:
        key = f"cluster_barycenter_{label}"
        assert np.allclose(
            _CURRENT_ARRAYS[key], _BASELINE_ARRAYS[key], rtol=1e-5, atol=1e-8
        ), f"{key} has drifted from the golden baseline"

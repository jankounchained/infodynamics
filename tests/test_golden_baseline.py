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

# ORIGINAL tight band (float64-grade). The encoder-independent, seeded-rng
# WindowedRollingDistance/Scalogram/FooteNovelty arrays and the DTW cluster
# barycenters compute entirely in float64, so cross-platform BLAS reordering
# perturbs them only at ~1e-15 — keep this band tight.
_NUMERIC_RTOL = 1e-5
_NUMERIC_ATOL = 1e-8

# Looser float32 band for transformer-derived signals. sentence-transformers
# returns float32 embeddings, and the SSMs, scalograms, resonance/novelty/
# transience signals, and SSM-derived descriptors all inherit float32.
# atol=1e-6 is ~6x the empirically observed cross-platform float32 noise
# floor (1.6e-7, see .planning/debug/golden-baseline-ci-drift.md) and ~8x
# float32 machine epsilon, while still 4+ orders of magnitude tighter than
# any plausible algorithm regression.
_TRANSFORMER_RTOL = 1e-5
_TRANSFORMER_ATOL = 1e-6


def test_text_signals_match_golden_baseline():
    for name in ("a", "b", "c"):
        for signal in ("novelty", "transience", "resonance"):
            key = f"{name}_{signal}"
            assert np.allclose(
                _CURRENT_ARRAYS[key],
                _BASELINE_ARRAYS[key],
                rtol=_TRANSFORMER_RTOL,
                atol=_TRANSFORMER_ATOL,
            ), f"{key} has drifted from the golden baseline"


def test_multiscale_structure_matches_golden_baseline():
    for name in ("a", "b", "c"):
        for signal in ("ssm", "scalogram", "novelty"):
            key = f"multiscale_{name}_{signal}"
            assert np.allclose(
                _CURRENT_ARRAYS[key],
                _BASELINE_ARRAYS[key],
                rtol=_TRANSFORMER_RTOL,
                atol=_TRANSFORMER_ATOL,
            ), f"{key} has drifted from the golden baseline"

        current_descriptors = _CURRENT_META["fixtures"][name]["descriptors"]
        baseline_descriptors = _BASELINE_META["fixtures"][name]["descriptors"]
        for descriptor_key, baseline_value in baseline_descriptors.items():
            assert np.allclose(
                current_descriptors[descriptor_key],
                baseline_value,
                rtol=_TRANSFORMER_RTOL,
                atol=_TRANSFORMER_ATOL,
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
            _CURRENT_ARRAYS[key], _BASELINE_ARRAYS[key], rtol=_NUMERIC_RTOL, atol=_NUMERIC_ATOL
        ), f"{key} has drifted from the golden baseline"

    current_descriptors = _CURRENT_META["numeric"]["descriptors"]
    baseline_descriptors = _BASELINE_META["numeric"]["descriptors"]
    for descriptor_key, baseline_value in baseline_descriptors.items():
        assert np.allclose(
            current_descriptors[descriptor_key],
            baseline_value,
            rtol=_NUMERIC_RTOL,
            atol=_NUMERIC_ATOL,
        ), f"numeric descriptor {descriptor_key!r} has drifted"


def test_cluster_labels_and_barycenters_match_golden_baseline():
    assert np.array_equal(_CURRENT_ARRAYS["cluster_labels"], _BASELINE_ARRAYS["cluster_labels"])

    baseline_label_keys = _BASELINE_META["cluster"]["label_keys"]
    for label in baseline_label_keys:
        key = f"cluster_barycenter_{label}"
        assert np.allclose(
            _CURRENT_ARRAYS[key], _BASELINE_ARRAYS[key], rtol=_NUMERIC_RTOL, atol=_NUMERIC_ATOL
        ), f"{key} has drifted from the golden baseline"


def test_golden_baseline_tolerance_policy():
    # Pins the two-band tolerance policy so a future edit cannot silently
    # re-tighten the transformer tolerance back to a float64 grade (which
    # would reintroduce the cross-platform CI failure this plan closes) or
    # loosen it into meaninglessness.
    assert _TRANSFORMER_ATOL > _NUMERIC_ATOL
    assert _TRANSFORMER_ATOL >= 1.6e-7

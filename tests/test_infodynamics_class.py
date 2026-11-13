"""
"""
import pytest
import numpy as np
from hypothesis import given, strategies as st

from infodynamics.metrics import js_dist
from infodynamics import WindowedRollingDistance


def test_calc_signal_data_shapes():
    """shape same as input"""

    X = np.vstack(
        [
            np.random.uniform(0, 1, size=100),
            np.random.uniform(0, 1, size=100),
            np.random.uniform(0, 1, size=100),
            np.random.uniform(0, 1, size=100),
            np.random.uniform(0, 1, size=100),
        ]
    )

    i0 = WindowedRollingDistance(measure=js_dist, window_size=0)
    i0.fit(X)

    i1 = WindowedRollingDistance(measure=js_dist, window_size=1)
    i1.fit(X)

    i2 = WindowedRollingDistance(measure=js_dist, window_size=2)
    i2.fit(X)

    input_shape = X.shape[0]
    output_shapes = [
        i0.signal_["N_hat"].shape[0],
        i1.signal_["N_hat"].shape[0],
        i2.signal_["N_hat"].shape[0],
    ]

    assert np.allclose(input_shape, output_shapes)


def test_transience_calculation():
    """
    does it work with varying windows (incl. w=0)?
    """
    rng = np.random.default_rng(42)
    X = rng.standard_normal(size=(30, 6))

    for window_size in (0, 1, 2, 3):
        i = WindowedRollingDistance(measure="cosine", window_size=window_size)
        i.fit(X)

        assert i.signal_["T_hat"].shape == (30,)
        assert not np.isnan(i.signal_["T_hat"]).any()


def test_negative_values_in_input_data():
    """distances against arbitrary-magnitude real vectors (incl. negatives)
    must stay finite, not NaN/Inf."""
    rng = np.random.default_rng(7)
    X = rng.standard_normal(size=(25, 6))

    i = WindowedRollingDistance(measure="cosine", window_size=3)
    i.fit(X)

    for key in ("N_hat", "T_hat", "R_hat"):
        signal = i.signal_[key]
        assert signal.shape == (25,)
        assert np.isfinite(signal).all()


def test_very_small_numbers():
    """numerical stability at the denormal edge: very small magnitudes
    must not produce NaN/Inf output."""
    rng = np.random.default_rng(7)
    X = rng.standard_normal(size=(25, 6)) * 1e-300

    i = WindowedRollingDistance(measure="cosine", window_size=3)
    i.fit(X)

    for key in ("N_hat", "T_hat", "R_hat"):
        signal = i.signal_[key]
        assert signal.shape == (25,)
        assert np.isfinite(signal).all()


def test_validate_input_list_of_lists():
    """ """
    a = [[0.5, 0.5], [0.5, 0.5]]
    i = WindowedRollingDistance(measure=js_dist, window_size=1)
    X = i._as_array(a)

    assert isinstance(X, np.ndarray)
    assert X.shape == (2, 2)


@pytest.mark.slow
@given(
    st.lists(
        st.lists(
            st.floats(allow_nan=False, allow_infinity=False), min_size=2, max_size=2
        ),
        min_size=1,
    )
)
def test_validate_data_hypothesis(input_list):
    i = WindowedRollingDistance(measure=js_dist, window_size=1)
    X = i._as_array(input_list)

    assert isinstance(X, np.ndarray)
    assert X.shape == (len(input_list), len(input_list[0]))

    # Check that the values in the original list and the resulting ndarray are the same
    for original_list, array_row in zip(input_list, X):
        assert all(
            np.isclose(original_value, array_value)
            for original_value, array_value in zip(original_list, array_row)
        )


@pytest.mark.slow
@given(
    st.data(),
    st.integers(min_value=0, max_value=100),  # Generate a random window_size
)
def test_window_size(data, window_size):
    X = data.draw(
        st.lists(
            st.floats(
                min_value=0.01, max_value=1
            ),  # positive values: js_dist compares distributions
            min_size=100,
            max_size=100,
        )
    )

    X = np.array(X)
    iw = WindowedRollingDistance(measure=js_dist, window_size=window_size)
    Xw = iw.fit_transform(X)

    # Actual output shape: fit_transform returns the stacked
    # (n_samples, 3) novelty/transience/resonance array; N_hat is
    # always shape (n_samples,) regardless of window_size.
    assert Xw.shape == (len(X), 3)
    assert iw.signal_["N_hat"].shape == (len(X),)

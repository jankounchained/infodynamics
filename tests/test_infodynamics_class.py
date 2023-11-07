"""
"""
import pytest
import numpy as np
from hypothesis import given, strategies as st

from infodynamics.metrics import _rel_entr, kl_div, js_div, js_dist, cos_sim
from infodynamics.main import InfoDynamics


def test_calc_signal_data_shapes():
    """shape same as input"""

    X = np.vstack(
        [
            np.random.uniform(0, 1, size=100),
            np.random.normal(0, 1, size=100),
            np.random.normal(0, 1, size=100),
            np.random.normal(0, 1, size=100),
            np.random.normal(0, 1, size=100),
        ]
    )

    i0 = InfoDynamics(measure=js_dist, window_size=0)
    X0 = i0.fit_transform(X)

    i1 = InfoDynamics(measure=js_dist, window_size=1)
    X1 = i1.fit_transform(X)

    i2 = InfoDynamics(measure=js_dist, window_size=2)
    X2 = i2.fit_transform(X)

    input_shape = X.shape[0]
    output_shapes = [
        X0["N_hat"].shape[0],
        X1["N_hat"].shape[0],
        X2["N_hat"].shape[0],
    ]

    assert np.allclose(input_shape, output_shapes)


def test_transience_calculation():
    """
    does it work with varying windows (incl. w=0)?
    """
    pass


def test_validate_input_list_of_lists():
    """ """
    a = [[0.5, 0.5], [0.5, 0.5]]
    i = InfoDynamics(measure=js_dist, window_size=1)
    X = i._validate_data(a)

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
    i = InfoDynamics(measure=js_dist, window_size=1)
    X = i._validate_data(input_list)

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
                min_value=0, max_value=1
            ),  # Generate a random array of input data
            min_size=100,
            max_size=100,
        )
    )

    X = np.array(X)
    iw = InfoDynamics(measure=js_dist, window_size=window_size)
    Xw = iw.fit_transform(X)

    # Add your assertions here, e.g., check the shape of Xw
    assert Xw["N_hat"].shape == (len(X) - window_size + 1, window_size)

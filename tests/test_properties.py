"""
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st

from infodynamics.metrics_entropic import _rel_entr, kl_div, js_div, js_dist
from infodynamics.main import InfoDynamics


@given(
    st.data(),
    st.integers(min_value=0, max_value=100),  # Generate a random window_size
)
def test_window_size(data, window_size):
    X = data.draw(
        st.lists(
            st.floats(min_value=0, max_value=1),  # Generate a random array of input data
            min_size=100, max_size=100,
        )
    )

    X = np.array(X)
    iw = InfoDynamics(measure=js_dist, window_size=window_size)
    Xw = iw.fit_transform(X)

    # Add your assertions here, e.g., check the shape of Xw
    assert Xw['N_hat'].shape == (len(X) - window_size + 1, window_size)
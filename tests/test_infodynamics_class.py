"""
"""


import pytest
import numpy as np

from infodynamics.metrics_entropic import _rel_entr, kl_div, js_div, js_dist
from infodynamics.main import InfoDynamics


def test_InfoDynamics_fit_transform():
    # Test the fit_transform method of the InfoDynamics class with some sample data
    X = np.random.rand(100)
    iw = InfoDynamics(measure=js_dist, window_size=10)
    Xw = iw.fit_transform(X)
    assert Xw['N_hat'].shape == (len(X) - 10 + 1, 10)


def test_calc_signal_data_shapes():
    """shape same as input
    """

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
        X0["N_hat"].shape[0], X1["N_hat"].shape[0], X2["N_hat"].shape[0],
        ]

    assert np.allclose(input_shape, output_shapes)


def test_transience_calculation():
    """
    does it work with varying windows (incl. w=0)?
    """
    pass
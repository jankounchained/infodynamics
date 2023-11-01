"""
test
- negative values in input data
- window size > input data length
- non-probability distribution passed into novelty !!!
- edge case, very small numbers: https://github.com/scipy/scipy/issues/19436
- output signal same length as input data
"""

import pytest
import numpy as np

from metrics_entropic import _rel_entr, kl_div, js_div, js_dist
from main import InfoDynamics


def test_relative_entropy_single_comparison():
    """
    compare two prob dists
    """
    p = np.array([0.8, 0.2, 0.0])
    q = np.array([0.5, 0.5, 0.0])

    res_rel_entr = _rel_entr(p, q)
    res_kl_div = kl_div(p, q)
    res_js_div = js_div(p, q)
    res_js_dist = js_dist(p, q)

    assert np.allclose(res_rel_entr, np.array([0.54245752, -0.26438562, 0.0]))
    assert res_kl_div == pytest.approx(0.2780719051126376)
    assert res_js_div == pytest.approx(0.07310400793180975)
    assert res_js_dist == pytest.approx(0.27037752852596636)


def test_relative_entropy_directionality():
    """
    JS is symmetric, KL is asymmetric, i.e. KLD(P|Q) != KLD(Q|P)
    """
    p = np.array([0.8, 0.2, 0.0])
    q = np.array([0.5, 0.5, 0.0])

    res_kl_div_0 = kl_div(p, q)
    res_kl_div_1 = kl_div(q, p)
    res_js_div_0 = js_div(p, q)
    res_js_div_1 = js_div(q, p)

    assert res_kl_div_0 != res_kl_div_1
    assert res_js_div_0 == res_js_div_1


def test_relative_entropy_multiple_comparisons():
    """
    test vectorized versions of entropy functions
    """
    p = np.array([0.8, 0.2, 0.0])
    q = np.array([[0.5, 0.5, 0.0], [0.3, 0.7, 0.0]])

    res_rel_entr = _rel_entr(p, q)
    res_kl_div = kl_div(p, q)
    res_js_div = js_div(p, q)
    res_js_dist = js_dist(p, q)

    assert np.allclose(
        res_rel_entr,
        np.array([[0.54245752, -0.26438562, 0.0], [1.13203, -0.36147098, 0.0]]),
    )
    assert np.allclose(res_kl_div, np.array([0.27807191, 0.77055902]))
    assert np.allclose(res_js_div, np.array([0.07310401, 0.19116496]))
    assert np.allclose(res_js_dist, np.array([0.27037753, 0.43722415]))


def test_novelty_calculation():
    """
    does it work with varying windows (incl. w=0)?
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
    output_shapes = [X0["N_hat"].shape[0], X1["N_hat"].shape[0], X2["N_hat"].shape[0]]

    assert np.allclose(input_shape, output_shapes)


def test_transience_calculation():
    pass


def test_negative_values_in_input_data():
    pass


def test_window_size_larger_than_input_data():
    pass


def test_very_small_numbers():
    pass

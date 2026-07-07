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
from numpy.linalg import norm

from infodynamics.metrics import _rel_entr, kl_div, js_div, js_dist, cos_sim, cos_dist, DISTANCES
from infodynamics import WindowedRollingDistance


def test_rel_entr():
    # Test the _rel_entr function with some sample data
    p = np.array([0.1, 0.2, 0.7])
    q = np.array([0.2, 0.3, 0.5])
    result = _rel_entr(p, q).sum()
    expected_result = np.sum(p * np.log2(p / q))
    assert np.isclose(result, expected_result)


def test_kl_div():
    # Test the kl_div function with some sample data
    p = np.array([0.1, 0.2, 0.7])
    q = np.array([0.2, 0.3, 0.5])
    result = kl_div(p, q)
    expected_result = np.sum(_rel_entr(p, q))
    assert np.isclose(result, expected_result)


def test_js_div():
    # Test the js_div function with some sample data
    p = np.array([0.1, 0.2, 0.7])
    q = np.array([0.2, 0.3, 0.5])
    result = js_div(p, q)
    m = 0.5 * (p + q)
    expected_result = 0.5 * (kl_div(p, m) + kl_div(q, m))
    assert np.isclose(result, expected_result)


def test_js_dist():
    # Test the js_dist function with some sample data
    p = np.array([0.1, 0.2, 0.7])
    q = np.array([0.2, 0.3, 0.5])
    result = js_dist(p, q)
    expected_result = np.sqrt(js_div(p, q))
    assert np.isclose(result, expected_result)


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


def test_negative_values_in_input_data():
    pass


def test_very_small_numbers():
    pass


def test_cossim_single_comparison():
    p = np.array([0.5, 0.2, 0.7])
    q = np.array([0.2, 0.1, 0.5])

    res_cos_sim = cos_sim(p, q)
    expected_result = np.dot(p, q) / (norm(p) * norm(q))

    assert np.isclose(res_cos_sim, expected_result)


def test_cossim_multiple_comparisons():
    p = np.array([0.5, 0.2, 0.7])
    q = np.array([[0.2, 0.1, 0.5], [0.1, 0.8, 0.7], [0.4, 0.6, 0.2]])

    res_cos_sim = cos_sim(p, q)

    expected_result = []
    for qi in q:
        row_cos_sim = np.dot(p, qi) / (norm(p) * norm(qi))
        expected_result.append(row_cos_sim)

    assert np.allclose(res_cos_sim, np.array(expected_result))


def test_cos_dist_is_one_minus_cos_sim():
    p = np.array([0.5, 0.2, 0.7])
    q = np.array([0.2, 0.1, 0.5])

    assert np.isclose(cos_dist(p, q), 1.0 - cos_sim(p, q))


def test_cos_dist_identical_vectors_is_zero():
    p = np.array([0.5, 0.2, 0.7])

    assert np.isclose(cos_dist(p, p), 0.0)


def test_distances_cosine_key_is_a_distance_not_a_similarity():
    """'cosine' must resolve to a distance (higher = more dissimilar), since
    WindowedRollingDistance/InfoDynamics default to it for novelty/transience."""
    assert DISTANCES["cosine"] is cos_dist
    assert DISTANCES["cosine_similarity"] is cos_sim

""" """
import numpy as np
import pytest

tslearn = pytest.importorskip("tslearn")

from infodynamics.clustering import SignalClusterer, barycenter_average, pairwise_distance


def _make_series():
    x = np.linspace(0, 4 * np.pi, 50)
    # two groups of similar shapes, offset in phase/length, plus noise
    rng = np.random.default_rng(0)
    group_a = [np.sin(x) + rng.normal(scale=0.05, size=x.shape) for _ in range(4)]
    group_b = [np.sin(x[:40] + np.pi) + rng.normal(scale=0.05, size=40) for _ in range(4)]
    return group_a + group_b


def test_pairwise_distance_shape_and_symmetry():
    series = _make_series()
    distance_matrix = pairwise_distance(series)

    n = len(series)
    assert distance_matrix.shape == (n, n)
    assert np.allclose(distance_matrix, distance_matrix.T)
    assert np.allclose(np.diag(distance_matrix), 0.0, atol=1e-8)


def test_barycenter_average_dba_and_soft_dtw():
    series = _make_series()[:4]

    dba = barycenter_average(series, method="dba")
    soft = barycenter_average(series, method="soft_dtw")

    assert dba.ndim == 1
    assert soft.ndim == 1


def test_barycenter_average_invalid_method_raises():
    with pytest.raises(ValueError):
        barycenter_average(_make_series()[:2], method="not-a-method")


def test_signal_clusterer_fit_with_explicit_k():
    series = _make_series()
    clusterer = SignalClusterer(n_clusters=2).fit(series)

    assert clusterer.labels_.shape == (len(series),)
    assert clusterer.n_clusters_ == 2
    assert set(clusterer.barycenters_.keys()) == set(clusterer.labels_.tolist())


def test_signal_clusterer_selects_k_via_silhouette():
    series = _make_series()
    clusterer = SignalClusterer(k_range=range(2, 4)).fit(series)

    assert clusterer.n_clusters_ in (2, 3)


def test_signal_clusterer_recovers_the_two_groups():
    series = _make_series()
    clusterer = SignalClusterer(n_clusters=2).fit(series)

    labels = clusterer.labels_
    # first half and second half of `series` were built from two distinct shapes
    assert len(set(labels[:4])) == 1
    assert len(set(labels[4:])) == 1
    assert labels[0] != labels[4]

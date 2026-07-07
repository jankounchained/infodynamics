""" """
import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

tslearn = pytest.importorskip("tslearn")

from infodynamics import viz
from infodynamics.clustering import SignalClusterer


def _make_series():
    x = np.linspace(0, 4 * np.pi, 50)
    rng = np.random.default_rng(0)
    group_a = [np.sin(x) + rng.normal(scale=0.05, size=x.shape) for _ in range(3)]
    group_b = [np.sin(x + np.pi) + rng.normal(scale=0.05, size=x.shape) for _ in range(3)]
    return group_a + group_b


def test_plot_overlay_runs():
    ax = viz.plot_overlay({"a": np.array([0.1, 0.2, 0.3]), "b": np.array([0.3, 0.2, 0.1, 0.0])})
    assert len(ax.lines) == 2


def test_plot_side_by_side_runs():
    fig = viz.plot_side_by_side({"a": np.array([0.1, 0.2, 0.3]), "b": np.array([0.3, 0.2])})
    assert len(fig.axes) == 2


def test_plot_dendrogram_and_archetypes_and_projection_run():
    series = _make_series()
    clusterer = SignalClusterer(n_clusters=2).fit(series)

    ax = viz.plot_dendrogram(clusterer)
    assert ax is not None

    fig = viz.plot_cluster_archetypes(clusterer, series)
    assert len(fig.axes) == clusterer.n_clusters_

    ax = viz.plot_projection(clusterer, method="pca")
    assert ax is not None

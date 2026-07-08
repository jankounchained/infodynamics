"""
Visualization utilities for information dynamics signals.
"""
from typing import Dict, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from infodynamics.util import znorm_rows


def plot_overlay(
    signals: Dict[str, np.ndarray],
    relative_x: bool = True,
    ax: Optional[Axes] = None,
    **kwargs,
) -> Axes:
    """Overlays one or more named signals on a single set of axes.

    Parameters
    ----------
    signals : dict[str, np.ndarray]
        mapping of a display name (e.g. document title) to its signal.

    relative_x : bool, default=True
        plot against relative position (0-1) rather than raw chunk index,
        so that signals of different lengths remain comparable.
    """
    if ax is None:
        _, ax = plt.subplots()

    for name, signal in signals.items():
        x = np.linspace(0, 1, len(signal)) if relative_x else np.arange(len(signal))
        ax.plot(x, signal, label=name, **kwargs)

    ax.set_xlabel("relative position" if relative_x else "chunk index")
    ax.legend()
    return ax


def plot_side_by_side(signals: Dict[str, np.ndarray], **kwargs) -> Figure:
    """Plots each named signal in its own subplot, arranged horizontally.

    Parameters
    ----------
    signals : dict[str, np.ndarray]
        mapping of a display name (e.g. document title) to its signal.
    """
    fig, axes = plt.subplots(1, len(signals), sharey=True, figsize=(5 * len(signals), 4))
    if len(signals) == 1:
        axes = [axes]

    for ax, (name, signal) in zip(axes, signals.items()):
        ax.plot(np.arange(len(signal)), signal, **kwargs)
        ax.set_title(name)
        ax.set_xlabel("chunk index")

    fig.tight_layout()
    return fig


def plot_dendrogram(clusterer, ax: Optional[Axes] = None, **kwargs) -> Axes:
    """Plots the agglomerative clustering dendrogram of a fitted SignalClusterer."""
    from scipy.cluster.hierarchy import dendrogram

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))

    model = clusterer.model_
    n_samples = len(model.labels_)
    counts = np.zeros(model.children_.shape[0])
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack([model.children_, model.distances_, counts]).astype(float)

    dendrogram(linkage_matrix, ax=ax, **kwargs)
    return ax


def plot_cluster_archetypes(clusterer, series: Sequence[np.ndarray], **kwargs) -> Figure:
    """Plots, per cluster, the individual signals (thin) and the DBA/soft-DTW archetype (bold).

    Parameters
    ----------
    clusterer : SignalClusterer
        a fitted clusterer.

    series : Sequence[np.ndarray]
        the same time series that were passed to 'clusterer.fit'.
    """
    labels = clusterer.labels_
    unique_labels = np.unique(labels)

    fig, axes = plt.subplots(
        1, len(unique_labels), figsize=(5 * len(unique_labels), 4), sharey=True
    )
    if len(unique_labels) == 1:
        axes = [axes]

    for ax, label in zip(axes, unique_labels):
        for s, l in zip(series, labels):
            if l == label:
                ax.plot(np.linspace(0, 1, len(s)), s, alpha=0.2, color="gray")

        barycenter = clusterer.barycenters_[label]
        ax.plot(np.linspace(0, 1, len(barycenter)), barycenter, linewidth=2, **kwargs)
        ax.set_title(f"Cluster {label}")

    fig.tight_layout()
    return fig


def plot_projection(clusterer, method: str = "pca", ax: Optional[Axes] = None, **kwargs) -> Axes:
    """Projects the pairwise DTW distance matrix to 2D and colors points by cluster label.

    Parameters
    ----------
    clusterer : SignalClusterer
        a fitted clusterer.

    method : {'pca', 'umap'}, default='pca'
        'umap' requires the optional 'umap-learn' dependency.
    """
    if ax is None:
        _, ax = plt.subplots()

    if method == "pca":
        from sklearn.decomposition import PCA

        projection = PCA(n_components=2).fit_transform(clusterer.distance_matrix_)
    elif method == "umap":
        try:
            from umap import UMAP
        except ImportError as e:
            raise ImportError(
                "The 'viz-projection' extra is required to use method='umap'. "
                "Install it with `pip install infodynamics[viz-projection]`."
            ) from e

        projection = UMAP(n_components=2, metric="precomputed").fit_transform(
            clusterer.distance_matrix_
        )
    else:
        raise ValueError(f"Invalid value for parameter 'method': {method}. Must be 'pca' or 'umap'.")

    scatter = ax.scatter(projection[:, 0], projection[:, 1], c=clusterer.labels_, **kwargs)
    ax.legend(*scatter.legend_elements(), title="cluster")
    return ax


def plot_ssm(S: np.ndarray, ax: Optional[Axes] = None, **kwargs) -> Axes:
    """Plots a self-similarity matrix as a heatmap.

    Parameters
    ----------
    S : np.ndarray of shape (n_chunks, n_chunks)
        self-similarity matrix, e.g. from infodynamics.scalogram.self_similarity_matrix.
    """
    if ax is None:
        _, ax = plt.subplots()

    kwargs.setdefault("cmap", "magma")
    kwargs.setdefault("origin", "upper")
    kwargs.setdefault("aspect", "auto")
    ax.imshow(S, **kwargs)
    ax.set_xlabel("chunk index")
    ax.set_ylabel("chunk index")
    return ax


def plot_scalogram(
    matrix: np.ndarray,
    scales: Sequence[int],
    ax: Optional[Axes] = None,
    znormalize: bool = True,
    **kwargs,
) -> Axes:
    """Plots a scalogram (window-size x chunk-index distance matrix) as a heatmap.

    Parameters
    ----------
    matrix : np.ndarray of shape (n_scales, n_chunks)
        scalogram matrix, e.g. from infodynamics.scalogram.Scalogram.

    scales : Sequence[int]
        window size for each row of 'matrix'.

    znormalize : bool, default=True
        z-normalize each row before plotting, so scales become visually comparable.
    """
    if ax is None:
        _, ax = plt.subplots()

    values = znorm_rows(matrix) if znormalize else matrix
    kwargs.setdefault("cmap", "viridis")
    kwargs.setdefault("origin", "lower")
    kwargs.setdefault("aspect", "auto")
    ax.imshow(values, extent=[0, matrix.shape[1], 0, len(scales)], **kwargs)
    ax.set_yticks(np.arange(len(scales)) + 0.5)
    ax.set_yticklabels(scales)
    ax.set_xlabel("chunk index")
    ax.set_ylabel("window size")
    return ax


def plot_multiscale_novelty(
    novelty: np.ndarray, radii: Sequence[int], ax: Optional[Axes] = None, **kwargs
) -> Axes:
    """Plots multi-scale Foote novelty, one line per kernel radius.

    Parameters
    ----------
    novelty : np.ndarray of shape (n_radii, n_chunks)
        novelty matrix, e.g. from infodynamics.scalogram.FooteNovelty.

    radii : Sequence[int]
        kernel radius for each row of 'novelty'.
    """
    if ax is None:
        _, ax = plt.subplots()

    for row, radius in zip(novelty, radii):
        ax.plot(row, label=f"r={radius}", **kwargs)

    ax.set_xlabel("chunk index")
    ax.set_ylabel("novelty")
    ax.legend(title="kernel radius")
    return ax

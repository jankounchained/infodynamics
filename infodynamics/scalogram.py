"""
Multi-scale text structure: a scalogram (windowed rolling distance across
many window sizes) and Foote novelty (a Gaussian-tapered checkerboard kernel
correlated down the diagonal of the self-similarity matrix at many radii).

Both stack a family of single-scale signals into a [n_scales x n_chunks]
matrix, giving a scale-space view of topic-shift dynamism that a single
WindowedRollingDistance window size can't show on its own.
"""
from typing import Callable, Optional, Sequence, Union

import numpy as np
from numpy.typing import ArrayLike
from sklearn.base import BaseEstimator, TransformerMixin
from typing_extensions import Self

from infodynamics.metrics import _resolve_measure, cos_sim


def rolling_gap_distance(
    embeddings: ArrayLike, window_size: int, measure: Union[str, Callable] = "cosine"
) -> np.ndarray:
    """Distance, at a single scale, between the mean embedding of the
    'window_size' chunks before and after each position. Positions where a
    full window doesn't fit (near the edges) are filled with the nearest
    valid value.

    Parameters
    ----------
    embeddings : np.ndarray of shape (n_chunks, n_features)

    window_size : int
        number of chunks pooled on each side of a position.

    measure : str or Callable, default='cosine'
        distance measure to compare the two pooled vectors with. See infodynamics.metrics.DISTANCES.

    Returns
    -------
    distance : np.ndarray of shape (n_chunks,)
    """
    measure = _resolve_measure(measure)
    embeddings = np.asarray(embeddings)
    n = embeddings.shape[0]

    distance = np.full(n, np.nan)
    for i in range(n):
        past = embeddings[max(0, i - window_size) : i]
        future = embeddings[i : min(n, i + window_size)]
        if past.shape[0] == 0 or future.shape[0] == 0:
            continue
        distance[i] = float(np.asarray(measure(past.mean(0), future.mean(0))).item())

    valid = np.where(~np.isnan(distance))[0]
    if len(valid):
        distance[: valid[0]] = distance[valid[0]]
        distance[valid[-1] + 1 :] = distance[valid[-1]]
    return distance


class Scalogram(BaseEstimator, TransformerMixin):
    """Stacks rolling_gap_distance across several window sizes ("scales")
    into a [n_scales x n_chunks] matrix: a scale-space view of how
    topic-shift dynamism changes with the size of the context window.
    """

    def __init__(self, scales: Sequence[int], measure: Union[str, Callable] = "cosine"):
        """

        Parameters
        ----------
        scales : Sequence[int]
            window sizes to compute rolling_gap_distance at. Scales that
            don't fit inside the input (scale >= n_chunks) are dropped.

        measure : str or Callable, default='cosine'
            distance measure passed to rolling_gap_distance. See infodynamics.metrics.DISTANCES.
        """
        self.scales = scales
        self.measure = measure

    def fit(self, embeddings: ArrayLike, y=None) -> Self:
        """Fit the scalogram to a sequence of chunk embeddings.

        Parameters
        ----------
        embeddings : np.ndarray of shape (n_chunks, n_features)

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            instance with the estimated scalogram matrix.
        """
        embeddings = np.asarray(embeddings)
        scales = [w for w in self.scales if w < embeddings.shape[0]]
        if not scales:
            raise ValueError(
                "No 'scales' fit inside the input: every scale must be < n_chunks "
                f"({embeddings.shape[0]})."
            )

        self.matrix_ = np.vstack(
            [rolling_gap_distance(embeddings, w, measure=self.measure) for w in scales]
        )
        self.scales_ = scales
        return self

    def transform(self, embeddings: ArrayLike, y=None) -> np.ndarray:
        """Recompute the scalogram matrix fresh from embeddings (no fit-time
        state is reused) and return the [n_scales x n_chunks] matrix."""
        self.fit(embeddings)
        return self.matrix_

    def fit_transform(self, embeddings: ArrayLike, y=None) -> np.ndarray:
        """Fit to embeddings, return the [n_scales x n_chunks] scalogram matrix."""
        self.fit(embeddings)
        return self.matrix_


def self_similarity_matrix(embeddings: ArrayLike) -> np.ndarray:
    """Cosine similarity matrix between every pair of chunk embeddings."""
    embeddings = np.asarray(embeddings)
    return cos_sim(embeddings, embeddings)


def checkerboard_kernel(radius: int, sigma: Optional[float] = None) -> np.ndarray:
    """Gaussian-tapered checkerboard kernel of shape (2*radius+1, 2*radius+1),
    positive on the top-left/bottom-right quadrants (self-similarity) and
    negative on the off-diagonal quadrants (cross-similarity), as in Foote (2000).

    Parameters
    ----------
    radius : int
        kernel radius (kernel width = 2 * radius + 1).

    sigma : float or None, default=None
        standard deviation of the Gaussian taper. Defaults to 'radius / 2'.
    """
    if sigma is None:
        sigma = radius / 2.0
    x = np.arange(-radius, radius + 1)
    X, Y = np.meshgrid(x, x)
    gaussian = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
    sign = np.sign(X) * np.sign(Y)
    return sign * gaussian


def foote_novelty(S: np.ndarray, radius: int) -> np.ndarray:
    """Slide a Gaussian checkerboard kernel of the given radius down the
    diagonal of a self-similarity matrix, at a single scale.

    Parameters
    ----------
    S : np.ndarray of shape (n_chunks, n_chunks)
        self-similarity matrix, e.g. from self_similarity_matrix().

    radius : int
        kernel radius (kernel width = 2 * radius + 1).

    Returns
    -------
    novelty : np.ndarray of shape (n_chunks,)
    """
    n = S.shape[0]
    kernel = checkerboard_kernel(radius)
    scale = np.abs(kernel).sum()
    padded = np.pad(S, radius, mode="edge")

    novelty = np.empty(n)
    for i in range(n):
        window = padded[i : i + 2 * radius + 1, i : i + 2 * radius + 1]
        novelty[i] = float((window * kernel).sum()) / scale
    novelty[novelty < 0] = 0.0  # novelty is positive by convention
    return novelty


class FooteNovelty(BaseEstimator, TransformerMixin):
    """Multi-scale structural novelty: correlates a Gaussian-tapered
    checkerboard kernel (Foote, 2000) down the diagonal of the
    self-similarity matrix at several kernel radii ("scales"), stacked into
    a [n_radii x n_chunks] matrix.
    """

    def __init__(self, radii: Sequence[int]):
        """

        Parameters
        ----------
        radii : Sequence[int]
            checkerboard kernel radii to compute novelty at. Radii that
            don't fit inside the input (2*radius+1 > n_chunks) are dropped.
        """
        self.radii = radii

    def fit(self, embeddings: ArrayLike, y=None) -> Self:
        """Fit multi-scale Foote novelty to a sequence of chunk embeddings.

        Parameters
        ----------
        embeddings : np.ndarray of shape (n_chunks, n_features)

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            instance with the estimated self-similarity matrix and novelty matrix.
        """
        embeddings = np.asarray(embeddings)
        S = self_similarity_matrix(embeddings)
        radii = [r for r in self.radii if 2 * r + 1 <= S.shape[0]]
        if not radii:
            raise ValueError(
                "No 'radii' fit inside the input: every radius must satisfy "
                f"2 * radius + 1 <= n_chunks ({S.shape[0]})."
            )

        self.ssm_ = S
        self.novelty_ = np.vstack([foote_novelty(S, r) for r in radii])
        self.radii_ = radii
        return self

    def transform(self, embeddings: ArrayLike, y=None) -> np.ndarray:
        """Recompute Foote novelty fresh from embeddings (no fit-time state
        is reused) and return the [n_radii x n_chunks] novelty matrix."""
        self.fit(embeddings)
        return self.novelty_

    def fit_transform(self, embeddings: ArrayLike, y=None) -> np.ndarray:
        """Fit to embeddings, return the [n_radii x n_chunks] novelty matrix."""
        self.fit(embeddings)
        return self.novelty_


def structure_descriptors(
    embeddings: ArrayLike, S: Optional[np.ndarray] = None, window_size: int = 5
) -> dict:
    """Cheap, interpretable per-document summary statistics of semantic
    structure: redundancy (how similar chunks are to each other overall)
    and dynamism (how much the local topic shifts at a small window size).

    Parameters
    ----------
    embeddings : np.ndarray of shape (n_chunks, n_features)

    S : np.ndarray of shape (n_chunks, n_chunks) or None, default=None
        self-similarity matrix. Computed from 'embeddings' if not given.

    window_size : int, default=5
        window size used for the dynamism descriptors.
    """
    embeddings = np.asarray(embeddings)
    if S is None:
        S = self_similarity_matrix(embeddings)

    off_diagonal = S[np.triu_indices_from(S, k=1)]
    gap = rolling_gap_distance(embeddings, window_size)
    return {
        "n_chunks": embeddings.shape[0],
        "mean_offdiag_sim": float(off_diagonal.mean()),  # redundancy proxy (higher=more)
        "p90_offdiag_sim": float(np.quantile(off_diagonal, 0.9)),
        f"dist_var_w{window_size}": float(np.nanvar(gap)),  # topic-shift dynamism
        f"dist_mean_w{window_size}": float(np.nanmean(gap)),
    }

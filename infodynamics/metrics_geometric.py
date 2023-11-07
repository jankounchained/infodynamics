"""
"""

from typing import Union
import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics.pairwise import cosine_similarity


def calc_vector_histogram(x: ArrayLike, bins: int = 256) -> np.ndarray:
    # calculate a histogram
    hist, bin_edges = np.histogram(x, bins=bins)
    # normalize histogram to sum to one
    hist_norm = hist / hist.sum()

    return hist_norm


def calc_vector_entropy(x: ArrayLike, bins: int = 256) -> float:
    hist_norm = calc_vector_histogram(x, bins=bins)
    # entropy with log2 + add a small constant to avoid log(0)
    H = -np.sum(hist_norm * np.log2(hist_norm + np.finfo(float).eps))

    return H


def cos_sim(x: ArrayLike, y: ArrayLike) -> Union[float, np.ndarray]:
    """Wrapper of sklearn's cosine_similarity that handles 1d arrays."""
    if x.ndim == 1:
        x = x.reshape(1, -1)
    if y.ndim == 1:
        y = y.reshape(1, -1)

    return cosine_similarity(x, y)

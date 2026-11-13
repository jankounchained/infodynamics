"""
Distance and divergence measures between observations, and the
``DISTANCES`` registry that estimators resolve a ``measure`` string against.
"""
from typing import Callable, Union

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def _rel_entr(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """
    Vectorized, element-wise relative entropy.
    """
    # add smallest possible float to avoid RunTime warnings
    # about zero division
    p = np.asarray(p) + np.finfo(float).eps
    q = np.asarray(q) + np.finfo(float).eps

    mask = (p > 0) & (q > 0)
    result = np.where(mask, p * np.log2(p / q), 0)
    return result


def kl_div(p: np.ndarray, q: np.ndarray) -> Union[float, np.ndarray]:
    """
    Kullback-Leibler divergence between two discrete distributions.

    Returns a float for 1-D inputs, or one value per row when either
    input is 2-D.
    """
    return _rel_entr(p, q).sum(axis=-1)


def js_div(p: np.ndarray, q: np.ndarray) -> Union[float, np.ndarray]:
    """
    Jensen-Shannon divergence between two discrete distributions.

    Inputs are normalised to sum to one. Returns a float for 1-D inputs,
    or one value per row when either input is 2-D.
    """
    p = p / np.sum(p, axis=-1, keepdims=True)
    q = q / np.sum(q, axis=-1, keepdims=True)
    m = (p + q) / 2.0
    return 0.5 * kl_div(p, m) + 0.5 * kl_div(q, m)


def js_dist(p: np.ndarray, q: np.ndarray) -> Union[float, np.ndarray]:
    """
    Jensen-Shannon *distance* (square root of the divergence) between two
    discrete distributions.
    """
    return np.sqrt(js_div(p, q))


def cos_sim(x: np.ndarray, y: np.ndarray) -> Union[float, np.ndarray]:
    """Wrapper of sklearn's cosine_similarity that handles 1d arrays."""
    if x.ndim == 1:
        x = x.reshape(1, -1)
    if y.ndim == 1:
        y = y.reshape(1, -1)

    return cosine_similarity(x, y)


def cos_dist(x: np.ndarray, y: np.ndarray) -> Union[float, np.ndarray]:
    """Cosine *distance* (1 - cosine similarity); higher means more dissimilar."""
    return 1.0 - cos_sim(x, y)


DISTANCES = {
    "kld": kl_div,
    "jsd": js_div,
    "jensenshannon": js_dist,
    "cosine": cos_dist,
    "cosine_similarity": cos_sim,
}


def _resolve_measure(measure: Union[str, Callable]) -> Callable:
    """Look up a measure by name in ``DISTANCES``, or pass a callable through."""
    if isinstance(measure, str) and measure in DISTANCES:
        return DISTANCES[measure]
    elif callable(measure):
        return measure
    else:
        raise ValueError(
            f"Invalid value for parameter 'measure': {measure!r}. "
            f"Use one of {sorted(DISTANCES)} or a callable."
        )

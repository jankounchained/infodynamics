"""
Distance and divergence measures between observations, and the
``DISTANCES`` registry that estimators resolve a ``measure`` string against.
"""
from typing import Callable, Union

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def _check_non_negative(*arrays: np.ndarray) -> None:
    """KL and Jensen-Shannon compare probability distributions, so negative
    entries are invalid input rather than something to compute around."""
    for x in arrays:
        if np.any(np.asarray(x) < 0):
            raise ValueError(
                "KL and Jensen-Shannon measures expect non-negative values "
                "(probability distributions). For embeddings or other "
                "real-valued vectors, use measure='cosine'."
            )


def _rel_entr(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """
    Vectorized, element-wise relative entropy of non-negative inputs.
    """
    # add the smallest possible float so that zero entries
    # don't divide by zero or take log2(0)
    p = np.asarray(p) + np.finfo(float).eps
    q = np.asarray(q) + np.finfo(float).eps
    return p * np.log2(p / q)


def kl_div(p: np.ndarray, q: np.ndarray) -> Union[float, np.ndarray]:
    """
    Kullback-Leibler divergence between two discrete distributions.

    Returns a float for 1-D inputs, or one value per row when either
    input is 2-D. Raises ValueError for negative entries.
    """
    _check_non_negative(p, q)
    return _rel_entr(p, q).sum(axis=-1)


def js_div(p: np.ndarray, q: np.ndarray) -> Union[float, np.ndarray]:
    """
    Jensen-Shannon divergence between two discrete distributions.

    Inputs are normalised to sum to one. Returns a float for 1-D inputs,
    or one value per row when either input is 2-D. Raises ValueError for
    negative entries or for a distribution that sums to zero.
    """
    _check_non_negative(p, q)
    if np.any(np.sum(p, axis=-1) == 0) or np.any(np.sum(q, axis=-1) == 0):
        raise ValueError(
            "Jensen-Shannon measures need distributions with a positive sum; "
            "got one that sums to zero."
        )
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

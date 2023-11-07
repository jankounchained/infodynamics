"""
"""
import numpy as np


def _rel_entr(p, q):
    """
    Vectorized, element-wise relative entropy.
    """
    # add smalles possible float to avoid RunTime warnings
    # about zero division
    p = np.asarray(p) + np.finfo(float).eps
    q = np.asarray(q) + np.finfo(float).eps

    mask = (p > 0) & (q > 0)
    result = np.where(mask, p * np.log2(p / q), 0)
    return result


def kl_div(p, q):
    """
    Kullback-Leibler Divergence between two discrete distributions.
    """
    return _rel_entr(p, q).sum(axis=-1)


def js_div(p, q):
    """
    Jensen-Shannon divergence between two discrete distributions.
    """
    p = p / np.sum(p, axis=-1, keepdims=True)
    q = q / np.sum(q, axis=-1, keepdims=True)
    m = (p + q) / 2.0
    return 0.5 * kl_div(p, m) + 0.5 * kl_div(q, m)


def js_dist(p, q):
    """
    Jesen-Shannon *distance* between two discrete distributions.
    """
    return np.sqrt(js_div(p, q))

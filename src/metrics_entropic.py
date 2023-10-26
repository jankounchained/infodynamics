"""
"""
import numpy as np

def _rel_entr(p, q):
    """
    Adapted from scipy.special.rel_entr
    """
    if np.isnan(p) or np.isnan(q):
        return np.nan
    elif p > 0 and q > 0:
        return p * np.log2(p / q)
    elif p == 0 and q >= 0:
        return 0
    else:
        return np.inf

def kl_div(p, q):
    _element_wise_kld = np.vectorize(_rel_entr)
    return _element_wise_kld(p, q).sum()

def js_div(p, q):
    p = p / np.sum(p, keepdims=True)
    q = q / np.sum(q, keepdims=True)
    m = (p + q) / 2.0
    return 0.5 * kl_div(p, m) + 0.5 * kl_div(q, m)

def js_dist(p, q):
    return np.sqrt(js_div(p, q))
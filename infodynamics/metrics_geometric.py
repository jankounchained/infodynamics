"""
"""

import numpy as np


def calc_vector_histogram(x, bins=256):
    # calculate a histogram
    hist, bin_edges = np.histogram(x, bins=bins)
    # normalize histogram to sum to one
    hist_norm = hist / hist.sum()

    return hist_norm


def calc_vector_entropy(x, bins=256):
    hist_norm = calc_vector_histogram(x, bins=bins)
    # entropy with log2 + add a small constant to avoid log(0)
    H = -np.sum(hist_norm * np.log2(hist_norm + np.finfo(float).eps))

    return H
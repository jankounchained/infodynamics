'''
Functions to clalculate relative entropy
'''
import numpy as np
from scipy.stats import entropy


def kld(p, q, base=2):
    """KL-divergence for two probability distributions"""
    p, q = np.asarray(p), np.asarray(q)

    return entropy(p, q, base=base)


def jsd(p, q, base=2):
    """Pairwise Jensen-Shannon Divergence for two probability distributions"""
    # convert to np.array
    p, q = np.asarray(p), np.asarray(q)
    # normalize p, q to probabilities
    p, q = p / p.sum(), q / q.sum()
    m = 1.0 / 2 * (p + q)
    return entropy(p, m, base=base) / 2.0 + entropy(q, m, base=base) / 2.0


def cosine_distance(p, q):
    """Cosine distance for two vectors"""

    p, q = np.asarray(p), np.asarray(q)

    dot_prod = np.dot(p, q)
    magnitude = np.sqrt(p.dot(p)) * np.sqrt(q.dot(q))
    cos_sim = dot_prod / magnitude
    cos_dist = 1 - cos_sim

    return cos_dist

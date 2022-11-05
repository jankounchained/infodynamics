'''
Functions to clalculate relative entropy
'''
import numpy as np
from scipy import stats


def kld(p, q):
    """KL-divergence for two probability distributions"""
    p = np.asarray(p, dtype=np.float)
    q = np.asarray(q, dtype=np.float)

    return np.sum(np.where(p != 0, (p - q) * np.log2(p / q), 0))


def jsd(p, q, base=2):
    """Pairwise Jensen-Shannon Divergence for two probability distributions"""
    # convert to np.array
    p, q = np.asarray(p), np.asarray(q)
    # normalize p, q to probabilities
    p, q = p / p.sum(), q / q.sum()
    m = 1.0 / 2 * (p + q)
    return stats.entropy(p, m, base=base) / 2.0 + stats.entropy(q, m, base=base) / 2.0


def cosine_distance(p, q):
    """Cosine distance for two vectors"""

    p, q = np.asarray(p), np.asarray(q)

    dot_prod = np.dot(p, q)
    magnitude = np.sqrt(p.dot(p)) * np.sqrt(q.dot(q))
    cos_sim = dot_prod / magnitude
    cos_dist = 1 - cos_sim

    return cos_dist

# def kld(p, q):
#     '''Kullback-Leibler Divergence'''
#     p = np.asarray(p, dtype=np.float64)
#     q = np.asarray(q, dtype=np.float64)

#     return np.sum(np.where(p != 0, (p - q) * np.log2(p / q), 0))

# def kl_divergence(p, q):
#     return sum(p[i] * np.log2(p[i]/q[i]) for i in range(len(p)))

# # %%
# px = np.random.normal(loc=60, scale=5, size=50)
# qx = np.random.beta(a=60, b=5, size=50)
# # %%
# from scipy.special import rel_entr
# # %%
# sum(rel_entr(px, qx))
# # %%
# kld(px, qx)
# # %%
# kl_divergence(px, qx)
# # %%

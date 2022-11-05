'''
Functions to clalculate relative entropy
'''
# %%
import numpy as np


def kld(p, q):
    '''Kullback-Leibler Divergence'''
    p = np.asarray(p, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)

    return np.sum(np.where(p != 0, (p - q) * np.log2(p / q), 0))

def kl_divergence(p, q):
    return sum(p[i] * np.log2(p[i]/q[i]) for i in range(len(p)))

# %%
px = np.random.normal(loc=60, scale=5, size=50)
qx = np.random.beta(a=60, b=5, size=50)
# %%
from scipy.special import rel_entr
# %%
sum(rel_entr(px, qx))
# %%
kld(px, qx)
# %%
kl_divergence(px, qx)
# %%

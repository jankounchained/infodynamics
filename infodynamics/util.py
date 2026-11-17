"""
Small array helpers shared by the plotting code.
"""

import numpy as np
from numpy.typing import ArrayLike


def znorm_rows(M: ArrayLike) -> np.ndarray:
    """Z-normalizes each row of a 2D array independently (mean 0, sd 1), so
    that rows on different scales (e.g. a scalogram's window sizes) become
    visually comparable."""
    M = np.asarray(M)
    mean = np.nanmean(M, axis=1, keepdims=True)
    sd = np.nanstd(M, axis=1, keepdims=True)
    sd[sd == 0] = 1.0
    return (M - mean) / sd

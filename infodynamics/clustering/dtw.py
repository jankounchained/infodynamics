"""
Pairwise Dynamic Time Warping (DTW) distance between time series signals.
"""
from typing import Sequence

import numpy as np


def pairwise_distance(series: Sequence[np.ndarray], z_normalize: bool = True) -> np.ndarray:
    """
    Computes a pairwise DTW distance matrix between (possibly differently
    lengthed) 1D time series, e.g. novelty/transience/resonance signals from
    different documents.

    Parameters
    ----------
    series : Sequence[np.ndarray]
        the time series to compare.

    z_normalize : bool, default=True
        z-normalize each time series before comparison, so that series are
        compared based on their shape rather than their absolute scale.
    """
    try:
        from tslearn.metrics import cdist_dtw
        from tslearn.preprocessing import TimeSeriesScalerMeanVariance
        from tslearn.utils import to_time_series_dataset
    except ImportError as e:
        raise ImportError(
            "The 'clustering' extra is required to use this function. "
            "Install it with `pip install infodynamics[clustering]`."
        ) from e

    dataset = to_time_series_dataset(list(series))
    if z_normalize:
        dataset = TimeSeriesScalerMeanVariance().fit_transform(dataset)

    return cdist_dtw(dataset)

"""
Dynamic Time Warping Barycenter Averaging (DBA) of a set of time series.
"""
from typing import Literal, Sequence

import numpy as np


def average(
    series: Sequence[np.ndarray], method: Literal["dba", "soft_dtw"] = "dba", **kwargs
) -> np.ndarray:
    """
    Computes an archetypical time series (barycenter) for a set of
    (possibly differently lengthed) 1D time series.

    Parameters
    ----------
    series : Sequence[np.ndarray]
        the time series to average.

    method : {'dba', 'soft_dtw'}, default='dba'
        'dba' uses DTW Barycenter Averaging (Petitjean et al., 2011).
        'soft_dtw' uses a differentiable, smoothed variant of DTW.

    **kwargs
        forwarded to tslearn's dtw_barycenter_averaging / softdtw_barycenter.
    """
    try:
        from tslearn.barycenters import dtw_barycenter_averaging, softdtw_barycenter
        from tslearn.utils import to_time_series_dataset
    except ImportError as e:
        raise ImportError(
            "The 'clustering' extra is required to use this function. "
            "Install it with `pip install infodynamics[clustering]`."
        ) from e

    dataset = to_time_series_dataset(list(series))

    if method == "dba":
        barycenter = dtw_barycenter_averaging(dataset, **kwargs)
    elif method == "soft_dtw":
        barycenter = softdtw_barycenter(dataset, **kwargs)
    else:
        raise ValueError(
            f"Invalid value for parameter 'method': {method}. Must be 'dba' or 'soft_dtw'."
        )

    return barycenter.ravel()

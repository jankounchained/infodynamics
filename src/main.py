"""
Class for estimation of information dynamics of time-dependent probabilistic document representations.

TODO
- there could be a generalizable rolling average function that could be used for novelty, transience and jump entorpy

Removed functionality:
- sorting
- normalization
"""
import warnings
from typing import Optional, Union, Callable, Tuple
from numpy.typing import ArrayLike

import numpy as np
from pandas import DataFrame


class InfoDynamics:
    def __init__(self, measure: Callable, window: int, inplace_constant: Optional[Union[int, float]] = 0, averaging_weigts: Optional[ArrayLike] = None):
        """

        Parameters
        -----------
        measure : Callable
            distance / similarity metric to use for comparison of observations.

        window : int
            context size (n observations) for calculating novelty.

        inplace_constant : Optional[Union[int, float]]
            constant number that gets added to the signal at the beginning and end of the time series.
            0 by default.
        
        averaging_weigts : Optional[np.Array]
            Weights for averaging novelty and transience.
            Can be used to give more weight to more recent observations.
            Must be of length window - 1.
        """
        self.measure = measure
        self.window = window
        self.inplace_constant = inplace_constant
        self.averaging_weigts = averaging_weigts

    def _summarize_tmp(self, tmp: ArrayLike) -> np.ndarray:
        """
        """
        if self.averaging_weigts is not None:
            return np.average(tmp, weights=self.averaging_weigts, axis=0), np.std(tmp)
        else:
            return np.mean(tmp), np.std(tmp)

    def calculate_novelty(self, X: ArrayLike) -> Tuple[np.ndarray, np.ndarray]:

        ts_len = X.shape[0]

        N_hat = np.empty(ts_len)
        N_sd = np.empty(ts_len)

        for i, x in enumerate(X):
            # select {window} elements before i, or empty array
            submat = X[max(0, i - self.window):i, ]
            
            if submat.shape[0] == self.window:
                # use broadcasting to calculate js_dist for all elements in submat
                tmp = self.measure(x, submat)
                # skip the first comparison (x with itself)
                tmp = tmp[1:]
            else:
                tmp = np.full([self.window - 1], self.inplace_constant)

            N_hat[i], N_sd[i] = self._summarize_tmp(tmp)

        return N_hat, N_sd

    def calculate_transience(self, X: ArrayLike) -> Tuple[np.ndarray, np.ndarray]:

        ts_len = X.shape[0]

        T_hat = np.empty(ts_len)
        T_sd = np.empty(ts_len)

        for i, x in enumerate(X):
            # select {window} elements after i, or empty array
            submat = X[i : max(ts_len + 1, i + self.window + 1), ]
            
            if submat.shape[0] == self.window:
                # use broadcasting to calculate js_dist for all elements in submat
                tmp = self.measure(x, submat)
                # skip the first comparison (x with itself)
                tmp = tmp[1:]
            else:
                tmp = np.full([self.window - 1], self.inplace_constant)

            T_hat[i], T_sd[i] = self._summarize_tmp(tmp)

        return T_hat, T_sd

    # def calc_jump(self, X: np.Array, j, jumps):

    #     ts_len = X.shape[0]

    #     N_hat = np.empty(ts_len)
    #     N_sd = np.empty(ts_len)

    #     for i, x in enumerate(X):
    #         submat = theta[(i - window):(i+window),]
    #         submat_jump = theta[((i - window) + j):((i+window)+j),]
    #         tmp = np.zeros(submat.shape[0])
    #         if submat.any():
    #             for ii, (xx, xx_j) in enumerate(zip(submat, submat_jump)):
    #                 tmp[ii] = meas(xx, xx_j)
    #         else:
    #             tmp = np.zeros([window]) + weight

    #         N_hat[i] = np.mean(tmp)
    #         N_sd[i] = np.std(tmp)
    #     jumps[j] = N_hat

    #     return jumps

    # def slice_zeros(self):
    #     self.nsignal = self.nsignal[self.window:-self.window]
    #     self.nsigma = self.nsigma[self.window:-self.window]
    #     self.tsignal = self.tsignal[self.window:-self.window]
    #     self.tsigma = self.tsigma[self.window:-self.window]
    #     self.rsignal = self.rsignal[self.window:-self.window]
    #     self.rsigma = self.rsigma[self.window:-self.window]

    # def _validate_data(self, X: np.Array) -> np.Array:
    #     """
    #     """
    #     if isinstance(X, list):
    #         if isinstance(X[0], list):
    #             X = np.array(X)
    #     elif isinstance(X, DataFrame):
    #         X = X.to_numpy()
    #     elif isinstance(X, np.ndarray):
    #         pass
    #     else:
    #         warnings.warn(f"Input data type ({type(X)}) not recognized. Returning input data as is."

    #     return X

    # def fit(self):
    #     pass

    # def fit_transform(self, X, slice_w=False):
    #     """
    #     Parameters
    #     ----------
    #     X : {array-like, pd.DataFrame, List[List[float]]} of shape (n_samples, n_features)

    #     """

    #     # validate data
    #     X = self._validate_data(X)

    #     # validate parameters
    #     if self.window < X.shape[0]: 
    #         warnings.warn(f"Window size ({self.window}) is greater than the length of input data ({X.shape[0]}).")

    #     novelty = self.calculate_novelty(X)
    #     transience = self.calculate_transience(X)
    #     resonance = novelty - transience

    #     if slice_w:
    #         self.slice_zeros()

    # # DEPRECATED
    # def fit_save(self, meas, path, slice_w=False):
    #     self.fit(meas, slice_w)

    #     out = {
    #         'novelty': self.nsignal.tolist(),
    #         'novelty_sigma': self.nsigma.tolist(),
    #         'transience': self.tsignal.tolist(),
    #         'transience_sigma': self.tsigma.tolist(),
    #         'resonance': self.rsignal.tolist(),
    #         'resonance_sigma': self.rsigma.tolist(),
    #     }

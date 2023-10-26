"""
Class for estimation of information dynamics of time-dependent probabilistic document representations.

Removed functionality:
- sorting
- normalization
"""
import warnings
from typing import Optional, Union, Callable

import numpy as np
import pandas as pd


class InfoDynamics:
    def __init__(self, measure: Callable, window: int, weight: Optional[Union[int, float]] = 0]):
        """

        Parameters
        -----------
        measure : Callable
            distance / similarity metric to use for comparison of observations.

        window : int
            context size (n observations) for calculating novelty.

        weight : Optional[Union[int, float]]
            flat number that gets added to the signal at the beginning and end of the time series.
            0 by default.
        """
        self.measure = measure
        self.window = window
        self.weight = weight

    def calculate_novelty(self, X: np.Array) -> np.Array:

        ts_len = X.shape[0]
        ts_width = X.shape[1]

        N_hat = np.zeros(ts_len)
        N_sd = np.zeros(ts_len)

        for i, x in enumerate(X):
            submat = self.data[(i - self.window):i, ]
            tmp = np.zeros(submat.shape[0])
            if submat.any():
                for ii, xx in enumerate(submat):
                    tmp[ii] = self.measure(x, xx)
            else:
                tmp = np.zeros([self.window]) + self.weight

            N_hat[i] = np.mean(tmp)
            N_sd[i] = np.std(tmp)

        return N_hat, N_sd

    def calculate_transience(self, X):
        T_hat = np.zeros(self.m)
        T_sd = np.zeros(self.m)
        for i, x in enumerate(self.data):
            submat = self.data[i + 1:(i + self.window + 1), ]
            tmp = np.zeros(submat.shape[0])
            if submat.any():
                for ii, xx in enumerate(submat):
                    tmp[ii] = self.measure(x, xx)
            else:
                tmp = np.zeros([self.window])

            T_hat[i] = np.mean(tmp)
            T_hat[-self.window:] = np.zeros([self.window]) + self.weight
            T_sd[i] = np.std(tmp)

        self.tsignal = T_hat
        self.tsigma = T_sd

    # DEPRECATED
    def calculate_resonance(self, meas=kld):
        self.novelty(meas)
        self.transience(meas)
        self.rsignal = self.nsignal - self.tsignal
        self.rsignal[:self.window] = np.zeros([self.window]) + self.weight
        self.rsignal[-self.window:] = np.zeros([self.window]) + self.weight
        self.rsigma = (self.nsigma + self.tsigma) / 2
        self.rsigma[:self.window] = np.zeros([self.window]) + self.weight
        self.rsigma[-self.window:] = np.zeros([self.window]) + self.weight

    def slice_zeros(self):
        self.nsignal = self.nsignal[self.window:-self.window]
        self.nsigma = self.nsigma[self.window:-self.window]
        self.tsignal = self.tsignal[self.window:-self.window]
        self.tsigma = self.tsigma[self.window:-self.window]
        self.rsignal = self.rsignal[self.window:-self.window]
        self.rsigma = self.rsigma[self.window:-self.window]

    def _validate_data(self, X: np.Array) -> np.Array:
        """
        """
        if isinstance(X, list):
            if isinstance(X[0], list):
                X = np.array(X)
        elif isinstance(X, pd.DataFrame):
            X = X.to_numpy()
        elif isinstance(X, np.ndarray):
            pass

        return X

    def fit(self):
        pass

    def fit_transform(self, X, slice_w=False):
        """
        Parameters
        ----------
        X : {array-like, pd.DataFrame, List[List[float]]} of shape (n_samples, n_features)

        """

        # validate data
        X = self._validate_data(X)

        # validate parameters
        if self.window < X.shape[0]: 
            warnings.warn(f"Window size ({self.window}) is greater than the length of input data ({X.shape[0]}).")

        novelty = self.calculate_novelty(X)
        transience = self.calculate_transience(X)
        resonance = novelty - transience

        if slice_w:
            self.slice_zeros()

    # DEPRECATED
    def fit_save(self, meas, path, slice_w=False):
        self.fit(meas, slice_w)

        out = {
            'novelty': self.nsignal.tolist(),
            'novelty_sigma': self.nsigma.tolist(),
            'transience': self.tsignal.tolist(),
            'transience_sigma': self.tsigma.tolist(),
            'resonance': self.rsignal.tolist(),
            'resonance_sigma': self.rsigma.tolist(),
        }

        with open(path, 'w') as f:
            json.dump(out, f)
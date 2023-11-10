"""
Class for estimation of information dynamics of time-dependent probabilistic document representations.

Removed functionality:
- sorting
- normalization

TODO
- window_size=1 doesn't work
"""
import warnings
from typing import Optional, Union, Callable, Tuple
from numpy.typing import ArrayLike

import numpy as np


class WindowedRollingDistance:
    def __init__(
        self,
        measure: Callable,
        window_size: int,
        jump_size: int = 0,
        inplace_constant: Union[int, float] = 0,
        averaging_weigts: Optional[ArrayLike] = None,
        estimate_error: Optional[bool] = False,
    ):
        """

        Parameters
        -----------
        measure : Callable
            distance / similarity metric to use for comparison of observations.

        window_size : int
            context size (n observations) for calculating novelty.

        jump_size : int
            number of observations to ignore before window kicks in.

        inplace_constant : Optional[Union[int, float]]
            constant number that gets added to the signal at the beginning and end of the time series.
            0 by default.

        averaging_weigts : Optional[np.Array]
            Weights for averaging novelty and transience.
            Can be used to give more weight to more recent observations.
            Must be of length window - 1.

        estimate_error: Optional[bool]
            Return the standard deviation of the novelty, transience and resonance signals?
            False by default.
        """
        self.measure = measure
        self.window = window_size
        self.jump = jump_size
        self.inplace_constant = inplace_constant
        self.averaging_weigts = averaging_weigts
        self.estimate_error = estimate_error

    def _summarize_tmp(self, tmp: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """ """
        if self.averaging_weigts is not None:
            return np.average(tmp, weights=self.averaging_weigts, axis=0), np.std(tmp)
        else:
            return np.mean(tmp), np.std(tmp)

    def _validate_data(self, X: ArrayLike) -> np.ndarray:
        """
        UNFINISHED
        Super basic data validation, converts lists of lists to np.ndarray.
        """
        if isinstance(X, list):
            if isinstance(X[0], list):
                X = np.array(X)
        elif isinstance(X, np.ndarray):
            pass
        else:
            warnings.warn(
                f"Input data type ({type(X)}) not recognized. Returning input data as is."
            )

        return X

    def calc_signal(
        self, X: np.ndarray, relative_to="past"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Parameters
        ----------
        X : {array-like, pd.DataFrame, List[List[float]]}
            of shape (n_samples, n_features)

        relative_to : str
            'past' or 'future'
        """

        ts_len = X.shape[0]

        H_hat = np.empty(ts_len)
        H_sd = np.empty(ts_len)

        for i, x in enumerate(X):
            # select {window} elements after i, or empty array
            if relative_to == "past":
                jump_index = i - self.jump
                # compare x with elements before it
                i_lower = max(0, jump_index - self.window)
                i_upper = max(0, jump_index)
                submat = X[i_lower:i_upper,]
            elif relative_to == "future":
                jump_index = i + self.jump
                # compare x with elements after it
                i_lower = jump_index
                i_upper = min(ts_len - 1, jump_index + self.window)
                submat = X[i_lower:i_upper,]
            else:
                raise ValueError(
                    f"Invalid value for parameter 'relative_to': {relative_to}. Must be 'past' or 'future'."
                )

            if submat.shape[0] == self.window:
                # use broadcasting to calculate js_dist for all elements in submat
                tmp = self.measure(x, submat)
                # skip the first comparison (x with itself)
                tmp = tmp[1:]
            else:
                tmp = np.full([self.window - 1], self.inplace_constant)

            H_hat[i], H_sd[i] = self._summarize_tmp(tmp)

        return H_hat, H_sd

    def _calc_resonance(
        self, N_hat: np.ndarray, T_hat: np.ndarray, N_sd: np.ndarray, T_sd: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """ """
        R_hat = N_hat - T_hat
        R_sd = (N_sd + T_sd) / 2

        # invalidate the signal outside of window bounds
        # R_hat[: self.window] = np.zeros([self.window], dtype=float) + self.inplace_constant
        # R_hat[-self.window :] = np.zeros([self.window], dtype=float) + self.inplace_constant
        # R_sd[: self.window] = np.zeros([self.window], dtype=float) + self.inplace_constant
        # R_sd[-self.window :] = np.zeros([self.window], dtype=float) + self.inplace_constant

        return R_hat, R_sd

    def fit(self, X: ArrayLike, y=None) -> None:
        """Fit signal to data: distance from past, distance from future, difference between distances.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data to estimate fit the signal on.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            Instance with estimated signal.
        """
        X = self._validate_data(X)

        # novelty & transience
        N_hat, N_sd = self.calc_signal(X, relative_to="past")
        T_hat, T_sd = self.calc_signal(X, relative_to="future")
        # resonance
        # TODO consider turning this off for jump calculations
        R_hat, R_sd = self._calc_resonance(N_hat, T_hat, N_sd, T_sd)

        # base output
        signal = {}

        if self.estimate_error:
            signal.update(
                {
                    "N_hat": N_hat,
                    "N_sd": N_sd,
                    "T_hat": T_hat,
                    "T_sd": T_sd,
                    "R_hat": R_hat,
                    "R_sd": R_sd,
                }
            )
        else:
            signal.update(
                {
                    "N_hat": N_hat,
                    "T_hat": T_hat,
                    "R_hat": R_hat,
                }
            )

        self.signal = signal

    def fit_transform(self, X: ArrayLike, y=None) -> dict[str, np.ndarray]:
        """
        Fit to data, return dict with signal.

        Parameters
        ----------
        X : {array-like, pd.DataFrame, List[List[float]]}
            of shape (n_samples, n_features)
            Training set.

        y : Ignored
            Not used, present for API consistency by convention.

        Returns
        -------
        X_new : ndarray array of shape (n_samples, n_features_new)
            Transformed array.
        """
        self.fit(X)
        return self.signal

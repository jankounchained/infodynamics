"""
Detect and describe: estimates novelty, transience and resonance
(single-scale) and multi-scale structure from a numeric embeddings time
series.
"""
from typing import Callable, Sequence, Union
from typing_extensions import Self

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

from infodynamics.scalogram import FooteNovelty, Scalogram, structure_descriptors
from infodynamics.time_series import WindowedRollingDistance


class InfoDynamics(BaseEstimator, TransformerMixin):
    """
    Estimates the rate of flow of information (novelty, transience,
    resonance) between the rows of a numeric embeddings time series.
    """

    def __init__(
        self,
        measure: Union[str, Callable] = "cosine",
        window_size: int = 3,
        jump_size: int = 0,
        estimate_error: bool = False,
    ):
        """

        Parameters
        ----------
        measure : str or Callable, default='cosine'
            distance measure to compare chunk embeddings with. See infodynamics.metrics.DISTANCES.

        window_size : int, default=3
            context size (n chunks) for calculating novelty, transience and resonance.

        jump_size : int, default=0
            number of chunks to ignore before the context window kicks in.

        estimate_error : bool, default=False
            also return the standard deviation of the novelty, transience and resonance signals?
        """
        self.measure = measure
        self.window_size = window_size
        self.jump_size = jump_size
        self.estimate_error = estimate_error

    def fit(self, X, y=None) -> Self:
        """Fit signal to a numeric embeddings time series: estimate
        novelty/transience/resonance.

        Parameters
        ----------
        X : np.ndarray of shape (n_chunks, n_features)
            the embeddings time series to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            instance with estimated signal.
        """
        wrd = WindowedRollingDistance(
            measure=self.measure,
            window_size=self.window_size,
            jump_size=self.jump_size,
            estimate_error=self.estimate_error,
        )
        wrd.fit(X)
        signal = wrd.signal_

        self.signal_ = {
            "novelty": signal["N_hat"],
            "transience": signal["T_hat"],
            "resonance": signal["R_hat"],
        }
        if self.estimate_error:
            self.signal_.update(
                {
                    "novelty_sd": signal["N_sd"],
                    "transience_sd": signal["T_sd"],
                    "resonance_sd": signal["R_sd"],
                }
            )

        return self

    def transform(self, X, y=None) -> np.ndarray:
        """
        Recompute fresh from X (same code path as fit()) and return the
        stacked novelty/transience/resonance signal.

        Parameters
        ----------
        X : np.ndarray of shape (n_chunks, n_features)
            the embeddings time series to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        X_new : np.ndarray of shape (n_chunks, 3)
            novelty, transience and resonance signals stacked as columns.
            The full signal dict (including *_sd keys when
            estimate_error=True) is available on the fitted attribute
            self.signal_.
        """
        self.fit(X)
        return np.column_stack(
            [
                self.signal_["novelty"],
                self.signal_["transience"],
                self.signal_["resonance"],
            ]
        )

    def fit_transform(self, X, y=None) -> np.ndarray:
        """
        Fit to a numeric embeddings time series, return the stacked
        novelty/transience/resonance array.

        Parameters
        ----------
        X : np.ndarray of shape (n_chunks, n_features)
            the embeddings time series to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        X_new : np.ndarray of shape (n_chunks, 3)
            novelty, transience and resonance signals stacked as columns.
            The full signal dict (including *_sd keys when
            estimate_error=True) is available on the fitted attribute
            self.signal_.
        """
        self.fit(X)
        return np.column_stack(
            [
                self.signal_["novelty"],
                self.signal_["transience"],
                self.signal_["resonance"],
            ]
        )


class MultiscaleInfoDynamics(BaseEstimator, TransformerMixin):
    """
    Estimates the multi-scale semantic structure of a numeric embeddings
    time series: a scalogram (rolling distance across window sizes), a
    self-similarity matrix, Foote novelty (checkerboard-kernel novelty
    across kernel radii), and interpretable summary descriptors.

    Complements InfoDynamics, which estimates novelty/transience/resonance
    at a single scale.
    """

    def __init__(
        self,
        scales: Sequence[int] = (2, 3, 5, 8, 13, 21),
        radii: Sequence[int] = (3, 5, 8, 13, 21),
        measure: Union[str, Callable] = "cosine",
    ):
        """

        Parameters
        ----------
        scales : Sequence[int], default=(2, 3, 5, 8, 13, 21)
            window sizes for the scalogram. See infodynamics.scalogram.Scalogram.

        radii : Sequence[int], default=(3, 5, 8, 13, 21)
            checkerboard kernel radii for Foote novelty. See infodynamics.scalogram.FooteNovelty.

        measure : str or Callable, default='cosine'
            distance measure used by the scalogram. See infodynamics.metrics.DISTANCES.
        """
        self.scales = scales
        self.radii = radii
        self.measure = measure

    def fit(self, X, y=None) -> Self:
        """Fit multi-scale structure to a numeric embeddings time series:
        compute the scalogram, self-similarity matrix, Foote novelty and
        summary descriptors.

        Parameters
        ----------
        X : np.ndarray of shape (n_chunks, n_features)
            the embeddings time series to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            instance with estimated multi-scale structure.
        """
        scalogram = Scalogram(scales=self.scales, measure=self.measure).fit(X)
        foote = FooteNovelty(radii=self.radii).fit(X)

        self.ssm_ = foote.ssm_
        self.scalogram_ = scalogram.matrix_
        self.scales_ = scalogram.scales_
        self.novelty_ = foote.novelty_
        self.radii_ = foote.radii_
        self.descriptors_ = structure_descriptors(X, S=self.ssm_)
        self.result_ = {
            "ssm": self.ssm_,
            "scalogram": self.scalogram_,
            "novelty": self.novelty_,
            "descriptors": self.descriptors_,
        }

        return self

    def transform(self, X, y=None) -> np.ndarray:
        """
        Recompute fresh from X (same code path as fit()) and return the
        scalogram matrix.

        Parameters
        ----------
        X : np.ndarray of shape (n_chunks, n_features)
            the embeddings time series to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        X_new : np.ndarray of shape (n_scales, n_chunks)
            the scalogram matrix. The full multi-scale structure dict
            (self-similarity matrix, scalogram, Foote novelty, and
            descriptors) is available on the fitted attribute self.result_.
        """
        self.fit(X)
        return self.scalogram_

    def fit_transform(self, X, y=None) -> np.ndarray:
        """
        Fit to a numeric embeddings time series, return the scalogram
        matrix.

        Parameters
        ----------
        X : np.ndarray of shape (n_chunks, n_features)
            the embeddings time series to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        X_new : np.ndarray of shape (n_scales, n_chunks)
            the scalogram matrix. The full multi-scale structure dict
            (self-similarity matrix, scalogram, Foote novelty, and
            descriptors) is available on the fitted attribute self.result_.
        """
        self.fit(X)
        return self.scalogram_

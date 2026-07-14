"""
Convenience wrappers restoring the one-call fit_transform(text) ergonomics
lost once infodynamics.pipeline.InfoDynamics/MultiscaleInfoDynamics went
ndarray-only (D-04). Each wrapper composes TextSegmenter -> Encoder -> the
corresponding core estimator internally.
"""
from typing import Callable, Optional, Union

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from typing_extensions import Self

from infodynamics.pipeline import InfoDynamics
from infodynamics.text.embedding import Encoder
from infodynamics.text.segmentation import Level, TextSegmenter


class TextInfoDynamics(BaseEstimator, TransformerMixin):
    """
    One-call text convenience wrapper composing TextSegmenter -> Encoder ->
    InfoDynamics: estimates novelty, transience and resonance directly from
    raw text, without requiring the caller to segment/embed manually.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        encoder=None,
        segment_level: Level = "sentence",
        chunk_size: int = 1,
        measure: Union[str, Callable] = "cosine",
        window_size: int = 3,
        jump_size: int = 0,
        estimate_error: bool = False,
        device: Optional[str] = None,
        batch_size: int = 32,
    ):
        """

        Parameters
        ----------
        model_name : str, optional
            HuggingFace Hub encoder model to embed chunks with. Required
            unless 'encoder' is provided.

        encoder : object, optional
            a pre-built encoder (e.g. infodynamics.text.embedding.Encoder)
            exposing fit_transform(List[str]) or encode(List[str]).
            Required unless 'model_name' is provided.

        segment_level : {'word', 'sentence', 'paragraph'}, default='sentence'
            the base unit to split text into. See TextSegmenter.

        chunk_size : int, default=1
            number of consecutive base units to group into a single chunk.

        measure : str or Callable, default='cosine'
            distance measure to compare chunk embeddings with. See infodynamics.metrics.DISTANCES.

        window_size : int, default=3
            context size (n chunks) for calculating novelty, transience and resonance.

        jump_size : int, default=0
            number of chunks to ignore before the context window kicks in.

        estimate_error : bool, default=False
            also return the standard deviation of the novelty, transience and resonance signals?

        device : str, optional
            device to load the encoder model on (e.g. 'cpu', 'cuda'). Only
            used when 'model_name' is provided (i.e. no explicit 'encoder').

        batch_size : int, default=32
            batch size used when encoding chunks. Only used when
            'model_name' is provided (i.e. no explicit 'encoder').
        """
        self.model_name = model_name
        self.encoder = encoder
        self.segment_level = segment_level
        self.chunk_size = chunk_size
        self.measure = measure
        self.window_size = window_size
        self.jump_size = jump_size
        self.estimate_error = estimate_error
        self.device = device
        self.batch_size = batch_size

    def fit(self, text: str, y=None) -> Self:
        """Fit signal to raw text: segment, embed, then estimate
        novelty/transience/resonance.

        Parameters
        ----------
        text : str
            the text to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            instance with estimated signal.
        """
        if self.encoder is None and self.model_name is None:
            raise ValueError("One of 'model_name' or 'encoder' is required.")

        self.segmenter_ = TextSegmenter(level=self.segment_level, chunk_size=self.chunk_size)
        chunks_text = self.segmenter_.fit_transform(text)

        encoder = (
            self.encoder
            if self.encoder is not None
            else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
        )
        if hasattr(encoder, "fit_transform"):
            embeddings = encoder.fit_transform(chunks_text)
        else:
            embeddings = np.asarray(encoder.encode(chunks_text))

        self.info_dynamics_ = InfoDynamics(
            measure=self.measure,
            window_size=self.window_size,
            jump_size=self.jump_size,
            estimate_error=self.estimate_error,
        ).fit(embeddings)

        self.chunks_ = self.segmenter_.chunks_
        self.embeddings_ = np.asarray(embeddings)
        self.signal_ = self.info_dynamics_.signal_

        return self

    def transform(self, text: str, y=None) -> np.ndarray:
        """
        Recompute fresh from text (same code path as fit()) and return the
        stacked novelty/transience/resonance signal.

        Parameters
        ----------
        text : str
            the text to analyze.

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
        self.fit(text)
        return self.info_dynamics_.transform(self.embeddings_)

    def fit_transform(self, text: str, y=None) -> np.ndarray:
        """
        Fit to raw text, return the stacked novelty/transience/resonance
        array.

        Parameters
        ----------
        text : str
            the text to analyze.

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
        self.fit(text)
        return self.info_dynamics_.transform(self.embeddings_)

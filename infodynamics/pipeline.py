"""
Embed, Detect, Describe: turns a raw text document into novelty,
transience and resonance signals.
"""
from typing import Callable, Optional, Sequence, Union
from typing_extensions import Self

from sklearn.base import BaseEstimator, TransformerMixin

from infodynamics.embedding import Encoder
from infodynamics.scalogram import FooteNovelty, Scalogram, structure_descriptors
from infodynamics.segmentation import Level, segment
from infodynamics.time_series import WindowedRollingDistance


class InfoDynamics(BaseEstimator, TransformerMixin):
    """
    Segments a text document, embeds its chunks with a HuggingFace Hub
    encoder model, and estimates the rate of flow of information
    (novelty, transience, resonance) between chunks.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        encoder: Optional[object] = None,
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
        model_name : str or None, default=None
            name of a HuggingFace Hub encoder model, e.g. "sentence-transformers/all-MiniLM-L6-v2".
            Ignored if `encoder` is given. One of `model_name` or `encoder` is required.

        encoder : object or None, default=None
            a pre-built encoder exposing `.encode(texts: List[str]) -> np.ndarray`, e.g.
            infodynamics.embedding.Encoder or infodynamics.morphology.MorphologicalEncoder.
            Takes precedence over `model_name` if given.

        segment_level : {'word', 'sentence', 'paragraph'}, default='sentence'
            base unit to split the text document into.

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

        device : str or None, default=None
            device to load the encoder model onto, e.g. "cuda" or "cpu". Defaults to the model's own default.

        batch_size : int, default=32
            number of chunks to embed per encoder batch.
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
        """Fit signal to a text document: segment, embed, and estimate novelty/transience/resonance.

        Parameters
        ----------
        text : str
            the text document to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            instance with estimated signal.
        """
        if self.encoder is None and self.model_name is None:
            raise ValueError("One of 'model_name' or 'encoder' is required.")

        chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
        encoder = self.encoder if self.encoder is not None else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
        embeddings = encoder.encode([chunk.text for chunk in chunks])

        wrd = WindowedRollingDistance(
            measure=self.measure,
            window_size=self.window_size,
            jump_size=self.jump_size,
            estimate_error=self.estimate_error,
        )
        signal = wrd.fit_transform(embeddings)

        self.chunks_ = chunks
        self.embeddings_ = embeddings
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

    def fit_transform(self, text: str, y=None) -> dict:
        """
        Fit to a text document, return dict with signal.

        Parameters
        ----------
        text : str
            the text document to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        signal : dict[str, np.ndarray]
            novelty, transience and resonance signals (and their standard deviations, if requested).
        """
        self.fit(text)
        return self.signal_


class MultiscaleInfoDynamics(BaseEstimator, TransformerMixin):
    """
    Segments a text document, embeds its chunks with a HuggingFace Hub
    encoder model, and estimates its multi-scale semantic structure: a
    scalogram (rolling distance across window sizes), a self-similarity
    matrix, Foote novelty (checkerboard-kernel novelty across kernel radii),
    and interpretable summary descriptors.

    Complements InfoDynamics, which estimates novelty/transience/resonance
    at a single scale.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        encoder: Optional[object] = None,
        segment_level: Level = "sentence",
        chunk_size: int = 1,
        scales: Sequence[int] = (2, 3, 5, 8, 13, 21),
        radii: Sequence[int] = (3, 5, 8, 13, 21),
        measure: Union[str, Callable] = "cosine",
        device: Optional[str] = None,
        batch_size: int = 32,
    ):
        """

        Parameters
        ----------
        model_name : str or None, default=None
            name of a HuggingFace Hub encoder model, e.g. "sentence-transformers/all-MiniLM-L6-v2".
            Ignored if `encoder` is given. One of `model_name` or `encoder` is required.

        encoder : object or None, default=None
            a pre-built encoder exposing `.encode(texts: List[str]) -> np.ndarray`, e.g.
            infodynamics.embedding.Encoder or infodynamics.morphology.MorphologicalEncoder.
            Takes precedence over `model_name` if given.

        segment_level : {'word', 'sentence', 'paragraph'}, default='sentence'
            base unit to split the text document into.

        chunk_size : int, default=1
            number of consecutive base units to group into a single chunk.

        scales : Sequence[int], default=(2, 3, 5, 8, 13, 21)
            window sizes for the scalogram. See infodynamics.scalogram.Scalogram.

        radii : Sequence[int], default=(3, 5, 8, 13, 21)
            checkerboard kernel radii for Foote novelty. See infodynamics.scalogram.FooteNovelty.

        measure : str or Callable, default='cosine'
            distance measure used by the scalogram. See infodynamics.metrics.DISTANCES.

        device : str or None, default=None
            device to load the encoder model onto, e.g. "cuda" or "cpu". Defaults to the model's own default.

        batch_size : int, default=32
            number of chunks to embed per encoder batch.
        """
        self.model_name = model_name
        self.encoder = encoder
        self.segment_level = segment_level
        self.chunk_size = chunk_size
        self.scales = scales
        self.radii = radii
        self.measure = measure
        self.device = device
        self.batch_size = batch_size

    def fit(self, text: str, y=None) -> Self:
        """Fit multi-scale structure to a text document: segment, embed, and
        compute the scalogram, self-similarity matrix, Foote novelty and
        summary descriptors.

        Parameters
        ----------
        text : str
            the text document to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            instance with estimated multi-scale structure.
        """
        if self.encoder is None and self.model_name is None:
            raise ValueError("One of 'model_name' or 'encoder' is required.")

        chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
        encoder = self.encoder if self.encoder is not None else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
        embeddings = encoder.encode([chunk.text for chunk in chunks])

        scalogram = Scalogram(scales=self.scales, measure=self.measure).fit(embeddings)
        foote = FooteNovelty(radii=self.radii).fit(embeddings)

        self.chunks_ = chunks
        self.embeddings_ = embeddings
        self.ssm_ = foote.ssm_
        self.scalogram_ = scalogram.matrix_
        self.scales_ = scalogram.scales_
        self.novelty_ = foote.novelty_
        self.radii_ = foote.radii_
        self.descriptors_ = structure_descriptors(embeddings, S=self.ssm_)

        return self

    def fit_transform(self, text: str, y=None) -> dict:
        """
        Fit to a text document, return dict with multi-scale structure.

        Parameters
        ----------
        text : str
            the text document to analyze.

        y : Ignored
            not used, present here for API consistency by convention.

        Returns
        -------
        structure : dict
            self-similarity matrix ('ssm'), scalogram matrix ('scalogram'),
            Foote novelty matrix ('novelty'), and summary descriptors ('descriptors').
        """
        self.fit(text)
        return {
            "ssm": self.ssm_,
            "scalogram": self.scalogram_,
            "novelty": self.novelty_,
            "descriptors": self.descriptors_,
        }

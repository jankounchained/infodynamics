"""
Embed, Detect, Describe: turns a raw text document into novelty,
transience and resonance signals.
"""
from typing import Callable, Optional, Union
from typing_extensions import Self

from sklearn.base import BaseEstimator, TransformerMixin

from infodynamics.embedding import Encoder
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
        model_name: str,
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
        model_name : str
            name of a HuggingFace Hub encoder model, e.g. "sentence-transformers/all-MiniLM-L6-v2".

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
        chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
        encoder = Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
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

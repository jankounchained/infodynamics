"""
Loads HuggingFace Hub encoder models and embeds text chunks.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from typing_extensions import Self

_MODEL_CACHE: Dict[Tuple[str, Optional[str]], "object"] = {}


def _load_model(model_name: str, device: Optional[str] = None):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "The 'embedding' extra is required to use Encoder. "
            "Install it with `pip install infodynamics[embedding]`."
        ) from e

    key = (model_name, device)
    if key not in _MODEL_CACHE:
        if device is not None:
            _MODEL_CACHE[key] = SentenceTransformer(model_name, device=device)
        else:
            _MODEL_CACHE[key] = SentenceTransformer(model_name)
    return _MODEL_CACHE[key]


class Encoder(BaseEstimator, TransformerMixin):
    """Embeds text chunks with a HuggingFace Hub encoder model."""

    def __init__(
        self,
        model_name: str,
        device: Optional[str] = None,
        batch_size: int = 32,
        normalize: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize = normalize

    def fit(self, texts: List[str], y=None) -> Self:
        return self

    def transform(self, texts: List[str], y=None) -> np.ndarray:
        return self.encode(texts)

    def encode(self, texts: List[str]) -> np.ndarray:
        model = _load_model(self.model_name, self.device)

        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings)

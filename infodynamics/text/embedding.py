"""
Loads HuggingFace Hub encoder models and embeds text chunks.
"""
from typing import Dict, List, Optional

import numpy as np

_MODEL_CACHE: Dict[str, "object"] = {}


def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "The 'embedding' extra is required to use Encoder. "
            "Install it with `pip install infodynamics[embedding]`."
        ) from e

    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]


class Encoder:
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

    def encode(self, texts: List[str]) -> np.ndarray:
        model = _load_model(self.model_name)
        if self.device is not None:
            model.to(self.device)

        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings)

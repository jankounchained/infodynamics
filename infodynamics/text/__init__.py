"""infodynamics.text — text on-ramp (segmentation, embedding, morphological encoding)."""
from infodynamics.text.embedding import Encoder
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.text.pipeline import TextInfoDynamics, TextMultiscaleInfoDynamics
from infodynamics.text.segmentation import Chunk, TextSegmenter, segment, strip_markdown

__all__ = [
    "TextInfoDynamics",
    "TextMultiscaleInfoDynamics",
    "TextSegmenter",
    "Encoder",
    "MorphologicalEncoder",
    "Chunk",
    "segment",
    "strip_markdown",
]

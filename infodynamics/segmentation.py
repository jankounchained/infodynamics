"""
Splits raw text into chunks (words, sentences or paragraphs, optionally
grouped by a custom count) ahead of embedding.
"""
import re
from dataclasses import dataclass
from typing import List, Literal, Tuple

Level = Literal["word", "sentence", "paragraph"]


@dataclass
class Chunk:
    text: str
    start: int
    end: int


def _word_spans(text: str) -> List[Tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]


def _sentence_parts(text: str) -> List[str]:
    import syntok.segmenter as segmenter

    parts = []
    for paragraph in segmenter.process(text):
        for sentence in paragraph:
            part = "".join(token.spacing + token.value for token in sentence).strip()
            if part:
                parts.append(part)
    return parts


def _paragraph_parts(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]


def _spans_from_parts(text: str, parts: List[str]) -> List[Tuple[int, int]]:
    spans = []
    cursor = 0
    for part in parts:
        start = text.index(part, cursor)
        end = start + len(part)
        spans.append((start, end))
        cursor = end
    return spans


def _base_spans(text: str, level: Level) -> List[Tuple[int, int]]:
    if level == "word":
        return _word_spans(text)
    elif level == "sentence":
        return _spans_from_parts(text, _sentence_parts(text))
    elif level == "paragraph":
        return _spans_from_parts(text, _paragraph_parts(text))
    else:
        raise ValueError(
            f"Invalid value for parameter 'level': {level}. Must be 'word', 'sentence' or 'paragraph'."
        )


def segment(text: str, level: Level = "sentence", chunk_size: int = 1) -> List[Chunk]:
    """
    Splits text into chunks.

    Parameters
    ----------
    text : str
        the text to segment.

    level : {'word', 'sentence', 'paragraph'}, default='sentence'
        the base unit to split text into.

    chunk_size : int, default=1
        number of consecutive base units to group into a single chunk.
    """
    if chunk_size < 1:
        raise ValueError(f"'chunk_size' must be >= 1, got {chunk_size}.")

    spans = _base_spans(text, level)

    chunks = []
    for i in range(0, len(spans), chunk_size):
        group = spans[i : i + chunk_size]
        start = group[0][0]
        end = group[-1][1]
        chunks.append(Chunk(text=text[start:end], start=start, end=end))

    return chunks

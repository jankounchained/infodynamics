""" """
import pytest

from infodynamics.segmentation import Chunk, segment

TEXT = "Hello world. This is a test! Is it working?\n\nNew paragraph here. Another sentence."


def test_segment_words():
    chunks = segment(TEXT, level="word")
    assert [c.text for c in chunks][:3] == ["Hello", "world.", "This"]
    for chunk in chunks:
        assert TEXT[chunk.start : chunk.end] == chunk.text


def test_segment_sentences():
    chunks = segment(TEXT, level="sentence")
    assert [c.text for c in chunks] == [
        "Hello world.",
        "This is a test!",
        "Is it working?",
        "New paragraph here.",
        "Another sentence.",
    ]
    for chunk in chunks:
        assert TEXT[chunk.start : chunk.end] == chunk.text


def test_segment_paragraphs():
    chunks = segment(TEXT, level="paragraph")
    assert [c.text for c in chunks] == [
        "Hello world. This is a test! Is it working?",
        "New paragraph here. Another sentence.",
    ]
    for chunk in chunks:
        assert TEXT[chunk.start : chunk.end] == chunk.text


def test_segment_offsets_survive_paragraph_boundary():
    chunks = segment(TEXT, level="sentence")
    last = chunks[-1]
    assert TEXT[last.start : last.end] == "Another sentence."
    assert last.start == TEXT.index("Another sentence.")


def test_chunk_size_groups_consecutive_units():
    chunks = segment("One. Two. Three. Four. Five.", level="sentence", chunk_size=2)
    assert [c.text for c in chunks] == ["One. Two.", "Three. Four.", "Five."]


def test_chunk_size_must_be_positive():
    with pytest.raises(ValueError):
        segment(TEXT, chunk_size=0)


def test_invalid_level_raises():
    with pytest.raises(ValueError):
        segment(TEXT, level="paragraphs")


def test_returns_chunk_dataclass():
    chunks = segment(TEXT, level="sentence")
    assert all(isinstance(c, Chunk) for c in chunks)

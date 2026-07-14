""" """
import pytest

from infodynamics.text.segmentation import Chunk, segment, strip_markdown

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


def test_strip_markdown_removes_heading_hashes():
    assert strip_markdown("# Title\nSome text.") == "Title\nSome text."


def test_strip_markdown_removes_bullets_and_numbered_lists():
    assert strip_markdown("- First item\n* Second item\n1. Third item") == (
        "First item\nSecond item\nThird item"
    )


def test_strip_markdown_removes_emphasis_markers():
    assert strip_markdown("This is **bold** and _italic_ text.") == "This is bold and italic text."


def test_strip_markdown_keeps_link_text_drops_url():
    assert strip_markdown("See [the docs](https://example.com) for more.") == (
        "See the docs for more."
    )


def test_strip_markdown_removes_blockquote_markers():
    assert strip_markdown("> A quoted line.") == "A quoted line."


def test_strip_markdown_removes_inline_code():
    result = strip_markdown("Run `pip install infodynamics` now.")
    assert "`" not in result
    assert "now." in result


def test_strip_markdown_preserves_punctuation():
    text = "Well, this works! Doesn't it? Yes: absolutely; 100%."
    assert strip_markdown(text) == text

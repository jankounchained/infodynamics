import infodynamics
import infodynamics.text


def test_core_all_matches_expected_symbols():
    expected = {
        "InfoDynamics", "MultiscaleInfoDynamics", "WindowedRollingDistance",
        "Scalogram", "FooteNovelty", "SignalClusterer",
        "self_similarity_matrix", "structure_descriptors",
    }
    assert set(infodynamics.__all__) == expected
    for name in infodynamics.__all__:
        assert hasattr(infodynamics, name), f"{name} in __all__ but not importable"


def test_core_init_has_no_text_imports():
    import inspect
    source = inspect.getsource(infodynamics)
    assert ".text" not in source, "infodynamics/__init__.py must not import from .text (D-05)"


def test_text_all_matches_expected_symbols():
    expected = {
        "TextInfoDynamics", "TextMultiscaleInfoDynamics", "TextSegmenter",
        "Encoder", "MorphologicalEncoder", "Chunk", "segment", "strip_markdown",
    }
    assert set(infodynamics.text.__all__) == expected
    for name in infodynamics.text.__all__:
        assert hasattr(infodynamics.text, name), f"{name} in __all__ but not importable"

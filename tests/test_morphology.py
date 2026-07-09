""" """
import numpy as np
import pytest

spacy = pytest.importorskip("spacy")
pytest.importorskip("textdescriptives")

from spacy.tokens import Doc  # noqa: E402

import infodynamics.pipeline as pipeline_module  # noqa: E402
from infodynamics import MorphologicalEncoder  # noqa: E402
from infodynamics.pipeline import MultiscaleInfoDynamics  # noqa: E402


class FakeNlp:
    """Stand-in for a spacy_udpipe pipeline, avoids network/model download."""

    def __init__(self, docs):
        self._docs = docs

    def pipe(self, texts):
        return iter(self._docs)


def _make_docs():
    nlp = spacy.blank("cs")
    nlp.add_pipe("attribute_ruler")
    nlp.add_pipe("textdescriptives/pos_proportions")

    doc_verb_heavy = Doc(nlp.vocab, words=["Běžel", "a", "skákal"], pos=["VERB", "CCONJ", "VERB"])
    doc_noun_heavy = Doc(nlp.vocab, words=["Kočka", "a", "pes"], pos=["NOUN", "CCONJ", "NOUN"])
    return [doc_verb_heavy, doc_noun_heavy]


def test_invalid_feature_group_raises():
    with pytest.raises(ValueError):
        MorphologicalEncoder(feature_group="not_a_real_group")


def test_encode_returns_matrix_with_feature_names():
    encoder = MorphologicalEncoder(feature_group="pos_proportions", nlp=FakeNlp(_make_docs()))
    matrix = encoder.encode(["Běžel a skákal.", "Kočka a pes."])

    assert matrix.shape == (2, len(encoder.feature_names_))
    assert "pos_prop_VERB" in encoder.feature_names_
    assert "pos_prop_NOUN" in encoder.feature_names_


def test_encode_fills_missing_pos_tags_with_zero():
    encoder = MorphologicalEncoder(feature_group="pos_proportions", nlp=FakeNlp(_make_docs()))
    matrix = encoder.encode(["Běžel a skákal.", "Kočka a pes."])

    verb_col = encoder.feature_names_.index("pos_prop_VERB")
    noun_col = encoder.feature_names_.index("pos_prop_NOUN")

    assert matrix[1, verb_col] == 0.0  # noun-heavy chunk has no verbs
    assert matrix[0, noun_col] == 0.0  # verb-heavy chunk has no nouns


class FakeMorphologicalEncoder:
    """Deterministic stand-in, avoids depending on a real UDPipe model in the pipeline test."""

    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts):
        rng = np.random.default_rng(0)
        return rng.normal(size=(len(texts), 5))


def test_multiscale_info_dynamics_accepts_custom_encoder():
    text = "Cats chase mice. Dogs chase cats. The sun is bright today. Rain falls on the roof."
    model = MultiscaleInfoDynamics(encoder=FakeMorphologicalEncoder(), scales=[1, 2], radii=[1, 2])
    model.fit(text)

    assert model.descriptors_["n_chunks"] == len(model.chunks_)


def test_fit_raises_without_model_name_or_encoder():
    model = pipeline_module.MultiscaleInfoDynamics()
    with pytest.raises(ValueError):
        model.fit("Some text.")

"""
Proves the two sklearn-composability requirements:

- API-01: every public estimator (core + text on-ramp + wrappers) passes a
  clone()/get_params()/set_params() round-trip.
- API-02: the text on-ramp -> analysis flow composes end-to-end inside a
  sklearn.pipeline.Pipeline, and set_params(step__param=...) takes effect.

Runs green in the default (no-heavy-extras) suite via a deterministic stub
encoder as the Pipeline's middle step; the literal Encoder() form (ROADMAP
success criterion 4) is covered separately under an importorskip guard.
"""
import numpy as np
import pytest
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.pipeline import Pipeline

from infodynamics import (
    FooteNovelty,
    InfoDynamics,
    MultiscaleInfoDynamics,
    Scalogram,
    SignalClusterer,
    WindowedRollingDistance,
)
from infodynamics.text import TextInfoDynamics, TextMultiscaleInfoDynamics, TextSegmenter
from infodynamics.text.embedding import Encoder
from infodynamics.text.morphology import MorphologicalEncoder

TEXT = (
    "Cats chase mice in the yard. Dogs bark loudly at strangers. "
    "The sun rises over the quiet hills. Rain falls gently on the roof. "
    "Birds sing sweetly at dawn. Fish swim silently in the pond. "
    "Wind blows softly through the trees. Snow falls quietly in winter. "
    "Leaves rustle in the autumn breeze. Waves crash steadily on the shore."
)


def _build_public_estimators():
    """Representative instance of every public estimator (core + text
    on-ramp + convenience wrappers). Constructing Encoder/MorphologicalEncoder
    does not load their heavy models (lazy), so this runs in the default
    no-extras suite."""
    return [
        WindowedRollingDistance(measure="cosine", window_size=3),
        Scalogram(scales=[2, 3, 5]),
        FooteNovelty(radii=[3, 5]),
        InfoDynamics(window_size=3),
        MultiscaleInfoDynamics(scales=[2, 3, 5], radii=[3, 5]),
        SignalClusterer(n_clusters=2),
        TextSegmenter(level="sentence"),
        Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu"),
        MorphologicalEncoder(feature_group="pos_proportions"),
        TextInfoDynamics(model_name="m"),
        TextMultiscaleInfoDynamics(model_name="m"),
    ]


@pytest.mark.parametrize(
    "estimator",
    _build_public_estimators(),
    ids=lambda est: type(est).__name__,
)
def test_all_public_estimators_clone_round_trip(estimator):
    cloned = clone(estimator)

    assert type(cloned) is type(estimator)
    assert cloned.get_params() == estimator.get_params()

    params = estimator.get_params()
    assert params, f"{type(estimator).__name__} exposes no params to round-trip"
    key = next(iter(params))
    result = estimator.set_params(**{key: params[key]})
    assert result is estimator


class _StubEncoder(BaseEstimator, TransformerMixin):
    """Deterministic Pipeline-legal encoder double standing in for
    infodynamics.text.embedding.Encoder: a real estimator instance (not a
    monkeypatched module attribute) usable as a Pipeline step, with no
    network/heavy-dependency calls."""

    def fit(self, texts, y=None):
        return self

    def transform(self, texts, y=None):
        rng = np.random.default_rng(0)
        return rng.standard_normal((len(texts), 8))


def test_pipeline_composes_text_to_analysis():
    pipe = Pipeline(
        [
            ("segment", TextSegmenter()),
            ("encode", _StubEncoder()),
            ("analyze", MultiscaleInfoDynamics(scales=[2, 3], radii=[3])),
        ]
    )

    result = pipe.fit_transform(TEXT)

    assert isinstance(result, np.ndarray)
    n_chunks = len(pipe.named_steps["segment"].chunks_)
    assert result.shape[1] == n_chunks
    assert result.shape[0] == len(pipe.named_steps["analyze"].scales_)


def test_pipeline_set_params_takes_effect():
    pipe = Pipeline(
        [
            ("segment", TextSegmenter()),
            ("encode", _StubEncoder()),
            ("analyze", InfoDynamics(window_size=3)),
        ]
    )

    pipe.set_params(segment__chunk_size=2)
    assert pipe.named_steps["segment"].chunk_size == 2

    pipe.set_params(analyze__window_size=1)
    assert pipe.named_steps["analyze"].window_size == 1

    result = pipe.fit_transform(TEXT)
    assert isinstance(result, np.ndarray)


@pytest.mark.network
def test_pipeline_with_real_encoder():
    """The literal criterion-4 form named in ROADMAP.md: Pipeline([("segment",
    TextSegmenter()), ("encode", Encoder()), ("analyze",
    MultiscaleInfoDynamics())]).fit_transform(text). Skipped when the
    'embedding' extra is absent so the default suite stays green."""
    pytest.importorskip("sentence_transformers")

    long_text = " ".join(f"Sentence number {i} describes a simple event." for i in range(50))

    pipe = Pipeline(
        [
            ("segment", TextSegmenter()),
            ("encode", Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")),
            ("analyze", MultiscaleInfoDynamics()),
        ]
    )

    result = pipe.fit_transform(long_text)

    assert isinstance(result, np.ndarray)

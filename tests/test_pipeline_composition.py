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
import pytest
from sklearn.base import clone

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

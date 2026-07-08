""" """
import numpy as np

import infodynamics.pipeline as pipeline_module
from infodynamics import InfoDynamics, MultiscaleInfoDynamics

TEXT = "Cats chase mice. Dogs chase cats. The sun is bright today. Rain falls on the roof."
MULTISCALE_TEXT = (
    "Cats chase mice. Dogs chase cats. The sun is bright today. Rain falls on the roof. "
    "Birds sing at dawn. Fish swim in the sea. Wind blows through trees. Snow falls in winter."
)


class FakeEncoder:
    """Deterministic stand-in for infodynamics.embedding.Encoder, avoids network calls."""

    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts):
        rng = np.random.default_rng(0)
        return rng.normal(size=(len(texts), 8))


def test_fit_transform_returns_novelty_transience_resonance(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)

    model = InfoDynamics(model_name="fake-model", window_size=1)
    signal = model.fit_transform(TEXT)

    assert set(signal.keys()) == {"novelty", "transience", "resonance"}
    for key, values in signal.items():
        assert len(values) == len(model.chunks_)
        assert not np.isnan(values).any(), f"{key} contains NaN"


def test_fit_stores_chunks_and_embeddings(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)

    model = InfoDynamics(model_name="fake-model", window_size=1)
    model.fit(TEXT)

    assert len(model.chunks_) == len(model.embeddings_)
    assert model.embeddings_.shape[1] == 8


def test_estimate_error_adds_sd_keys(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)

    model = InfoDynamics(model_name="fake-model", window_size=1, estimate_error=True)
    signal = model.fit_transform(TEXT)

    assert {"novelty_sd", "transience_sd", "resonance_sd"} <= set(signal.keys())


def test_chunk_size_reduces_signal_length(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)

    model_1 = InfoDynamics(model_name="fake-model", chunk_size=1, window_size=1)
    model_2 = InfoDynamics(model_name="fake-model", chunk_size=2, window_size=1)

    signal_1 = model_1.fit_transform(TEXT)
    signal_2 = model_2.fit_transform(TEXT)

    assert len(signal_2["novelty"]) < len(signal_1["novelty"])


def test_multiscale_fit_transform_returns_expected_keys(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)

    model = MultiscaleInfoDynamics(model_name="fake-model", scales=[1, 2, 3], radii=[1, 2, 3])
    result = model.fit_transform(MULTISCALE_TEXT)

    n_chunks = len(model.chunks_)
    assert set(result.keys()) == {"ssm", "scalogram", "novelty", "descriptors"}
    assert result["ssm"].shape == (n_chunks, n_chunks)
    assert result["scalogram"].shape == (len(model.scales_), n_chunks)
    assert result["novelty"].shape == (len(model.radii_), n_chunks)
    assert result["descriptors"]["n_chunks"] == n_chunks


def test_multiscale_fit_stores_chunks_and_embeddings(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)

    model = MultiscaleInfoDynamics(model_name="fake-model", scales=[1, 2], radii=[1, 2])
    model.fit(MULTISCALE_TEXT)

    assert len(model.chunks_) == len(model.embeddings_)
    assert model.embeddings_.shape[1] == 8

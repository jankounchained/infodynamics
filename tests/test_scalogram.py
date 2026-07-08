""" """
import numpy as np
import pytest

from infodynamics.scalogram import (
    FooteNovelty,
    Scalogram,
    checkerboard_kernel,
    foote_novelty,
    rolling_gap_distance,
    self_similarity_matrix,
    structure_descriptors,
)


def _make_embeddings(n=20, d=6, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def test_rolling_gap_distance_matches_length_and_has_no_nan():
    emb = _make_embeddings()
    d = rolling_gap_distance(emb, window_size=3)
    assert d.shape == (emb.shape[0],)
    assert not np.isnan(d).any()


def test_scalogram_stacks_scales_and_drops_too_large():
    emb = _make_embeddings(n=10)
    scal = Scalogram(scales=[2, 3, 20]).fit(emb)
    assert scal.scales_ == [2, 3]
    assert scal.matrix_.shape == (2, 10)


def test_scalogram_fit_transform_returns_matrix():
    emb = _make_embeddings(n=10)
    matrix = Scalogram(scales=[2, 3]).fit_transform(emb)
    assert matrix.shape == (2, 10)


def test_scalogram_raises_when_no_scale_fits():
    emb = _make_embeddings(n=5)
    with pytest.raises(ValueError):
        Scalogram(scales=[10]).fit(emb)


def test_self_similarity_matrix_is_symmetric_with_unit_diagonal():
    emb = _make_embeddings()
    S = self_similarity_matrix(emb)
    assert S.shape == (emb.shape[0], emb.shape[0])
    np.testing.assert_allclose(S, S.T, atol=1e-6)
    np.testing.assert_allclose(np.diag(S), 1.0, atol=1e-6)


def test_checkerboard_kernel_shape_and_sign():
    K = checkerboard_kernel(radius=4)
    assert K.shape == (9, 9)
    assert K[0, 0] > 0  # top-left quadrant: same-side, same-side -> positive
    assert K[0, -1] < 0  # top-right quadrant: opposite signs -> negative


def test_foote_novelty_matches_length_and_nonnegative():
    emb = _make_embeddings()
    S = self_similarity_matrix(emb)
    nov = foote_novelty(S, radius=3)
    assert nov.shape == (emb.shape[0],)
    assert (nov >= 0).all()


def test_footenovelty_stacks_radii_and_drops_too_large():
    emb = _make_embeddings(n=10)
    foote = FooteNovelty(radii=[2, 3, 20]).fit(emb)
    assert foote.radii_ == [2, 3]
    assert foote.novelty_.shape == (2, 10)
    assert foote.ssm_.shape == (10, 10)


def test_footenovelty_fit_transform_returns_matrix():
    emb = _make_embeddings(n=10)
    novelty = FooteNovelty(radii=[2, 3]).fit_transform(emb)
    assert novelty.shape == (2, 10)


def test_footenovelty_raises_when_no_radius_fits():
    emb = _make_embeddings(n=4)
    with pytest.raises(ValueError):
        FooteNovelty(radii=[10]).fit(emb)


def test_structure_descriptors_keys_and_types():
    emb = _make_embeddings()
    desc = structure_descriptors(emb, window_size=3)
    assert desc["n_chunks"] == emb.shape[0]
    assert set(desc) == {
        "n_chunks",
        "mean_offdiag_sim",
        "p90_offdiag_sim",
        "dist_var_w3",
        "dist_mean_w3",
    }


def test_structure_descriptors_reuses_given_ssm():
    emb = _make_embeddings()
    S = self_similarity_matrix(emb)
    desc = structure_descriptors(emb, S=S)
    assert desc["mean_offdiag_sim"] == pytest.approx(
        float(S[np.triu_indices_from(S, k=1)].mean())
    )

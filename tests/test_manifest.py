""" """
import json
import shutil
from pathlib import Path

import pytest

from infodynamics import __version__
from infodynamics.cache_contract import (
    CACHE_SCHEMA_VERSION,
    build_manifest,
    config_hash,
    hash_cache_files,
    normalize_config,
    verify_manifest,
)
from infodynamics.shipping import pack_project, pull_project, verify_project

BASE_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "csv_path": "/machine/a/data.csv",
    "cache_dir": "/machine/a/cache",
    "device": "mps",
    "batch_size": 32,
    "authors": ["ai", "human"],
    "min_sentences": 12,
    "n_docs": 78,
    "n_sentences": 17486,
    "emb_dim": 384,
}


# --------------------------------------------------------------------------- #
# config_hash normalization + stability
# --------------------------------------------------------------------------- #
def test_normalize_config_drops_machine_specific_fields():
    normalized = normalize_config(BASE_CONFIG)
    assert "csv_path" not in normalized
    assert "cache_dir" not in normalized
    assert "device" not in normalized
    assert "batch_size" not in normalized
    assert "n_docs" not in normalized
    assert "n_sentences" not in normalized
    assert "emb_dim" not in normalized
    assert normalized["model_name"] == BASE_CONFIG["model_name"]


def test_config_hash_stable_across_machine_specific_differences():
    other_machine = {
        **BASE_CONFIG,
        "csv_path": "/machine/b/somewhere/else.csv",
        "cache_dir": "/machine/b/cache",
        "device": "cuda",
        "batch_size": 8,
        "n_docs": 999,
        "n_sentences": 999,
        "emb_dim": 999,
    }
    assert config_hash(BASE_CONFIG) == config_hash(other_machine)


def test_config_hash_ignores_key_order():
    reordered = dict(reversed(list(BASE_CONFIG.items())))
    assert config_hash(BASE_CONFIG) == config_hash(reordered)


def test_config_hash_changes_with_meaningful_param():
    changed = {**BASE_CONFIG, "min_sentences": 20}
    assert config_hash(BASE_CONFIG) != config_hash(changed)


def test_config_hash_changes_with_model_name():
    changed = {**BASE_CONFIG, "model_name": "Qwen/Qwen3-Embedding-8B"}
    assert config_hash(BASE_CONFIG) != config_hash(changed)


def test_config_hash_is_sha256_prefixed():
    assert config_hash(BASE_CONFIG).startswith("sha256:")


# --------------------------------------------------------------------------- #
# checksum round-trip
# --------------------------------------------------------------------------- #
def _make_cache_dir(tmp_path: Path) -> Path:
    cache = tmp_path / "cache"
    (cache / "emb").mkdir(parents=True)
    (cache / "config.json").write_text('{"model_name": "fake"}')
    (cache / "emb" / "doc1.npy").write_bytes(b"\x00\x01\x02\x03")
    return cache


def test_hash_cache_files_excludes_manifest_itself(tmp_path):
    cache = _make_cache_dir(tmp_path)
    (cache / "manifest.json").write_text("{}")
    files = hash_cache_files(cache)
    assert "manifest.json" not in files
    assert "config.json" in files
    assert "emb/doc1.npy" in files


def test_build_manifest_and_verify_round_trip(tmp_path):
    cache = _make_cache_dir(tmp_path)
    corpus = tmp_path / "corpus.csv"
    corpus.write_text("file_name,author,content\na,human,hello\n")

    manifest = build_manifest(
        pipeline_version=__version__, cache_dir=cache, corpus_path=corpus,
        config=BASE_CONFIG, n_docs=1, n_sentences=1,
        models={"embedding": {"name": "fake", "revision": None}}, repo_dir=None,
    )
    (cache / "manifest.json").write_text(json.dumps(manifest))

    assert manifest["cache_schema_version"] == CACHE_SCHEMA_VERSION
    assert manifest["corpus_hash"].startswith("sha256:")
    assert manifest["pipeline_git_sha"] is None  # repo_dir=None -> best-effort skip
    assert verify_manifest(cache) == []


def test_verify_manifest_detects_tampering(tmp_path):
    cache = _make_cache_dir(tmp_path)
    corpus = tmp_path / "corpus.csv"
    corpus.write_text("file_name,author,content\na,human,hello\n")
    manifest = build_manifest(
        pipeline_version=__version__, cache_dir=cache, corpus_path=corpus,
        config=BASE_CONFIG, n_docs=1, n_sentences=1,
        models={"embedding": {"name": "fake", "revision": None}}, repo_dir=None,
    )
    (cache / "manifest.json").write_text(json.dumps(manifest))

    (cache / "emb" / "doc1.npy").write_bytes(b"\xff\xff\xff\xff")
    assert verify_manifest(cache) == ["emb/doc1.npy"]


def test_verify_manifest_detects_missing_file(tmp_path):
    cache = _make_cache_dir(tmp_path)
    corpus = tmp_path / "corpus.csv"
    corpus.write_text("file_name,author,content\na,human,hello\n")
    manifest = build_manifest(
        pipeline_version=__version__, cache_dir=cache, corpus_path=corpus,
        config=BASE_CONFIG, n_docs=1, n_sentences=1,
        models={"embedding": {"name": "fake", "revision": None}}, repo_dir=None,
    )
    (cache / "manifest.json").write_text(json.dumps(manifest))

    (cache / "emb" / "doc1.npy").unlink()
    assert verify_manifest(cache) == ["emb/doc1.npy"]


# --------------------------------------------------------------------------- #
# pack / pull round-trip (via infodynamics/shipping.py), rclone against a
# plain local directory used as the "remote" -- no rclone.conf entry needed.
# --------------------------------------------------------------------------- #
requires_rclone = pytest.mark.skipif(
    shutil.which("rclone") is None, reason="rclone binary not installed")


def _make_project(tmp_path: Path, name: str = "myproject") -> Path:
    project = tmp_path / name
    cache = project / "cache" / "emb"
    cache.mkdir(parents=True)
    (project / "data").mkdir()
    corpus = project / "data" / "corpus.csv"
    corpus.write_text("file_name,author,content\na,human,hello world\n")
    (project / "config.json").write_text(json.dumps({**BASE_CONFIG, "csv_path": str(corpus)}))
    (project / "requirements.txt").write_text(f"infodynamics=={__version__}\n")
    (cache.parent / "config.json").write_text(json.dumps({**BASE_CONFIG, "csv_path": str(corpus)}))
    (cache / "doc1.npy").write_bytes(b"\x01\x02\x03\x04")

    manifest = build_manifest(
        pipeline_version=__version__, cache_dir=project / "cache", corpus_path=corpus,
        config=BASE_CONFIG, n_docs=1, n_sentences=1,
        models={"embedding": {"name": "fake", "revision": None}}, repo_dir=None,
    )
    (project / "cache" / "manifest.json").write_text(json.dumps(manifest))
    return project


@requires_rclone
def test_pack_pull_round_trip_yields_identical_cache(tmp_path):
    remote = tmp_path / "remote"
    remote.mkdir()
    project = _make_project(tmp_path / "source")

    pack_project(project, str(remote))

    pulled = tmp_path / "pulled"
    pull_project(pulled, str(remote))

    original_files = sorted((project / "cache").rglob("*"))
    for path in original_files:
        if path.is_file():
            rel = path.relative_to(project)
            assert (pulled / rel).read_bytes() == path.read_bytes()

    verify_project(pulled)  # should not raise


@requires_rclone
def test_verify_project_fails_after_tampering_post_pull(tmp_path):
    remote = tmp_path / "remote"
    remote.mkdir()
    project = _make_project(tmp_path / "source")
    pack_project(project, str(remote))

    pulled = tmp_path / "pulled"
    pull_project(pulled, str(remote))

    (pulled / "cache" / "emb" / "doc1.npy").write_bytes(b"\x00\x00\x00\x00")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        verify_project(pulled)


@requires_rclone
def test_pack_fails_loudly_on_precorrupted_cache(tmp_path):
    remote = tmp_path / "remote"
    remote.mkdir()
    project = _make_project(tmp_path / "source")

    (project / "cache" / "emb" / "doc1.npy").write_bytes(b"\x00\x00\x00\x00")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        pack_project(project, str(remote))

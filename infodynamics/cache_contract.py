"""
Shared contract for a project's cache/ directory: the schema version it's
built against, and the checksum/config-hash logic used both to *write*
cache/manifest.json (dashboard/build_dashboard_artifacts.py) and to *check*
it (infodynamics/shipping.py's pack/pull/verify commands). Keeping this in one
place means the builder and the shipper can never disagree about what a
manifest means.

Bump CACHE_SCHEMA_VERSION only when the on-disk cache layout itself changes
(new/renamed files, changed formats) -- not on every pipeline release.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CACHE_SCHEMA_VERSION = 1

# config.json fields that are machine-specific or derived from the corpus at
# build time, not part of what defines "the same cache build" -- excluded so
# config_hash is stable across machines/devices and the corpus is represented
# by corpus_hash instead of csv_path.
_CONFIG_HASH_EXCLUDE = {"csv_path", "cache_dir", "device", "batch_size", "n_docs", "n_sentences", "emb_dim"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def normalize_config(config: dict) -> dict:
    """Drops machine-specific/derived fields so the result only reflects
    parameters that change the actual cache contents."""
    return {k: config[k] for k in sorted(config) if k not in _CONFIG_HASH_EXCLUDE}


def config_hash(config: dict) -> str:
    normalized = normalize_config(config)
    payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return sha256_bytes(payload)


def git_sha(repo_dir: Path) -> Optional[str]:
    """Best-effort `git rev-parse HEAD` in repo_dir. Returns None (not an
    error) if repo_dir isn't a git checkout at all, e.g. a shallow/no-git
    export onto an ephemeral GPU box."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_dir,
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def resolve_hf_revision(model_name: str) -> Optional[str]:
    """Best-effort resolution of the exact commit hash behind a HuggingFace
    Hub model name, so manifest.json pins precisely which weights built a
    cache (a model *name* can move; a commit hash can't). Returns None if
    huggingface_hub isn't installed or the lookup fails (offline, gated repo,
    a local path rather than a Hub id, ...) -- this is provenance, not a hard
    requirement of the build."""
    try:
        from huggingface_hub import HfApi
        return HfApi().model_info(model_name).sha
    except Exception:
        return None


def hash_cache_files(cache_dir: Path) -> dict:
    """sha256 of every file under cache_dir (except manifest.json itself,
    which doesn't exist yet when this runs), keyed by POSIX-style relative
    path so the manifest is stable across OSes. This is the integrity check
    pack/pull/verify all reuse."""
    files = {}
    for path in sorted(cache_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            rel = path.relative_to(cache_dir).as_posix()
            files[rel] = sha256_file(path)
    return files


def build_manifest(*, pipeline_version: str, cache_dir: Path, corpus_path: Path,
                    config: dict, n_docs: int, n_sentences: int,
                    models: dict, repo_dir: Optional[Path] = None) -> dict:
    """Assembles the manifest.json payload -- see BRIEF_artifact_backbone.md
    for the field list. Call after every other cache file has been written,
    since `files` is a checksum walk of cache_dir at call time."""
    return {
        "pipeline_version": pipeline_version,
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline_git_sha": git_sha(repo_dir) if repo_dir is not None else None,
        "config_hash": config_hash(config),
        "corpus_hash": sha256_file(corpus_path),
        "models": models,
        "n_docs": n_docs,
        "n_sentences": n_sentences,
        "files": hash_cache_files(cache_dir),
    }


def verify_manifest(cache_dir: Path) -> list:
    """Recomputes checksums for every file cache_dir/manifest.json claims.
    Returns a list of relative paths that are missing or altered (empty if
    everything matches). Raises FileNotFoundError if manifest.json itself is
    missing."""
    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{manifest_path} not found")
    manifest = json.loads(manifest_path.read_text())
    mismatches = []
    for rel, expected in manifest["files"].items():
        path = cache_dir / rel
        if not path.is_file() or sha256_file(path) != expected:
            mismatches.append(rel)
    return mismatches

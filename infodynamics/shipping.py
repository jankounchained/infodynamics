"""
Ships a project's cache/ bundle to/from remote storage via rclone.

infodynamics runs its (expensive, GPU-bound) precompute once per project and
then needs to move the resulting cache/ around -- typically GPU box -> Google
Drive -> a laptop running the dashboard. Google Drive handles one big file far
better than many small ones, so this packs the whole project into a single
`.tar.zst` rather than syncing cache/ loose (see BRIEF_artifact_backbone.md).

Four thin, shell-based commands (registered as console_scripts in setup.py):
    infodynamics-pack          verify + tar + rclone-copy a project up
    infodynamics-pull          rclone-copy + untar + verify a project down
    infodynamics-verify        recheck an existing project's cache/ in place
    infodynamics-init-project  scaffold a new project directory

These shell out to the system `rclone` and `tar` binaries rather than adding a
Python rclone dependency. Checksum/config-hash logic lives in
infodynamics.cache_contract, shared with the dashboard build script that
writes cache/manifest.json in the first place -- pack/pull/verify never
recompute that logic independently.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from infodynamics import __version__
from infodynamics.cache_contract import CACHE_SCHEMA_VERSION, verify_manifest

# The parts of a project directory that make up a shippable bundle -- see
# BRIEF_artifact_backbone.md's scaffold layout. cache/ itself is produced by
# the build, not by infodynamics-init-project.
BUNDLE_MEMBERS = ("config.json", "data", "cache", "manifest.json", "requirements.txt")


def _run(cmd: list) -> subprocess.CompletedProcess:
    """subprocess.run wrapper that fails loudly: pack/pull/verify are meant to
    run unattended on a GPU box or in CI, so a silently-swallowed non-zero
    exit from tar/rclone would be worse than a raised exception."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(cmd)}\n{result.stderr}")
    return result


def _read_manifest(project: Path) -> dict:
    manifest_path = project / "cache" / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{manifest_path} not found -- build the cache first.")
    return json.loads(manifest_path.read_text())


def verify_project(project: Path) -> dict:
    """Recomputes checksums for every file cache/manifest.json claims and
    confirms cache_schema_version is one this installed pipeline can read.
    Raises on schema incompatibility or any checksum mismatch; only warns (to
    stderr) on a pipeline_version difference, since a newer/older patch
    version alone doesn't mean the cache is unreadable. Returns the manifest
    on success.
    """
    manifest = _read_manifest(project)
    if manifest["cache_schema_version"] != CACHE_SCHEMA_VERSION:
        raise RuntimeError(
            f"cache_schema_version {manifest['cache_schema_version']} is incompatible with "
            f"the installed infodynamics (schema {CACHE_SCHEMA_VERSION})")
    if manifest["pipeline_version"] != __version__:
        print(f"warning: cache was built with infodynamics {manifest['pipeline_version']}, "
              f"installed version is {__version__}", file=sys.stderr)
    mismatches = verify_manifest(project / "cache")
    if mismatches:
        raise RuntimeError(f"checksum mismatch for {len(mismatches)} file(s): {mismatches}")
    return manifest


def pack_project(project: Path, remote: str) -> Path:
    """Verifies the project's cache against its manifest, tars the shippable
    bundle, and rclone-copies the archive to `<remote>/<project_name>/`.
    Archive name embeds the first 8 hex chars of config_hash so distinct
    builds of the same project don't silently overwrite one another remotely.
    """
    project = project.resolve()
    manifest = verify_project(project)

    members = [m for m in BUNDLE_MEMBERS if (project / m).exists()]
    config_hash_prefix = manifest["config_hash"].split(":")[-1][:8]
    archive_name = f"{project.name}-{config_hash_prefix}.tar.zst"
    archive_path = project.parent / archive_name

    _run(["tar", "--zstd", "-cf", str(archive_path), "-C", str(project), *members])

    dest = f"{remote.rstrip('/')}/{project.name}/"
    _run(["rclone", "copy", str(archive_path), dest])
    print(f"packed -> {archive_path}")
    print(f"shipped -> {dest}")
    return archive_path


def _newest_remote_archive(remote: str, project_name: str) -> str:
    remote_dir = f"{remote.rstrip('/')}/{project_name}/"
    result = _run(["rclone", "lsjson", remote_dir])
    entries = json.loads(result.stdout)
    archives = [e for e in entries if e["Path"].endswith(".tar.zst")]
    if not archives:
        raise FileNotFoundError(f"no .tar.zst archives found in {remote_dir}")
    return max(archives, key=lambda e: e["ModTime"])["Path"]


def pull_project(project: Path, remote: str, archive: Optional[str] = None) -> None:
    """rclone-copies an archive down and unpacks it into `project`, then
    verifies every file against the unpacked manifest.json -- refusing to
    leave a half-verified bundle in place if anything doesn't match (the
    extraction happens in a temp dir first; `project` is only touched once
    verification passes).
    """
    project = project.resolve()
    archive_name = archive or _newest_remote_archive(remote, project.name)
    remote_dir = f"{remote.rstrip('/')}/{project.name}/"

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _run(["rclone", "copy", f"{remote_dir}{archive_name}", str(tmp)])
        archive_path = tmp / archive_name
        if not archive_path.is_file():
            raise FileNotFoundError(f"{archive_path} was not downloaded from {remote_dir}")

        extract_dir = tmp / "extracted"
        extract_dir.mkdir()
        _run(["tar", "--zstd", "-xf", str(archive_path), "-C", str(extract_dir)])

        verify_project(extract_dir)  # raises before anything touches `project`

        project.mkdir(parents=True, exist_ok=True)
        for item in extract_dir.iterdir():
            dest = project / item.name
            if dest.is_dir():
                shutil.rmtree(dest)
            elif dest.exists():
                dest.unlink()
            shutil.move(str(item), str(dest))

    print(f"pulled -> {project} (from {archive_name})")


def init_project(project: Path, config_path: Path) -> None:
    """Scaffolds the standard per-project layout: data/ for the user's corpus
    CSV, config.json copied from --config, requirements.txt pinned to the
    installed infodynamics version, .gitignore for cache/ and archives, and a
    one-line README. cache/ itself is created by the build (run_pipeline()),
    not here.
    """
    project.mkdir(parents=True, exist_ok=True)
    (project / "data").mkdir(exist_ok=True)
    shutil.copy(config_path, project / "config.json")
    (project / "requirements.txt").write_text(f"infodynamics=={__version__}\n")
    (project / ".gitignore").write_text("cache/\n*.tar.zst\n")
    (project / "README.md").write_text(
        f"# {project.name}\n\n"
        "Drop the corpus CSV in `data/`, then build the cache on the GPU box:\n\n"
        "    python build_dashboard_artifacts.py --model-name <hf-model> "
        f"--csv data/<corpus>.csv --cache-dir {project.name}/cache\n\n"
        "Ship it and pull it down locally:\n\n"
        f"    infodynamics-pack --project . --remote <remote>\n"
        f"    infodynamics-pull --project . --remote <remote>\n"
    )
    print(f"scaffolded -> {project}")


# --------------------------------------------------------------------------- #
# console_scripts entry points
# --------------------------------------------------------------------------- #
def pack_main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Verify a project's cache, tar it, and rclone-copy it to a remote.")
    parser.add_argument("--project", type=Path, required=True, help="project directory.")
    parser.add_argument("--remote", required=True,
                        help="rclone remote and base path, e.g. 'gdrive:infodynamics-projects'.")
    args = parser.parse_args(argv)
    pack_project(args.project, args.remote)


def pull_main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(
        description="rclone-copy a project's archive down, unpack it, and verify it.")
    parser.add_argument("--project", type=Path, required=True, help="project directory.")
    parser.add_argument("--remote", required=True,
                        help="rclone remote and base path, e.g. 'gdrive:infodynamics-projects'.")
    parser.add_argument("--archive", default=None,
                        help="archive filename (default: newest in the project's remote folder).")
    args = parser.parse_args(argv)
    pull_project(args.project, args.remote, args.archive)


def verify_main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Recompute checksums for a project's cache/ and confirm they match manifest.json.")
    parser.add_argument("--project", type=Path, required=True, help="project directory.")
    args = parser.parse_args(argv)
    manifest = verify_project(args.project)
    print(f"verify ok -- {len(manifest['files'])} files match manifest.json")


def init_project_main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description="Scaffold a new infodynamics project directory.")
    parser.add_argument("dir", type=Path, help="directory to create/scaffold.")
    parser.add_argument("--config", type=Path, required=True,
                        help="config.json to copy into the new project.")
    args = parser.parse_args(argv)
    init_project(args.dir, args.config)

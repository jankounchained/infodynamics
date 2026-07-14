---
phase: 02-reorganize-into-core-text-on-ramp
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - infodynamics/text/__init__.py
  - tests/text/__init__.py
  - infodynamics/__init__.py
  - infodynamics/pipeline.py
  - tests/golden/capture_baseline.py
  - benchmark_embedding.py
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found (info-only)

## Summary

This phase's actual edits are narrow: two new docstring/marker `__init__.py` stubs for the new `infodynamics/text/` and `tests/text/` packages, and four files with import-path updates (`infodynamics.embedding` → `infodynamics.text.embedding`, `infodynamics.morphology` → `infodynamics.text.morphology`, `infodynamics.segmentation` → `infodynamics.text.segmentation`).

Verification performed beyond static reading:
- Confirmed via `git show 974ddb3^:...` that `infodynamics/__init__.py`'s eager top-level `from infodynamics.text.morphology import MorphologicalEncoder` is **not a new bug** — the pre-phase version already eagerly imported `MorphologicalEncoder` at package-import time (`from infodynamics.morphology import ...`); this phase only repointed the path. `infodynamics/text/morphology.py` itself imports only `numpy` at module scope and defers `spacy_udpipe`/`textdescriptives` imports (with `ImportError` guards giving install instructions) inside functions — so `import infodynamics` still does not require the `morphology` extra. Confirmed the same holds for `infodynamics/text/embedding.py` (module-scope import is only `numpy`; `sentence_transformers` is lazily imported inside `_load_model` with an `ImportError` guard) and `infodynamics/text/segmentation.py` (`syntok` is lazily imported inside `_sentence_parts`). All lazy heavy-dependency guards are preserved intact (these files were untouched, per the git-mv byte-identical move).
- Ran `.venv/bin/python -c "import infodynamics"` — succeeds cleanly.
- Ran `pytest tests/test_pipeline.py tests/text/ -q` — 28 passed. Confirmed `tests/test_pipeline.py`'s `monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)` still works correctly post-refactor, since `infodynamics/pipeline.py`'s `from infodynamics.text.embedding import Encoder` binds the same `Encoder` name into `pipeline_module`'s namespace regardless of the source path.
- Grepped the full git-tracked tree for stale `infodynamics.embedding` / `infodynamics.morphology` / `infodynamics.segmentation` references outside the reviewed diff — found none in executable code; only a leftover docstring/comment in `tests/test_pipeline.py:15` (not part of this phase's diff, and not executed code, but stale — see IN-01 below). Untracked scratch scripts at repo root (`run_multiscale_demo.py`, `run_morphology_demo.py`, `segmentation_demo.py`) also reference the pre-move `infodynamics.segmentation` path and would now fail with `ModuleNotFoundError`, but these are untracked/out-of-scope files, not part of this phase's commits — noted for awareness only, not scored as a finding.
- Confirmed `setup.py` uses `find_packages()` (no explicit package list to update), so the new `infodynamics.text` subpackage is automatically discovered for install/build.

The import-path edits themselves are correct and complete within the reviewed file set. No bugs, security issues, or behavior changes were introduced. Findings below are minor and informational only.

## Info

### IN-01: Stale docstring reference to pre-move import path (outside this phase's diff, but related)

**File:** `tests/test_pipeline.py:15`
**Issue:** `FakeEncoder`'s docstring reads "Deterministic stand-in for infodynamics.embedding.Encoder" — the module moved to `infodynamics.text.embedding` in this phase, but this comment (not part of the reviewed diff) wasn't updated. Purely cosmetic (comment only, no functional impact), but leaves a discoverability gap for anyone grepping for the old path.
**Fix:**
```python
class FakeEncoder:
    """Deterministic stand-in for infodynamics.text.embedding.Encoder, avoids network calls."""
```

### IN-02: Import-order convention drifts slightly after path rewrite

**File:** `infodynamics/__init__.py:3-8`
**Issue:** The pre-phase file was ordered alphabetically by module path (`clustering`, `morphology`, `pipeline`, `scalogram`, `segmentation`, `time_series`). After repointing two of the six imports to `infodynamics.text.*`, the list is no longer alphabetically sorted by the string that now appears on each line (`infodynamics.text.morphology` sorts after `infodynamics.time_series` alphabetically, but appears second in the file). Purely stylistic — no functional effect — but worth a quick pass if the project cares about import ordering as a lint-able convention.
**Fix:** Re-sort if desired:
```python
from infodynamics.clustering import SignalClusterer
from infodynamics.pipeline import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.scalogram import FooteNovelty, Scalogram, self_similarity_matrix, structure_descriptors
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.text.segmentation import Chunk, segment, strip_markdown
from infodynamics.time_series import WindowedRollingDistance
```

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

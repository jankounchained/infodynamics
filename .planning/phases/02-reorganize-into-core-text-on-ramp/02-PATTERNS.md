# Phase 2: Reorganize Into Core + Text On-Ramp - Pattern Map

**Mapped:** 2026-07-14
**Files analyzed:** 10 (3 moved modules, 2 moved tests, 2 new `__init__.py`, 2 import-fix-only files, 1 discretionary fix)
**Analogs found:** 10 / 10 (this phase is self-referential — every "analog" is the file's own current content; there is no cross-codebase pattern search needed because this is a pure relocation, not new code)

**Note on methodology:** This phase does not require searching for "closest analog" files elsewhere in the codebase — every file listed below already exists at its pre-move path with exact, verified content (from `02-RESEARCH.md`'s exhaustive grep/read inventory). The "pattern" to copy is each file's own current content, `git mv`'d verbatim, with only import-path strings edited. This document exists to give the planner copy-paste-ready before/after excerpts so no additional file reads are needed during planning or execution.

## File Classification

| New/Modified File | Role | Data Flow | Source (pre-move) | Match Quality |
|---|---|---|---|---|
| `infodynamics/text/__init__.py` | module init | N/A (new, empty) | none (new file) | new |
| `infodynamics/text/segmentation.py` | utility | transform | `infodynamics/segmentation.py` (git mv, content unchanged) | exact (self) |
| `infodynamics/text/embedding.py` | service | transform | `infodynamics/embedding.py` (git mv, content unchanged) | exact (self) |
| `infodynamics/text/morphology.py` | service | transform | `infodynamics/morphology.py` (git mv, content unchanged) | exact (self) |
| `infodynamics/__init__.py` | config/barrel | request-response (import surface) | itself, import-path edit only | exact (self) |
| `infodynamics/pipeline.py` | service (orchestrator) | transform | itself, import-path + docstring edit only | exact (self) |
| `tests/text/__init__.py` | test | N/A (new, empty) | none (new file) | new |
| `tests/text/test_segmentation.py` | test | request-response (unit test) | `tests/test_segmentation.py` (git mv, import edit) | exact (self) |
| `tests/text/test_morphology.py` | test | request-response (unit test) | `tests/test_morphology.py` (git mv, import edit) | exact (self) |
| `tests/golden/capture_baseline.py` | test/fixture | batch | itself, import-path edit only (D-06) | exact (self) |
| `benchmark_embedding.py` (discretionary, see Open Question) | script | batch | itself, import-path edit only | exact (self) |

## Pattern Assignments

### `infodynamics/text/segmentation.py` (utility, transform)

**Source:** `git mv infodynamics/segmentation.py infodynamics/text/segmentation.py`

No content edits. Internal imports (`re`, `dataclasses`, `typing`, lazy `syntok.segmenter`) are unaffected — they don't reference the moving package paths.

---

### `infodynamics/text/embedding.py` (service, transform)

**Source:** `git mv infodynamics/embedding.py infodynamics/text/embedding.py`

No content edits. Preserve the lazy-import pattern verbatim (do not rework):
```python
# infodynamics/embedding.py:11-18 (inside _load_model(), called from Encoder.encode())
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "The 'embedding' extra is required to use Encoder. "
            "Install it with `pip install infodynamics[embedding]`."
        ) from e
```

---

### `infodynamics/text/morphology.py` (service, transform)

**Source:** `git mv infodynamics/morphology.py infodynamics/text/morphology.py`

No content edits. Preserve the lazy-import pattern verbatim (occurs at lines 36-50, 71, 110-117, 125-131, 186 pre-move — same relative offsets post-move since content is byte-identical):
```python
# infodynamics/morphology.py:36-50 (inside _load_pipeline(), called from MorphologicalEncoder.encode())
def _load_pipeline(lang: str, feature_group: str, model_path: Optional[str] = None):
    try:
        import spacy_udpipe
    except ImportError as e:
        raise ImportError(
            "The 'morphology' extra is required to use MorphologicalEncoder. "
            "Install it with `pip install infodynamics[morphology]`."
        ) from e
    try:
        import textdescriptives  # noqa: F401  (registers the textdescriptives/* spaCy factories)
    except ImportError as e:
        raise ImportError(
            "The 'morphology' extra is required to use MorphologicalEncoder. "
            "Install it with `pip install infodynamics[morphology]`."
        ) from e
```

---

### `infodynamics/text/__init__.py` (module init, new)

**No analog needed** — new empty file per D-03 (no re-exports this phase).
```python
"""infodynamics.text — text on-ramp (segmentation, embedding, morphological encoding).

Symbol re-exports are deferred to a later phase (API-03/API-04).
"""
```
(Empty docstring-only file is sufficient; do not add re-exports.)

---

### `infodynamics/__init__.py` (barrel/config, request-response)

**Analog:** itself — import-path-only edit (D-04)

**Before (verified exact current file, 8 lines):**
```python
__version__ = "0.1.0"

from infodynamics.clustering import SignalClusterer
from infodynamics.morphology import MorphologicalEncoder
from infodynamics.pipeline import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.scalogram import FooteNovelty, Scalogram, self_similarity_matrix, structure_descriptors
from infodynamics.segmentation import Chunk, segment, strip_markdown
from infodynamics.time_series import WindowedRollingDistance
```

**After (only these two lines' RHS path changes):**
```python
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.text.segmentation import Chunk, segment, strip_markdown
```
All other lines unchanged.

---

### `infodynamics/pipeline.py` (service/orchestrator, transform)

**Analog:** itself — import-path + docstring edit only (D-01, D-02, Pitfall 1)

**Before (verified exact current lines 10, 12):**
```python
from infodynamics.embedding import Encoder
from infodynamics.scalogram import FooteNovelty, Scalogram, structure_descriptors
from infodynamics.segmentation import Level, segment
from infodynamics.time_series import WindowedRollingDistance
```

**After:**
```python
from infodynamics.text.embedding import Encoder
from infodynamics.scalogram import FooteNovelty, Scalogram, structure_descriptors
from infodynamics.text.segmentation import Level, segment
from infodynamics.time_series import WindowedRollingDistance
```

**Docstring hygiene fix (Pitfall 1) — lines 46 and 188:** both `InfoDynamics.__init__` and `MultiscaleInfoDynamics.__init__` docstrings prose-mention `infodynamics.embedding.Encoder` / `infodynamics.morphology.MorphologicalEncoder` in the `encoder` parameter docs. Update these two prose mentions to `infodynamics.text.embedding.Encoder` / `infodynamics.text.morphology.MorphologicalEncoder` in the same edit pass (not caught by the functional-import grep sweep since no `import`/`from` keyword is present).

**Call sites unaffected (no edit needed)** — bound names stay the same inside the module namespace:
```python
# infodynamics/pipeline.py:103-105 (InfoDynamics.fit) and :243-245 (MultiscaleInfoDynamics.fit), identical pattern
chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
encoder = self.encoder if self.encoder is not None else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
embeddings = encoder.encode([chunk.text for chunk in chunks])
```
Phase 3 removes these calls entirely — do not touch them this phase.

**Verification after edit:** `grep -n "infodynamics\.embedding\|infodynamics\.morphology" infodynamics/pipeline.py` must return zero hits (only `infodynamics.text.embedding`/`infodynamics.text.morphology` should remain).

---

### `tests/text/__init__.py` (test, new)

**No analog needed** — new empty file, mirrors `tests/golden/__init__.py` (0 lines, confirmed empty).

---

### `tests/text/test_segmentation.py` (test, request-response)

**Source:** `git mv tests/test_segmentation.py tests/text/test_segmentation.py`, then edit import.

**Before:**
```python
# tests/test_segmentation.py:4
from infodynamics.segmentation import Chunk, segment, strip_markdown
```

**After:**
```python
from infodynamics.text.segmentation import Chunk, segment, strip_markdown
```

---

### `tests/text/test_morphology.py` (test, request-response)

**Source:** `git mv tests/test_morphology.py tests/text/test_morphology.py`, then edit ONE of two imports (Pitfall 2 — easy to miss the second).

**Before:**
```python
# tests/test_morphology.py:11-12
from infodynamics import MorphologicalEncoder  # noqa: E402          <- NO CHANGE (re-export via infodynamics/__init__.py, D-04)
from infodynamics.morphology import encode_all_feature_groups  # noqa: E402   <- MUST CHANGE
```

**After:**
```python
from infodynamics import MorphologicalEncoder  # noqa: E402
from infodynamics.text.morphology import encode_all_feature_groups  # noqa: E402
```

**Why line 11 does NOT change:** `MorphologicalEncoder` resolves through the package's top-level re-export surface (`infodynamics/__init__.py`), which is fixed separately (D-04) — editing it here would be redundant/inconsistent, not wrong, but the research explicitly flags this as the pitfall to watch: don't assume both lines need the same treatment.

---

### `tests/golden/capture_baseline.py` (test/fixture, batch)

**Analog:** itself — single import-path edit only (D-06). File location unchanged (D-08 — does NOT move to `tests/text/`).

**Before:**
```python
# tests/golden/capture_baseline.py:34
from infodynamics.embedding import Encoder
```

**After:**
```python
from infodynamics.text.embedding import Encoder
```

**Do NOT touch:** the `if __name__ == "__main__":` block's self-check logic, or re-run it to regenerate `baseline_arrays.npz`/`baseline_meta.json` (Pitfall 3 — would violate zero-behavior-change).

---

### `benchmark_embedding.py` (script, batch) — discretionary, flagged by research as Open Question 1

**Analog:** itself — same two-line edit pattern as `capture_baseline.py`.

**Before:**
```python
# benchmark_embedding.py:31-32
from infodynamics.embedding import Encoder
from infodynamics.segmentation import segment
```

**After:**
```python
from infodynamics.text.embedding import Encoder
from infodynamics.text.segmentation import segment
```
Also update the docstring prose mention at line 4 for consistency (same hygiene pattern as pipeline.py Pitfall 1).

**Recommendation carried from RESEARCH.md:** Fix it in the same pass as the other 5 files — it is tracked in git (unlike the explicitly out-of-scope untracked demo scripts `run_multiscale_demo.py`, `run_morphology_demo.py`, `segmentation_demo.py`), it's a 2-line change, and leaving a tracked file with dangling imports contradicts the phase's "zero behavior change / no dangling references" spirit. If the planner disagrees, treat this as an explicit logged decision, not a silent omission.

## Shared Patterns

### Lazy heavy-dependency import (preserve verbatim across all three moved modules)
**Source:** `infodynamics/embedding.py` (pre-move), `infodynamics/morphology.py` (pre-move)
**Apply to:** `infodynamics/text/embedding.py`, `infodynamics/text/morphology.py` — no rework, just relocate
```python
try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "The 'embedding' extra is required to use Encoder. "
        "Install it with `pip install infodynamics[embedding]`."
    ) from e
```
This `try/except ImportError` → actionable `pip install infodynamics[extra]` message pattern is the project's established convention for every optional heavy dependency (also used in `infodynamics/clustering/barycenter.py` for `tslearn`, out of scope this phase but confirms the pattern is codebase-wide).

### Import-path-only edit (applies to all 5 tracked call-site files + 1 discretionary)
**Pattern:** `from infodynamics.<module> import X` → `from infodynamics.<module> import X` becomes `from infodynamics.text.<module> import X`. No other line in any of these files changes. Apply identically to: `infodynamics/__init__.py`, `infodynamics/pipeline.py`, `tests/text/test_segmentation.py`, `tests/text/test_morphology.py`, `tests/golden/capture_baseline.py`, and (discretionary) `benchmark_embedding.py`.

### `git mv` for history preservation
**Apply to:** the three moved source files and two moved test files. Use `git mv` (not copy+delete) so git's rename detection (100% content similarity pre-edit) keeps `git log --follow` history intact. Make the import-path edit as a separate step/commit from the `git mv` if commit granularity matters (Claude's discretion per CONTEXT.md).

## No Analog Found

None — every file in scope already exists in the codebase today; this phase is a pure relocation, not new code, so there is no case where an external analog needs to be invented.

## Metadata

**Analog search scope:** Not applicable in the traditional sense — source of truth is `02-RESEARCH.md`'s exhaustive grep/read inventory of the current repo (verified against live files, not inferred).
**Files scanned:** 3 moved modules + 2 moved tests + 2 barrel/orchestrator files + 1 fixture file + 1 discretionary script + confirmed-zero-reference files (`infodynamics/clustering/*.py`, `scalogram.py`, `time_series.py`, `metrics.py`, `util.py`, `viz.py`, and 5 other test files) = full repo coverage per RESEARCH.md Step 3.
**Pattern extraction date:** 2026-07-14

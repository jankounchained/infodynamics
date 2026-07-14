# Phase 4: Curate the Public API - Pattern Map

**Mapped:** 2026-07-14
**Files analyzed:** 5 (2 modified, 1 test fix, 2 new)
**Analogs found:** 5 / 5

This phase is a mechanical packaging refactor. RESEARCH.md already resolved every mechanical detail (exact current re-exports, target `__all__` contents, the one breaking test import). This PATTERNS.md maps each file to its closest in-repo analog and captures the concrete excerpts to copy from, per GSD convention.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `infodynamics/__init__.py` | config (package export surface) | transform (re-export) | `infodynamics/clustering/__init__.py` | exact (same role: curated `__init__.py` re-export surface) |
| `infodynamics/text/__init__.py` | config (package export surface) | transform (re-export) | `infodynamics/clustering/__init__.py` | exact |
| `tests/text/test_morphology.py` | test | request-response (import fix only) | itself (single-line import edit) | exact |
| `examples/basic_usage.py` | utility (docs/example script) | batch (script, `__main__` guard) | none in-repo (no `examples/` dir exists) — model after RESEARCH.md's specified structure and existing demo scripts' import style | no analog |
| `CHANGELOG.md` | config (docs) | transform (static table) | none in-repo (no CHANGELOG exists) | no analog |
| `tests/test_public_api.py` | test | request-response (assertion-only) | `tests/test_viz.py` (existing test that already imports submodules directly, e.g. `from infodynamics import viz`) | role-match |

## Pattern Assignments

### `infodynamics/__init__.py` (config, transform)

**Analog:** `infodynamics/clustering/__init__.py` (curated re-export precedent, D-04 keeps it unchanged as the style model)

**Current full content** (`infodynamics/__init__.py:1-8`):
```python
__version__ = "0.1.0"

from infodynamics.clustering import SignalClusterer
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.pipeline import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.scalogram import FooteNovelty, Scalogram, self_similarity_matrix, structure_descriptors
from infodynamics.text.segmentation import Chunk, segment, strip_markdown
from infodynamics.time_series import WindowedRollingDistance
```

**Analog style to copy** (`infodynamics/clustering/__init__.py:1-3`, plain re-export, no aliasing, no `__all__` currently but style of import grouping is the model):
```python
from infodynamics.clustering.barycenter import average as barycenter_average
from infodynamics.clustering.cluster import SignalClusterer
from infodynamics.clustering.dtw import pairwise_distance
```

**Target content** (per RESEARCH.md Pattern 1, D-01/D-02/D-03/D-05 — remove both `.text` imports, add `__all__` of exactly 8 core symbols):
```python
__version__ = "0.1.0"

from infodynamics.clustering import SignalClusterer
from infodynamics.pipeline import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.scalogram import (
    FooteNovelty,
    Scalogram,
    self_similarity_matrix,
    structure_descriptors,
)
from infodynamics.time_series import WindowedRollingDistance

__all__ = [
    "InfoDynamics",
    "MultiscaleInfoDynamics",
    "WindowedRollingDistance",
    "Scalogram",
    "FooteNovelty",
    "SignalClusterer",
    "self_similarity_matrix",
    "structure_descriptors",
]
```

**Hard constraint (D-05):** zero occurrences of `from .text import` / `from infodynamics.text import` anywhere in this file. Verify with:
```bash
grep -n "from \.text import\|from infodynamics\.text import" infodynamics/__init__.py
# must exit 1 (no matches)
```

---

### `infodynamics/text/__init__.py` (config, transform)

**Analog:** `infodynamics/clustering/__init__.py` (same curated re-export pattern) + this file's own current content (extend, don't replace, its existing 2 imports)

**Current full content** (`infodynamics/text/__init__.py:1-6`):
```python
"""infodynamics.text — text on-ramp (segmentation, embedding, morphological encoding).

__all__ curation is deferred to a later phase (API-03/API-04).
"""
from infodynamics.text.pipeline import TextInfoDynamics, TextMultiscaleInfoDynamics
from infodynamics.text.segmentation import TextSegmenter
```

**Target content** (per RESEARCH.md Pattern 1 / CONTEXT.md's Claude's-discretion note — fold in the 4 D-05-displaced symbols plus `Encoder`, update docstring to remove the "deferred" note):
```python
"""infodynamics.text — text on-ramp (segmentation, embedding, morphological encoding)."""
from infodynamics.text.embedding import Encoder
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.text.pipeline import TextInfoDynamics, TextMultiscaleInfoDynamics
from infodynamics.text.segmentation import Chunk, TextSegmenter, segment, strip_markdown

__all__ = [
    "TextInfoDynamics",
    "TextMultiscaleInfoDynamics",
    "TextSegmenter",
    "Encoder",
    "MorphologicalEncoder",
    "Chunk",
    "segment",
    "strip_markdown",
]
```

---

### `tests/text/test_morphology.py` (test, request-response — import fix)

**Analog:** self (single-line import path change, verified as the only broken call site by RESEARCH.md's repo-wide sweep)

**Current** (`tests/text/test_morphology.py:10`):
```python
from infodynamics import MorphologicalEncoder  # noqa: E402
```

**Target:**
```python
from infodynamics.text import MorphologicalEncoder  # noqa: E402
```

No other lines in this file need to change (lines 8, 11, 12 already import from correct paths — `spacy.tokens`, `infodynamics.text.morphology.encode_all_feature_groups`, `infodynamics.text.TextMultiscaleInfoDynamics`).

**No other call sites need fixing** — RESEARCH.md's Pitfall 2 section confirms `tests/test_pipeline_composition.py` and `tests/golden/capture_baseline.py` use multi-line `from infodynamics import (...)` blocks but neither imports any of the 4 migrating symbols. Re-verify with a grep sweep before finalizing, but do not assume new call sites beyond this one.

---

### `tests/test_public_api.py` (test, request-response — new)

**Analog:** `tests/test_viz.py` (existing precedent for `from infodynamics import <submodule>` style access, proving submodule reachability without `__all__` inclusion — role-match: both are lightweight import/attribute assertion tests, not fixture-heavy)

**Full target content** (already fully specified in RESEARCH.md's Verification Mechanics section, copy verbatim):
```python
import infodynamics
import infodynamics.text


def test_core_all_matches_expected_symbols():
    expected = {
        "InfoDynamics", "MultiscaleInfoDynamics", "WindowedRollingDistance",
        "Scalogram", "FooteNovelty", "SignalClusterer",
        "self_similarity_matrix", "structure_descriptors",
    }
    assert set(infodynamics.__all__) == expected
    for name in infodynamics.__all__:
        assert hasattr(infodynamics, name), f"{name} in __all__ but not importable"


def test_core_init_has_no_text_imports():
    import inspect
    source = inspect.getsource(infodynamics)
    assert ".text" not in source, "infodynamics/__init__.py must not import from .text (D-05)"


def test_text_all_matches_expected_symbols():
    expected = {
        "TextInfoDynamics", "TextMultiscaleInfoDynamics", "TextSegmenter",
        "Encoder", "MorphologicalEncoder", "Chunk", "segment", "strip_markdown",
    }
    assert set(infodynamics.text.__all__) == expected
    for name in infodynamics.text.__all__:
        assert hasattr(infodynamics.text, name), f"{name} in __all__ but not importable"
```

**Note:** unlike most tests in `tests/`, this one deliberately imports the package under test wholesale (`import infodynamics`) rather than specific symbols — matches `tests/test_viz.py`'s `from infodynamics import viz` precedent of exercising the package surface directly rather than individual functions.

---

### `examples/basic_usage.py` (utility/docs, batch script — new, no in-repo analog)

**No close analog exists** — `examples/` directory does not exist yet, and the repo's existing root-level demo scripts (`run_morphology_demo.py`, `run_multiscale_demo.py`, `run_scalogram_demo.py`, `segmentation_demo.py`, `descriptors_analysis.py`, `shit.py`) are explicitly out of scope to repurpose (PROJECT.md, CONTEXT.md boundary note). They may still be read for their **import style** (how they call `InfoDynamics`/`MultiscaleInfoDynamics`) as loose inspiration, but the new file must not be a rename or copy of any of them.

**Structural requirement (from RESEARCH.md Recommended Project Structure + Pitfall notes):**
- Plain runnable script, module docstring, `if __name__ == "__main__":` guard — no sphinx-gallery scaffolding.
- Two demonstrated paths:
  1. **Core-only:** construct a numeric `ndarray`/embedding matrix directly, feed into `InfoDynamics`/`MultiscaleInfoDynamics` — imports only from `infodynamics` (the curated 8-symbol `__all__`), zero `infodynamics.text` imports.
  2. **Full `Pipeline` composition:** text on-ramp (`infodynamics.text.TextInfoDynamics` or `TextMultiscaleInfoDynamics`, which internally wire `TextSegmenter` + `Encoder`) → analysis — imports from `infodynamics.text`.
- Must be a new tracked file at `examples/basic_usage.py`, not added as an installable package (no `__init__.py` in `examples/`).

---

### `CHANGELOG.md` (config/docs — new, no in-repo analog)

**No analog exists** — no `CHANGELOG.md`/`MIGRATION.md` present. README.md exists but is empty (do not fold content into it, per CONTEXT.md discretion note).

**Required content shape** (flat old→new import-path table, NOT Keep-a-Changelog prose sections, per RESEARCH.md's Alternatives Considered):
- One row per symbol that moved across this milestone's phases (Phase 2 reorg, Phase 3 `Text*` wrapper additions, this phase's `__all__` curation).
- Minimum symbols to cover based on this phase's D-05 change: `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown` (old: `from infodynamics import X` → new: `from infodynamics.text import X`), plus `Encoder` (newly public via `infodynamics.text`, wasn't reachable at package level before).
- Source data for the full historical table: `.planning/STATE.md` Decisions log (Phase 2/3 moves) plus the current vs. target re-export lists captured above in this document.

## Shared Patterns

### Curated re-export `__init__.py` style
**Source:** `infodynamics/clustering/__init__.py` (all 3 lines)
**Apply to:** `infodynamics/__init__.py`, `infodynamics/text/__init__.py`
```python
from infodynamics.clustering.barycenter import average as barycenter_average
from infodynamics.clustering.cluster import SignalClusterer
from infodynamics.clustering.dtw import pairwise_distance
```
Plain `from module import Name` imports, no aliasing (no linter configured in this repo — confirmed via CLAUDE.md), each `__init__.py` ends with an explicit `__all__` list enumerating every re-exported name once.

### Submodule reachability without top-level export (D-02/D-03/D-04)
**Source:** `tests/test_viz.py:11` — `from infodynamics import viz` already works today with no `__all__` present, proving `__all__` does not gate `from package import submodule` — only `from package import *`.
**Apply to:** Verification of `infodynamics.viz.*`, `infodynamics.metrics.*`, `infodynamics.scalogram.checkerboard_kernel`/`foote_novelty`/`rolling_gap_distance`, `infodynamics.clustering.barycenter_average`/`pairwise_distance` all remaining reachable after the `__init__.py` rewrites, despite not appearing in the new `__all__` lists. Sanity-check both before and after with:
```bash
python -c "from infodynamics import viz; from infodynamics import scalogram; from infodynamics.clustering import barycenter_average"
```

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `examples/basic_usage.py` | utility/docs | batch | No `examples/` directory exists yet; existing root demo scripts are explicitly out-of-scope to repurpose. Use RESEARCH.md's Architecture Patterns / Code Examples sections as the structural template instead. |
| `CHANGELOG.md` | config/docs | transform | No changelog/migration doc exists yet in this repo. Use RESEARCH.md's Alternatives Considered guidance (flat old→new table format) as the template. |

## Metadata

**Analog search scope:** `infodynamics/`, `infodynamics/text/`, `infodynamics/clustering/`, `tests/`, `tests/text/`, repo root (for examples/changelog precedent — none found)
**Files scanned:** `infodynamics/__init__.py`, `infodynamics/text/__init__.py`, `infodynamics/clustering/__init__.py`, `tests/text/test_morphology.py`, `tests/test_viz.py`, repo root listing
**Pattern extraction date:** 2026-07-14

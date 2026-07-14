# Phase 2: Reorganize Into Core + Text On-Ramp - Research

**Researched:** 2026-07-14
**Domain:** Python package reorganization (`git mv` refactor), sklearn-compatible library boundary enforcement
**Confidence:** HIGH

## Summary

This phase is a pure relocation: `segmentation.py`, `embedding.py`, and `morphology.py` move from `infodynamics/` to `infodynamics/text/`, with mirrored tests under `tests/text/`. No new libraries, no algorithmic changes — the entire research task was an exhaustive, tool-verified call-site inventory of every place in the repository that imports these three modules or their public symbols, so the planner can enumerate every file that needs a one-line import-path fix (and no more).

The inventory (Step 3 below) found the scope is smaller than it might appear: **only 5 tracked files** need import-path edits (`infodynamics/__init__.py`, `infodynamics/pipeline.py`, `tests/test_segmentation.py`→`tests/text/`, `tests/test_morphology.py`→`tests/text/`, `tests/golden/capture_baseline.py`), plus one newly-tracked file surfaced by this research that CONTEXT.md and the ROADMAP did not mention: **`benchmark_embedding.py`** (tracked in git, at repo root, imports both `infodynamics.embedding` and `infodynamics.segmentation` directly) — see Open Questions. `infodynamics/clustering/*.py` and all other core modules (`scalogram.py`, `time_series.py`, `metrics.py`, `util.py`, `viz.py`) already have **zero** references to the moving modules — CORE-01's "no core→text dependency" is already true for everything except `pipeline.py` (the documented D-01/D-02 exception).

Two mechanical facts were verified directly (not assumed) and materially de-risk the plan: (1) `setuptools.find_packages()` auto-discovers `infodynamics.text` with **no `setup.py` edit required**, confirmed by running it against a scratch package layout; (2) the repo's PEP 660 editable install uses a dynamic per-directory `MAPPING` + `PathFinder` delegation (not a static per-file map), so `git mv` inside `infodynamics/` **will not** break `pip install -e .`'s import resolution — no reinstall is needed for functional correctness, only `infodynamics.egg-info/SOURCES.txt` (build metadata, irrelevant until packaging, which is explicitly out of scope this milestone) goes cosmetically stale.

**Primary recommendation:** Treat this as two mechanical passes — (1) `git mv` the three files + their two test files into `infodynamics/text/` and `tests/text/`, add the two new `__init__.py` files; (2) fix exactly the 5 known import-path call sites plus decide on `benchmark_embedding.py` — then run the full verification suite (grep sweep, no-extras smoke test, full pytest, golden-baseline diff) as the phase gate, not per-task.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `pipeline.py` stays at `infodynamics/pipeline.py` (does NOT move to `infodynamics/text/`). Its imports are updated to full submodule paths: `from infodynamics.text.embedding import Encoder` and `from infodynamics.text.segmentation import Level, segment`. This is a **deliberate, documented interim exception** — `pipeline.py` is core per CORE-01 and per the ROADMAP's own module list, but it isn't actually decoupled from text until Phase 3.
- **D-02:** ROADMAP.md Phase 2 success criterion 3 (grep for `infodynamics.text` imports across `infodynamics/*.py` excluding `infodynamics/text/`, expecting zero hits) needs a one-line amendment during planning to explicitly exclude `infodynamics/pipeline.py`, with a note that Phase 3 resolves it. Flag this to the planner — don't silently violate a written success criterion.
- **D-03:** `infodynamics/text/__init__.py` does NOT re-export symbols this phase (no `Chunk`/`segment`/`Encoder`/`MorphologicalEncoder` re-exports at the `infodynamics.text` level yet). All internal call sites import from full submodule paths.
- **D-04:** `infodynamics/__init__.py`'s existing top-level re-exports (`Chunk`, `segment`, `strip_markdown`, `MorphologicalEncoder`) keep working this phase — only their import *paths* change to point at `infodynamics.text.*`.
- **D-05:** `tests/test_segmentation.py` → `tests/text/test_segmentation.py`; `tests/test_morphology.py` → `tests/text/test_morphology.py`; add `tests/text/__init__.py`.
- **D-06:** `tests/golden/capture_baseline.py`'s import (`from infodynamics.embedding import Encoder`) is updated to `from infodynamics.text.embedding import Encoder` as part of this phase's mechanical path fixes.
- **D-07:** There is no `tests/test_embedding.py` today (pre-existing test-coverage gap) — not this phase's job to add one.
- **D-08:** `tests/golden/` itself does NOT move under `tests/text/` — it covers all six estimators (core + text).

### Claude's Discretion

User delegated both primary gray areas ("You decide") and confirmed the test-layout follow-up as "obvious mirror is fine." Claude has full discretion on any remaining mechanical details not explicitly decided above (e.g., exact commit granularity, whether to squash the `git mv` + import-fix into one commit or split them) as long as the phase stays a pure move with zero numerical/behavioral drift.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. No scope-creep items surfaced; both delegated decisions and the test-layout confirmation were all within the phase's "pure move" boundary.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEXT-01 | `segmentation`, `embedding`, and `morphology` are relocated under an `infodynamics.text` subpackage | Step 3 inventory confirms exact source files and their current sizes/imports (segmentation.py 107 lines, embedding.py 53 lines, morphology.py 195 lines); confirmed `find_packages()` auto-discovers the new subpackage with no `setup.py` edit |
| TEXT-03 | Heavy optional deps imported lazily; `import infodynamics` / `import infodynamics.text` succeed without them | Verified (quoted below) that `sentence_transformers`, `spacy_udpipe`, `textdescriptives` are already imported inside function/method bodies, not at module top level — TEXT-03 is mechanically already true post-move, not new work |
| CORE-01 | Core modules import nothing from `infodynamics.text` | Verified via full-repo grep: `infodynamics/clustering/*.py`, `scalogram.py`, `time_series.py`, `metrics.py`, `util.py`, `viz.py` have zero references to segmentation/embedding/morphology today; only `pipeline.py` does (the documented D-01/D-02 exception) |

## Architectural Responsibility Map

This is a library, not a web app — "tiers" here map to the package boundary this milestone is building, not browser/server layers.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Text segmentation (`segment`, `Chunk`, `strip_markdown`) | `infodynamics.text` | — | TEXT-01: relocates here verbatim |
| Sentence embedding (`Encoder`) | `infodynamics.text` | — | TEXT-01: relocates here verbatim |
| Morphological encoding (`MorphologicalEncoder`, `encode_all_feature_groups`) | `infodynamics.text` | — | TEXT-01: relocates here verbatim |
| Pipeline orchestration (`InfoDynamics`, `MultiscaleInfoDynamics`) | `infodynamics` (core) | `infodynamics.text` (interim import dependency) | CORE-01 says core, but D-01 documents pipeline.py's live import of `infodynamics.text.embedding`/`infodynamics.text.segmentation` as an interim exception until Phase 3 |
| Multi-scale/DTW/clustering analysis (`scalogram.py`, `time_series.py`, `clustering/`) | `infodynamics` (core) | — | Verified zero references to text modules already; numeric-only inputs |
| Public export surface (`infodynamics/__init__.py`) | `infodynamics` (core) | `infodynamics.text` (via re-export, D-04) | Re-exports `Chunk`/`segment`/`strip_markdown`/`MorphologicalEncoder` from `infodynamics.text.*`; curating this further is Phase 4 (API-03) |
| Package discovery / build metadata | Build tooling (`setup.py`) | — | Verified `find_packages()` auto-discovers `infodynamics.text` — no edit needed |

## Standard Stack

No new libraries are introduced by this phase — it is a pure file relocation. The existing stack (numpy, scikit-learn, matplotlib, syntok, typing-extensions as `install_requires`; sentence-transformers/spacy-udpipe/textdescriptives/tslearn/scipy as optional extras) is unchanged. `setup.py`'s `extras_require` dict does not need edits — none of its entries reference file paths, only package names.

**Installation:** No new installs required for this phase.

## Package Legitimacy Audit

**Not applicable this phase.** No external packages are introduced, upgraded, or newly declared. `setup.py`'s dependency list is unchanged by a pure `git mv`.

## Architecture Patterns

### System Architecture Diagram (target state, end of Phase 2)

```
                    ┌─────────────────────────────────────────┐
                    │   infodynamics/__init__.py (core)        │
                    │   re-exports (D-04, paths updated):      │
                    │   Chunk, segment, strip_markdown,        │
                    │   MorphologicalEncoder  ──────────┐      │
                    └───────────┬────────────────────────┼─────┘
                                │ imports (unchanged)     │ imports (path updated)
                                ▼                         ▼
        ┌──────────────────────────────────┐   ┌──────────────────────────────────┐
        │  infodynamics/ (core, numeric)     │   │  infodynamics/text/ (on-ramp)     │
        │  scalogram.py, time_series.py,     │   │  segmentation.py                  │
        │  metrics.py, util.py, viz.py,      │   │  embedding.py  (lazy: sentence-   │
        │  clustering/{cluster,dtw,          │   │                 transformers)     │
        │    barycenter}.py                  │   │  morphology.py (lazy: spacy_udpipe│
        │  -- ZERO imports of text/ (verified)│   │                textdescriptives)  │
        └──────────────────────────────────┘   └──────────────────────────────────┘
                                ▲                         ▲
                                │                         │
                                └──────────┬──────────────┘
                                           │  D-01/D-02 documented interim exception
                                ┌──────────┴──────────────┐
                                │  infodynamics/pipeline.py │
                                │  InfoDynamics,             │
                                │  MultiscaleInfoDynamics    │
                                │  imports:                  │
                                │   infodynamics.text.embedding.Encoder
                                │   infodynamics.text.segmentation.{Level,segment}
                                │  (Phase 3 removes this edge)│
                                └────────────────────────────┘
```

A reader tracing CORE-01 compliance: every arrow into `infodynamics/text/` originates either from `infodynamics/__init__.py` (a documented, path-updated re-export, D-04) or from `infodynamics/pipeline.py` (the documented D-01/D-02 exception). No other core module has an edge into `infodynamics/text/` — verified, not assumed (see Step 3 inventory).

### Recommended Project Structure (after this phase)
```
infodynamics/
├── __init__.py              # re-exports updated to infodynamics.text.* paths (D-04)
├── pipeline.py               # imports infodynamics.text.* (D-01 interim exception)
├── metrics.py                # unchanged
├── time_series.py            # unchanged
├── scalogram.py               # unchanged
├── viz.py                    # unchanged
├── util.py                   # unchanged
├── clustering/                # unchanged, zero text/ imports
│   ├── __init__.py
│   ├── cluster.py
│   ├── dtw.py
│   └── barycenter.py
└── text/                     # NEW subpackage (TEXT-01)
    ├── __init__.py            # NEW, empty for now (D-03 — no re-exports yet)
    ├── segmentation.py        # git mv'd from infodynamics/segmentation.py, unchanged content
    ├── embedding.py           # git mv'd from infodynamics/embedding.py, unchanged content
    └── morphology.py          # git mv'd from infodynamics/morphology.py, unchanged content

tests/
├── golden/                    # unchanged location (D-08), only capture_baseline.py's
│   ├── __init__.py            #   Encoder import path updated (D-06)
│   ├── capture_baseline.py
│   ├── baseline_arrays.npz
│   └── baseline_meta.json
├── test_infodynamics_class.py # unchanged
├── test_pipeline.py           # unchanged (patches infodynamics.pipeline.Encoder by attribute name, not import path)
├── test_scalogram.py          # unchanged
├── test_clustering.py         # unchanged
├── test_metrics.py            # unchanged
├── test_viz.py                # unchanged
├── test_golden_baseline.py    # unchanged
└── text/                      # NEW mirror directory (D-05)
    ├── __init__.py             # NEW, empty
    ├── test_segmentation.py    # git mv'd from tests/test_segmentation.py, import path updated
    └── test_morphology.py      # git mv'd from tests/test_morphology.py, import path updated
```

### Pattern 1: Lazy heavy-dependency import (preserve verbatim, don't rework)
**What:** `sentence_transformers`, `spacy_udpipe`, `textdescriptives` are imported inside function/method bodies, not at module top level, guarded by `try/except ImportError` that re-raises with an actionable `pip install infodynamics[extra]` message.
**When to use:** Already the established pattern in this codebase for every optional heavy dependency (including `tslearn` in `clustering/barycenter.py` and `clustering/dtw.py`) — TEXT-03 asks this to remain true after the move, not be re-implemented.
**Verified locations (exact, quoted):**
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
`spacy_udpipe`/`textdescriptives` are also lazily imported at `morphology.py:71`, `morphology.py:110-117`, `morphology.py:125-131`, and `morphology.py:186` (inside `MorphologicalEncoder.encode()`). No occurrence of these three package names exists at module top level in either file — confirmed by reading both files in full.

**Module-level imports that DO stay at top level** (not heavy, not optional — `install_requires`, not `extras_require`): `infodynamics/text/segmentation.py` imports `re`, `dataclasses`, `typing` at top level, and lazily imports `syntok.segmenter` inside `_sentence_parts()` (syntok is a required dependency, so this is a bonus, not a TEXT-03 requirement).

### Anti-Patterns to Avoid
- **Adding a backward-compat shim module** (e.g. a stub `infodynamics/segmentation.py` that re-imports from `infodynamics.text.segmentation`): explicitly out of scope per REQUIREMENTS.md ("Backward-compatible import paths / deprecation shims" — breaking changes accepted pre-1.0). Don't add one even for the untracked demo scripts (see Open Questions).
- **Reinstalling to "fix" the editable install after `git mv`:** unnecessary — verified the PEP 660 finder maps only the top-level `infodynamics` directory and delegates nested-module resolution to the filesystem via `PathFinder`, so newly-created `infodynamics/text/*.py` files are importable immediately without `pip install -e .` again. (A reinstall is harmless but not required for correctness — see Runtime State Inventory.)
- **Editing `setup.py`'s `packages=find_packages()` call:** unnecessary — verified `find_packages()` auto-discovers any directory with `__init__.py`, including the new `infodynamics/text/`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Making `infodynamics.text` importable as a package after the move | Manual `packages=[...]` list in `setup.py` | `find_packages()` (already used, verified to auto-discover) | Confirmed via direct execution: `find_packages()` against a scratch `mypkg/text/` layout with `__init__.py` returns `['mypkg', 'mypkg.text']` with zero configuration |
| Preserving git history across the move | Copy file contents + delete old file | `git mv` (or stage as rename — git detects renames automatically on >50% content similarity, which is 100% here since content is byte-identical) | `git log --follow` on the new path recovers full pre-move history; a copy+delete loses the rename-tracking convenience (though the blob history is still technically recoverable via similarity detection) |
| Verifying the "no heavy extras" import succeeds | Manually uninstalling packages from the working `.venv` and reinstalling after the check | A throwaway `python -m venv` with only `install_requires` packages installed | The working `.venv` already has all extras installed (verified: sentence-transformers 5.6.0, spacy-udpipe 1.0.0, textdescriptives 2.8.2, tslearn 0.9.0, scipy 1.18.0 all present) — mutating it to test the no-extras path risks leaving the dev environment in a broken state for later phases |

**Key insight:** Every mechanical concern this phase might worry about (package discovery, editable-install resolution, git history) already has a built-in, zero-configuration answer in the existing toolchain — the actual work is the file moves plus five import-path edits.

## Runtime State Inventory

*Triggered: this is a rename/refactor (`git mv`) phase.*

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database, no datastore keys reference `infodynamics.segmentation`/`embedding`/`morphology` by name. `_MODEL_CACHE` (embedding.py) and `_PIPELINE_CACHE` (morphology.py) are in-process Python dicts keyed by model name/lang tuples, not module paths; they are reset on every process start regardless of file location. | None |
| Live service config | None — Phase 1 already removed `dashboard/` and its cache/manifest system; no external service (n8n, Datadog, etc.) is part of this repo. | None |
| OS-registered state | None — no `pm2`, `launchd`, `systemd`, or Task Scheduler entries reference these module names; this is a library repo, not a daemon. | None |
| Secrets/env vars | None — no `.env`, no SOPS keys, no CI/CD env var names reference `segmentation`/`embedding`/`morphology` by string. `setup.py` has no `console_scripts` entry points referencing these modules (those were removed in Phase 1 — RM-03). | None |
| Build artifacts / installed packages | `infodynamics.egg-info/SOURCES.txt` lists the pre-move flat paths (`infodynamics/embedding.py`, `infodynamics/morphology.py`, `infodynamics/segmentation.py`) — **verified this file is build metadata only** (used for sdist/wheel manifests), not consulted at import time. **The editable-install finder (`.venv/lib/python3.14/site-packages/__editable___infodynamics_0_1_0_finder.py`) does NOT need regeneration** — its `MAPPING` dict maps only the top-level `infodynamics` directory (`{'infodynamics': '/Users/janko/Repositories/infodynamics/infodynamics'}`) and delegates all nested-module resolution to `importlib.machinery.PathFinder` against the filesystem, so `infodynamics.text.segmentation` etc. resolve automatically post-`git mv` with zero reinstall. Optional hygiene: `pip install -e .` again to refresh `SOURCES.txt` (cosmetic only, not required for tests to pass; packaging is out of scope this milestone per REQUIREMENTS.md). |

## Common Pitfalls

### Pitfall 1: Missing `infodynamics/pipeline.py`'s two docstring references
**What goes wrong:** `pipeline.py` has two prose docstring mentions of `infodynamics.embedding.Encoder or infodynamics.morphology.MorphologicalEncoder` (lines 46 and 188, in the `encoder` parameter docs of both `InfoDynamics.__init__` and `MultiscaleInfoDynamics.__init__`). These are not executable imports, so they won't break tests or fail the grep sweep (the grep sweep looks for `from`/`import` statements, and these are prose inside a docstring using dotted-name notation without an `import` keyword) — but leaving them pointing at the pre-move paths is a documentation drift the planner should fix in the same commit as the functional import-path edit, for consistency.
**Why it happens:** Easy to update the two functional `from infodynamics.embedding import Encoder` / `from infodynamics.segmentation import Level, segment` lines (10, 12) and miss that the same file also *mentions* the old paths in prose twice.
**How to avoid:** Include the docstring lines in the same find/replace pass as the functional import lines when editing `pipeline.py`.
**Warning signs:** `grep -n "infodynamics\.embedding\|infodynamics\.morphology" infodynamics/pipeline.py` after the edit should return zero hits (only `infodynamics.text.embedding`/`infodynamics.text.morphology` should remain).

### Pitfall 2: `tests/test_morphology.py`'s two-line import split
**What goes wrong:** `tests/test_morphology.py` has two separate import statements referencing the moving code — line 11 `from infodynamics import MorphologicalEncoder` (top-level re-export, **does not need editing**, works automatically once `infodynamics/__init__.py` is fixed per D-04) and line 12 `from infodynamics.morphology import encode_all_feature_groups` (**does need editing** to `from infodynamics.text.morphology import encode_all_feature_groups`, since `encode_all_feature_groups` is a module-level function, not currently re-exported at the top of `infodynamics/__init__.py`). It's easy to "fix" one and assume the file is done.
**Why it happens:** The two imports look similar but resolve differently — one goes through the package's re-export surface, one goes direct-to-submodule.
**How to avoid:** After editing, run `python -c "import ast; ..."` or simply grep the specific file for the old module path string after the edit.
**Warning signs:** `ModuleNotFoundError: No module named 'infodynamics.morphology'` when running `tests/text/test_morphology.py` post-move if line 12 is missed.

### Pitfall 3: Assuming `tests/golden/capture_baseline.py`'s determinism self-check re-runs full pytest coverage
**What goes wrong:** `capture_baseline.py` has an `if __name__ == "__main__":` block that recomputes the golden snapshot and includes its own assertions (determinism, NaN/Inf checks, scale/radii-survival checks) — this only runs when the script is executed directly (`python tests/golden/capture_baseline.py`), NOT when pytest imports it as a module (which `tests/test_golden_baseline.py` does, at module import time, calling only `compute_outputs()`). Fixing the `Encoder` import (D-06) is required for **both** paths, but the planner should not assume running `pytest` alone re-validates the `__main__` block's extra self-checks — it doesn't execute that code path.
**Why it happens:** The file serves two purposes (one-time capture script + shared fixture-computation module) and only one of `pytest`'s import paths exercises the module-level code, not the `__main__` guard.
**How to avoid:** The phase gate only needs `pytest -q` to pass (it exercises `compute_outputs()` via `tests/test_golden_baseline.py`); re-running `python tests/golden/capture_baseline.py` directly is optional extra verification, not required by any of the 4 ROADMAP success criteria, and should NOT regenerate `baseline_arrays.npz`/`baseline_meta.json` in this phase (that would be a behavior/output change, violating "zero behavior change").
**Warning signs:** Don't re-run `capture_baseline.py`'s `__main__` block and let it overwrite `baseline_arrays.npz` — that file must stay byte-identical this phase (it's the pre-move ground truth the golden test compares against).

### Pitfall 4: `find_packages()` silently including unwanted directories
**What goes wrong:** Not applicable to this specific move (verified `find_packages()` only picks up `infodynamics.text` because it has `__init__.py`), but worth flagging: if the planner accidentally leaves a stray `__init__.py` in a demo-output directory (e.g. `morphology_demo_output/`) it would get picked up by `find_packages()` too. Not currently an issue (none of those directories have `__init__.py`, confirmed via `find`), but a spot-check after adding the two new `__init__.py` files is cheap insurance.
**Why it happens:** `find_packages()` has no allowlist by default — any directory with `__init__.py` anywhere under the repo root is a candidate package.
**How to avoid:** `python -c "from setuptools import find_packages; print(find_packages())"` after the move should print exactly `['infodynamics', 'infodynamics.clustering', 'infodynamics.text']` — no more, no less.
**Warning signs:** An unexpected extra entry in that list.

## Code Examples

### Exact current import lines requiring a path change (verified by direct file read)

```python
# infodynamics/pipeline.py:10,12 (BEFORE — verified exact current lines)
from infodynamics.embedding import Encoder
from infodynamics.scalogram import FooteNovelty, Scalogram, structure_descriptors
from infodynamics.segmentation import Level, segment
from infodynamics.time_series import WindowedRollingDistance

# AFTER (per D-01)
from infodynamics.text.embedding import Encoder
from infodynamics.scalogram import FooteNovelty, Scalogram, structure_descriptors
from infodynamics.text.segmentation import Level, segment
from infodynamics.time_series import WindowedRollingDistance
```

`pipeline.py`'s `fit()` call sites for `segment()`/`Encoder.encode()` (verified, confirms CONTEXT.md's canonical_refs claim exactly):
```python
# infodynamics/pipeline.py:103-105 (InfoDynamics.fit)
chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
encoder = self.encoder if self.encoder is not None else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
embeddings = encoder.encode([chunk.text for chunk in chunks])

# infodynamics/pipeline.py:243-245 (MultiscaleInfoDynamics.fit) — identical pattern
chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
encoder = self.encoder if self.encoder is not None else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
embeddings = encoder.encode([chunk.text for chunk in chunks])
```
These call sites are unaffected by the import-path change (the bound names `segment`/`Encoder` stay the same inside `pipeline.py`'s namespace) — Phase 3 is what removes these calls, not Phase 2.

```python
# infodynamics/__init__.py (BEFORE — verified exact current file, 8 lines total)
__version__ = "0.1.0"

from infodynamics.clustering import SignalClusterer
from infodynamics.morphology import MorphologicalEncoder
from infodynamics.pipeline import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.scalogram import FooteNovelty, Scalogram, self_similarity_matrix, structure_descriptors
from infodynamics.segmentation import Chunk, segment, strip_markdown
from infodynamics.time_series import WindowedRollingDistance

# AFTER (per D-04 — only these two lines' RHS path changes)
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.text.segmentation import Chunk, segment, strip_markdown
```

```python
# tests/test_segmentation.py:4 (BEFORE)
from infodynamics.segmentation import Chunk, segment, strip_markdown
# AFTER, file relocated to tests/text/test_segmentation.py
from infodynamics.text.segmentation import Chunk, segment, strip_markdown
```

```python
# tests/test_morphology.py:11-12 (BEFORE)
from infodynamics import MorphologicalEncoder  # noqa: E402          <- NO CHANGE (re-export)
from infodynamics.morphology import encode_all_feature_groups  # noqa: E402   <- CHANGE
# AFTER, file relocated to tests/text/test_morphology.py
from infodynamics import MorphologicalEncoder  # noqa: E402
from infodynamics.text.morphology import encode_all_feature_groups  # noqa: E402
```

```python
# tests/golden/capture_baseline.py:34 (BEFORE)
from infodynamics.embedding import Encoder
# AFTER (D-06; file location unchanged, D-08)
from infodynamics.text.embedding import Encoder
```

### Full exhaustive grep inventory (ground truth, run against entire repo excluding `.venv/`)

```bash
grep -rn "infodynamics\.segmentation\|infodynamics\.embedding\|infodynamics\.morphology" --include="*.py" . | grep -v "\.venv/"
```
Result (verbatim, 16 matches across 8 files):
```
run_multiscale_demo.py:39:from infodynamics.segmentation import Level                          # UNTRACKED, out of scope
run_morphology_demo.py:39:from infodynamics.segmentation import Level                           # UNTRACKED, out of scope
benchmark_embedding.py:4: (docstring prose mention)                                              # TRACKED — see Open Questions
benchmark_embedding.py:31:from infodynamics.embedding import Encoder                             # TRACKED — see Open Questions
benchmark_embedding.py:32:from infodynamics.segmentation import segment                          # TRACKED — see Open Questions
segmentation_demo.py:2:from infodynamics.segmentation import segment                             # UNTRACKED, out of scope
tests/test_segmentation.py:4:from infodynamics.segmentation import Chunk, segment, strip_markdown  # FIX (D-05, then relocate)
tests/test_morphology.py:12:from infodynamics.morphology import encode_all_feature_groups         # FIX (D-05, then relocate)
tests/test_pipeline.py:15: (docstring prose mention only, no import)                              # NO CHANGE
tests/golden/capture_baseline.py:34:from infodynamics.embedding import Encoder                    # FIX (D-06)
infodynamics/__init__.py:4:from infodynamics.morphology import MorphologicalEncoder               # FIX (D-04)
infodynamics/__init__.py:7:from infodynamics.segmentation import Chunk, segment, strip_markdown   # FIX (D-04)
infodynamics/pipeline.py:10:from infodynamics.embedding import Encoder                            # FIX (D-01)
infodynamics/pipeline.py:12:from infodynamics.segmentation import Level, segment                  # FIX (D-01)
infodynamics/pipeline.py:46: (docstring prose mention)                                            # FIX (hygiene, Pitfall 1)
infodynamics/pipeline.py:188: (docstring prose mention)                                           # FIX (hygiene, Pitfall 1)
```
No relative-import forms (`from .segmentation`, `from .embedding`, `from .morphology`) exist anywhere in the repo — verified separately, zero matches. No bare `import segmentation`/`import embedding`/`import morphology` (unqualified) exist anywhere — verified separately, zero matches.

**Files confirmed to have ZERO references** (verified by reading each in full or by the grep above returning no hits for them): `infodynamics/clustering/__init__.py`, `infodynamics/clustering/cluster.py`, `infodynamics/clustering/dtw.py`, `infodynamics/clustering/barycenter.py`, `infodynamics/scalogram.py`, `infodynamics/time_series.py`, `infodynamics/metrics.py`, `infodynamics/util.py`, `infodynamics/viz.py`, `tests/test_infodynamics_class.py`, `tests/test_clustering.py`, `tests/test_scalogram.py`, `tests/test_metrics.py`, `tests/test_viz.py`, `tests/golden/__init__.py` (this file is empty — 0 lines), `setup.py` (its `extras_require` dict has no file-path references, only PyPI package names), `descriptors_analysis.py`, `radomil_texts_to_csv.py`, `scalogram_foote_prototype.py` (defines its own local `strip_markdown`, does not import the package's), `shit.py` (imports `infodynamics.pipeline`, `infodynamics.viz`, `infodynamics.clustering.cluster` — all unaffected top-level/submodule imports that don't touch the three moving modules).

## State of the Art

Not applicable — this is an internal file reorganization with no external-facing API or library-version dependency, so there is no "old approach vs. current approach" industry pattern to compare against. The one relevant piece of tooling knowledge (setuptools `find_packages()` auto-discovery, PEP 660 editable-install dynamic path resolution) was verified directly rather than researched externally, and both are documented, stable, long-standing setuptools/pip behaviors (no recent deprecation or change).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `benchmark_embedding.py` is not exercised by the pytest suite or by any CI/tooling that would surface a failure if its imports are left stale | Open Questions | Low — verified by grep that no test file imports `benchmark_embedding`; it's a standalone script. If wrong, a hidden test dependency would surface as an unexpected collection error, which the phase gate's `pytest --collect-only -q` would catch anyway. |

*This log is short because nearly every claim in this document was directly verified against the live codebase via `grep`/`Read`/tool execution during this research session, not drawn from training knowledge — see per-section "(verified ...)" annotations throughout.*

## Open Questions

1. **`benchmark_embedding.py` is tracked in git but not covered by any CONTEXT.md decision or ROADMAP success criterion.**
   - What we know: `git ls-files` confirms `benchmark_embedding.py` is a tracked, committed file at the repo root. It directly imports `from infodynamics.embedding import Encoder` and `from infodynamics.segmentation import segment` (lines 31-32), plus a docstring prose mention (line 4). ROADMAP success criterion 3 scopes the grep sweep to `infodynamics/*.py` and `infodynamics/clustering/*.py` only — it does not mention root-level tracked scripts. REQUIREMENTS.md's "Out of Scope" table excludes "untracked root clutter (demo scripts...)" by name, but `benchmark_embedding.py` is tracked, so that exclusion doesn't literally cover it.
   - What's unclear: Whether the planner should fix its two import lines (cheap, consistent with "no dangling references" spirit, and it's tracked so leaving it broken would be a regression a future `git grep` audit would flag) or explicitly defer it as out of scope alongside the untracked demo scripts, since it's not named in any locked decision.
   - Recommendation: Fix it in the same pass as the other 5 files — it's a 2-line edit, it's tracked (unlike the explicitly-deferred untracked scripts), and leaving a tracked file with broken imports contradicts the phase's "zero behavior change / no dangling references" spirit even though it's not literally required by ROADMAP criterion 3's narrower grep scope. If the planner disagrees, this should be an explicit, logged decision (like D-01/D-02), not a silent omission.

2. **The untracked demo/prototype scripts at repo root will break after this move (imports will 404) — is that acceptable?**
   - What we know: `run_multiscale_demo.py`, `run_morphology_demo.py`, `segmentation_demo.py` (all untracked per `git status`) import `infodynamics.segmentation`/`infodynamics.embedding` directly and will raise `ModuleNotFoundError` after the move, since REQUIREMENTS.md explicitly rules out backward-compat shims.
   - What's unclear: Nothing — REQUIREMENTS.md's "Out of Scope" table explicitly names this class of file ("Cleanup of untracked root clutter... addressed separately, not this milestone").
   - Recommendation: No action needed this phase. Do not "fix" these files (out of scope) and do not be alarmed if manually running them post-move raises `ModuleNotFoundError` — that is expected and does not indicate a regression in any of the 4 ROADMAP success criteria (none of which touch untracked files).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | Full suite verification (criterion 4) | ✓ | 9.1.1 | — |
| numpy, matplotlib, scikit-learn, syntok, typing-extensions (`install_requires`) | Core import (criterion 2) | ✓ | (installed in `.venv`) | — |
| sentence-transformers, spacy-udpipe, textdescriptives, tslearn, scipy (optional extras) | Golden baseline test, full-extras dev workflow | ✓ (all present in `.venv`: 5.6.0 / 1.0.0 / 2.8.2 / 0.9.0 / 1.18.0) | see versions | — |
| A **fresh venv with no optional extras installed** | ROADMAP criterion 2 ("no optional heavy extras installed") | ✗ (the working `.venv` has everything installed — cannot be used to test this criterion) | — | Planner must create a throwaway venv (`python3 -m venv /tmp/id-no-extras && /tmp/id-no-extras/bin/pip install -e . --no-deps && /tmp/id-no-extras/bin/pip install numpy matplotlib scikit-learn syntok typing-extensions`) and run the import smoke test there. Do not attempt to uninstall extras from the working `.venv` — that would break the golden-baseline test for the rest of this session. |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** A no-extras venv (fallback: create a throwaway one, documented above) — this is expected setup work for verifying criterion 2, not a blocker.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (installed; `setup.py` extras_require['test'] pins `pytest>=6.2.2`) |
| Config file | none — no `pytest.ini`/`setup.cfg`/`pyproject.toml`/`conftest.py` found anywhere in the repo (verified via `find`/`ls`); pytest uses default rootdir-relative discovery |
| Quick run command | `.venv/bin/python -m pytest tests/text/ -q` (post-move; targets only the relocated tests) |
| Full suite command | `.venv/bin/python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEXT-01 | Modules live under `infodynamics/text/`, tests mirrored under `tests/text/` | structural | `test -f infodynamics/text/segmentation.py infodynamics/text/embedding.py infodynamics/text/morphology.py infodynamics/text/__init__.py tests/text/test_segmentation.py tests/text/test_morphology.py tests/text/__init__.py && test ! -e infodynamics/segmentation.py && test ! -e tests/test_segmentation.py` | ✅ (files exist today at old paths; check inverts post-move) |
| TEXT-01 | Test content still passes at new location | unit | `.venv/bin/python -m pytest tests/text/ -q` | ✅ (currently `tests/test_segmentation.py` + `tests/test_morphology.py`, both green today per collection run below) |
| TEXT-03 | `import infodynamics` / `import infodynamics.text` succeed with no heavy extras | smoke | fresh no-extras venv: `python -c "import infodynamics; import infodynamics.text; print('OK')"` | ❌ — no such venv exists yet; must be created per Environment Availability above (Wave 0-equivalent setup step, not new test code) |
| CORE-01 | No core→text import outside the documented `pipeline.py` exception | grep | `grep -rln "from infodynamics\.text\|import infodynamics\.text" infodynamics/*.py infodynamics/clustering/*.py \| grep -v infodynamics/pipeline.py` — expect empty output | ✅ (grep is the test; no file needed) |
| — | Full suite green, no numerical drift | regression | `.venv/bin/python -m pytest -q` — expect 72/72 passing (today's baseline count, verified via `pytest --collect-only -q`), including `tests/test_golden_baseline.py`'s 4 comparison functions unchanged | ✅ `tests/test_golden_baseline.py` exists and currently passes |

### Sampling Rate
- **Per task commit:** Targeted run of the file(s) touched (e.g. `pytest tests/text/test_segmentation.py -q` after that specific move+fix).
- **Per wave merge:** `.venv/bin/python -m pytest -q` (full suite; cheap enough at 72 tests / ~15s collection to run every merge, no need to sample).
- **Phase gate:** All four rows in the map above, run in this order: (1) structural file-existence checks, (2) grep sweep, (3) full pytest suite (includes golden-baseline diff), (4) no-extras smoke test in a throwaway venv.

### Wave 0 Gaps
None — existing test infrastructure (pytest, hypothesis, the golden-baseline harness from Phase 1) fully covers this phase's verification needs. This phase relocates existing test files; it does not require new test framework setup, fixtures, or config.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V1 Architecture | Marginal | The package-boundary enforcement this phase performs (CORE-01: core imports nothing from text) is itself a form of architectural/trust-boundary hygiene, but ASVS V1 targets application security architecture (trust boundaries between untrusted/trusted zones), not internal library module boundaries — not a meaningful fit here. |
| V2 Authentication | No | No auth surface in this library. |
| V3 Session Management | No | No sessions. |
| V4 Access Control | No | No access-controlled resources. |
| V5 Input Validation | No (unchanged) | This phase doesn't touch any input-validation code paths (`segment()`'s `chunk_size < 1` check, `MorphologicalEncoder.__init__`'s `feature_group` allowlist check) — they move file location only, logic is byte-identical. |
| V6 Cryptography | No | Not applicable. |
| V10 Malicious Code | Marginal | The one security-relevant property already in the code (fail-closed `ImportError` with an actionable message when an optional heavy dependency is missing, in `embedding.py`/`morphology.py`) must be preserved verbatim through the move — this is a supply-chain / graceful-degradation control, not a new one to add. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Optional dependency silently missing causes a confusing downstream `AttributeError`/`NameError` instead of a clear error | Information Disclosure (of internal state) / general robustness | Already implemented (`try/except ImportError` re-raising with `pip install infodynamics[extra]` guidance) — this phase's only obligation is to not break or weaken this pattern while relocating the files it lives in. |

No new attack surface is introduced by this phase — it changes file locations and import statements only, with byte-identical logic.

## Sources

### Primary (HIGH confidence — direct tool verification against this repository, ground truth)
- Direct file reads: `infodynamics/pipeline.py`, `infodynamics/__init__.py`, `infodynamics/embedding.py`, `infodynamics/morphology.py`, `infodynamics/segmentation.py`, `infodynamics/clustering/{__init__,cluster,dtw,barycenter}.py`, `tests/test_pipeline.py`, `tests/test_morphology.py`, `tests/golden/capture_baseline.py`, `tests/test_golden_baseline.py`, `tests/golden/__init__.py`, `setup.py`, `shit.py`, `descriptors_analysis.py`
- `grep -rn` sweeps across the entire repository (excluding `.venv/`) for module names, relative-import forms, and public symbol names
- `.venv/bin/python -m pytest --collect-only -q` — confirmed 72 tests collected, zero collection errors, current baseline
- `.venv/bin/python -c "import infodynamics"` — confirmed core imports today (heavy extras happen to be installed in this venv, so this doesn't test the no-extras path)
- `find_packages()` executed against a scratch `mypkg/text/` layout — confirmed `['mypkg', 'mypkg.text']` auto-discovery with zero config
- `.venv/lib/python3.14/site-packages/__editable___infodynamics_0_1_0_finder.py` — read directly, confirmed dynamic `MAPPING` + `PathFinder` delegation (not a static per-file map)
- `.venv/bin/python -m pip list` — confirmed exact installed versions of all optional extras
- `.planning/phases/02-reorganize-into-core-text-on-ramp/02-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/ARCHITECTURE.md` — read in full

### Secondary (MEDIUM confidence)
None used — this phase required no external documentation lookups (no new libraries, no framework changes); every claim was verifiable directly against the live codebase.

### Tertiary (LOW confidence)
None.

## Metadata

**Confidence breakdown:**
- Standard stack: N/A (no new stack) — HIGH by default, nothing to get wrong
- Architecture: HIGH — every import edge was verified by direct grep/read, not inferred
- Pitfalls: HIGH — each pitfall traces to a specific verified line number in the actual codebase
- Package discovery / editable install mechanics: HIGH — verified by direct tool execution (`find_packages()` scratch test, reading the actual finder file), not training-data assumption

**Research date:** 2026-07-14
**Valid until:** Effectively indefinite for this specific inventory (it's a snapshot of the current repo state) — but re-verify the grep inventory if any commits land on this repo between this research and plan execution, since new files could add new call sites.

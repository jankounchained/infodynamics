---
phase: 01-baseline-removal
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - setup.py
  - tests/golden/__init__.py
  - tests/golden/baseline_arrays.npz
  - tests/golden/baseline_meta.json
  - tests/golden/capture_baseline.py
  - tests/test_golden_baseline.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the new golden-baseline regression harness (`tests/golden/`, `tests/test_golden_baseline.py`) and the `setup.py` edit that strips the `console_scripts` block. The `setup.py` change is clean and correctly scoped — it removes exactly the `entry_points` block referencing `infodynamics.shipping`, with no dangling references left in the file. `baseline_arrays.npz` was loaded and its array shapes cross-checked against `baseline_meta.json`'s `shapes` block; they agree, and the harness was executed locally (`pytest tests/test_golden_baseline.py`) and passes.

The significant problem is that the harness's declared runtime dependencies don't match what `setup.py` actually installs for testing, and unlike every other optional-dependency test already in this repo, the new golden test does not gate gracefully on missing extras. This undermines the stated purpose of this phase — establishing a reliable verification gate before Plan 02's removal work — because the gate can silently fail to even collect in the documented minimal test environment. Additional maintainability concerns (module-level side effects at import time, an overly broad `except ImportError`, and an unpinned embedding model revision) are noted as warnings.

## Critical Issues

### CR-01: Golden baseline test has undeclared, ungated optional-extra dependencies

**File:** `tests/golden/capture_baseline.py:29,153,195` and `tests/test_golden_baseline.py:22`
**Issue:**
`compute_outputs()` constructs a real `Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")` (requires the `embedding` extra, and network access to the HuggingFace Hub on a cold cache) and a `SignalClusterer` (requires the `clustering` extra: `tslearn`, `scipy`). Neither dependency is included in `setup.py`'s `extras_require['test']` (`['pytest>=6.2.2', 'hypothesis>=6.87.0']`), which is the officially documented minimal test setup (`pip install -e .[test]`).

Worse, `test_golden_baseline.py` calls `compute_outputs()` unconditionally at **module import time** (line 22), with no `pytest.importorskip` guard. Every other optional-dependency test in this repo follows a consistent, established pattern of gating gracefully:
```python
# tests/test_clustering.py:5
tslearn = pytest.importorskip("tslearn")
# tests/test_morphology.py:5-6
spacy = pytest.importorskip("spacy")
pytest.importorskip("textdescriptives")
# tests/test_viz.py:9
tslearn = pytest.importorskip("tslearn")
```
`tests/test_golden_baseline.py` does not follow this convention. In an environment that only has `pip install -e .[test]` installed (as documented), collecting this test file raises an uncaught `ImportError` from deep inside `infodynamics.embedding._load_model` / `infodynamics.clustering.barycenter`, aborting collection for the whole file with an ugly traceback instead of a clean skip — and this also silently breaks any CI configuration that installs only the `test` extra, exactly the scenario this golden-baseline harness exists to protect (verifying the Phase-01/Plan-02 removal didn't change numerical output).

By contrast, other pipeline tests in this repo (`tests/test_pipeline.py`) deliberately avoid this problem by monkeypatching a `FakeEncoder` to avoid requiring `sentence-transformers` or network access at all — a pattern this new harness explicitly cannot use (it needs the real encoder to produce a genuine golden baseline), which makes explicit dependency declaration and graceful skipping even more important here.

**Fix:**
```python
# tests/golden/capture_baseline.py (top, before other infodynamics imports)
import pytest
pytest.importorskip("sentence_transformers")
pytest.importorskip("tslearn")
pytest.importorskip("scipy")
```
and/or, in `setup.py`, make sure the `test` extra actually provides what the golden harness needs:
```python
extras_require['test'] = sorted(
    set(extras_require['test']) | set(extras_require['embedding']) | set(extras_require['clustering'])
)
```
Pick at least one of these — ideally both, so `pip install -e .[test]` is sufficient and a partial-extras environment still gets a clean skip rather than a collection error.

## Warnings

### WR-01: Expensive pipeline runs as a module-import side effect, not a fixture

**File:** `tests/test_golden_baseline.py:22`
**Issue:** `_CURRENT_ARRAYS, _CURRENT_META = compute_outputs()` runs unconditionally at module scope during import. This means `pytest --collect-only`, `pytest -k <unrelated>`, or any tool that merely imports this test module pays the full cost (~14s locally, plus a HuggingFace Hub network round-trip on a cold cache) regardless of whether any test in the file is actually selected or executed.
**Fix:** Convert to a module-scoped fixture so the cost is only paid when a test in this file runs:
```python
@pytest.fixture(scope="module")
def current_outputs():
    return compute_outputs()

def test_text_signals_match_golden_baseline(current_outputs):
    current_arrays, _ = current_outputs
    ...
```

### WR-02: Overly broad `except ImportError` masks unrelated import failures (and is dead code)

**File:** `tests/test_golden_baseline.py:8-16`
**Issue:**
```python
try:
    from tests.golden.capture_baseline import ARRAYS_PATH, META_PATH, compute_outputs
except ImportError:
    # Fallback for environments where "tests" isn't importable as a package
    ...
    from capture_baseline import ARRAYS_PATH, META_PATH, compute_outputs
```
This catches *any* `ImportError` raised while importing `capture_baseline` — including a genuine bug deep in its own import chain (e.g. a broken `infodynamics.embedding` import) — and silently retries via `sys.path` manipulation, which would produce a confusing secondary traceback instead of surfacing the real failure. It's also unreachable in practice: verified empirically in this repo's Python 3.14 environment that `from tests.golden.capture_baseline import ARRAYS_PATH` succeeds directly (Python 3's implicit namespace packages make the missing `tests/__init__.py` a non-issue), so the fallback branch never executes in normal use. The comment's premise ("this repo has no `tests/__init__.py`... so we need a fallback") is incorrect for Python 3.3+.
**Fix:** Remove the fallback and the misleading comment, or if genuinely needed for some non-standard invocation, narrow the except to only trigger on the specific `ModuleNotFoundError: No module named 'tests'` case.

### WR-03: Golden baseline model reference is not pinned to a revision

**File:** `tests/golden/capture_baseline.py:153`
**Issue:** `Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")` references a HuggingFace Hub model by name only. `infodynamics.embedding.Encoder` (and the underlying `SentenceTransformer` call) has no `revision`/commit-hash parameter exposed, so if the upstream repo's default branch is ever updated with different weights, the "golden" numbers captured in `baseline_arrays.npz` would silently become unreproducible from a fresh download, with no code diff to explain the drift — undermining the "single source of truth" claim in the module docstring.
**Fix:** Pin a specific revision (commit SHA) when constructing the encoder for baseline capture, e.g. extend `Encoder` to accept and forward a `revision` kwarg to `SentenceTransformer(model_name, revision=...)`, and record the pinned revision in `baseline_meta.json` for traceability.

## Info

### IN-01: Duplicated tolerance constants

**File:** `tests/test_golden_baseline.py:29-31,39-40,45-47,59-61,66-68,77-79`
**Issue:** The pair `rtol=1e-5, atol=1e-8` is repeated verbatim 8 times across the four test functions.
**Fix:** Extract once at module scope: `RTOL, ATOL = 1e-5, 1e-8`, then reference `rtol=RTOL, atol=ATOL` at each call site.

### IN-02: `text_sha256` fixture hashes are captured but never verified

**File:** `tests/golden/capture_baseline.py:169`, `tests/test_golden_baseline.py`
**Issue:** `compute_outputs()` records a `text_sha256` per fixture in `meta["fixtures"][name]`, and it's persisted in `baseline_meta.json`, but `test_golden_baseline.py` never reads or asserts against this field — it's informational/audit-only (any actual text drift would already be caught indirectly via the novelty/descriptor comparisons). Not incorrect, but worth a one-line comment near the field noting it's not load-bearing for the regression test itself, so a future reader doesn't assume otherwise.
**Fix:** Add a short comment in `capture_baseline.py` near the `text_sha256` computation, e.g. `# informational only -- not asserted directly by test_golden_baseline.py`.

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

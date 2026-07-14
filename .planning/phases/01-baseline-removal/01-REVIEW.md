---
phase: 01-baseline-removal
reviewed: 2026-07-14T09:21:16Z
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
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-14T09:21:16Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This is a re-review after gap-closure plan `01-04` (commits `ec5c1e3`, `4cca827`) landed to fix the prior review's CR-01 finding (golden-baseline test had undeclared, ungated optional-extra dependencies). All six files from the original review scope were re-read fresh and cross-checked against the current git history.

**CR-01 is confirmed resolved**, both by static reading and by empirical verification:

- `tests/golden/capture_baseline.py:19-23` now imports `pytest` and calls `pytest.importorskip("sentence_transformers")`, `pytest.importorskip("tslearn")`, `pytest.importorskip("scipy")` before the `infodynamics` import block, exactly matching the fix suggested in the prior review.
- `setup.py:30` now unions `extras_require['test']` with the `embedding` and `clustering` extras, so `pip install -e .[test]` alone provides `sentence-transformers`, `tslearn`, and `scipy` — the documented minimal test environment is now actually sufficient to run the golden-baseline harness.
- Empirical check performed as part of this review: with `sys.modules['sentence_transformers'] = None` (and `tslearn`, `scipy` likewise, simulating an environment where only the base `test` extra is installed), `pytest tests/test_golden_baseline.py` produces a clean `1 skipped in 0.15s` — no traceback, no collection error. With the real dependencies present (this repo's `.venv`), the same command produces `4 passed in 13.07s`, confirming the golden baseline itself still holds under the current code.

The three warnings and two info items from the prior review (WR-01, WR-02, WR-03, IN-01, IN-02) were explicitly out of scope for the gap-closure plan and remain **unfixed** in the current files — they are re-flagged below (line numbers re-verified against the current file state; `capture_baseline.py`'s line numbers shifted slightly due to the CR-01 fix, `tests/test_golden_baseline.py` is byte-for-byte untouched since the prior review). No new issues were introduced by the CR-01 fix itself; `setup.py`'s union expression and `capture_baseline.py`'s guard placement were both re-checked and are correct and sufficient.

## Warnings

### WR-01: Expensive pipeline runs as a module-import side effect, not a fixture

**File:** `tests/test_golden_baseline.py:22`
**Issue:** `_CURRENT_ARRAYS, _CURRENT_META = compute_outputs()` runs unconditionally at module scope during import. This means `pytest --collect-only`, `pytest -k <unrelated>`, or any tool that merely imports this test module pays the full cost (~13s locally, plus a HuggingFace Hub network round-trip on a cold cache) regardless of whether any test in the file is actually selected or executed. Still present unchanged; not addressed by the CR-01 gap-closure plan.
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
This catches *any* `ImportError` raised while importing `capture_baseline` — including a genuine bug deep in its own import chain — and silently retries via `sys.path` manipulation, producing a confusing secondary traceback instead of surfacing the real failure. Re-verified in this environment: `from tests.golden.capture_baseline import ARRAYS_PATH` succeeds directly (Python 3's implicit namespace packages make the missing `tests/__init__.py` a non-issue), so the fallback branch is still unreachable in normal use. Note (checked as part of this re-review): the `pytest.importorskip` guards added for CR-01 raise `pytest.Skipped` — a `BaseException` subclass, not `ImportError` — when dependencies are missing, so they correctly bypass this `except ImportError` and propagate as a clean skip. CR-01's fix does not interact badly with this pre-existing issue, but the dead fallback branch and its misleading comment remain unaddressed.
**Fix:** Remove the fallback and the misleading comment, or if genuinely needed for some non-standard invocation, narrow the except to only trigger on the specific `ModuleNotFoundError: No module named 'tests'` case.

### WR-03: Golden baseline model reference is not pinned to a revision

**File:** `tests/golden/capture_baseline.py:158`
**Issue:** `Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")` references a HuggingFace Hub model by name only. `infodynamics.embedding.Encoder` has no `revision`/commit-hash parameter exposed, so if the upstream repo's default branch is ever updated with different weights, the "golden" numbers captured in `baseline_arrays.npz` would silently become unreproducible from a fresh download, with no code diff to explain the drift. Still present unchanged; not addressed by the CR-01 gap-closure plan.
**Fix:** Pin a specific revision (commit SHA) when constructing the encoder for baseline capture, e.g. extend `Encoder` to accept and forward a `revision` kwarg to `SentenceTransformer(model_name, revision=...)`, and record the pinned revision in `baseline_meta.json` for traceability.

## Info

### IN-01: Duplicated tolerance constants

**File:** `tests/test_golden_baseline.py:29-31,39-40,45-47,59-61,66-68,77-79`
**Issue:** The pair `rtol=1e-5, atol=1e-8` is repeated verbatim 8 times across the four test functions. Still present unchanged.
**Fix:** Extract once at module scope: `RTOL, ATOL = 1e-5, 1e-8`, then reference `rtol=RTOL, atol=ATOL` at each call site.

### IN-02: `text_sha256` fixture hashes are captured but never verified

**File:** `tests/golden/capture_baseline.py:174`, `tests/test_golden_baseline.py`
**Issue:** `compute_outputs()` records a `text_sha256` per fixture in `meta["fixtures"][name]`, and it's persisted in `baseline_meta.json`, but `test_golden_baseline.py` never reads or asserts against this field — it's informational/audit-only (any actual text drift would already be caught indirectly via the novelty/descriptor comparisons). Still present unchanged.
**Fix:** Add a short comment in `capture_baseline.py` near the `text_sha256` computation, e.g. `# informational only -- not asserted directly by test_golden_baseline.py`.

## Data Files (noted, not line-reviewed)

- `tests/golden/baseline_arrays.npz` — 87,136 bytes, 30 arrays; shapes cross-checked against `baseline_meta.json`'s `shapes` block and confirmed consistent.
- `tests/golden/baseline_meta.json` — 3,478 bytes; well-formed JSON, keys match what `capture_baseline.py:compute_outputs()` produces.
- `tests/golden/__init__.py` — empty package marker, no issues.

---

_Reviewed: 2026-07-14T09:21:16Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

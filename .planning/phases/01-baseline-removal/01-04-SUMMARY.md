---
phase: 01-baseline-removal
plan: 04
subsystem: testing
tags: [pytest, importorskip, setuptools, extras_require, packaging]

# Dependency graph
requires:
  - phase: 01-baseline-removal (plan 01)
    provides: golden-output baseline snapshot pattern (tests/golden/capture_baseline.py, tests/test_golden_baseline.py)
provides:
  - "capture_baseline.py gates sentence_transformers/tslearn/scipy imports with pytest.importorskip so collection skips cleanly under a minimal test extra"
  - "setup.py's extras_require['test'] is self-sufficient (unions in embedding + clustering extras)"
affects: [phase-02, phase-03, phase-04, phase-05]

# Tech tracking
tech-stack:
  added: []
  patterns: ["pytest.importorskip guard convention (matches tests/test_clustering.py, tests/test_morphology.py, tests/test_viz.py) now also applied to the golden-baseline capture module"]

key-files:
  created: []
  modified: [tests/golden/capture_baseline.py, setup.py]

key-decisions:
  - "Fixed CR-01 both ways per reviewer recommendation: added importorskip guards AND made the test extra self-sufficient, rather than picking just one"

patterns-established: []

requirements-completed: [QA-01]

coverage:
  - id: D1
    description: "tests/golden/capture_baseline.py gates sentence_transformers, tslearn, and scipy with pytest.importorskip before importing infodynamics"
    requirement: "QA-01"
    verification:
      - kind: unit
        ref: "tests/test_golden_baseline.py (4 passed)"
        status: pass
      - kind: other
        ref: "grep -c 'pytest.importorskip(' tests/golden/capture_baseline.py == 3; offset check importorskip < from infodynamics"
        status: pass
    human_judgment: false
  - id: D2
    description: "setup.py's extras_require['test'] is the sorted union of base test deps + embedding + clustering extras"
    requirement: "QA-01"
    verification:
      - kind: other
        ref: "python -c isolated exec of extras_require block, asserting sentence-transformers/tslearn/scipy/pytest/hypothesis all present"
        status: pass
    human_judgment: false
  - id: D3
    description: "No regression to full suite: 72 collected, 71 passed / 1 failed (pre-existing test_window_size, QA-03)"
    verification:
      - kind: integration
        ref: ".venv/bin/pytest -q (full suite)"
        status: pass
    human_judgment: false

duration: 2min
completed: 2026-07-14
status: complete
---

# Phase 01 Plan 04: Golden-Baseline Test Extras Gap Closure Summary

**Guarded `tests/golden/capture_baseline.py` with `pytest.importorskip` for sentence_transformers/tslearn/scipy and unioned `setup.py`'s `test` extra with `embedding` + `clustering`, closing CR-01 / Truth #9.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-07-14T11:11:00+02:00 (approx, first commit)
- **Completed:** 2026-07-14T11:11:57+02:00
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments
- `tests/golden/capture_baseline.py` now imports `pytest` and calls `pytest.importorskip("sentence_transformers")`, `pytest.importorskip("tslearn")`, `pytest.importorskip("scipy")` before importing `infodynamics`, so collecting `tests/test_golden_baseline.py` skips cleanly instead of raising an uncaught ImportError when the embedding/clustering extras are absent
- `setup.py`'s `extras_require['test']` is now the sorted set-union of the base test deps (`pytest`, `hypothesis`) with the `embedding` (`sentence-transformers`) and `clustering` (`tslearn`, `scipy`) extras, making `pip install -e .[test]` self-sufficient for the golden-baseline test
- Verified no regression: full suite still `72` collected, `71 passed / 1 failed` (only the pre-existing `test_window_size`, tracked as QA-03 for Phase 3); `tests/test_golden_baseline.py` still `4 passed`

## Task Commits

Each task was committed atomically:

1. **Task 1: Gate capture_baseline.py's optional-extra dependencies with pytest.importorskip** - `ec5c1e3` (fix)
2. **Task 2: Make setup.py's test extra self-sufficient by unioning embedding + clustering** - `4cca827` (fix)

_No TDD tasks; both are additive/mechanical guard edits._

## Files Created/Modified
- `tests/golden/capture_baseline.py` - Added `import pytest` and three `pytest.importorskip(...)` guards (sentence_transformers, tslearn, scipy) positioned after `import numpy as np` and before `from infodynamics import (...)`
- `setup.py` - Inserted `extras_require['test'] = sorted(set(extras_require['test']) | set(extras_require['embedding']) | set(extras_require['clustering']))` between the `extras_require = {...}` literal and the `extras_require['all'] = ...` line

## Decisions Made
- Implemented both halves of the reviewer's CR-01 recommendation (importorskip guards AND self-sufficient test extra) rather than choosing one, per the plan's explicit instruction — belt-and-suspenders: a partial-extras environment gets a clean skip, and the documented `test` extra alone is now sufficient to run the golden-baseline test at all.

## Deviations from Plan

None - plan executed exactly as written. Both tasks were mechanical, targeted edits matching the exact strings specified in the plan's `<action>` blocks.

## Issues Encountered

None. `.venv/bin/pytest -q tests/test_golden_baseline.py` and `.venv/bin/pytest -q` (full suite) both ran without issue in this dev environment (extras already installed, so the new guards do not trigger skips here — they only activate under a bare `test` extra, which was verified at the source level per the plan's "Empirical bar note").

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- VERIFICATION.md Truth #9 is now satisfiable: the golden-baseline gate is self-sufficient under the documented `test` extra and degrades gracefully (skip, not error) when embedding/clustering extras are absent.
- All 9 Phase 1 verification truths and CR-01 are now closed with no scope creep into the deferred review items (WR-01/WR-02/WR-03/IN-01/IN-02) or the QA-03 `test_window_size` fix (explicitly out of scope, deferred to Phase 3).
- Phase 1 (baseline-removal) is ready to close out; Phase 2 can proceed on a clean, drift-detectable baseline.

---
*Phase: 01-baseline-removal*
*Completed: 2026-07-14*

## Self-Check: PASSED

All created/modified files verified present on disk; all task and summary commit hashes verified present in git log (ec5c1e3, 4cca827, 26915a4).

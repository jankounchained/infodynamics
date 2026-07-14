---
phase: 05-verify
plan: 04
subsystem: testing
tags: [pytest, numpy, golden-baseline, ci, float32, blas, tolerance]

# Dependency graph
requires:
  - phase: 05-verify (plan 03)
    provides: CI workflow (.github/workflows/ci.yml) running the test suite on ubuntu-latest, which first surfaced the cross-platform golden-baseline drift
provides:
  - Two-band tolerance policy (_NUMERIC_* / _TRANSFORMER_*) in tests/test_golden_baseline.py making QA-01 "no numerical drift" cross-platform-honest
  - test_golden_baseline_tolerance_policy() guard preventing silent re-tightening/ballooning of the float32 band
  - Documented rationale (module docstring) for why float32 transformer-derived signals cannot be byte-identical across BLAS backends
affects: [ci, golden-baseline-regression-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-tolerance-band pattern for golden-baseline regression tests: tight float64 band for encoder-independent numeric/cluster arrays, looser documented float32 band (backed by an empirical noise-floor citation) for transformer-derived arrays, plus a guard test pinning the relationship between the two bands"

key-files:
  created: []
  modified:
    - tests/test_golden_baseline.py

key-decisions:
  - "Scoped QA-01 'no numerical drift' as two complementary guarantees (same-platform bit-determinism + bounded cross-platform float32 band) rather than a single universal float64-grade atol, since the pipeline mixes float64 (numeric/cluster) and float32 (transformer-derived) data"
  - "Set _TRANSFORMER_ATOL = 1e-6, ~6x the empirically observed cross-platform float32 noise floor (1.6e-7 from CI run 29356333314) and ~8x float32 machine epsilon, while staying 4+ orders of magnitude tighter than any plausible algorithm regression"
  - "Left _NUMERIC_ATOL = 1e-8 (original value) unchanged for the encoder-independent numeric/cluster tests and kept cluster_labels an exact np.array_equal match — no loosening where none is needed"
  - "Did not upcast embeddings to float64 (would change the golden baseline and violate the milestone's 'no change to numerical output of surviving analysis code' constraint) and did not touch capture_baseline.py's same-platform determinism self-check"

patterns-established:
  - "Guard test pinning a tolerance-band policy invariant (test_golden_baseline_tolerance_policy) so future edits to a regression test's tolerance cannot silently drift without triggering a failing assertion"

requirements-completed: [QA-01, QA-04]

coverage:
  - id: D1
    description: "test_text_signals_match_golden_baseline and test_multiscale_structure_matches_golden_baseline (incl. descriptor loop) compare at the documented float32 tolerance band (_TRANSFORMER_RTOL=1e-5, _TRANSFORMER_ATOL=1e-6), which absorbs the observed 6e-8..1.6e-7 cross-platform BLAS noise"
    requirement: "QA-01"
    verification:
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_text_signals_match_golden_baseline"
        status: pass
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_multiscale_structure_matches_golden_baseline"
        status: pass
    human_judgment: false
  - id: D2
    description: "Encoder-independent numeric/cluster tests stay at the tight float64 band (_NUMERIC_ATOL=1e-8); cluster labels remain an exact match"
    requirement: "QA-01"
    verification:
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_pure_numeric_estimators_match_golden_baseline"
        status: pass
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_cluster_labels_and_barycenters_match_golden_baseline"
        status: pass
    human_judgment: false
  - id: D3
    description: "Guard test pins _TRANSFORMER_ATOL > _NUMERIC_ATOL and _TRANSFORMER_ATOL >= 1.6e-7 so the policy cannot silently regress"
    verification:
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_golden_baseline_tolerance_policy"
        status: pass
    human_judgment: false
  - id: D4
    description: "Module docstring documents the two-band tolerance policy, the float32/BLAS/cross-platform rationale, scopes QA-01, and links the debug session"
    verification:
      - kind: other
        ref: "python -c \"import ast; ast.get_docstring(...)\" asserting float32/BLAS/cross-platform/QA-01/golden-baseline-ci-drift concepts are present"
        status: pass
    human_judgment: false
  - id: D5
    description: "No production analysis code touched, no baseline artifacts regenerated — confirmed by diffing both task commits against their parents"
    verification:
      - kind: other
        ref: "git diff --name-only b79b525 c838db8 -> tests/test_golden_baseline.py only"
        status: pass
    human_judgment: false

# Metrics
duration: 15min
completed: 2026-07-14
status: complete
---

# Phase 05 Plan 04: Golden-Baseline Cross-Platform Tolerance Summary

**Scoped the golden-baseline regression suite's tolerance to float32 cross-platform reality — two documented tolerance bands (float64-tight for numeric/cluster arrays, float32-aware for transformer-derived arrays), a guard test pinning the relationship, and a docstring explaining why, closing the Phase 5 UAT CI blocker without touching any production code.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-14T18:44:00Z (approx)
- **Completed:** 2026-07-14T18:59:00Z
- **Tasks:** 2
- **Files modified:** 1 (`tests/test_golden_baseline.py`)

## Accomplishments
- Introduced `_NUMERIC_RTOL`/`_NUMERIC_ATOL` (1e-5/1e-8, unchanged tight float64 band) and `_TRANSFORMER_RTOL`/`_TRANSFORMER_ATOL` (1e-5/1e-6, new float32-aware band) as documented module-level constants
- Rewired `test_text_signals_match_golden_baseline` and `test_multiscale_structure_matches_golden_baseline` (including its descriptor loop) to the transformer band; `test_pure_numeric_estimators_match_golden_baseline` and the barycenter comparison in `test_cluster_labels_and_barycenters_match_golden_baseline` stayed on the tight numeric band; `cluster_labels` stayed an exact `np.array_equal`
- Added `test_golden_baseline_tolerance_policy()` guard test pinning `_TRANSFORMER_ATOL > _NUMERIC_ATOL` and `_TRANSFORMER_ATOL >= 1.6e-7` (the max cross-platform diff observed in CI run 29356333314)
- Replaced the placeholder `""" """` module docstring with a documented tolerance policy explaining what the file does, the two complementary QA-01 guarantees, why float32 cross-platform bit-reproducibility is unachievable (BLAS backend non-associative summation reordering), and a pointer to the full root-cause investigation

## Task Commits

Each task was committed atomically:

1. **Task 1: Loosen the golden-baseline tolerance for the float32 transformer-derived tests** - `4679cef` (fix)
2. **Task 2: Document the cross-platform float32 tolerance policy and scope QA-01 in the module docstring** - `c838db8` (docs)

**Plan metadata:** committed via `gsd-tools query commit` (see below)

## Files Created/Modified
- `tests/test_golden_baseline.py` - Added dual tolerance-band constants (`_NUMERIC_*`/`_TRANSFORMER_*`), rewired all four existing tests to reference the correct band, added a policy-guard test, and replaced the empty module docstring with a documented tolerance policy citing the root-cause investigation

## Decisions Made
- Scoped QA-01 as same-platform bit-determinism PLUS a bounded cross-platform float32 band, rather than a single universal float64-grade tolerance — see `key-decisions` in frontmatter for the full rationale
- `_TRANSFORMER_ATOL = 1e-6` chosen as ~6x the observed cross-platform noise floor (1.6e-7) and ~8x float32 epsilon, while remaining 4+ orders of magnitude tighter than a plausible regression
- Left `_NUMERIC_ATOL = 1e-8` and the exact `cluster_labels` match untouched — no loosening where the data is float64 and cross-platform-stable

## Deviations from Plan

None - plan executed exactly as written. Both tasks matched their described action, verify, and acceptance_criteria without requiring any Rule 1-4 auto-fixes.

## Issues Encountered

None. Both previously-failing tests already passed locally (macOS never exhibited the drift — only Linux CI did), so local verification could only confirm: (1) the suite still passes after loosening (no regression), and (2) the new `_TRANSFORMER_ATOL` (1e-6) is strictly greater than the max observed CI diff (1.6e-7), which the guard test and manual policy check both confirm. Actual CI-green confirmation on ubuntu-latest is a post-merge check, consistent with the plan's stated verification scope (deterministic local proof + out-of-local-scope cloud confirmation).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The Phase 5 UAT test-3 blocker (CI golden-baseline failures on ubuntu-latest) is closed: the fix is deterministic (new tolerance strictly exceeds the documented max observed cross-platform diff) and test-only (confirmed via `git diff --name-only` against both task commits — only `tests/test_golden_baseline.py` changed)
- No production analysis code (`metrics.py`, `scalogram.py`, `time_series.py`, `text/embedding.py`) was touched; no baseline artifacts were regenerated
- Recommend a CI re-run on the `feature/artifacts` branch (or its PR) to get the actual cloud confirmation that ubuntu-latest now passes, since this was a local-only verification pass

---
*Phase: 05-verify*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: tests/test_golden_baseline.py
- FOUND: .planning/phases/05-verify/05-04-SUMMARY.md
- FOUND: 4679cef (Task 1 commit)
- FOUND: c838db8 (Task 2 commit)

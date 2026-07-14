---
phase: 03-decouple-the-pipeline
plan: 01
subsystem: api
tags: [sklearn, scikit-learn, numpy, estimators, pipeline-composability]

# Dependency graph
requires:
  - phase: 02-reorganize-into-core-text-on-ramp
    provides: infodynamics/scalogram.py and infodynamics/time_series.py at their post-reorg module paths
provides:
  - WindowedRollingDistance with fixed averaging_weights spelling, verbatim __init__, fit()-time measure resolution, completed _validate_data
  - WindowedRollingDistance.transform()/fit_transform() returning a (n_chunks, 3) stacked array (novelty/transience/resonance columns), full dict preserved as self.signal_
  - Scalogram.transform() and FooteNovelty.transform() standalone methods matching fit_transform()
affects: [03-02, 03-03, 03-04, 03-06, 03-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sklearn param-verbatim __init__ + resolution/validation deferred to fit() as a trailing-underscore fitted attribute (self.measure_), following SignalClusterer's reference pattern"
    - "Array-return transform()/fit_transform() with the rich structured output preserved as a fitted attribute (self.signal_) for callers who want it"
    - "transform() recomputes fresh from X via self.fit(X) — no fit/transform state leakage, uniform across all three estimators (D-02)"

key-files:
  created: []
  modified:
    - infodynamics/time_series.py
    - infodynamics/scalogram.py

key-decisions:
  - "Column order for WindowedRollingDistance's stacked array locked as novelty/transience/resonance (N_hat, T_hat, R_hat), per D-03's note leaving stacking convention to Claude's discretion"
  - "_validate_data converged to a single np.asarray(X) call, matching every other estimator's validation idiom in the codebase (no bespoke list/array/dataframe branching)"
  - "_resolve_measure imported from infodynamics.scalogram rather than duplicated, reusing the existing helper as the single source of truth for measure resolution"

patterns-established:
  - "Every public single-scale estimator (WindowedRollingDistance, Scalogram, FooteNovelty) now implements a real standalone transform() per D-02, ready for InfoDynamics/MultiscaleInfoDynamics (Plan 03) to adopt the same shape"

requirements-completed: [CORE-02, API-01, QA-02]

coverage:
  - id: D1
    description: "WindowedRollingDistance QA-02 bugs fixed: averaging_weigts -> averaging_weights rename, __init__ stores measure verbatim (resolved in fit() as self.measure_), _validate_data completed to np.asarray(X)"
    requirement: "QA-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 1 <verify> block): clone() round-trip, invalid measure raises AttributeError from fit() not __init__, _validate_data coercion"
        status: pass
    human_judgment: false
  - id: D2
    description: "WindowedRollingDistance.transform()/fit_transform() return a (n_chunks, 3) stacked ndarray (novelty/transience/resonance columns); full signal dict preserved as self.signal_"
    requirement: "CORE-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 2 <verify> block): shape assertion, column-to-dict-key equality, estimate_error=True adds *_sd keys, clone() round-trip"
        status: pass
    human_judgment: false
  - id: D3
    description: "Scalogram and FooteNovelty each expose a standalone transform() matching fit_transform(), sklearn clone()-compatible"
    requirement: "API-01"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 3 <verify> block): shape assertions, transform()==fit_transform() equality, clone() round-trip, _resolve_measure import regression guard"
        status: pass
    human_judgment: false

# Metrics
duration: 4min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 01: Fix Single-Scale Estimators for sklearn Pipeline-Composability Summary

**WindowedRollingDistance's QA-02 bugs fixed (averaging_weights rename, verbatim __init__, completed _validate_data) and all three single-scale estimators (WindowedRollingDistance, Scalogram, FooteNovelty) converged onto a uniform array-return transform()/fit_transform() contract with rich state preserved as fitted attributes**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-14T11:59:17Z
- **Completed:** 2026-07-14T12:02:48Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Fixed all three QA-02 bugs in `WindowedRollingDistance` as their own labeled commit: misspelled `averaging_weigts` renamed to `averaging_weights`, measure resolution moved out of `__init__` into `fit()` (stored verbatim on `self.measure`, resolved as `self.measure_`), `_validate_data` completed from an "UNFINISHED" list-of-lists-only stub to a single `np.asarray(X)` coercion
- `WindowedRollingDistance` now has a real standalone `transform()` returning a `(n_chunks, 3)` stacked array (novelty/transience/resonance columns); the full rich dict (`N_hat`/`T_hat`/`R_hat`, plus `*_sd` keys when `estimate_error=True`) is preserved as the fitted attribute `self.signal_`
- `Scalogram` and `FooteNovelty` each gained a standalone `transform()` matching their existing `fit_transform()`, closing the D-02 gap (both estimators previously only had `fit()`/`fit_transform()`)
- All three estimators verified to pass `sklearn.base.clone()` round-trips

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix WindowedRollingDistance QA-02 bugs (param-verbatim __init__, rename, _validate_data)** - `c297759` (fix)
2. **Task 2: Give WindowedRollingDistance a real transform() with array output and self.signal_ (D-02/D-03)** - `b564336` (feat)
3. **Task 3: Add standalone transform() to Scalogram and FooteNovelty (D-02)** - `7e0398c` (feat)

**Plan metadata:** (recorded below after this commit)

## Files Created/Modified
- `infodynamics/time_series.py` - `WindowedRollingDistance`: renamed `averaging_weigts` -> `averaging_weights`; `__init__` stores `measure` verbatim; `fit()` resolves `self.measure_` via the shared `_resolve_measure` helper (imported from `infodynamics.scalogram`); `_validate_data` completed to `np.asarray(X)`; `self.signal` renamed to `self.signal_`; added `transform()`; `fit_transform()` now returns the stacked `(n_chunks, 3)` array instead of the dict
- `infodynamics/scalogram.py` - Added `Scalogram.transform()` and `FooteNovelty.transform()`, each delegating to the same code path as their existing `fit_transform()` (no fit-time state reused, per D-02)

## Decisions Made
- Locked the stacked-array column order for `WindowedRollingDistance` as novelty/transience/resonance (`N_hat`, `T_hat`, `R_hat`) — left to Claude's discretion by D-03
- Converged `_validate_data` to the same one-line `np.asarray(X)` idiom every other estimator in the codebase already uses, rather than inventing bespoke validation logic (no in-repo analog existed for a "complete" version)
- Imported `_resolve_measure` from `infodynamics.scalogram` instead of duplicating it in `time_series.py`, keeping measure resolution single-sourced

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Confirmed the plan's own expected-breakage note: this plan intentionally changes `WindowedRollingDistance`'s output shape from a dict to an ndarray. Running the full test suite afterward shows the breakage confined exactly where the plan predicted — `infodynamics/pipeline.py`'s `InfoDynamics.fit()` still indexes `WindowedRollingDistance.fit_transform()`'s return value as a dict (`signal["N_hat"]`), which now raises `IndexError` since `fit_transform()` returns an ndarray. This propagates into `tests/test_pipeline.py`, `tests/test_infodynamics_class.py` (2 of 5 tests), and collection of `tests/test_golden_baseline.py`. All other test files (59 tests) pass unaffected. This is explicitly out of scope for Plan 01 — `infodynamics/pipeline.py` is Plan 03's responsibility (CORE-02/D-03 convergence for `InfoDynamics`/`MultiscaleInfoDynamics`), and the golden-snapshot re-verification is Plan 06's job per the wave ordering. No fix applied here; documented per the plan's own verification section ("Full-suite green is NOT expected at the close of this plan in isolation").

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `WindowedRollingDistance`, `Scalogram`, and `FooteNovelty` are now uniform, Pipeline-legal building blocks (verbatim params, working `transform()`, array output, `clone()`-safe) ready for `infodynamics/pipeline.py` (`InfoDynamics`/`MultiscaleInfoDynamics`) to consume in Plan 03
- Known, plan-anticipated breakage in `tests/test_pipeline.py`, `tests/test_infodynamics_class.py`, and `tests/test_golden_baseline.py` collection is unresolved by design — Plan 03 (pipeline.py rewrite) and Plan 06 (golden re-verification) will close it
- `_resolve_measure` remains importable from `infodynamics.scalogram` and is now also relied upon by `infodynamics/time_series.py` — any future move of that helper must update both call sites

---
*Phase: 03-decouple-the-pipeline*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: infodynamics/time_series.py
- FOUND: infodynamics/scalogram.py
- FOUND: .planning/phases/03-decouple-the-pipeline/03-01-SUMMARY.md
- FOUND: commit c297759 (Task 1)
- FOUND: commit b564336 (Task 2)
- FOUND: commit 7e0398c (Task 3)

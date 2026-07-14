---
phase: 03-decouple-the-pipeline
plan: 04
subsystem: testing
tags: [pytest, hypothesis, sklearn, numpy, test-debt]

# Dependency graph
requires:
  - phase: 03-decouple-the-pipeline (Plan 01)
    provides: WindowedRollingDistance's D-02/D-03 array-return transform()/fit_transform() with self.signal_
provides:
  - tests/test_infodynamics_class.py fully green, no empty stubs, correct shape assertions
  - WindowedRollingDistance window_size=0 edge case fixed (no longer crashes with sklearn measures or silently produces NaN)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Test reads WindowedRollingDistance output via the fitted signal_ dict attribute or the stacked (n_chunks,3) return array, never the removed dict-return shape"

key-files:
  created: []
  modified:
    - tests/test_infodynamics_class.py
    - infodynamics/time_series.py

key-decisions:
  - "Rule 1 auto-fix: WindowedRollingDistance.calc_signal crashed (ValueError from sklearn's check_pairwise_arrays) with cosine measure at window_size=0, and silently produced NaN with js_dist at window_size=0, because it computed a distance against an empty comparison window instead of taking the constant-fill fallback branch already designed for insufficient-context cases. Fixed by short-circuiting to inplace_constant when window_size == 0, before computing submat's measure. This is separate from the STATE.md-tracked 'pre-existing bug' (which was purely the test's wrong shape assertion, per QA-03/CONTEXT.md's explicit instruction not to touch the implementation for that one) — this is a genuine, previously-undiscovered production bug surfaced only by exercising w=0 with a real distance measure and asserting no-NaN output, which the plan's own test_transience_calculation spec required."
  - "test_window_size's old wrong assertion (len(X) - window_size + 1, window_size) removed entirely and replaced with the real output-shape assertions, per QA-03's explicit instruction: correct the assertion, don't bend the implementation to match a wrong assertion"
  - "Used measure='cosine' (not jensenshannon/js_dist) for the three new/rewritten hypothesis-free tests (test_transience_calculation, test_negative_values_in_input_data, test_very_small_numbers) since js_dist expects distribution-like non-negative rows and cosine handles arbitrary-magnitude real vectors including negatives"
  - "Verified golden-baseline collection failure (InfoDynamics(encoder=...) TypeError) and 8 test_pipeline.py/test_morphology.py failures are pre-existing, plan-anticipated breakage from Plan 03 (documented in 03-03-SUMMARY.md), deferred to Plans 05/06 — confirmed unaffected by this plan's changes"

patterns-established: []

requirements-completed: [QA-03]

coverage:
  - id: D1
    description: "test_calc_signal_data_shapes and test_window_size read WindowedRollingDistance's fit()-then-signal_ / fit_transform() (n_chunks,3) array output instead of the removed dict-return shape"
    requirement: "QA-03"
    verification:
      - kind: unit
        ref: "python -m pytest tests/test_infodynamics_class.py -k 'calc_signal_data_shapes or transience_calculation or window_size' -q — 3 passed"
        status: pass
    human_judgment: false
  - id: D2
    description: "test_window_size asserts the real (n_chunks,)/(n_chunks,3) output shape, removing the old wrong assertion; test_transience_calculation is a real test (no bare pass) covering window_size 0-3 with a no-NaN assertion"
    requirement: "QA-03"
    verification:
      - kind: unit
        ref: "grep -n 'len(X) - window_size + 1' tests/test_infodynamics_class.py — no matches; grep -A5 'def test_transience_calculation' shows real assertions, no bare pass"
        status: pass
    human_judgment: false
  - id: D3
    description: "test_negative_values_in_input_data and test_very_small_numbers exist, assert finite (no NaN/Inf) novelty/transience/resonance output, and pass"
    requirement: "QA-03"
    verification:
      - kind: unit
        ref: "python -m pytest tests/test_infodynamics_class.py -k 'negative_values_in_input_data or very_small_numbers' -q — 2 passed"
        status: pass
    human_judgment: false
  - id: D4
    description: "Whole test file is green"
    requirement: "QA-03"
    verification:
      - kind: unit
        ref: "python -m pytest tests/test_infodynamics_class.py -q — 7 passed"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 04: Fix QA-03 Test Debt in test_infodynamics_class.py Summary

**Resolved all QA-03 test debt in `tests/test_infodynamics_class.py` — corrected the wrong `test_window_size` shape assertion, implemented the empty `test_transience_calculation` stub, added the two missing finite-output tests, and fixed a genuine `WindowedRollingDistance` `window_size=0` crash/NaN bug surfaced along the way**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-14T12:20:37Z
- **Completed:** 2026-07-14T12:26:35Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `test_calc_signal_data_shapes` and `test_window_size` no longer index the removed dict return of `WindowedRollingDistance.fit_transform()` (`X0["N_hat"]`); both now read from the fitted `signal_` dict attribute or the `(n_chunks, 3)` stacked array
- `test_window_size`'s wrong assertion (`Xw["N_hat"].shape == (len(X) - window_size + 1, window_size)` — a shape the estimator never produced) removed and replaced with the real output-shape assertions (`Xw.shape == (len(X), 3)`, `iw.signal_["N_hat"].shape == (len(X),)`)
- `test_transience_calculation` implemented (was a bare `pass` stub): exercises `WindowedRollingDistance(measure="cosine")` across `window_size` in `(0, 1, 2, 3)`, asserting `signal_["T_hat"]` has the correct shape and contains no NaN
- Added `test_negative_values_in_input_data` and `test_very_small_numbers`, both asserting finite (`np.isfinite`) novelty/transience/resonance output for negative-valued and denormal-magnitude (`1e-300`) input arrays
- **Rule 1 bug fix** in `infodynamics/time_series.py`: `WindowedRollingDistance.calc_signal` crashed with a `ValueError` (sklearn's `check_pairwise_arrays`, cosine measure) or silently produced `NaN` (js_dist measure) at `window_size=0`, because the empty comparison window (`submat.shape[0] == 0 == self.window_size`) incorrectly satisfied the "compute the real measure" branch instead of falling into the existing constant-fill fallback. Fixed by short-circuiting to `self.inplace_constant` whenever `window_size == 0`, before computing `submat`'s measure — this is what let `test_transience_calculation`'s w=0 case (required by this plan) pass with a genuine no-NaN assertion instead of either crashing or silently returning garbage.

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix test_window_size + test_calc_signal_data_shapes for the new output, implement test_transience_calculation (QA-03)** - `ee4f189` (fix) — includes the `infodynamics/time_series.py` window_size=0 bug fix
2. **Task 2: Add test_negative_values_in_input_data and test_very_small_numbers (QA-03)** - `fe79256` (test)

## Files Created/Modified
- `tests/test_infodynamics_class.py` - `test_calc_signal_data_shapes`/`test_window_size` corrected to read the new array/`signal_` output; `test_transience_calculation` implemented; `test_negative_values_in_input_data` and `test_very_small_numbers` added
- `infodynamics/time_series.py` - `WindowedRollingDistance.calc_signal` short-circuits to `self.inplace_constant` at `window_size == 0` instead of computing a distance against an empty comparison window (Rule 1 fix, out-of-plan-scope file touched to unblock Task 1's own acceptance criteria)

## Decisions Made
- Fixed a genuine `WindowedRollingDistance` `window_size=0` crash/NaN bug (Rule 1) in `infodynamics/time_series.py`, even though the plan's `files_modified` only listed the test file — this was required to satisfy Task 1's own action spec (`test_transience_calculation` must assert no-NaN output including `w=0`), and is distinct from the STATE.md-tracked "pre-existing bug" (which QA-03/CONTEXT.md explicitly scoped as assertion-only, implementation untouched)
- Used `measure="cosine"` for the new/rewritten tests rather than `js_dist`/`jensenshannon`, since `js_dist` expects distribution-like non-negative rows and would misbehave (or already silently NaN) on negative/tiny/arbitrary-magnitude real vectors
- Split the single-file test rewrite into two atomic commits matching the plan's task boundaries, by temporarily holding back the two new test functions until Task 1's commit, then re-adding them for Task 2's commit

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed WindowedRollingDistance crash/NaN at window_size=0**
- **Found during:** Task 1 (writing `test_transience_calculation` per the plan's own spec, which required `window_size=0` with a no-NaN assertion)
- **Issue:** `WindowedRollingDistance.calc_signal` computed `submat = X[i_lower:i_upper]` which is empty (shape `(0, n_features)`) when `window_size=0`; the guard `if submat.shape[0] == self.window_size` incorrectly evaluated `True` (`0 == 0`), routing into the real-measure computation branch instead of the constant-fill fallback designed for insufficient-context cases. With `measure="cosine"`, this raised `ValueError: Found array with 0 sample(s)` from sklearn's `check_pairwise_arrays`. With `measure=js_dist`, it silently computed `np.mean`/`np.std` of an empty array, producing `NaN` with `RuntimeWarning`s.
- **Fix:** Added an explicit `if self.window_size == 0:` short-circuit before the submat-based branch, setting `H_hat[i], H_sd[i] = self.inplace_constant, 0.0` and `continue`, mirroring the existing fallback's intent (no context available → use the configured constant) rather than attempting a measure computation with no comparison data.
- **Files modified:** `infodynamics/time_series.py`
- **Commit:** `ee4f189`
- **Numerical-drift check:** confirmed the golden baseline (`tests/golden/capture_baseline.py`) only exercises `WindowedRollingDistance`/`InfoDynamics` with `window_size=3`, never `0` — this fix changes behavior only for the previously broken (`NaN`/crash) `window_size=0` case, no drift to any established golden numerical output.

Or: "None - plan executed exactly as written." — not applicable; one deviation documented above.

## Issues Encountered

Ran the full non-golden test suite after both tasks to confirm no unintended regressions: 8 pre-existing failures remain in `tests/test_pipeline.py` (6) and `tests/text/test_morphology.py` (2), exactly matching the plan-anticipated breakage documented in `03-03-SUMMARY.md` ("Issues Encountered" section) from `InfoDynamics`/`MultiscaleInfoDynamics` going ndarray-only — deferred to Plans 05/06 per existing wave ordering, out of this plan's scope. `tests/test_golden_baseline.py` still fails collection (`InfoDynamics(encoder=...)` `TypeError`), also pre-existing and plan-anticipated. `tests/test_infodynamics_class.py` itself: 7/7 passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `tests/test_infodynamics_class.py` is fully green (7/7), no empty stubs, no dict-indexing of the removed `fit_transform()` return shape — QA-03's test-debt list for this file is closed
- `WindowedRollingDistance` now handles `window_size=0` correctly across all measure types (no crash, no NaN) — a latent bug that would otherwise have resurfaced whenever any future plan/test exercised that edge case
- Known, plan-anticipated breakage in `tests/test_pipeline.py`, `tests/text/test_morphology.py`, and `tests/test_golden_baseline.py` collection remains unresolved by design — Plans 05 (text wrappers) and 06 (golden re-verification + test migration) will close it

---
*Phase: 03-decouple-the-pipeline*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: tests/test_infodynamics_class.py
- FOUND: infodynamics/time_series.py
- FOUND: .planning/phases/03-decouple-the-pipeline/03-04-SUMMARY.md
- FOUND: commit ee4f189 (Task 1)
- FOUND: commit fe79256 (Task 2)

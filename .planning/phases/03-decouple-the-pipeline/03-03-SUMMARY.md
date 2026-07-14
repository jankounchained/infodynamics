---
phase: 03-decouple-the-pipeline
plan: 03
subsystem: api
tags: [sklearn, scikit-learn, numpy, estimators, pipeline-composability]

# Dependency graph
requires:
  - phase: 03-decouple-the-pipeline (Plan 01)
    provides: WindowedRollingDistance/Scalogram/FooteNovelty converged onto array-return transform()/fit_transform() with rich state on fitted attributes
provides:
  - InfoDynamics ndarray-only (measure, window_size, jump_size, estimate_error); fit(X)/transform(X)/fit_transform(X) return a (n_chunks, 3) novelty/transience/resonance array with the rich dict on self.signal_
  - MultiscaleInfoDynamics ndarray-only (scales, radii, measure); fit(X)/transform(X)/fit_transform(X) return the (n_scales, n_chunks) scalogram matrix with the four-part structure dict on self.result_ (plus ssm_/scalogram_/novelty_/scales_/radii_/descriptors_ individually preserved)
  - infodynamics/pipeline.py with zero infodynamics.text imports or segment()/Encoder/.encode() calls, resolving the Phase 2 interim exception
affects: [03-05, 03-06, 03-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Composite estimators (InfoDynamics/MultiscaleInfoDynamics) delegate to already-decoupled single-scale estimators (WindowedRollingDistance/Scalogram/FooteNovelty) via .fit(X), reading their fitted attributes rather than re-deriving computation"
    - "Array-return transform()/fit_transform() with the rich structured output preserved as a fitted attribute (self.signal_ / self.result_), matching the D-03 convention Plan 01 established"

key-files:
  created: []
  modified:
    - infodynamics/pipeline.py

key-decisions:
  - "MultiscaleInfoDynamics.transform()/fit_transform() return self.scalogram_ (the (n_scales, n_chunks) matrix) as the primary array, per D-03's note leaving the choice to Claude's discretion — MultiscaleInfoDynamics is legitimately Pipeline-terminal; its transform() output need not chain further"
  - "Split the single-file pipeline.py rewrite into two atomic commits (InfoDynamics first, MultiscaleInfoDynamics second) by holding an intermediate state where InfoDynamics is fully decoupled but MultiscaleInfoDynamics and the module's text imports remain temporarily unchanged, matching the plan's two-task breakdown"

patterns-established:
  - "Composite estimator decoupling pattern: strip text params from __init__, accept X (ndarray) in fit(), delegate to core single-scale estimators, keep dict-shaped rich output on a fitted attribute while transform()/fit_transform() return a single array"

requirements-completed: [CORE-02, API-01]

coverage:
  - id: D1
    description: "InfoDynamics.__init__ reduced to (measure, window_size, jump_size, estimate_error); fit(X) accepts embeddings ndarray directly (no segment()/Encoder.encode()); transform(X)/fit_transform(X) return a (n_chunks, 3) novelty/transience/resonance array; self.signal_ dict preserved; clone()-safe"
    requirement: "CORE-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 1 <verify> block): shape assertion, column-to-dict-key equality, estimate_error=True adds *_sd keys, get_params() key set, clone() round-trip"
        status: pass
    human_judgment: false
  - id: D2
    description: "MultiscaleInfoDynamics.__init__ reduced to (scales, radii, measure); fit(X) accepts embeddings ndarray directly (no segment()/Encoder.encode()); transform(X)/fit_transform(X) return the (n_scales, n_chunks) scalogram matrix; self.result_ dict plus all individual fitted attributes preserved; clone()-safe"
    requirement: "CORE-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 2 <verify> block): shape assertions, transform()==fit_transform()==scalogram_ equality, result_ dict keys, ssm_/descriptors_ shape checks, get_params() key set, clone() round-trip"
        status: pass
    human_judgment: false
  - id: D3
    description: "infodynamics/pipeline.py contains zero text imports or segment()/Encoder/.encode() calls anywhere in the file — CORE-02 decoupling complete, Phase 2 interim text-import exception resolved"
    requirement: "API-01"
    verification:
      - kind: unit
        ref: "grep -En \"infodynamics.text|segment\\(|Encoder|\\.encode\\(\" infodynamics/pipeline.py — no matches"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 03: Decouple InfoDynamics and MultiscaleInfoDynamics From Text Summary

**InfoDynamics and MultiscaleInfoDynamics rewritten as ndarray-only composite estimators — InfoDynamics returns a (n_chunks, 3) novelty/transience/resonance array with self.signal_, MultiscaleInfoDynamics returns the scalogram matrix with self.result_, and pipeline.py's Phase-2-flagged text-import exception is now fully resolved**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-14T12:11:51Z
- **Completed:** 2026-07-14T12:17:53Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `InfoDynamics.__init__` reduced to `(measure, window_size, jump_size, estimate_error)` — all text-coupling params (`model_name`, `encoder`, `segment_level`, `chunk_size`, `device`, `batch_size`) removed; `fit(X)` accepts embeddings ndarray directly and delegates to `WindowedRollingDistance`, reading its `self.signal_` dict rather than re-deriving computation
- `InfoDynamics.transform(X)`/`fit_transform(X)` now return a `(n_chunks, 3)` stacked novelty/transience/resonance array (same column order `WindowedRollingDistance` locked in Plan 01); the rich dict (plus `*_sd` keys when `estimate_error=True`) is preserved on `self.signal_`
- `MultiscaleInfoDynamics.__init__` reduced to `(scales, radii, measure)` — same text params removed; `fit(X)` delegates to `Scalogram(X)`/`FooteNovelty(X)` directly
- `MultiscaleInfoDynamics.transform(X)`/`fit_transform(X)` now return the `(n_scales, n_chunks)` scalogram matrix; a new `self.result_` fitted attribute holds the four-part dict (`ssm`/`scalogram`/`novelty`/`descriptors`), with `self.ssm_`/`self.scalogram_`/`self.scales_`/`self.novelty_`/`self.radii_`/`self.descriptors_` all still individually set
- `infodynamics/pipeline.py` no longer imports `infodynamics.text.embedding.Encoder` or `infodynamics.text.segmentation.{Level, segment}` — the Phase 2 interim exception (`02-CONTEXT.md` D-01/D-02, "resolved in Phase 3") is closed; `grep -En "infodynamics.text|segment\(|Encoder|\.encode\("` on the file returns nothing
- Both estimators verified to pass `sklearn.base.clone()` round-trips

## Task Commits

Each task was committed atomically:

1. **Task 1: Make InfoDynamics ndarray-only with array output and self.signal_ (CORE-02, D-02, D-03)** - `f1d9bbc` (feat)
2. **Task 2: Make MultiscaleInfoDynamics ndarray-only with scalogram-matrix output and self.result_ (CORE-02, D-02, D-03)** - `c823caf` (feat)

**Plan metadata:** (recorded below after this commit)

## Files Created/Modified
- `infodynamics/pipeline.py` - `InfoDynamics` and `MultiscaleInfoDynamics` both stripped of text-only constructor params and `segment()`/`Encoder.encode()` calls; both now `fit(X)` on embeddings ndarrays, delegating to the already-decoupled `WindowedRollingDistance`/`Scalogram`/`FooteNovelty`; `transform()`/`fit_transform()` converged onto array-return-with-rich-attribute per D-03 (`self.signal_` for `InfoDynamics`, `self.result_` for `MultiscaleInfoDynamics`)

## Decisions Made
- Locked `MultiscaleInfoDynamics.transform()`/`fit_transform()`'s primary array as `self.scalogram_` (the `(n_scales, n_chunks)` matrix) — D-03 explicitly left this choice to Claude's discretion, noting `MultiscaleInfoDynamics` may be legitimately Pipeline-terminal since none of its four heterogeneous outputs has an obvious single "the array" the way `Scalogram`/`FooteNovelty` do
- Committed the single-file `pipeline.py` rewrite as two atomic, task-scoped commits (matching the plan's Task 1/Task 2 split) by staging an intermediate state where `InfoDynamics` is fully decoupled while `MultiscaleInfoDynamics` and the module's text imports remained temporarily in place, then completing the second commit with `MultiscaleInfoDynamics`'s rewrite and the import cleanup

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Ran the full test suite after both tasks to confirm the plan-anticipated breakage stayed exactly where predicted: `tests/test_golden_baseline.py` fails collection (`InfoDynamics(encoder=..., window_size=3).fit_transform(text)` — `encoder` param no longer exists), `tests/test_pipeline.py` fails all 6 tests (still calls the old text-coupled `fit(text)` API), `tests/test_infodynamics_class.py::{test_calc_signal_data_shapes, test_window_size}` fail (both construct `InfoDynamics`/exercise the old text-coupled path), and `tests/text/test_morphology.py::{test_multiscale_info_dynamics_accepts_custom_encoder, test_fit_raises_without_model_name_or_encoder}` fail (2 tests, exactly as the plan's own `<verification>` section predicted). All other 58 tests pass. This is the documented wave-ordering artifact — Plan 06 migrates these call sites onto the new `TextInfoDynamics`/`TextMultiscaleInfoDynamics` wrappers (D-04, Plan 05) and re-verifies the golden baseline. No fix applied here, per the plan's own scope boundary.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `InfoDynamics` and `MultiscaleInfoDynamics` are now uniform, Pipeline-legal composite estimators (verbatim params, ndarray-only `fit`/`transform`/`fit_transform`, array output, `clone()`-safe) ready for Plan 05's `TextInfoDynamics`/`TextMultiscaleInfoDynamics` wrappers to compose `TextSegmenter → Encoder → InfoDynamics`/`MultiscaleInfoDynamics` internally
- `infodynamics/pipeline.py` has zero text imports — CORE-02's core substantive rewrite is complete
- Known, plan-anticipated breakage in `tests/test_pipeline.py`, 2 tests in `tests/test_infodynamics_class.py`, 2 tests in `tests/text/test_morphology.py`, and `tests/test_golden_baseline.py` collection remains unresolved by design — Plan 05 (text wrappers) and Plan 06 (golden re-verification + test migration) will close it

---
*Phase: 03-decouple-the-pipeline*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: infodynamics/pipeline.py
- FOUND: .planning/phases/03-decouple-the-pipeline/03-03-SUMMARY.md
- FOUND: commit f1d9bbc (Task 1)
- FOUND: commit c823caf (Task 2)

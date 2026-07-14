---
phase: 03-decouple-the-pipeline
plan: 05
subsystem: api
tags: [sklearn, scikit-learn, text, pipeline-composability, convenience-wrapper]

# Dependency graph
requires:
  - phase: 03-decouple-the-pipeline (Plan 02)
    provides: TextSegmenter/Encoder/MorphologicalEncoder as Pipeline-legal BaseEstimator+TransformerMixin text on-ramp estimators
  - phase: 03-decouple-the-pipeline (Plan 03)
    provides: InfoDynamics/MultiscaleInfoDynamics rewritten ndarray-only, no text imports in infodynamics/pipeline.py
provides:
  - TextInfoDynamics(BaseEstimator, TransformerMixin) composing TextSegmenter -> Encoder -> InfoDynamics in one fit(text)/fit_transform(text) call
  - TextMultiscaleInfoDynamics(BaseEstimator, TransformerMixin) composing TextSegmenter -> Encoder -> MultiscaleInfoDynamics in one fit(text)/fit_transform(text) call
  - infodynamics/text/__init__.py re-exports TextSegmenter, TextInfoDynamics, TextMultiscaleInfoDynamics
affects: [03-06, 03-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "D-04 convenience-wrapper pattern: relocate the pre-refactor InfoDynamics.fit/MultiscaleInfoDynamics.fit segment->encode->analyze body verbatim into a thin infodynamics.text wrapper, composing already-decoupled estimators rather than reimplementing logic"
    - "Duck-typed encoder dispatch: prefer encoder.fit_transform(texts) (sklearn-legal), fall back to encoder.encode(texts) for back-compat with legacy .encode()-only encoder objects (golden capture, custom test doubles)"

key-files:
  created:
    - infodynamics/text/pipeline.py
  modified:
    - infodynamics/text/__init__.py

key-decisions:
  - "Kept Task 1 (TextInfoDynamics) and Task 2 (TextMultiscaleInfoDynamics + __init__.py re-exports) as two separate atomic commits per the plan's task breakdown, even though both land in the same new file"
  - "Verified Task 1 functionally via a direct infodynamics.text.pipeline import before the __init__.py re-export existed (Task 2), then re-ran the plan's literal infodynamics.text import-based verify command after Task 2 landed — both pass"

patterns-established:
  - "infodynamics.text convenience wrappers mirror the OLD (pre-refactor) InfoDynamics/MultiscaleInfoDynamics text-facing __init__ signatures as a drop-in migration path, while the core infodynamics.pipeline estimators stay ndarray-only"

requirements-completed: [TEXT-02, API-01]

coverage:
  - id: D1
    description: "TextInfoDynamics composes TextSegmenter -> Encoder -> InfoDynamics in one fit(text)/fit_transform(text) call; exposes signal_/chunks_/embeddings_; guards on missing model_name/encoder; clone()-safe"
    requirement: "TEXT-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 1 <verify> block, re-run after Task 2's __init__.py update): shape assertion, signal_ dict keys, chunks_ length, ValueError guard message, clone() round-trip"
        status: pass
    human_judgment: false
  - id: D2
    description: "TextMultiscaleInfoDynamics composes TextSegmenter -> Encoder -> MultiscaleInfoDynamics in one fit(text)/fit_transform(text) call; exposes result_ plus all delegated fitted attrs (ssm_/scalogram_/novelty_/scales_/radii_/descriptors_); clone()-safe"
    requirement: "TEXT-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 2 <verify> block): output shape, result_ dict keys, descriptors_['n_chunks'] equality, clone() round-trip"
        status: pass
    human_judgment: false
  - id: D3
    description: "TextSegmenter, TextInfoDynamics, TextMultiscaleInfoDynamics all importable as infodynamics.text.<Name>; no __all__ added; top-level infodynamics/__init__.py untouched"
    requirement: "API-01"
    verification:
      - kind: unit
        ref: "grep -n __all__ infodynamics/text/__init__.py (no assignment found); git diff --stat infodynamics/__init__.py (empty)"
        status: pass
    human_judgment: false

# Metrics
duration: 8min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 05: Add TextInfoDynamics and TextMultiscaleInfoDynamics Convenience Wrappers Summary

**D-04 convenience wrappers restore one-call `fit_transform(text)` ergonomics: `TextInfoDynamics` and `TextMultiscaleInfoDynamics` compose `TextSegmenter -> Encoder -> InfoDynamics`/`MultiscaleInfoDynamics` under `infodynamics.text`, relocating the pre-refactor text-coupled `fit()` bodies verbatim**

## Performance

- **Duration:** 8 min
- **Started:** 2026-07-14T12:26:00Z
- **Completed:** 2026-07-14T12:34:15Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `infodynamics/text/pipeline.py` with `TextInfoDynamics(BaseEstimator, TransformerMixin)`: mirrors the pre-refactor `InfoDynamics` text-facing `__init__` signature (`model_name`, `encoder`, `segment_level`, `chunk_size`, `measure`, `window_size`, `jump_size`, `estimate_error`, `device`, `batch_size`), raises the same `ValueError` guard (now moved out of the ndarray-only core `InfoDynamics` per Plan 03), and composes `TextSegmenter.fit_transform(text) -> Encoder(.fit_transform|.encode) -> InfoDynamics.fit(embeddings)` in one `fit(text)` call
- Added `TextMultiscaleInfoDynamics(BaseEstimator, TransformerMixin)` to the same file, mirroring the pre-refactor `MultiscaleInfoDynamics` text-facing signature (`scales`, `radii`, `measure` plus the same segmenter/encoder params), composing the identical segment->encode chain into `MultiscaleInfoDynamics.fit(embeddings)`, and delegating `result_`/`ssm_`/`scalogram_`/`novelty_`/`scales_`/`radii_`/`descriptors_` from the wrapped instance
- Both wrappers duck-type the encoder: use `encoder.fit_transform(texts)` when available (sklearn-legal `Encoder`/any Pipeline-style transformer), fall back to `np.asarray(encoder.encode(texts))` for legacy `.encode()`-only encoders (the golden capture's shared `Encoder` instance, custom test doubles)
- Updated `infodynamics/text/__init__.py` to re-export `TextSegmenter`, `TextInfoDynamics`, `TextMultiscaleInfoDynamics` — all three now importable as `infodynamics.text.<Name>`; no `__all__` added (curation deferred to Phase 4/API-03); top-level `infodynamics/__init__.py` untouched
- Both wrappers pass `sklearn.base.clone()` round-trips

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TextInfoDynamics wrapper (D-04, TEXT-02)** - `7cdf97d` (feat)
2. **Task 2: Create TextMultiscaleInfoDynamics wrapper + re-export both wrappers and TextSegmenter (D-04, TEXT-02)** - `bc4df8c` (feat)

**Plan metadata:** (recorded below after this commit)

## Files Created/Modified
- `infodynamics/text/pipeline.py` - New file: `TextInfoDynamics` and `TextMultiscaleInfoDynamics`, both `BaseEstimator, TransformerMixin`, composing `TextSegmenter -> Encoder -> {InfoDynamics, MultiscaleInfoDynamics}` in one `fit(text)`/`fit_transform(text)` call
- `infodynamics/text/__init__.py` - Added re-exports for `TextSegmenter`, `TextInfoDynamics`, `TextMultiscaleInfoDynamics`; module docstring updated to reflect `__all__` curation is a later-phase concern

## Decisions Made
- Kept Task 1 and Task 2 as two separate atomic commits matching the plan's task breakdown, even though both edit `infodynamics/text/pipeline.py` (Task 2 appends `TextMultiscaleInfoDynamics` to the file Task 1 created)
- Task 1's own `<verify>` block references `from infodynamics.text import TextInfoDynamics`, which only becomes valid after Task 2's `__init__.py` re-export lands — verified Task 1 functionally via the equivalent direct `infodynamics.text.pipeline` import first, then re-ran the plan's literal `infodynamics.text`-import verify command after Task 2 completed; both pass

## Deviations from Plan

None - plan executed exactly as written. (One minor ordering note under "Decisions Made" above: Task 1's verify block textually depends on Task 2's `__init__.py` change, which is inherent to the plan's own task split, not a deviation from it — the plan's full verification suite passes end-to-end.)

## Issues Encountered

Ran `tests/text/` after both tasks: 20/22 pass. The 2 failures (`test_multiscale_info_dynamics_accepts_custom_encoder`, `test_fit_raises_without_model_name_or_encoder` in `tests/text/test_morphology.py`) are the pre-existing, Plan-03-documented breakage — these tests still construct `infodynamics.pipeline.MultiscaleInfoDynamics` directly with the old text-coupled params (`encoder=`, raw `text` fit input), which no longer exists on the now-ndarray-only core class. Plan 03's summary explicitly flagged these as its own anticipated breakage, to be closed by Plan 06's test migration onto the new `TextInfoDynamics`/`TextMultiscaleInfoDynamics` wrappers built here. Left untouched per scope boundary. Full non-golden/pipeline/infodynamics_class test suite otherwise green (55 passed, same 2 known failures, no new regressions).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `TextInfoDynamics` and `TextMultiscaleInfoDynamics` are ready for Plan 06 to consume in the golden re-capture script and in migrating `tests/text/test_morphology.py`'s two currently-failing tests off the old text-coupled `MultiscaleInfoDynamics` API
- Plan 07's Pipeline composition test can reference these wrappers, `TextSegmenter`, `Encoder`, `InfoDynamics`, and `MultiscaleInfoDynamics` as the full set of Pipeline-legal building blocks
- Known, Plan-03-anticipated breakage in `tests/text/test_morphology.py` (2 tests) and `tests/test_golden_baseline.py`/`tests/test_pipeline.py`/`tests/test_infodynamics_class.py` collection remains unresolved by design — still Plan 06's responsibility

---
*Phase: 03-decouple-the-pipeline*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: infodynamics/text/pipeline.py
- FOUND: infodynamics/text/__init__.py
- FOUND: .planning/phases/03-decouple-the-pipeline/03-05-SUMMARY.md
- FOUND: commit 7cdf97d (Task 1)
- FOUND: commit bc4df8c (Task 2)

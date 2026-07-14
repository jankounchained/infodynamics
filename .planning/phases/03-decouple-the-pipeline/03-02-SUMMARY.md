---
phase: 03-decouple-the-pipeline
plan: 02
subsystem: api
tags: [sklearn, scikit-learn, text, embedding, morphology, pipeline-composability]

# Dependency graph
requires:
  - phase: 02-reorganize-into-core-text-on-ramp
    provides: infodynamics/text/segmentation.py, embedding.py, morphology.py at their post-reorg module paths
provides:
  - TextSegmenter estimator (BaseEstimator+TransformerMixin) wrapping segment(); transform(text) returns List[str], chunks_ preserves List[Chunk] span info
  - Encoder as a Pipeline-legal BaseEstimator+TransformerMixin with fit/transform wrapping encode()
  - MorphologicalEncoder as a Pipeline-legal BaseEstimator+TransformerMixin with fit/transform wrapping encode()
  - _MODEL_CACHE keyed by (model_name, device); in-place .to(device) mutation removed (QA-02 fixed)
affects: [03-05, 03-06, 03-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TextSegmenter.transform(text) returns List[str] (plain chunk texts); List[Chunk] span info preserved as the fitted attribute chunks_ (D-01)"
    - "Thin fit()/transform() wrappers delegating to an already-correct .encode() method, applied identically to both Encoder and MorphologicalEncoder"
    - "Lazy heavy-import pattern (sentence_transformers, spacy_udpipe, textdescriptives) preserved inside encode()/_load_model/_load_pipeline — never at class-definition or __init__ time"
    - "Model cache keyed by a tuple of every parameter that changes model identity ((model_name, device)) rather than mutating a shared cached instance in place"

key-files:
  created: []
  modified:
    - infodynamics/text/segmentation.py
    - infodynamics/text/embedding.py
    - infodynamics/text/morphology.py

key-decisions:
  - "QA-02 cache fix and the Encoder Pipeline-wrapper change kept as two separate labeled commits (fix vs feat) per ROADMAP criterion 5, even though both touch embedding.py"
  - "_load_model now takes device and constructs SentenceTransformer(model_name, device=device) at load time instead of mutating a cached model's device after the fact"

patterns-established:
  - "Every text on-ramp estimator (TextSegmenter, Encoder, MorphologicalEncoder) is now BaseEstimator+TransformerMixin with clone-safe get_params/set_params, ready for Plan 05's TextInfoDynamics/TextMultiscaleInfoDynamics composition and Plan 07's Pipeline composition test"

requirements-completed: [TEXT-02, API-01, QA-02]

coverage:
  - id: D1
    description: "TextSegmenter estimator added: transform(text) returns List[str], chunks_ fitted attribute preserves List[Chunk] span info, clone-round-trip safe"
    requirement: "TEXT-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 1 <verify> block): isinstance BaseEstimator/TransformerMixin, fit_transform returns List[str] len 3, chunks_ is List[Chunk], get_params, clone()"
        status: pass
      - kind: unit
        ref: "tests/text/test_segmentation.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "_MODEL_CACHE keyed by (model_name, device); in-place .to(self.device) mutation removed so a second Encoder with a different device no longer mutates another instance's cached model (QA-02)"
    requirement: "QA-02"
    verification:
      - kind: unit
        ref: "python -c smoke check (Task 2 <verify> block): grep confirms no .to(self.device) call, _MODEL_CACHE annotation is Tuple-keyed, import infodynamics.text.embedding succeeds"
        status: pass
    human_judgment: false
  - id: D3
    description: "Encoder and MorphologicalEncoder are BaseEstimator+TransformerMixin with fit/transform/get_params/set_params, clone-safe, and stay import-lazy (no sentence-transformers/spacy-udpipe/textdescriptives import at module or class-definition time)"
    requirement: "API-01"
    verification:
      - kind: unit
        ref: "python -c smoke checks (Task 2 and Task 3 <verify> blocks): isinstance checks, clone(), get_params, lazy-import regression (import infodynamics.text.embedding / .morphology succeed standalone), invalid feature_group still raises ValueError at construction"
        status: pass
      - kind: unit
        ref: "tests/text/test_morphology.py"
        status: pass
    human_judgment: false

# Metrics
duration: 3min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 02: Build the Text On-Ramp Estimators (TextSegmenter, Encoder, MorphologicalEncoder) Summary

**New `TextSegmenter` estimator wrapping `segment()`, plus `Encoder`/`MorphologicalEncoder` converted to Pipeline-legal `BaseEstimator`/`TransformerMixin` classes, with the QA-02 `_MODEL_CACHE` device-mutation bug fixed as its own labeled commit**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-14T12:06:03Z
- **Completed:** 2026-07-14T12:09:45Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added `TextSegmenter(BaseEstimator, TransformerMixin)` to `infodynamics/text/segmentation.py`: wraps the existing `segment()` unchanged, `transform(text)` returns `List[str]` (plain chunk texts) per D-01, `chunks_` fitted attribute preserves the full `List[Chunk]` span info
- Fixed QA-02 in `infodynamics/text/embedding.py`: `_MODEL_CACHE` re-keyed from `Dict[str, object]` to `Dict[Tuple[str, Optional[str]], object]` (`(model_name, device)`); removed the in-place `model.to(self.device)` mutation — `_load_model` now constructs `SentenceTransformer(model_name, device=device)` at load time so a second `Encoder` with a different device resolves to a distinct cache entry instead of mutating a shared model
- Made `Encoder` and `MorphologicalEncoder` Pipeline-legal: both now subclass `BaseEstimator, TransformerMixin` with thin `fit()` (no-op, returns `self`) / `transform()` (delegates to the existing `.encode()`) wrappers; `__init__` signatures, existing validation (`MorphologicalEncoder`'s `feature_group` check), and both classes' lazy heavy-import patterns are untouched
- All three text on-ramp classes are now `clone()`-safe with working `get_params`/`set_params`, and `import infodynamics.text` / `import infodynamics.text.embedding` / `import infodynamics.text.morphology` still succeed without the embedding/morphology extras installed

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the TextSegmenter estimator (D-01, TEXT-02)** - `7513a04` (feat)
2. **Task 2a: Fix _MODEL_CACHE device-mutation bug (QA-02)** - `f48be4f` (fix)
2. **Task 2b: Make Encoder Pipeline-legal (TEXT-02)** - `d0a3f72` (feat)
3. **Task 3: Make MorphologicalEncoder Pipeline-legal (TEXT-02)** - `f3ad823` (feat)

**Plan metadata:** (recorded below after this commit)

## Files Created/Modified
- `infodynamics/text/segmentation.py` - Added `TextSegmenter(BaseEstimator, TransformerMixin)`; `segment()`, `strip_markdown()`, `Chunk` untouched
- `infodynamics/text/embedding.py` - `_MODEL_CACHE` re-keyed by `(model_name, device)`, in-place `.to()` mutation removed (QA-02); `Encoder` now `BaseEstimator, TransformerMixin` with `fit`/`transform`
- `infodynamics/text/morphology.py` - `MorphologicalEncoder` now `BaseEstimator, TransformerMixin` with `fit`/`transform`; `_PIPELINE_CACHE` and `__init__` validation untouched

## Decisions Made
- Kept the QA-02 cache-key fix and the Encoder estimator-wrapper change as two separate labeled commits in `embedding.py` (fix vs feat), per ROADMAP criterion 5's requirement that bug fixes stay separate and labeled from API-shape changes, even though both land in the same file within the same task
- `_load_model` now takes an explicit `device` parameter and constructs the model on that device at load time (`SentenceTransformer(model_name, device=device)`) rather than mutating a cached model's device after the fact — matches `morphology.py`'s already-correct `_PIPELINE_CACHE` tuple-key pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Ran the plan's overall verification (`import infodynamics` / `import infodynamics.text`, `tests/text/test_segmentation.py`, `tests/text/test_morphology.py` — 22 passed) plus a full-suite sanity check excluding the three files with known pre-existing breakage from Plan 01 (`tests/test_golden_baseline.py`, `tests/test_pipeline.py`, `tests/test_infodynamics_class.py` — `InfoDynamics.fit()` still indexes `WindowedRollingDistance`'s now-ndarray output as a dict, exactly the breakage Plan 01's summary documented as Plan 03's responsibility to resolve). The remaining 57 tests pass; no new regressions were introduced by this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `TextSegmenter`, `Encoder`, and `MorphologicalEncoder` are now uniform, Pipeline-legal building blocks (verbatim params, working `fit`/`transform`, `clone()`-safe, import-lazy) ready for Plan 03's `InfoDynamics`/`MultiscaleInfoDynamics` rewrite to consume via `TextSegmenter.transform(text) -> List[str] -> Encoder.transform(...) -> ndarray`
- Plan 05's `TextInfoDynamics`/`TextMultiscaleInfoDynamics` convenience wrappers (D-04) can now compose these three estimators directly
- Known, Plan-01-documented breakage in `tests/test_pipeline.py`, `tests/test_infodynamics_class.py`, and `tests/test_golden_baseline.py` collection remains unresolved by design — still Plan 03's (pipeline.py rewrite) and Plan 06's (golden re-verification) responsibility, untouched by this plan

---
*Phase: 03-decouple-the-pipeline*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: infodynamics/text/segmentation.py
- FOUND: infodynamics/text/embedding.py
- FOUND: infodynamics/text/morphology.py
- FOUND: .planning/phases/03-decouple-the-pipeline/03-02-SUMMARY.md
- FOUND: commit 7513a04 (Task 1)
- FOUND: commit f48be4f (Task 2a - QA-02 fix)
- FOUND: commit d0a3f72 (Task 2b - Encoder wrapper)
- FOUND: commit f3ad823 (Task 3)
</content>

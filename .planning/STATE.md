---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 04
current_phase_name: curate-the-public-api
status: verifying
stopped_at: Phase 4 context gathered
last_updated: "2026-07-14T14:49:00.454Z"
last_activity: 2026-07-14
last_activity_desc: Phase 04 execution started
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 15
  completed_plans: 15
  percent: 80
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-13)

**Core value:** One clean, sklearn-compatible library that computes novelty/structure signals from any numeric time series — with text as a first-class but separable on-ramp — free of dashboard and case-study baggage.
**Current focus:** Phase 04 — curate-the-public-api

## Current Position

Phase: 04 (curate-the-public-api) — EXECUTING
Plan: 2 of 2
Status: Phase complete — ready for verification
Last activity: 2026-07-14 — Phase 04 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 13
- Average duration: - min
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4 | - | - |
| 02 | 2 | - | - |
| 03 | 7 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01 P01 | 15 | 2 tasks | 5 files |
| Phase 01-baseline-removal P02 | 16min | 2 tasks | 11 files |
| Phase 01 P03 | 12min | 2 tasks | 0 files |
| Phase 01 P04 | 2min | 2 tasks | 2 files |
| Phase 02 P01 | 15min | 2 tasks | 11 files |
| Phase 02 P02 | 10min | 2 tasks | 0 files |
| Phase 03 P01 | 4min | 3 tasks | 2 files |
| Phase 03 P02 | 3min | 3 tasks tasks | 3 files files |
| Phase 03 P03 | 6min | 2 tasks | 1 files |
| Phase 03 P04 | 6min | 2 tasks | 2 files |
| Phase 03 P05 | 8min | 2 tasks | 2 files |
| Phase 03 P06 | 6min | 2 tasks tasks | 3 files files |
| Phase 03 P07 | 6min | 2 tasks | 1 files |
| Phase 04 P01 | 6min | 2 tasks tasks | 4 files files |
| Phase 04 P02 | 5min | 2 tasks tasks | 2 files files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: subtractive-before-additive, move-before-refactor phase ordering (Remove → Reorganize → Decouple → Curate → Verify) chosen so numerical drift stays bisectable
- Roadmap: golden-output baseline captured as prerequisite work inside Phase 1, re-verified at close of every subsequent phase
- Roadmap: all flagged bugs (QA-02) and test debt (QA-03) fixed this milestone, attached to Phase 3 as their own labeled commits — not deferred
- [Phase 01-01]: Golden-output snapshot pattern established: tests/golden/ one-time capture script + checked-in .npz/.json + permanent pytest comparison test, reused at close of every subsequent phase
- [Phase 01-02]: Recalculated expected post-removal pytest collection count as 72 (not the plan's hardcoded 68), accounting for 4 golden-baseline tests Plan 01 added before this plan ran
- [Phase 01-03]: Investigated test_window_size failure surfaced during full-suite re-run; confirmed pre-existing (predates Phase 01 per .hypothesis/ cache mtime and git history) and already tracked as QA-03 for Phase 3 fix — left unfixed per scope boundary.
- [Phase ?]: [Phase 01-04] Implemented both halves of CR-01 fix (importorskip guards AND self-sufficient test extra) per reviewer recommendation, rather than choosing one
- [Phase ?]: benchmark_embedding.py: fixed its two imports + docstring in this pass rather than deferring (tracked file, zero-dangling-reference spirit)
- [Phase ?]: infodynamics/text/__init__.py stays docstring-only, no re-exports yet (D-03) — export curation deferred to Phase 4
- [Phase ?]: Confirmed test_window_size failure (71/1) is pre-existing QA-03, not a Phase 2 regression -- deferred to Phase 3 per existing decision log
- [Phase 03]: [Phase 03-01] Locked WindowedRollingDistance's stacked-array column order as novelty/transience/resonance (N_hat/T_hat/R_hat), per D-03's discretion note
- [Phase 03]: [Phase 03-01] Converged WindowedRollingDistance._validate_data to a single np.asarray(X) idiom, matching every other estimator's validation pattern in the codebase
- [Phase 03]: [Phase 03-02] Kept the QA-02 _MODEL_CACHE device-mutation fix as a separate labeled commit from the Encoder Pipeline-wrapper change in embedding.py, per ROADMAP criterion 5
- [Phase 03]: [Phase 03-02] _load_model now constructs SentenceTransformer(model_name, device=device) at load time instead of mutating a cached model's device after the fact, matching morphology.py's already-correct tuple-keyed _PIPELINE_CACHE pattern
- [Phase 03]: [Phase 03-03] MultiscaleInfoDynamics.transform()/fit_transform() return self.scalogram_ as the primary array; MultiscaleInfoDynamics may be legitimately Pipeline-terminal (D-03 discretion)
- [Phase 03]: [Phase 03-03] Split single-file pipeline.py rewrite into two atomic task commits by staging an intermediate state (InfoDynamics decoupled, MultiscaleInfoDynamics + text imports temporarily unchanged)
- [Phase 03-04]: Fixed WindowedRollingDistance window_size=0 crash/NaN bug (Rule 1) surfaced while implementing test_transience_calculation's required w=0 no-NaN assertion
- [Phase ?]: [Phase 03-05] Kept Task 1 (TextInfoDynamics) and Task 2 (TextMultiscaleInfoDynamics + __init__.py re-exports) as two separate atomic commits per the plan's task breakdown, even though both land in infodynamics/text/pipeline.py
- [Phase ?]: [Phase 03-05] Task 1's verify block references importing TextInfoDynamics from infodynamics.text, valid only after Task 2's __init__.py re-export lands - verified functionally via direct submodule import first, then re-ran the plan's literal verify command after Task 2 completed
- [Phase ?]: [Phase 03-06] No numeric-behavior changes were needed to migrate tests to the Text* wrappers -- purely call-site/API-shape migration, empirically confirming CORE-02/QA-02's decoupling and bug fixes stayed non-numerical
- [Phase ?]: [Phase 03-06] Golden baseline re-verified: tests/test_golden_baseline.py passes 4/4 against the EXISTING, unmodified baseline_arrays.npz/baseline_meta.json -- zero numerical drift proven across Phase 3's Plans 01/02/03/05
- [Phase ?]: [Phase 03-07] Split the single new test file into two atomic commits (clone round-trip, then Pipeline composition) matching the plan's Task 1/Task 2 boundary
- [Phase ?]: [Phase 03-07] test_pipeline_with_real_encoder uses a 50-sentence synthetic text (not the shared 10-sentence fixture) because MultiscaleInfoDynamics()'s literal criterion-4 defaults require n_chunks >= 43 for every scale/radius to fit
- [Phase 04-01]: infodynamics.__all__ = exactly 8 core symbols per D-01; zero .text imports remain (D-05)
- [Phase 04-01]: infodynamics.text.__all__ folds in Encoder/MorphologicalEncoder/Chunk/segment/strip_markdown alongside the 3 existing Text* wrappers, per Claude's-discretion note
- [Phase 04-02]: examples/basic_usage.py demonstrates core_only_demo() (ndarray -> InfoDynamics/MultiscaleInfoDynamics, zero infodynamics.text imports) and pipeline_demo() (sklearn.pipeline.Pipeline([TextSegmenter, Encoder, MultiscaleInfoDynamics]).fit_transform), no examples/__init__.py
- [Phase 04-02]: CHANGELOG.md written as a flat old->new import migration table (not Keep-a-Changelog prose), kept as a dedicated root file rather than folded into README.md

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 3 (Decouple the Pipeline) is the substantive, riskiest phase — flagged in research for deeper design discussion at plan time (transform(X_new) semantics, dict-returning fit_transform vs Pipeline chaining, possible TextInfoDynamics convenience wrapper). See ROADMAP.md Phase 3 "Research flag".
- test_window_size (tests/test_infodynamics_class.py) fails on window_size=0 edge case — pre-existing bug, already tracked as QA-03, scheduled for Phase 3 fix with a deliberate golden-snapshot update.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-07-14T14:47:23.111Z
Stopped at: Phase 4 context gathered
Resume file: .planning/phases/04-curate-the-public-api/04-CONTEXT.md

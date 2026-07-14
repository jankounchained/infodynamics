---
phase: 04-curate-the-public-api
plan: 02
subsystem: docs
tags: [examples, changelog, public-api, migration-note, sklearn-pipeline]

# Dependency graph
requires:
  - phase: 04-curate-the-public-api
    plan: 01
    provides: "Curated infodynamics.__all__ (8 core symbols, zero .text imports) and infodynamics.text.__all__ (8 text symbols) — the exact import surface this plan's example and CHANGELOG must reference"
provides:
  - "examples/basic_usage.py: canonical, runnable core-only + full Pipeline demonstration of the curated public API"
  - "CHANGELOG.md: flat old->new import-path migration table for every symbol that moved this milestone"
affects: [future-dashboard-migration, downstream-consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "examples/ as a plain non-package docs directory (no __init__.py) — excluded from find_packages() by construction, not by MANIFEST.in exclusion"
    - "Flat old->new import migration table instead of Keep-a-Changelog prose sections — appropriate for a pre-1.0, unpublished, one-time internal reorg rather than a versioned release history"

key-files:
  created:
    - examples/basic_usage.py
    - CHANGELOG.md
  modified: []

key-decisions:
  - "examples/basic_usage.py demonstrates core_only_demo() (ndarray -> InfoDynamics/MultiscaleInfoDynamics, zero infodynamics.text imports) and pipeline_demo() (sklearn.pipeline.Pipeline([TextSegmenter, Encoder, MultiscaleInfoDynamics]).fit_transform(text)) as two clearly separated functions called from a __main__ guard"
  - "No examples/__init__.py created — examples/ stays a plain docs directory, automatically excluded from find_packages()"
  - "CHANGELOG.md written as a flat old->new import-path table (per RESEARCH.md's Alternatives Considered), not Keep-a-Changelog Added/Changed/Removed prose, and kept as a dedicated root file rather than folded into the still-empty README.md"
  - "CHANGELOG covers all 5 migrated symbols (MorphologicalEncoder, Chunk, segment, strip_markdown, Encoder) plus the 3 new Phase 3 Text* wrappers with no old path, and explicitly restates the pre-1.0 no-back-compat-shim policy and the 8 core symbols unaffected by the migration"

requirements-completed: [API-04]

coverage:
  - id: D1
    description: "examples/basic_usage.py runs end-to-end via .venv/bin/python examples/basic_usage.py with exit code 0, no examples/__init__.py present"
    requirement: "API-04"
    verification:
      - kind: smoke
        ref: ".venv/bin/python examples/basic_usage.py (manual run, exit 0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "core_only_demo() imports only from infodynamics (and numpy), zero infodynamics.text imports"
    requirement: "API-04"
    verification:
      - kind: manual
        ref: "Code inspection of examples/basic_usage.py:core_only_demo"
        status: pass
    human_judgment: true
  - id: D3
    description: "pipeline_demo() composes sklearn.pipeline.Pipeline([TextSegmenter, Encoder, MultiscaleInfoDynamics]).fit_transform(text) on a >= 50-sentence text"
    requirement: "API-04"
    verification:
      - kind: smoke
        ref: ".venv/bin/python examples/basic_usage.py (manual run, prints scalogram shape (6, 50))"
        status: pass
    human_judgment: false
  - id: D4
    description: "CHANGELOG.md exists at repo root with old->new rows for MorphologicalEncoder, Chunk, segment, strip_markdown, Encoder"
    requirement: "API-04"
    verification:
      - kind: automated
        ref: "grep checks in plan's <verify> block (all matched)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full pytest suite stays green after both new files land (no collection/behavior regression)"
    requirement: "API-04"
    verification:
      - kind: unit
        ref: "pytest -q (91 passed, 0 failed)"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-07-14
status: complete
---

# Phase 4 Plan 02: Canonical Example and CHANGELOG Summary

**New `examples/basic_usage.py` runnably demonstrates both the modality-agnostic core-only path and the full text-on-ramp -> analysis `sklearn.pipeline.Pipeline` composition; new `CHANGELOG.md` gives downstream consumers a mechanical old->new import-path table for every symbol this milestone's reorg moved.**

## Performance

- **Duration:** ~5 min
- **Completed:** 2026-07-14
- **Tasks:** 2
- **Files modified:** 2 (both created)

## Accomplishments
- `examples/basic_usage.py` runs end-to-end with exit code 0, printing shapes for both demonstrated paths: `InfoDynamics.fit_transform` -> `(60, 3)`, `MultiscaleInfoDynamics.fit_transform` -> `(6, 60)` (core-only path, zero `infodynamics.text` imports), and the full `Pipeline.fit_transform(text)` -> `(6, 50)` (text on-ramp -> analysis, using the real `sentence-transformers` `Encoder`, which is installed in this dev venv)
- No `examples/__init__.py` was created — `examples/` stays a plain, non-package docs directory, correctly excluded from `find_packages()` by construction
- `CHANGELOG.md` created at repo root as a flat old->new import migration table covering `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown` (all: old `infodynamics`/pre-milestone submodule import -> new `infodynamics.text` import), `Encoder` (pre-milestone `infodynamics.embedding` -> new `infodynamics.text`), plus the three Phase-3-added `Text*` wrappers documented as new-with-no-old-path
- Full pytest suite verified green (91 passed) after both additions — no import or collection regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the canonical usage example (core-only path + full Pipeline path)** - `0dc0fa9` (feat)
2. **Task 2: Write the CHANGELOG old->new import migration note** - `5313af8` (docs)

**Plan metadata:** (final commit follows this summary)

## Files Created/Modified
- `examples/basic_usage.py` - New: `core_only_demo()` (ndarray -> `InfoDynamics`/`MultiscaleInfoDynamics`, no text imports) and `pipeline_demo()` (`sklearn.pipeline.Pipeline([TextSegmenter, Encoder, MultiscaleInfoDynamics]).fit_transform(text)` on a 50-sentence synthetic text), invoked from an `if __name__ == "__main__":` guard
- `CHANGELOG.md` - New: flat old->new import migration table, phase-by-phase narrative of the reorg, list of the 8 core symbols unaffected by the migration, and a pointer to `examples/basic_usage.py`

## Decisions Made
- Mirrored `tests/test_pipeline_composition.py::test_pipeline_with_real_encoder`'s exact Pipeline shape and 50-sentence synthetic text pattern for `pipeline_demo()`, per the plan's `<read_first>` guidance, so the example is provably representative of an already-tested code path.
- Used the module docstring to note the `embedding` extra requirement for `pipeline_demo()` rather than gating the demo behind a try/except or `pytest.importorskip`-style guard — the plan's acceptance criteria call for the script to "complete with exit code 0" unconditionally, and `sentence-transformers` is confirmed installed in this dev venv, so no guard was needed for this run.
- Kept `CHANGELOG.md` as a dedicated root file, not folded into the still-empty `README.md`, per `04-CONTEXT.md`'s explicit discretion note and to avoid entangling this migration doc with README's undecided future scope.
- Documented both the pre-Phase-2 submodule import forms (`infodynamics.segmentation`, `infodynamics.embedding`, `infodynamics.morphology`) and the Phase-2-to-Phase-4 top-level `infodynamics` re-export forms as "old" paths in the migration table, since both were real, working import paths at different points before this phase's `__all__` curation — not just the single most-recent one.

## Deviations from Plan

None - plan executed exactly as written. Both files match every structural and content requirement in the plan's `<action>` and `<acceptance_criteria>` blocks; no auto-fixes, blockers, or architectural questions arose.

## Issues Encountered
None. The Pipeline demo path required the `embedding` extra (`sentence-transformers`), which was already present in `.venv` (confirmed before writing the script), so the full example ran green on the first attempt with no stub/guard needed.

## User Setup Required
None - no external service configuration required. (The Pipeline demo does trigger a one-time HuggingFace Hub model weight load for `sentence-transformers/all-MiniLM-L6-v2`, cached locally on first run — this is pre-existing library behavior, not new setup.)

## Next Phase Readiness
- API-04 fully satisfied: canonical example (core-only + Pipeline) and CHANGELOG migration note both present and verified.
- Phase 4 (Curate the Public API) is now fully complete: API-03 (Plan 01) and API-04 (this plan) both satisfied, full pytest suite green (91 passed), zero numerical drift.
- No further plans remain in this phase per `04-PLAN.md`'s frontmatter (`depends_on: [04-01]`, no downstream plan references `04-02`).

---
*Phase: 04-curate-the-public-api*
*Completed: 2026-07-14*

## Self-Check: PASSED

All created files verified present on disk (`examples/basic_usage.py`, `CHANGELOG.md`, `04-02-SUMMARY.md`); both task commit hashes (`0dc0fa9`, `5313af8`) verified in git log.

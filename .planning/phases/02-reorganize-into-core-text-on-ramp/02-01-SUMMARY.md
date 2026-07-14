---
phase: 02-reorganize-into-core-text-on-ramp
plan: 01
subsystem: core-reorg
tags: [python, sklearn, package-layout, git-mv, import-paths]

# Dependency graph
requires:
  - phase: 01-baseline-removal
    provides: golden-output baseline (tests/golden/) used to verify zero numerical drift after this move
provides:
  - infodynamics/text/ subpackage housing segmentation.py, embedding.py, morphology.py
  - tests/text/ subpackage mirroring the two relocated unit test files
  - infodynamics/__init__.py and infodynamics/pipeline.py repointed to infodynamics.text.*
  - tests/golden/capture_baseline.py and benchmark_embedding.py repointed to infodynamics.text.*
affects: [phase-02-plan-02, phase-03-decouple-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: ["git mv for file relocation preserving history", "import-path-only edits with byte-identical logic"]

key-files:
  created:
    - infodynamics/text/__init__.py
    - tests/text/__init__.py
  modified:
    - infodynamics/__init__.py
    - infodynamics/pipeline.py
    - tests/golden/capture_baseline.py
    - benchmark_embedding.py

key-decisions:
  - "benchmark_embedding.py: fixed its two imports + docstring in this pass rather than deferring (tracked file, contradicts zero-dangling-reference spirit if left broken) — logged in the plan's Decisions section"
  - "infodynamics/text/__init__.py is docstring-only, no re-exports yet (D-03) — export curation deferred to Phase 4 (API-03/API-04)"
  - "infodynamics/pipeline.py stays at its current path and keeps a documented interim import dependency on infodynamics.text (D-01) — Phase 3 removes the coupling, not this phase"

patterns-established:
  - "Text on-ramp modules live under infodynamics/text/; test mirror lives under tests/text/"

requirements-completed: [TEXT-01, CORE-01, TEXT-03]

coverage:
  - id: D1
    description: "segmentation.py, embedding.py, morphology.py relocated to infodynamics/text/ via git mv, byte-identical content, lazy heavy-dep import guards preserved"
    requirement: "TEXT-01"
    verification:
      - kind: unit
        ref: ".venv/bin/python -c \"import infodynamics; import infodynamics.text; import infodynamics.text.segmentation; import infodynamics.text.embedding; import infodynamics.text.morphology\""
        status: pass
    human_judgment: false
  - id: D2
    description: "infodynamics/__init__.py and infodynamics/pipeline.py repointed to infodynamics.text.* (imports + docstring prose); no analysis module beyond pipeline.py's documented D-01 exception imports text"
    requirement: "CORE-01"
    verification:
      - kind: unit
        ref: "grep -vE '^[[:space:]]*#' infodynamics/pipeline.py | grep -cE 'infodynamics\\.(embedding|morphology|segmentation)' == 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "import infodynamics and import infodynamics.text (and submodules) succeed with no top-level heavy-dependency imports introduced"
    requirement: "TEXT-03"
    verification:
      - kind: unit
        ref: "grep -cE '^(import|from) (sentence_transformers|spacy_udpipe|textdescriptives)' infodynamics/text/embedding.py infodynamics/text/morphology.py == 0 for both files"
        status: pass
    human_judgment: false
  - id: D4
    description: "tests/text/test_segmentation.py and tests/text/test_morphology.py relocated and repointed; full suite still green (71/72, 1 pre-existing unrelated failure); golden snapshot byte-identical"
    verification:
      - kind: unit
        ref: ".venv/bin/python -m pytest tests/text/ -q (22 passed)"
        status: pass
      - kind: unit
        ref: ".venv/bin/python -m pytest -q (71 passed, 1 pre-existing failure: test_window_size, tracked as QA-03)"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-07-14
status: complete
---

# Phase 2 Plan 1: Relocate Text Modules Into infodynamics.text Summary

**Pure `git mv` relocation of segmentation.py, embedding.py, and morphology.py into `infodynamics/text/`, with mirrored tests under `tests/text/` and every tracked call site (core `__init__.py`, `pipeline.py`, golden baseline capture, benchmark script) repointed to the new import paths — zero behavior change, golden snapshot byte-identical.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-07-14
- **Tasks:** 2
- **Files modified:** 11 (3 relocated source modules, 2 relocated test files, 2 new `__init__.py`, 4 import-path-only edits)

## Accomplishments
- Relocated `infodynamics/segmentation.py`, `embedding.py`, and `morphology.py` into `infodynamics/text/` with `git mv` (history preserved), content byte-identical, lazy heavy-dependency `try/except ImportError` guards untouched
- Created `infodynamics/text/__init__.py` as a docstring-only module (D-03 — no re-exports yet, deferred to Phase 4)
- Repointed `infodynamics/__init__.py`'s two re-export lines and `infodynamics/pipeline.py`'s two functional imports + two docstring prose mentions to `infodynamics.text.*`
- Mirrored `tests/test_segmentation.py` and `tests/test_morphology.py` under `tests/text/` (git mv, history preserved), added empty `tests/text/__init__.py`
- Repointed the direct-submodule import in `tests/text/test_morphology.py` (left the re-export-surface import on line 11 untouched per D-04), `tests/golden/capture_baseline.py`'s `Encoder` import, and `benchmark_embedding.py`'s two imports + docstring mention

## Task Commits

Each task was committed atomically:

1. **Task 1: Move the three source modules into infodynamics/text/ and repoint the two core call sites** - `974ddb3` (feat)
2. **Task 2: Mirror the two test files under tests/text/ and repoint the remaining tracked call sites** - `1d1b4c0` (test)

**Plan metadata:** (pending — final docs commit follows this summary)

## Files Created/Modified
- `infodynamics/text/__init__.py` - new docstring-only module init (no re-exports, D-03)
- `infodynamics/text/segmentation.py` - relocated verbatim from `infodynamics/segmentation.py`
- `infodynamics/text/embedding.py` - relocated verbatim from `infodynamics/embedding.py`
- `infodynamics/text/morphology.py` - relocated verbatim from `infodynamics/morphology.py`
- `infodynamics/__init__.py` - two re-export RHS import paths updated to `infodynamics.text.*`
- `infodynamics/pipeline.py` - two functional imports + two docstring prose mentions updated to `infodynamics.text.*`
- `tests/text/__init__.py` - new empty file, mirrors `tests/golden/__init__.py`
- `tests/text/test_segmentation.py` - relocated from `tests/test_segmentation.py`, one import repointed
- `tests/text/test_morphology.py` - relocated from `tests/test_morphology.py`, one direct-submodule import repointed (re-export import on line 11 left as-is)
- `tests/golden/capture_baseline.py` - one `Encoder` import repointed; file location unchanged (D-08)
- `benchmark_embedding.py` - two imports + docstring prose mention repointed

## Decisions Made
- **benchmark_embedding.py: fixed, not deferred.** It is tracked in git, imports the two moving modules, and isn't named in any locked decision or ROADMAP grep scope — left it broken would contradict the phase's zero-dangling-reference intent. Repointed in the same pass as the other call sites (plan's explicit Decisions note).
- **infodynamics/text/__init__.py stays docstring-only** (D-03) — no `Chunk`/`segment`/`Encoder`/`MorphologicalEncoder` re-exports introduced at the `infodynamics.text` level; that's Phase 4's job (API-03/API-04).
- **infodynamics/pipeline.py's import dependency on infodynamics.text is a documented interim exception** (D-01) — its actual decoupling (removing the `segment()`/`Encoder.encode()` calls from `fit()`) is Phase 3's job.
- **Untracked root demo scripts left untouched** (`run_multiscale_demo.py`, `run_morphology_demo.py`, `segmentation_demo.py`) — explicitly out of scope; their post-move `ModuleNotFoundError` if run manually is expected, not a regression.
- **No `tests/text/test_embedding.py` added** (D-07) — pre-existing test-coverage gap, not this phase's job to fix.

## Deviations from Plan

None - plan executed exactly as written. All two tasks matched their `<action>` steps precisely; all acceptance criteria passed on first verification.

## Issues Encountered

None specific to this plan. The pre-existing `test_window_size` failure (tracked as QA-03 in STATE.md, scheduled for a Phase 3 fix with a deliberate golden-snapshot update) is present both before and after this plan's changes — confirmed it is not a regression introduced by the relocation; full-suite result is identical to the pre-move baseline (71 passed, 1 pre-existing failure, same as recorded in STATE.md prior to this plan).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `infodynamics/text/` and `tests/text/` subpackages are in place and importable; Plan 02 of this phase can proceed with any remaining CORE-01 grep sweep, structural inversion checks, `find_packages()` spot-check, and the no-extras smoke test called out in the plan's own verification section.
- Phase 3 (Decouple the Pipeline) can now target `infodynamics/pipeline.py`'s documented D-01 exception directly — the import paths it needs to remove already point at the final `infodynamics.text.*` locations.
- No blockers.

---
*Phase: 02-reorganize-into-core-text-on-ramp*
*Completed: 2026-07-14*

## Self-Check: PASSED

All created files found at expected paths; both task commits (974ddb3, 1d1b4c0) found in git log.

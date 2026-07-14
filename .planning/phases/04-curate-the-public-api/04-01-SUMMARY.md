---
phase: 04-curate-the-public-api
plan: 01
subsystem: api
tags: [python-packaging, __all__, sklearn-compatible, public-api]

# Dependency graph
requires:
  - phase: 03-decouple-the-pipeline
    provides: "TextInfoDynamics/TextMultiscaleInfoDynamics wrappers under infodynamics.text, deferred __all__ curation flagged as this phase's job"
provides:
  - "Explicit infodynamics.__all__ (8 core sklearn-facing symbols), zero .text imports in core __init__.py (D-05)"
  - "Explicit infodynamics.text.__all__ (8 text symbols), folding in Encoder/MorphologicalEncoder/Chunk/segment/strip_markdown"
  - "Permanent pytest contract (tests/test_public_api.py) locking both __all__ lists and the zero-.text-import invariant"
affects: [04-02-canonical-example-and-changelog, future-dashboard-migration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Curated __init__.py re-export style: plain `from module import Name` imports (no aliasing, no linter to appease) terminated by an explicit __all__ list — modeled on infodynamics/clustering/__init__.py"
    - "Submodule reachability without top-level export: names deliberately excluded from __all__ (viz, metrics, scalogram internals, clustering helpers) remain reachable via `from infodynamics import <submodule>` — __all__ only gates `from package import *`"

key-files:
  created:
    - tests/test_public_api.py
  modified:
    - infodynamics/__init__.py
    - infodynamics/text/__init__.py
    - tests/text/test_morphology.py

key-decisions:
  - "infodynamics.__all__ = exactly 8 symbols (InfoDynamics, MultiscaleInfoDynamics, WindowedRollingDistance, Scalogram, FooteNovelty, SignalClusterer, self_similarity_matrix, structure_descriptors) per D-01"
  - "infodynamics/__init__.py contains zero .text imports (D-05, hard requirement) — MorphologicalEncoder and Chunk/segment/strip_markdown re-exports removed"
  - "infodynamics.text.__all__ = exactly 8 symbols, folding the 4 D-05-displaced symbols plus Encoder into the text on-ramp's public surface (Claude's discretion per 04-CONTEXT.md) so nothing becomes unreachable"
  - "tests/text/test_morphology.py:10 migrated to `from infodynamics.text import MorphologicalEncoder` — the one tracked call site RESEARCH.md identified as breaking under D-05"

requirements-completed: [API-03]

coverage:
  - id: D1
    description: "infodynamics.__all__ equals exactly the 8-symbol core set and every name resolves via hasattr"
    requirement: "API-03"
    verification:
      - kind: unit
        ref: "tests/test_public_api.py#test_core_all_matches_expected_symbols"
        status: pass
    human_judgment: false
  - id: D2
    description: "infodynamics/__init__.py source contains no '.text' substring (D-05 zero-text-import invariant)"
    requirement: "API-03"
    verification:
      - kind: unit
        ref: "tests/test_public_api.py#test_core_init_has_no_text_imports"
        status: pass
    human_judgment: false
  - id: D3
    description: "infodynamics.text.__all__ equals exactly the 8-symbol text set and every name resolves via hasattr"
    requirement: "API-03"
    verification:
      - kind: unit
        ref: "tests/test_public_api.py#test_text_all_matches_expected_symbols"
        status: pass
    human_judgment: false
  - id: D4
    description: "Full test suite collects with zero import regressions after the __init__.py rewrite and the test_morphology.py import migration"
    requirement: "API-03"
    verification:
      - kind: unit
        ref: "pytest --collect-only -q (91 tests collected, 0 errors)"
        status: pass
      - kind: unit
        ref: "pytest -q (91 passed, 0 failed)"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-07-14
status: complete
---

# Phase 4 Plan 01: Curate the Public API (Core + Text __init__.py) Summary

**Explicit `__all__` at both `infodynamics` (8 sklearn-facing symbols) and `infodynamics.text` (8 text-on-ramp symbols), with zero `.text` imports remaining in the core package root — locked by a new `tests/test_public_api.py` contract test.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-14T14:35:01Z
- **Completed:** 2026-07-14T14:41:00Z
- **Tasks:** 2
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments
- `infodynamics/__init__.py` now defines an explicit `__all__` of exactly 8 core symbols and contains zero `from .text import` / `from infodynamics.text import` statements (D-05 satisfied)
- `infodynamics/text/__init__.py` now defines an explicit `__all__` of exactly 8 text symbols, giving `Encoder`, `MorphologicalEncoder`, `Chunk`, `segment`, and `strip_markdown` an official public home at the text-on-ramp root
- New `tests/test_public_api.py` permanently locks both `__all__` contracts and the zero-`.text`-import invariant, following the RED (Task 1) → GREEN (Task 2) TDD-style sequence the plan specified
- The one tracked call site broken by removing `MorphologicalEncoder` from core (`tests/text/test_morphology.py:10`) was migrated to `infodynamics.text` in the same commit as the `__init__.py` rewrite, so collection never broke between commits

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the failing public-API contract test (RED scaffold)** - `9577d2d` (test)
2. **Task 2: Curate both __init__.py export surfaces and migrate the one broken test import (GREEN)** - `057dbca` (feat)

**Plan metadata:** (final commit follows this summary)

## Files Created/Modified
- `tests/test_public_api.py` - New: 3 assertion-only tests locking `infodynamics.__all__`, `infodynamics.text.__all__`, and the D-05 zero-`.text`-import invariant
- `infodynamics/__init__.py` - Rewritten: explicit 8-symbol `__all__`, both `.text` re-exports (`MorphologicalEncoder`, `Chunk`/`segment`/`strip_markdown`) removed
- `infodynamics/text/__init__.py` - Rewritten: explicit 8-symbol `__all__`, docstring's "deferred" note removed, `Encoder`/`MorphologicalEncoder`/`Chunk`/`segment`/`strip_markdown` newly re-exported at the text-package root
- `tests/text/test_morphology.py` - Line 10: `from infodynamics import MorphologicalEncoder` → `from infodynamics.text import MorphologicalEncoder`

## Decisions Made
- Followed D-01 through D-05 from `04-CONTEXT.md` verbatim for the core `__all__` contents and the zero-`.text`-import hard requirement — no deviation.
- Followed the Claude's-discretion resolution already baked into `04-CONTEXT.md`/`04-PATTERNS.md`: folded all 5 displaced/newly-surfaced text symbols (`Encoder`, `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown`) into `infodynamics.text.__all__` alongside the 3 existing `Text*` wrappers.
- No new architectural decisions were required — RESEARCH.md and PATTERNS.md had already fully specified the exact target content for both files; execution was mechanical.

## Deviations from Plan

None - plan executed exactly as written. Both `__init__.py` target contents matched PATTERNS.md verbatim; the test file matched RESEARCH.md's Verification Mechanics block verbatim; the one-line test import fix matched PATTERNS.md's specified before/after exactly.

## Issues Encountered
None. RED state was confirmed before Task 2 (all 3 new tests failed with the expected `AttributeError: module 'infodynamics' has no attribute '__all__'` / `.text` present in source), and GREEN state was confirmed after (3 passed, full suite 91 passed, submodule reachability for `viz`/`metrics`/`scalogram` internals/`clustering` helpers all verified intact via direct `python -c` import checks).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- API-03 fully satisfied and permanently locked by `tests/test_public_api.py`; safe foundation for Plan 02 (canonical example + CHANGELOG, API-04) to build on
- Full pytest suite green at 91 collected/passed tests, zero numerical drift (this plan touched only import/export surfaces, no analysis code)
- `infodynamics.text.__all__` now exposes `Encoder`/`MorphologicalEncoder`/`Chunk`/`segment`/`strip_markdown` as officially public — Plan 02's canonical example and CHANGELOG can reference these paths directly without further discovery

---
*Phase: 04-curate-the-public-api*
*Completed: 2026-07-14*

## Self-Check: PASSED

All created/modified files verified present on disk; both task commit hashes (`9577d2d`, `057dbca`) verified in git log.

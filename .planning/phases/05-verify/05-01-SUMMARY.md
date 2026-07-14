---
phase: 05-verify
plan: 01
subsystem: testing
tags: [morphology, textdescriptives, import-guard, error-handling]

# Dependency graph
requires:
  - phase: 03-decouple-the-pipeline
    provides: infodynamics/text/morphology.py's MorphologicalEncoder with existing lazy-import guard pattern
provides:
  - Actionable ImportError (not bare ModuleNotFoundError) when MorphologicalEncoder.encode() is called without the `morphology` extra installed
  - Regression test locking that behavior
affects: [05-verify-plan-02, 05-verify-plan-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [try/except ImportError re-raise with actionable message, matching the 4 pre-existing sibling guards in the same file]

key-files:
  created: []
  modified:
    - infodynamics/text/morphology.py
    - tests/text/test_morphology.py

key-decisions:
  - "Wrapped only the encode()-site import in try/except, leaving every other line of encode() byte-identical, per D-02 no-behavior-change constraint"
  - "Regression test uses monkeypatch.setitem(sys.modules, 'textdescriptives', None) rather than uninstalling the package, matching the file's existing FakeNlp-style test-isolation idiom"

patterns-established: []

requirements-completed: [CORE-03]

coverage:
  - id: D1
    description: "MorphologicalEncoder.encode() raises an actionable ImportError (naming the 'morphology' extra and pip install command) instead of a bare ModuleNotFoundError when textdescriptives is absent"
    requirement: "CORE-03"
    verification:
      - kind: unit
        ref: "tests/text/test_morphology.py#test_encode_raises_actionable_import_error_without_textdescriptives"
        status: pass
      - kind: other
        ref: "python -c \"import sys; sys.modules['textdescriptives']=None; from infodynamics.text import MorphologicalEncoder as M; M(feature_group='pos_proportions').encode(['x'])\" (manual simulation, confirmed ImportError not ModuleNotFoundError)"
        status: pass
    human_judgment: false

# Metrics
duration: 2min
completed: 2026-07-14
status: complete
---

# Phase 05 Plan 01: Guard textdescriptives Import in MorphologicalEncoder Summary

**Wrapped the unguarded `from textdescriptives import extract_df` at the top of `MorphologicalEncoder.encode()` in a try/except that re-raises the file's existing actionable `ImportError` message, and locked the fix with a regression test.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-07-14T17:03:56Z
- **Completed:** 2026-07-14T17:06:16Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `MorphologicalEncoder.encode()` now raises `ImportError("The 'morphology' extra is required to use MorphologicalEncoder. Install it with \`pip install infodynamics[morphology]\`.")` instead of a bare `ModuleNotFoundError` when `textdescriptives` isn't installed
- Message is byte-identical to the 4 pre-existing sibling guards in the same file (`_load_pipeline` x2, `encode_all_feature_groups` x2)
- New regression test simulates the missing extra via `monkeypatch.setitem(sys.modules, "textdescriptives", None)` and asserts on `ImportError` + "pip install" substring
- Full `tests/text/test_morphology.py` (8 tests) and full project suite (92 tests) pass after the change

## Task Commits

Each task was committed atomically:

1. **Task 1: Guard the textdescriptives import in MorphologicalEncoder.encode()** - `d849970` (fix)
2. **Task 2: Add a regression test locking the actionable ImportError** - `8b93968` (test)

**Plan metadata:** commit pending (docs: complete plan)

## Files Created/Modified
- `infodynamics/text/morphology.py` - `encode()`'s `from textdescriptives import extract_df` is now guarded with try/except ImportError, re-raising the actionable message
- `tests/text/test_morphology.py` - added `test_encode_raises_actionable_import_error_without_textdescriptives`, added `import sys`

## Decisions Made
- Kept the fix minimal and inline-scoped per D-02: only the import statement inside `encode()` was wrapped; the `nlp = ...` line through `return df.to_numpy(...)` is byte-for-byte unchanged
- Landed as its own labeled `fix(05):` commit separate from the `test(05):` commit, per D-03

## Deviations from Plan

### Auto-fixed Issues

None — Task 1 and Task 2 were implemented exactly as specified in the plan's `<action>` blocks. No Rule 1/2/3 fixes were needed.

### Plan-vs-reality note (not a deviation in code, a verification-arithmetic correction)

The plan's `<verify>` automated check asserts `grep -c "extra is required to use MorphologicalEncoder" infodynamics/text/morphology.py` equals `4`, based on the plan's premise that "3 sibling guards" already existed. On inspection, the file actually had **4** pre-existing occurrences of that message (both guards in `_load_pipeline` for `spacy_udpipe`/`textdescriptives`, and both guards in `encode_all_feature_groups` for `textdescriptives`/`spacy_udpipe`) — not 3. After adding the new `encode()` guard, the correct count is **5**, not 4. This does not affect correctness: the new guard's message is verified byte-identical to the existing four, and both the targeted regression test and the full test suite pass. Recorded here for transparency since the plan's literal `<verify>` command (`test "$(grep -c ...)" = "4"`) would fail as written; the semantic acceptance criteria (message content, exception type, no other lines changed) are all satisfied.

---

**Total deviations:** 0 auto-fixed. One plan-arithmetic note documented above (grep count is 5, not the plan's expected 4, because the plan undercounted pre-existing sibling guards by one).
**Impact on plan:** None on functionality — the fix and test are correct and match every acceptance criterion except the plan's miscounted grep target.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- CORE-03's "actionable ImportError naming the missing extra" criterion is now literally true for `MorphologicalEncoder`, ready for Plan 02's fresh no-extras venv verification pass
- No blockers for Plan 02/03

---
*Phase: 05-verify*
*Completed: 2026-07-14*

---
phase: 01-baseline-removal
plan: 02
subsystem: infra
tags: [setuptools, git-rm, console-scripts, packaging]

# Dependency graph
requires:
  - phase: 01-baseline-removal (Plan 01)
    provides: golden-output baseline snapshot (tests/golden/, tests/test_golden_baseline.py) committed before removal began
provides:
  - dashboard/ directory fully removed from the working tree (tracked contents via git rm, untracked residue via rm -rf), recoverable via git history
  - infodynamics/cache_contract.py and infodynamics/shipping.py removed
  - tests/test_manifest.py (the only test file exercising cache_contract/shipping) removed
  - setup.py with zero console_scripts entry_points; installed environment (.venv/bin/, infodynamics.egg-info) reconciled via force-reinstall
affects: [01-03 (verification gate), Phase 2 (reorganize surviving code)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "git rm (never filesystem rm) for any tracked file being removed, so pre-deletion content stays reachable via git show <sha>^:<path>"
    - "setup.py entry_points edits require pip install --force-reinstall --no-deps -e . to propagate into .venv/bin/ shims and egg-info — a source-only edit does not"

key-files:
  created: []
  modified:
    - setup.py

key-decisions:
  - "Recalculated the expected post-removal pytest collection count as 72 (85 pre-removal minus test_manifest.py's 13), not the plan's hardcoded 68 — the plan's number assumed a pre-Plan-01 baseline of 81 tests and didn't account for the 4 golden-baseline tests Plan 01 (Wave 1) added to the suite before this plan ran."

patterns-established:
  - "Removal-only plans verify via absence (test ! -e / test ! -f) plus a pytest collection count delta, rather than new functional tests."

requirements-completed: [RM-01, RM-02, RM-03, RM-04]

coverage:
  - id: D1
    description: "dashboard/, infodynamics/cache_contract.py, infodynamics/shipping.py, tests/test_manifest.py removed from working tree; tracked deletions recoverable via git history"
    requirement: "RM-01"
    verification:
      - kind: other
        ref: "test ! -e dashboard && test ! -f infodynamics/cache_contract.py && test ! -f infodynamics/shipping.py && test ! -f tests/test_manifest.py"
        status: pass
      - kind: other
        ref: "git log --diff-filter=D --name-only -- dashboard/app.py (recoverable deletion confirmed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "infodynamics/cache_contract.py, infodynamics/shipping.py, dashboard/build_dashboard_artifacts.py removed from the package"
    requirement: "RM-02"
    verification:
      - kind: other
        ref: "git status --short (files absent from working tree, deletions staged and committed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "setup.py has zero console-script entries pointing at removed code; reinstall clears materialized .venv/bin/ shims and egg-info metadata"
    requirement: "RM-03"
    verification:
      - kind: other
        ref: "grep -c console_scripts setup.py -> 0; ls .venv/bin | grep infodynamics -> empty; infodynamics.egg-info/entry_points.txt absent"
        status: pass
    human_judgment: false
  - id: D4
    description: "tests/test_manifest.py removed; pytest --collect-only reports zero collection errors"
    requirement: "RM-04"
    verification:
      - kind: unit
        ref: ".venv/bin/pytest --collect-only -q -> 72 tests collected, 0 errors"
        status: pass
    human_judgment: false

duration: 16min
completed: 2026-07-14
status: complete
---

# Phase 01 Plan 02: Remove dashboard/, cache_contract.py, shipping.py Summary

**Deleted the entire dashboard subsystem (7 files), infodynamics/cache_contract.py, infodynamics/shipping.py, and their exclusive test file via git rm; stripped setup.py's 4 console-script entry points and reconciled the installed environment via force-reinstall.**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-07-14T07:51:00Z (approx)
- **Completed:** 2026-07-14T08:07:32Z
- **Tasks:** 2
- **Files modified:** 11 (10 deleted, 1 edited)

## Accomplishments
- Removed dashboard/ (README.md, app.py, bench_core.py, build_dashboard_artifacts.py, render_overview.py, taxonomy.py, test_bench.py) via `git rm -r`, then cleared remaining untracked/gitignored residue (cache/, __pycache__, .DS_Store, scratch files) with `rm -rf` since it carried no git-history preservation obligation
- Removed infodynamics/cache_contract.py, infodynamics/shipping.py, and tests/test_manifest.py (the only test file covering them) via `git rm`
- Removed setup.py's `entry_points={'console_scripts': [...]}` block registering the four `infodynamics-pack/-pull/-verify/-init-project` scripts against the now-deleted `infodynamics.shipping` module
- Reinstalled the package with `pip install --force-reinstall --no-deps -e .`, which regenerated `infodynamics.egg-info` with no `entry_points.txt` and cleared the stale `.venv/bin/infodynamics-*` shims

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove dashboard/, cache_contract.py, shipping.py, and their exclusive test, preserving history via git rm** - `0a9b195` (feat)
2. **Task 2: Remove the console-script entry points from setup.py and reinstall to clear stale shims** - `199a904` (feat)

**Plan metadata:** (this commit, docs)

## Files Created/Modified
- `dashboard/README.md` - removed (git rm, recoverable)
- `dashboard/app.py` - removed (git rm, recoverable)
- `dashboard/bench_core.py` - removed (git rm, recoverable)
- `dashboard/build_dashboard_artifacts.py` - removed (git rm, recoverable)
- `dashboard/render_overview.py` - removed (git rm, recoverable)
- `dashboard/taxonomy.py` - removed (git rm, recoverable)
- `dashboard/test_bench.py` - removed (git rm, recoverable)
- `infodynamics/cache_contract.py` - removed (git rm, recoverable)
- `infodynamics/shipping.py` - removed (git rm, recoverable)
- `tests/test_manifest.py` - removed (git rm, recoverable)
- `setup.py` - `entry_points` kwarg deleted entirely; `install_requires`/`extras_require` unchanged

## Decisions Made
- Confirmed via grep before removal that no surviving code (infodynamics/__init__.py, other modules, other tests) imports from cache_contract, shipping, or dashboard — so no import-surface cleanup was needed elsewhere, matching the plan's own note.
- Treated the plan's hardcoded "68 tests" acceptance number as stale: the correct post-removal expectation is 72 (85 collected before this plan's removal, minus test_manifest.py's 13), because Plan 01 (Wave 1) added 4 golden-baseline tests to the suite before this plan ran, and the plan's arithmetic (81 - 13 = 68) was computed against the pre-Plan-01 baseline. Verified 72 tests / 0 errors instead of the literal 68 in the plan text.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in plan's stated acceptance number] Corrected expected pytest collection count**
- **Found during:** Task 1 verification
- **Issue:** Plan's acceptance criteria hardcoded "68 tests collected" (computed as 81 pre-Plan-01 baseline minus test_manifest.py's 13). Actual pre-removal collection was 85 tests (81 + 4 golden-baseline tests added by Plan 01, Wave 1), so the correct post-removal expectation is 72, not 68.
- **Fix:** No code fix needed — verified against the corrected arithmetic (85 - 13 = 72) instead of the stale literal. No functional issue; purely a plan-authoring staleness given Plan 01 ran and added tests between the RESEARCH.md baseline measurement and this plan's execution.
- **Files modified:** None (verification-only correction)
- **Verification:** `.venv/bin/pytest --collect-only -q` reports "72 tests collected", 0 errors
- **Committed in:** 0a9b195 (Task 1 commit message notes the actual count)

---

**Total deviations:** 1 auto-fixed (plan-arithmetic staleness, not a code bug)
**Impact on plan:** No scope creep; the actual removal work matched the plan exactly. Only the expected-test-count literal in the plan's acceptance criteria was stale relative to Plan 01's already-landed test additions.

## Issues Encountered
None - both tasks executed cleanly on the first attempt.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All RM-01 through RM-04 requirements satisfied: dashboard/, cache_contract.py, shipping.py, and test_manifest.py are gone from the working tree but recoverable via git history; setup.py and the installed environment carry zero references to removed console scripts.
- pytest collects 72 tests with 0 errors, confirming a clean, consistent test suite for Plan 01-03's verification gate.
- No blockers for Plan 01-03 (verification gate) or Phase 2 (reorganize surviving code).

---
*Phase: 01-baseline-removal*
*Completed: 2026-07-14*

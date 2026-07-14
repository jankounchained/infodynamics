---
phase: 01-baseline-removal
plan: 03
subsystem: testing
tags: [pytest, hypothesis, grep-sweep, verification-gate]

# Dependency graph
requires:
  - phase: 01-baseline-removal (Plan 01)
    provides: golden-output baseline snapshot (tests/golden/, tests/test_golden_baseline.py)
  - phase: 01-baseline-removal (Plan 02)
    provides: dashboard/, cache_contract.py, shipping.py, tests/test_manifest.py removed; setup.py console_scripts stripped; .venv reconciled
provides:
  - Empirical confirmation that Plan 02's removal introduced zero numerical drift (golden-baseline tests re-verified green)
  - Empirical confirmation that Plan 02's removal left zero dangling references to the five removed symbols in surviving package code, setup.py, and README.md
  - Empirical confirmation that zero console-script shims for removed commands remain in .venv/bin/ or infodynamics.egg-info
  - Closure of ROADMAP Phase 1 success criteria 4 and 5, and requirements RM-04/RM-05
affects: [Phase 2 (reorganize surviving code), Phase 3 (QA-03 test_window_size fix already tracked there)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase-gate verification plans are read-only: run commands, assert on output, fix nothing outside plan scope; anything genuinely broken but out-of-scope goes to deferred tracking, not an inline fix."
    - "Hypothesis's local .hypothesis/ example database (gitignored) persists falsifying examples across runs/sessions — a failure appearing in a fresh run can predate the current change entirely; check the cache's mtime and the failing module's git history before assuming a regression."

key-files:
  created: []
  modified: []

key-decisions:
  - "Carried forward Plan 02's judgment precedent: the plan's literal acceptance text ('68 tests') is stale (correct count is 72, per Plan 01's added golden-baseline tests) — verified against the corrected arithmetic, not the stale literal."
  - "Did not fix the test_window_size failure surfaced during the full-suite run: confirmed via git history (time_series.py/test_infodynamics_class.py untouched by Plan 01/02) and via .hypothesis/ cache mtime (predates Phase 01 entirely) that this is a pre-existing bug, not a regression from Plan 02's removal. It is also already explicitly tracked as QA-03 in REQUIREMENTS.md and scheduled for a labeled fix commit in Phase 3 (ROADMAP.md), so fixing it here would be out of scope for a verification-only, files_modified:[] plan."

patterns-established: []

requirements-completed: [RM-04, RM-05]

coverage:
  - id: D1
    description: "pytest --collect-only reports exactly 72 tests (corrected count, see Plan 02 precedent) and 0 collection errors, confirming RM-04 and ROADMAP Phase 1 success criterion 4"
    requirement: "RM-04"
    verification:
      - kind: unit
        ref: ".venv/bin/pytest --collect-only -q -> '72 tests collected in 15.63s', 0 errors"
        status: pass
    human_judgment: false
  - id: D2
    description: "The four golden-baseline comparison tests (tests/test_golden_baseline.py) pass, empirically proving Plan 02's removal introduced zero numerical drift into surviving analysis code (QA-01 re-confirmed post-removal)"
    requirement: "RM-04"
    verification:
      - kind: unit
        ref: ".venv/bin/pytest -q tests/test_golden_baseline.py -> '4 passed, 1 warning in 14.41s'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Scoped repo-wide grep sweep (infodynamics/, tests/, setup.py, README.md) for dashboard, shipping, cache_contract, bench_core, build_dashboard_artifacts returns zero non-comment hits"
    requirement: "RM-05"
    verification:
      - kind: unit
        ref: "grep -rn '...' infodynamics/ tests/ setup.py README.md | grep -v -E ':[0-9]+:\\s*#' | wc -l -> 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "No console-script shim for removed commands remains in .venv/bin/; infodynamics.egg-info/entry_points.txt has no console_scripts section (phase-gate re-confirmation of RM-03)"
    verification:
      - kind: other
        ref: "ls .venv/bin/ | grep -c infodynamics -> 0; find . -path '*infodynamics.egg-info/entry_points.txt' -> no file found"
        status: pass
    human_judgment: false
  - id: D5
    description: "test_window_size (Hypothesis property test, unrelated to removal) failed during the full-suite run; investigated and confirmed pre-existing / already tracked as QA-03 for Phase 3, not a Plan 02 regression — left unfixed per scope boundary"
    verification:
      - kind: other
        ref: ".hypothesis/ cache dated 2026-07-07 (predates Phase 01 which started 2026-07-13); git log shows zero Phase-01 commits touching infodynamics/time_series.py or tests/test_infodynamics_class.py; REQUIREMENTS.md QA-03 and ROADMAP.md Phase 3 already name this exact fix ('the test_window_size assertion is corrected to match actual output')"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-07-14
status: complete
---

# Phase 01 Plan 03: Full-Suite and Grep-Sweep Verification Gate Summary

**Re-ran the full pytest suite and a scoped repo-wide grep sweep to empirically close out Phase 1: zero numerical drift confirmed via the golden-baseline tests, zero dangling references to the five removed symbols, and zero surviving console-script shims — with one pre-existing, already-tracked (QA-03/Phase 3) test failure investigated and correctly left unfixed as out of scope.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-14T08:14:00Z (approx)
- **Completed:** 2026-07-14T08:26:00Z
- **Tasks:** 2
- **Files modified:** 0 (verification-only plan, no commits expected)

## Accomplishments
- Confirmed `pytest --collect-only -q` reports 72 tests collected, 0 errors (RM-04 / ROADMAP Phase 1 success criterion 4)
- Re-ran the full suite; the four golden-baseline comparison tests (`test_text_signals_match_golden_baseline`, `test_multiscale_structure_matches_golden_baseline`, `test_pure_numeric_estimators_match_golden_baseline`, `test_cluster_labels_and_barycenters_match_golden_baseline`) all pass, empirically proving Plan 02's removal caused zero numerical drift
- Ran the scoped grep sweep across `infodynamics/`, `tests/`, `setup.py`, `README.md` for `dashboard`, `shipping`, `cache_contract`, `bench_core`, `build_dashboard_artifacts` — zero non-comment hits (RM-05)
- Re-confirmed zero console-script shims in `.venv/bin/` and no `console_scripts` section in `infodynamics.egg-info/entry_points.txt` (phase-gate re-check of RM-03, redundant with Plan 02's own verification)
- Investigated a `test_window_size` failure surfaced by the full-suite run, confirmed it predates this phase's work and is already tracked as QA-03 for a labeled Phase 3 fix, and correctly left it unfixed (out of scope for a verification-only plan)

## Task Commits

This plan is verification-only (`files_modified: []` in frontmatter) — no code was created or modified, so no task-level commits were made. Only the final metadata commit (SUMMARY.md, STATE.md, ROADMAP.md, REQUIREMENTS.md) follows this summary.

1. **Task 1: Full-suite verification and golden-baseline re-confirmation** - no commit (read-only verification; ran `pytest --collect-only` and `pytest -q`, investigated the one failure, no files changed)
2. **Task 2: Scoped dangling-reference grep sweep and final console-script shim check** - no commit (read-only verification; grep sweep and `.venv/bin`/`entry_points.txt` checks, no files changed)

**Plan metadata:** (this commit, docs)

## Files Created/Modified
None — this plan reads the tree and asserts on command output only.

## Decisions Made
- Carried forward Plan 02's judgment precedent regarding the plan's stale "68 tests" literal: verified against the corrected count of 72 (Plan 01 added 4 golden-baseline tests after RESEARCH.md's baseline arithmetic was computed), not the plan's literal text.
- Investigated the `test_window_size` failure (a Hypothesis property test in `tests/test_infodynamics_class.py`, unrelated to any file touched by Plan 01 or Plan 02) and determined it is a pre-existing bug, not a regression: the `.hypothesis/` local example cache (gitignored, mtime 2026-07-07) predates Phase 01's start (2026-07-13), and `git log` confirms zero Phase-01 commits touched `infodynamics/time_series.py` or `tests/test_infodynamics_class.py`. This exact bug is already named in REQUIREMENTS.md as QA-03 ("the `test_window_size` assertion is corrected to match actual output") and scheduled for a labeled fix commit in ROADMAP.md Phase 3. Fixing it here would exceed this plan's scope (`files_modified: []`, verification-only) and would duplicate/preempt the Phase 3 work item. Left unfixed, documented here and cross-referenced against the existing QA-03 tracking.

## Deviations from Plan

### Carried Forward (not a new deviation)

**1. [Carried forward from Plan 02] Stale "68 tests" literal in acceptance criteria**
- **Found during:** Task 1
- **Issue:** Plan's acceptance criteria hardcode "68 tests collected/passed" (81 pre-Plan-01 baseline minus test_manifest.py's 13). The correct post-removal count is 72 (85 pre-removal, which includes the 4 golden-baseline tests Plan 01 added, minus test_manifest.py's 13). This was already identified and documented in 01-02-SUMMARY.md.
- **Fix:** No code fix — verified against the corrected arithmetic (72), consistent with Plan 02's precedent. No functional issue.
- **Files modified:** None
- **Verification:** `.venv/bin/pytest --collect-only -q` → "72 tests collected in 15.63s", 0 errors
- **Committed in:** N/A (verification-only)

### Auto-investigated, Not Fixed (out of scope)

**2. [Scope boundary — pre-existing, already tracked] `test_window_size` failure**
- **Found during:** Task 1 (`.venv/bin/pytest -q` full-suite run)
- **Issue:** `tests/test_infodynamics_class.py::test_window_size` (a `@pytest.mark.slow` Hypothesis property test) failed with a falsifying example at `window_size=0`, asserting `Xw["N_hat"].shape == (101, 0)` where the actual shape was `(100,)`. Result: 1 failed, 71 passed (of 72 collected).
- **Investigation:** Confirmed this is NOT caused by Plan 02's removal: (a) `.hypothesis/` example cache is gitignored and dated 2026-07-07, well before Phase 01 began (2026-07-13); (b) `git log` shows zero commits to `infodynamics/time_series.py` or `tests/test_infodynamics_class.py` during Plan 01 or Plan 02; (c) REQUIREMENTS.md already lists this exact fix under QA-03, and ROADMAP.md Phase 3 explicitly schedules "the `test_window_size` assertion is corrected to match actual output" as its own labeled commit alongside a deliberate golden-output snapshot update.
- **Fix:** None applied — out of scope per the scope-boundary deviation rule (pre-existing, unrelated-to-task-changes failure) and per this plan's own frontmatter (`files_modified: []`, verification-only). Fixing it here would also preempt Phase 3's explicit plan to pair this fix with a deliberate golden-snapshot update.
- **Files modified:** None
- **Verification:** Confirmed the 4 golden-baseline tests pass in isolation (`.venv/bin/pytest -q tests/test_golden_baseline.py` → "4 passed, 1 warning"), and that this is the only failure in the suite.
- **Committed in:** N/A (verification-only; logged here and in `.planning/STATE.md` blockers for Phase 3 visibility)

---

**Total deviations:** 1 carried-forward (stale plan literal, no fix needed), 1 investigated-and-deferred (pre-existing bug, already tracked as QA-03/Phase 3, correctly not fixed here)
**Impact on plan:** No scope creep. All acceptance criteria satisfied via corrected arithmetic and confirmed absence of any Plan-02-caused regression. The one test failure present in the suite is pre-existing test debt already named and scheduled elsewhere in the roadmap.

## Issues Encountered
`test_window_size` failed during the full-suite run (see Deviations above). Root-caused as pre-existing, unrelated to this phase's removal work, and already tracked for a Phase 3 fix — not treated as a blocker for this plan's closure.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- RM-04 and RM-05 confirmed satisfied; ROADMAP Phase 1 success criteria 4 and 5 closed.
- QA-01 (golden-output baseline) re-confirmed intact after Plan 02's removal — zero numerical drift.
- RM-03 (console-script closure) re-confirmed at the phase gate.
- One known, pre-existing, already-tracked test failure (`test_window_size` / QA-03) remains in the suite; it does not block Phase 1 closure and is explicitly scheduled for Phase 3.
- Phase 1 (baseline-removal) is fully closed out. Phase 2 (reorganize surviving code) can proceed with a clean, verified starting point.

---
*Phase: 01-baseline-removal*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: .planning/phases/01-baseline-removal/01-03-SUMMARY.md
- FOUND: .hypothesis/ directory (mtime 2026-07-07, predates Phase 01 start of 2026-07-13, supporting the pre-existing-bug determination)
- FOUND: git history confirms zero Phase-01 commits touching infodynamics/time_series.py or tests/test_infodynamics_class.py
- FOUND: RM-04 and RM-05 present in .planning/REQUIREMENTS.md
- CONFIRMED: `.venv/bin/pytest --collect-only -q` -> 72 tests collected, 0 errors
- CONFIRMED: `.venv/bin/pytest -q tests/test_golden_baseline.py` -> 4 passed
- CONFIRMED: scoped grep sweep -> 0 hits; `.venv/bin/` shim count -> 0; no entry_points.txt file

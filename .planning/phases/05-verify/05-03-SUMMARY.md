---
phase: 05-verify
plan: 03
subsystem: infra
tags: [github-actions, ci, pytest]

# Dependency graph
requires:
  - phase: 05-verify (05-02)
    provides: proof of the 5 gating ROADMAP criteria (this plan is independent of that proof)
provides:
  - Minimal, non-gating GitHub Actions CI workflow (.github/workflows/ci.yml) that installs `.[test]` and runs pytest on push/PR
affects: [ci, packaging]

# Tech tracking
tech-stack:
  added: [github-actions]
  patterns: ["Single-job, single-Python-version CI: checkout -> setup-python -> pip install .[test] -> pytest -q, no matrix/codecov/poetry/mkdocs"]

key-files:
  created: [.github/workflows/ci.yml]
  modified: []

key-decisions:
  - "Re-verified actions/checkout and actions/setup-python latest major tags via `gh api .../releases/latest` at execution time rather than trusting RESEARCH.md's v6 note; found checkout@v7 (was v6 at research time, now superseded) and setup-python@v6 (matched research) — pinned to the freshly-verified tags per T-05-03"

patterns-established:
  - "Pattern 3 (RESEARCH.md): minimal single-job GitHub Actions CI — no permissions block, no secrets, no matrix, no publish/deploy step"

requirements-completed: []

coverage:
  - id: D1
    description: "Minimal, non-gating CI workflow (.github/workflows/ci.yml): single job on ubuntu-latest, installs .[test], runs pytest -q"
    verification:
      - kind: other
        ref: "python -c \"import yaml; ...\" (plan's automated verify block) — validated YAML structure, pinned Actions, no permissions block"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-07-14
status: complete
---

# Phase 05 Plan 03: Minimal non-gating CI workflow Summary

**Added a single-job GitHub Actions CI workflow (checkout -> setup-python 3.14 -> pip install .[test] -> pytest -q) with both third-party Actions re-verified and pinned to current major-version tags, and no permissions escalation.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-14T17:06:00Z (approx.)
- **Completed:** 2026-07-14T17:10:46Z
- **Tasks:** 1 completed
- **Files modified:** 1

## Accomplishments
- Created `.github/workflows/ci.yml`: single `test` job on `ubuntu-latest`, `python-version: "3.14"`, `pip install .[test]`, `pytest -q`
- Re-verified `actions/checkout` and `actions/setup-python` current major-version tags live via `gh api repos/<owner>/<repo>/releases/latest` (RESEARCH A1) rather than trusting the research doc's snapshot — found `actions/checkout` had moved to `v7.0.0` since the research session (which cited `v6`), pinned to `@v7`; `actions/setup-python` matched research at `v6.3.0`, pinned to `@v6`
- No `permissions:` block, no `secrets:`, no codecov/poetry/mkdocs/release job, no version matrix — matches D-07's minimal-bonus-deliverable scope and PROJECT.md's "no packaging modernization" constraint
- Verified locally: YAML parses, both Actions pinned to `@vN` (no `@main`/`@master`), no `permissions` key present at workflow or job level

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the minimal non-gating CI workflow** - `16f2baf` (feat)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `.github/workflows/ci.yml` - Single-job GitHub Actions CI workflow: checkout, setup-python 3.14, pip install .[test], pytest -q

## Decisions Made
- Re-verified Action tags live via `gh api` instead of trusting RESEARCH.md's point-in-time `v6` note for `actions/checkout` — caught that it had advanced to `v7.0.0` since the research session, avoiding pinning a now-superseded major tag. `actions/setup-python` was unchanged at `v6.3.0`.

## Deviations from Plan

None - plan executed exactly as written. The plan explicitly anticipated the tag-drift scenario ("re-verify... `v6` was confirmed current at research time — pin to whatever the checked latest major is") and this execution followed that instruction precisely.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. The workflow will run automatically on the next push/PR to `main` once this commit reaches GitHub; its cloud-run result is explicitly non-gating for Phase 5 completion per D-07.

## Next Phase Readiness
Phase 5 gating status is unaffected by this plan (requirements: [] by design — QA-04 is fully covered by Plan 02's full-suite pytest run). This bonus CI workflow provides ongoing automated regression protection for future milestones. No blockers.

---
*Phase: 05-verify*
*Completed: 2026-07-14*

# Phase 5: Verify - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-14
**Phase:** 5-Verify
**Areas discussed:** Failure/remediation policy, Deliverable form & permanence, Golden-baseline & test-count reconciliation authority

---

## Failure/remediation policy

| Option | Description | Selected |
|--------|-------------|----------|
| Fix small issues inline | Claude fixes obviously in-scope issues, then re-verifies; bigger issues get flagged | ✓ |
| Report only, no fixes | This phase is a read-only audit; every failure becomes a new backlog item | |
| Fix everything found | Keep fixing until all 5 criteria pass regardless of change size | |

**User's choice:** Fix small issues inline (recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Anything touching public API/behavior | Signature changes, renames, numerical-output changes get flagged | ✓ |
| Anything beyond a one-line fix | Stricter — even small multi-line fixes get flagged | |
| Claude decides case by case | No fixed line | |

**User's choice:** Anything touching public API/behavior (recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Separate, labeled commits | e.g. `fix(05): ...` per issue, matches Phases 1-4 discipline | ✓ |
| Bundle into one verification commit | Single commit covers report + fixes | |

**User's choice:** Separate, labeled commits (recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Stop and ask you | Constraint conflicts are a founder-level call | ✓ |
| Fix it anyway, document the deviation | Prioritize green over strict constraint adherence | |

**User's choice:** Stop and ask you (recommended)

**Notes:** All four questions in this area landed on the recommended option — no pushback or alternate framing offered.

---

## Deliverable form & permanence

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, a VERIFICATION.md in the phase dir | One file walking through all 5 criteria with evidence | ✓ |
| No dedicated file | Pass/fail confirmed via commits/chat only | |
| Yes, but at repo root | Top-level VERIFICATION.md visible outside .planning/ | |

**User's choice:** Yes, a VERIFICATION.md in the phase dir (recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| One-off manual venv, documented in the report | Run once, capture results in VERIFICATION.md, no ongoing tooling | ✓ |
| Permanent committed script/test | e.g. subprocess-based smoke test, reusable in future CI | |
| Both | One-off now plus a reusable script for later | |

**User's choice:** One-off manual venv, documented in the report (recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| No — out of scope | CI/tox setup isn't in the roadmap or requirements | |
| Yes — add a minimal CI workflow | Wire up GitHub Actions as part of proving "tests green" | ✓ |

**User's choice:** Yes — add a minimal CI workflow (non-recommended pick)

**Follow-up:** Flagged that this goes beyond Phase 5's 5 stated ROADMAP success criteria (scope-guardrail check). Asked how it should fit:

| Option | Description | Selected |
|--------|-------------|----------|
| Bonus deliverable, doesn't gate phase completion | Phase 5 is done once the 5 ROADMAP criteria pass; CI is additional, non-gating | ✓ |
| Required for this phase to be done | Treat CI as a self-imposed 6th success criterion | |
| Actually, make it separate follow-up work | Defer CI setup to a future phase/milestone instead | |

**User's choice:** Bonus deliverable, doesn't gate phase completion (recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Existing tests are sufficient | `test_golden_baseline.py` + `test_pipeline_composition.py` already cover criterion 5 | ✓ |
| Add a standalone Phase 5 script anyway | Extra auditability despite existing coverage | |

**User's choice:** Existing tests are sufficient (recommended)

---

## Golden-baseline & test-count reconciliation authority

| Option | Description | Selected |
|--------|-------------|----------|
| Just start → target → actual | 81 pre-refactor, 68 target floor, 91 actual — concise | ✓ |
| Full per-phase breakdown | Show count after each phase (68 → 72 → … → 91) | |

**User's choice:** Just start → target → actual (recommended)
**Notes:** Numbers verified live during discussion — `git show 0513127:tests/*.py` (pre-Phase-1 HEAD) confirmed 81 test functions across 9 files, matching `.planning/codebase/TESTING.md`. `test_manifest.py` accounted for 13. Current `pytest --collect-only -q` reports 91.

| Option | Description | Selected |
|--------|-------------|----------|
| Run the full suite including slow tests | QA-04 says "the full pytest suite passes" — run everything, note timing | ✓ |
| Skip slow marker for the main pass | Run `pytest -m "not slow"` as primary evidence | |

**User's choice:** Run the full suite including slow tests (recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Whatever tests/test_golden_baseline.py already asserts | Don't re-litigate tolerance — existing test is the source of truth | ✓ |
| Tighten to bit-exact for this pass | Additionally diff raw snapshot files for byte-identity | |

**User's choice:** Whatever tests/test_golden_baseline.py already asserts (recommended)

---

## Claude's Discretion

- **"Fast" import threshold (criterion 2):** Not discussed — user selected the other three areas instead of this one when choosing what to discuss. Default: qualitative note in VERIFICATION.md unless research surfaces a reason to pin a hard number.
- **CI workflow scope/contents:** Per the resolved D-07, the exact triggers/steps of the minimal CI workflow are left to the planner, as long as it stays non-gating.

## Deferred Ideas

None — the one scope-adjacent item raised (adding CI) was resolved inline as a non-gating bonus deliverable rather than deferred to a separate phase.

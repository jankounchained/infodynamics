# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v0.5 — Core Extraction

**Shipped:** 2026-07-14
**Phases:** 5 | **Plans:** 18 | **Sessions:** several (spanning ~1.1 days, 2026-07-13 16:26 → 2026-07-14 19:40)

### What Was Built
- Golden-output baseline (all 6 estimators) captured pre-refactor and wired into a permanent drift-detection pytest gate, re-verified at the close of every subsequent phase
- Dashboard, `cache_contract.py`, `shipping.py`, and their console-script entry points removed entirely (preserved in git history)
- Surviving code reorganized into a modality-agnostic core + `infodynamics.text` on-ramp via pure `git mv`, zero behavior change
- Analysis pipeline decoupled to ndarray-only and made genuinely sklearn `Pipeline`-composable; known bugs (`averaging_weigts` typo, `window_size=0` crash, `_MODEL_CACHE` device mutation) fixed as labeled commits along the way
- Curated public API (`__all__` at both `infodynamics` and `infodynamics.text`), canonical usage example, and an old→new import migration table
- Milestone's definition of done proven empirically (not assumed): repo-wide grep sweep, fresh no-extras venv smoke test, full suite green (92 tests, count reconciled), golden baseline + clone spot-checks — all with literal, checked-in evidence

### What Worked
- Subtractive-before-additive, move-before-refactor phase ordering (Remove → Reorganize → Decouple → Curate → Verify) kept numerical drift bisectable at every step — the golden-output snapshot caught nothing because pure-move and bug-fix commits were never mixed in the same commit
- Separating "pure relocation" commits from "behavior-changing fix" commits (sharpest in Phase 3) meant any drift, had it occurred, would have pointed at exactly one commit
- Writing the phase-5 verification as its own scripted, evidence-gathering plan (rather than a checklist of "should pass" assertions) produced a `VERIFICATION.md` that pastes literal commands and literal output — independently re-derivable, not just asserted
- The independent `gsd-verifier` re-check for Phase 5 caught nothing new (all 5 criteria held up), but it *did* re-derive the 81→68 baseline from a separate scratch worktree rather than trusting the prior number — that's the kind of check that's cheap when it passes and invaluable when it doesn't

### What Was Inefficient
- Plan 05-02's executor self-declared phase and milestone completion (flipped ROADMAP.md/REQUIREMENTS.md/STATE.md to "Complete") in its own final commit, ahead of and independent from the orchestrator's dedicated verification step. The technical claims held up when independently re-checked, but the process gate was bypassed once — worth hardening the plan/executor template so an executor's own commit can never cascade phase-level completion.
- The code-review file-scoping script (extracts `key-files.created`/`modified` from a SUMMARY.md's YAML frontmatter) only parses multi-line list syntax (`created:\n  - file.py`), not inline array syntax (`created: [file.yml]`). This silently dropped `.github/workflows/ci.yml` from the Phase 5 review scope until caught by manual inspection.
- Plan 05-02's `<verify>` block hardcoded an expected test count ("91 tests collected") that went stale the moment its own sibling plan (05-01) added a regression test earlier in the same phase — the executor had to reconcile 92 vs. 91 on the fly rather than the plan anticipating a same-phase dependency could move the baseline.

### Patterns Established
- Golden-output snapshot pattern: one-time capture script (`tests/golden/capture_baseline.py`) + checked-in `.npz`/`.json` + permanent `np.allclose` pytest comparison test, re-verified at the close of every phase — reusable for any future refactor requiring numerical-drift protection
- Scripted, evidence-citing `VERIFICATION.md`: every claimed truth pastes the literal command and literal output that proves it, never "should pass" — set the bar for what "empirically verified" means in this project going forward

### Key Lessons
1. When a plan's own deliverable *is* the phase verification (as Phase 5's evidence-gathering plan was), still route the result through the standard independent verifier pass — don't let a plan's self-authored "status: passed" become the trigger for marking tracking files complete.
2. Hardcoded expected counts (test counts, occurrence counts) in a plan's `<verify>` block go stale the instant an earlier plan in the same phase changes the baseline — frame these as "reconcile against actual, explain any delta" rather than a fixed literal to match.
3. YAML frontmatter extraction used for review/audit file-scoping needs to handle both inline (`[a, b]`) and multi-line list array syntax — a script that only handles one silently produces an incomplete scope with no error.

### Cost Observations
- Model mix: `executor_model`/`verifier_model` = sonnet throughout Phase 5 execution; `planner_model` = opus (used in earlier planning sessions, not directly observed this session)
- Sessions: at least 2 within this visible window (Phase 5 execute-phase run; milestone completion run), likely several more across Phases 1-4 given the ~27-hour, 115-commit span
- Notable: Phase 5 ran fully sequential (no parallel worktrees) because the local worktree base had diverged from `origin/HEAD` — the auto-degrade guard caught this cleanly rather than failing; setting `worktree.baseRef:"head"` would restore parallel wave execution for future milestones if that recurs

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v0.5 | several | 5 | First milestone — baseline for future comparison |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|---------------------|
| v0.5 | 92 | not tracked | 0 (GitHub Actions CI added, but non-gating/bonus) |

### Top Lessons (Verified Across Milestones)

1. *(none yet — first milestone; lessons above become candidates for cross-validation once a second milestone ships)*

# Phase 5: Verify - Context

**Gathered:** 2026-07-14
**Status:** Ready for planning

<domain>
## Phase Boundary

The milestone's definition of done — decoupled, reorganized, tests green, no numerical drift — gets proven empirically, not assumed. This phase delivers no new capability: it audits the finish line against the 5 ROADMAP success criteria (grep-clean of removed infra, no-extras-venv import + core-only path, full pytest green with test-count reconciliation, golden-snapshot + clone/get_params/set_params spot-check) and produces a written record of the evidence.

Requirements in scope: CORE-03, QA-04.

</domain>

<decisions>
## Implementation Decisions

### Failure/remediation policy
- **D-01:** When a verification check fails, fix small, obviously in-scope issues inline as part of this phase (stray leftover reference, non-actionable `ImportError` message, minor `__all__` gap), then re-verify. Do not treat every failure as blocking-stop.
- **D-02:** Escalate (stop and ask) rather than auto-fix anything that touches public API or behavior — signature changes, symbol renames, or numerical-output changes. Everything smaller (stray references, docstrings, import wiring) is fair game to fix inline.
- **D-03:** Fixes discovered during verification get their own separate, labeled commits (e.g. `fix(05): ...`), not bundled into one big verification commit. Matches the move-before-refactor / subtractive-first commit discipline already used in Phases 1-4.
- **D-04:** If a failing check can only be fixed by violating a locked constraint (e.g. adding a back-compat import shim, which PROJECT.md's "no backward-compatible import paths" constraint rules out), stop and ask — don't bend the constraint unilaterally.

### Deliverable form & permanence
- **D-05:** Produce a checked-in `VERIFICATION.md` in the phase directory (`.planning/phases/05-verify/`) walking through all 5 ROADMAP success criteria with evidence: grep output, no-extras-venv results, test counts, golden-diff/clone-spot-check results.
- **D-06:** The fresh-venv / no-extras check (criteria 2-3) is a one-off manual verification this phase — `python -m venv` + `pip install .` (no extras) run once, results captured in `VERIFICATION.md`. Do not leave behind permanent no-extras smoke-test tooling; that would be new scope beyond what ROADMAP asks for.
- **D-07:** Add a minimal CI workflow (this repo currently has none — no `.github/workflows`, no tox/nox) as a **bonus deliverable that does not gate phase completion**. Phase 5 is still "done" once the 5 ROADMAP criteria pass regardless of whether CI exists; the CI workflow is additional value-add, not a 6th success criterion. Scope of the workflow itself (what it runs) is Claude's call at plan time — keep it minimal (e.g. install + run pytest on push).
- **D-08:** No new tooling needed for criterion 5 (golden snapshot + clone/get_params/set_params spot-check) — `tests/test_golden_baseline.py` and `tests/test_pipeline_composition.py` already cover this from Phase 1/3. Phase 5 just runs pytest and confirms they're green.

### Golden-baseline & test-count reconciliation
- **D-09 (verified during discussion):** Pre-refactor baseline = 81 test functions across 9 files (confirmed via `git show 0513127:tests/*.py` — commit `0513127` "docs: create roadmap (5 phases)" is the pre-Phase-1 HEAD; matches `.planning/codebase/TESTING.md`'s "81 test functions"). `test_manifest.py` accounted for 13 of those. Reconciliation floor per QA-04 = 81 − 13 = **68** (matches ROADMAP's Phase 1 criterion "full suite green at exactly 68 tests"). Current suite collects **91** via `pytest --collect-only -q` — comfortably above the floor; tests were *added* in Phases 2-4 (text-mirror tests, golden-baseline tests, pipeline-composition parametrized tests, public-API tests), nothing silently lost.
- **D-10:** `VERIFICATION.md` shows only start → target → actual for the test-count reconciliation (81 → 68 → 91), not a full per-phase breakdown (68 → 72 → … → 91). Keep it concise.
- **D-11:** The verification pytest run includes the `@pytest.mark.slow` hypothesis property-based tests in `test_infodynamics_class.py` — run the full suite once (QA-04 says "the full pytest suite passes"), note the timing in the report.
- **D-12:** Golden-snapshot "still matches" (criterion 5) means whatever `tests/test_golden_baseline.py` already asserts (its existing floating-point tolerance) — don't add a stricter bit-exact/byte-identity check on top. Phase 5 confirms the existing test passes, doesn't re-litigate its tolerance.

### Claude's Discretion
- **"Fast" import threshold (criterion 2):** left undiscussed — user selected other areas instead. Default to a qualitative note in `VERIFICATION.md` (e.g. "sub-second, no heavy deps imported") unless the researcher/planner finds a reason to pin a hard numeric assertion; this is a technical implementation detail, not a founder-level call.
- **CI workflow scope/contents:** per D-07, keep minimal — planner decides exact triggers/steps (e.g. install core deps + `pytest`, matrix or single Python version) as long as it doesn't become a phase-gating dependency.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase & milestone scope
- `.planning/ROADMAP.md` §"Phase 5: Verify" — goal, 5 success criteria, requirements mapping (CORE-03, QA-04)
- `.planning/REQUIREMENTS.md` — CORE-03 (core-only path with no heavy extras), QA-04 (full suite passes, test count reconciled)
- `.planning/PROJECT.md` — constraints (no back-compat shims, breaking changes accepted pre-1.0), Out of Scope table (PyPI publishing, `pyproject.toml` migration/packaging modernization, full `check_estimator` conformance all explicitly out — CI is not listed either way, hence D-07's "bonus, non-gating" resolution)

### Prior phase context (what this phase verifies)
- `.planning/phases/04-curate-the-public-api/04-CONTEXT.md` — the curated `__all__` surfaces this phase's grep sweep and import checks validate
- `.planning/phases/03-decouple-the-pipeline/03-CONTEXT.md` — D-02/D-03 (transform semantics, array output) and the `tests/test_pipeline_composition.py` clone/get_params/set_params round-trip this phase spot-checks
- `.planning/phases/02-reorganize-into-core-text-on-ramp/02-CONTEXT.md` — the no-extras-venv import contract (`infodynamics` and `infodynamics.text` both importable without heavy extras) this phase re-verifies end-to-end

### Existing code / evidence (verified during this discussion)
- `tests/test_golden_baseline.py` — existing golden-snapshot drift test (Phase 1/3), source of truth for criterion 5's tolerance (D-12)
- `tests/test_pipeline_composition.py` — existing clone/get_params/set_params round-trip + end-to-end Pipeline composition test (Phase 3), source of truth for criterion 5's estimator spot-check (D-08)
- `tests/golden/capture_baseline.py`, `tests/golden/__init__.py` — golden-baseline capture harness
- `.planning/codebase/TESTING.md` — pre-refactor test inventory (81 functions / 9 files), confirmed still accurate against commit `0513127`
- `setup.py` — `extras_require`: `embedding`, `morphology`, `clustering`, `viz-projection`, `test` (self-sufficient per Phase 1's `01-04-PLAN.md`); `install_requires` is the core-only dependency set criterion 3 must run against
- `CHANGELOG.md` — existing old→new import migration table (Phase 4), relevant background for the grep sweep (nothing in it should point at removed `dashboard`/`shipping`/`cache_contract`/`bench_core` paths)
- No `.github/workflows/`, `tox.ini`, or `noxfile.py` exist yet — confirmed absent; relevant to D-07 (there's history of a prior, now-removed CI setup per `git log` commit `924d6fb rm ci`, but nothing to build on today)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/golden/capture_baseline.py` — can be re-run standalone to regenerate/compare against the golden snapshot if needed during verification
- `tests/test_public_api.py` (Phase 4) — already locks `infodynamics.__all__` / `infodynamics.text.__all__`; useful cross-check alongside the manual no-extras venv import test

### Established Patterns
- `pytest.importorskip()` used throughout for optional-dependency gating (`tests/test_clustering.py` etc.) — the pattern to point to when explaining why `Encoder()`/`MorphologicalEncoder()`/`SignalClusterer()` must fail only at *instantiation*, not at *import time*
- Commit message convention `type(NN-MM): description` used consistently across all prior phases — D-03's separate fix commits should follow this (`fix(05): ...`)

### Integration Points
- Fresh no-extras venv check touches `setup.py`'s `install_requires` vs `extras_require` split directly — this is the boundary criterion 2/3 actually tests
- Repo-wide grep sweep (criterion 1) targets: `dashboard`, `cache_contract`, `shipping`, `bench_core` — same term set used in Phase 1's original sweep (`01-03-PLAN.md`), now re-run as the final confirmation

</code_context>

<specifics>
## Specific Ideas

No specific UI/behavioral requirements (this is an internal, empirical verification phase). The concrete, user-driven decisions are the failure/remediation policy (D-01–D-04), the VERIFICATION.md + bonus-CI deliverable shape (D-05–D-08), and the confirmed reconciliation math (D-09–D-12) captured above.

</specifics>

<deferred>
## Deferred Ideas

None beyond the CI-scope clarification already resolved inline (D-07) — no new capabilities were proposed outside the phase's verification boundary during this discussion.

### Reviewed Todos (not folded)
None — `todo.match-phase` returned zero matches for Phase 5.

</deferred>

---

*Phase: 5-Verify*
*Context gathered: 2026-07-14*

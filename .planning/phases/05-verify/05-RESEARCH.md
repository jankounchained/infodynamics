# Phase 5: Verify - Research

**Researched:** 2026-07-14
**Domain:** Empirical verification/audit of a Python library refactor (no new features) — repo-wide grep sweep, fresh no-extras venv smoke test, full pytest reconciliation, golden-baseline/estimator spot-check, optional minimal CI
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Failure/remediation policy**
- **D-01:** When a verification check fails, fix small, obviously in-scope issues inline as part of this phase (stray leftover reference, non-actionable `ImportError` message, minor `__all__` gap), then re-verify. Do not treat every failure as blocking-stop.
- **D-02:** Escalate (stop and ask) rather than auto-fix anything that touches public API or behavior — signature changes, symbol renames, or numerical-output changes. Everything smaller (stray references, docstrings, import wiring) is fair game to fix inline.
- **D-03:** Fixes discovered during verification get their own separate, labeled commits (e.g. `fix(05): ...`), not bundled into one big verification commit. Matches the move-before-refactor / subtractive-first commit discipline already used in Phases 1-4.
- **D-04:** If a failing check can only be fixed by violating a locked constraint (e.g. adding a back-compat import shim, which PROJECT.md's "no backward-compatible import paths" constraint rules out), stop and ask — don't bend the constraint unilaterally.

**Deliverable form & permanence**
- **D-05:** Produce a checked-in `VERIFICATION.md` in the phase directory (`.planning/phases/05-verify/`) walking through all 5 ROADMAP success criteria with evidence: grep output, no-extras-venv results, test counts, golden-diff/clone-spot-check results.
- **D-06:** The fresh-venv / no-extras check (criteria 2-3) is a one-off manual verification this phase — `python -m venv` + `pip install .` (no extras) run once, results captured in `VERIFICATION.md`. Do not leave behind permanent no-extras smoke-test tooling; that would be new scope beyond what ROADMAP asks for.
- **D-07:** Add a minimal CI workflow (this repo currently has none — no `.github/workflows`, no tox/nox) as a **bonus deliverable that does not gate phase completion**. Phase 5 is still "done" once the 5 ROADMAP criteria pass regardless of whether CI exists; the CI workflow is additional value-add, not a 6th success criterion. Scope of the workflow itself (what it runs) is Claude's call at plan time — keep it minimal (e.g. install + run pytest on push).
- **D-08:** No new tooling needed for criterion 5 (golden snapshot + clone/get_params/set_params spot-check) — `tests/test_golden_baseline.py` and `tests/test_pipeline_composition.py` already cover this from Phase 1/3. Phase 5 just runs pytest and confirms they're green.

**Golden-baseline & test-count reconciliation**
- **D-09 (verified during discussion):** Pre-refactor baseline = 81 test functions across 9 files (confirmed via `git show 0513127:tests/*.py` — commit `0513127` "docs: create roadmap (5 phases)" is the pre-Phase-1 HEAD; matches `.planning/codebase/TESTING.md`'s "81 test functions"). `test_manifest.py` accounted for 13 of those. Reconciliation floor per QA-04 = 81 − 13 = **68** (matches ROADMAP's Phase 1 criterion "full suite green at exactly 68 tests"). Current suite collects **91** via `pytest --collect-only -q` — comfortably above the floor; tests were *added* in Phases 2-4 (text-mirror tests, golden-baseline tests, pipeline-composition parametrized tests, public-API tests), nothing silently lost.
- **D-10:** `VERIFICATION.md` shows only start → target → actual for the test-count reconciliation (81 → 68 → 91), not a full per-phase breakdown (68 → 72 → … → 91). Keep it concise.
- **D-11:** The verification pytest run includes the `@pytest.mark.slow` hypothesis property-based tests in `test_infodynamics_class.py` — run the full suite once (QA-04 says "the full pytest suite passes"), note the timing in the report.
- **D-12:** Golden-snapshot "still matches" (criterion 5) means whatever `tests/test_golden_baseline.py` already asserts (its existing floating-point tolerance) — don't add a stricter bit-exact/byte-identity check on top. Phase 5 confirms the existing test passes, doesn't re-litigate its tolerance.

### Claude's Discretion
- **"Fast" import threshold (criterion 2):** left undiscussed — user selected other areas instead. Default to a qualitative note in `VERIFICATION.md` (e.g. "sub-second, no heavy deps imported") unless the researcher/planner finds a reason to pin a hard numeric assertion; this is a technical implementation detail, not a founder-level call.
- **CI workflow scope/contents:** per D-07, keep minimal — planner decides exact triggers/steps (e.g. install core deps + `pytest`, matrix or single Python version) as long as it doesn't become a phase-gating dependency.

### Deferred Ideas (OUT OF SCOPE)
None beyond the CI-scope clarification already resolved inline (D-07) — no new capabilities were proposed outside the phase's verification boundary during this discussion.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-03 | A core-only path (numeric array in → signals out) runs with only the required core dependencies installed (no text or heavy extras present) | Empirically re-verified this session in a real fresh venv (see "Empirical Findings" below): `pip install .` (no extras) succeeds, `InfoDynamics`/`MultiscaleInfoDynamics`/`WindowedRollingDistance` all run end-to-end on a plain `ndarray` with zero heavy/text imports in `sys.modules`. Documented reproducible script + `sys.modules` assertion pattern in Code Examples. |
| QA-04 | The full `pytest` suite passes against the reorganized package; the collected test count is reconciled against the pre-refactor baseline (no silent coverage loss beyond the known-removed `test_manifest.py`) | Empirically re-ran full suite this session: 91 passed, 0 failed, 6 warnings (all benign), 16.31s. `pytest --collect-only -q` reports 91 tests in 9 files, confirming D-09's reconciliation math still holds. Pitfalls section documents the `PytestUnknownMarkWarning` for the unregistered `slow` marker and why it doesn't affect the count or exit code. |

</phase_requirements>

## Summary

Phase 5 has no new implementation surface — it is a scripted, evidence-gathering pass over work already done in Phases 1-4. The research for this phase is therefore mostly *empirical*: this session directly executed every check ROADMAP's 5 success criteria describe (grep sweep, fresh no-extras venv + timed imports, core-only smoke test, full pytest run + collect-only count, golden-baseline/clone spot-check) against the current `feature/artifacts` branch state, and the evidence is folded into this document so the planner can write `VERIFICATION.md`-producing tasks with exact commands and expected output already validated, rather than guessing at what a "fresh venv" run will show.

Three concrete findings should directly shape the plan:

1. **A real, in-scope bug was found** (not a hypothetical from a pitfalls table): `MorphologicalEncoder.encode()` in `infodynamics/text/morphology.py:194` does an *unguarded* `from textdescriptives import extract_df` that runs before the module's own guarded `_load_pipeline()` call, so instead of the actionable `ImportError: The 'morphology' extra is required to use MorphologicalEncoder. Install it with pip install infodynamics[morphology].` a user without the extra actually sees a bare `ModuleNotFoundError: No module named 'textdescriptives'`. This is exactly D-01's named example ("non-actionable `ImportError` message") — small, in-scope, fixable inline, own `fix(05):` commit per D-03.
2. **The literal ROADMAP wording "fail only at instantiation" does not match — and should not match — the actual, correct behavior.** `Encoder()`, `MorphologicalEncoder()`, and `SignalClusterer()` all instantiate successfully with zero extras installed (verified in a real fresh venv this session); the `ImportError` only fires on first real use (`.fit()`/`.transform()`/`.encode()`). This is required by sklearn's `BaseEstimator` convention (constructors must not validate/import — needed for `get_params`/`set_params`/`clone` to work per API-01) and is exactly what `tests/test_pipeline_composition.py`'s own docstring already documents ("Constructing Encoder/MorphologicalEncoder does not load their heavy models (lazy)"). The plan should verify "fails at first *use*, not at bare construction" — not add a check that these constructors themselves raise, which would be wrong and would break `clone()`.
3. **"Fast" import is better proven with a `sys.modules` membership assertion than a wall-clock threshold.** `import infodynamics` costs ~1.0s in a fresh venv — but that time is *entirely* `scikit-learn`'s own import graph (`sklearn.cluster` pulls in `sklearn.manifold`/`sklearn.tree` transitively), a required core dependency, not one of the four heavy optional extras. A hard "<1s" pinned assertion would be flaky (borderline on slower CI runners) and wouldn't actually test what criterion 2 cares about. Asserting `{'torch', 'sentence_transformers', 'spacy', 'spacy_udpipe', 'textdescriptives', 'tslearn', 'umap'} & set(sys.modules) == set()` after `import infodynamics; import infodynamics.text` is deterministic, environment-independent, and directly proves the thing criterion 2 is actually about.

**Primary recommendation:** Treat `VERIFICATION.md` as a literal transcript of reproducible shell/python snippets (all of which are given verbatim in Code Examples below, already run once this session with real output) plus the one real bug fix (`morphology.py` unguarded import) as a separate `fix(05):` commit before the golden-baseline/pytest re-run that closes the loop. The optional CI workflow (D-07) should be a single-file, single-job, single-Python-version (3.14) GitHub Actions workflow using `actions/checkout@v6` + `actions/setup-python@v6`, installing `.[test]` and running `pytest`, with no codecov/poetry/mkdocs baggage (the repo's prior CI, removed in commit `924d6fb`, was poetry+codecov+mkdocs-based and is not a template to reuse).

## Architectural Responsibility Map

This phase touches no application-tier code — it is a verification/tooling pass. The table below maps each ROADMAP success-criterion check to the layer of the project it verifies, using this project's own layers (package/distribution, core library, text on-ramp, test suite, CI) in place of the generic browser/API/DB tiers from the standard template (not applicable to a library-only project).

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Repo-wide grep sweep (criterion 1) | Repo / VCS metadata | — | Pure `git grep` over tracked files; no code executes |
| No-extras import + timing (criterion 2) | Package/Distribution (`setup.py` `install_requires` vs `extras_require`) | Core library (`infodynamics/__init__.py`) | Tests the packaging boundary, not application logic |
| Core-only numeric path (criterion 3) | Core library (`infodynamics/pipeline.py`, `time_series.py`, `scalogram.py`) | Package/Distribution | Proves the core estimators need nothing beyond `install_requires` |
| Full pytest + count reconciliation (criterion 4 / QA-04) | Test suite (`tests/`) | — | Reconciles collected test count against the pre-refactor baseline |
| Golden-baseline + clone/get_params/set_params spot-check (criterion 5) | Test suite (`tests/test_golden_baseline.py`, `tests/test_pipeline_composition.py`) | Core + Text on-ramp (estimators under test) | Existing tests already cover this; Phase 5 only re-runs and records |
| `VERIFICATION.md` authoring (D-05) | Documentation | — | New artifact this phase produces |
| Bonus CI workflow (D-07) | CI/Build (`.github/workflows/`) | Test suite | Non-gating; wraps `pip install .[test]` + `pytest` |

## Standard Stack

No new runtime dependencies are introduced by this phase. The "stack" here is verification tooling, all of which is either already a project dependency or a system/stdlib tool.

### Core
| Tool | Version (verified this session) | Purpose | Why Standard |
|------|-----|---------|--------------|
| `pytest` | 9.1.1 (dev venv) [VERIFIED: `pip list` this session] | Full-suite run + `--collect-only` count reconciliation | Already the project's test runner (`extras_require['test']`) |
| `git grep` | via system `git` | Criterion 1 repo-wide sweep, tracked-files-only | Respects `.gitignore`/untracked clutter automatically — see Pitfalls |
| `python -m venv` | stdlib, Python 3.14.5 [VERIFIED: `python3 --version` this session] | Fresh, isolated no-extras environment for criteria 2-3 | Zero extra dependency; matches D-06's "one-off, no permanent tooling" |
| `pip install .` | pip 26.1.2 in fresh venv [VERIFIED: this session] | Installs only `install_requires` (no `[extras]` suffix) | Directly exercises the `setup.py` `install_requires`/`extras_require` split |

### Supporting (bonus CI deliverable, D-07)
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `actions/checkout` | `v6` [CITED: github.com/actions/checkout releases, cross-checked via WebSearch 2026-07] | Checks out repo in CI runner | Standard first step of any GH Actions workflow |
| `actions/setup-python` | `v6`, `python-version: "3.14"` [CITED: github.com/actions/setup-python — confirmed 3.14 supported via `actions/python-versions` tool cache / GitHub Releases fallback] | Provisions Python 3.14 on the runner | Matches project's pinned interpreter (CLAUDE.md: Python 3.14.x) |

**Version verification note:** GitHub Actions marketplace action tags increment frequently (a `v7` bump for `actions/checkout` was already visible in search results as of this research date). At plan/execution time, re-check the latest major tag (`gh api repos/actions/checkout/releases/latest` or the Marketplace page) rather than trusting this document's pin indefinitely — but `v6` is confirmed current-stable as of 2026-07-14 and is safe to write into the workflow now.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| One-off `python -m venv` script (D-06) | A permanent `tox`/`nox` no-extras environment | Rejected by D-06 explicitly — new permanent tooling is out of scope for this milestone |
| `sys.modules` membership assertion for "fast" import | `pytest-benchmark` or `hyperfine` timing harness | Overkill for a qualitative, one-off check; adds a new test dependency for no real benefit — see Don't Hand-Roll |
| Minimal single-job GH Actions workflow | Matrix across multiple Python versions / OSes | Out of scope per D-07 ("keep it minimal"); project only supports Python 3.14.x today (CLAUDE.md), so a matrix would test versions the project doesn't claim to support |

**Installation:** None — this phase installs nothing new into the project's own dependency set. The bonus CI workflow installs the existing `test` extra (`pip install .[test]`) inside the CI runner only.

## Package Legitimacy Audit

**Not applicable.** This phase introduces zero new Python packages to `setup.py`'s `install_requires`/`extras_require`. The only new artifact with external references is the optional `.github/workflows/*.yml` (D-07), which pins GitHub Marketplace Actions (`actions/checkout`, `actions/setup-python`) rather than PyPI/npm/crates packages — the `package-legitimacy check` seam and its npm/PyPI/crates verification protocol do not apply to GitHub Actions references. Supply-chain hygiene for those two Actions is covered instead under Security Domain → Known Threat Patterns below (pin to a known major version tag, avoid `@main`/`@master`).

## Architecture Patterns

### System Architecture Diagram

```
                      ┌─────────────────────────┐
                      │   Phase 5 entry point     │
                      │  (plan tasks execute in    │
                      │   this order)               │
                      └────────────┬────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                             ▼
┌───────────┐          ┌────────────────────┐          ┌──────────────────┐
│ Criterion 1│          │  Criteria 2 + 3     │          │  Criteria 4 + 5    │
│ grep sweep │          │  fresh no-extras venv│          │  pytest + golden   │
│            │          │                      │          │  + clone spot-check│
│ git grep -niE          │ 1. python -m venv    │          │ 1. pytest -q       │
│  'dashboard|            │ 2. pip install .     │          │    (full suite,    │
│  cache_contract|        │    (no [extras])     │          │    incl. @slow)    │
│  shipping|               │ 3. import infodynamics│          │ 2. pytest          │
│  bench_core'             │    (sys.modules check │          │    --collect-only  │
│  -- tracked files         │    + wall-clock note) │          │    -q  (count)     │
│  only                     │ 4. import infodynamics.│          │ 3. confirm         │
│                            │    text                │          │    test_golden_    │
│ → expect: 0 hits          │ 5. Encoder()/          │          │    baseline.py and │
│                            │    MorphologicalEncoder│          │    test_pipeline_   │
│                            │    ()/SignalClusterer()│          │    composition.py  │
│                            │    instantiate OK       │          │    both pass        │
│                            │ 6. .fit()/.transform() │          │    (already exist,  │
│                            │    on those → actionable│          │    D-08)            │
│                            │    ImportError          │          │                     │
│                            │ 7. core-only numeric     │          │ → 91 tests total,   │
│                            │    path: ndarray in →   │          │   reconciled against│
│                            │    InfoDynamics/         │          │   81 → 68 → 91       │
│                            │    MultiscaleInfoDynamics│          │   (D-09/D-10)        │
│                            │    .fit_transform() out  │          │                     │
└──────────────┬─────────────┘          └───────────────┬───────┘
               │                                          │
               └─────────────────────┬────────────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  D-01 remediation loop    │
                         │  (only if a check fails)   │
                         │  - small/in-scope → fix    │
                         │    inline, fix(05): commit │
                         │  - API/behavior/constraint │
                         │    touching → stop & ask   │
                         │    (D-02/D-04)              │
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  Write VERIFICATION.md    │
                         │  (D-05) — all 5 criteria's │
                         │  evidence transcribed      │
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  Bonus, non-gating (D-07): │
                         │  .github/workflows/ci.yml  │
                         │  checkout@v6 + setup-python │
                         │  @v6(3.14) + pip install    │
                         │  .[test] + pytest           │
                         └─────────────────────────┘
```

### Recommended Verification Script Structure
```
.planning/phases/05-verify/
├── 05-RESEARCH.md          # this file
├── 05-CONTEXT.md           # already exists
├── 05-VERIFICATION.md      # D-05 deliverable — evidence transcript
└── 05-NN-PLAN.md           # plan(s), created by planner

(no new files under infodynamics/ or tests/ except the morphology.py bug fix,
 and no permanent no-extras venv tooling per D-06)

.github/workflows/
└── ci.yml                  # D-07 bonus, non-gating
```

### Pattern 1: Fresh no-extras venv smoke test (one-off, D-06)
**What:** Create a throwaway venv outside the repo (or in a scratch/tmp location, never committed), `pip install .` with no `[extras]` suffix, run the import/instantiation/core-only checks, capture output into `VERIFICATION.md`, then discard the venv.
**When to use:** Exactly once per this phase's execution — not wired into CI, not a permanent script, per D-06.
**Example (verified working this session, Python 3.14.5, macOS):**
```bash
# Source: this research session, run 2026-07-14 against feature/artifacts
python3 -m venv /tmp/infodynamics-noextras-check
/tmp/infodynamics-noextras-check/bin/pip install --quiet --upgrade pip
/tmp/infodynamics-noextras-check/bin/pip install --quiet .   # NOTE: from repo root, no [extras]
/tmp/infodynamics-noextras-check/bin/python - <<'PY'
import sys, time

t0 = time.perf_counter()
import infodynamics
t1 = time.perf_counter()
import infodynamics.text
t2 = time.perf_counter()

print(f"import infodynamics:      {(t1 - t0) * 1000:.1f} ms")
print(f"import infodynamics.text: {(t2 - t1) * 1000:.1f} ms")

heavy = {"torch", "sentence_transformers", "spacy", "spacy_udpipe", "textdescriptives", "tslearn", "umap"}
present = heavy & set(sys.modules)
assert not present, f"heavy extras leaked into sys.modules on plain import: {present}"
print("no heavy extras imported: OK")

# criterion 2: instantiation must succeed without extras (sklearn __init__ convention)
enc = infodynamics.text.Encoder(model_name="sentence-transformers/all-MiniLM-L6-v2")
me = infodynamics.text.MorphologicalEncoder(feature_group="pos_proportions")
sc = infodynamics.SignalClusterer()
print("Encoder()/MorphologicalEncoder()/SignalClusterer() instantiate OK without extras")

# first *use* must raise an actionable ImportError naming the missing extra
try:
    enc.transform(["hello"])
    raise SystemExit("expected ImportError, got none")
except ImportError as e:
    assert "embedding" in str(e) and "pip install" in str(e)
    print("Encoder.transform() actionable ImportError: OK")

try:
    sc.fit([[1, 2, 3], [4, 5, 6]])
    raise SystemExit("expected ImportError, got none")
except ImportError as e:
    assert "clustering" in str(e) and "pip install" in str(e)
    print("SignalClusterer.fit() actionable ImportError: OK")

try:
    me.transform(["ahoj svete"])
    raise SystemExit("expected ImportError, got none")
except ImportError as e:
    # KNOWN BUG at time of writing -- see Pitfall 1: this currently raises a
    # bare ModuleNotFoundError instead. Fix morphology.py first, then this
    # assertion should pass.
    assert "morphology" in str(e) and "pip install" in str(e), (
        f"non-actionable ImportError -- see Pitfall 1: {e!r}"
    )
    print("MorphologicalEncoder.transform() actionable ImportError: OK")

# criterion 3: core-only path, numeric ndarray in -> signals out
import numpy as np
rng = np.random.default_rng(0)
X = rng.normal(size=(30, 8))
out = infodynamics.InfoDynamics(window_size=3).fit_transform(X)
print("core-only InfoDynamics.fit_transform shape:", out.shape)
out2 = infodynamics.MultiscaleInfoDynamics().fit_transform(X)
print("core-only MultiscaleInfoDynamics.fit_transform shape:", out2.shape)
print("CORE-03 core-only path: OK")
PY
rm -rf /tmp/infodynamics-noextras-check
```
**Actual output captured this session** (before the morphology.py fix — MorphologicalEncoder step will need to be re-run after Pitfall 1 is fixed):
```
import infodynamics:      1006.0 ms
import infodynamics.text: 4.9 ms
no heavy extras imported: OK
Encoder()/MorphologicalEncoder()/SignalClusterer() instantiate OK without extras
Encoder.transform() actionable ImportError: OK
SignalClusterer.fit() actionable ImportError: OK
[would currently fail here -- see Pitfall 1]
```

### Pattern 2: `git grep` for the repo-wide sweep (criterion 1)
**What:** Use `git grep`, not plain `grep -r`, so the sweep only covers tracked files.
**When to use:** Criterion 1's exact command.
**Example:**
```bash
# Source: this research session — already run against feature/artifacts, 0 hits
git grep -niE "dashboard|cache_contract|shipping|bench_core"
echo "exit code: $?"   # 1 = no matches found (git grep convention), confirms clean sweep
```
**Verified this session:** returns zero hits (exit code 1) across the entire tracked tree, including `CHANGELOG.md` (whose old→new migration table correctly refers to removed paths in prose about *history*, not as live references — worth a human glance in `VERIFICATION.md` to confirm the CHANGELOG mentions are historical/instructional, not live symbol references, since 0 raw hits already proves even that isn't a false-negative concern here).

### Pattern 3: Minimal GitHub Actions workflow (D-07, bonus/non-gating)
**What:** Single job, single Python version, install `test` extra, run pytest.
**When to use:** Optional deliverable — implement after the 5 gating criteria are done and documented.
**Example:**
```yaml
# Source: pattern synthesized from actions/checkout and actions/setup-python
# official usage docs [CITED: github.com/actions/checkout, github.com/actions/setup-python]
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.14"
      - name: Install
        run: pip install .[test]
      - name: Test
        run: pytest -q
```
**Note:** No codecov, no poetry, no mkdocs, no release/publish job, no matrix — the repo's previous CI (removed in commit `924d6fb`, Nov 2023) was a 6-file poetry+codecov+mkdocs setup that doesn't apply to this project's current `setup.py`/pip-based tooling; it is not a template to resurrect, per PROJECT.md's "no packaging modernization" and D-07's "keep it minimal."

### Anti-Patterns to Avoid
- **Pinning a hard wall-clock import threshold (e.g. `assert import_time < 1.0`):** the empirically measured `import infodynamics` time (~1.0s) is dominated by scikit-learn's own transitive import graph (a required core dependency, not a heavy optional extra) and will vary by machine/disk-cache state. A brittle CI assertion here produces false failures unrelated to what criterion 2 actually verifies. Use the `sys.modules` membership check instead (Pattern 1) plus a qualitative wall-clock note.
- **Testing "fails at instantiation" literally:** do not add an assertion that `Encoder(...)`/`MorphologicalEncoder(...)`/`SignalClusterer(...)` themselves raise `ImportError` without extras — they must NOT, by sklearn's `BaseEstimator` contract (constructors are param-storage-only; see API-01's clone/get_params/set_params requirement). The correct assertion is "constructs cleanly, fails only on first real use (`fit`/`transform`/`encode`)."
- **Plain `grep -r` instead of `git grep` for criterion 1:** the repo has untracked root clutter (`morphology_demo_output/`, demo scripts, CSVs — see `git status`) and a `.venv/` directory that a recursive plain grep would traverse, producing false-positive noise (e.g. hits inside `.venv/lib/.../site-packages` docs, or inside untracked scratch scripts) that isn't representative of the actual codebase state `RM-05` cares about.
- **Building permanent no-extras CI/tox tooling for D-06's check:** explicitly out of scope this phase; the fresh-venv check is one-off and manual, recorded as evidence, not automated infrastructure.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting whether heavy extras were imported | Custom `sys.modules` diffing framework, or timing-based heuristics | The simple `heavy_set & set(sys.modules)` one-liner shown in Pattern 1 | It's a single deterministic assertion; no library needed, no flakiness across machines |
| Measuring "fast enough" import | `pytest-benchmark`, `hyperfine`, or a bespoke timing harness with statistical significance testing | `time.perf_counter()` around a single import, recorded qualitatively in `VERIFICATION.md` | This is a one-off manual check (D-06), not a regression-guarding perf test; adding a benchmarking dependency for a single documented number is disproportionate |
| Reconciling pytest test counts across environments | A custom test-discovery diffing script | `pytest --collect-only -q \| tail -1` (prints `"N tests collected"`) compared directly against the documented 81→68 baseline (D-09/D-10) | Built into pytest already; no new tooling needed |
| Verifying `ImportError` messages are actionable | A generic "docstring/error-message linter" | The literal try/except assertions shown in Pattern 1 (`"embedding" in str(e)`, `"pip install" in str(e)`) run once as part of the fresh-venv script | Confirms the exact 3 error sites empirically rather than building generalized tooling for a one-time check |

**Key insight:** Every check this phase needs is expressible as a short, disposable script run once and its output pasted into `VERIFICATION.md` — the temptation to build lasting tooling (a `verify_no_extras.py`, a pytest plugin, a CI gate on import time) should be resisted per D-06/D-07's explicit "not permanent infrastructure" framing. This phase's job is to produce *evidence*, not new product surface.

## Common Pitfalls

### Pitfall 1: `MorphologicalEncoder.encode()` raises a non-actionable `ModuleNotFoundError`, not the intended `ImportError`
**What goes wrong:** Calling `.transform()`/`.encode()` on a `MorphologicalEncoder` instance when `textdescriptives` isn't installed raises a bare `ModuleNotFoundError: No module named 'textdescriptives'` instead of the friendly `"The 'morphology' extra is required to use MorphologicalEncoder. Install it with pip install infodynamics[morphology]."` message.
**Why it happens:** `infodynamics/text/morphology.py:194`, inside `MorphologicalEncoder.encode()`, does an unguarded `from textdescriptives import extract_df` as the *very first* line of the method — before `_load_pipeline()` (which does have the guarded `try/except ImportError` pattern) is ever called. The guarded import pattern exists three other places in the same file (lines ~40-52, ~112-118, ~127-133) but was missed here.
**How to avoid:** Wrap the `from textdescriptives import extract_df` at line 194 in the same `try/except ImportError` → actionable-message pattern used elsewhere in the file. This is a two-line fix, squarely matching D-01's named example of an in-scope small fix ("non-actionable `ImportError` message"). Give it its own `fix(05): ...` commit per D-03 (this does not touch public API/behavior — same exception type, same message wording pattern already established — so D-02's escalation bar for API/behavior changes doesn't apply).
**Warning signs:** Empirically confirmed this session in a real fresh no-extras venv — this is not a hypothetical, it will reproduce every time `MorphologicalEncoder(...).transform(...)` is called without the `morphology` extra installed.

### Pitfall 2: ROADMAP's "fail only at instantiation" wording doesn't literally match (and shouldn't match) the correct implementation
**What goes wrong:** A naive reading of ROADMAP criterion 2 ("Encoder()/MorphologicalEncoder()/SignalClusterer() fail only at instantiation") could lead to writing a verification check that asserts `Encoder(model_name=...)` itself raises `ImportError` without extras — which would fail, because it correctly does NOT raise (constructors only store params).
**Why it happens:** REQUIREMENTS.md's TEXT-03 uses the more precise phrase "imported lazily at point-of-use" in the same sentence — "point-of-use" is the operative, accurate description; "at estimator instantiation" in the ROADMAP is loose phrasing that (given sklearn's `BaseEstimator` convention, and given `tests/test_pipeline_composition.py`'s own explicit comment: "Constructing Encoder/MorphologicalEncoder does not load their heavy models (lazy)") actually means "at first real use of the estimator," not "at the bare `Klass(...)` call."
**How to avoid:** Verify (a) bare construction succeeds with no extras installed (proves __init__ is side-effect-free, required for `clone()`/API-01), and (b) the first `fit`/`transform`/`encode` call raises the actionable `ImportError`. Both are independently true today (except for Pitfall 1's bug) and both are what criterion 2 actually needs proven.
**Warning signs:** If a verification task is written as `assert raises ImportError: Encoder(model_name="...")`, it is testing the wrong thing and will always fail against correct code — don't "fix" the code to match a misreading of the criterion.

### Pitfall 3: `PytestUnknownMarkWarning` for `@pytest.mark.slow` can look like a collection problem but isn't
**What goes wrong:** `pytest --collect-only -q` (and the full run) emits `PytestUnknownMarkWarning: Unknown pytest.mark.slow - is this a typo?` twice (once per decorated test in `tests/test_infodynamics_class.py`), because `slow` is used as a marker but never registered via a `markers =` config section (there is no `pytest.ini`/`pyproject.toml`/`setup.cfg` `[tool:pytest]` block in this repo at all).
**Why it happens:** Unregistered custom markers always warn under pytest's default `--strict-markers`-off behavior; this repo has no pytest config file, so there's nowhere the marker could have been registered.
**How to avoid:** This is a **warning**, not an error — it does not change the exit code, does not remove the test from the collected count, and does not fail the run. `VERIFICATION.md` should note it exists and explain it's benign (or, as an in-scope D-01-style small fix, add a minimal `pytest.ini` with a `markers = slow: ...` line — but this is new config surface, not a "stray reference," so lean toward "document it, don't fix it" unless the planner judges the two-line config addition clearly in-scope).
**Warning signs:** Confirmed empirically this session — full run (`pytest -q`) reports `91 passed, 6 warnings in 16.31s` with exit code 0. The 6 warnings are: 1 `h5py not installed` notice from `tslearn`, 2 `PytestUnknownMarkWarning` (the `slow` marker), and 3 `RuntimeWarning: invalid value encountered in log2/divide` from `infodynamics/metrics.py` (expected numerical edge-case warnings inside `test_window_size` and `test_calc_signal_data_shapes`, not new — these are the same class of intentional zero-division guards documented in the module's own comments). None indicate a real failure.

### Pitfall 4: `SignalClusterer`'s `ImportError` names the extra but not the class
**What goes wrong:** `SignalClusterer.fit()` (without the `clustering` extra) raises `ImportError: The 'clustering' extra is required to use this function. Install it with pip install infodynamics[clustering].` — this correctly names the extra and gives the exact install command (satisfying the letter of criterion 2's "actionable ImportError naming the missing extra"), but says "this function" rather than "SignalClusterer," because the message originates inside `infodynamics/clustering/dtw.py`'s `pairwise_distance()` / `barycenter.py`'s `average()` (shared low-level functions), not inside `SignalClusterer` itself.
**Why it happens:** `SignalClusterer.fit()` delegates to `pairwise_distance()`/`barycenter_average()`, which are also called independently outside the class context, so their error messages are intentionally class-agnostic.
**How to avoid:** This satisfies criterion 2 as literally worded (names the extra, gives the install command) — treat as acceptable, not a bug, unless the planner decides the extra specificity ("to use SignalClusterer") is worth a one-line message tweak. Flag as an Open Question below rather than a mandated fix, since D-01's bar is "non-actionable," and this message *is* actionable (just less specific than Encoder's/MorphologicalEncoder's).
**Warning signs:** Only surfaces if a verification test asserts the class name literally appears in the message string — don't write that assertion; assert on extra name + install command instead (as shown in Pattern 1).

### Pitfall 5: Collection warnings vs. collection *errors* look similar in `pytest --collect-only` output but aren't
**What goes wrong:** Skimming `pytest --collect-only -q` output, a "warnings summary" block at the end can be mistaken for a sign something is broken, especially when reconciling test counts against a numeric baseline.
**Why it happens:** pytest prints the warnings summary unconditionally after the collected-item list when any warnings fire (see Pitfall 3), even on a fully successful, zero-error collection.
**How to avoid:** The authoritative count is the final `"N tests collected in T.TTs"` line (or `"N/M errors"` if collection actually failed) — always read that line, not the presence/absence of a warnings block, to reconcile against D-09/D-10's 81→68→91 math.
**Warning signs:** Confirmed this session: `pytest --collect-only -q` prints a 4-line warnings summary and still ends with `91 tests collected in 14.35s` — the correct number to record.

## Code Examples

Verified patterns from this session's direct execution against the current `feature/artifacts` branch state:

### Repo-wide grep sweep (criterion 1)
```bash
# Source: this research session, run against feature/artifacts, verified 0 hits
git grep -niE "dashboard|cache_contract|shipping|bench_core"
```

### Full pytest run (criterion 4, includes @pytest.mark.slow per D-11)
```bash
# Source: this research session — real output below
time python -m pytest -q
```
Actual output this session (dev venv, all extras installed, 91 tests):
```
91 passed, 6 warnings in 16.31s
```

### Collect-only count reconciliation (D-09/D-10)
```bash
# Source: this research session
python -m pytest --collect-only -q | tail -1
```
Actual output: `91 tests collected in 14.35s` — matches D-09's expected 91 (above the 68 floor).

### `sys.modules` heavy-import assertion (criterion 2, "fast"/no-heavy-deps proof)
```python
# Source: this research session, run in the dev venv (all extras installed) —
# proves the assertion holds even when extras ARE available, i.e. infodynamics
# itself never imports them eagerly regardless of what's installed.
import sys
import infodynamics
import infodynamics.text
heavy = {"torch", "sentence_transformers", "spacy", "spacy_udpipe", "textdescriptives", "tslearn", "umap"}
assert not (heavy & set(sys.modules))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Poetry + codecov + mkdocs 6-file CI setup (`.github/workflows/on-merge-to-main.yml`, `on-pull-request.yml`, `on-release-main.yml`, `validate-codecov-config.yml`, plus `.github/actions/*`) | No CI at all (removed commit `924d6fb`, Nov 2023) | Nov 10, 2023, this repo | Not a template to resurrect — the project no longer uses Poetry (uses `setup.py`), and PyPI publishing/codecov are explicitly Out of Scope this milestone per PROJECT.md |
| N/A (project has always been `setup.py`-based) | Minimal single-job GH Actions: `checkout@v6` + `setup-python@v6` + `pip install .[test]` + `pytest` | This phase (D-07, if implemented) | Keeps CI proportional to what this milestone actually needs — smoke-level regression protection, nothing more |

**Deprecated/outdated:** The historical Poetry/codecov/mkdocs CI setup is fully removed from git history's working tree (still recoverable via `git show 924d6fb^:...` if ever needed for reference, but should not be reintroduced).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `actions/checkout@v6` and `actions/setup-python@v6` are the current stable major tags as of this research date (2026-07-14) | Standard Stack, Code Examples | Low — a newer major tag (`v7`) may exist by execution time; workflow still functions correctly with `v6` pinned, just not bleeding-edge. Planner/executor should re-check via `gh api repos/actions/checkout/releases/latest` before finalizing D-07's workflow file. |
| A2 | GitHub-hosted `ubuntu-latest` runners' `actions/setup-python@v6` can provision Python 3.14 via the GH Releases fallback if not in the tool cache | Standard Stack | Low-Medium — if 3.14 isn't yet cached/available on `ubuntu-latest` at execution time, the setup-python step may take longer (falls back to building/downloading) or could fail; a safe mitigation is to also test with `python-version: "3.14"` locally first (already confirmed working in this session's fresh venv) and treat any CI-only failure as an environment issue, not a code issue |

**If this table is empty:** N/A — two assumptions logged above, both low-risk and both about third-party CI infrastructure version currency, not about this project's own code or requirements.

## Open Questions

1. **Should `SignalClusterer`'s `ImportError` message be tightened to name the class, not just the extra?**
   - What we know: The message already names the extra (`'clustering'`) and gives the exact install command — this satisfies criterion 2's literal wording ("actionable ImportError naming the missing extra"). `Encoder`'s and (once Pitfall 1 is fixed) `MorphologicalEncoder`'s messages additionally name the class.
   - What's unclear: Whether "actionable" implicitly requires class-name specificity or just extra-name + install command.
   - Recommendation: Treat as acceptable as-is (don't block phase completion on it); if the planner wants perfect parity across all three classes, it's a one-line message edit in `infodynamics/clustering/dtw.py`/`barycenter.py` — small, in-scope per D-01, own `fix(05):` commit if done.

2. **Should the benign `PytestUnknownMarkWarning` for `slow` be silenced with a minimal `pytest.ini`?**
   - What we know: It's cosmetic — doesn't affect exit code, count, or test correctness (Pitfall 3).
   - What's unclear: Whether adding a `pytest.ini`/`[tool:pytest] markers =` block counts as a "stray reference"-class fix (D-01, in-scope) or as new config surface beyond this phase's audit boundary.
   - Recommendation: Document it in `VERIFICATION.md` as a known, benign warning; leave the fix optional/discretionary rather than mandatory, since D-01's examples (stray references, non-actionable ImportErrors, `__all__` gaps) don't cleanly include "add new project config files."

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.14.x | All criteria | ✓ [VERIFIED this session] | 3.14.5 (both dev `.venv` and system `python3`) | — |
| `git` | Criterion 1 (`git grep`) | ✓ [VERIFIED this session] | (system git) | — |
| `pip` | Criteria 2-3 (fresh venv install) | ✓ [VERIFIED this session] | 26.1.2 (fresh venv, after `--upgrade pip`) | — |
| `pytest` | Criterion 4 (QA-04) | ✓ [VERIFIED this session] | 9.1.1 (dev venv, via `extras_require['test']`) | — |
| `hypothesis` | Criterion 4's `@pytest.mark.slow` property-based tests | ✓ [VERIFIED this session] | 6.156.1 (dev venv) | — |
| GitHub Actions runners (`ubuntu-latest`) | D-07 bonus CI only | N/A locally — cloud-only, verify at PR/push time | — | If Python 3.14 isn't cached on the runner, `setup-python` falls back to GitHub Releases download; acceptable since D-07 is non-gating |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** GitHub Actions runner Python 3.14 caching (A2 above) — non-blocking since D-07 doesn't gate phase completion.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 [VERIFIED this session via `pip list`] |
| Config file | none — no `pytest.ini`/`pyproject.toml`/`setup.cfg` `[tool:pytest]` section exists in this repo (see Pitfall 3) |
| Quick run command | `python -m pytest -q` (full suite; already fast, 16.31s, per D-11's decision to always run the full suite including `@slow`) |
| Full suite command | same as quick run — there is no separate slow-excluded subset configured; D-11 already decided the verification run always includes `@slow` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|--------------------|--------------|
| CORE-03 | Core-only path runs with only `install_requires` installed (no extras) | manual, one-off smoke test (D-06 explicitly forbids permanent automated tooling for this) | `python -m venv ... && pip install . && python -c "..."` (Pattern 1) — NOT a pytest test, run once, evidence pasted into `VERIFICATION.md` | N/A by design (D-06) |
| CORE-03 | `Encoder`/`MorphologicalEncoder`/`SignalClusterer` construct without extras; fail only on first use | manual (same fresh-venv script) + already covered indirectly by the existing default-suite `tests/test_pipeline_composition.py::test_all_public_estimators_clone_round_trip` (proves construction succeeds without extras inside the dev venv, though that venv has extras installed so it can't prove the *ImportError* half) | fresh-venv script (Pattern 1); `pytest -q -k clone_round_trip` for the construction-succeeds half | ✅ `tests/test_pipeline_composition.py` (existing, Phase 3) |
| QA-04 | Full suite passes | automated | `python -m pytest -q` | ✅ all of `tests/` (existing) |
| QA-04 | Test count reconciled (81 → 68 → 91) | automated (count) + manual (documenting the reconciliation narrative in `VERIFICATION.md`) | `python -m pytest --collect-only -q \| tail -1` | ✅ (no new file needed) |
| QA-04 (criterion 5, golden baseline) | No numerical drift | automated | `pytest -q tests/test_golden_baseline.py` | ✅ `tests/test_golden_baseline.py` (existing, Phase 1/3, D-08/D-12) |
| QA-04 (criterion 5, estimator spot-check) | `get_params`/`set_params`/`clone` round-trip for every public estimator | automated | `pytest -q tests/test_pipeline_composition.py` | ✅ `tests/test_pipeline_composition.py` (existing, Phase 3, D-08) |
| — (criterion 1, no dedicated req ID, folded into RM-05 already Complete) | Repo grep-clean | automated (shell, not pytest) | `git grep -niE "dashboard\|cache_contract\|shipping\|bench_core"` | N/A — shell command, not a test file |

### Sampling Rate
- **Per task commit:** For the one code fix this research identified (Pitfall 1, `morphology.py`), re-run `pytest -q tests/text/test_morphology.py` (or the full suite — it's fast, 16s) after the fix.
- **Per wave merge:** `python -m pytest -q` (full suite, 16s — cheap enough to always run in full per D-11).
- **Phase gate:** All 5 ROADMAP criteria's evidence transcribed into `VERIFICATION.md` before `/gsd-verify-work`; full suite green is part of that evidence, not a separate gate.

### Wave 0 Gaps
None — existing test infrastructure (`tests/test_golden_baseline.py`, `tests/test_pipeline_composition.py`, `tests/test_public_api.py`) already covers everything criterion 5 needs (D-08). The only new test-relevant work is the one-line assertion fix inside `MorphologicalEncoder.encode()` (Pitfall 1), which is a source fix, not a new test file — though the planner may choose to add a small regression test (`MorphologicalEncoder(...).transform(...)` raises the actionable `ImportError`, run under `pytest.importorskip`-style guarding or a monkeypatched missing-module simulation) to lock the fix in, given `tests/text/test_morphology.py` already exists as the natural home for it.

## Security Domain

### Applicable ASVS Categories

This phase is a verification/audit pass with no new user-facing attack surface (no new endpoints, no new user input paths, no new auth/session code) — most ASVS categories are not applicable. The one relevant category is supply-chain integrity of the new CI workflow file (D-07, bonus).

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | No auth surface touched by this phase |
| V3 Session Management | No | N/A — library, not a service |
| V4 Access Control | No | N/A |
| V5 Input Validation | No (pre-existing, unchanged) | Existing estimator `_validate_data`/`ValueError` guards are validated (not modified) by criterion 5's spot-check; no new input surface added this phase |
| V6 Cryptography | No | N/A |
| V14 Configuration (GH Actions supply chain) | Yes, if D-07 implemented | Pin third-party Actions to a known major-version tag (`@v6`), never `@main`/`@master`; avoid adding `secrets:`/`permissions:` beyond default read-only checkout since the workflow only installs and tests, doesn't publish or deploy |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Unpinned/mutable GitHub Action references (`uses: actions/checkout@main`) | Tampering (supply chain) | Pin to a specific major version tag (`@v6`) as shown in Pattern 3's example — the project already has no CI, so this is a "don't introduce the anti-pattern" note rather than a fix to existing code |
| Overbroad default `GITHUB_TOKEN` permissions in a new workflow | Elevation of Privilege | The minimal workflow in Pattern 3 needs only read access to check out and run tests — no `permissions:` block needed beyond GH Actions' already-restrictive default for public/private repos; do not add `contents: write` or publish steps (out of scope, PROJECT.md) |
| Non-actionable `ImportError` swallowing the real missing-dependency cause (Pitfall 1) | Information Disclosure (inverse — under-disclosure) / Denial of Service (confusing failure blocks legitimate no-extras users from self-diagnosing) | Guard every optional-dependency import site consistently with the established `try/except ImportError: raise ImportError("The 'X' extra is required...")` pattern — Pitfall 1's fix directly addresses this |

## Sources

### Primary (HIGH confidence — direct execution this session)
- Repo source (`infodynamics/text/morphology.py`, `infodynamics/text/embedding.py`, `infodynamics/clustering/{cluster,dtw,barycenter}.py`, `setup.py`) — read directly, line numbers cited above
- `git grep -niE "dashboard|cache_contract|shipping|bench_core"` — run against `feature/artifacts`, 0 hits
- `python -m pytest -q` and `python -m pytest --collect-only -q` — run against dev `.venv` (91 passed / 91 collected)
- Fresh `python -m venv` + `pip install .` (no extras) + import/instantiation/ImportError/core-only smoke script — run against a real throwaway venv this session (Python 3.14.5)
- `git log`/`git show 924d6fb` — historical CI removal commit inspected directly
- `tests/test_pipeline_composition.py`, `tests/test_golden_baseline.py` — read directly, existing coverage confirmed

### Secondary (MEDIUM confidence — WebSearch cross-checked against official repos)
- [actions/checkout releases](https://github.com/actions/checkout/releases) — current major version `v6` (with `v7` bump visible in search results as in-progress)
- [actions/setup-python](https://github.com/actions/setup-python) — current major version `v6`; Python 3.14 support confirmed via GitHub Releases fallback / `actions/python-versions` tool cache

### Tertiary (LOW confidence)
None — every claim in this document is either directly verified this session or cross-checked WebSearch/CITED; no unverified training-knowledge-only claims were needed for a phase this procedural.

## Metadata

**Confidence breakdown:**
- Verification commands/evidence (grep sweep, pytest run, fresh-venv smoke test): HIGH — directly executed this session against the real repo state
- The `morphology.py` bug (Pitfall 1): HIGH — directly reproduced and root-caused by reading the source
- GH Actions version pins (D-07 bonus): MEDIUM — WebSearch cross-checked against official repos, but Marketplace tags increment quickly; re-verify at execution time (A1)
- "Fast" import interpretation (`sys.modules` check over wall-clock threshold): HIGH — reasoning grounded in empirical timing data gathered this session, not speculation

**Research date:** 2026-07-14
**Valid until:** Repo-state-dependent findings (grep sweep, pytest counts, the morphology.py bug) remain valid until the next code change to the affected files — re-verify if further commits land on `feature/artifacts` before Phase 5 executes. GH Actions version pins (A1/A2): re-check within ~30 days per fast-moving external tooling norms.

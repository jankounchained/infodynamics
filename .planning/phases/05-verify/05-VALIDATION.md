---
phase: 5
slug: verify
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-14
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (dev venv, already installed via `extras_require['test']`) |
| **Config file** | none — no `pytest.ini`/`pyproject.toml`/`setup.cfg` `[tool:pytest]` section exists (unregistered `slow` marker warns benignly, see 05-RESEARCH.md Pitfall 3) |
| **Quick run command** | `.venv/bin/python -m pytest --collect-only -q` |
| **Full suite command** | `.venv/bin/python -m pytest -q` (includes `@pytest.mark.slow` per D-11 — no excluded subset) |
| **Estimated runtime** | ~16s full suite (91 tests, verified this session), ~14s collect-only |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest --collect-only -q` (fast import-error catch); for the `morphology.py` fix task specifically, also run `.venv/bin/python -m pytest -q tests/text/test_morphology.py`
- **After every plan wave:** Run `.venv/bin/python -m pytest -q` (full suite — catches numerical drift in the golden-baseline test and any regression from the in-scope fix)
- **Before `/gsd-verify-work`:** Full suite must be green; `VERIFICATION.md` must transcribe evidence for all 5 ROADMAP criteria (grep sweep, fresh no-extras venv script output, full pytest + collect-only counts, golden-baseline/clone spot-check results)
- **Max feedback latency:** ~16s

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-xx | 01 | 1 | — (RM-05 re-verification, no dedicated REQ ID) | — / N/A | Repo-wide grep sweep for `dashboard`\|`cache_contract`\|`shipping`\|`bench_core` returns zero hits | shell/manual | `git grep -niE "dashboard\|cache_contract\|shipping\|bench_core"` (expect exit code 1) | N/A — shell command, not a test file | ⬜ pending |
| 05-01-xx | 01 | 1 | CORE-03 | — / N/A | Fresh no-extras venv: `import infodynamics`/`import infodynamics.text` succeed, no heavy-extra module leaks into `sys.modules`, `Encoder()`/`MorphologicalEncoder()`/`SignalClusterer()` construct cleanly and fail only at first use with an actionable `ImportError` naming the missing extra, core-only `ndarray` path runs end-to-end | manual, one-off | Pattern 1 script from `05-RESEARCH.md` run in a throwaway `python -m venv` (D-06 forbids permanent tooling) | N/A by design (D-06) | ⬜ pending |
| 05-0x-xx | — | — | — (D-01 in-scope fix) | — / N/A | `MorphologicalEncoder.encode()` raises the actionable `ImportError` ("morphology" extra + install command), not a bare `ModuleNotFoundError`, when `textdescriptives` is absent | unit (new/extended test) | `.venv/bin/python -m pytest -q tests/text/test_morphology.py` | ✅ existing file (`tests/text/test_morphology.py`), extended with one new case | ⬜ pending |
| 05-0x-xx | — | — | QA-04 | — / N/A | Full suite passes | automated | `.venv/bin/python -m pytest -q` | ✅ all of `tests/` (existing) | ⬜ pending |
| 05-0x-xx | — | — | QA-04 | — / N/A | Collected test count reconciled: 81 (pre-refactor) → 68 (floor after known `test_manifest.py` removal) → actual (≥68, currently 91) | automated (count) + manual (narrative in `VERIFICATION.md`) | `.venv/bin/python -m pytest --collect-only -q \| tail -1` | ✅ (no new file needed) | ⬜ pending |
| 05-0x-xx | — | — | QA-04 (criterion 5, golden baseline) | — / N/A | No numerical drift vs. Phase 1 golden snapshot | automated | `.venv/bin/python -m pytest -q tests/test_golden_baseline.py` | ✅ existing (Phase 1/3, D-08/D-12) | ⬜ pending |
| 05-0x-xx | — | — | QA-04 (criterion 5, estimator spot-check) | — / N/A | Every public estimator passes `get_params`/`set_params`/`clone` round-trip | automated | `.venv/bin/python -m pytest -q tests/test_pipeline_composition.py` | ✅ existing (Phase 3, D-08) | ⬜ pending |
| 05-0x-xx | — | — | — (D-05 deliverable) | — / N/A | `VERIFICATION.md` exists in `.planning/phases/05-verify/` and transcribes evidence for all 5 criteria | manual-only | N/A — reviewed by inspection during `/gsd-verify-work` | ❌ Wave 0 (file doesn't exist yet — this phase creates it) | ⬜ pending |
| 05-0x-xx | — | — | — (D-07 bonus, non-gating) | V14 (GH Actions supply chain) / pin third-party Actions to a known major tag, no `@main` | `.github/workflows/ci.yml` exists, pins `actions/checkout@v6` + `actions/setup-python@v6`, installs `.[test]`, runs `pytest` | manual (observed via GitHub Actions run) | N/A locally — verify by pushing/opening a PR and checking the Actions tab; optionally `actionlint .github/workflows/ci.yml` if available | ❌ Wave 0 (new file, this phase's bonus deliverable) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Exact Task IDs are assigned by the planner; this table maps requirement → test, not final task numbering. Phase 5 is a verification/audit phase — most rows are one-off manual evidence-gathering (D-06), not new automated tests; only the `morphology.py` fix produces new/extended automated test coverage.*

---

## Wave 0 Requirements

- [ ] No new test framework or fixtures needed — pytest is already installed and configured via `extras_require['test']`
- [ ] No new test *files* needed — the one regression case this phase adds (`MorphologicalEncoder` actionable `ImportError`, Pitfall 1 fix) extends the existing `tests/text/test_morphology.py`
- [ ] `VERIFICATION.md` and (optionally, D-07) `.github/workflows/ci.yml` are new *documentation/CI* artifacts this phase produces, not test infrastructure — see Per-Task Verification Map above

*Existing infrastructure (`tests/test_golden_baseline.py`, `tests/test_pipeline_composition.py`, `tests/test_public_api.py`) already covers everything criterion 5 needs (D-08); no Wave 0 test scaffolding required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|--------------------|
| Repo-wide grep sweep is clean | RM-05 re-verification (no dedicated Phase 5 REQ ID; folded into criterion 1) | Shell command over VCS-tracked files, not a pytest-expressible assertion | `git grep -niE "dashboard\|cache_contract\|shipping\|bench_core"` — expect exit code 1 (no matches). Use `git grep`, not plain `grep -r`, to exclude untracked root clutter and `.venv/` (05-RESEARCH.md Anti-Patterns) |
| Fresh no-extras venv smoke test (import success/speed, `sys.modules` purity, instantiation, actionable `ImportError`s, core-only numeric path) | CORE-03 | D-06 explicitly forbids permanent automated no-extras tooling; this is a one-off manual check run in a throwaway venv outside the repo | Run the Pattern 1 script from `05-RESEARCH.md` verbatim in a fresh `python -m venv` (not the dev `.venv`), paste full output into `VERIFICATION.md`, then discard the venv |
| `VERIFICATION.md` accurately and completely transcribes evidence for all 5 ROADMAP success criteria | CORE-03, QA-04 (D-05, D-10) | Content/evidence-completeness judgment, not mechanically checkable | During `/gsd-verify-work`: confirm each of the 5 numbered criteria has a corresponding pasted command + real output (not paraphrased), and that the 81→68→91 reconciliation narrative (D-10) is present |
| (Bonus, D-07) `.github/workflows/ci.yml` actually runs green on GitHub | — (non-gating) | A workflow file's correctness is proven by GitHub's own Actions runner, not locally mockable without `act`/Docker | Push the branch or open a PR and check the Actions tab; treat any CI-only failure (e.g. Python 3.14 runner availability, 05-RESEARCH.md A2) as non-blocking per D-07 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (or are explicitly documented as manual-only above)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (none needed — existing infra sufficient per D-08)
- [x] No watch-mode flags
- [x] Feedback latency < 30s (~16s full suite)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 01
slug: baseline-removal
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-13
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (installed; `setup.py extras_require['test']` declares `pytest>=6.2.2`) |
| **Config file** | none — no `pytest.ini`/`pyproject.toml` config exists; defaults apply |
| **Quick run command** | `pytest tests/test_golden_baseline.py -x` (new file this phase adds) |
| **Full suite command** | `pytest` (currently 81 tests, expected 68 after `test_manifest.py` removal) |
| **Estimated runtime** | ~30-60s (81→68 tests; collect-only alone takes 5.21s; full run includes real sentence-transformers encoder calls for the golden-baseline capture/comparison) |

---

## Sampling Rate

- **After every task commit:** Run `pytest --collect-only -q` (fast, catches import breakage immediately after each removal step)
- **After every plan wave:** Run full `pytest` + the RM-05 grep sweep (scoped to `infodynamics/`, `tests/`, `setup.py`, `README.md`) + the `.venv/bin/` console-script shim check (`ls .venv/bin/ | grep infodynamics` should return nothing)
- **Before `/gsd-verify-work`:** Full suite must be green (68/68), golden baseline captured and passing, grep clean, zero console-script shims for removed code
- **Max feedback latency:** ~60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 0 | QA-01 | — | Golden-output snapshot matches current pipeline output within `np.allclose` tolerance | unit/regression | `pytest tests/test_golden_baseline.py -x` | ❌ Wave 0 — new file | ⬜ pending |
| TBD | TBD | TBD | RM-04 | — | `pytest --collect-only -q` reports zero collection errors, exactly 68 tests | smoke | `pytest --collect-only -q` | ✅ existing invocation | ⬜ pending |
| TBD | TBD | TBD | RM-05 | T-01-01 | Repo-wide grep for removed symbols returns no hits in scoped paths | smoke (non-pytest) | `grep -rn "dashboard\|shipping\|cache_contract\|bench_core\|build_dashboard_artifacts" infodynamics/ tests/ setup.py README.md` | N/A — shell command | ⬜ pending |
| TBD | TBD | TBD | RM-03 | — | No console-script shim in `.venv/bin/` points at removed code | smoke (non-pytest) | `ls .venv/bin/ \| grep infodynamics` returns nothing (after `pip install -e .` rerun) | N/A — shell command | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Planner assigns real Task IDs/Plan/Wave values when PLAN.md is written; the requirement→test mapping above is fixed by research and should carry through unchanged.*

---

## Wave 0 Requirements

- [ ] `tests/golden/capture_baseline.py` — one-time capture script (QA-01)
- [ ] `tests/golden/baseline_arrays.npz` + `tests/golden/baseline_meta.json` — the checked-in snapshot itself (QA-01)
- [ ] `tests/test_golden_baseline.py` — the reusable pytest comparison test (QA-01, reused by Phases 2-5 per STATE.md)
- Framework install: none — pytest already installed

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

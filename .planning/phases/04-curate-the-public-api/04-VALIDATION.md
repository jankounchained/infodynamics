---
phase: 4
slug: curate-the-public-api
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-14
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 6.2.2+ (already installed, `.venv/bin/pytest`) |
| **Config file** | none — default discovery via `test_*.py` naming in `tests/` |
| **Quick run command** | `.venv/bin/python -m pytest --collect-only -q` |
| **Full suite command** | `.venv/bin/python -m pytest -q` |
| **Estimated runtime** | ~15s (quick collection check); full suite consistent with prior phases |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest --collect-only -q` (fast import-error catch)
- **After every plan wave:** Run `.venv/bin/python -m pytest -q` (full suite — catches any runtime behavior change; none expected this phase, but golden-baseline tests must stay green)
- **Before `/gsd-verify-work`:** Full suite must be green, plus manual read of `CHANGELOG.md` and a manual run of `examples/basic_usage.py`
- **Max feedback latency:** ~15s

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-xx | 01 | 1 | API-03 | — / N/A (no applicable ASVS controls) | `infodynamics.__all__` == exact 8-symbol set, all resolve | unit | `pytest tests/test_public_api.py::test_core_all_matches_expected_symbols -x` | ❌ Wave 0 | ⬜ pending |
| 04-01-xx | 01 | 1 | API-03 | — / N/A | `infodynamics/__init__.py` source contains no `.text` import (D-05) | unit | `pytest tests/test_public_api.py::test_core_init_has_no_text_imports -x` | ❌ Wave 0 | ⬜ pending |
| 04-01-xx | 01 | 1 | API-03 | — / N/A | `infodynamics.text.__all__` == exact 8-symbol set, all resolve | unit | `pytest tests/test_public_api.py::test_text_all_matches_expected_symbols -x` | ❌ Wave 0 | ⬜ pending |
| 04-01-xx | 01 | 1 | API-03 | — / N/A | No import regressions anywhere in the suite (fixes `tests/text/test_morphology.py:10`) | smoke | `pytest --collect-only -q` (expect 0 errors, count >= 88) | ✅ (pytest itself; no new file) | ⬜ pending |
| 04-02-xx | 02 | — | API-04 | — / N/A | `examples/basic_usage.py` runs end-to-end (core-only path + full Pipeline path) without error | smoke | `.venv/bin/python examples/basic_usage.py` | ❌ Wave 0 (file doesn't exist yet — this phase creates it) | ⬜ pending |
| 04-02-xx | 02 | — | API-04 | — / N/A | `CHANGELOG.md` exists and lists old→new import path for every symbol that moved this milestone | manual-only | N/A — reviewed by inspection during `/gsd-verify-work`; no automated content check warranted for prose/table doc content | ❌ (doc, not test) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Exact Task IDs are assigned by the planner; this table maps requirement → test, not final task numbering.*

---

## Wave 0 Requirements

- [ ] `tests/test_public_api.py` — new file, covers API-03 (`__all__` completeness for both `infodynamics` and `infodynamics.text`, plus the zero-`.text`-import assertion for D-05)
- [ ] No framework install needed — pytest already present in the `test` extra
- [ ] No shared fixtures needed — `test_public_api.py` only imports `infodynamics` / `infodynamics.text` directly

*`examples/basic_usage.py` is itself a Wave 0-created deliverable (the API-04 example artifact), not a test file — see Per-Task Verification Map above.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|--------------------|
| `CHANGELOG.md` accurately lists every symbol's old→new import path for this milestone (Phase 2 text/ relocation, Phase 3 Text* wrapper additions, Phase 4 `__all__` curation) | API-04 | Content correctness (did we list every moved symbol, is the mapping accurate) is a documentation-quality judgment, not a mechanically checkable assertion | During `/gsd-verify-work`: read `CHANGELOG.md` and cross-check each entry against `infodynamics/__init__.py`'s current vs. Phase-1-baseline re-exports and `.planning/STATE.md`'s Decisions log |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (`tests/test_public_api.py`)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

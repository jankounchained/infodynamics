---
phase: 2
slug: reorganize-into-core-text-on-ramp
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-14
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (installed; `setup.py` extras_require['test'] pins `pytest>=6.2.2`) |
| **Config file** | none — no `pytest.ini`/`setup.cfg`/`pyproject.toml`/`conftest.py` found anywhere in the repo; pytest uses default rootdir-relative discovery |
| **Quick run command** | `.venv/bin/python -m pytest tests/text/ -q` |
| **Full suite command** | `.venv/bin/python -m pytest -q` |
| **Estimated runtime** | ~15 seconds (72 tests collected today) |

---

## Sampling Rate

- **After every task commit:** Run a targeted `pytest` invocation against the specific file(s) touched by that task (e.g. `pytest tests/text/test_segmentation.py -q` after that move+import-fix).
- **After every plan wave:** Run `.venv/bin/python -m pytest -q` (full suite; cheap enough at 72 tests / ~15s to run every wave).
- **Before `/gsd-verify-work`:** Full suite must be green, plus the structural/grep/smoke checks below.
- **Max feedback latency:** ~15 seconds.

---

## Per-Task Verification Map

Task IDs are TBD until planning assigns them; rows below map each phase requirement to its concrete automated check per `02-RESEARCH.md`'s Validation Architecture. The planner should attach these checks to the task(s) that implement each requirement.

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| TEXT-01 | Modules live under `infodynamics/text/`, tests mirrored under `tests/text/` | structural | `test -f infodynamics/text/segmentation.py infodynamics/text/embedding.py infodynamics/text/morphology.py infodynamics/text/__init__.py tests/text/test_segmentation.py tests/text/test_morphology.py tests/text/__init__.py && test ! -e infodynamics/segmentation.py && test ! -e tests/test_segmentation.py` | ✅ (files exist today at old paths; check inverts post-move) | ⬜ pending |
| TEXT-01 | Test content still passes at new location | unit | `.venv/bin/python -m pytest tests/text/ -q` | ✅ | ⬜ pending |
| TEXT-03 | `import infodynamics` / `import infodynamics.text` succeed with no heavy extras | smoke | fresh no-extras venv: `python -c "import infodynamics; import infodynamics.text; print('OK')"` (see Wave 0 Requirements — venv must be created first) | ❌ — venv does not exist yet | ⬜ pending |
| CORE-01 | No core→text import outside the documented `pipeline.py` exception | grep | `grep -rln "from infodynamics\.text\|import infodynamics\.text" infodynamics/*.py infodynamics/clustering/*.py \| grep -v infodynamics/pipeline.py` — expect empty output | ✅ (grep is the test; no file needed) | ⬜ pending |
| — | Full suite green, no numerical drift | regression | `.venv/bin/python -m pytest -q` — expect 72/72 passing (today's baseline, verified via `pytest --collect-only -q`), including `tests/test_golden_baseline.py`'s 4 comparison functions unchanged | ✅ `tests/test_golden_baseline.py` exists and currently passes | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Throwaway no-extras venv: `python3 -m venv /tmp/id-no-extras && /tmp/id-no-extras/bin/pip install -e . --no-deps && /tmp/id-no-extras/bin/pip install numpy matplotlib scikit-learn syntok typing-extensions` — required to prove TEXT-03 (criterion 2); the working `.venv` has all extras installed and cannot be used for this check. Do not uninstall extras from the working `.venv`.

*No new test framework, fixtures, or config needed — existing pytest + hypothesis + Phase 1's golden-baseline harness fully cover this phase's verification.*

---

## Manual-Only Verifications

*None — all phase behaviors have automated verification (structural checks, grep sweep, pytest, no-extras import smoke test).*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (no-extras venv)
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

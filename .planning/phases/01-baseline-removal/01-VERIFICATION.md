---
phase: 01-baseline-removal
verified: 2026-07-14T11:30:00Z
status: passed
score: 9/9 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 8/9
  gaps_closed:
    - "The golden-baseline pytest test (tests/test_golden_baseline.py) collects and runs — or gracefully skips — using only the documented `test` extra (`pip install -e .[test]`)"
  gaps_remaining: []
  regressions: []
---

# Phase 1: Baseline & Removal Verification Report

**Phase Goal:** A golden-output baseline exists to detect any future numerical drift, and all dashboard/case-study/shipping infrastructure is gone from the repo with no dangling references.
**Verified:** 2026-07-14
**Status:** passed
**Re-verification:** Yes — after gap closure (plan 01-04, commits `ec5c1e3`, `4cca827`)

## Goal Achievement

All 9 truths from the initial verification pass were re-checked from scratch in this session — every command below was independently re-run, not read off SUMMARY.md or the prior VERIFICATION.md.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A checked-in golden-output snapshot exists, captured against pre-refactor HEAD, covering all six target estimators' outputs on fixed inputs | VERIFIED | `tests/golden/baseline_arrays.npz` (87,136 bytes) + `tests/golden/baseline_meta.json` (3,478 bytes) exist. `np.load` re-confirms 27 array keys spanning all six estimators (`a/b/c_novelty/transience/resonance`, `multiscale_*_ssm/scalogram/novelty`, `numeric_wrd_*`, `numeric_scalogram_matrix`, `numeric_foote_*`, `cluster_labels`, `cluster_barycenter_0/1`). `git log` confirms capture commit `f243e94` predates the dashboard-removal commits (`b9c967b`/`33a2fce`/`79b563b` are pre-Phase-1 history; the removal commit `0a9b195` post-dates `f243e94`). |
| 2 | The multiscale snapshot exercises the full default scales (2,3,5,8,13,21) and radii (3,5,8,13,21) with no silent truncation | VERIFIED | Re-read `baseline_meta.json`'s `shapes` block directly: `multiscale_a_scalogram: [6, 48]` (6 = all default scales), `multiscale_a_novelty: [5, 48]` (5 = all default radii); numeric half confirms identically (`numeric_scalogram_matrix: [6, 60]`, `numeric_foote_novelty: [5, 60]`). No truncation. |
| 3 | Re-running the current, unmodified code on the same fixed inputs matches the snapshot within `np.allclose(rtol=1e-5, atol=1e-8)` under a plain `pytest` invocation | VERIFIED | Freshly run: `.venv/bin/pytest -q tests/test_golden_baseline.py` → `4 passed, 1 warning in 12.80s`. All four test functions pass. |
| 4 | `dashboard/`, `infodynamics/cache_contract.py`, `infodynamics/shipping.py`, and `build_dashboard_artifacts.py` no longer exist in the working tree, recoverable via git history | VERIFIED | `test ! -e dashboard`, `test ! -f infodynamics/cache_contract.py`, `test ! -f infodynamics/shipping.py` all succeed; `find . -iname build_dashboard_artifacts.py` (excluding `.git/`) returns nothing. Deletion commit `0a9b195` located via `git log --diff-filter=D`; `git show 0a9b195^:dashboard/app.py` successfully recovers pre-deletion content (confirmed by direct `git show`, not assumed). |
| 5 | `setup.py` has zero `infodynamics-pack`/`-pull`/`-verify`/`-init-project` console-script entries; `pip install -e .` registers no script pointing at removed code | VERIFIED | `grep -n "console_scripts\|entry_points\|infodynamics-pack..." setup.py` → 0 hits (grep exit 1). `ls .venv/bin/ | grep infodynamics` → 0 hits. `infodynamics.egg-info/` exists but contains no `entry_points.txt` file at all (`cat` confirms "No such file or directory") — fully absent, not just empty. |
| 6 | `pytest --collect-only -q` reports zero collection errors after `tests/test_manifest.py` is removed | VERIFIED | Freshly run: `.venv/bin/pytest --collect-only -q` → "72 tests collected in 15.11s", 0 errors (only a pre-existing, unrelated `PytestUnknownMarkWarning` for `@pytest.mark.slow`). |
| 7 | A repo-wide grep for `dashboard`, `shipping`, `cache_contract`, `bench_core`, `build_dashboard_artifacts`, scoped to `infodynamics/`, `tests/`, `setup.py`, `README.md`, returns no hits | VERIFIED | `grep -rn "dashboard\|shipping\|cache_contract\|bench_core\|build_dashboard_artifacts" infodynamics/ tests/ setup.py README.md 2>/dev/null \| grep -v -E ':[0-9]+:\s*#'` → 0 output (exit 1 = no matches). |
| 8 | The full pytest suite passes, confirming removal introduced zero numerical drift into surviving analysis code | VERIFIED (documented, non-blocking exception) | Freshly run: `.venv/bin/pytest -q` → `1 failed, 71 passed, 16 warnings in 15.04s`. The one failure, `tests/test_infodynamics_class.py::test_window_size`, is re-confirmed as pre-existing: `git log --oneline 62b6ff5..HEAD -- infodynamics/time_series.py tests/test_infodynamics_class.py` returns zero commits — neither file has been touched by any Phase 1 commit, including the 01-04 gap-closure commits. Tracked as QA-03 for Phase 3 per REQUIREMENTS.md. Not a regression from the gap-closure plan. |
| 9 | The golden-baseline pytest test collects and runs — or gracefully skips — using only the documented `test` extra (`pip install -e .[test]`) | VERIFIED (gap now closed) | **Static:** `tests/golden/capture_baseline.py` lines 19-23 now contain `import pytest` followed by `pytest.importorskip("sentence_transformers")`, `pytest.importorskip("tslearn")`, `pytest.importorskip("scipy")`, all positioned before the `from infodynamics import (...)` block (confirmed by direct read). `setup.py` line 30: `extras_require['test'] = sorted(set(extras_require['test']) \| set(extras_require['embedding']) \| set(extras_require['clustering']))`; isolated `exec()` of the extras block confirms the resulting `test` set contains `sentence-transformers>=2.2`, `tslearn>=0.6`, `scipy>=1.10`, `pytest>=6.2.2`, `hypothesis>=6.87.0`. **Empirical:** built a `sys.meta_path` finder that raises `ModuleNotFoundError` (the exception a genuinely-missing package actually raises, verified to be the accurate simulation — `pytest.importorskip`'s default `exc_type` in this installed pytest 9.1.1 catches `ModuleNotFoundError`, not a bare `ImportError`) for `sentence_transformers`/`tslearn`/`scipy`, then ran `pytest -q tests/test_golden_baseline.py` under it: result `1 skipped in 0.21s`, exit 0 — a clean skip, no traceback, no collection error. In this dev venv (extras genuinely installed — confirmed via `pip show`), the unmodified command still reports `4 passed`. Both halves of the CR-01 fix are confirmed working, not just present. |

**Score:** 9/9 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/golden/__init__.py` | Empty package marker | VERIFIED | Exists |
| `tests/golden/capture_baseline.py` | Inline fixtures + `compute_outputs()` + serializer + importorskip guards | VERIFIED | 3 `pytest.importorskip(...)` calls confirmed present and correctly ordered (character-offset check: `importorskip` occurs before `from infodynamics`) |
| `tests/golden/baseline_arrays.npz` | Checked-in ndarray snapshot | VERIFIED | 87,136 bytes, 27 array keys |
| `tests/golden/baseline_meta.json` | Checked-in dict/scalar snapshot | VERIFIED | 3,478 bytes, `shapes`/`fixtures`/`cluster`/`numeric` keys present |
| `tests/test_golden_baseline.py` | Permanent `np.allclose` comparison test | VERIFIED | 4 test functions pass; unchanged since prior review (byte-for-byte, per 01-REVIEW.md) |
| `setup.py` | `console_scripts` block removed; `test` extra self-sufficient | VERIFIED | Zero console-script entries; `test` extra unions `embedding` + `clustering` (confirmed via isolated exec) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `tests/test_golden_baseline.py` | `tests/golden/capture_baseline.py` | imports `ARRAYS_PATH`, `META_PATH`, `compute_outputs` | WIRED | Confirmed by direct read |
| `tests/test_golden_baseline.py` | `tests/golden/baseline_arrays.npz` | `np.load(ARRAYS_PATH)` | WIRED | Re-confirmed by successful test run |
| `setup.py` entry_points removal | `.venv/bin/` + `infodynamics.egg-info/entry_points.txt` | force-reinstall propagation | WIRED | No shims; no `entry_points.txt` file exists |
| `tests/golden/capture_baseline.py` importorskip guards | `pytest.importorskip` exc_type semantics | guard skips cleanly under `ModuleNotFoundError` | WIRED (empirically proven) | Simulated bare-extras run → `1 skipped`, exit 0 |
| `setup.py` `extras_require['test']` union | `embedding` + `clustering` extras | set union, no hand-retyped specs | WIRED | Isolated `exec()` confirms specs carried verbatim |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| QA-01 | 01-01, 01-04 | Golden-output baseline captured; no numerical drift; verification gate reliable under documented `test` extra | SATISFIED | Truths 1-3, 8, 9 |
| RM-01 | 01-02 | `dashboard/` removed, preserved in git history | SATISFIED | Truth 4 |
| RM-02 | 01-02 | `cache_contract.py`, `shipping.py`, `build_dashboard_artifacts.py` removed | SATISFIED | Truth 4 |
| RM-03 | 01-02 | Console-script entries removed from `setup.py`; no registered script references deleted code | SATISFIED | Truth 5 |
| RM-04 | 01-02, 01-03 | `tests/test_manifest.py` removed; `pytest --collect-only` zero errors | SATISFIED | Truth 6 |
| RM-05 | 01-03 | Repo-wide grep for removed symbols returns no hits | SATISFIED | Truth 7 |

**Orphan check:** REQUIREMENTS.md maps exactly QA-01, RM-01–RM-05 to Phase 1; all six appear in at least one plan's `requirements:` frontmatter (01-01: QA-01; 01-02: RM-01–04; 01-03: RM-04–05; 01-04: QA-01 gap-closure). No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_golden_baseline.py` | ~22 | Expensive real-model pipeline run as a module-import side effect, no fixture conversion (WR-01) | ⚠️ Warning | Explicitly out of scope for the 01-04 gap-closure plan (`gap_closure_scope` limited to CR-01 only); not a Phase 1 success-criterion blocker. Cost/perf concern, not correctness. |
| `tests/test_golden_baseline.py` | 8-16 | Overly broad `except ImportError` masking unrelated import failures; dead fallback branch (WR-02) | ⚠️ Warning | Confirmed via `grep -c "except ImportError"` = 1, still present. Re-reviewed in 01-REVIEW.md: `pytest.importorskip`'s `Skipped` exception is a `BaseException` subclass, not `ImportError`, so it correctly bypasses this except clause — the CR-01 fix does not interact badly with this pre-existing issue. Out of gap-closure scope. |
| `tests/golden/capture_baseline.py` | ~153 | `Encoder(...)` model reference unpinned to a revision (WR-03) | ⚠️ Warning | Out of gap-closure scope; relevant risk noted for Phase 2-5 reuse of the golden gate, not a Phase 1 blocker. |
| `tests/test_golden_baseline.py` | multiple | Duplicated `rtol=1e-5, atol=1e-8` literals (IN-01) | ℹ️ Info | Cosmetic, out of scope. |
| `tests/golden/capture_baseline.py` | ~169 | `text_sha256` captured but never asserted (IN-02) | ℹ️ Info | Informational-only field, out of scope. |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` debt markers found in any of the three phase-relevant files (`tests/golden/capture_baseline.py`, `setup.py`, `tests/test_golden_baseline.py`) via direct grep — confirmed clean.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite passes (drift check) | `.venv/bin/pytest -q` | "1 failed, 71 passed, 16 warnings in 15.04s" | ✓ PASS (1 failure is pre-existing/tracked, Truth 8) |
| Golden baseline test passes in this environment | `.venv/bin/pytest -q tests/test_golden_baseline.py` | "4 passed, 1 warning in 12.80s" | ✓ PASS |
| Collection count matches corrected arithmetic | `.venv/bin/pytest --collect-only -q` | "72 tests collected", 0 errors | ✓ PASS |
| Scoped grep sweep clean | `grep -rn ... infodynamics/ tests/ setup.py README.md \| grep -v comment` | 0 output | ✓ PASS |
| No console-script shims remain | `ls .venv/bin/ \| grep infodynamics` | no output | ✓ PASS |
| No `entry_points.txt` in egg-info | `cat infodynamics.egg-info/entry_points.txt` | "No such file or directory" | ✓ PASS |
| `test_window_size` failure is pre-existing, not a regression | `git log --oneline 62b6ff5..HEAD -- infodynamics/time_series.py tests/test_infodynamics_class.py` | no commits | ✓ PASS |
| **Golden-baseline test collection skips cleanly under simulated bare `test`-extra env (Truth #9)** | Custom `sys.meta_path` finder raising `ModuleNotFoundError` for `sentence_transformers`/`tslearn`/`scipy`, then `pytest -q tests/test_golden_baseline.py` | "1 skipped in 0.21s", exit 0 | ✓ PASS |
| `setup.py`'s `test` extra is self-sufficient (source-level) | Isolated `exec()` of the `extras_require` block | `test extra OK: ['hypothesis>=6.87.0', 'pytest>=6.2.2', 'scipy>=1.10', 'sentence-transformers>=2.2', 'tslearn>=0.6']` | ✓ PASS |
| No scope creep in gap-closure commits | `git show ec5c1e3`, `git show 4cca827` (full diffs) | `capture_baseline.py`: +5 lines (import pytest + 3 guards) only; `setup.py`: +1 line (union statement) only | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` conventional probes or PLAN/SUMMARY-declared probes found for this phase. SKIPPED (no runnable probe entry points beyond pytest, covered above under Behavioral Spot-Checks).

### Human Verification Required

None. Every truth in this phase is machine-verifiable (file existence, git history, grep, pytest exit codes, isolated exec of the extras block, simulated dependency-absence run); no visual/UX/real-time behavior is in scope for a removal-and-verification phase, and no `<human-check>` blocks were found in any of the phase's PLAN files.

### Gaps Summary

**Re-verification result: no gaps remain.** The single gap from the initial verification pass (Truth #9 / CR-01 — the golden-baseline test's dependency gating under the documented minimal `test` extra) is now closed by gap-closure plan `01-04`, and this closure has been independently re-confirmed in this session both statically (guard placement, extras union, exact diff scope) and empirically (a simulated bare-`test`-extra run produces a clean `1 skipped`, exit 0, rather than the previously-uncaught `ImportError`).

All 8 previously-verified truths were re-run from scratch and show zero regression:
- Full suite: still `1 failed, 71 passed` — same pre-existing `test_window_size` failure, re-confirmed untouched by any Phase 1 commit (including the two 01-04 gap-closure commits).
- Golden-baseline test: still `4 passed` in this dev environment.
- Collection: still `72 tests collected`, 0 errors.
- Removal/grep/console-script truths: all re-confirmed unchanged.

The 01-04 gap-closure diffs are minimal and precisely scoped (5 added lines in `capture_baseline.py`, 1 added line in `setup.py`), matching the plan's stated scope discipline (CR-01 only; WR-01/WR-02/WR-03/IN-01/IN-02 and the QA-03 `test_window_size` fix explicitly deferred, and confirmed still present/deferred in this re-verification).

**Phase 1 goal is achieved: 9/9 truths VERIFIED, all 6 mapped requirements (QA-01, RM-01–RM-05) SATISFIED, no orphaned requirements, no blockers, no human verification needed. Ready to proceed to Phase 2.**

---

_Verified: 2026-07-14_
_Verifier: Claude (gsd-verifier)_

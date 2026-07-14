---
phase: 01-baseline-removal
plan: 01
subsystem: testing
tags: [numpy, pytest, sentence-transformers, tslearn, golden-master, regression-testing]

# Dependency graph
requires: []
provides:
  - "tests/golden/capture_baseline.py — single-source-of-truth fixtures + compute_outputs() + one-time serializer"
  - "tests/golden/baseline_arrays.npz + baseline_meta.json — checked-in golden snapshot of all six target estimators' outputs"
  - "tests/test_golden_baseline.py — permanent pytest regression test reused at the close of every subsequent phase"
affects: [01-02-removal, 01-03-verification, phase-02, phase-03, phase-04, phase-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Golden-output snapshot pattern (tests/golden/): one-time capture script + checked-in .npz/.json snapshot + permanent pytest comparison test"
    - "Single-source-of-truth compute_outputs() function imported by both the capture script's __main__ block and the comparison test, so drift can never come from divergent computation logic"

key-files:
  created:
    - tests/golden/__init__.py
    - tests/golden/capture_baseline.py
    - tests/golden/baseline_arrays.npz
    - tests/golden/baseline_meta.json
    - tests/test_golden_baseline.py
  modified: []

key-decisions:
  - "Used 48-sentence inline fixtures (not the untracked root CSV/UDPipe files) per RESEARCH.md Pitfall 1, sized so the full default scales (2,3,5,8,13,21) and radii (3,5,8,13,21) survive filtering (verified: n_chunks=48 >= 43 needed for radius 21)"
  - "Real Encoder(device='cpu') used for the text half (not FakeEncoder) so this snapshot also validates Phase 2's segmentation+embedding move for zero drift"
  - "Deterministic np.random.default_rng(20260713) seeds a shared rng across the numeric WindowedRollingDistance/Scalogram/FooteNovelty fixture and the 5-series SignalClusterer fixture, continuing draws from one rng instance for full reproducibility"
  - "compute_outputs() run twice inside capture_baseline.py's __main__ block as a determinism self-check before serializing, guarding the future comparison test against encoder/DBA flakiness"

requirements-completed: [QA-01]

coverage:
  - id: D1
    description: "Golden-output baseline capture harness (tests/golden/capture_baseline.py) with inline fixtures and single-source-of-truth compute_outputs()"
    requirement: "QA-01"
    verification:
      - kind: unit
        ref: ".venv/bin/python tests/golden/capture_baseline.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Checked-in golden snapshot (baseline_arrays.npz + baseline_meta.json) covering all six target estimators on fixed inputs, with full default multiscale scales/radii surviving filtering"
    requirement: "QA-01"
    verification:
      - kind: unit
        ref: "tests/golden/baseline_arrays.npz + baseline_meta.json existence/content checks"
        status: pass
    human_judgment: false
  - id: D3
    description: "Permanent pytest comparison test (tests/test_golden_baseline.py) asserting np.allclose(rtol=1e-5, atol=1e-8) against the snapshot, no monkeypatch/FakeEncoder"
    requirement: "QA-01"
    verification:
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_text_signals_match_golden_baseline"
        status: pass
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_multiscale_structure_matches_golden_baseline"
        status: pass
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_pure_numeric_estimators_match_golden_baseline"
        status: pass
      - kind: unit
        ref: "tests/test_golden_baseline.py::test_cluster_labels_and_barycenters_match_golden_baseline"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-07-14
status: complete
---

# Phase 01 Plan 01: Golden-Output Baseline Capture Summary

**Checked-in golden-master snapshot of all six analysis estimators (InfoDynamics, MultiscaleInfoDynamics, WindowedRollingDistance, Scalogram, FooteNovelty, SignalClusterer) captured against pre-refactor HEAD, wired into a permanent np.allclose pytest regression test.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-14T09:40:00+02:00 (approx.)
- **Completed:** 2026-07-14T09:55:47+02:00
- **Tasks:** 2/2
- **Files modified:** 5 (all new)

## Accomplishments
- Built `tests/golden/capture_baseline.py`: three 48-sentence inline text fixtures (FIXTURE_A/B/C) and one deterministic numeric fixture, feeding a single `compute_outputs()` function that exercises all six target estimators with the real (CPU-pinned) `sentence-transformers/all-MiniLM-L6-v2` encoder
- Captured `tests/golden/baseline_arrays.npz` (27 ndarrays) and `tests/golden/baseline_meta.json` (descriptors, fixture hashes, scales/radii, cluster label→barycenter mapping), verified via a two-run determinism self-check and a full-default-scales/radii-survival assertion before serialization
- Wired the snapshot into `tests/test_golden_baseline.py`: 4 pytest test functions (text signals, multiscale structure, pure-numeric estimators, cluster labels/barycenters), all passing against the freshly captured snapshot, with zero monkeypatch/FakeEncoder substitution

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the capture harness and generate the checked-in snapshot** - `f243e94` (test)
2. **Task 2: Wire the snapshot into a permanent pytest comparison test** - `2c5f888` (test)

**Plan metadata:** (this commit, docs)

_Note: Task 2 was flagged `tdd="true"` in the plan; see "TDD Gate Compliance" below for why the standard RED→GREEN split doesn't apply here._

## Files Created/Modified
- `tests/golden/__init__.py` - empty package marker, makes `tests/golden` importable
- `tests/golden/capture_baseline.py` - inline fixtures, `compute_outputs()` single source of truth, one-time serializer with determinism/coverage self-checks
- `tests/golden/baseline_arrays.npz` - checked-in ndarray snapshot (27 arrays)
- `tests/golden/baseline_meta.json` - checked-in descriptors/hashes/scales/radii/cluster-key snapshot
- `tests/test_golden_baseline.py` - permanent pytest comparison test, 4 test functions, np.allclose(rtol=1e-5, atol=1e-8)

## Decisions Made
- Sized fixtures at 48 sentences each (not the RESEARCH-recommended minimum of ~15-20) to comfortably clear the n_chunks >= 43 requirement for the largest default Foote radius (21), confirmed at capture time: all three fixtures produced exactly 48 chunks and preserved all 6 default scales and all 5 default radii.
- Reused one `Encoder` instance across `InfoDynamics` and `MultiscaleInfoDynamics` per fixture (each still re-embeds independently, matching the RESEARCH Pattern 2 example) rather than caching embeddings, to keep the capture script's structure simple and directly traceable to the plan's `<action>` text.
- Used a single continuing `np.random.default_rng(NUMERIC_SEED)` instance across the numeric array, the WindowedRollingDistance/Scalogram/FooteNovelty computation, and the 5-series clustering fixture (per plan's "from the same rng" instruction), rather than separate seeded RNGs per estimator.
- `tests/test_golden_baseline.py` imports `capture_baseline` via `from tests.golden.capture_baseline import ...` with a fallback to inserting `tests/golden` onto `sys.path` and importing `capture_baseline` directly, since this repo has no `tests/__init__.py` (only `tests/golden/__init__.py`) and TESTING.md documents no conftest/package-sharing convention. Both import paths were verified to work with `pytest --collect-only` and `pytest tests/test_golden_baseline.py -x`.

## Deviations from Plan

None - plan executed exactly as written. `averaging_weigts` was not passed explicitly to `WindowedRollingDistance` (left at its default `None`), consistent with the plan's acceptance criterion that the literal string should appear "only if... constructed with that kwarg" — it wasn't needed for the golden baseline's default behavior.

## TDD Gate Compliance

Task 2 was marked `tdd="true"` in the plan. This plan's frontmatter `type` is `execute` (not `tdd`), so the whole-plan RED/GREEN/REFACTOR gate enforcement doesn't apply; only the task-level `tdd_execution` guidance is relevant.

The standard RED (failing test) → GREEN (implementation) cycle does not map cleanly onto this task: the "test" being created (`tests/test_golden_baseline.py`) is itself a golden-master/characterization test whose entire purpose is to assert that the **already-existing, already-correct** pipeline code matches a snapshot captured from that same code moments earlier in Task 1. There is no separate "production" behavior left to implement in Task 2 — writing a version of the test that fails first would require artificially breaking either the snapshot or the assertions, which would violate the "fail-fast rule" guidance to investigate (not manufacture) unexpected passes. The task's own `<action>` text confirms this reading: it instructs to write the test and "confirm it passes against the just-captured snapshot," with no RED step described.

Given this, the task was executed as a single write-run-verify-commit cycle, committed as `test(01-01): ...` (matching the file's nature as test-only content). Git log confirms two `test(...)` commits for this plan (`f243e94`, `2c5f888`) and no `feat(...)` commit — expected, since neither task modified any production/source file.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Golden baseline is captured and committed against pre-refactor HEAD (dashboard/, cache_contract.py, shipping.py all still present at this commit), establishing the clean bisection point Plan 01-02's removal work depends on.
- `tests/test_golden_baseline.py` is discoverable by a plain `pytest` invocation and ready for reuse at the close of Phases 2-5 to prove zero numerical drift.
- Full-suite collection now reports 85 tests (81 pre-existing + 4 new golden tests), 0 collection errors — consistent with RESEARCH.md's expected count before Plan 01-02 removes `tests/test_manifest.py`'s 13 tests.
- No blockers for Plan 01-02 (removal).

---
*Phase: 01-baseline-removal*
*Completed: 2026-07-14*

## Self-Check: PASSED

All created files confirmed present on disk (`tests/golden/__init__.py`, `tests/golden/capture_baseline.py`, `tests/golden/baseline_arrays.npz`, `tests/golden/baseline_meta.json`, `tests/test_golden_baseline.py`, this SUMMARY.md). Both task commits (`f243e94`, `2c5f888`) confirmed present in `git log --oneline --all`.

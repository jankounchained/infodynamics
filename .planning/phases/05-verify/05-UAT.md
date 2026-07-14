---
status: complete
phase: 05-verify
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md]
started: 2026-07-14T18:28:59Z
updated: 2026-07-14T19:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. [05-01/D1] Actionable ImportError for MorphologicalEncoder.encode() without textdescriptives
expected: MorphologicalEncoder.encode() raises an actionable ImportError (naming the 'morphology' extra and pip install command) instead of a bare ModuleNotFoundError when textdescriptives is absent
result: pass
source: automated
coverage_id: D1

### 2. [05-02/D1] Fresh no-extras venv smoke test
expected: import infodynamics / infodynamics.text succeed with zero heavy extras in sys.modules; Encoder/MorphologicalEncoder/SignalClusterer construct cleanly and raise an actionable ImportError only on first use; core-only ndarray path runs end-to-end on install_requires only
result: pass
source: automated
coverage_id: D1

### 3. [05-02/D2] Full pytest suite + golden-baseline reconciliation
expected: Full pytest suite passes (93 tests, incl. new tolerance-policy guard) with golden-baseline tests green on CI (ubuntu-latest), not just locally (macOS); pipeline-composition (clone/get_params/set_params) tests green
result: pass
coverage_id: D2
resolution: |
  Root-caused as float32 cross-platform BLAS precision noise (.planning/debug/golden-baseline-ci-drift.md), NOT a refactor regression. Fixed by 05-04-PLAN.md: split tests/test_golden_baseline.py's tolerance into a tight float64 band (_NUMERIC_ATOL=1e-8, unchanged) for encoder-independent numeric/cluster tests, and a float32-aware band (_TRANSFORMER_ATOL=1e-6) for the two transformer-derived tests, plus a guard test and documenting docstring. Test-only change, zero production code touched.
  Confirmed fixed on CI: gh run 29360296063 (GitHub Actions, ubuntu-latest, feature/artifacts) — status: success. PR #9 checks: test/pass (2m25s).
  Local: .venv/bin/python -m pytest -q -> 93 passed.

### 4. [05-02/D3] Repo-wide grep sweep for removed symbols
expected: Scoped repo-wide grep sweep for dashboard/cache_contract/shipping/bench_core across surviving package code + user docs returns zero hits
result: pass
source: automated
coverage_id: D3

### 5. [05-03/D1] Minimal non-gating CI workflow
expected: .github/workflows/ci.yml — single job on ubuntu-latest, installs .[test], runs pytest -q, third-party Actions pinned to major-version tags, no permissions escalation
result: pass
source: automated
coverage_id: D1

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

- truth: "Golden-baseline tests (test_text_signals_match_golden_baseline, test_multiscale_structure_matches_golden_baseline) pass at rtol=1e-5, atol=1e-8 against the captured pre-refactor baseline"
  status: resolved
  reason: "User reported: CI fails. Two tests give a numerical error compared to golden baseline. test_text_signals_match_golden_baseline and test_multiscale_structure_matches_golden_baseline"
  severity: blocker
  test: 3
  root_cause: "atol=1e-8 is float64-grade precision applied to float32-precision data. Encoder.encode() returns sentence-transformers/PyTorch's default float32 embeddings (never explicitly chosen); everything downstream (cosine-similarity SSMs, resonance/novelty/transience signals) inherits that dtype. The golden baseline was captured only on macOS (Apple Accelerate/vecLib BLAS); CI runs on ubuntu-latest (OpenBLAS/manylinux BLAS). Same code, same math, different platform BLAS backend -> non-associative float32 summation order -> ~1 ULP (1.19e-7) difference, exceeding atol=1e-8 on a handful of elements. Confirmed NOT a v0.5 refactor regression: recomputing on the same macOS machine that holds the baseline reproduces it with 0/27 array mismatches, even with materially newer numpy/scikit-learn/torch/sentence-transformers versions. This is the first time the suite has ever run on Linux/CI (05-03 added CI in this same phase) — the cross-platform gap was structurally guaranteed to surface, independent of code correctness."
  fix_plan: .planning/phases/05-verify/05-04-PLAN.md
  fix_summary: .planning/phases/05-verify/05-04-SUMMARY.md
  verified_on_ci: "gh run 29360296063 (feature/artifacts, ubuntu-latest) — status: success"
  debug_session: .planning/debug/golden-baseline-ci-drift.md

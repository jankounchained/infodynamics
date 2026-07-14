---
status: diagnosed
phase: 05-verify
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md]
started: 2026-07-14T18:28:59Z
updated: 2026-07-14T18:45:00Z
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
expected: Full pytest suite passes (92 tests) with collected count reconciled 81 -> 68 -> 92 against pre-refactor baseline; golden-baseline and pipeline-composition (clone/get_params/set_params) tests green at existing tolerance
result: issue
reported: "CI fails. Two tests give a numerical error compared to golden baseline. test_text_signals_match_golden_baseline and test_multiscale_structure_matches_golden_baseline"
severity: blocker
coverage_id: D2
evidence: |
  gh run 29356333314 (GitHub Actions, ubuntu-latest, Python 3.14.6): 2 failed, 82 passed, 1 skipped.
  FAILED tests/test_golden_baseline.py::test_text_signals_match_golden_baseline - AssertionError: a_resonance has drifted from the golden baseline
  FAILED tests/test_golden_baseline.py::test_multiscale_structure_matches_golden_baseline - AssertionError: multiscale_a_ssm has drifted from the golden baseline
  Diffs are ~1e-7 magnitude (e.g. 0.64189547 vs 0.64189553), well below rtol=1e-5 for most elements individually but np.allclose fails on the full array — 05-01/05-02 SUMMARY.md and 05-VERIFICATION.md both claimed this suite green, evidence was captured locally (macOS) not on CI (ubuntu-latest).

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
passed: 4
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Golden-baseline tests (test_text_signals_match_golden_baseline, test_multiscale_structure_matches_golden_baseline) pass at rtol=1e-5, atol=1e-8 against the captured pre-refactor baseline"
  status: failed
  reason: "User reported: CI fails. Two tests give a numerical error compared to golden baseline. test_text_signals_match_golden_baseline and test_multiscale_structure_matches_golden_baseline"
  severity: blocker
  test: 3
  root_cause: "atol=1e-8 is float64-grade precision applied to float32-precision data. Encoder.encode() returns sentence-transformers/PyTorch's default float32 embeddings (never explicitly chosen); everything downstream (cosine-similarity SSMs, resonance/novelty/transience signals) inherits that dtype. The golden baseline was captured only on macOS (Apple Accelerate/vecLib BLAS); CI runs on ubuntu-latest (OpenBLAS/manylinux BLAS). Same code, same math, different platform BLAS backend -> non-associative float32 summation order -> ~1 ULP (1.19e-7) difference, exceeding atol=1e-8 on a handful of elements. Confirmed NOT a v0.5 refactor regression: recomputing on the same macOS machine that holds the baseline reproduces it with 0/27 array mismatches, even with materially newer numpy/scikit-learn/torch/sentence-transformers versions. This is the first time the suite has ever run on Linux/CI (05-03 added CI in this same phase) — the cross-platform gap was structurally guaranteed to surface, independent of code correctness."
  artifacts:
    - path: "tests/test_golden_baseline.py"
      issue: "rtol=1e-5, atol=1e-8 tolerance is too tight for float32-precision, cross-platform (macOS vs Linux BLAS) data"
    - path: "infodynamics/text/embedding.py"
      issue: "Encoder.encode() inherits float32 dtype from sentence-transformers/PyTorch convert_to_numpy=True — never an explicit, documented choice"
    - path: "infodynamics/scalogram.py"
      issue: "self_similarity_matrix() preserves float32 through the SSM computation, propagating the precision limit"
    - path: "tests/golden/capture_baseline.py"
      issue: "Baseline was captured on macOS only, never validated against a second platform before CI (05-03) was added"
  missing:
    - "Loosen/adjust the golden-baseline tolerance to reflect float32 reality (e.g. raise atol to ~1e-6, or drop the fixed atol in favor of rtol-only comparison for float32-derived arrays)"
    - "Document that byte-exact cross-platform reproducibility of float32 transformer-derived signals is not achievable; scope QA-01 'no numerical drift' as same-platform determinism plus a looser cross-platform tolerance band"
  debug_session: .planning/debug/golden-baseline-ci-drift.md

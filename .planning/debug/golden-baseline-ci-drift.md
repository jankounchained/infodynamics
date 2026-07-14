---
status: diagnosed
trigger: "CI (ubuntu-latest, GitHub Actions) fails two golden-baseline regression tests that pass locally (macOS) — test_text_signals_match_golden_baseline and test_multiscale_structure_matches_golden_baseline in tests/test_golden_baseline.py."
created: 2026-07-14T18:40:54Z
updated: 2026-07-14T18:40:54Z
---

## Current Focus

hypothesis: CONFIRMED — cross-platform float32 BLAS/SIMD non-determinism in the sentence-transformer embedding step, propagated through cosine-similarity-derived signals, exceeds the golden-baseline test's atol=1e-8 (a float64-grade tolerance) on a small number of elements, specifically on macOS (Accelerate/vecLib BLAS) vs ubuntu-latest Linux (OpenBLAS/manylinux wheel BLAS) — not a refactor logic bug.
test: (1) recomputed compute_outputs() on the same macOS machine that holds the checked-in baseline and diffed against baseline_arrays.npz; (2) pulled full CI failure log (gh run view --log-failed) to get exact array values and dtypes; (3) traced dtype provenance (Encoder.encode -> sentence-transformers convert_to_numpy=True -> torch float32 tensors -> cos_sim/self_similarity_matrix preserve float32).
expecting: local recompute == baseline (proves no logic regression); CI diffs magnitude ~= float32 machine epsilon (~1.19e-7) and concentrated in float32-dtype arrays (proves platform/BLAS float32 noise, not an algorithm bug).
next_action: N/A — diagnose-only mode, root cause confirmed and returned to caller for gap-closure planning (loosen tolerance / upcast to float64 downstream / pin BLAS-relevant deps / accept as known platform limitation).

## Symptoms

expected: Both tests pass at rtol=1e-5, atol=1e-8 comparing freshly-computed signals/structure against a checked-in golden-baseline .npz/.npy snapshot captured pre-refactor (per QA-01 requirement: "no numerical drift").
actual: On CI (gh run 29356333314, Python 3.14.6 on ubuntu-latest), both tests fail:
  - test_text_signals_match_golden_baseline: "AssertionError: a_resonance has drifted from the golden baseline" — e.g. current=-0.74750471 vs baseline=-0.74750465 (diff ~6e-8); current=0.64189547 vs baseline=0.64189553.
  - test_multiscale_structure_matches_golden_baseline: "AssertionError: multiscale_a_ssm has drifted from the golden baseline" — e.g. current=0.99999994 vs baseline=1.0000001 (dtype=float32, shape=(48,48)).
  Both tests pass locally on the developer's machine (macOS, per 05-02-SUMMARY.md and 05-VERIFICATION.md, which recorded "92 passed" including these two tests, run pre-refactor and post-refactor).
errors: pytest AssertionError as above (full log pulled via `gh run view 29356333314 --log-failed`, see Evidence).
reproduction: Run `pytest tests/test_golden_baseline.py -v` in this checkout. Compare against how the baseline was captured — check tests/golden/capture_baseline.py for capture methodology and whether numpy/scikit-learn/scipy versions are pinned anywhere (setup.py) vs what CI actually installs (unpinned `pip install .[test]` in .github/workflows/ci.yml resolves to whatever is latest at CI run time, which may differ from what's installed in the local .venv/).
started: Discovered during /gsd-verify-work UAT for phase 05-verify, after PR #9 (branch feature/artifacts) was opened and CI ran for the first time — this is the first time this suite has run on Linux/CI; it was previously only run locally on macOS during Phase 1 baseline capture and Phase 5 verification.

## Eliminated

- hypothesis: "The refactor (v0.5 core extraction) introduced a genuine logic/numerical regression in the analysis pipeline (WindowedRollingDistance, self_similarity_matrix, etc.)."
  evidence: Recomputed `compute_outputs()` from tests/golden/capture_baseline.py on the same macOS machine that holds the checked-in tests/golden/baseline_arrays.npz. Result: 0 mismatches across all 27 checked arrays (rtol=1e-5, atol=1e-8), including a_resonance and multiscale_a_ssm. The current, post-refactor code reproduces the pre-refactor-captured baseline exactly on the same platform. This rules out a code-logic bug introduced by the refactor.
  timestamp: 2026-07-14T18:40Z

- hypothesis: "The test/CI run is simply flaky/non-deterministic (unrelated to platform)."
  evidence: The CI log (gh run 29356333314) shows a clean, complete run (82 passed, 1 skipped, 2 failed) with no other anomalies; the failing values are stable within that run and every diff is uniformly ULP-scale (6e-8 to 1.6e-7), not the kind of large/erratic jump typical of true non-determinism (e.g., dropout, uninitialized memory, thread races). Also ruled out via the determinism self-check built into capture_baseline.py's `__main__` block, which already asserts two independent same-machine compute_outputs() calls agree — this passed when the baseline was originally captured. The uniform ULP-magnitude and float32 dtype signature (see Evidence) is much better explained by platform BLAS/SIMD differences than by generic flakiness.
  timestamp: 2026-07-14T18:40Z

## Evidence

- timestamp: 2026-07-14T18:35Z
  checked: `gh run view 29356333314 --log-failed` (full CI failure log, Python 3.14.6, ubuntu-latest)
  found: a_resonance diffs are all in the 6e-8 to 1.6e-7 range (e.g. -0.74750471 vs -0.74750465; 0.02784276 vs 0.02784288; 0.64189547 vs 0.64189553). multiscale_a_ssm is explicitly printed with `dtype=float32`, shape=(48,48); diagonal self-similarity values that should be exactly 1.0 show as 0.99999994 / 1.0000002 (current) vs 1.0000001 (baseline) — diffs ~1.6e-7. Every single diff across both failures is within one order of magnitude of float32 machine epsilon (~1.19e-7).
  implication: The magnitude and uniformity of the drift is the signature of IEEE-754 float32 rounding noise from non-associative floating-point summation order in vectorized matrix-multiply kernels — not a logic/algorithm bug (which would produce larger, structurally patterned, or asymmetric differences).

- timestamp: 2026-07-14T18:20Z
  checked: infodynamics/text/embedding.py (Encoder.encode) and infodynamics/scalogram.py (self_similarity_matrix) and infodynamics/metrics.py (cos_sim/cosine_similarity)
  found: `Encoder.encode()` calls `model.encode(texts, ..., convert_to_numpy=True, ...)` on a `sentence_transformers.SentenceTransformer` — this returns numpy arrays converted directly from PyTorch tensors, which are float32 by default (PyTorch's default tensor dtype). `self_similarity_matrix()` calls `cos_sim(embeddings, embeddings)` (sklearn's `cosine_similarity`), which preserves float32 input dtype in its output. No explicit float32/float64 casting exists anywhere in this path — no code intentionally chose float32; it is simply inherited from the embedding model's native output dtype.
  implication: multiscale_a_ssm (and the a/b/c SSM/scalogram signals) are float32 purely because the upstream sentence-transformer embeddings are float32, by construction of the embedding library — never explicitly chosen or documented in this codebase.

- timestamp: 2026-07-14T18:38Z
  checked: Local recompute of `compute_outputs()` on this macOS machine (numpy 2.4.6, scikit-learn 1.9.0, scipy 1.18.0, torch 2.12.1, sentence-transformers 5.6.0 — all newer than whatever was installed at original Phase 1 baseline-capture time) vs the checked-in tests/golden/baseline_arrays.npz.
  found: 0 mismatches across all 27 arrays. `a_resonance` dtype is float64 (upcast somewhere downstream of the embeddings, likely via numpy/sklearn internal promotion), but its values still carry the ULP-scale noise floor inherited from the float32 embeddings. `multiscale_a_ssm` dtype is float32, confirming the CI log's reported dtype.
  implication: Even with newer numpy/scikit-learn/torch/sentence-transformers versions than were presumably installed at original capture time, this exact macOS machine reproduces the baseline bit-for-bit. The drift is not explained by "unpinned versions drifting forward over time" on a single platform — it only appears cross-platform (macOS baseline vs Linux CI). This points specifically at platform-dependent BLAS/SIMD backend differences (Apple Accelerate/vecLib on macOS wheels vs OpenBLAS on Linux manylinux wheels, used internally by numpy and by PyTorch's CPU backend for the transformer forward pass), which produce mathematically-equivalent but not bit-identical float32 results due to non-associative floating-point summation order — not from version differences per se.

- timestamp: 2026-07-14T18:15Z
  checked: setup.py extras_require and install_requires
  found: numpy, scikit-learn, scipy, sentence-transformers, torch (transitive via sentence-transformers) are all declared with `>=` minimum-version bounds only — no upper pin, no lockfile (confirmed also in CLAUDE.md: "No requirements.txt or Pipfile"). `.github/workflows/ci.yml` runs `pip install .[test]` with no constraints file.
  implication: CI and local `.venv` can resolve different exact versions over time, which is a secondary contributing risk to reproducibility — but per the evidence above, is NOT the primary driver of the observed drift (same-platform recompute matched exactly despite likely version drift; the failure is specifically macOS-vs-Linux, which persists even at matched version numbers, because the SAME numpy/torch version ships different compiled BLAS backends per platform).

- timestamp: 2026-07-14T18:10Z
  checked: .planning/phases/05-verify/05-UAT.md and .planning/STATE.md
  found: UAT gap explicitly documents: "05-01/05-02 SUMMARY.md and 05-VERIFICATION.md both claimed this suite green, evidence was captured locally (macOS) not on CI (ubuntu-latest)." This is the first time the golden-baseline suite has ever executed on Linux; .github/workflows/ci.yml (05-03) was only added/enabled in this same phase.
  implication: The rtol=1e-5/atol=1e-8 tolerance chosen for the golden-baseline test was never validated against a second platform before being shipped — the cross-platform gap was structurally guaranteed to surface the first time CI ran, regardless of code correctness.

## Resolution

root_cause: |
  The two golden-baseline tests compare float32-precision data (sentence-transformer
  embeddings, and everything derived from them: cosine-similarity self-similarity
  matrices, and the resonance/novelty/transience signals) using a fixed absolute
  tolerance (atol=1e-8) that is appropriate for float64 data but tighter than the
  natural float32 machine-epsilon noise floor (~1.19e-7). The embeddings are produced
  by sentence-transformers' `model.encode(..., convert_to_numpy=True)`, which returns
  PyTorch's default float32 tensor dtype — never explicitly chosen in this codebase,
  simply inherited. When the exact same code runs on a different CPU
  architecture/BLAS backend (macOS Apple Accelerate/vecLib wheels, used to capture
  the golden baseline, vs ubuntu-latest's Linux/manylinux OpenBLAS wheels used by
  CI), the non-associative floating-point summation order inside the transformer's
  matrix-multiply kernels produces mathematically-equivalent but not bit-identical
  float32 results — a difference of roughly one machine epsilon (confirmed: every
  reported diff in the CI log is 6e-8 to 1.6e-7). This ULP-scale, platform-specific
  noise exceeds atol=1e-8 on a handful of elements (particularly near-zero /
  near-one values where the atol term dominates over the rtol term), causing
  np.allclose to fail for the whole array.

  This is NOT a logic bug introduced by the v0.5 refactor: recomputing the exact
  same pipeline on the same macOS machine that captured the baseline reproduces it
  with 0 mismatches across all 27 golden arrays, even with materially newer
  numpy/scikit-learn/torch/sentence-transformers versions than were presumably
  installed at capture time. The drift is specific to running on a *different
  platform* (Linux CI) than the one that captured the baseline (macOS dev machine) —
  it was structurally impossible to catch before CI ran for the first time in this
  phase, because the golden-baseline suite (and its tolerance) had only ever been
  exercised on macOS (per 05-02-SUMMARY.md / 05-VERIFICATION.md and the UAT gap
  note itself).

fix: (not applied — diagnose-only mode, goal: find_root_cause_only)
verification: (not applicable — no fix applied)
files_changed: []

# Milestones

## v0.5 Core Extraction (Shipped: 2026-07-14)

**Phases completed:** 5 phases, 18 plans, 37 tasks

**Key accomplishments:**

- Checked-in golden-master snapshot of all six analysis estimators (InfoDynamics, MultiscaleInfoDynamics, WindowedRollingDistance, Scalogram, FooteNovelty, SignalClusterer) captured against pre-refactor HEAD, wired into a permanent np.allclose pytest regression test.
- Deleted the entire dashboard subsystem (7 files), infodynamics/cache_contract.py, infodynamics/shipping.py, and their exclusive test file via git rm; stripped setup.py's 4 console-script entry points and reconciled the installed environment via force-reinstall.
- Re-ran the full pytest suite and a scoped repo-wide grep sweep to empirically close out Phase 1: zero numerical drift confirmed via the golden-baseline tests, zero dangling references to the five removed symbols, and zero surviving console-script shims — with one pre-existing, already-tracked (QA-03/Phase 3) test failure investigated and correctly left unfixed as out of scope.
- Guarded `tests/golden/capture_baseline.py` with `pytest.importorskip` for sentence_transformers/tslearn/scipy and unioned `setup.py`'s `test` extra with `embedding` + `clustering`, closing CR-01 / Truth #9.
- Pure `git mv` relocation of segmentation.py, embedding.py, and morphology.py into `infodynamics/text/`, with mirrored tests under `tests/text/` and every tracked call site (core `__init__.py`, `pipeline.py`, golden baseline capture, benchmark script) repointed to the new import paths — zero behavior change, golden snapshot byte-identical.
- Ran the complete Phase 2 verification gate against the post-move state from Plan 01 — proved TEXT-03 in a disposable no-extras venv, then confirmed structural inversion, the amended CORE-01 grep sweep, `find_packages()` auto-discovery, and full-suite + golden-snapshot byte-identity — all four ROADMAP Phase 2 success criteria pass, zero source files touched.
- WindowedRollingDistance's QA-02 bugs fixed (averaging_weights rename, verbatim __init__, completed _validate_data) and all three single-scale estimators (WindowedRollingDistance, Scalogram, FooteNovelty) converged onto a uniform array-return transform()/fit_transform() contract with rich state preserved as fitted attributes
- New `TextSegmenter` estimator wrapping `segment()`, plus `Encoder`/`MorphologicalEncoder` converted to Pipeline-legal `BaseEstimator`/`TransformerMixin` classes, with the QA-02 `_MODEL_CACHE` device-mutation bug fixed as its own labeled commit
- InfoDynamics and MultiscaleInfoDynamics rewritten as ndarray-only composite estimators — InfoDynamics returns a (n_chunks, 3) novelty/transience/resonance array with self.signal_, MultiscaleInfoDynamics returns the scalogram matrix with self.result_, and pipeline.py's Phase-2-flagged text-import exception is now fully resolved
- Resolved all QA-03 test debt in `tests/test_infodynamics_class.py` — corrected the wrong `test_window_size` shape assertion, implemented the empty `test_transience_calculation` stub, added the two missing finite-output tests, and fixed a genuine `WindowedRollingDistance` `window_size=0` crash/NaN bug surfaced along the way
- D-04 convenience wrappers restore one-call `fit_transform(text)` ergonomics: `TextInfoDynamics` and `TextMultiscaleInfoDynamics` compose `TextSegmenter -> Encoder -> InfoDynamics`/`MultiscaleInfoDynamics` under `infodynamics.text`, relocating the pre-refactor text-coupled `fit()` bodies verbatim
- Migrated tests/test_pipeline.py, tests/text/test_morphology.py, and tests/golden/capture_baseline.py off the now-ndarray-only core InfoDynamics/MultiscaleInfoDynamics onto TextInfoDynamics/TextMultiscaleInfoDynamics, then re-ran the golden baseline comparison to empirically confirm zero numerical drift across Phase 3's entire decoupling and bug-fix work
- New `tests/test_pipeline_composition.py` — 11-estimator clone/get_params/set_params round-trip parametrized test (API-01) plus three Pipeline composition tests proving the text on-ramp -> analysis chain runs end-to-end, `set_params(step__param=)` propagates, and the literal ROADMAP criterion-4 form works (API-02)
- Explicit `__all__` at both `infodynamics` (8 sklearn-facing symbols) and `infodynamics.text` (8 text-on-ramp symbols), with zero `.text` imports remaining in the core package root — locked by a new `tests/test_public_api.py` contract test.
- New `examples/basic_usage.py` runnably demonstrates both the modality-agnostic core-only path and the full text-on-ramp -> analysis `sklearn.pipeline.Pipeline` composition; new `CHANGELOG.md` gives downstream consumers a mechanical old->new import-path table for every symbol this milestone's reorg moved.
- Wrapped the unguarded `from textdescriptives import extract_df` at the top of `MorphologicalEncoder.encode()` in a try/except that re-raises the file's existing actionable `ImportError` message, and locked the fix with a regression test.
- Ran all 5 ROADMAP Phase-5 success criteria as scripted checks (scoped grep sweep, fresh no-extras venv smoke test, full pytest + collect-only reconciliation, golden-baseline + estimator clone spot-check) and transcribed literal command+output evidence into a checked-in `05-VERIFICATION.md`, closing CORE-03 and QA-04.
- Added a single-job GitHub Actions CI workflow (checkout -> setup-python 3.14 -> pip install .[test] -> pytest -q) with both third-party Actions re-verified and pinned to current major-version tags, and no permissions escalation.

---

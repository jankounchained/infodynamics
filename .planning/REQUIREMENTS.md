# Requirements: infodynamics (core)

**Defined:** 2026-07-13
**Core Value:** One clean, sklearn-compatible library that computes novelty/structure signals from any numeric time series — text as a first-class but separable on-ramp — free of dashboard and case-study baggage.

## v1 Requirements

Requirements for this milestone: extract a lean, modality-agnostic, sklearn-composable core. Each maps to a roadmap phase.

### Removal

- [x] **RM-01**: The `dashboard/` directory is removed from the repository (preserved in git history)
- [x] **RM-02**: `cache_contract.py`, `shipping.py`, and `build_dashboard_artifacts.py` are removed from the package
- [x] **RM-03**: The `infodynamics-pack` / `-pull` / `-verify` / `-init-project` `console_scripts` entries are removed from `setup.py`; no registered console script references deleted code
- [x] **RM-04**: Tests that exclusively cover removed code (`tests/test_manifest.py`) are removed; `pytest --collect-only` reports zero collection errors
- [ ] **RM-05**: A repo-wide search for removed symbols (`dashboard`, `shipping`, `cache_contract`, `bench_core`, `build_dashboard_artifacts`) returns no references in surviving package code, `setup.py`, or docs

### Core (modality-agnostic)

- [ ] **CORE-01**: Core analysis modules (`metrics`, `time_series`, `scalogram`, `clustering/`, `viz`, `util`, `pipeline`) live at the top-level `infodynamics` namespace and import nothing from `infodynamics.text`
- [ ] **CORE-02**: Core estimators (`InfoDynamics`, `MultiscaleInfoDynamics`, `WindowedRollingDistance`, `Scalogram`, `FooteNovelty`, `SignalClusterer`) accept numeric `ndarray` / array-like input and never accept raw text or `Chunk` objects
- [ ] **CORE-03**: A core-only path (numeric array in → signals out) runs with only the required core dependencies installed (no text or heavy extras present)

### Text on-ramp

- [ ] **TEXT-01**: `segmentation`, `embedding`, and `morphology` are relocated under an `infodynamics.text` subpackage
- [ ] **TEXT-02**: `infodynamics.text` exposes a `TextSegmenter` estimator wrapping `segment()`; `Encoder` and `MorphologicalEncoder` are Pipeline-legal (`fit`/`transform`/`get_params`/`set_params`) and emit the `(n_chunks, n_features)` array contract the core consumes
- [ ] **TEXT-03**: All heavy optional dependencies (sentence-transformers, spacy-udpipe, textdescriptives, tslearn) are imported lazily at point-of-use; `import infodynamics` and `import infodynamics.text` succeed without them, failing only at estimator instantiation with an actionable `ImportError`

### Public API & sklearn composability

- [ ] **API-01**: Every public estimator implements `fit` / `transform` / `fit_transform` with working `get_params` / `set_params` and passes an `sklearn.base.clone()` round-trip
- [ ] **API-02**: The text on-ramp → analysis flow composes end-to-end in an `sklearn.pipeline.Pipeline` (`fit_transform` runs; `set_params(step__param=...)` takes effect), verified by `tests/test_pipeline_composition.py`
- [ ] **API-03**: Public API is curated — explicit `__all__` at `infodynamics` and `infodynamics.text`; the core `__init__.py` never imports from `.text`
- [ ] **API-04**: A canonical example demonstrates both core-only (`ndarray` in) use and full `Pipeline` composition; a CHANGELOG/migration note maps old→new import paths for moved symbols

### Quality & correctness

- [x] **QA-01**: A golden-output baseline is captured before any refactor; core numerical outputs (`novelty`/`transience`/`resonance`, SSM, scalogram, Foote novelty, descriptors, cluster labels/barycenters) match it at milestone completion (no numerical drift)
- [ ] **QA-02**: Known bugs are fixed, each as its own labeled commit: `averaging_weigts` → `averaging_weights` rename; `WindowedRollingDistance.__init__` stores params verbatim with validation moved to `fit`; `_MODEL_CACHE` keyed by `device` with no in-place mutation; `_validate_data` completed
- [ ] **QA-03**: Test debt is resolved: empty stubs (`test_transience_calculation`, `test_negative_values_in_input_data`, `test_very_small_numbers`) are implemented; the `test_window_size` assertion is corrected to match actual output
- [ ] **QA-04**: The full `pytest` suite passes against the reorganized package; the collected test count is reconciled against the pre-refactor baseline (no silent coverage loss beyond the known-removed `test_manifest.py`)

## v2 Requirements

Deferred to future milestones. Tracked but not in this roadmap.

### Packaging

- **PKG-01**: Migrate `setup.py` `extras_require` to `pyproject.toml` `[project.optional-dependencies]`
- **PKG-02**: Publish v0.1.0 to PyPI (`pip install infodynamics` from the index)

### API depth

- **APX-01**: Full `sklearn.utils.estimator_checks.check_estimator` conformance for applicable estimators
- **APX-02**: Discrete novelty-event surface (`predict()` / `decision_function()`) alongside continuous scores
- **APX-03**: `__sklearn_tags__` for programmatic capability inspection
- **APX-04**: Additional modality on-ramps (audio, sensor) reusing the modality-agnostic core

## Out of Scope

Explicitly excluded this milestone. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| PyPI publish / packaging modernization | Finish line is "decoupled + reorganized, tests green"; packaging is a later milestone (PROJECT.md) |
| Full `check_estimator` conformance | Assumes tabular `(n_samples, n_features)` + `X,y` semantics this domain doesn't fit; Pipeline-composability is the bar |
| Standing up the dashboard's new repo | Separate future project; here we only *remove* the code |
| Additional modalities (audio/sensor) | Core is *designed* modality-agnostic, but only the text on-ramp is built now |
| Backward-compatible import paths / deprecation shims | Breaking changes accepted pre-1.0; a documented old→new mapping (API-04) suffices |
| Cleanup of untracked root clutter (demo scripts, CSVs, `czech-*.udpipe`, `morphology_demo_output/`) | Untracked and harmless; addressed separately, not this milestone (user decision) |
| Algorithmic/performance rewrites (e.g. O(n²) SSM memory) | Refactor, not rewrite — surviving analysis behavior must not change |

## Traceability

Each requirement maps to exactly one phase.

| Requirement | Phase | Status |
|-------------|-------|--------|
| QA-01 | Phase 1 | Complete |
| RM-01 | Phase 1 | Complete |
| RM-02 | Phase 1 | Complete |
| RM-03 | Phase 1 | Complete |
| RM-04 | Phase 1 | Complete |
| RM-05 | Phase 1 | Pending |
| TEXT-01 | Phase 2 | Pending |
| TEXT-03 | Phase 2 | Pending |
| CORE-01 | Phase 2 | Pending |
| CORE-02 | Phase 3 | Pending |
| TEXT-02 | Phase 3 | Pending |
| API-01 | Phase 3 | Pending |
| API-02 | Phase 3 | Pending |
| QA-02 | Phase 3 | Pending |
| QA-03 | Phase 3 | Pending |
| API-03 | Phase 4 | Pending |
| API-04 | Phase 4 | Pending |
| CORE-03 | Phase 5 | Pending |
| QA-04 | Phase 5 | Pending |

**Coverage:**

- v1 requirements: 19 total
- Mapped to phases: 19 (5 phases)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-13*
*Last updated: 2026-07-13 after roadmap creation*

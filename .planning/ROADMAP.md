# Roadmap: infodynamics (core)

## Overview

This milestone extracts a lean, modality-agnostic, sklearn-composable `infodynamics` core from a bloated monorepo. The sequence is subtractive-before-additive and move-before-refactor, so numerical drift stays bisectable at every step: capture a golden-output baseline and strip dashboard/case-study/shipping infrastructure first (Phase 1), mechanically relocate surviving code into a core + `infodynamics.text` on-ramp split with zero behavior change (Phase 2), then do the one substantive rewrite — decoupling the analysis pipeline from text so it's genuinely `sklearn.pipeline.Pipeline`-composable, fixing the known constructor/dict-return/cache bugs along the way (Phase 3). Once the boundaries are real, curate the public API surface and migration docs (Phase 4), and close with an empirical, no-shortcuts verification pass proving the milestone's definition of done: decoupled, reorganized, tests green, no numerical drift (Phase 5).

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Baseline & Removal** - Capture the golden-output snapshot, then strip the dashboard, cache/shipping infra, and their entry points/tests (completed 2026-07-14)
- [x] **Phase 2: Reorganize Into Core + Text On-Ramp** - Pure `git mv` of segmentation/embedding/morphology under `infodynamics.text`; zero behavior change (completed 2026-07-14)
- [x] **Phase 3: Decouple the Pipeline** - Make the analysis pipeline ndarray-only and every public estimator genuinely `Pipeline`-composable; fix known bugs and test debt (completed 2026-07-14)
- [x] **Phase 4: Curate the Public API** - Explicit curated exports, canonical usage example, old→new import migration notes (completed 2026-07-14)
- [x] **Phase 5: Verify** - Empirically prove the finish line: grep-clean, minimal-venv smoke test, full suite green, no numerical drift (completed 2026-07-14)

## Phase Details

### Phase 1: Baseline & Removal

**Goal**: A golden-output baseline exists to detect any future numerical drift, and all dashboard/case-study/shipping infrastructure is gone from the repo with no dangling references.
**Depends on**: Nothing (first phase)
**Requirements**: QA-01, RM-01, RM-02, RM-03, RM-04, RM-05
**Success Criteria** (what must be TRUE):

  1. A checked-in golden-output snapshot exists, captured against pre-refactor `HEAD`, covering `InfoDynamics`/`MultiscaleInfoDynamics`/`WindowedRollingDistance`/`SignalClusterer`/`Scalogram`/`FooteNovelty` outputs (novelty/transience/resonance, SSM, scalogram, Foote novelty, descriptors, cluster labels/barycenters) on 2-3 fixed inputs
  2. `dashboard/`, `cache_contract.py`, `shipping.py`, and `build_dashboard_artifacts.py` no longer exist in the working tree (recoverable via git history)
  3. `setup.py` has zero `infodynamics-pack`/`-pull`/`-verify`/`-init-project` console-script entries; `pip install -e .` registers no script pointing at removed code
  4. `pytest --collect-only -q` reports zero collection errors after `tests/test_manifest.py` is removed
  5. A repo-wide grep for `dashboard`, `shipping`, `cache_contract`, `bench_core`, `build_dashboard_artifacts` returns no hits in surviving package code, `setup.py`, or docs

**Plans**: 4/4 plans complete
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Capture golden-output baseline (all six estimators) and wire it into a permanent pytest comparison test

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Remove dashboard/, cache_contract.py, shipping.py, test_manifest.py; strip setup.py entry_points; reinstall to clear stale shims

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Verification gate: full suite green at exactly 68 tests, scoped grep sweep clean, console-script shims confirmed gone

**Wave 1 (gap closure)** *(added after verification; independent of Waves 1-3)*

- [x] 01-04-PLAN.md — Close Truth #9 / CR-01: gate golden-baseline test deps with pytest.importorskip and make setup.py's `test` extra self-sufficient (embedding + clustering)

### Phase 2: Reorganize Into Core + Text On-Ramp

**Goal**: Core and text on-ramp code live at their final module locations, split cleanly, with no behavior change and no core→text dependency.
**Depends on**: Phase 1
**Requirements**: TEXT-01, TEXT-03, CORE-01
**Success Criteria** (what must be TRUE):

  1. `segmentation.py`, `embedding.py`, and `morphology.py` live under `infodynamics/text/`, with mirrored tests under `tests/text/`
  2. `python -c "import infodynamics"` and `python -c "import infodynamics.text"` both succeed in a venv with no optional heavy extras (sentence-transformers, spacy-udpipe, textdescriptives, tslearn) installed
  3. A grep for `from .text` / `from infodynamics.text` / `import infodynamics.text` across `infodynamics/*.py` and `infodynamics/clustering/*.py` (excluding `infodynamics/text/`, and — per D-02/D-04 — the documented `infodynamics/pipeline.py` interim exception and the `infodynamics/__init__.py` re-export barrel) returns zero hits. *(Phase 2 amendment: `pipeline.py`'s live text import is a documented interim exception resolved in Phase 3 per D-01/D-02; `__init__.py`'s `infodynamics.text.*` re-exports are legitimate this phase per D-04 and are curated in Phase 4 per API-03. The zero-hit sweep therefore targets the core analysis modules — metrics, time_series, scalogram, viz, util, clustering/* — which is CORE-01's own module list.)*
  4. The full pytest suite is green with only module locations changed; the Phase 1 golden-output snapshot still matches exactly (confirms this is a pure move, no drift)

**Plans**: 2/2 plans complete
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — `git mv` segmentation/embedding/morphology into `infodynamics/text/`, mirror the two tests under `tests/text/`, and fix every tracked import-path call site (pipeline.py imports + docstrings, __init__.py re-exports, capture_baseline.py, benchmark_embedding.py); package stays importable, golden snapshot untouched

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Verification gate: no-extras venv smoke test (TEXT-03), structural inversion checks, CORE-01 grep sweep (amended per D-02/D-04), `find_packages()` spot-check, full pytest at 72, golden byte-identity diff

### Phase 3: Decouple the Pipeline

**Goal**: The text on-ramp and analysis core compose via a real `sklearn.pipeline.Pipeline`; every public estimator satisfies the sklearn constructor/get_params/clone contract; known bugs and test debt are resolved.
**Depends on**: Phase 2
**Requirements**: CORE-02, TEXT-02, API-01, API-02, QA-02, QA-03
**Success Criteria** (what must be TRUE):

  1. `InfoDynamics`/`MultiscaleInfoDynamics.fit`/`transform` in `infodynamics/pipeline.py` accept only numeric `ndarray` input; no internal `segment()`/`Encoder.encode()` calls remain
  2. `TextSegmenter`, `Encoder`, and `MorphologicalEncoder` each independently implement `fit`/`transform`/`get_params`/`set_params` and are individually Pipeline-legal (non-terminal-step capable)
  3. Every public estimator — including `WindowedRollingDistance` (params now stored verbatim in `__init__`, resolution/validation moved to `fit`) — passes a `get_params()`/`set_params()`/`sklearn.base.clone()` round-trip
  4. `sklearn.pipeline.Pipeline([("segment", TextSegmenter()), ("encode", Encoder()), ("analyze", MultiscaleInfoDynamics())]).fit_transform(text)` runs end-to-end, asserted in `tests/test_pipeline_composition.py`
  5. Known bugs are fixed as their own labeled commits (`averaging_weigts`→`averaging_weights` rename; `_MODEL_CACHE` keyed by `device` with no in-place mutation; `_validate_data` completed), and test debt is resolved (`test_transience_calculation`, `test_negative_values_in_input_data`, `test_very_small_numbers` implemented; `test_window_size` assertion corrected) — each bug-fix commit updates the golden-output snapshot deliberately, separate from any pure-move commit

**Plans**: 7/7 plans complete
Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Core single-scale estimators: fix WindowedRollingDistance QA-02 bugs (rename, measure resolution → fit, `_validate_data`), give it + Scalogram + FooteNovelty real `transform()`/array output (D-02/D-03)
- [x] 03-02-PLAN.md — Text estimators: new `TextSegmenter` (D-01), make `Encoder`/`MorphologicalEncoder` Pipeline-legal, fix `_MODEL_CACHE` device bug (QA-02)

**Wave 2** *(blocked on Wave 1)*

- [x] 03-03-PLAN.md — Decouple `InfoDynamics`/`MultiscaleInfoDynamics` to ndarray-only (CORE-02), array output + `signal_`/`result_` (D-03); resolves Phase 2's interim text-import exception
- [x] 03-04-PLAN.md — QA-03 test debt in `test_infodynamics_class.py`: fix `test_window_size` assertion, implement `test_transience_calculation`, add negative/small-number tests

**Wave 3** *(blocked on Waves 1-2)*

- [x] 03-05-PLAN.md — D-04 convenience wrappers `TextInfoDynamics`/`TextMultiscaleInfoDynamics` in new `infodynamics/text/pipeline.py`, re-exported from `infodynamics.text`

**Wave 4** *(blocked on Wave 3)*

- [x] 03-06-PLAN.md — Migrate `test_pipeline.py`/`test_morphology.py` to the wrappers; update golden `capture_baseline.py` and re-verify zero numerical drift (criterion 5)
- [x] 03-07-PLAN.md — New `tests/test_pipeline_composition.py`: clone/get_params/set_params round-trip for every public estimator (API-01) + end-to-end Pipeline composition (API-02, criterion 4)

**Research flag** *(resolved)*: The three open questions were resolved during `/gsd-discuss-phase` and locked as decisions in `03-CONTEXT.md`: (a) transform() semantics → **D-02** (every estimator gets a real standalone `transform(X)` recomputing fresh; `MultiscaleInfoDynamics` is legitimately Pipeline-terminal); (b) dict-vs-array output → **D-03** (array-valued `transform()`/`fit_transform()` with the rich dict preserved on `signal_`/`result_`); (c) convenience wrapper → **D-04** (add `TextInfoDynamics`/`TextMultiscaleInfoDynamics` under `infodynamics.text`). Plus **D-01** (TextSegmenter returns `List[str]`, spans preserved on `chunks_`).

### Phase 4: Curate the Public API

**Goal**: `infodynamics` presents one clean, intentional import surface, and downstream consumers (including the future dashboard repo) have a documented migration path.
**Depends on**: Phase 3
**Requirements**: API-03, API-04
**Success Criteria** (what must be TRUE):

  1. `infodynamics/__init__.py` defines an explicit `__all__` covering only core symbols, with zero `from .text import ...` statements
  2. `infodynamics/text/__init__.py` defines its own explicit `__all__`
  3. A canonical example demonstrates both core-only usage (`ndarray` in, no text on-ramp) and full `Pipeline` composition (text on-ramp → analysis)
  4. A CHANGELOG/migration note lists the old→new import path for every symbol that moved during this milestone

**Plans**: 2/2 plans complete
Plans:
**Wave 1**

- [x] 04-01-PLAN.md — Curate both `__init__.py` export surfaces (explicit `__all__`: 8 core symbols with zero `.text` imports per D-01..D-05; 8 text symbols), migrate the one broken test import, lock it with `tests/test_public_api.py` (API-03)

**Wave 2** *(blocked on Wave 1)*

- [x] 04-02-PLAN.md — Canonical `examples/basic_usage.py` (core-only `ndarray` path + full `Pipeline` composition) and `CHANGELOG.md` old→new import-path migration note (API-04)

### Phase 5: Verify

**Goal**: The milestone's definition of done — decoupled, reorganized, tests green, no numerical drift — is proven empirically, not assumed.
**Depends on**: Phase 4
**Requirements**: CORE-03, QA-04
**Success Criteria** (what must be TRUE):

  1. A repo-wide grep sweep for `dashboard`, `cache_contract`, `shipping`, `bench_core` returns zero hits
  2. In a fresh venv installed with no extras, `import infodynamics` succeeds and is fast, and `import infodynamics.text` succeeds; `Encoder()`/`MorphologicalEncoder()`/`SignalClusterer()` fail only at instantiation with an actionable `ImportError` naming the missing extra
  3. The core-only path (numeric `ndarray` in → signals out) runs end-to-end with only required core dependencies installed — no text or heavy extras present
  4. The full `pytest` suite passes; the collected test count is reconciled against the pre-refactor baseline, with only the known-removed `test_manifest.py` accounting for any drop
  5. The Phase 1 golden-output snapshot still matches for all preserved numerical behavior; every public estimator passes a final `get_params`/`set_params`/`clone` spot-check

**Plans**: 3/3 plans complete
Plans:
**Wave 1**

- [x] 05-01-PLAN.md — Fix the one in-scope bug (guard `MorphologicalEncoder.encode()`'s unguarded `textdescriptives` import → actionable `ImportError`) + regression test; own `fix(05):` commit (D-01/D-03)
- [x] 05-03-PLAN.md — Bonus, non-gating CI workflow `.github/workflows/ci.yml` (single job: `pip install .[test]` + `pytest`, pinned Actions) (D-07)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md — Run all 5 ROADMAP criteria checks (scoped grep sweep, fresh no-extras venv, full pytest + 81→68→91 reconciliation, golden + clone spot-check) and author `05-VERIFICATION.md` evidence transcript (D-05, CORE-03, QA-04)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline & Removal | 4/4 | Complete    | 2026-07-14 |
| 2. Reorganize Into Core + Text On-Ramp | 2/2 | Complete    | 2026-07-14 |
| 3. Decouple the Pipeline | 7/7 | Complete    | 2026-07-14 |
| 4. Curate the Public API | 2/2 | Complete    | 2026-07-14 |
| 5. Verify | 3/3 | Complete    | 2026-07-14 |

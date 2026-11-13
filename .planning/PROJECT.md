# infodynamics (core)

> Snapshot of the v0.5 milestone (2026-07-14, merged as PR #9). Figures below describe that state.

## What This Is

`infodynamics` is a Python library for **novelty detection from complex time series**. It provides sklearn-compatible estimators that compute information dynamics (novelty, transience, resonance), multi-scale structure (scalogram, self-similarity, Foote novelty), and clustering — plus a first-class **text on-ramp** that turns documents into meaningful time series. As of v0.5, it has been extracted from a bloated monorepo into a lean, modality-agnostic core package: the analysis core takes plain numeric arrays, `infodynamics.text` is a separable on-ramp, every public estimator is sklearn `Pipeline`-composable, and the dashboard/cache/shipping infrastructure that used to couple it to a specific case study is gone. The dashboard itself has not yet been stood up as its own repo — that's future work.

## Core Value

One clean, sklearn-compatible library that computes novelty/structure signals from any numeric time series — with text as a first-class but separable on-ramp — free of dashboard and case-study baggage.

## Requirements

### Validated

<!-- Existing, working capabilities inferred from the codebase (.planning/codebase/). These are relied upon and survive the reorg — the refactor must preserve their numerical behavior. -->

- ✓ Single-scale information dynamics (novelty / transience / resonance) via windowed rolling distance — existing
- ✓ Multi-scale structure: scalogram, self-similarity matrix, Foote novelty, structure descriptors — existing
- ✓ DTW-distance clustering with barycenter archetypes — existing
- ✓ Signal / SSM / scalogram / novelty / dendrogram visualization — existing
- ✓ Text segmentation (words / sentences / paragraphs) via syntok — existing
- ✓ HuggingFace sentence-embedding encoder — existing
- ✓ Morphological encoder (UDPipe + textdescriptives) — existing
- ✓ sklearn-style `fit` / `fit_transform` estimators (`BaseEstimator` / `TransformerMixin`, stateless transformers) — existing
- ✓ Golden-output baseline (all six estimators) captured pre-refactor and wired into a permanent drift-detection pytest gate; dashboard/`cache_contract.py`/`shipping.py`/`build_dashboard_artifacts.py` and related artifact-serving code removed from the repo, preserved in git history — Validated in Phase 01: Baseline & Removal
- ✓ Surviving code reorganized into a **modality-agnostic analysis core** + an **`infodynamics.text` on-ramp** subpackage (`segmentation.py`, `embedding.py`, `morphology.py` relocated via `git mv`, all call sites repointed, lazy heavy-dependency guards preserved byte-identically) — Validated in Phase 02: Reorganize Into Core + Text On-Ramp
- ✓ Analysis primitives (`InfoDynamics`, `MultiscaleInfoDynamics`) operate on generic numeric `ndarray` input, independent of text — zero `infodynamics.text` imports or `segment()`/`Encoder.encode()` calls remain in `pipeline.py` — Validated in Phase 03: Decouple the Pipeline
- ✓ Public estimators are **sklearn Pipeline-composable** — every public estimator (`TextSegmenter`, `Encoder`, `MorphologicalEncoder`, `InfoDynamics`, `MultiscaleInfoDynamics`, `WindowedRollingDistance`, `Scalogram`, `FooteNovelty`, …) passes a `get_params`/`set_params`/`clone()` round-trip, and the full text-on-ramp → analysis chain composes end-to-end inside a real `sklearn.pipeline.Pipeline` (`tests/test_pipeline_composition.py`) — Validated in Phase 03: Decouple the Pipeline
- ✓ Clean, intentional **public API** — `infodynamics.__all__` (8 core symbols, zero `.text` imports) and `infodynamics.text.__all__` (8 text symbols) are explicit and locked by `tests/test_public_api.py`; a canonical `examples/basic_usage.py` demonstrates both the core-only `ndarray` path and full `Pipeline` composition; `CHANGELOG.md` maps every moved symbol's old→new import path — Validated in Phase 04: Curate the Public API
- ✓ Test suite passes against the reorganized package, empirically and independently re-verified: repo-wide grep sweep clean; fresh no-extras venv imports core cleanly and every heavy-dependency estimator fails only at first use with an actionable `ImportError`; core-only `ndarray` path runs end-to-end; full `pytest` suite green (92 passed in the development venv, count reconciled 81→68→92 against the pre-refactor baseline; a clean install with only the `test` extra gives 85 passed, 1 skipped, because the morphology tests need their own extra); golden-output baseline and `get_params`/`set_params`/`clone` spot-checks intact — Validated in Phase 05: Verify

### Active

<!-- No committed milestone in progress. Next milestone's requirements are defined by /gsd-new-milestone. -->

*(none — v0.5 fully validated; next milestone's requirements not yet defined)*

### Out of Scope

- PyPI publishing / first release upload — **deferred to a later packaging milestone**; the finish line here is "decoupled + reorganized, tests green"
- `pyproject.toml` migration / packaging modernization — later milestone
- Standing up the dashboard's new repo — separate future project; here we only *remove* its code
- Additional modalities beyond text (audio, sensor, …) — core is *designed* modality-agnostic, but only the text on-ramp is provided this milestone
- Full sklearn `check_estimator` conformance — nice-to-have, not a gate (Pipeline-composability is the bar)
- Backward-compatible import paths — breaking changes accepted (pre-1.0, full reorg)

## Context

- **Brownfield, post-v0.5 extraction.** Mature monorepo prior to this milestone; full pre-refactor analysis in `.planning/codebase/`. The bloat that drove v0.5 was the coupling of a general analysis library with a case-study-specific dashboard + cache/shipping backbone — that coupling is now gone.
- The codebase is **sklearn-compatible by design, not just convention** — every public estimator (`BaseEstimator` / `TransformerMixin`) passes a `get_params`/`set_params`/`clone()` round-trip and composes in a real `sklearn.pipeline.Pipeline`, locked by `tests/test_pipeline_composition.py` and `tests/test_public_api.py`.
- Size at v0.5: 2,128 lines of Python in 16 files under `infodynamics/`, 83 test functions. A clean install with the `test` extra runs 85 passed, 1 skipped.
- **Known, accepted tech debt (from Phase 05 code review, non-blocking):** `.github/workflows/ci.yml` installs `.[test]`, which doesn't include the `morphology` extra, so `tests/text/test_morphology.py` silently skips on a real CI runner instead of running. Doesn't block anything today (CI is an explicit non-gating bonus deliverable), but worth fixing before relying on CI as a real regression gate — see the `05-REVIEW.md` finding WR-01 (phase 05 artifacts, archived with this milestone).
- Repo root still holds case-study clutter (demo scripts, CSVs, `czech-pdt-ud-2.5-191206.udpipe`, `morphology_demo_output/`, etc.) — untracked, harmless, explicitly deferred (user decision, not in scope for v0.5).
- **Two-project split still pending:** this repo is code-ready to become `infodynamics-core`, but the dashboard has not yet been spun out to its own repo — that's future work, not started.

## Constraints

- **Tech stack**: Python 3.14.x — keep stdlib + numpy / scikit-learn / scipy / matplotlib as core; heavy deps (sentence-transformers, spacy-udpipe, textdescriptives, tslearn) stay **optional extras**.
- **Compatibility**: sklearn `Pipeline`-composability is a hard design constraint for public estimators.
- **Architecture**: modality-agnostic analysis core; text tooling is separable under `infodynamics.text`.
- **Refactor, not rewrite**: no change to the numerical output of surviving analysis code.
- **Preservation**: removed code must exist in git history (and/or be copied to the dashboard repo) before deletion.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| This repo becomes `infodynamics-core`; dashboard spins out to its own repo | De-bloat the monorepo into two reusable products | — Pending |
| Two separate repos (not a monorepo/workspace) | Cleanest boundary between library and EDA tool | — Pending |
| cache/shipping/artifact-serving code leaves with the dashboard | It's case-study infra, not general novelty detection | ◐ Removed from this repo, preserved in git history — Phase 01; physical move to a dashboard repo still Pending |
| Modality-agnostic core + `infodynamics.text` on-ramp | Headline product is novelty from complex time series; text is first-class but separable | ✓ Done — Phase 02 |
| Full namespace reorg, breaking imports accepted | Pre-1.0 — a clean, intentional public API is worth the churn | ✓ Done — Phase 04 |
| Finish line = decoupled + reorganized, tests green (no PyPI/packaging) | Packaging & publishing is a separate later milestone | ✓ Done — Phase 05 |
| sklearn Pipeline-composable, not full `check_estimator` | Practical composability is the goal; edge-case conformance isn't worth it now | ✓ Done — Phase 03 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-14 after v0.5 (Core Extraction) milestone completion*

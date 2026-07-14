# infodynamics (core)

## What This Is

`infodynamics` is a Python library for **novelty detection from complex time series**. It provides sklearn-compatible estimators that compute information dynamics (novelty, transience, resonance), multi-scale structure (scalogram, self-similarity, Foote novelty), and clustering — plus a first-class **text on-ramp** that turns documents into meaningful time series. This milestone extracts it from a bloated monorepo into a lean, modality-agnostic core package; the dashboard becomes a separate downstream project.

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

### Active

<!-- This milestone: extract a clean, modality-agnostic core. -->

- [ ] Reorganize surviving code into a **modality-agnostic analysis core** + an **`infodynamics.text` on-ramp** subpackage (segmentation, embedding, morphology)
- [ ] Analysis primitives operate on generic numeric time series / embeddings, independent of text
- [ ] Design a clean, intentional **public API** (curated top-level exports) for the reorganized package
- [ ] Public estimators are **sklearn Pipeline-composable** — chain text on-ramp → analysis, with working `get_params` / `set_params` and `fit` / `transform` / `fit_transform`
- [ ] Test suite passes against the reorganized package (remove or adapt tests tied to deleted code)

### Out of Scope

- PyPI publishing / first release upload — **deferred to a later packaging milestone**; the finish line here is "decoupled + reorganized, tests green"
- `pyproject.toml` migration / packaging modernization — later milestone
- Standing up the dashboard's new repo — separate future project; here we only *remove* its code
- Additional modalities beyond text (audio, sensor, …) — core is *designed* modality-agnostic, but only the text on-ramp is provided this milestone
- Full sklearn `check_estimator` conformance — nice-to-have, not a gate (Pipeline-composability is the bar)
- Backward-compatible import paths — breaking changes accepted (pre-1.0, full reorg)

## Context

- **Brownfield.** Mature monorepo; full analysis in `.planning/codebase/`. The bloat driving this milestone is the coupling of a general analysis library with a case-study-specific dashboard + cache/shipping backbone.
- The codebase **already leans sklearn-compatible** (`BaseEstimator` / `TransformerMixin`, stateless transformers) — this milestone elevates that from convention to a first-class API constraint.
- Repo root holds case-study clutter (demo scripts, CSVs, `czech-pdt-ud-2.5-191206.udpipe`, `morphology_demo_output/`, etc.) — candidates for removal/relocation, not part of the shipped package.
- **Two-project split:** this repo → `infodynamics-core`; the dashboard → its own repo (future work). This milestone plans only the core side.

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
| cache/shipping/artifact-serving code leaves with the dashboard | It's case-study infra, not general novelty detection | — Pending |
| Modality-agnostic core + `infodynamics.text` on-ramp | Headline product is novelty from complex time series; text is first-class but separable | — Pending |
| Full namespace reorg, breaking imports accepted | Pre-1.0 — a clean, intentional public API is worth the churn | — Pending |
| Finish line = decoupled + reorganized, tests green (no PyPI/packaging) | Packaging & publishing is a separate later milestone | — Pending |
| sklearn Pipeline-composable, not full `check_estimator` | Practical composability is the goal; edge-case conformance isn't worth it now | — Pending |

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
*Last updated: 2026-07-14 after Phase 01 (Baseline & Removal) completion*

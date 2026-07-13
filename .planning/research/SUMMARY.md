# Project Research Summary

**Project:** infodynamics (core)
**Domain:** Extraction/reorg of a scientific Python library into a lean, modality-agnostic, sklearn-compatible core (refactor, not greenfield)
**Researched:** 2026-07-13
**Confidence:** HIGH (codebase-grounded; sklearn/packaging conventions verified against official docs)

> Synthesis note: the Stack, Features, and Architecture research completed as parallel subagents; the Pitfalls research subagent wrote its full document then hit a session limit on a follow-up step. This SUMMARY was assembled inline by the orchestrator from all four completed files. All four are consistent — no conflicts to reconcile.

## Executive Summary

`infodynamics` is being carved out of a bloated monorepo into a standalone, publishable-later library for **novelty detection from complex time series**, with text as a first-class but separable on-ramp. Research strongly validates the plan: **every comparable library (ruptures, sktime, stumpy, tslearn, scikit-learn) keeps domain-specific data ingestion out of the algorithm layer, and none ship dashboard/caching/serving infra.** The cross-library convergence confirms both halves of the milestone — the modality-agnostic core + `infodynamics.text` on-ramp split, and the removal of dashboard/`cache_contract`/`shipping`.

The good news: the surviving core modules (`metrics`, `time_series`, `scalogram`, `clustering/`, `viz`, `util`) already operate on numeric arrays — they need **relocation, not rewriting**. The real work concentrates in one place: **decoupling `pipeline.py`.** Today `InfoDynamics`/`MultiscaleInfoDynamics` accept *raw text* and internally segment+encode; they must become ndarray-in/ndarray-out so the text path becomes explicit `sklearn.pipeline.Pipeline` composition.

The main risk the research surfaced is that "sklearn-compatible" is currently **shallower than it looks.** Reading the source, the Pitfalls research found the public estimators mostly implement only `fit`/`fit_transform` (no standalone `transform()`), several `fit_transform`s **return dicts** (which can't chain as non-terminal Pipeline steps), and `WindowedRollingDistance.__init__` **resolves params eagerly** (breaking `get_params`/`clone`). So the "Pipeline-composable" requirement is real engineering, not a formality — and it's exactly the milestone's acceptance bar. Two guardrails dominate mitigation: a **golden-output snapshot** captured before any change (to prove "no numerical drift"), and a **real `Pipeline([...])` + `clone()`/`get_params()` composition test** (to prove composability empirically, not by inheritance).

## Key Findings

### Recommended Stack

The codebase already does the right things and mostly needs **formalizing, not replacing**: lazy `try/except ImportError` guards at point-of-use, capability-scoped `extras_require`, and `BaseEstimator`/`TransformerMixin` transformers. Everything is tagged `[NOW]` (serves this milestone) vs `[LATER]` (packaging-modernization milestone — explicitly deferred).

**Core technologies:**
- scikit-learn ≥1.9.0: `BaseEstimator`/`TransformerMixin`/`Pipeline`/`clone` — the only correct foundation for the sklearn-compat bar (3.14 wheels confirmed)
- numpy ≥2.x / scipy ≥1.16: array + clustering primitives (already satisfied in venv)
- pytest + hypothesis: `hypothesis.extra.numpy.arrays()` for numeric edge-cases; a hand-written `Pipeline` composition test as the real acceptance check
- Heavy deps (sentence-transformers, spacy-udpipe, textdescriptives, tslearn, umap) stay **optional extras**, lazily imported

**Explicitly NOT this milestone:** full `check_estimator` conformance (assumes tabular `(n_samples, n_features)` + `X,y` that this domain doesn't fit), `pyproject.toml` migration, PyPI publish. Use the 6-rule constructor checklist + `clone()`/`get_params()` round-trip instead.

### Expected Features

**Must have (table stakes) — this milestone:**
- Core estimators consume plain numeric arrays, not text (the central refactor)
- `fit`/`transform`/`fit_transform` + working `get_params`/`set_params`/`clone` on every public estimator
- `sklearn.pipeline.Pipeline`-composability (text on-ramp → analysis)
- Curated top-level exports (`__all__` at `infodynamics` and `infodynamics.text`), subpackage-scoped like sktime/tslearn
- Optional heavy deps degrade gracefully (already implemented — preserve)

**Should have (differentiators — protect, don't dilute):**
- The novelty/transience/resonance triad tied to multi-scale structure (scalogram + Foote + SSM) — the headline product; no comparable library frames it this way
- `infodynamics.text` as a swappable on-ramp with two interchangeable encoders (semantic vs morphological) feeding the same core
- `structure_descriptors()` as a compact numeric featurization of dynamics

**Defer (later milestones):** discrete `predict()`/`decision_function()` novelty-event API; `__sklearn_tags__`; additional modality on-ramps (audio/sensor — core is *designed* for it, not built this milestone); packaging/PyPI.

**Anti-features (deliberately removed):** Streamlit dashboard, `cache_contract`/manifest, `shipping`/pack-pull-verify CLI, `infodynamics-init-project` scaffold, hardcoded-schema corpus/CSV loading. All leave with the dashboard.

### Architecture Approach

Two-tier single distribution: a flat modality-agnostic **core** at the top level and one nested **`infodynamics.text/`** on-ramp subpackage. The only type crossing the seam is a numeric `ndarray (n_items, n_features)` — no `Chunk`, no raw string, ever enters a core `fit`/`transform`. Dependency direction is strictly one-way: `infodynamics.text` → core, never the reverse (enforced by a grep/CI check).

**Major components:**
1. **Core** (`metrics`, `time_series`/`WindowedRollingDistance`, `scalogram`/`Scalogram`/`FooteNovelty`/`structure_descriptors`, `clustering/`/`SignalClusterer`, `viz`, `util`, `pipeline` reworked to ndarray-in) — modality-agnostic
2. **`infodynamics.text`** (`segmentation`+`TextSegmenter`, `embedding`/`Encoder`, `morphology`/`MorphologicalEncoder`) — the only modality-specific code, all heavy deps lazy
3. **Curated `__init__.py`** at each level as the public-API contract (core `__init__` never imports `.text`)

### Critical Pitfalls

1. **Silent numerical drift during "pure refactor"** — capture a golden-output snapshot before Phase 1; assert `np.allclose` at every checkpoint; never edit a numeric expected-value in a move commit.
2. **Estimators aren't actually composable** — they lack `transform()` and some return dicts; add real `transform()`, separate the rich dict onto a `*_` attribute, and prove it with a `Pipeline([...])` + `clone()` test.
3. **`__init__` doing work** (`WindowedRollingDistance` resolves `measure` eagerly) — move all validation/resolution to `fit`; store params verbatim.
4. **Heavy dep at import time / core imports `.text`** — keep lazy imports; `__init__` exports core only; grep gate + minimal-venv smoke test.
5. **Dangling imports & stale metadata after removal** — grep the whole repo (incl. `setup.py` console scripts, demo scripts, docs) up front; delete in one commit; `pytest --collect-only` must be clean; watch for silent coverage shrinkage (`test_manifest.py` is expected loss).

## Implications for Roadmap

Research converges on a **5-step extraction sequence** with a test-green checkpoint after each. This maps naturally onto Standard-granularity phases. A **golden-output baseline** is prerequisite work before Phase 1 (capture against current `HEAD`), then re-verified at every checkpoint.

### Phase 1: Remove dashboard + cache/shipping (subtractive, lowest risk, first)
**Rationale:** It's a precondition, not parallel work — `build_dashboard_artifacts.py` touches core internals, re-coupling text/corpus assumptions; nothing in core imports the removed code, so removal should be clean.
**Delivers:** `dashboard/`, `cache_contract.py`, `shipping.py`, `build_dashboard_artifacts.py`, `test_manifest.py`, and their `setup.py` console-script entries removed; root-level case-study clutter relocated/deleted.
**Addresses:** Anti-features removal (FEATURES).
**Avoids:** Pitfalls 3, 5, 8 (dangling imports, stale entry points, collection errors).

### Phase 2: Reorganize into core + `infodynamics.text` (pure move, no behavior change)
**Rationale:** Can't curate or decouple a split that doesn't exist yet; do the mechanical `git mv` first.
**Delivers:** `segmentation.py`/`embedding.py`/`morphology.py` → `infodynamics/text/`; tests mirrored to `tests/text/`; intra-package imports fixed; `import infodynamics` still works.
**Uses:** two-tier namespace (ARCHITECTURE); lazy-import audit (STACK).
**Avoids:** Pitfall 4/9 (circular imports, core→text leakage) via `python -c "import infodynamics"` + grep gate.

### Phase 3: Decouple the pipeline + make estimators genuinely composable (substantive, riskiest — own phase)
**Rationale:** This is where "modality-agnostic core" and "Pipeline-composable" actually become true; the one phase likely needing design discussion during planning.
**Delivers:** `InfoDynamics`/`MultiscaleInfoDynamics` take only ndarray; `TextSegmenter` wrapper; real `transform()` + array (not dict) outputs where chaining is needed; `WindowedRollingDistance.__init__` param-storage fix; `tests/test_pipeline_composition.py` (Pipeline + `get_params`/`set_params`/`clone`).
**Implements:** the numeric-array seam (ARCHITECTURE Pattern 1).
**Avoids:** Pitfalls 1, 2, 3, 6, 7 (composability gaps, dict returns, `__init__` work).

### Phase 4: Curate the public API surface
**Rationale:** Only meaningful once the split is real.
**Delivers:** explicit `__all__` at `infodynamics` and `infodynamics.text`; core `__init__` free of `.text`; one canonical example showing both core-only ndarray use and full Pipeline composition; docs/CHANGELOG old→new import mapping.
**Avoids:** Pitfall 4 (core imports `.text`), API/DX churn.

### Phase 5: Verify (finish line)
**Rationale:** Prove the milestone's definition of done empirically.
**Delivers:** full-repo grep sweep (zero hits for removed symbols); fresh no-extras venv smoke test (`import infodynamics` fast; heavy deps fail only at instantiation); full pytest green; `clone`/`get_params`/`set_params` on every public estimator; golden-output snapshot matches.
**Avoids:** Pitfalls 4, 7 ("looks done but isn't").

### Phase Ordering Rationale
- **Subtractive-before-additive:** remove dead code first so the reorg operates on a smaller, cleaner surface.
- **Move-before-refactor:** pure relocation (Phase 2) is separated from behavior change (Phase 3) so drift is bisectable.
- **Split-before-curate:** the public API (Phase 4) can only be curated once boundaries exist.
- **Two-lane commit hygiene throughout:** pure moves vs intentional bug fixes (typo, cache-key, validation) land as separate, labeled commits; golden-output snapshot updated only for the latter.

### Research Flags
- **Phase 3 (Decouple pipeline):** deepest design work — whether to add an `infodynamics.text.TextInfoDynamics` convenience wrapper vs documented `Pipeline` composition; what `transform(X_new)` semantically means for a novelty signal (may legitimately be Pipeline-terminal). Discuss during planning.
- **Phases 1, 2, 4, 5:** standard, mechanical patterns — light or no per-phase research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | sklearn/sktime/tslearn/ruptures facts fetched from official docs & source; versions match installed venv |
| Features | MEDIUM-HIGH | Cross-library API conventions via web search + official docs; core-vs-on-ramp mapping grounded in this repo (HIGH) |
| Architecture | HIGH | sklearn/packaging conventions cross-verified; build order grounded in codebase dependency graph |
| Pitfalls | HIGH | Grounded in direct source reading with file:line citations (found real composability gaps, `__init__` violation, dict returns) |

**Overall confidence:** HIGH

### Gaps to Address
- **`transform()` semantics per estimator:** whether novelty/scalogram estimators are Pipeline-terminal-by-design or should support `transform(X_new)`. Resolve in Phase 3 planning/discussion, document the decision.
- **Root-level clutter fate:** demo scripts, CSVs, `czech-pdt-ud-2.5-191206.udpipe`, `morphology_demo_output/` are untracked case-study artifacts flagged for removal/relocation but not a hard Active requirement — decide during Phase 1.
- **Pre-existing test debt:** empty stubs (`test_transience_calculation`, etc.) and the wrong-assertion `test_window_size` — triage in Phase 3/5 so "tests green" means "correct," not "hollow."

## Sources

### Primary (HIGH confidence)
- `.planning/codebase/{ARCHITECTURE,STACK,STRUCTURE,CONCERNS,TESTING}.md` — first-party codebase analysis
- `.planning/PROJECT.md` — milestone scope, constraints, key decisions
- Direct source reading (Pitfalls): `time_series.py`, `pipeline.py`, `scalogram.py`, `clustering/cluster.py`, `embedding.py`, `morphology.py`, `__init__.py`, `setup.py`, `tests/test_manifest.py`
- scikit-learn.org — "Developing scikit-learn estimators", `BaseEstimator`/`TransformerMixin`/`Pipeline`/`clone` API
- sktime / tslearn / ruptures `pyproject.toml` fetched from GitHub — extras & dependency-tier patterns

### Secondary (MEDIUM confidence)
- ruptures / sktime / stumpy / tslearn / sklearn public API docs — feature landscape & competitor comparison
- packaging.python.org — namespace/subpackage layout, extras conventions

### Detailed research
- `.planning/research/STACK.md`, `FEATURES.md`, `ARCHITECTURE.md`, `PITFALLS.md`

---
*Research completed: 2026-07-13*
*Ready for roadmap: yes*

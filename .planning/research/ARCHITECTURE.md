# Architecture Research

**Domain:** Modality-agnostic, sklearn-compatible scientific Python library (core + on-ramp split)
**Researched:** 2026-07-13
**Confidence:** HIGH (sklearn/packaging conventions are well-documented and cross-verified against scikit-learn.org, scikit-learn-contrib, and packaging.python.org); the specific mapping onto this codebase is architectural judgment grounded in `.planning/codebase/ARCHITECTURE.md` and `STRUCTURE.md`, not an external fact.

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    infodynamics.text  (on-ramp)                       │
│  ┌───────────────┐   ┌───────────────┐   ┌─────────────────────┐     │
│  │ segmentation  │   │  embedding    │   │    morphology        │     │
│  │ TextSegmenter │   │  Encoder      │   │ MorphologicalEncoder │     │
│  │ str → Chunks  │→  │ Chunks → ndarray│  │ Chunks → ndarray    │     │
│  └───────────────┘   └───────────────┘   └─────────────────────┘     │
│         optional extras: syntok, sentence-transformers,               │
│                            spacy-udpipe, textdescriptives              │
└───────────────────────────────┬────────────────────────────────────────┘
                                 │ ndarray (n_items, n_features)
                                 │  ← the ONLY contract crossing the seam
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    infodynamics  (core, modality-agnostic)            │
│  ┌───────────┐  ┌───────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ metrics   │  │time_series│  │ scalogram  │  │   clustering/     │  │
│  │ cosine/JS │  │ Windowed  │  │ SSM, Foote │  │ dtw, barycenter,  │  │
│  │ /KL div.  │  │ Rolling   │  │ novelty,   │  │ SignalClusterer   │  │
│  │           │  │ Distance  │  │ descriptors│  │ (optional: tslearn)│ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬──────┘  └────────┬──────────┘  │
│        └──────────────┴──────┬───────┴──────────────────┘             │
│                               ▼                                        │
│                  ┌─────────────────────────┐                           │
│                  │  pipeline.py             │                           │
│                  │ InfoDynamics /            │                           │
│                  │ MultiscaleInfoDynamics    │                           │
│                  │ (ndarray in → signals out)│                          │
│                  └─────────────────────────┘                           │
│  ┌────────────────────────┐                                            │
│  │ viz.py, util.py         │  required deps only: numpy, scikit-learn,  │
│  │ (plain functions,       │  scipy, matplotlib                        │
│  │  not estimators)        │                                           │
│  └────────────────────────┘                                            │
└──────────────────────────────────────────────────────────────────────┘

Dependency direction:  infodynamics.text  ──depends on──▶  infodynamics
                        (never the reverse — core has zero knowledge
                         that a `text` package exists)
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|-------------------------|
| `infodynamics.metrics` | Pure numeric distance/similarity functions | Stateless functions, no sklearn class needed |
| `infodynamics.time_series` | Single-scale novelty/transience/resonance from a numeric sequence | `BaseEstimator` + `TransformerMixin`, `fit`/`transform` on `ndarray` |
| `infodynamics.scalogram` | Multi-scale structure: SSM, scalogram, Foote novelty, descriptors | Mix of estimator class (`Scalogram`, `FooteNovelty`) + pure functions (`self_similarity_matrix`, `structure_descriptors`) |
| `infodynamics.clustering` | DTW-distance clustering + barycenter archetypes over numeric sequences | Estimator class (`SignalClusterer`) wrapping `dtw.py`/`barycenter.py` helpers; heavy dep (`tslearn`) imported lazily inside functions, not at module top |
| `infodynamics.pipeline` | Orchestrate metrics/time_series/scalogram/clustering into end-to-end analysis estimators | `InfoDynamics`, `MultiscaleInfoDynamics` — **must** take `ndarray` in `fit`/`transform`, never raw text |
| `infodynamics.viz` | Render numeric arrays as matplotlib figures | Plain functions taking arrays + optional `ax`, not estimators |
| `infodynamics.util` | Generic numeric helpers (e.g. `znorm_rows`) | Plain functions |
| `infodynamics.text.segmentation` | Split raw text into `Chunk`s | Function core (`segment()`) + thin estimator wrapper (`TextSegmenter`) for Pipeline use |
| `infodynamics.text.embedding` | Text chunks → dense semantic vectors | Estimator class (`Encoder`), lazy import of `sentence-transformers` |
| `infodynamics.text.morphology` | Text chunks → morphological/syntactic feature vectors | Estimator class (`MorphologicalEncoder`), lazy import of `spacy-udpipe`/`textdescriptives` |

## Recommended Project Structure

```
infodynamics/
├── __init__.py              # curated public API: InfoDynamics, MultiscaleInfoDynamics,
│                             # WindowedRollingDistance, Scalogram, FooteNovelty,
│                             # self_similarity_matrix, structure_descriptors,
│                             # SignalClusterer, metrics.*, viz.*, util.*
│                             # — explicit __all__, no `from .text import *`
├── metrics.py                # cosine / JS-divergence / KL-divergence (pure numeric)
├── time_series.py             # WindowedRollingDistance
├── scalogram.py                # Scalogram, FooteNovelty, self_similarity_matrix, structure_descriptors
├── pipeline.py                  # InfoDynamics, MultiscaleInfoDynamics — ndarray-only contract
├── viz.py                        # plot_overlay, plot_ssm, plot_scalogram, plot_multiscale_novelty, plot_dendrogram
├── util.py                        # znorm_rows, generic numeric helpers
├── clustering/
│   ├── __init__.py
│   ├── dtw.py                      # DTW distance (tslearn, lazy import)
│   ├── barycenter.py                # DBA / soft-DTW barycenter (tslearn, lazy import)
│   └── cluster.py                    # SignalClusterer
└── text/                               # on-ramp subpackage — the ONLY modality-specific code
    ├── __init__.py                      # curated: TextSegmenter (or segment + Chunk), Encoder, MorphologicalEncoder
    ├── segmentation.py                    # Chunk dataclass, segment(), strip_markdown(), TextSegmenter estimator wrapper
    ├── embedding.py                        # Encoder (sentence-transformers, lazy import)
    └── morphology.py                        # MorphologicalEncoder (spacy-udpipe + textdescriptives, lazy import)

tests/
├── test_metrics.py
├── test_time_series.py
├── test_scalogram.py
├── test_pipeline.py           # core: ndarray-in/ndarray-out, get_params/set_params/clone
├── test_viz.py
├── test_clustering.py
├── test_pipeline_composition.py   # NEW: sklearn.pipeline.Pipeline([text on-ramp → core]) end-to-end
└── text/
    ├── test_segmentation.py
    ├── test_embedding.py
    └── test_morphology.py

setup.py / pyproject.toml
  [extras]
  clustering = ["tslearn"]                                   # core, optional
  text-embedding = ["sentence-transformers", "syntok"]        # on-ramp, optional
  text-morphology = ["spacy-udpipe", "textdescriptives", "syntok"]  # on-ramp, optional
  # matplotlib stays a REQUIRED core dep per project constraints — not an extra
```

### Structure Rationale

- **Flat core, one nested `text/` on-ramp:** the core modules (`metrics`, `time_series`, `scalogram`, `clustering/`, `pipeline`, `viz`, `util`) already operate on numeric arrays today (per `.planning/codebase/ARCHITECTURE.md`, the "Signal Analysis Layer") — they need no code changes to become modality-agnostic, only relocation is required for `segmentation.py`/`embedding.py`/`morphology.py`. Everything that consumes or produces raw text lives under `text/`; everything that consumes or produces only `ndarray`/scalars/dict-of-numerics lives at the top level. This is a two-tier namespace, not a namespace-package split across distributions — matches the PROJECT.md framing of "core + `infodynamics.text` on-ramp **subpackage**" (single installable distribution), not a separate PyPI package. Splitting into truly separate distributions is explicitly deferred (packaging modernization is out of scope this milestone).
- **`clustering/` stays under core, not `text/`:** DTW clustering operates on arbitrary multivariate time series (embeddings, morphological features, or any numeric signal) — it has nothing to do with text and must not be coupled to it, even though it currently has its own heavy optional dependency (`tslearn`). Optional-dependency status and namespace placement are orthogonal decisions.
- **Estimator classes over module-level functions where Pipeline composition is needed; plain functions elsewhere:** `viz.py` and `util.py` are consumed directly by user code / other core modules, not chained in a `Pipeline` — keep them as plain functions. Anything that needs to sit in a `Pipeline` step (segmentation, encoding, analysis) needs `fit`/`transform`/`get_params`/`set_params`, so it needs a `BaseEstimator`/`TransformerMixin` class, even if it wraps a pre-existing pure function (`segment()` → `TextSegmenter`).
- **Mirrored `tests/text/` directory:** keeps on-ramp tests (which require optional heavy deps to run fully) separable from core tests (which should run with only `numpy`/`scikit-learn`/`scipy`/`matplotlib` installed) — makes it trivial to run `pytest tests/ --ignore=tests/text` in a minimal-deps CI lane if ever desired.

## Architectural Patterns

### Pattern 1: Numeric-array seam between on-ramp and core

**What:** The only thing that crosses from `infodynamics.text` into `infodynamics` core is an `ndarray` of shape `(n_items, n_features)` (or a 1-D numeric sequence). No `Chunk`, no raw string, no text-specific type ever appears in a core module's `fit`/`transform` signature.

**When to use:** Always, at the on-ramp/core boundary. This is what makes `infodynamics.pipeline.MultiscaleInfoDynamics` reusable for embeddings, morphological features, or any future modality (audio, sensor) without modification — it is the mechanism that satisfies "modality-agnostic core."

**Trade-offs:** Requires splitting today's `InfoDynamics`/`MultiscaleInfoDynamics`, which currently accept a raw text string and internally call `segment()` + `Encoder.encode()` before analysis (per current data flow in `.planning/codebase/ARCHITECTURE.md`). This is a breaking API change — explicitly accepted in PROJECT.md ("breaking imports accepted").

**Example:**
```python
from sklearn.pipeline import Pipeline
from infodynamics.text import TextSegmenter, Encoder
from infodynamics import MultiscaleInfoDynamics

pipe = Pipeline([
    ("segment", TextSegmenter(level="sentence")),
    ("encode", Encoder(model_name="sentence-transformers/all-MiniLM-L6-v2")),
    ("analyze", MultiscaleInfoDynamics(scales=(2, 3, 5, 8, 13, 21))),
])
result = pipe.fit_transform(raw_text_string)
# analyze.fit/transform only ever sees an (n_sentences, n_dims) ndarray
```

### Pattern 2: Function core, estimator shell

**What:** Keep the actual numeric/text logic as a plain, independently-testable function (`segment()`, `self_similarity_matrix()`, `structure_descriptors()`); wrap it in a thin `BaseEstimator`/`TransformerMixin` class only where Pipeline composition is required. This mirrors scikit-learn's own convention (e.g. `sklearn.preprocessing.scale()` function alongside `StandardScaler` class).

**When to use:** Any module where you want both (a) a simple function-call API for notebook/script use and (b) Pipeline compatibility. Already the pattern in this codebase for `scalogram.py` (`Scalogram` class wraps scale-stacking logic; `self_similarity_matrix`/`structure_descriptors` remain plain functions) — extend it deliberately to `segmentation.py`.

**Trade-offs:** Slight duplication (function + thin wrapper class), but keeps unit tests for the function decoupled from sklearn's estimator contract, and keeps the function usable outside a Pipeline context.

**Example:**
```python
def segment(text: str, level: str = "sentence") -> list[Chunk]:
    ...  # pure function, already exists

class TextSegmenter(BaseEstimator, TransformerMixin):
    def __init__(self, level: str = "sentence"):
        self.level = level  # __init__ only stores params — no validation/computation here

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return segment(X, level=self.level)
```

### Pattern 3: Curated `__init__.py` as the only public-API surface

**What:** Each package level (`infodynamics/__init__.py`, `infodynamics/text/__init__.py`) explicitly imports and re-exports (with `__all__`) only the classes/functions meant for external use. Internal modules (`scalogram.py`, `embedding.py`, etc.) remain importable directly for advanced use, but the curated `__init__.py` is the documented contract.

**When to use:** Always, for a library meant to be depended on by another project (the dashboard, and any future consumer) — prevents accidental coupling to internals and gives a clean place to enforce the "on-ramp depends on core, never the reverse" rule (core `__init__.py` must never import anything from `.text`).

**Trade-offs:** Requires discipline to keep `__all__` in sync as modules evolve; worth it given this milestone's explicit goal of "a clean, intentional public API."

## Data Flow

### Request Flow (single document, in-process)

```
raw text string
    ↓  infodynamics.text.TextSegmenter.transform
list[Chunk]
    ↓  infodynamics.text.Encoder.transform  (or MorphologicalEncoder.transform)
ndarray (n_chunks, n_features)          ← SEAM: last text-aware step
    ↓  infodynamics.pipeline.MultiscaleInfoDynamics.transform
    │     ├─ infodynamics.scalogram.self_similarity_matrix → SSM (n, n)
    │     ├─ infodynamics.scalogram.Scalogram.fit_transform → (n_scales, n)
    │     ├─ infodynamics.scalogram.FooteNovelty.fit_transform → (n_radii, n)
    │     └─ infodynamics.scalogram.structure_descriptors → dict[str, float]
dict of numeric signals
    ↓  infodynamics.viz.plot_* (optional)
matplotlib Figure
```

### State Management

- No global state in core or on-ramp modules beyond the existing process-level model caches (`text/embedding.py:_MODEL_CACHE`, `text/morphology.py:_PIPELINE_CACHE`) — these are a text-on-ramp concern only and must not leak into core.
- All core and on-ramp estimators remain stateless-except-for-`fit`-learned-attributes transformers (`fit(X)` populates `*_`-suffixed attributes; `transform(X)` is pure given those).

### Key Data Flows

1. **Text → signal (the on-ramp → core seam):** exactly one type crosses the boundary — a numeric `ndarray`. This is the load-bearing invariant for modality-agnosticism; any future modality (audio, sensor) on-ramp must terminate at the same contract.
2. **Core-only reuse (no text at all):** a caller with pre-computed embeddings/features from anywhere (not just `infodynamics.text`) can call `MultiscaleInfoDynamics.fit_transform(ndarray)` directly — this is the proof that decoupling worked, and should be the primary "core only" example in docs/tests.

## Scaling Considerations

Not a distributed-systems scaling question here — the relevant "scale" axis is **dependency weight and import cost**, not request volume.

| Concern | Minimal install (`pip install infodynamics`) | With `[clustering]` | With `[text-embedding]`/`[text-morphology]` |
|---------|-----------------------------------------------|----------------------|-----------------------------------------------|
| Import cost | `numpy`, `scikit-learn`, `scipy`, `matplotlib` only — `import infodynamics` must succeed and be fast | adds `tslearn` only when `SignalClusterer`/`dtw`/`barycenter` is actually used (lazy import inside functions) | adds `sentence-transformers` / `spacy-udpipe` + `textdescriptives` only when `Encoder`/`MorphologicalEncoder` is instantiated |
| Failure mode if extra missing | N/A — core always works | `ImportError` with install instructions, raised at `SignalClusterer()` construction or first DTW call, not at `import infodynamics.clustering` | same pattern, raised at `Encoder()`/`MorphologicalEncoder()` construction, not at `import infodynamics.text` |

### Scaling Priorities

1. **First risk:** `import infodynamics` accidentally pulling in a heavy optional dependency at module top-level (e.g. `import tslearn` at the top of `clustering/dtw.py`, or `import sentence_transformers` at the top of `text/embedding.py`). Verify with a smoke test in a venv that has only the required core deps installed.
2. **Second risk:** `infodynamics/__init__.py` importing `infodynamics.text` (even indirectly) — this would force core users to have text extras installed just to `import infodynamics`. Verify with the same minimal-deps smoke test plus a grep-based check (see Anti-Patterns).

## Anti-Patterns

### Anti-Pattern 1: Core estimator that accepts raw text

**What people do:** Leave `InfoDynamics`/`MultiscaleInfoDynamics.fit()` accepting a raw text string and calling `segment()`/`Encoder.encode()` internally (today's behavior), because it's convenient for the single "text → signal" use case and avoids touching working code.

**Why it's wrong:** It re-couples the "modality-agnostic core" to text, defeating the entire point of the reorg — it also breaks Pipeline composability, since a `Pipeline` step's `transform` output must match the next step's `fit`/`transform` input, and text-in/signal-out is not a composable unit with a text-in/chunks-out segmenter feeding it.

**Do this instead:** `InfoDynamics`/`MultiscaleInfoDynamics` take only numeric arrays. Provide the text convenience as **composition**, not internal coupling — a documented `sklearn.pipeline.Pipeline([...])` recipe, or (if truly wanted) a separate, clearly-labeled convenience wrapper living in `infodynamics.text` (e.g. `infodynamics.text.TextInfoDynamics`) that internally builds and delegates to that same `Pipeline` — never inside core `pipeline.py`.

### Anti-Pattern 2: `infodynamics/__init__.py` importing from `.text`

**What people do:** `from .text import Encoder` in the top-level `__init__.py` "for convenience," so users get everything from one `import infodynamics`.

**Why it's wrong:** Silently makes the optional text extras a hard dependency of `import infodynamics` (import-time `ImportError` if `sentence-transformers` isn't installed), and creates exactly the reverse dependency this milestone forbids.

**Do this instead:** `infodynamics/__init__.py` exports only core symbols. `infodynamics.text` is a separate, explicit import: `from infodynamics.text import Encoder`. Enforce with a one-line CI check: `grep -rn "^from .text\|^from infodynamics.text\|^import infodynamics.text" infodynamics/*.py infodynamics/clustering/*.py` must return nothing (excluding `infodynamics/text/`).

### Anti-Pattern 3: Deleting `cache_contract.py`/`shipping.py`/`dashboard/` and discovering dangling imports later via runtime errors

**What people do:** Delete the removed-code directories/files first, then run the test suite and firefight whatever `ImportError`s show up, in whatever order they're encountered.

**Why it's wrong:** `ImportError`s surface one at a time as pytest collects modules, and can mask deeper issues (e.g. a demo script or `setup.py` entry point that only fails at runtime, not at collection).

**Do this instead:** Before deleting, grep the whole repo for every reference to the doomed modules (`cache_contract`, `shipping`, `dashboard`, `bench_core`, `render_overview`, `taxonomy`) — including `setup.py` console-script entries and root-level demo scripts — build the full removal set up front, delete it all in one commit, then run the full test suite once as the checkpoint. Per the current architecture map (`.planning/codebase/ARCHITECTURE.md`), `cache_contract.py`/`shipping.py` sit at the bottom of the dependency graph (nothing in the Signal Analysis / Pipeline layers imports them), so a clean grep-verified removal should require zero follow-up fixes in surviving core code — verify that assumption instead of assuming it.

## Integration Points

### External Services

Not applicable to this milestone — network/cloud integrations (rclone shipping) are exactly what's being removed. No new external service integration is introduced by the reorg.

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `infodynamics.text` → `infodynamics` (core) | Direct Python import (e.g. `from infodynamics.util import znorm_rows`), one-directional | Allowed and expected — on-ramp may reuse core numeric utilities |
| `infodynamics` (core) → `infodynamics.text` | **Forbidden** | Enforce via grep/CI check (see Anti-Pattern 2); this is the single most important boundary rule for this milestone |
| `infodynamics.text.*` step → `infodynamics.pipeline.*` step | `sklearn.pipeline.Pipeline`, via the `fit`/`transform`/`ndarray` contract | The only sanctioned way on-ramp output reaches core input — not direct function calls between the two packages inside a shared orchestration class |
| `infodynamics.clustering` (tslearn, optional) → rest of core | Lazy import inside `dtw.py`/`barycenter.py` functions, not module top-level | Keeps `import infodynamics` and `import infodynamics.clustering` cheap even without `tslearn` installed |
| Future dashboard repo → `infodynamics` (this package) | `pip install infodynamics` (or path/git dependency) as a normal downstream consumer | Out of scope this milestone, but the curated `__init__.py` + `infodynamics.text` split is exactly the contract that repo will consume — treat it as the de facto "first external consumer" when deciding what's public |

## Recommended Build Order (Extraction Sequence)

Each step ends with a **test-green checkpoint**; do not proceed to the next step until the previous checkpoint passes. Small, reviewable commits per step (not one mega-commit) so a bad step is easy to `git revert`.

**Checkpoint 0 — Baseline.** Full test suite green on current `main`/branch tip before any change. Tag or note the commit as the rollback point.

**Step 1 — Remove (subtractive, lowest risk, do first).**
1. Grep the whole repo up front for every reference to the doomed code: `cache_contract`, `shipping`, `dashboard`, `bench_core`, `render_overview`, `taxonomy`, `build_dashboard_artifacts`, `infodynamics-pack`/`-pull`/`-verify`/`-init-project` console scripts. Build the complete removal set before deleting anything (see Anti-Pattern 3).
2. Delete `dashboard/` wholesale (it depends on core, nothing in core depends on it — per current architecture map, safe standalone deletion).
3. Delete `infodynamics/cache_contract.py`, `infodynamics/shipping.py`.
4. Remove their `console_scripts` entries from `setup.py`.
5. Delete `tests/test_manifest.py` (tests only the removed cache/shipping code).
6. Delete/relocate root-level artifacts that only existed to feed the dashboard build (`BRIEF_artifact_backbone.md`, `build_dashboard_artifacts.py`-dependent demo scripts) if they reference removed code — verify via the same grep.
7. **Checkpoint 1:** re-run the grep (must return zero hits outside git history/CHANGELOG), `import infodynamics` succeeds, full test suite green.

**Step 2 — Reorganize (pure move, no behavior change).**
1. Create `infodynamics/text/__init__.py` (empty/minimal for now).
2. `git mv infodynamics/segmentation.py infodynamics/text/segmentation.py`; same for `embedding.py`, `morphology.py`.
3. Fix intra-package imports broken by the move (e.g. `from .util import znorm_rows` → `from ..util import znorm_rows`).
4. Mirror the move in tests: `git mv tests/test_segmentation.py tests/text/test_segmentation.py`, etc.
5. Update `infodynamics/pipeline.py` and `infodynamics/__init__.py` imports to the new paths — **do not change behavior yet**, `pipeline.py` may still call into `infodynamics.text.*` internally at this point.
6. **Checkpoint 2:** full test suite green, nothing behaviorally different, only module locations changed.

**Step 3 — Decouple the pipeline (the substantive, riskiest change — isolate in its own commit(s)).**
1. Wrap `segment()` in a `TextSegmenter(BaseEstimator, TransformerMixin)` in `infodynamics/text/segmentation.py` (Pattern 2).
2. Confirm `Encoder`/`MorphologicalEncoder` already satisfy `fit`/`transform`/`get_params`/`set_params` (add if missing) so they're Pipeline-legal on their own.
3. Change `InfoDynamics`/`MultiscaleInfoDynamics.fit`/`transform` in `infodynamics/pipeline.py` to accept only numeric `ndarray` input — remove internal `segment()`/`Encoder.encode()` calls.
4. Rewrite `tests/test_pipeline.py`/`tests/test_infodynamics_class.py` to feed `ndarray` fixtures directly (not raw text) into core estimators.
5. Add `tests/test_pipeline_composition.py`: build `sklearn.pipeline.Pipeline([("segment", TextSegmenter()), ("encode", Encoder()), ("analyze", MultiscaleInfoDynamics())])`, assert `fit_transform` runs end-to-end, `get_params()`/`set_params()` round-trip, and `sklearn.base.clone(pipe)` succeeds.
6. **Checkpoint 3:** full test suite green, including the new composition test — this is the step that proves the milestone's core constraint (Pipeline-composability) is actually met, not just structurally implied.

**Step 4 — Curate the public API surface.**
1. Rewrite `infodynamics/__init__.py` with an explicit `__all__` covering only core symbols; remove any `from .text import ...`.
2. Write `infodynamics/text/__init__.py` with its own explicit `__all__`.
3. Add/update one canonical usage example (README or a kept/rewritten demo script) showing both `from infodynamics import MultiscaleInfoDynamics` (core-only, ndarray in) and the full `Pipeline` composition with `infodynamics.text`.
4. **Checkpoint 4:** full test suite green; the CI grep for "core imports from `.text`" (Anti-Pattern 2) returns nothing.

**Step 5 — Verify (final pass, before declaring the milestone done).**
1. Full-repo grep sweep for `dashboard`, `cache_contract`, `shipping`, `bench_core` — zero hits.
2. Fresh venv, install with **no extras** (`pip install -e .`), confirm `import infodynamics` succeeds and is fast; confirm `import infodynamics.text` succeeds (structure imports fine even without heavy deps) and only fails, with a clear `ImportError` + install instructions, when `Encoder()`/`MorphologicalEncoder()`/`SignalClusterer()` is actually instantiated.
3. Full pytest suite green.
4. Lightweight Pipeline-composability smoke check on every public estimator (`get_params`/`set_params`/`clone`) — deliberately short of full `check_estimator` conformance, per PROJECT.md's explicit scope boundary.
5. **Checkpoint 5 (finish line):** decoupled + reorganized + tests green — matches PROJECT.md's stated definition of done for this milestone.

## Sources

- [Developing scikit-learn estimators — scikit-learn 1.9.0 documentation](https://scikit-learn.org/stable/developers/develop.html)
- [BaseEstimator — scikit-learn 1.9.0 documentation](https://scikit-learn.org/stable/modules/generated/sklearn.base.BaseEstimator.html)
- [TransformerMixin — scikit-learn 1.9.0 documentation](https://scikit-learn.org/stable/modules/generated/sklearn.base.TransformerMixin.html)
- [8.1. Pipelines and composite estimators — scikit-learn 1.9.0 documentation](https://scikit-learn.org/stable/modules/compose.html)
- [scikit-learn-contrib/project-template](https://github.com/scikit-learn-contrib/project-template) — canonical skeleton for sklearn-extension packages (estimator-check tests, one-package-per-family layout)
- [Packaging namespace packages — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/)
- [Writing your pyproject.toml — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- `.planning/codebase/ARCHITECTURE.md` — current-state dependency graph confirming cache/shipping sit at the bottom with no upstream core dependents
- `.planning/codebase/STRUCTURE.md` — current-state directory layout and existing extras convention (`embedding`, `morphology`, `clustering`, `viz-projection`, `test`)
- `.planning/PROJECT.md` — milestone constraints (breaking imports accepted, Pipeline-composability as the bar, `check_estimator` conformance explicitly out of scope)

---
*Architecture research for: modality-agnostic sklearn-compatible library reorg (infodynamics core + text on-ramp)*
*Researched: 2026-07-13*

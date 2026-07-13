# Feature Research

**Domain:** Public API surface for a modality-agnostic novelty-detection-from-time-series library (Python, sklearn ecosystem)
**Researched:** 2026-07-13
**Confidence:** MEDIUM (cross-checked against official docs of ruptures, sktime, stumpy, tslearn, scikit-learn; verified against current codebase architecture)

## Feature Landscape

### Table Stakes (Users Expect These)

Every comparable library in this space (ruptures, sktime, stumpy, tslearn, sklearn.covariance/svm) converges on the same handful of API expectations. Missing any of these makes the package feel like a research script, not a library.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `fit` / `transform` / `fit_transform` on every analysis primitive | Universal sklearn contract; ruptures, sktime transformers, tslearn all use it. `TransformerMixin` gives `fit_transform` for free if `fit` returns `self` | LOW | Codebase already does this (`BaseEstimator`/`TransformerMixin`, stateless transformers) — must be preserved, not re-invented |
| Constructor stores params only, no computation | sklearn's hard rule: `__init__` sets public attributes 1:1 with args, no validation/data. Enables `get_params`/`set_params`/`clone()` | LOW | Verify current pipeline classes (`InfoDynamics`, `MultiscaleInfoDynamics`) don't validate/load models in `__init__` |
| `get_params()` / `set_params()` working correctly | Required for `sklearn.pipeline.Pipeline`, `GridSearchCV`, `clone()` — this is what "sklearn-compatible" *means*, not just having `fit`/`transform` | LOW-MEDIUM | Free from `BaseEstimator` if constructor follows the param-storing rule; breaks silently if `**kwargs` or mutable defaults are used |
| Learned attributes end in `_` (trailing underscore) | sklearn convention (`coef_`, `components_`) distinguishes hyperparameters from fitted state; `check_is_fitted()` scans for these | LOW | E.g. computed SSM/scalogram/descriptors on stateful objects should be `self.ssm_`, `self.scalogram_`, not bare attrs |
| Pipeline-composability (`sklearn.pipeline.Pipeline([...])`) | Explicit PROJECT.md constraint. ruptures/tslearn/sktime all support chaining; this is the actual "does it feel like a real sklearn library" test | MEDIUM | Requires 2D-array-in/2D-array-out (or well-defined ndarray shape) consistency between every step — text on-ramp steps must emit arrays the core steps accept |
| Core estimators consume plain numeric arrays (`np.ndarray` / array-like), not text | Modality-agnostic requirement; matches how sktime/tslearn/stumpy/ruptures all operate purely on numeric series — text handling is *never* baked into the algorithm layer of any comparable library | MEDIUM | This is the central refactor: `InfoDynamics`/`MultiscaleInfoDynamics` currently accept raw text and do segmentation+encoding internally — must split |
| Curated top-level exports (`from infodynamics import X`) | sklearn (`sklearn.svm.OneClassSVM`), tslearn (`tslearn.clustering.TimeSeriesKMeans`), ruptures (`ruptures.Pelt`) — all expose a small, intentional set of names at package/subpackage root, not "import everything from every module" | LOW | Needs an explicit `__init__.py` allow-list per subpackage; currently the package likely re-exports whatever pipeline.py happens to define |
| Dual output convention: label/segmentation + continuous score | sklearn's outlier detectors expose both `predict()` (discrete) and `decision_function()`/`score_samples()` (continuous); ruptures exposes `predict()` (breakpoints) separately from the underlying cost curve | MEDIUM | Novelty/transience/resonance curves are already continuous scores — decide if a discrete "is this a novelty point" thresholding surface is worth adding (see Differentiators, not required for MVP) |
| Optional heavy dependencies degrade gracefully | sktime/tslearn both gate optional backends (e.g. tslearn's DTW extras) behind soft imports with actionable `ImportError`; PROJECT.md already commits to this for sentence-transformers/spacy-udpipe/textdescriptives/tslearn | LOW | Already implemented per ARCHITECTURE.md (`embedding.py:14-18`) — preserve pattern when reorganizing |
| Deterministic, documented input/output shapes | Every comparable library documents exact input shape (`(n_samples, n_timestamps)` for tslearn, `(n_samples, n_features)` for ruptures signal) — ambiguity here is the #1 integration friction point in issue trackers for all four libraries | LOW | Docstring/type-hint every `fit`/`transform` signature as part of the reorg, not deferred |

### Differentiators (Competitive Advantage)

Where this library can legitimately claim territory none of ruptures/sktime/stumpy/tslearn/sklearn cover alone.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Single-scale + multi-scale novelty/transience/resonance as one coherent framework | No comparable library frames "novelty" as a *triad* (novelty/transience/resonance) tied to multi-scale structure (scalogram + Foote novelty + SSM) in one package — stumpy has matrix-profile-based regime detection (`fluss`) but no scale-stack; ruptures does change points but no continuous novelty curve; sktime has point-anomaly detectors but not this specific decomposition | HIGH (already built) | This *is* the headline product — protect it, don't dilute it chasing generality |
| DTW-distance clustering with barycenter archetypes, tuned for novelty-signal outputs | tslearn provides the DTW/barycenter primitives generically; this library's differentiation is wiring them specifically to cluster *novelty/scalogram signal shapes* (not raw time series) with sensible defaults for that use case | MEDIUM | Keep as a thin, composable layer on top of tslearn rather than re-implementing DTW — avoid becoming "a worse tslearn" |
| `infodynamics.text` as a first-class, swappable Pipeline on-ramp (segmentation → embedding/morphology → arrays) | No general time-series library (ruptures/sktime/stumpy/tslearn) ships a *text*-specific on-ramp; NLP libraries don't ship novelty/multi-scale-structure analysis. The seam between them — "turn documents into meaningful numeric series, ready for a generic novelty core" — is largely this library's own territory | MEDIUM (mostly exists) | Must be *removable*: someone using only the core for sensor/audio data should never import anything from `infodynamics.text` or its heavy deps |
| Two interchangeable text-encoding strategies (semantic embedding vs. morphological/stylometric) feeding the *same* core | Differentiator over generic "embed then analyze" tooling — offers apples-to-apples comparison of meaning-drift vs. style-drift over the same document using the same downstream analysis | MEDIUM | Both must emit the same `(n_chunks, n_features)` contract so they're truly interchangeable Pipeline steps |
| `structure_descriptors()` as a compact numeric summary of multi-scale structure | Turns a whole document's dynamics into ~10 scalar features suitable for corpus-level comparison, clustering, or downstream ML — a "featurization of novelty," not just a visualization artifact | LOW (exists) | Good candidate for a stable, versioned public function since it's the bridge to "novelty dynamics as ML features" |

### Anti-Features (Deliberately Excluded)

These are explicitly named as leaving the package per PROJECT.md, and match a broader pattern: every comparable *analysis* library (ruptures, sktime, stumpy, tslearn, sklearn) ships **zero** serving/dashboard/caching infra — that's uniformly left to downstream apps or separate ecosystem packages (e.g., MLflow, not sklearn itself).

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|------------------|-------------|
| Streamlit dashboard / UI (`dashboard/app.py`) | "Users want to *see* results" | Couples a research/analysis library to a specific UI framework's release cycle and deployment model; no comparable library (sklearn, sktime, tslearn, ruptures, stumpy) ships a UI | Downstream dashboard repo consumes the library's plain arrays/dicts; `infodynamics.viz` (matplotlib) stays as a *lightweight, optional* convenience, not a UI |
| Cache contract / manifest system (`cache_contract.py`) | "Expensive to recompute embeddings/SSM every time" | Caching is an *application-level* concern (which corpus, which config, which run) — baking it into the library couples it to one project's cache schema and versioning; none of ruptures/sktime/stumpy/tslearn ship caching | Downstream consumers use `joblib.Memory`, `functools.lru_cache`, or their own manifest system around the library's pure `fit_transform` calls |
| Shipping / pack-pull-verify CLI (`shipping.py`, rclone integration) | "Need to move cache bundles to/from cloud storage" | Zero relationship to novelty detection; it's artifact-distribution infra for one specific dashboard deployment | Leaves with the dashboard repo entirely; not even referenced from core |
| `infodynamics-init-project` scaffolding CLI | "Nice onboarding for new case studies" | Assumes a specific project template (`data/`, `config.json`, `requirements.txt`) tied to the old case-study workflow — a general library shouldn't opinionatedly scaffold consumer projects | A `cookiecutter`/template repo, if wanted, lives outside the library |
| Corpus/CSV loading with hardcoded schema (`author`, `file_name`, `content` columns) | "Convenient to load and go" | Assumes one dataset shape; every comparable library (ruptures, tslearn, stumpy) accepts arrays/DataFrames the caller already prepared — none ship domain-specific file loaders | `infodynamics.text` on-ramp starts from already-loaded text/strings; loading corpora is the caller's job (or an example script, not library code) |
| Process-level singleton model caches as *implicit* global state (`_MODEL_CACHE`, `_PIPELINE_CACHE`) | "Avoid reloading HuggingFace/UDPipe models" | Not wrong to cache, but hidden module-level globals are surprising in a library meant to be Pipeline-composed and possibly used across threads/processes; sklearn estimators are expected to be stateless w.r.t. global mutable state outside `fit`-set attributes | Keep the caching (real perf win) but document it explicitly as an intentional, scoped exception — do not let similar hidden global state creep into the *core* novelty-analysis classes |
| AutoML / automatic hyperparameter search for scales, window sizes, thresholds | "Users don't want to hand-pick `scales=(2,3,5,8,13,21)`" | None of ruptures/sktime/tslearn ship this baked into their estimators — it's `GridSearchCV`'s job once the estimator exposes proper `get_params`; building it in-house duplicates sklearn's model-selection machinery poorly | Ensure estimators are clean enough that `sklearn.model_selection.GridSearchCV` / `Pipeline` works out of the box; no bespoke tuner |
| Real-time/streaming novelty detection API | "Feels modern, matches 'live dashboard' framing" | Current algorithms (SSM, scalogram, Foote novelty) are inherently batch/whole-series computations (need the full matrix); faking a streaming API on top would be misleading and is out of scope per PROJECT.md ("Refactor, not rewrite") | Batch `fit`/`transform` only; if streaming is ever wanted, it's a distinct future estimator, not a retrofit |
| Built-in model download/registry management beyond what `sentence-transformers`/`spacy-udpipe` already do | "One-stop model management" | Reinvents HuggingFace Hub / spacy-udpipe's own resolution logic; adds a maintenance surface with no differentiation | Pass through to the underlying library's native model resolution (already the current pattern per ARCHITECTURE.md) |

## API Surface Mapping: Core vs. `infodynamics.text`

This is the load-bearing structural decision for the milestone. Grounded in how sktime separates "transformers" (series-to-series/series-to-primitives, modality-agnostic) from task-specific estimators, and how ruptures/tslearn/stumpy never let domain-specific ingestion leak into the algorithm layer:

| API surface | Belongs in | Rationale | Current location |
|---|---|---|---|
| `WindowedRollingDistance` (novelty/transience/resonance from windowed rolling distance) | **core** | Operates on any `(n, n_features)` numeric array — no text-specific logic | `infodynamics/time_series.py` |
| `Scalogram`, `FooteNovelty`, `self_similarity_matrix()` | **core** | Pure array-in/array-out multi-scale structure; identical shape whether the array came from text embeddings, audio features, or sensor readings | `infodynamics/scalogram.py` |
| `structure_descriptors()` | **core** | Numeric featurization of SSM/scalogram output — modality-agnostic by construction | `infodynamics/scalogram.py` (or `metrics.py`) |
| `SignalClusterer` (DTW clustering, barycenters) | **core** | Clusters arbitrary numeric signal arrays; DTW/barycenter math has no notion of text | `infodynamics/clustering/cluster.py` |
| `InfoDynamics`, `MultiscaleInfoDynamics` (current top-level pipeline classes) | **split** | These currently accept *raw text* and do segmentation+encoding+analysis internally — this conflates on-ramp and core. Must become: a core estimator taking arrays (`InfoDynamics`/`MultiscaleInfoDynamics` reworked to array-in) that a user reaches via `sklearn.pipeline.Pipeline([("segment+encode", ...), ("analyze", MultiscaleInfoDynamics())])`, OR keep as a convenience wrapper that *internally* composes an `infodynamics.text` on-ramp + core Pipeline for the common case | `infodynamics/pipeline.py` |
| `Segmentation` / `segment()`, `Chunk`, `strip_markdown()` | **`infodynamics.text`** | Text-specific chunking; no other modality has "sentences/paragraphs" | `infodynamics/segmentation.py` |
| `Encoder` (HuggingFace sentence-embedding) | **`infodynamics.text`** | Text-to-vector; a sklearn `TransformerMixin` whose `transform` output (`(n_chunks, n_dims)` array) is exactly what core consumes — the seam is clean *if* the array contract matches | `infodynamics/embedding.py` |
| `MorphologicalEncoder` (UDPipe + textdescriptives) | **`infodynamics.text`** | Syntactic/stylometric feature extraction, inherently text-specific | `infodynamics/morphology.py` |
| `viz.py` (plot_overlay, plot_ssm, plot_scalogram, plot_multiscale_novelty, plot_dendrogram) | **core, optional** | Visualizes arrays (SSM/scalogram/novelty/dendrogram) regardless of source modality; keep as a lightweight `matplotlib`-only optional module, not folded into either on-ramp or dashboard | `infodynamics/viz.py` |
| Dashboard, cache_contract, shipping, build_dashboard_artifacts | **neither — removed** | Case-study/serving infra; see Anti-Features | `dashboard/`, `infodynamics/cache_contract.py`, `infodynamics/shipping.py` |

**Naming/export convention implication:** mirror sktime/tslearn's pattern of subpackage-scoped curated exports:
```python
import infodynamics as idyn                      # core: InfoDynamics, MultiscaleInfoDynamics, Scalogram, SignalClusterer, structure_descriptors
import infodynamics.text as idyn_text             # on-ramp: Segmentation/segment, Encoder, MorphologicalEncoder
import infodynamics.viz as idyn_viz               # optional plotting
```
Avoid a flat `from infodynamics import *` grab-bag — every comparable library (sklearn, sktime, tslearn) organizes by subpackage (`sklearn.svm`, `sktime.transformations`, `tslearn.clustering`) rather than dumping everything at root.

## Feature Dependencies

```
Text on-ramp (Segmentation, Encoder, MorphologicalEncoder)
    └──feeds (array contract: (n_chunks, n_features))──> Core analysis (WindowedRollingDistance, Scalogram, FooteNovelty)
                                                              └──feeds (signal array)──> SignalClusterer (DTW + barycenter)
                                                              └──feeds (SSM + scalogram)──> structure_descriptors()

Pipeline-composability (get_params/set_params, array contracts)
    └──requires──> Constructor discipline (params-only __init__, no *args/**kwargs)
    └──requires──> Consistent fit/transform shapes across every step (text on-ramp AND core)

Curated top-level exports
    └──requires──> Core/on-ramp module split to already exist (can't curate what isn't organized yet)

Optional viz (infodynamics.viz)
    └──enhances──> Core analysis (visual QA of SSM/scalogram/novelty) but is never a dependency of it

Dashboard/cache/shipping (removed)
    └──conflicts with──> Modality-agnostic core design goal (introduces text-corpus-shaped, project-shaped assumptions into what should be a generic library)
```

### Dependency Notes

- **Text on-ramp feeds core, never the reverse:** core classes must not import anything from `infodynamics.text`; the on-ramp imports core (or is Pipeline-composed alongside it) but not vice versa. This one-directional dependency is what makes "core is modality-agnostic" true rather than aspirational.
- **Pipeline-composability requires constructor discipline first:** you cannot bolt on `get_params`/`set_params` correctness after the fact if constructors currently validate or compute — this needs to be an explicit pass over every public class during the reorg, not an assumed side effect of moving files.
- **Curated exports require the split to be real:** deciding *what's* exported at `infodynamics.__init__` only makes sense once core/text-on-ramp module boundaries exist; sequence the reorg before the export curation.
- **Dashboard/cache/shipping conflicts with the core design goal:** this is why PROJECT.md treats their removal as a *precondition*, not an optional cleanup — their continued presence in-tree would keep re-coupling core code to text/corpus-shaped assumptions via `build_dashboard_artifacts.py`'s heavy use of pipeline internals.

## MVP Definition

This is a refactor of an existing, working codebase — "MVP" here means the minimum reorganization that satisfies PROJECT.md's Active requirements, not new algorithm work.

### Launch With (v1 of the reorg)

- [ ] Core subpackage with array-in/array-out `WindowedRollingDistance`, `Scalogram`, `FooteNovelty`, `structure_descriptors`, `SignalClusterer` — no text imports anywhere in this subpackage — essential to satisfy "Analysis primitives operate on generic numeric time series/embeddings, independent of text"
- [ ] `infodynamics.text` subpackage with `Segmentation`, `Encoder`, `MorphologicalEncoder` — essential to satisfy "first-class but separable" on-ramp
- [ ] Core pipeline classes (`InfoDynamics`, `MultiscaleInfoDynamics` or their reworked equivalents) accept numeric arrays; text convenience path goes through explicit `sklearn.pipeline.Pipeline` composition — essential for the Pipeline-composability requirement
- [ ] Curated `__init__.py` exports at package root and at `infodynamics.text` — essential for "clean, intentional public API"
- [ ] `get_params`/`set_params` verified working (e.g., a smoke test constructing a `Pipeline` and calling `clone()`) on every public estimator — essential; this is the actual bar PROJECT.md sets ("Pipeline-composability is the bar", not full `check_estimator`)
- [ ] Dashboard, `cache_contract.py`, `shipping.py`, `build_dashboard_artifacts.py` removed from the repo tree (preserved in git history) — explicit Active requirement
- [ ] Test suite green against the reorganized package — explicit Active requirement

### Add After Validation (v1.x — later milestones, not blocking this one)

- [ ] `pyproject.toml` migration / packaging modernization — explicitly deferred in PROJECT.md
- [ ] PyPI publish — explicitly deferred
- [ ] Full `sklearn.utils.estimator_checks.check_estimator` conformance — explicitly "nice-to-have, not a gate"
- [ ] `__sklearn_tags__` implementation for programmatic capability inspection — natural follow-on once Pipeline-composability is solid, not needed for it

### Future Consideration (v2+)

- [ ] Additional modality on-ramps (audio, sensor) — PROJECT.md explicitly scopes this milestone to text-only on-ramp, core designed to make this addable later
- [ ] Discrete "is this point a novelty event" thresholding API (`predict()` returning -1/1 alongside continuous scores, mirroring `sklearn.svm.OneClassSVM`) — a real differentiator opportunity, but adds a new decision surface (threshold selection) not needed for the reorg itself
- [ ] Estimator registry/discovery utility mirroring `sktime.registry.all_estimators` — only worth it once there are enough estimator variants to need discovery

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Core subpackage, array-only analysis primitives | HIGH | MEDIUM | P1 |
| `infodynamics.text` on-ramp subpackage | HIGH | LOW (mostly moving existing code) | P1 |
| Curated top-level exports | HIGH | LOW | P1 |
| Pipeline-composability verification (get_params/set_params/clone smoke test) | HIGH | LOW-MEDIUM | P1 |
| Remove dashboard/cache/shipping code | HIGH (unblocks everything else) | MEDIUM (careful extraction, preserve history) | P1 |
| Discrete predict()/decision_function() novelty-event API | MEDIUM | MEDIUM | P3 |
| `__sklearn_tags__` / full `check_estimator` conformance | LOW (nice-to-have per PROJECT.md) | MEDIUM-HIGH | P3 |
| pyproject.toml / packaging modernization | MEDIUM | LOW-MEDIUM | P3 (separate milestone) |
| Additional modality on-ramps (audio/sensor) | MEDIUM (future) | HIGH | P3 (future milestone) |

**Priority key:**
- P1: Must have for this milestone
- P2: Should have, add when possible (none identified for this milestone — reorg scope is tightly bounded by PROJECT.md)
- P3: Explicitly deferred per PROJECT.md Out of Scope, or a future differentiator not needed for the reorg to succeed

## Competitor Feature Analysis

| Dimension | ruptures | sktime | stumpy | tslearn | sklearn.covariance/svm | infodynamics (target) |
|---|---|---|---|---|---|---|
| Primary API shape | Class-based, `fit`/`predict`/`fit_predict` | Class-based, task-typed estimators (`fit`/`predict` or `fit`/`transform`) | Function-first (`stump`, `fluss`), arrays in/out, no estimator classes | Class-based, full `BaseEstimator` (`fit`/`predict`) | Class-based, `fit`/`predict`/`decision_function` | Class-based (`BaseEstimator`/`TransformerMixin`), matching sktime/tslearn more than stumpy |
| Modality-agnostic core | Yes — pure numeric signal in | Yes — series-to-series/primitives transformers are generic | Yes — pure numpy arrays | Yes — numeric time series arrays | Yes — feature matrix `X` | **Target**: yes, this is the milestone's core deliverable |
| Domain-specific on-ramp shipped in same package | No | No (separate `sktime` extension packages exist for domain data loaders) | No | No | No | **Yes, deliberately** — `infodynamics.text`, kept separable |
| Dashboard/UI shipped | No | No | No | No | No | No (removed this milestone) |
| Caching/serving infra shipped | No | No | No | No | No | No (removed this milestone) |
| Pluggable algorithm/strategy via constructor param | Yes (cost function classes) | Yes (many estimator variants, uniform interface) | N/A (single algorithm family) | Yes (`metric='dtw'/'softdtw'/'euclidean'`) | N/A (each detector is its own class) | Should follow tslearn's pattern where reasonable (e.g. distance metric as param, not subclass) |
| Discrete + continuous output | Discrete only (`predict()` → breakpoints); pen-based severity via cost curve | Detector-type-dependent | Continuous (matrix profile) + `fluss` regime boundaries | N/A (clustering, not detection) | Both (`predict()` label + `decision_function()` score) | Currently continuous-only (novelty/transience/resonance curves) — sklearn's dual-output pattern is the differentiator gap worth flagging for roadmap, not required for this milestone |
| Curated top-level namespace | Yes (`ruptures.Pelt`, `ruptures.Binseg`) | Yes (subpackage-scoped: `sktime.forecasting`, `sktime.transformations`) | Yes (flat but small: `stumpy.stump`) | Yes (subpackage-scoped: `tslearn.clustering`) | Yes (`sklearn.svm.OneClassSVM`) | **Target**: subpackage-scoped like sktime/tslearn (`infodynamics` core + `infodynamics.text`) |

## Sources

- [ruptures documentation](https://centre-borelli.github.io/ruptures-docs/) — MEDIUM confidence
- [ruptures GitHub](https://github.com/deepcharles/ruptures) — MEDIUM confidence
- [sktime — The AI Framework for Time Series](https://www.sktime.net/) — MEDIUM confidence
- [sktime: Time series detection tasks (detectors) API reference](https://www.sktime.net/en/latest/api_reference/detection.html) — MEDIUM confidence
- [sktime: Time series transformations API reference](https://www.sktime.net/en/latest/api_reference/transformations.html) — MEDIUM confidence
- [sktime: A Unified Interface for Machine Learning with Time Series (arXiv)](https://ar5iv.labs.arxiv.org/html/1909.07872) — MEDIUM confidence
- [STUMPY API Reference](https://stumpy.readthedocs.io/en/latest/api.html) — MEDIUM confidence
- [STUMPY GitHub](https://github.com/stumpy-dev/stumpy) — MEDIUM confidence
- [tslearn: TimeSeriesKMeans documentation](https://tslearn.readthedocs.io/en/stable/gen_modules/clustering/tslearn.clustering.TimeSeriesKMeans.html) — MEDIUM confidence
- [tslearn: Time Series Clustering user guide](https://tslearn.readthedocs.io/en/stable/user_guide/clustering.html) — MEDIUM confidence
- [scikit-learn: 2.7. Novelty and Outlier Detection](https://scikit-learn.org/stable/modules/outlier_detection.html) — MEDIUM confidence
- [scikit-learn: Developing scikit-learn estimators](https://scikit-learn.org/stable/developers/develop.html) — MEDIUM confidence
- `.planning/codebase/ARCHITECTURE.md` (this repo, current codebase analysis) — HIGH confidence (primary source)
- `.planning/PROJECT.md` (this repo, milestone scope) — HIGH confidence (primary source)

---
*Feature research for: modality-agnostic novelty-detection library public API*
*Researched: 2026-07-13*

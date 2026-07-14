# Phase 3: Decouple the Pipeline - Pattern Map

**Mapped:** 2026-07-14
**Files analyzed:** 9 (modified) + 1 (new)
**Analogs found:** 9 / 9 (one file, `cluster.py`, is itself the canonical analog and is unchanged)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `infodynamics/time_series.py` (`WindowedRollingDistance`) | transform/estimator | CRUD-like transform (array in, array out) | `infodynamics/clustering/cluster.py` (`SignalClusterer`) | role-match (bug fix target; canonical sklearn shape lives in cluster.py) |
| `infodynamics/scalogram.py` (`Scalogram`, `FooteNovelty`) | transform/estimator | transform (array in, array out) | `infodynamics/clustering/cluster.py` (`SignalClusterer`) | role-match (already array-returning; only needs `transform()` added) |
| `infodynamics/pipeline.py` (`InfoDynamics`, `MultiscaleInfoDynamics`) | composite/orchestrator estimator | transform (ndarray in/out, no more text-in) | `infodynamics/scalogram.py` (`Scalogram`/`FooteNovelty` array-return convention) + `cluster.py` (mixin/param pattern) | exact (they already sit next to these; needs API-shape convergence per D-03) |
| `infodynamics/text/segmentation.py` (new `TextSegmenter` class) | new estimator (wraps existing `segment()` function) | transform (str in, `List[str]` out) | `infodynamics/clustering/cluster.py` (`SignalClusterer`) | role-match (best available `BaseEstimator`+mixin skeleton in the codebase) |
| `infodynamics/text/embedding.py` (`Encoder` — add `fit`/`transform`/`get_params`/`set_params`) | estimator wrapper around lazy-loaded model | transform (`List[str]` in, ndarray out) | `infodynamics/clustering/cluster.py` (`SignalClusterer`) | role-match |
| `infodynamics/text/morphology.py` (`MorphologicalEncoder` — add `fit`/`transform`/`get_params`/`set_params`) | estimator wrapper around lazy-loaded pipeline | transform (`List[str]` in, ndarray out) | `infodynamics/clustering/cluster.py` (`SignalClusterer`) | role-match |
| `infodynamics/text/__init__.py` (new `TextInfoDynamics`, `TextMultiscaleInfoDynamics`) | composite convenience wrapper | transform (str in, dict/array out) | `infodynamics/pipeline.py` (current `InfoDynamics.fit`, pre-refactor, as the "segment→encode→analyze" chain to reproduce) | exact (this is literally today's `InfoDynamics.fit` body, relocated) |
| `tests/test_infodynamics_class.py` (fix `test_transience_calculation`, `test_window_size`, add negative/small-number tests) | test | request-response (unit test) | itself (existing hypothesis test `test_validate_data_hypothesis`, lines 60-81) | exact (same file, extend existing test idioms) |
| `tests/golden/capture_baseline.py` (update `compute_outputs()` calls) | test/fixture (golden snapshot) | batch/transform | itself, lines 143-218 (`compute_outputs`) | exact (must be edited in place to match new ndarray-only `fit`/`fit_transform` signatures) |
| `tests/test_pipeline_composition.py` (new) | test | request-response (Pipeline contract test) | `tests/test_infodynamics_class.py` (existing test file conventions: imports, `pytest`/`hypothesis` usage) | role-match (no existing Pipeline-composition test to copy structurally; must be built from scratch using sklearn's `clone`/`Pipeline` idioms) |

## Pattern Assignments

### `infodynamics/time_series.py` — `WindowedRollingDistance` (estimator, transform)

**Analog:** `infodynamics/clustering/cluster.py` (`SignalClusterer`)

**Canonical `__init__` pattern to copy** (cluster.py lines 24-56):
```python
class SignalClusterer(BaseEstimator, ClusterMixin):
    def __init__(
        self,
        n_clusters: Optional[int] = None,
        k_range: Sequence[int] = range(2, 10),
        linkage: str = "average",
        z_normalize: bool = True,
        barycenter_method: Literal["dba", "soft_dtw"] = "dba",
    ):
        self.n_clusters = n_clusters
        self.k_range = k_range
        self.linkage = linkage
        self.z_normalize = z_normalize
        self.barycenter_method = barycenter_method
```
Key property: every constructor arg is stored **verbatim**, unresolved, no validation, no branching. This is exactly what QA-02 requires: `WindowedRollingDistance.__init__` currently resolves `measure` via `DISTANCES` lookup and raises `AttributeError` inline (`time_series.py` lines 56-61) — that resolution must move into `fit()`/a helper, following `scalogram.py`'s own `_resolve_measure()` (lines 20-26) as the resolution-helper pattern:
```python
def _resolve_measure(measure: Union[str, Callable]) -> Callable:
    if measure in DISTANCES:
        return DISTANCES[measure]
    elif callable(measure):
        return measure
    else:
        raise AttributeError(f"Invalid value for parameter 'measure': {measure}")
```
`WindowedRollingDistance.fit()` should call this same helper (or import it from `scalogram.py`) instead of resolving in `__init__`.

**`fit()`/state pattern to copy** (cluster.py lines 76-115): store every derived result as a `*_`-suffixed fitted attribute, return `self`. `time_series.py`'s current `fit()` (lines 154-203) already does this partially (`self.signal = signal` — note: missing trailing underscore, should become `self.signal_` per D-03/convention) but needs a `transform()` method added, mirroring `scalogram.py`'s existing `fit_transform()` split (lines 120-123):
```python
def fit_transform(self, embeddings: ArrayLike, y=None) -> np.ndarray:
    """Fit to embeddings, return the [n_scales x n_chunks] scalogram matrix."""
    self.fit(embeddings)
    return self.matrix_
```
Per D-02/D-03, `WindowedRollingDistance.transform(X)` must recompute fresh from `X` (same code path as `fit`) and return a single stacked array (novelty/transience/resonance), with the full dict preserved as `self.signal_`.

**`_validate_data` completion target** — currently marked "UNFINISHED" (`time_series.py` lines 70-85), only handles list-of-lists. No close analog exists in-repo for array validation beyond `np.asarray()` calls already used in `scalogram.py` (e.g. `embeddings = np.asarray(embeddings)`, line 106, line 128, line 216). Recommend converging `_validate_data` to a thin `np.asarray(X)` wrapper (matching every other estimator's validation strategy) rather than inventing new logic — see "No Analog Found" below.

---

### `infodynamics/scalogram.py` — `Scalogram`, `FooteNovelty` (estimators, transform)

**Analog:** `infodynamics/clustering/cluster.py` (for the missing `transform()` method shape) + self (existing `fit`/`fit_transform` split, lines 91-123 and 201-233).

These two classes already match D-03's target output convention (array-returning `fit_transform()` with rich fitted attributes: `matrix_`, `scales_` / `novelty_`, `ssm_`, `radii_`). The only gap per D-02 is a standalone `transform()`:
```python
# Existing (lines 120-123), to be supplemented with:
def transform(self, embeddings: ArrayLike, y=None) -> np.ndarray:
    """Recompute the scalogram matrix fresh from embeddings (no fit-time state is reused)."""
    self.fit(embeddings)
    return self.matrix_
```
Since fit/transform are identical here (no leakage risk per D-02's note), `transform` can literally delegate to `fit_transform`'s body, or `fit_transform` can be simplified to call `self.fit(X).transform(X)` (relying on `TransformerMixin`'s default) — planner's discretion per "Established Patterns" note in CONTEXT.md.

---

### `infodynamics/pipeline.py` — `InfoDynamics`, `MultiscaleInfoDynamics` (composite estimators)

**Analog:** `infodynamics/scalogram.py`'s array-return convention (target state) + current `infodynamics/pipeline.py` itself (source of the `chunks_` fitted-attribute convention that D-01 reuses).

**Current text-coupled `fit()` to be removed** (pipeline.py lines 84-131, `InfoDynamics.fit`):
```python
def fit(self, text: str, y=None) -> Self:
    if self.encoder is None and self.model_name is None:
        raise ValueError("One of 'model_name' or 'encoder' is required.")

    chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
    encoder = self.encoder if self.encoder is not None else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
    embeddings = encoder.encode([chunk.text for chunk in chunks])

    wrd = WindowedRollingDistance(...)
    signal = wrd.fit_transform(embeddings)

    self.chunks_ = chunks
    self.embeddings_ = embeddings
    self.signal_ = {
        "novelty": signal["N_hat"],
        "transience": signal["T_hat"],
        "resonance": signal["R_hat"],
    }
    ...
    return self
```
CORE-02 removes the `segment()`/`Encoder.encode()` calls entirely — `fit(X)` becomes ndarray-only (`X` = embeddings). This logic (segment → encode → analyze) must be relocated verbatim into the new `infodynamics.text.TextInfoDynamics` convenience wrapper (D-04) — see below.

**`self.chunks_ = chunks` fitted-attribute pattern** (pipeline.py line 115, line 250) — this exact convention is the direct analog for `TextSegmenter.chunks_` per D-01. Copy the assignment idiom (store list-of-`Chunk` as a fitted attribute distinct from the return value of `transform()`).

**Output-dict-vs-array convergence target** (D-03): `MultiscaleInfoDynamics.fit()` (lines 222-259) already stores everything needed as fitted attributes (`self.ssm_`, `self.scalogram_`, `self.novelty_`, `self.descriptors_`) — this part doesn't change. Only `fit_transform()`'s *return value* changes from dict (lines 261-285) to converge with `Scalogram`/`FooteNovelty`'s single-array convention; planner decides the "primary array" per D-03's note (no locked decision).

---

### `infodynamics/text/segmentation.py` — new `TextSegmenter` class

**Analog:** `infodynamics/clustering/cluster.py` (`SignalClusterer`) for the `BaseEstimator`/mixin skeleton; `infodynamics/text/segmentation.py`'s own `segment()` function (lines 79-106) for the actual chunking logic to wrap (not reimplement).

**Skeleton to follow** (adapting cluster.py's shape to `TransformerMixin` instead of `ClusterMixin`, matching pipeline.py's own `BaseEstimator, TransformerMixin` import at line 8):
```python
from sklearn.base import BaseEstimator, TransformerMixin
from typing_extensions import Self

class TextSegmenter(BaseEstimator, TransformerMixin):
    def __init__(self, level: Level = "sentence", chunk_size: int = 1):
        self.level = level
        self.chunk_size = chunk_size

    def fit(self, text: str, y=None) -> Self:
        self.chunks_ = segment(text, level=self.level, chunk_size=self.chunk_size)
        return self

    def transform(self, text: str, y=None) -> List[str]:
        self.fit(text)  # recompute fresh per D-02 (no fit/transform state leakage)
        return [chunk.text for chunk in self.chunks_]
```
Per D-01: `transform()` returns `List[str]` (plain chunk texts, slots directly into `Encoder.encode()`); `self.chunks_` (`List[Chunk]`) is the fitted attribute preserving position info, directly modeled on `pipeline.py`'s `self.chunks_ = chunks` (line 115/250).

---

### `infodynamics/text/embedding.py` — `Encoder` (add `fit`/`transform`/`get_params`/`set_params`)

**Analog:** `infodynamics/clustering/cluster.py` for the mixin/param pattern; `Encoder`'s existing `.encode()` (lines 40-52) is the core logic to wrap, not change.

**Current class** (embedding.py lines 25-52):
```python
class Encoder:
    """Embeds text chunks with a HuggingFace Hub encoder model."""

    def __init__(
        self,
        model_name: str,
        device: Optional[str] = None,
        batch_size: int = 32,
        normalize: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize = normalize

    def encode(self, texts: List[str]) -> np.ndarray:
        model = _load_model(self.model_name)
        if self.device is not None:
            model.to(self.device)
        embeddings = model.encode(...)
        return np.asarray(embeddings)
```
Already stores every param verbatim (matches `SignalClusterer`'s pattern exactly) — just needs `BaseEstimator, TransformerMixin` inheritance and thin `fit`/`transform` wrappers around the existing `.encode()`:
```python
class Encoder(BaseEstimator, TransformerMixin):
    ...  # __init__ unchanged
    def fit(self, texts: List[str], y=None) -> Self:
        return self

    def transform(self, texts: List[str], y=None) -> np.ndarray:
        return self.encode(texts)
```
**QA-02 bug fix (cache key + mutation) target** — `_MODEL_CACHE: Dict[str, "object"]` (line 8) keyed only by `model_name`, and `.to(self.device)` (line 43) mutates the shared cached model in place. Fix: key by `(model_name, device)` tuple, matching `morphology.py`'s already-correct `_PIPELINE_CACHE: Dict[Tuple[str, str, Optional[str]], "object"]` (line 9) as the canonical "already fixed" analog:
```python
# morphology.py line 9 — the correct pattern to replicate in embedding.py:
_PIPELINE_CACHE: Dict[Tuple[str, str, Optional[str]], "object"] = {}
```

---

### `infodynamics/text/morphology.py` — `MorphologicalEncoder` (add `fit`/`transform`/`get_params`/`set_params`)

**Analog:** Same as `Encoder` above — `infodynamics/clustering/cluster.py` for the mixin pattern; `MorphologicalEncoder`'s own `.encode()` (lines 185-194) is the logic to wrap unchanged. `_PIPELINE_CACHE` (line 9) is already correctly keyed — explicitly "not part of the bug, don't touch" per CONTEXT.md.

**Current class** (morphology.py lines 147-194) — same shape as `Encoder`: `__init__` stores params verbatim (lines 153-183), `.encode()` does the work. Apply the identical thin `fit`/`transform` wrapper pattern shown above for `Encoder`.

---

### `infodynamics/text/__init__.py` (or new module) — `TextInfoDynamics`, `TextMultiscaleInfoDynamics` (D-04)

**Analog:** `infodynamics/pipeline.py`'s **current** (pre-refactor) `InfoDynamics.fit()` (lines 84-131) and `MultiscaleInfoDynamics.fit()` (lines 222-259) — this is the exact "segment → encode → analyze" chain being relocated, not a new pattern.

**Pattern to replicate** (composing three fitted estimators in sequence, mirroring today's inline logic at pipeline.py lines 103-105):
```python
chunks = segment(text, level=self.segment_level, chunk_size=self.chunk_size)
encoder = self.encoder if self.encoder is not None else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
embeddings = encoder.encode([chunk.text for chunk in chunks])
```
becomes, using the new `TextSegmenter`/`Encoder.transform`:
```python
class TextInfoDynamics(BaseEstimator, TransformerMixin):
    def __init__(self, segmenter=None, encoder=None, info_dynamics=None, ...):
        ...

    def fit(self, text: str, y=None) -> Self:
        chunks_text = self.segmenter.fit_transform(text)
        embeddings = self.encoder.fit_transform(chunks_text)
        self.info_dynamics_ = self.info_dynamics.fit(embeddings)
        self.chunks_ = self.segmenter.chunks_
        return self
```
Lives under `infodynamics.text` per D-04 (text-specific sugar, not core).

## Shared Patterns

### sklearn `BaseEstimator`/mixin skeleton (the canonical "what good looks like")
**Source:** `infodynamics/clustering/cluster.py` lines 17-56 (`SignalClusterer.__init__`)
**Apply to:** `WindowedRollingDistance` (bug fix), new `TextSegmenter`, `Encoder`, `MorphologicalEncoder`
```python
class SignalClusterer(BaseEstimator, ClusterMixin):
    def __init__(self, n_clusters=None, k_range=range(2, 10), linkage="average",
                 z_normalize=True, barycenter_method="dba"):
        self.n_clusters = n_clusters
        self.k_range = k_range
        self.linkage = linkage
        self.z_normalize = z_normalize
        self.barycenter_method = barycenter_method
```
Rule extracted: **every constructor parameter is stored verbatim on `self` with the same name, no resolution/validation inline.** Resolution/validation (e.g. measure lookup, feature_group checks) happens later, in `fit()`.

### Measure resolution helper (already-correct pattern for QA-02's `WindowedRollingDistance` fix)
**Source:** `infodynamics/scalogram.py` lines 20-26 (`_resolve_measure`)
**Apply to:** `infodynamics/time_series.py`'s `WindowedRollingDistance.__init__`/`fit`
```python
def _resolve_measure(measure: Union[str, Callable]) -> Callable:
    if measure in DISTANCES:
        return DISTANCES[measure]
    elif callable(measure):
        return measure
    else:
        raise AttributeError(f"Invalid value for parameter 'measure': {measure}")
```

### Array-return + fitted-attribute-dict convention (D-03 target shape)
**Source:** `infodynamics/scalogram.py` lines 91-123 (`Scalogram.fit`/`fit_transform`)
**Apply to:** `WindowedRollingDistance`, `InfoDynamics`, `MultiscaleInfoDynamics`
```python
def fit(self, embeddings, y=None) -> Self:
    ...
    self.matrix_ = np.vstack([...])
    self.scales_ = scales
    return self

def fit_transform(self, embeddings, y=None) -> np.ndarray:
    self.fit(embeddings)
    return self.matrix_
```

### Correctly-keyed lazy-load cache (QA-02 fix reference)
**Source:** `infodynamics/text/morphology.py` line 9 (`_PIPELINE_CACHE`)
**Apply to:** `infodynamics/text/embedding.py`'s `_MODEL_CACHE` (currently keyed by `model_name` only, line 8)
```python
_PIPELINE_CACHE: Dict[Tuple[str, str, Optional[str]], "object"] = {}
```

### Lazy heavy-import pattern (preserve, don't disturb)
**Source:** `infodynamics/text/embedding.py` lines 11-22 (`_load_model`), `infodynamics/text/morphology.py` lines 36-63 (`_load_pipeline`)
**Apply to:** New `fit`/`transform` wrappers on `Encoder`/`MorphologicalEncoder` — must not import `sentence_transformers`/`spacy_udpipe`/`textdescriptives` at class-definition time or in `__init__`; only inside `.encode()`/model-loading helpers, exactly as today.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `infodynamics/time_series.py`'s `_validate_data` completion (QA-02) | validation utility | transform (input coercion) | No existing "complete" input-validation utility in the codebase to copy from — every other estimator (`scalogram.py`, `cluster.py`) validates inline via a single `np.asarray(X)` call rather than a dedicated method. Recommend converging `_validate_data` to that same one-line idiom instead of building bespoke list/array/dataframe branching logic. |
| `tests/test_pipeline_composition.py` (new, ROADMAP criterion 4) | test (Pipeline contract) | request-response | No existing test in the repo exercises `sklearn.pipeline.Pipeline` composition, `clone()`, or `get_params`/`set_params` round-trips. `tests/test_infodynamics_class.py` is the closest existing test file for *import/fixture conventions* (pytest, hypothesis, `from infodynamics import ...`) but has no structural pattern for Pipeline-specific assertions — must be authored using sklearn's own `sklearn.utils.estimator_checks` or manual `clone()`/`Pipeline([...])` idioms, not copied from an in-repo analog. |

## Metadata

**Analog search scope:** `infodynamics/` (pipeline.py, time_series.py, scalogram.py, clustering/cluster.py, text/embedding.py, text/morphology.py, text/segmentation.py), `tests/` (test_infodynamics_class.py, golden/capture_baseline.py)
**Files scanned:** 9
**Pattern extraction date:** 2026-07-14

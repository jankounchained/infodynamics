# Phase 3: Decouple the Pipeline - Context

**Gathered:** 2026-07-14
**Status:** Ready for planning

<domain>
## Phase Boundary

The one substantive rewrite in this milestone: cut `InfoDynamics`/`MultiscaleInfoDynamics` loose from direct `segment()`/`Encoder.encode()` calls so they accept only numeric `ndarray` input, build a real `TextSegmenter` estimator (doesn't exist yet), make every public estimator genuinely `sklearn.pipeline.Pipeline`-composable (`get_params`/`set_params`/`clone` round-trip, working `transform()`), and fix the known bugs/test debt (QA-02, QA-03) as their own labeled commits with a deliberate golden-snapshot update.

Requirements in scope: CORE-02, TEXT-02, API-01, API-02, QA-02, QA-03.

This is the phase the ROADMAP flagged as "the substantive, riskiest phase" with three open research questions — all resolved below.

</domain>

<decisions>
## Implementation Decisions

### TextSegmenter I/O contract (research flag: chunk flow)
- **D-01:** `TextSegmenter.transform(text)` returns `List[str]` (plain chunk texts), not `List[Chunk]`. This slots directly into `Encoder.encode()`'s existing `List[str]` signature with zero changes to `Encoder`/`MorphologicalEncoder` beyond adding `fit`/`transform`/`get_params`/`set_params`. Position info (start/end spans) is preserved as a fitted attribute — `self.chunks_` (`List[Chunk]`) — set during `fit()`, following the same fitted-attribute convention `pipeline.py` already uses (`self.chunks_ = chunks`). Nothing is silently dropped; it just doesn't flow through the Pipeline's `X`.
- Rationale: smallest diff, no changes needed to `Encoder`/`MorphologicalEncoder`'s input handling, and matches the existing `chunks_`-as-fitted-attribute pattern already established in `infodynamics/pipeline.py`.

### transform() semantics (research flag a)
- **D-02:** Every public estimator gets a real, standalone `transform(X)` — not just `fit()` + a `fit_transform()` that returns stored state. None of these estimators (`WindowedRollingDistance`, `Scalogram`, `FooteNovelty`, `InfoDynamics`, `MultiscaleInfoDynamics`, `TextSegmenter`, `Encoder`, `MorphologicalEncoder`) learn parameters from fit data in a way that could leak between fit and transform (no `mean_`/`std_`-style state) — they're pure functions of whatever `X` is passed. So `transform(X)` recomputes fresh from `X` using the same code path as `fit()`, uniformly across every estimator. This satisfies API-01's literal wording ("every public estimator implements fit / transform / fit_transform") for estimators that currently have no `transform()` at all — including `Scalogram`/`FooteNovelty`, which today only implement `fit()` + `fit_transform()`.
- Note for planner: this also fixes a real Pipeline gap — `Pipeline.transform(X_new)` on an already-fitted pipeline currently can't work for any of these steps since `transform()` doesn't exist yet.

### Dict output vs array output (research flag b) — explicit user decision
- **D-03:** `WindowedRollingDistance`, `InfoDynamics`, and `MultiscaleInfoDynamics` move to match `Scalogram`/`FooteNovelty`'s existing pattern: `transform()`/`fit_transform()` return a single array, with the full rich dict preserved as a fitted attribute (`self.signal_` / `self.result_`) for anyone who wants the structured output. This makes every estimator's output uniformly Pipeline-chainable and stops the codebase's two existing output conventions (array-returning vs dict-returning) from diverging further.
- **Left to planner/researcher:** the exact "primary array" shape for estimators with more than one natural output.
  - `WindowedRollingDistance`: novelty/transience/resonance are three equally-weighted signals (per PROJECT.md's own framing) — a stacked array (e.g. shape `(n_chunks, 3)` or `(3, n_chunks)`) is more defensible than picking one and demoting the other two to attribute-only, but this is an implementation detail, not a locked decision.
  - `MultiscaleInfoDynamics`: has four heterogeneous outputs (SSM, scalogram matrix, Foote novelty matrix, descriptors dict) with no single obvious "the array" the way `Scalogram`/`FooteNovelty` each have one canonical matrix. Planner should pick based on what ROADMAP's Pipeline composition test (criterion 4) actually needs downstream, or note that `MultiscaleInfoDynamics` may be legitimately Pipeline-terminal (its transform() output not consumed by anything further) despite D-02's "every estimator gets transform()" rule — D-02 is about satisfying API-01's contract test (`clone()`, `get_params`), not about every output needing to chain into another step.

### Convenience wrapper (research flag c) — explicit user decision
- **D-04:** Add `infodynamics.text.TextInfoDynamics` (and a multiscale counterpart, e.g. `TextMultiscaleInfoDynamics`) this phase. Thin wrappers composing `TextSegmenter → Encoder → InfoDynamics` / `TextSegmenter → Encoder → MultiscaleInfoDynamics` internally, so the one-call `fit_transform(text)` convenience isn't lost once `InfoDynamics`/`MultiscaleInfoDynamics` go ndarray-only. Lives under `infodynamics.text` (not core) since it's text-specific sugar over the modality-agnostic core, consistent with PROJECT.md's "text as a first-class but separable on-ramp" framing.
- Not scope creep: this is one of the ROADMAP's own three research-flagged questions for this phase, not a new capability invented mid-discussion.

### Known bugs and test debt (QA-02, QA-03) — already fully specified, not a gray area
- `averaging_weigts` → `averaging_weights` rename in `WindowedRollingDistance`.
- `WindowedRollingDistance.__init__` currently resolves `measure` (string → callable via `DISTANCES` lookup) and raises `AttributeError` on invalid values inside `__init__` itself — this breaks the sklearn "store params verbatim" contract needed for `get_params`/`set_params`/`clone`. Move measure resolution/validation into `fit()`; `__init__` must store `self.measure = measure` verbatim.
- `embedding.py`'s `_MODEL_CACHE` is keyed only by `model_name`; `Encoder.encode()` calls `model.to(self.device)` on the shared cached model in place — a second `Encoder` instance with a different `device` mutates the model out from under any other instance using it. Key the cache by `(model_name, device)` and stop the in-place `.to()` mutation.
- `_validate_data` in `WindowedRollingDistance` is marked "UNFINISHED" — only handles list-of-lists → ndarray; needs completing (see incomplete branches / hypothesis test `test_validate_data_hypothesis`).
- Test debt: `test_transience_calculation` is an empty `pass` stub; `test_negative_values_in_input_data` and `test_very_small_numbers` don't exist yet (per REQUIREMENTS.md QA-03) — implement them. `test_window_size` in `tests/test_infodynamics_class.py` asserts a shape (`(len(X) - window_size + 1, window_size)`) that doesn't match `WindowedRollingDistance`'s actual output shape (`N_hat` is always `(len(X),)`) — this is the confirmed pre-existing bug noted in STATE.md; correct the assertion, don't change the implementation to match the wrong assertion.
- Each bug fix is its own labeled commit with a deliberate, explained golden-snapshot update (per ROADMAP criterion 5) — separate from any pure API-shape-change commits from D-01–D-04.

### Claude's Discretion
User delegated the TextSegmenter I/O contract (D-01) and transform() semantics (D-02) fully to Claude's judgment — both captured above with rationale. Any remaining mechanical details (exact commit granularity/ordering among the D-01–D-04 changes and the QA-02/QA-03 bug fixes, precise stacking convention for multi-output arrays per D-03) are Claude's discretion at plan time, as long as: (1) bug-fix commits stay separate and labeled per ROADMAP criterion 5, (2) the golden-output baseline is re-verified and any deliberate drift is explained, (3) `tests/test_pipeline_composition.py` (ROADMAP criterion 4) passes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase & milestone scope
- `.planning/ROADMAP.md` §"Phase 3: Decouple the Pipeline" — goal, 5 success criteria, requirements mapping, and the "Research flag" paragraph (the three open questions this discussion resolved as D-01/D-02/D-03/D-04)
- `.planning/REQUIREMENTS.md` — CORE-02, TEXT-02, API-01, API-02, QA-02, QA-03 (this phase's requirements, with QA-02/QA-03's exact bug/test list)
- `.planning/PROJECT.md` — constraints (refactor not rewrite, sklearn Pipeline-composability as hard design constraint, no numerical drift, no back-compat shims)

### Codebase structure
- `.planning/codebase/STRUCTURE.md` — current file layout, naming conventions
- `.planning/codebase/ARCHITECTURE.md` — component responsibilities, data flow

### Prior phase context (relevant coupling this phase resolves)
- `.planning/phases/02-reorganize-into-core-text-on-ramp/02-CONTEXT.md` — D-01/D-02 there documented `pipeline.py`'s interim, still-live `segment()`/`Encoder.encode()` calls as a deliberate exception "resolved in Phase 3" — this phase is that resolution.

### Existing code (verified during this discussion, not yet reflected in codebase/ docs)
- `infodynamics/pipeline.py` — `InfoDynamics.fit()`/`MultiscaleInfoDynamics.fit()` currently call `segment()` and `Encoder.encode()`/`.encode()` directly; both currently accept `text: str` as their `fit`/`fit_transform` input and return dicts. This is exactly what CORE-02/success-criterion-1 removes.
- `infodynamics/time_series.py` — `WindowedRollingDistance.__init__` resolves/validates `measure` inline (breaks sklearn param-verbatim contract); `_validate_data` is explicitly marked "UNFINISHED"; only `fit()`/`fit_transform()` exist, no `transform()`.
- `infodynamics/scalogram.py` — `Scalogram`/`FooteNovelty` already return plain arrays (`matrix_`/`novelty_`) from `fit_transform()`, the pattern D-03 generalizes to the dict-returning estimators — but neither currently has a standalone `transform()` either (D-02 applies to them too).
- `infodynamics/text/embedding.py` — `Encoder` is a plain class (no `BaseEstimator`/`TransformerMixin`, no `fit`/`transform`/`get_params`/`set_params`), only has `.encode()`. `_MODEL_CACHE: Dict[str, object]` keyed by `model_name` only — the QA-02 in-place-mutation bug.
- `infodynamics/text/morphology.py` — `MorphologicalEncoder` is also a plain class with only `.encode()`, same gap as `Encoder`. Its own `_PIPELINE_CACHE` is already correctly keyed by `(lang, feature_group, model_path)` — not part of the bug, don't touch.
- `infodynamics/text/segmentation.py` — `segment()` (module function, unchanged) returns `List[Chunk]` (dataclass: `text`, `start`, `end`). No `TextSegmenter` class exists yet — build it here (TEXT-02).
- `infodynamics/clustering/cluster.py` — `SignalClusterer` is already a clean reference example: stores params verbatim in `__init__`, `BaseEstimator`/`ClusterMixin`, no bugs found. Not in scope for changes, useful as the "what good already looks like" pattern.
- `tests/test_infodynamics_class.py` — houses the QA-03 test debt (`test_transience_calculation` stub, `test_window_size` wrong assertion, `_validate_data` hypothesis tests).
- `tests/golden/capture_baseline.py` — currently calls `InfoDynamics(...).fit_transform(text)` and `MultiscaleInfoDynamics(...).fit_transform(text)` directly with raw text. Once `fit`/`fit_transform` go ndarray-only (CORE-02), this capture script's calls must change to build the segment→encode→analyze chain explicitly (or use the new `TextInfoDynamics`/`TextMultiscaleInfoDynamics` wrapper from D-04) before re-capturing the golden snapshot.
- No `tests/test_pipeline_composition.py` exists yet — ROADMAP success criterion 4 requires creating it.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `infodynamics/clustering/cluster.py`'s `SignalClusterer` — clean sklearn-compatible reference (verbatim `__init__` params, proper mixins) to model the fixed `WindowedRollingDistance`/new `TextSegmenter`/`Encoder`/`MorphologicalEncoder` after.
- `infodynamics/pipeline.py`'s existing `self.chunks_ = chunks` fitted-attribute pattern — directly reusable for `TextSegmenter.chunks_` per D-01.
- Lazy heavy-import pattern already established in `embedding.py`/`morphology.py`/`clustering/barycenter.py` — preserve as-is; TEXT-02's new `fit`/`transform` wrappers around `Encoder`/`MorphologicalEncoder` must not force heavy imports at class-definition time.

### Established Patterns
- Two competing output conventions currently coexist: dict-returning (`WindowedRollingDistance`, `InfoDynamics`, `MultiscaleInfoDynamics`) vs array-returning-with-rich-attributes (`Scalogram`, `FooteNovelty`). D-03 converges on the latter.
- `fit_transform()` is currently hand-written per class (calls `self.fit(X)` then returns an attribute) rather than relying on `TransformerMixin`'s default `fit(X).transform(X)` composition. Once real `transform()` methods exist (D-02), planner should decide whether to keep explicit `fit_transform()` overrides or drop them in favor of the mixin default — either is fine as long as output matches D-03.

### Integration Points
- `infodynamics/__init__.py` re-exports `WindowedRollingDistance`, `InfoDynamics`, `MultiscaleInfoDynamics`, `Scalogram`, `FooteNovelty` at top level already — new `TextSegmenter` (and D-04's `TextInfoDynamics`/`TextMultiscaleInfoDynamics`) need equivalent re-export decisions, but curating `__all__` is explicitly Phase 4's job (API-03) — just make the new symbols importable from sensible locations (`infodynamics.text`) this phase, don't design the final curated surface yet.
- `tests/golden/capture_baseline.py` is the one place that will need updating to keep exercising `InfoDynamics`/`MultiscaleInfoDynamics` end-to-end once their `fit()` signature changes — golden re-verification depends on this.

</code_context>

<specifics>
## Specific Ideas

No specific UI/behavioral requirements (internal library API design phase). The three ROADMAP "Research flag" questions were the specific, named things the user wanted resolved before planning — all captured as D-01/D-02/D-03/D-04 above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. The convenience-wrapper decision (D-04) and TextSegmenter contract (D-01) were both explicitly anticipated by the ROADMAP's own research flag for this phase, not scope creep introduced mid-discussion.

</deferred>

---

*Phase: 3-Decouple the Pipeline*
*Context gathered: 2026-07-14*

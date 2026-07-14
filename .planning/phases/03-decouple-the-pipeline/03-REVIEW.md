---
phase: 03-decouple-the-pipeline
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - infodynamics/pipeline.py
  - infodynamics/scalogram.py
  - infodynamics/text/__init__.py
  - infodynamics/text/embedding.py
  - infodynamics/text/morphology.py
  - infodynamics/text/pipeline.py
  - infodynamics/text/segmentation.py
  - infodynamics/time_series.py
  - tests/golden/capture_baseline.py
  - tests/test_infodynamics_class.py
  - tests/test_pipeline.py
  - tests/test_pipeline_composition.py
  - tests/text/test_morphology.py
findings:
  critical: 0
  warning: 11
  info: 3
  total: 14
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Reviewed the core `InfoDynamics`/`MultiscaleInfoDynamics`/`WindowedRollingDistance`/`Scalogram`/`FooteNovelty`
estimators, the new `infodynamics.text` on-ramp (segmentation, embedding, morphology, wrapper pipelines),
and the associated tests/golden-baseline harness for phase 03 ("decouple the pipeline"). No critical/security
issues were found — no injection vectors, no hardcoded secrets, no eval/exec usage, and the module boundary
between core (`infodynamics/`) and text (`infodynamics/text/`) is clean with no circular imports.

The main defects found are: (1) missing lower-bound input validation on `scales`/`radii`/`window_size`
parameters that silently produces NaN-filled arrays or crashes with opaque low-level numpy errors instead of
a clear `ValueError`, (2) an inconsistency where `_resolve_measure` raises `AttributeError` for an invalid
`measure` instead of the `ValueError` the project's documented error-handling convention calls for, (3) a
`strip_markdown` regex that silently corrupts non-markdown prose containing underscores/asterisks (snake_case
identifiers, math notation) rather than only stripping true emphasis markers, and (4) substantial, literal
duplication of `transform()`/`fit_transform()` method bodies across nearly every estimator in these files,
which is a real maintenance/drift risk (a future bug fix applied to one and not the other silently diverges).
None of these are hit by the shipped default configuration/tests, but all are reachable by a caller using the
public API with otherwise-reasonable inputs.

## Warnings

### WR-01: `Scalogram`/`FooteNovelty` don't validate that scales/radii are positive

**File:** `infodynamics/scalogram.py:107` (Scalogram.fit) and `infodynamics/scalogram.py:224` (FooteNovelty.fit)
**Issue:** The scale/radius filters only enforce an *upper* bound (`w < embeddings.shape[0]`, `2 * r + 1 <=
S.shape[0]`); they don't exclude `0` or negative values. Concretely:
- `Scalogram` with `scale=0` (or negative): in `rolling_gap_distance` (lines 55-67), `past`/`future` slices
  become empty for every position (`embeddings[i:i]`), so `distance` stays `np.full(n, np.nan)` for the
  *entire* row — `valid` is empty, so the edge-fill logic (lines 63-66) never runs and the NaN silently
  propagates into `Scalogram.matrix_` and `MultiscaleInfoDynamics.scalogram_`.
- `FooteNovelty` with `radius=0`: `checkerboard_kernel(0)` (lines 151-157) computes `sigma = 0`, so
  `gaussian = exp(-(X**2+Y**2) / (2 * 0**2))` divides by zero, producing `nan` (numpy emits a RuntimeWarning
  and continues). The resulting kernel/novelty row is all-NaN.
- `FooteNovelty` with `radius=-1`: passes the filter (`2*(-1)+1 = -1 <= n` is always true), then
  `checkerboard_kernel(-1)` produces an *empty* kernel (`np.arange(1, 0)` is empty), and `foote_novelty`'s
  `np.pad(S, radius, mode="edge")` (line 179) is called with a **negative** pad width, which raises an
  unhandled, low-level numpy exception instead of a clear validation error.

**Fix:**
```python
# Scalogram.fit
scales = [w for w in self.scales if 0 < w < embeddings.shape[0]]

# FooteNovelty.fit
radii = [r for r in self.radii if 0 < r and 2 * r + 1 <= S.shape[0]]
```

### WR-02: `_resolve_measure` raises the wrong exception type

**File:** `infodynamics/scalogram.py:20-26`
**Issue:** `_resolve_measure` raises `AttributeError` for an unrecognized `measure` value:
```python
def _resolve_measure(measure: Union[str, Callable]) -> Callable:
    if measure in DISTANCES:
        return DISTANCES[measure]
    elif callable(measure):
        return measure
    else:
        raise AttributeError(f"Invalid value for parameter 'measure': {measure}")
```
This contradicts the project's own documented error-handling convention ("`ValueError` raised for invalid
parameter values") and is inconsistent with every other parameter-validation error in this codebase (e.g.
`segment()`'s `chunk_size` check, `MorphologicalEncoder`'s `feature_group` check, `_base_spans`'s `level`
check all raise `ValueError`). Callers who correctly `except ValueError` to catch bad `measure` strings will
not catch this.
**Fix:**
```python
raise ValueError(f"Invalid value for parameter 'measure': {measure}")
```

### WR-03: `averaging_weights` only weights the mean, not the reported standard deviation

**File:** `infodynamics/time_series.py:56-61`
**Issue:**
```python
def _summarize_tmp(self, tmp: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if self.averaging_weights is not None:
        return np.average(tmp, weights=self.averaging_weights, axis=0), np.std(tmp)
    else:
        return np.mean(tmp), np.std(tmp)
```
When `averaging_weights` is supplied to emphasize e.g. more recent observations, the mean (`N_hat`/`T_hat`)
correctly reflects the weighting, but the paired standard deviation (`N_sd`/`T_sd`, only surfaced when
`estimate_error=True`) always uses the plain, unweighted `np.std(tmp)`. This is an internally inconsistent
uncertainty estimate: the reported "spread" doesn't correspond to the reported "center."
**Fix:** Either compute a weighted standard deviation (e.g. via a weighted variance formula) or document
explicitly that `*_sd` ignores `averaging_weights`.

### WR-04: No validation that `window_size`/`jump_size` are non-negative

**File:** `infodynamics/time_series.py:15-54` (constructor), `infodynamics/time_series.py:92-128` (`calc_signal`)
**Issue:** `WindowedRollingDistance.__init__` stores `window_size`/`jump_size` without any bounds check. A
negative `window_size` is not rejected at construction; it instead surfaces deep inside `calc_signal` as an
opaque numpy error: when `submat.shape[0] != self.window_size`, the fallback branch does
`np.full([self.window_size], self.inplace_constant)` (line 124), and `np.full` with a negative shape raises
`ValueError: negative dimensions are not allowed` with no indication of which parameter caused it. This
applies transitively to `InfoDynamics`/`MultiscaleInfoDynamics`, which pass `window_size` straight through
without validating it either.
**Fix:** Validate in `__init__` (matching the project convention already used for `chunk_size`):
```python
if window_size < 0:
    raise ValueError(f"'window_size' must be >= 0, got {window_size}.")
```

### WR-05: Dead, commented-out code left in `_calc_resonance`

**File:** `infodynamics/time_series.py:138-141`
**Issue:**
```python
# invalidate the signal outside of window bounds
# R_hat[: self.window_size] = np.zeros([self.window_size], dtype=float) + self.inplace_constant
# R_hat[-self.window_size :] = np.zeros([self.window_size], dtype=float) + self.inplace_constant
# R_sd[: self.window_size] = np.zeros([self.window_size], dtype=float) + self.inplace_constant
# R_sd[-self.window_size :] = np.zeros([self.window_size], dtype=float) + self.inplace_constant
```
Commented-out code left in a "decoupled" module makes it unclear whether this is intentionally abandoned
logic or an accidental omission (the surrounding `# TODO consider turning this off for jump calculations` at
line 168 compounds the ambiguity).
**Fix:** Remove the dead code, or if it documents a real, deliberately-deferred behavior change, replace it
with a tracked issue reference and a one-line explanation instead of raw commented-out code.

### WR-06: `strip_markdown`'s emphasis-stripping regex corrupts non-markdown text

**File:** `infodynamics/text/segmentation.py:27`
**Issue:**
```python
text = re.sub(r"[*_]{1,3}", "", text)  # bold/italic markers
```
This strips *any* run of 1-3 `*`/`_` characters anywhere in the text, not just paired markdown emphasis
markers. For prose that legitimately contains underscores or asterisks outside of markdown emphasis — e.g.
`snake_case` identifiers, filenames (`my_file.py`), math notation (`x_1`, `a*b`) — this silently deletes the
character and merges the surrounding text (`"the my_var setting"` becomes `"the myvar setting"`), changing
the meaning of the segmented chunk rather than just removing formatting.
**Fix:** Require the emphasis markers to be paired/word-boundary-anchored, e.g.:
```python
text = re.sub(r"(?<!\w)[*_]{1,3}(?=\S)|(?<=\S)[*_]{1,3}(?!\w)", "", text)
```
or use a proper markdown-emphasis regex (`\*\*(.+?)\*\*`, `\*(.+?)\*`, `_(.+?)_`, etc.) that only strips
matched marker *pairs*.

### WR-07: `_spans_from_parts` has no error handling for a failed `text.index()` lookup

**File:** `infodynamics/text/segmentation.py:58-66` (used by `_sentence_parts`/`_paragraph_parts` via `_base_spans`)
**Issue:**
```python
def _spans_from_parts(text: str, parts: List[str]) -> List[Tuple[int, int]]:
    spans = []
    cursor = 0
    for part in parts:
        start = text.index(part, cursor)   # <-- raises ValueError if not found
        end = start + len(part)
        spans.append((start, end))
        cursor = end
    return spans
```
This assumes the reconstructed sentence/paragraph text (`part`) is always a literal, verbatim substring of
`text` starting at or after `cursor`. If syntok's tokenizer normalizes any character during reconstruction
(e.g. smart quotes, non-breaking spaces, unusual whitespace runs) such that the joined string no longer
matches the original text byte-for-byte, `text.index` raises an uncaught `ValueError` with no context (no
indication of which part/position failed), crashing `TextSegmenter.fit()`/`segment()` entirely instead of
degrading gracefully or surfacing an actionable error.
**Fix:** Wrap the lookup and re-raise with context, e.g.:
```python
try:
    start = text.index(part, cursor)
except ValueError as e:
    raise ValueError(f"Could not locate segmented part in source text near offset {cursor}: {part[:50]!r}") from e
```

### WR-08: `model_name`/`encoder` mutual exclusivity is not validated

**File:** `infodynamics/text/pipeline.py:105-119` (`TextInfoDynamics.fit`) and `infodynamics/text/pipeline.py:267-281` (`TextMultiscaleInfoDynamics.fit`)
**Issue:** Both wrappers check that *at least one* of `model_name`/`encoder` is given:
```python
if self.encoder is None and self.model_name is None:
    raise ValueError("One of 'model_name' or 'encoder' is required.")
...
encoder = (
    self.encoder
    if self.encoder is not None
    else Encoder(self.model_name, device=self.device, batch_size=self.batch_size)
)
```
but never checks the case where *both* are supplied. If a caller passes both (e.g. leftover `model_name`
from a previous config while also passing a custom `encoder`), `model_name` is silently ignored with no
warning — a likely source of "why isn't my model_name being used" confusion in downstream tuning code
(e.g. sklearn `GridSearchCV` over `model_name` while `encoder` happens to also be set).
**Fix:** Either raise a `ValueError` when both are provided, or `warnings.warn()` that `model_name` is
ignored when `encoder` is also set (per this project's documented `warnings.warn()` convention for
non-fatal issues).

### WR-09: `structure_descriptors` crashes with an opaque numpy error for tiny inputs

**File:** `infodynamics/scalogram.py:248-277`
**Issue:** `structure_descriptors` computes `off_diagonal = S[np.triu_indices_from(S, k=1)]` and then calls
`off_diagonal.mean()` / `np.quantile(off_diagonal, 0.9)` unconditionally. For `n_chunks <= 1`, `S` is
`(1, 1)` or `(0, 0)`, `off_diagonal` is empty, and `np.quantile` on an empty array raises
`IndexError`/`ValueError` deep inside numpy rather than a clear, actionable error. `MultiscaleInfoDynamics`
happens to avoid this in practice because `Scalogram.fit()` raises first for default scales on such tiny
inputs — but `structure_descriptors` is a public, standalone function (`from infodynamics import
structure_descriptors`) that can be called directly on a too-small `embeddings` array without going through
`MultiscaleInfoDynamics` at all.
**Fix:** Validate `embeddings.shape[0] >= 2` (or `S.shape[0] >= 2`) at the top of `structure_descriptors` and
raise a clear `ValueError`.

### WR-10: Systematic duplication of `transform()`/`fit_transform()` bodies

**File:** `infodynamics/pipeline.py:92-150` (InfoDynamics), `infodynamics/pipeline.py:223-267`
(MultiscaleInfoDynamics), `infodynamics/scalogram.py:120-129` (Scalogram), `infodynamics/scalogram.py:236-245`
(FooteNovelty), `infodynamics/time_series.py:197-245` (WindowedRollingDistance),
`infodynamics/text/pipeline.py:134-180` (TextInfoDynamics), `infodynamics/text/pipeline.py:301-344`
(TextMultiscaleInfoDynamics)
**Issue:** In every one of these classes, `transform()` and `fit_transform()` have **literally identical**
bodies (same `self.fit(X)` call, same return expression), differing only in docstring. E.g.
`infodynamics/pipeline.py`:
```python
def transform(self, X, y=None) -> np.ndarray:
    self.fit(X)
    return np.column_stack([...])

def fit_transform(self, X, y=None) -> np.ndarray:
    self.fit(X)
    return np.column_stack([...])   # identical to transform()
```
This is copy-pasted seven times across these files. Any future bug fix or behavior change (e.g. adding a
new signal key, changing the returned shape) has to be made in two places per class, and it's easy to update
one and silently miss the other, causing `transform()` and `fit_transform()` to drift apart.
**Fix:** Have one call the other:
```python
def fit_transform(self, X, y=None) -> np.ndarray:
    return self.transform(X)
```
(safe here since `transform()` already performs a full `fit()` internally per the documented "recompute
fresh" design).

### WR-11: `time_series.py` imports a leading-underscore "private" helper across module boundaries

**File:** `infodynamics/time_series.py:11`
**Issue:**
```python
from infodynamics.scalogram import _resolve_measure
```
Per this project's own naming convention ("Leading underscore for private/internal functions"),
`_resolve_measure` is scalogram.py-internal. `time_series.py` (a sibling module with no other coupling to
`scalogram.py`) reaching into it for a "private" symbol is a module-boundary smell: it signals that
`_resolve_measure` is really a shared utility (alongside `DISTANCES`/`cos_sim` in `metrics.py`) that happens
to have been placed in the wrong module, and risks silent breakage if `scalogram.py` ever renames/removes it
without realizing an external module depends on it.
**Fix:** Move `_resolve_measure` to `infodynamics/metrics.py` (next to `DISTANCES`) and have both
`scalogram.py` and `time_series.py` import it from there as a public, intentionally-shared utility.

## Info

### IN-01: `infodynamics.text` doesn't export `Encoder`/`MorphologicalEncoder`

**File:** `infodynamics/text/__init__.py:1-6`
**Issue:** Only `TextInfoDynamics`, `TextMultiscaleInfoDynamics`, and `TextSegmenter` are re-exported; a
caller must know to import `from infodynamics.text.embedding import Encoder` /
`from infodynamics.text.morphology import MorphologicalEncoder` directly (as the tests do). The module
docstring notes this is deliberately deferred to a later phase, so this is informational only, not a defect.
**Fix:** N/A for this phase — flagged for awareness ahead of the deferred `__all__` curation phase.

### IN-02: `MorphologicalEncoder.__init__` validates eagerly, unlike sibling estimators

**File:** `infodynamics/text/morphology.py:180-181`
**Issue:**
```python
if feature_group not in self.FEATURE_GROUPS:
    raise ValueError(f"'feature_group' must be one of {self.FEATURE_GROUPS}, got {feature_group!r}.")
```
runs inside `__init__`, whereas every comparable estimator in this codebase (`TextSegmenter`/`segment()`,
`Scalogram`, `FooteNovelty`) defers equivalent validation to `fit()`. Eager constructor validation is a
mild deviation from scikit-learn's stated convention that `__init__` should only assign attributes, and from
this codebase's own established pattern elsewhere.
**Fix:** Consider moving the check into `fit()`/`encode()` for consistency, though note current tests
(`test_invalid_feature_group_raises`) exercise the current (constructor-time) behavior and would need
updating if changed.

### IN-03: `rolling_gap_distance` docstring overstates the edge-fill behavior

**File:** `infodynamics/scalogram.py:32-36`
**Issue:** The docstring states "Positions where a full window doesn't fit (near the edges) are filled with
the nearest valid value," but the implementation only does this for positions where *one side is completely
empty* (e.g. `i=0`). Positions with a partial-but-nonempty window on one side (e.g. `i=1` with
`window_size=3`) compute a genuine (if asymmetric) distance rather than being "filled" — the mean is taken
over fewer elements on the short side, not backfilled from a neighboring position.
**Fix:** Clarify the docstring, e.g. "positions with a completely empty past or future window are filled
with the nearest valid computed value; positions with a partial window compute the distance over
however-many elements are available on each side."

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---
phase: 04-curate-the-public-api
reviewed: 2026-07-14T15:30:09Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - examples/basic_usage.py
  - infodynamics/__init__.py
  - infodynamics/text/__init__.py
  - tests/test_public_api.py
  - tests/text/test_morphology.py
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-07-14T15:30:09Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

This phase curates the public export surface of `infodynamics` (explicit `__all__` for both the core package root and `infodynamics.text`), adds a canonical runnable example (`examples/basic_usage.py`), and adds/locks a contract test (`tests/test_public_api.py`). Cross-checked against the phase plans (`04-01-PLAN.md`, `04-02-PLAN.md`) and against the called modules (`infodynamics/pipeline.py`, `infodynamics/text/pipeline.py`, `infodynamics/text/embedding.py`, `infodynamics/text/segmentation.py`, `infodynamics/text/morphology.py`, `infodynamics/clustering/*`) to verify the D-05 "zero `.text` import in core" invariant actually holds transitively (confirmed via `grep`, not just the substring test) and that no optional heavy dependency (`sentence-transformers`, `spacy_udpipe`, `textdescriptives`, `tslearn`) is imported at module-import time anywhere in the curated surface.

Both `__init__.py` files match their approved PATTERNS.md target content exactly. `examples/basic_usage.py` was executed end-to-end during this review (`.venv/bin/python examples/basic_usage.py`) and exits 0, printing the expected shapes for both the core-only and full-Pipeline paths. `tests/test_public_api.py` and `tests/text/test_morphology.py` were run directly (`pytest tests/test_public_api.py tests/text/test_morphology.py -q`) — 10 passed.

No correctness bugs, security issues, or contract violations were found in the reviewed files. The findings below are minor test-reliability and documentation-consistency nits.

## Warnings

### WR-01: `FakeNlp.pipe()` mock ignores its `texts` argument, weakening two tests' ability to catch argument-forwarding regressions

**File:** `tests/text/test_morphology.py:21-22`
**Issue:** `FakeNlp.pipe(self, texts): return iter(self._docs)` completely discards the `texts` parameter and always yields the same fixed 2-doc list regardless of what is passed in. `test_encode_returns_matrix_with_feature_names` and `test_encode_all_feature_groups_returns_matrix_and_names_per_group` both assert `matrix.shape == (2, ...)` against a hardcoded literal `2` — the same `2` that `FakeNlp` returns unconditionally. If `MorphologicalEncoder.encode`/`encode_all_feature_groups` ever failed to correctly pass `texts` through to `nlp.pipe(texts)` (e.g. passed an empty list, the wrong variable, or a differently-sized batch), these tests would still pass, because the mock's output is decoupled from its input entirely. This reduces the tests' value as a regression guard for the input->output wiring, even though they do correctly validate the POS-proportions feature-name/zero-fill behavior downstream of that call.
**Fix:** Make the fake responsive to its input so a wiring bug would surface, e.g.:
```python
class FakeNlp:
    def __init__(self, docs):
        self._docs = docs

    def pipe(self, texts):
        texts = list(texts)
        assert len(texts) == len(self._docs), (
            f"expected {len(self._docs)} texts, got {len(texts)} — "
            "check that encode()/encode_all_feature_groups() forward `texts` unchanged"
        )
        return iter(self._docs)
```

## Info

### IN-01: Blank module docstring in `tests/text/test_morphology.py`

**File:** `tests/text/test_morphology.py:1`
**Issue:** The module docstring is a literal empty string (`""" """`), providing no description of what the test module covers. CLAUDE.md conventions call for module-level docstrings ("present in most files, sometimes minimal") — this one is present but contentless.
**Fix:**
```python
"""Tests for infodynamics.text.morphology: MorphologicalEncoder,
encode_all_feature_groups, and TextMultiscaleInfoDynamics composed with a
custom (morphological) encoder."""
```

### IN-02: `infodynamics/__init__.py` has no module docstring, unlike its sibling `infodynamics/text/__init__.py`

**File:** `infodynamics/__init__.py:1`
**Issue:** This phase added an explicit `__all__` to both package roots and gave `infodynamics/text/__init__.py` a one-line descriptive docstring (`"infodynamics.text — text on-ramp (segmentation, embedding, morphological encoding)."`), but `infodynamics/__init__.py` — the primary public entry point whose export surface this phase exists to curate — still has no docstring at all. This is consistent with the approved PATTERNS.md target content (not a deviation introduced during execution), but it is an inconsistency worth closing now that both files are being hand-curated in the same phase: a user running `help(infodynamics)` gets nothing, while `help(infodynamics.text)` gets a one-liner.
**Fix:**
```python
"""infodynamics — modality-agnostic novelty/structure analysis core
(InfoDynamics, MultiscaleInfoDynamics, clustering). See infodynamics.text
for the text on-ramp (segmentation, embedding, morphological encoding)."""
__version__ = "0.1.0"
```

### IN-03: `FakeMorphologicalEncoder` name overstates what the stub does

**File:** `tests/text/test_morphology.py:78-86`
**Issue:** `FakeMorphologicalEncoder` is a generic random-embedding stub (`rng.normal(size=(len(texts), 5))`) with no relationship to morphological/POS features — it stands in for *any* encoder satisfying `TextMultiscaleInfoDynamics(encoder=...)`'s duck-typed `.encode()` contract, not specifically for `MorphologicalEncoder`'s behavior. The class's own docstring ("Deterministic stand-in, avoids depending on a real UDPipe model in the pipeline test") clarifies intent, but the class name suggests it fakes `MorphologicalEncoder`'s semantics (POS proportions etc.), which it does not.
**Fix:** Rename to something scoped to its actual role, e.g. `FakeEncoder` or `RandomEncoderStub`, to avoid a reader assuming it exercises morphology-specific logic.

---

_Reviewed: 2026-07-14T15:30:09Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

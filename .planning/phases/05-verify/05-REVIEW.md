---
phase: 05-verify
reviewed: 2026-07-14T17:30:58Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - infodynamics/text/morphology.py
  - tests/text/test_morphology.py
  - .github/workflows/ci.yml
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-07-14T17:30:58Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the phase's one real source change (`infodynamics/text/morphology.py`'s guarded
`textdescriptives` import in `MorphologicalEncoder.encode()`), its regression test file, and the
new bonus CI workflow. The guarded-import fix itself is correct and matches the file's three
existing sibling guards byte-for-byte, and the new regression test exercises it via
`monkeypatch.setitem(sys.modules, "textdescriptives", None)` without needing a network/model
download — that part of the phase does what it claims.

The most consequential finding is cross-file: the new CI workflow installs `pip install .[test]`,
but `setup.py`'s `test` extra does **not** include the `morphology` extra (`textdescriptives`,
`spacy-udpipe`), and none of `test`'s other extras (`sentence-transformers`, `tslearn`, `scipy`)
pull those packages in transitively (verified via `pip show`). `tests/text/test_morphology.py`
gates its entire module on `pytest.importorskip("spacy")` / `pytest.importorskip("textdescriptives")`
(lines 7-8), so on a genuinely fresh CI runner every test in this file — including the new
regression test this phase just added — is silently skipped, not run. CI will report green while
never having executed the code this phase touched. Since this phase's stated purpose is empirical
verification (QA-04: "the full pytest suite passes"), and the CI workflow's own plan explicitly
claimed the `test` extra is "self-sufficient" for the suite, this is a real gap between what the
CI workflow appears to guarantee and what it actually exercises.

Beyond that, `morphology.py` has a few smaller robustness/quality issues: a broad `except Exception`
in the UDPipe-download fallback that violates the project's own documented `raise ... from e`
convention, silent (unwarned) dropping of non-numeric feature columns, and repeated
(copy-pasted) `ImportError` guard blocks that would need to be kept in sync by hand.

## Warnings

### WR-01: CI's `.[test]` extra never installs the deps `tests/text/test_morphology.py` needs, so those tests silently skip on every CI run

**File:** `.github/workflows/ci.yml:17` (root cause also touches `setup.py`'s `extras_require['test']`, not in review scope but load-bearing context)
**Issue:** `pip install .[test]` installs `pytest`, `hypothesis`, `sentence-transformers`, `tslearn`, and `scipy` (per `setup.py`'s `extras_require['test']` union), but never `textdescriptives` or `spacy-udpipe` (the `morphology` extra). Confirmed none of those packages pull `spacy`/`spacy_udpipe`/`textdescriptives` in transitively:
```
sentence-transformers requires: huggingface-hub, numpy, scikit-learn, scipy, torch, tqdm, transformers, typing_extensions
tslearn requires: joblib, numba, numpy, scikit-learn, scipy, statsmodels
```
`tests/text/test_morphology.py` starts with:
```python
spacy = pytest.importorskip("spacy")
pytest.importorskip("textdescriptives")
```
On a fresh `ubuntu-latest` runner (no pre-existing venv with these packages, unlike this local dev environment where they happen to already be installed), both `importorskip` calls raise `Skipped` at collection time, and **every test in the file — including the regression test this phase's Plan 01 added for the `encode()` ImportError guard — never executes.** `pytest -q` will report these as skipped (visible as `s` in the summary, non-failing), so the workflow still shows green. This directly undermines the phase's own QA-04 criterion ("the full pytest suite passes") — the suite reports success without ever running the morphology code path this phase modified.
**Fix:** Either install the morphology extra in CI, or explicitly document/accept the skip. The cheapest fix that keeps the CI workflow useful for this phase's own regression test:
```yaml
      - name: Install
        run: pip install .[test,morphology]
```
If keeping CI deliberately minimal (per D-07's "non-gating, smoke-level" framing) is a hard constraint, at minimum add a comment in `ci.yml` noting that morphology tests are skipped in this workflow, so a future reader doesn't mistake a green run for morphology coverage.

### WR-02: Broad `except Exception` in `_load_udpipe` masks the real failure and loses the original traceback

**File:** `infodynamics/text/morphology.py:77-81`
**Issue:**
```python
try:
    return spacy_udpipe.load(lang)
except Exception:
    spacy_udpipe.download(lang)
    return spacy_udpipe.load(lang)
```
This catches *any* exception from `spacy_udpipe.load(lang)` — not just "model not downloaded yet" — and unconditionally attempts a re-download. If the real failure is something else (corrupted local cache, disk-full, permission error, invalid `lang` code), the code silently retries a network download instead of surfacing the actual problem, and if the second `load(lang)` call also fails, the exception raised has no `from e` chain back to the original error. This violates the project's own documented error-handling convention ("Context provided via `from e` syntax") used consistently elsewhere in this same file (lines 42-45, 49-52, 115-118, 130-133, 197-200).
**Fix:** Narrow the catch (or at minimum preserve context):
```python
try:
    return spacy_udpipe.load(lang)
except OSError as e:  # or whatever spacy_udpipe actually raises for "not downloaded"
    try:
        spacy_udpipe.download(lang)
        return spacy_udpipe.load(lang)
    except Exception as download_err:
        raise RuntimeError(f"Failed to load or download UDPipe model for lang={lang!r}") from download_err
```

### WR-03: `_clean_feature_df` silently drops non-numeric columns with no warning

**File:** `infodynamics/text/morphology.py:25-35`
**Issue:** `df.select_dtypes(include=["number", "bool"])` silently discards any column that isn't numeric/bool dtype. The docstring only discusses the `fillna(0.0)` behavior for NaN values in kept columns, not the fact that entire columns can vanish. If a `textdescriptives` metric unexpectedly comes back as `object` dtype (e.g. a version bump changes a metric's return type, or a computation partially fails and produces mixed types), the resulting feature silently disappears from the matrix instead of surfacing an error — changing `feature_names_`/matrix width without any signal to the caller.
**Fix:** At minimum, warn when columns are dropped:
```python
def _clean_feature_df(df):
    numeric = df.select_dtypes(include=["number", "bool"])
    dropped = set(df.columns) - set(numeric.columns)
    if dropped:
        warnings.warn(f"Dropping non-numeric feature columns: {sorted(dropped)}")
    return numeric.fillna(0.0)
```
(matches the project's own `warnings.warn()` convention for non-fatal issues, per CLAUDE.md's Logging section).

## Info

### IN-01: Five near-identical `ImportError` guard blocks duplicated across the file

**File:** `infodynamics/text/morphology.py:39-45, 46-52, 112-118, 127-133, 194-200`
**Issue:** The exact same two-line message (`"The 'morphology' extra is required...pip install infodynamics[morphology]."`) is hand-copied into 5 separate `try/except ImportError` blocks. This was an intentional, byte-for-byte-consistent choice per the phase's own plan, but it means any future wording change has to be applied in 5 places by hand, and a missed one will silently drift.
**Fix:** Extract a small helper, e.g.:
```python
def _require_morphology_extra(module_name: str, exc: ImportError) -> None:
    raise ImportError(
        "The 'morphology' extra is required to use MorphologicalEncoder. "
        "Install it with `pip install infodynamics[morphology]`."
    ) from exc
```
and call it from each guard's `except ImportError as e: _require_morphology_extra(module_name, e)`.

### IN-02: Unnecessary string-quoted `"object"` forward reference in a type hint

**File:** `infodynamics/text/morphology.py:11`
**Issue:** `_PIPELINE_CACHE: Dict[Tuple[str, str, Optional[str]], "object"] = {}` quotes the builtin `object` as a forward reference, which is unnecessary since `object` is always resolvable at module load time — likely a copy-paste artifact from quoting a not-yet-defined class elsewhere.
**Fix:** `_PIPELINE_CACHE: Dict[Tuple[str, str, Optional[str]], object] = {}`

### IN-03: Empty module docstring in the test file

**File:** `tests/text/test_morphology.py:1`
**Issue:** `""" """` is a blank/whitespace-only module docstring, inconsistent with the project convention of present (if minimal) module docstrings.
**Fix:** Replace with a one-line description, e.g. `"""Tests for infodynamics.text.morphology."""`

### IN-04: No validation for empty `texts` input

**File:** `infodynamics/text/morphology.py:84-146` (`encode_all_feature_groups`), `193-208` (`MorphologicalEncoder.encode`)
**Issue:** Neither function checks for an empty `texts` list before calling `nlp.pipe(texts)` / `extract_df(...)`. Behavior on empty input is untested and unspecified — depending on `textdescriptives`' handling of a zero-row doc list, this could raise a confusing downstream error rather than a clear one from this module.
**Fix:** Add an explicit guard, e.g. `if not texts: raise ValueError("'texts' must be non-empty.")`, consistent with the project's convention of validating inputs before processing (e.g. `chunk_size < 1` in `time_series.py`).

### IN-05: `encode_all_feature_groups`'s `nlp` escape-hatch docstring omits the `attribute_ruler` prerequisite for `pos_proportions`

**File:** `infodynamics/text/morphology.py:107-110`
**Issue:** The docstring for the `nlp` parameter says a caller-supplied pipeline "must already have every `textdescriptives/{group}` in `feature_groups` added," but doesn't mention that `pos_proportions` specifically also requires a `tagger`/`attribute_ruler` pipe present first (documented only as an internal-path comment at lines 58-62). A caller using the escape hatch with `pos_proportions` who follows the docstring literally (without independently discovering the internal comment) will hit `textdescriptives`' pipe-registration error. The test's own `_make_docs()` helper gets this right, but only by mirroring the internal implementation detail rather than the public docstring.
**Fix:** Extend the `nlp` param docstring: "...must already have every `textdescriptives/{group}` added (and, for `pos_proportions`, a `tagger` or `attribute_ruler` pipe present first)."

---

_Reviewed: 2026-07-14T17:30:58Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

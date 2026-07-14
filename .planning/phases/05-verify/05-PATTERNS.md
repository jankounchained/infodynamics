# Phase 5: Verify - Pattern Map

**Mapped:** 2026-07-14
**Files analyzed:** 4 (1 bug fix, 1 new deliverable doc, 1 optional CI config, 1 possible regression test)
**Analogs found:** 3 / 4 (CI workflow has no analog in current tree — documented explicitly below, not invented)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|---------------|
| `infodynamics/text/morphology.py` (line 194 fix) | utility (optional-dependency guard) | request-response (import guard) | Same file, lines 38-52 / 112-118 / 127-133 (sibling guards) | exact — same file, same pattern, 3 existing instances |
| `.planning/phases/05-verify/05-VERIFICATION.md` | test/report (evidence transcript) | batch (audit transcript) | `.planning/phases/04-curate-the-public-api/04-VERIFICATION.md` | exact — same phase-deliverable role, same repo, most recent example |
| `.github/workflows/ci.yml` | config (CI) | event-driven (push/PR trigger) | none in current tree | no analog — confirmed absent; historical CI (commit `924d6fb`) is poetry/codecov/mkdocs-based and explicitly NOT a template (RESEARCH.md D-07 note) |
| `tests/text/test_morphology.py` (possible regression test addition) | test | request-response (raises ImportError) | Same file, `test_invalid_feature_group_raises` (lines 35-37) and module-level `pytest.importorskip` guards (lines 5-6) | exact — same file, same test style |

## Pattern Assignments

### `infodynamics/text/morphology.py` (utility, optional-dependency guard) — THE ONE REAL CODE CHANGE

**Analog:** same file, 3 sibling guarded-import sites.

**Bug location** (line 194, inside `MorphologicalEncoder.encode()`):
```python
def encode(self, texts: List[str]) -> np.ndarray:
    from textdescriptives import extract_df   # <-- UNGUARDED, line 194

    nlp = self.nlp if self.nlp is not None else _load_pipeline(self.lang, self.feature_group, self.model_path)
    docs = list(nlp.pipe(texts))

    df = _clean_feature_df(extract_df(docs, metrics=[self.feature_group], include_text=False))

    self.feature_names_ = list(df.columns)
    return df.to_numpy(dtype=float)
```
This raises a bare `ModuleNotFoundError: No module named 'textdescriptives'` instead of the project's actionable `ImportError` when the `morphology` extra isn't installed.

**Exact guarded-import pattern to copy** (lines 112-118, inside `encode_all_feature_groups`, closest sibling — same module-level `from textdescriptives import extract_df` statement, same function-body position):
```python
    try:
        import textdescriptives  # noqa: F401  (registers the textdescriptives/* spaCy factories)
    except ImportError as e:
        raise ImportError(
            "The 'morphology' extra is required to use MorphologicalEncoder. "
            "Install it with `pip install infodynamics[morphology]`."
        ) from e
    from textdescriptives import extract_df
```

**Two other sibling instances of the identical pattern** (for cross-reference, all in the same file, all raise the identical message string):
- lines 40-45 (`_load_pipeline`, guarding `import spacy_udpipe`)
- lines 46-52 (`_load_pipeline`, guarding `import textdescriptives`)
- lines 127-133 (`encode_all_feature_groups`, guarding `import spacy_udpipe`)

**Prescribed fix** — replace line 194's bare `from textdescriptives import extract_df` with:
```python
    def encode(self, texts: List[str]) -> np.ndarray:
        try:
            from textdescriptives import extract_df
        except ImportError as e:
            raise ImportError(
                "The 'morphology' extra is required to use MorphologicalEncoder. "
                "Install it with `pip install infodynamics[morphology]`."
            ) from e

        nlp = self.nlp if self.nlp is not None else _load_pipeline(self.lang, self.feature_group, self.model_path)
        ...
```
Message string must be copied verbatim (byte-for-byte identical to the other 3 sites) — do not paraphrase or introduce a 4th variant wording.

**Note on scope:** This is the only source-code change in this phase. It does not touch public API/behavior (same exception type, same message convention already established 3x in this file) — per CONTEXT.md D-02, this is squarely "import wiring," not something requiring escalation.

---

### `.planning/phases/05-verify/05-VERIFICATION.md` (evidence transcript)

**Analog:** `.planning/phases/04-curate-the-public-api/04-VERIFICATION.md` (full content read above — most recent, same repo, same deliverable type).

**Structural pattern to copy** (frontmatter + section skeleton):
```markdown
---
phase: 05-verify
verified: <date>
status: passed
score: N/N must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 5: Verify Verification Report

**Phase Goal:** <one-line from ROADMAP>
**Verified:** <date>
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ... | ✓ VERIFIED | <exact command + exact output pasted, not paraphrased> |
```

**Evidence-citation style to copy** (concrete example from `04-VERIFICATION.md` row 7):
```
| 7 | Full pytest suite collects and passes with no import regressions (91 tests) | ✓ VERIFIED | Ran `pytest --collect-only -q` → "91 tests collected" 0 errors. Ran `pytest -q` (full suite) → "91 passed, 6 warnings" (warnings are pre-existing numeric RuntimeWarnings unrelated to this phase). |
```
Every row pastes the literal command and literal output — never "should pass" or "expected to work." This is the exact discipline `05-VERIFICATION.md` must follow for the 5 ROADMAP criteria (grep sweep, no-extras venv, pytest count reconciliation, golden/clone spot-check), using the verbatim commands and outputs RESEARCH.md already captured (e.g. `git grep -niE "dashboard|cache_contract|shipping|bench_core"` → 0 hits; `pytest -q` → "91 passed, 6 warnings in 16.31s").

**Requirements Coverage table pattern** (lines 54-60 of `04-VERIFICATION.md`):
```markdown
### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| CORE-03 | 05-0N-PLAN.md | ... | ✓ SATISFIED | Truths N, M above |
| QA-04 | 05-0N-PLAN.md | ... | ✓ SATISFIED | Truths N, M above |
```

**"Anti-Patterns Found" / "Human Verification Required" / "Gaps Summary" sections** — copy directly; these are boilerplate closing sections in every prior phase's VERIFICATION.md (see lines 63-101 of the analog) and should read "None" with a one-paragraph justification, matching the analog's tone, unless a real gap surfaces.

---

### `.github/workflows/ci.yml` (bonus, non-gating — D-07)

**No analog found in current tree.** Confirmed via RESEARCH.md: no `.github/workflows/`, `tox.ini`, or `noxfile.py` exists anywhere in `feature/artifacts`. A prior CI setup existed and was removed in commit `924d6fb` ("rm ci") — it was Poetry + codecov + mkdocs based (6 files: `on-merge-to-main.yml`, `on-pull-request.yml`, `on-release-main.yml`, `validate-codecov-config.yml`, plus `.github/actions/*`). **Do not use it as a template** — the project no longer uses Poetry (uses `setup.py`), and PyPI publishing/codecov are explicitly out of scope this milestone.

Use RESEARCH.md's synthesized minimal pattern verbatim instead (already cross-checked against official `actions/checkout`/`actions/setup-python` docs):
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.14"
      - name: Install
        run: pip install .[test]
      - name: Test
        run: pytest -q
```
Re-check `actions/checkout`/`actions/setup-python` latest major tag at execution time (RESEARCH.md A1) rather than trusting `v6` indefinitely.

---

### `tests/text/test_morphology.py` (possible regression test for the Pitfall 1 fix)

**Analog:** same file — existing `test_invalid_feature_group_raises` (lines 35-37) for the "expect a specific exception" style, and the module-level `pytest.importorskip` guards (lines 5-6) for how this file already handles the optional-dependency boundary.

**Imports pattern already in file** (lines 1-12):
```python
""" """
import numpy as np
import pytest

spacy = pytest.importorskip("spacy")
pytest.importorskip("textdescriptives")

from spacy.tokens import Doc  # noqa: E402

from infodynamics.text import MorphologicalEncoder  # noqa: E402
from infodynamics.text.morphology import encode_all_feature_groups  # noqa: E402
from infodynamics.text import TextMultiscaleInfoDynamics  # noqa: E402
```
Note: this file's existing tests all run *with* `textdescriptives` installed (guarded by `importorskip`, not simulating its absence) — a regression test for Pitfall 1 needs to simulate the *missing* module, which none of the existing tests in this file currently do. The cleanest approach (per RESEARCH.md's Wave-0-gaps note) is `monkeypatch.setitem(sys.modules, "textdescriptives", None)` or an equivalent import-blocking fixture around a call to `MorphologicalEncoder(...).encode(...)`, asserting the raised `ImportError` (not `ModuleNotFoundError`) contains `"morphology"` and `"pip install"` — mirroring the assertion style already used in RESEARCH.md's fresh-venv script (Pattern 1):
```python
try:
    me.transform(["ahoj svete"])
    raise SystemExit("expected ImportError, got none")
except ImportError as e:
    assert "morphology" in str(e) and "pip install" in str(e)
```

**Exception-raising test style already established** (lines 35-37):
```python
def test_invalid_feature_group_raises():
    with pytest.raises(ValueError):
        MorphologicalEncoder(feature_group="not_a_real_group")
```
A regression test for the line-194 fix should follow this same `pytest.raises` idiom, substituting `ImportError` and a `match=` regex if desired, e.g.:
```python
def test_encode_raises_actionable_import_error_without_textdescriptives(monkeypatch):
    ...
    with pytest.raises(ImportError, match="morphology"):
        encoder.encode(["text"])
```

Per RESEARCH.md's Wave 0 Gaps note: this is optional/discretionary — the planner may choose to add it as a lock-in regression test, given `tests/text/test_morphology.py` is already the natural home, but D-08/D-12 don't mandate new test tooling for this phase.

---

## Shared Patterns

### Guarded optional-dependency import (the core reusable pattern this phase enforces)
**Source:** `infodynamics/text/morphology.py` lines 38-52, 112-118, 127-133 (3 existing correct instances)
**Apply to:** the line-194 fix — and as a reference if any other guarded-import gaps turn up elsewhere in the codebase during the criterion-1/2 sweep (e.g. `infodynamics/text/embedding.py`, `infodynamics/clustering/{cluster,dtw,barycenter}.py` — RESEARCH.md confirms these already use the correct pattern; no fix needed there, only `morphology.py:194` is broken).
```python
try:
    import <optional_module>
except ImportError as e:
    raise ImportError(
        "The '<extra_name>' extra is required to use <ClassName>. "
        "Install it with `pip install infodynamics[<extra_name>]`."
    ) from e
```

### VERIFICATION.md evidence-transcript discipline
**Source:** `.planning/phases/04-curate-the-public-api/04-VERIFICATION.md` (and `03-`, `02-`, `01-VERIFICATION.md` siblings, same shape)
**Apply to:** `.planning/phases/05-verify/05-VERIFICATION.md`
- Every claimed truth cites a literal command + literal output, never a paraphrase.
- Frontmatter includes `score: N/N must-haves verified`.
- Closing sections (`Anti-Patterns Found`, `Human Verification Required`, `Gaps Summary`) present even when empty, with a one-line justification.

### Commit-per-fix discipline (not a file pattern, but governs how the morphology.py fix lands)
**Source:** CONTEXT.md D-03, matches commit style already used in Phases 1-4 (`type(NN-MM): description`, e.g. `05a1452 docs(04): add code review report`, `271c0e8 docs(phase-04): evolve PROJECT.md after phase completion`)
**Apply to:** the `infodynamics/text/morphology.py` line-194 fix — its own commit, e.g. `fix(05): guard textdescriptives import in MorphologicalEncoder.encode`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.github/workflows/ci.yml` | config | event-driven | No `.github/workflows/`, `tox.ini`, or `noxfile.py` exists in the current tree. A historical CI setup existed (removed commit `924d6fb`) but is Poetry/codecov/mkdocs-based and explicitly not a valid template per RESEARCH.md — planner should use RESEARCH.md's synthesized minimal workflow (Pattern 3) instead of searching for a codebase analog. |

## Metadata

**Analog search scope:** `infodynamics/text/`, `infodynamics/clustering/`, `tests/text/`, `.planning/phases/*/` (VERIFICATION.md siblings), `.github/` (confirmed absent)
**Files scanned:** `infodynamics/text/morphology.py` (full read), `.planning/phases/04-curate-the-public-api/04-VERIFICATION.md` (full read), `tests/text/test_morphology.py` (partial read, first 60 lines — sufficient, remaining tests follow the same style already extracted)
**Pattern extraction date:** 2026-07-14

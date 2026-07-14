# Phase 4: Curate the Public API - Research

**Researched:** 2026-07-14
**Domain:** Python packaging / public API surface curation (no new architecture, no new deps)
**Confidence:** HIGH

## Summary

This is a mechanical Python packaging phase, not a domain-research phase: curate two `__init__.py` files with explicit `__all__`, write one canonical example script, and write one migration table. All four success criteria are already fully specified by `04-CONTEXT.md` (D-01 through D-05 resolve the only real gray area — the top-level symbol list). Research below verifies the mechanics: the exact current re-export statements, the one real call site that breaks under D-05, and the idiomatic patterns for `__all__`, changelogs, and example scripts in a small sklearn-compatible library.

The repo-wide import sweep found only **one** call site that needs updating: `tests/text/test_morphology.py:10` imports `MorphologicalEncoder` from top-level `infodynamics`, which will stop working once D-05 lands. All other test files already import the four migrating symbols (`MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown`) from their real submodule paths already. Two untracked root demo scripts (`run_morphology_demo.py`, `run_multiscale_demo.py`) also import top-level symbols that will break, but per `PROJECT.md`'s Out of Scope table ("Cleanup of untracked root clutter") these are explicitly not this phase's responsibility — do not touch them.

**Primary recommendation:** Rewrite both `__init__.py` files as explicit `__all__` lists with plain (non-aliased) re-export imports — this codebase has no linter configured, so the F401-avoidance aliasing trick (`import X as X`) is unnecessary; `__all__` alone is sufficient and matches the existing `infodynamics/clustering/__init__.py` style. Fix the one broken test import. Add `examples/basic_usage.py` (plain runnable script, no sphinx-gallery infra needed). Add `CHANGELOG.md` at repo root with an explicit old-path → new-path table, not full Keep-a-Changelog prose sections — the goal is a mechanical find/replace reference for downstream consumers, not a semver release history.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Core `__all__` curation | Library / Package root | — | `infodynamics/__init__.py` defines the package's public contract |
| Text `__all__` curation | Library / Subpackage root | — | `infodynamics/text/__init__.py` defines the on-ramp's public contract, independent of core |
| Call-site migration (tests) | Test suite | — | Tests are the only in-repo consumers of the symbols moving; must track the new import paths |
| Canonical usage example | Documentation / Examples | — | `examples/basic_usage.py` is a docs artifact, not library code — imports the public API exactly as an external consumer would |
| Migration note | Documentation | — | `CHANGELOG.md` is static documentation, no runtime component |

This phase touches no browser/server/API/database tiers — it is entirely within the "Library" tier (package `__init__.py` files, tests, docs).

## Standard Stack

No new dependencies. This phase edits only stdlib-level Python packaging constructs (`__all__`, imports) plus two new plain-text/plain-Python artifacts (`CHANGELOG.md`, `examples/basic_usage.py`). No `setup.py` changes needed — `find_packages()` already picks up `infodynamics.text` and `infodynamics.clustering`; `examples/` should NOT be added as an installable package (it's a docs artifact, not shipped code) — verify it is excluded by `find_packages()`'s default behavior (only directories with `__init__.py` are picked up, so a plain `examples/` folder without `__init__.py` is automatically excluded; no `MANIFEST.in`/`packages=` change required).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plain `from x import y` + `__all__` | `from x import y as y` (redundant-alias re-export) | Alias form is only needed to silence linters (Ruff/Flake8 F401) on files with no `__all__`, or to explicitly re-export names NOT listed in `__all__`. This repo has no linter configured (`CLAUDE.md` confirms no Black/isort/Prettier/pylint/flake8 config) and both files will have complete `__all__` lists, so plain imports are sufficient and match the existing `infodynamics/clustering/__init__.py` precedent. |
| `CHANGELOG.md` in "Keep a Changelog" format | Ad hoc old→new symbol table | Keep a Changelog's Added/Changed/Deprecated/Removed/Fixed/Security sections are built for cross-version semver release history on a *published* package. This is a pre-1.0, unreleased, unpublished library (no PyPI presence yet — `PKG-02` is v2 scope) documenting a single one-time internal reorg across this milestone's phases. A flat "old import → new import" table is more directly actionable for the one real consumer (the future dashboard repo) doing a mechanical find/replace. |
| `examples/` with sphinx-gallery scaffolding | Plain runnable `examples/basic_usage.py` | scikit-learn-contrib's official project-template uses `examples/` + sphinx-gallery + a `doc/` build to generate a rendered example gallery. This repo has no Sphinx/doc-build infrastructure and adding one is out of scope. A plain script with a module docstring and a `__main__` guard delivers the same "canonical example" success criterion without new tooling. |

**Installation:** None — no new packages.

## Package Legitimacy Audit

**Not applicable.** This phase introduces zero new external dependencies (verified: `setup.py` unchanged, no new imports of third-party packages in any planned artifact). Skip the Package Legitimacy Gate.

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────┐
                    │   infodynamics/__init__.py   │
                    │  __all__ = [8 core symbols]  │
                    └──────────────┬───────────────┘
                                   │ imports FROM (not .text)
        ┌──────────────┬──────────┼──────────┬──────────────────┐
        ▼              ▼          ▼          ▼                  ▼
   pipeline.py   time_series.py scalogram.py clustering/    (NO text import)
   (InfoDynamics, (WindowedRoll-  (Scalogram,  __init__.py
   Multiscale     ingDistance)    FooteNovelty, (SignalClusterer
   InfoDynamics)                  self_sim_matrix, re-exported;
                                   structure_       barycenter_average,
                                   descriptors)      pairwise_distance
                                                      submodule-only)

                    ┌──────────────────────────────────┐
                    │  infodynamics/text/__init__.py     │
                    │  __all__ = [TextInfoDynamics,      │
                    │   TextMultiscaleInfoDynamics,       │
                    │   TextSegmenter, Encoder,           │
                    │   MorphologicalEncoder, Chunk,      │
                    │   segment, strip_markdown]          │
                    └──────────────┬───────────────────────┘
                                   │ imports from
        ┌──────────────┬──────────┼──────────────┐
        ▼              ▼          ▼              ▼
   pipeline.py    embedding.py  morphology.py  segmentation.py
   (Text* wrappers) (Encoder)   (Morphological  (Chunk, segment,
                                  Encoder)        strip_markdown,
                                                   TextSegmenter)

   Consumers (tests/, examples/basic_usage.py) import ONLY via:
     from infodynamics import <core symbol>
     from infodynamics.text import <text symbol>
   Never via internal submodule paths unless explicitly reaching for
   a submodule-only utility (infodynamics.viz.*, infodynamics.metrics.*,
   infodynamics.scalogram.checkerboard_kernel, etc.)
```

### Recommended Project Structure
```
infodynamics/
├── __init__.py          # __all__ = 8 core symbols, zero .text imports (D-01..D-05)
├── text/
│   └── __init__.py      # __all__ = 8 text symbols (3 existing + 5 migrated)
├── clustering/
│   └── __init__.py      # unchanged (D-04) — existing curated re-export precedent
examples/
└── basic_usage.py       # NEW — core-only path + full Pipeline path
CHANGELOG.md              # NEW — old→new import path table
```

### Pattern 1: Explicit `__all__` with plain re-export imports
**What:** List every re-exported name once in `__all__`; import it with a plain `from module import Name` (no aliasing needed since there's no linter to appease).
**When to use:** Any `__init__.py` acting as a curated public-API surface over multiple submodules.
**Example:**
```python
# infodynamics/__init__.py — model this after infodynamics/clustering/__init__.py's
# existing curated-import precedent (D-04 keeps that file as-is / stylistic reference)
__version__ = "0.1.0"

from infodynamics.clustering import SignalClusterer
from infodynamics.pipeline import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.scalogram import (
    FooteNovelty,
    Scalogram,
    self_similarity_matrix,
    structure_descriptors,
)
from infodynamics.time_series import WindowedRollingDistance

__all__ = [
    "InfoDynamics",
    "MultiscaleInfoDynamics",
    "WindowedRollingDistance",
    "Scalogram",
    "FooteNovelty",
    "SignalClusterer",
    "self_similarity_matrix",
    "structure_descriptors",
]
```
```python
# infodynamics/text/__init__.py
"""infodynamics.text — text on-ramp (segmentation, embedding, morphological encoding)."""
from infodynamics.text.embedding import Encoder
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.text.pipeline import TextInfoDynamics, TextMultiscaleInfoDynamics
from infodynamics.text.segmentation import Chunk, TextSegmenter, segment, strip_markdown

__all__ = [
    "TextInfoDynamics",
    "TextMultiscaleInfoDynamics",
    "TextSegmenter",
    "Encoder",
    "MorphologicalEncoder",
    "Chunk",
    "segment",
    "strip_markdown",
]
```
Source: PEP 8 / general Python packaging convention; cross-checked against Ruff's documented F401 re-export handling `[CITED: docs.astral.sh/ruff/rules/unused-import]` — an explicit `__all__` is one of the two accepted ways to mark re-exports as intentional (the other being the `import X as X` alias, unnecessary here since no linter is configured).

### Pattern 2: Submodule reachability without top-level export
**What:** A name that is deliberately NOT in `__all__` or even NOT imported into `__init__.py` remains reachable as `infodynamics.<submodule>.<name>` once that submodule has been imported anywhere in the process (which it always will be, transitively, since `pipeline.py`/`scalogram.py` etc. get imported by the `__init__.py` imports above).
**When to use:** D-02 (`checkerboard_kernel`, `foote_novelty`, `rolling_gap_distance`), D-03 (`viz`, `metrics` modules), D-04 (`barycenter_average`, `pairwise_distance` via `infodynamics.clustering.*`).
**Verification:** `python -c "import infodynamics; infodynamics.viz.plot_ssm"` and `python -c "from infodynamics import viz"` both work regardless of whether `viz` appears in `__all__` — Python's `from package import name` import statement falls back to importing `package.name` as a submodule when `name` isn't already a package attribute. This is stdlib import-system behavior, not something `__all__` controls (`__all__` only affects `from package import *`). `[VERIFIED: existing tests/test_viz.py:11 already does `from infodynamics import viz` today with no `__all__` present, proving the mechanism]`

### Anti-Patterns to Avoid
- **Re-adding a `from .text import ...` statement anywhere in `infodynamics/__init__.py`, even indirectly:** D-05 is a hard requirement, not discretionary. The grep check in Verification Mechanics below must return zero matches.
- **Repurposing `run_morphology_demo.py`/`run_multiscale_demo.py`/`descriptors_analysis.py`/`segmentation_demo.py`/`shit.py` as the canonical example:** explicitly out of scope per `PROJECT.md`; CONTEXT.md restates this as a boundary note. `examples/basic_usage.py` must be a new, separate, tracked file.
- **Folding the CHANGELOG into README.md:** CONTEXT.md's discretion note explicitly recommends a dedicated file since README's scope is undecided; committing a migration note into an unrelated future-scope file creates rework risk.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting stray `from .text import` statements | A custom AST-walker script | `grep -n "from .text import\|from infodynamics.text import" infodynamics/__init__.py` | The check is a single-file, single-pattern search; a grep one-liner is sufficient and matches the "Verification Mechanics" research item's ask directly. |
| Verifying `__all__` completeness | Manual eyeballing | A one-line pytest assertion: `assert set(infodynamics.__all__) == {...}` plus `all(hasattr(infodynamics, n) for n in infodynamics.__all__)` | Cheap, deterministic, catches both "listed but not importable" and "importable but not listed" drift in future changes — see Validation Architecture below. |

**Key insight:** This phase has no algorithmic complexity — the only real risk is *forgetting* a call site or a symbol. Both risks are fully closed by grep + a completeness test, not by cleverness.

## Runtime State Inventory

**Not applicable — this is not a rename/refactor/migration-of-runtime-state phase.** No databases, external services, OS registrations, or secrets are touched. `git grep`/`grep` sweep covers the only "state" that matters here: static import statements in tracked `.py` files. Confirmed via full-repo sweep (see Verification Mechanics) — the only category to check is source-code import paths, and that has already been enumerated below.

## Common Pitfalls

### Pitfall 1: Assuming `__all__` controls `from package import submodule` reachability
**What goes wrong:** Someone "fixes" a perceived regression by re-adding `viz`/`metrics`/`scalogram` internals to `__all__` or to the `__init__.py` import list, defeating D-02/D-03's intent to keep the top-level surface small.
**Why it happens:** `__all__`'s actual scope (only `from package import *`) is a common Python misconception.
**How to avoid:** Document the reachability mechanism explicitly in a code comment or the CHANGELOG so future contributors don't "fix" what isn't broken. Verify with the `python -c "from infodynamics import viz"` check before and after the `__init__.py` rewrite — behavior must be unchanged.
**Warning signs:** A PR diff that adds `viz`, `metrics`, `checkerboard_kernel`, `foote_novelty`, `rolling_gap_distance`, `barycenter_average`, or `pairwise_distance` to the top-level `__all__` — check against D-01 through D-04 before merging.

### Pitfall 2: Missing a call site because grep patterns don't match the actual import style used
**What goes wrong:** A narrow grep (e.g., only `"from infodynamics import Chunk"`) misses `from infodynamics import (` multi-line parenthesized import blocks that include `Chunk`/`MorphologicalEncoder`/etc. as one of several names.
**Why it happens:** Two call sites in this repo (`tests/test_pipeline_composition.py`, `tests/golden/capture_baseline.py`) already use the multi-line parenthesized `from infodynamics import (\n ... \n)` form for *other* symbols — a naive single-line grep would silently skip them if they *had* imported a migrating symbol.
**How to avoid:** This research already resolved it by reading each `from infodynamics import (...)` block in full (see Verification Mechanics) rather than grepping in isolation — confirmed neither of those two blocks imports any of the 4 migrating symbols. The plan should re-run the full sweep as a verification step, not just trust this document, since new call sites could appear if branches diverge.
**Warning signs:** `pytest --collect-only` reporting an `ImportError` after the `__init__.py` rewrite — this is the definitive, cheap catch-all check (see Verification Mechanics), independent of grep completeness.

## Code Examples

### Migrating the one broken test import
```python
# tests/text/test_morphology.py — line 10, BEFORE:
from infodynamics import MorphologicalEncoder  # noqa: E402

# AFTER (D-05 removes MorphologicalEncoder from top-level infodynamics;
# it now lives in infodynamics.text per Claude's-discretion decision):
from infodynamics.text import MorphologicalEncoder  # noqa: E402
```
This is the **only** call-site fix required in tracked code. `[VERIFIED: repo-wide grep + manual read of every from-infodynamics-import block, 2026-07-14]`

### Verification Mechanics — grep pattern for D-05 (zero `.text` imports)
```bash
# Must return zero matches (exit code 1 from grep = "not found" = success):
grep -n "from \.text import\|from infodynamics\.text import" infodynamics/__init__.py
echo "exit code: $?"   # expect 1 (no matches found)
```

### Verification Mechanics — `__all__` completeness test
```python
# tests/test_public_api.py (new, small — fits Validation Architecture Wave 0 gap below)
import infodynamics
import infodynamics.text


def test_core_all_matches_expected_symbols():
    expected = {
        "InfoDynamics", "MultiscaleInfoDynamics", "WindowedRollingDistance",
        "Scalogram", "FooteNovelty", "SignalClusterer",
        "self_similarity_matrix", "structure_descriptors",
    }
    assert set(infodynamics.__all__) == expected
    for name in infodynamics.__all__:
        assert hasattr(infodynamics, name), f"{name} in __all__ but not importable"


def test_core_init_has_no_text_imports():
    import inspect
    source = inspect.getsource(infodynamics)
    assert ".text" not in source, "infodynamics/__init__.py must not import from .text (D-05)"


def test_text_all_matches_expected_symbols():
    expected = {
        "TextInfoDynamics", "TextMultiscaleInfoDynamics", "TextSegmenter",
        "Encoder", "MorphologicalEncoder", "Chunk", "segment", "strip_markdown",
    }
    assert set(infodynamics.text.__all__) == expected
    for name in infodynamics.text.__all__:
        assert hasattr(infodynamics.text, name), f"{name} in __all__ but not importable"
```
Note: `inspect.getsource(infodynamics)` reads the live `__init__.py` source text, which is a more robust check for D-05 than re-grepping the file from within Python (works the same whether run from repo root or an installed package).

### Verification Mechanics — full collection sanity check
```bash
.venv/bin/python -m pytest --collect-only -q
# BEFORE this phase: 88 tests collected, 0 errors (confirmed 2026-07-14)
# AFTER this phase: must still collect >= 88 tests (89+ once test_public_api.py is added),
# 0 collection errors. Any ImportError here is an unmigrated call site.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `infodynamics/__init__.py` re-exports 10 names incl. 4 text symbols, no `__all__` | `__init__.py` re-exports exactly 8 core symbols via explicit `__all__`, zero text imports | This phase | Downstream consumers doing `from infodynamics import *` (unlikely but possible) get a curated surface; `dir(infodynamics)`/IDE autocomplete reflects intent |
| `infodynamics/text/__init__.py` re-exports 3 names, no `__all__`, docstring says curation deferred | Re-exports 8 names via explicit `__all__` | This phase | `Encoder`, `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown` become "officially public" text-on-ramp API for the first time (previously reachable only via internal submodule paths or the accidental top-level core re-export) |

**Deprecated/outdated:** `from infodynamics import MorphologicalEncoder` / `from infodynamics import Chunk, segment, strip_markdown` — both stop working after this phase; no back-compat shim is provided (PROJECT.md: "Backward-compatible import paths / deprecation shims" explicitly Out of Scope this milestone — breaking changes accepted pre-1.0).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | Ruff's F401 re-export handling (explicit `__all__` suppresses the warning; `import X as X` is the alternative) generalizes to "Python packaging convention" broadly, not just Ruff specifically | Standard Stack / Architecture Patterns Pattern 1 | Low — this repo has no linter configured at all (confirmed via `CLAUDE.md` and a filesystem check for ruff/flake8/pylint/pyproject config, none found), so the convention is purely stylistic guidance here, not an enforced gate. If a linter is added later, revisit. |
| A2 | `examples/` as a plain (non-package) directory is automatically excluded from `find_packages()` in `setup.py` and needs no `MANIFEST.in`/packaging change | Standard Stack | Low — `find_packages()` only discovers directories containing `__init__.py`; `examples/basic_usage.py` with no `__init__.py` is excluded by construction. If the planner adds an `examples/__init__.py` for some reason, this would need re-checking, but there is no reason to. |

## Open Questions

None — CONTEXT.md's D-01 through D-05 resolve the only substantive gray area, and this research confirms the mechanical details (exact current re-exports, the one breaking call site, `__all__`/CHANGELOG/examples conventions) needed to plan without further exploration.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-------------------|
| API-03 | Public API is curated — explicit `__all__` at `infodynamics` and `infodynamics.text`; core `__init__.py` never imports from `.text` | Pattern 1 gives the exact target `__init__.py` content for both files (matches D-01–D-05 verbatim). Verification Mechanics gives the grep + pytest checks that prove both halves of this requirement mechanically. |
| API-04 | Canonical example demonstrates core-only + full Pipeline composition; CHANGELOG/migration note maps old→new import paths | Architecture Patterns / Recommended Project Structure locates `examples/basic_usage.py`; Standard Stack's Alternatives Considered table settles CHANGELOG format (flat table, not Keep-a-Changelog prose) with rationale, ready for the planner to draft the actual old→new symbol table (source data: `infodynamics/__init__.py`'s current vs. target re-exports, listed in Code Examples / Architecture Patterns above, plus Phase 2/3 moves already logged in `.planning/STATE.md`'s Decisions log). |
</phase_requirements>

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 6.2.2+ (already installed, `.venv/bin/pytest`) |
| Config file | none — default discovery via `test_*.py` naming in `tests/` |
| Quick run command | `.venv/bin/python -m pytest --collect-only -q` (import/collection sanity, ~14s) |
| Full suite command | `.venv/bin/python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|--------------------|--------------|
| API-03 | `infodynamics.__all__` == exact 8-symbol set, all resolve | unit | `pytest tests/test_public_api.py::test_core_all_matches_expected_symbols -x` | ❌ Wave 0 |
| API-03 | `infodynamics/__init__.py` source contains no `.text` import | unit | `pytest tests/test_public_api.py::test_core_init_has_no_text_imports -x` | ❌ Wave 0 |
| API-03 | `infodynamics.text.__all__` == exact 8-symbol set, all resolve | unit | `pytest tests/test_public_api.py::test_text_all_matches_expected_symbols -x` | ❌ Wave 0 |
| API-03 | No import regressions anywhere in the suite | smoke | `pytest --collect-only -q` (expect 0 errors, count >= 88) | ✅ (pytest itself; no new file) |
| API-04 | `examples/basic_usage.py` runs end-to-end (both paths) without error | smoke | `.venv/bin/python examples/basic_usage.py` | ❌ Wave 0 (file doesn't exist yet — this phase creates it) |
| API-04 | `CHANGELOG.md` exists and lists all migrated symbols | manual-only | N/A — reviewed by inspection during `/gsd-verify-work`; no automated content check is warranted for prose/table doc content | ❌ (doc, not test) |

### Sampling Rate
- **Per task commit:** `.venv/bin/python -m pytest --collect-only -q` (fast import-error catch, ~14s)
- **Per wave merge:** `.venv/bin/python -m pytest -q` (full suite, catches any runtime behavior change — none expected this phase, but golden-baseline tests must stay green)
- **Phase gate:** Full suite green before `/gsd-verify-work`, plus manual read of `CHANGELOG.md` and a manual run of `examples/basic_usage.py`

### Wave 0 Gaps
- [ ] `tests/test_public_api.py` — new file, covers API-03 (`__all__` completeness + zero-`.text`-import assertions)
- [ ] `examples/basic_usage.py` — new file, itself the deliverable for API-04's example criterion; runnable smoke-check, no pytest wrapper required (a plain script invocation is sufficient per CONTEXT.md's discretion note; a thin `tests/test_examples.py::test_basic_usage_runs` subprocess-invocation test is optional but not required by the phase's success criteria)
- [ ] No framework install needed — pytest already present in the `test` extra

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|-------------------|
| V2 Authentication | No | This phase touches no auth surface — it's a Python import/export curation change with no network/user-facing component |
| V3 Session Management | No | No sessions involved |
| V4 Access Control | No | No access-control surface |
| V5 Input Validation | No | No new input paths — `__all__` curation and a static example script don't accept untrusted input |
| V6 Cryptography | No | Not applicable |

### Known Threat Patterns for this stack

None apply. This phase is a pure static-surface refactor (import statements, docstrings, one new example script, one new markdown file) with zero new runtime input handling, zero new dependencies, and zero change to data flow or trust boundaries. `security_enforcement: true` is acknowledged but has no applicable ASVS controls to enforce here — the plan-checker should not block this phase on security grounds; note this explicitly so the planner doesn't manufacture unnecessary security tasks.

## Sources

### Primary (HIGH confidence)
- Direct repo inspection: `infodynamics/__init__.py`, `infodynamics/text/__init__.py`, `infodynamics/clustering/__init__.py`, `setup.py`, full `tests/` and `tests/text/` import sweep, `.venv/bin/python -m pytest --collect-only -q` (88 tests, 0 errors baseline) — all read/executed directly, 2026-07-14.
- `.planning/phases/04-curate-the-public-api/04-CONTEXT.md` — D-01 through D-05, Claude's-discretion notes, canonical refs.
- `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/config.json` — requirement text, decision history, workflow toggles (`nyquist_validation: true`, `security_enforcement: true`).

### Secondary (MEDIUM confidence)
- Ruff docs on F401 unused-import re-export handling `[CITED: docs.astral.sh/ruff/rules/unused-import]` — confirms explicit `__all__` and the `import X as X` alias are the two accepted intentional-re-export signals.
- keepachangelog.com format description (via WebSearch digest) `[CITED: keepachangelog.com]` — confirms Keep a Changelog's section structure and its orientation toward versioned release history rather than one-time reorg documentation.
- scikit-learn-contrib/project-template `examples/` + sphinx-gallery convention (via WebSearch digest) `[CITED: github.com/scikit-learn-contrib/project-template, contrib.scikit-learn.org/project-template]` — confirms `examples/` as the idiomatic location and structure for canonical usage scripts in sklearn-compatible libraries.

### Tertiary (LOW confidence)
- None — all findings above were either verified directly against this repo or cross-checked against an official/authoritative doc source.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; verified `setup.py` and `find_packages()` behavior directly.
- Architecture: HIGH — every symbol/import statement verified by direct file reads, not inferred.
- Pitfalls: HIGH — both pitfalls are grounded in a verified repo fact (existing `from infodynamics import viz` call site; existing multi-line import blocks that had to be read in full to rule out).

**Research date:** 2026-07-14
**Valid until:** Stable — no time-sensitive external dependency; re-verify only if the repo's tracked files change materially before planning executes (e.g., a new test file lands with a top-level import of a migrating symbol).

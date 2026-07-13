# Stack Research

**Domain:** Lean, sklearn-compatible scientific Python library (extraction/refactor, not greenfield)
**Researched:** 2026-07-13
**Confidence:** MEDIUM-HIGH (sklearn/sktime/tslearn facts verified against official docs and source; general "2025/2026 best practice" framing is web-search-aggregated, cross-checked across multiple independent sources)

## Milestone framing (read this first)

This milestone's finish line is **"decoupled + reorganized, tests green."** Not PyPI publishing, not `pyproject.toml` migration, not full `check_estimator` conformance. Every recommendation below is tagged:

- **[NOW]** — do this during the extraction, it's cheap and directly serves "reorganize cleanly + keep tests green"
- **[LATER]** — correct and worth knowing, but belongs to the deferred packaging-modernization milestone; don't let it scope-creep this one

The codebase already does several things right (verified by reading `infodynamics/embedding.py`, `infodynamics/morphology.py`, `infodynamics/clustering/barycenter.py`, `setup.py`): lazy `try/except ImportError` guards for heavy deps with actionable install messages, `extras_require` grouped by capability, and stateless `BaseEstimator`/`TransformerMixin` transformers. The recommendations here are about **making that existing convention rigorous and consistent**, not introducing new paradigms.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| scikit-learn | ≥1.9.0 (currently installed: 1.9.0) | Estimator base classes, Pipeline, conformance test utilities | First stable line with full CPython 3.14 wheels (uploaded June 2026); `BaseEstimator`/`TransformerMixin`/`estimator_checks` are the only correct foundation for "sklearn-compatible" as a hard constraint — verified via official scikit-learn.org docs |
| numpy | ≥2.x (currently installed: 2.4.6) | Array primitives for all analysis code | Confirmed Python 3.14 compatible per pyreadiness.org; numpy 2.x is the array-protocol baseline sklearn 1.9 itself expects |
| scipy | ≥1.16 (currently installed: 1.18.0) | Hierarchical clustering, distance utilities | SciPy 1.16.1 (July 2025) was the first stable release with Python 3.14 wheels; already satisfied in the current venv |
| pytest | ≥6.2.2 in current `extras_require['test']`; no version blocker for 3.14 | Test runner, `parametrize_with_checks` integration | sklearn's own conformance decorator (`sklearn.utils.estimator_checks.parametrize_with_checks`) is pytest-native — it yields one parametrized test per (estimator, check) pair, so `pytest -k` can target failures |
| hypothesis | ≥6.87.0 in current `extras_require['test']` | Property-based tests for numeric invariants | `hypothesis.extra.numpy.arrays()` generates arrays across dtype/shape/edge-cases (NaN, inf, empty) that hand-written fixtures miss — the natural fit for testing windowed-distance / scalogram code that must not blow up on degenerate input |

### Supporting Libraries (already in the codebase — confirm, don't add)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sklearn.base.BaseEstimator` | n/a (part of scikit-learn) | Supplies `get_params`/`set_params` by introspecting `__init__` signature | Every public estimator class (`InfoDynamics`, `MultiscaleInfoDynamics`, `Scalogram`, `FooteNovelty`, `SignalClusterer`, encoders) |
| `sklearn.base.TransformerMixin` | n/a | Supplies default `fit_transform = fit(X).transform(X)` | Every stateless transformer in the reorganized core |
| `sklearn.utils.estimator_checks.parametrize_with_checks` | n/a | pytest decorator that runs sklearn's own conformance suite | Selectively, on the subset of checks that make sense for domain-specific estimators (see "check_estimator: use selectively" below) |
| `sklearn.pipeline.Pipeline` | n/a | Compose text on-ramp → analysis into one fit/transform chain | The literal shape of the "Pipeline-composable" requirement in PROJECT.md — write a smoke test that builds `Pipeline([("segment", ...), ("embed", ...), ("analyze", ...)])` and calls `fit_transform` end-to-end |
| `sklearn.base.clone` | n/a | Deep-copies an estimator using only `get_params` | Use directly in tests to catch params that aren't cloneable (mutable defaults, unhashable objects passed as params) — cheaper than full `check_estimator` and catches the same class of bug |

## The sklearn-compatibility toolkit — prescriptive rules

These are the actual conventions `BaseEstimator`/`TransformerMixin`/`estimator_checks` enforce. Treat as a checklist during the reorg, not aspirational reading.

1. **`__init__` stores parameters only, verbatim.** No validation, no derived attributes, no calling other methods. `self.window_size = window_size`, full stop. (Validation happens in `fit`.) This is required for `get_params`/`clone`/`GridSearchCV` to work — `get_params` reads back exactly what was passed to `__init__` by inspecting the signature, so anything transformed in `__init__` breaks the round-trip.
2. **Every `__init__` parameter must be a public attribute with the same name.** No `self._window = window_size`. `BaseEstimator.get_params` fails loudly (or silently returns wrong values) if names don't line up 1:1.
3. **Attributes learned during `fit` end in a trailing underscore** (`self.model_`, `self.pipeline_`, `self.centers_`). This is the sklearn convention for "fitted state" vs "hyperparameter," and some `estimator_checks` explicitly probe for it.
4. **`fit` returns `self`.** Required for `Pipeline` chaining and for `TransformerMixin.fit_transform`'s default implementation to work.
5. **Don't mutate input `X`.** Copy before in-place ops. `Pipeline` and `clone()` assume transformers are side-effect-free on their inputs.
6. **`get_params(deep=True)` must recurse into nested estimators** if any constructor param is itself an estimator (e.g., if `MultiscaleInfoDynamics` takes an `encoder=` object). `BaseEstimator` handles this automatically *if* the nested object also inherits `BaseEstimator` — don't hand-roll composition here.

**Confidence: HIGH** — cross-checked against scikit-learn's official "Developing scikit-learn estimators" guide and the `BaseEstimator`/`TransformerMixin` API docs (scikit-learn.org/stable), which are unambiguous and stable across recent releases.

### `check_estimator` / `parametrize_with_checks`: use selectively, not as a gate **[mixed NOW/LATER]**

PROJECT.md explicitly scopes out full `check_estimator` conformance ("nice-to-have, not a gate — Pipeline-composability is the bar"). That's the right call for this milestone, and here's the nuance to preserve it correctly:

- `check_estimator` runs scikit-learn's *generic* estimator test suite — designed for classifiers/regressors/general transformers on tabular `(n_samples, n_features)` data with `X, y` signatures. Several of infodynamics' estimators don't fit that mold (e.g., `InfoDynamics.fit` takes a raw text string, not `(n_samples, n_features)`; `Scalogram` operates on a single time series, not i.i.d. samples). Running full `check_estimator` on those will fail checks that are *correctly* inapplicable to the domain, producing noise, not signal.
- **[NOW]** Do apply the checklist above (rules 1–6) by hand/code-review during the reorg — they're free and prevent the most common Pipeline-breaking mistakes (mutable `__init__`, missing trailing underscore, non-returning `fit`).
- **[NOW]** Do write one or two focused tests using `sklearn.base.clone()` and manual `get_params()`/`set_params()` round-trips on each public estimator — this catches 80% of what `check_estimator` would catch, without dragging in checks that assume tabular ML semantics.
- **[LATER]** If/when the text on-ramp encoders (`Encoder`, `MorphologicalEncoder`) are the only estimators consuming `(n_samples, n_features)`-shaped embeddings downstream, `parametrize_with_checks` on *those specific transformers* (not the whole library) becomes worth adding — defer to the packaging milestone or do opportunistically if cheap.

### Testing Pipeline composability specifically **[NOW]**

The PROJECT.md requirement is concrete: "chain text on-ramp → analysis, with working `get_params`/`set_params` and `fit`/`transform`/`fit_transform`." The direct test for this is not `check_estimator` — it's building a real `sklearn.pipeline.Pipeline` from the reorganized public API and exercising it:

```python
from sklearn.pipeline import Pipeline
from infodynamics.text import Segmenter, Encoder
from infodynamics import MultiscaleAnalyzer  # illustrative — actual names TBD in reorg

pipe = Pipeline([
    ("segment", Segmenter(level="sentence")),
    ("embed", Encoder(model_name="sentence-transformers/all-MiniLM-L6-v2")),
    ("analyze", MultiscaleAnalyzer(scales=(2, 3, 5, 8))),
])
result = pipe.fit_transform(raw_text)

# params round-trip through the whole pipeline, not just one step
params = pipe.get_params(deep=True)
pipe.set_params(analyze__scales=(2, 3, 5))
```

Add this as an integration test (`tests/test_pipeline_composition.py` or similar) once the reorg lands the new namespace. It is the single highest-value test for this milestone's actual acceptance bar.

## Optional-dependency / extras layout pattern

### What the ecosystem actually does (verified against source)

| Library | Core deps | Extras pattern | Source |
|---------|-----------|-----------------|--------|
| **sktime** | Minimal (pandas etc.) — deliberately minimized | Three-tier taxonomy: **core** (auto-installed) / **soft** (module-specific, manual install) / **developer** (contributor-only). Soft deps live in named extras (`forecasting`, `classification`, ...) plus an `all_extras` aggregate. Each soft dep gets explicit lower+upper version bounds (upper = next minor, to protect against breaking changes). | sktime official dependencies guide, fetched directly |
| **tslearn** | scikit-learn, numpy, scipy, numba, joblib, statsmodels | Named extras: `pytorch` (torch), `tests` (pytest+h5py), `docs`, and `all_features` (torch+h5py+keras+cesium+pandas+stumpy bundled). Platform-conditional constraints (e.g., numpy capped on macOS Intel for torch compat). | tslearn `pyproject.toml`, fetched directly from GitHub |
| **ruptures** | numpy, scipy, Cython (build-time) | **No optional-dependencies section at all** — it's a genuinely small, non-modality library, so everything is core. | ruptures `pyproject.toml`, fetched directly from GitHub |
| **stumpy** | numpy, scipy, numba (all core — numba is NOT optional, it's load-bearing for JIT performance) | `ci` extras group bundles dev/test/distributed-computing tools (dask, distributed, polars) — not a user-facing capability split | stumpy `pyproject.toml` / GitHub, cross-checked via search |
| **scikit-learn itself** | numpy, scipy, joblib, threadpoolctl | Optional soft deps (matplotlib, pandas) checked via `sklearn.utils._optional_dependencies.check_<name>_support(caller_name)` — a **module-level lazy-check function per dependency**, called from inside the feature that needs it, raising `ImportError` with an actionable `pip install X` message | scikit-learn `_optional_dependencies.py`, fetched directly from GitHub |

### The pattern to apply — infodynamics already does most of this **[NOW: formalize, don't invent]**

The codebase's current pattern (seen in `embedding.py`, `morphology.py`, `clustering/barycenter.py`) is: `try: from heavy_lib import X except ImportError as e: raise ImportError("The 'extra' is required... pip install infodynamics[extra]") from e`, called **inside the function that needs it**, not at module import time. This is exactly scikit-learn's own `check_<name>_support` idiom and exactly sktime's "avoid soft deps at module level, isolate to methods" guidance. Recommendation:

1. **[NOW]** Keep the existing `extras_require` groups (`embedding`, `morphology`, `clustering`, `viz-projection`, `test`, `all`) — they already map to capability boundaries, which is the right axis (not "heavy vs light," but "what feature needs this").
2. **[NOW]** During the reorg, audit every heavy import (`sentence-transformers`, `spacy-udpipe`, `textdescriptives`, `tslearn`, `umap-learn`) and confirm each is guarded with the try/except-at-point-of-use pattern, not imported at module top level. This is the single biggest lever for "core imports fast and doesn't require heavy deps to be installed" — which matters directly for `infodynamics.text` being genuinely separable from the numeric core per PROJECT.md.
3. **[NOW, low-effort]** Consider extracting the repeated try/except-with-message boilerplate into one small internal helper (`infodynamics._optional.require(module_name, extra_name, caller_name)`) mirroring `sklearn.utils._optional_dependencies` — reduces duplication across `embedding.py`/`morphology.py`/`clustering/barycenter.py` without adding a new dependency (it's ~10 lines, stdlib only).
4. **[LATER]** Migrating `extras_require` (setup.py) to `[project.optional-dependencies]` (pyproject.toml) is real and correct, per current Python packaging guidance — but PROJECT.md explicitly defers this. Don't do it in this milestone; the setup.py-based extras already work and tests don't care which packaging file declares them.
5. **[LATER]** sktime's "explicit upper+lower version bounds per soft dependency, upper bound = next minor" is a good discipline to adopt when the packaging milestone lands — not urgent now since nothing is being published to PyPI yet.

### `importlib.util.find_spec` vs `try/except ImportError`

sktime's dependency-checking utility (`_check_soft_dependencies`) recommends `importlib.util.find_spec(name)` over `try/except ImportError` for *presence checks* (e.g., "is torch installed at all, without importing it"), because `find_spec` avoids the cost and side effects of a full import when you just need a boolean. **[LATER / situational]** — not needed here since the codebase's pattern isn't "check then decide," it's "attempt and fail with a message," which is the correct pattern when you're about to use the dependency anyway (no benefit to a separate presence check). Only relevant if a future need arises for e.g. "list which optional features are available" introspection.

## Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `pytest` | Test runner | Already in `extras_require['test']`; no `conftest.py` currently exists in `tests/` — **[NOW]** worth adding one with shared fixtures (e.g., a small synthetic embedding matrix, a short text sample) once the reorg settles the new module boundaries, so tests for `infodynamics.text` and the numeric core can share setup without duplicating it per file |
| `hypothesis` | Property-based testing | Already in `extras_require['test']`. `hypothesis.extra.numpy.arrays()` — **[NOW, targeted]** good fit for `WindowedRollingDistance`, `Scalogram`, `FooteNovelty`: generate arrays with varying shape/dtype/NaN-presence and assert no crash + output shape invariants hold. Don't over-invest — a handful of property tests on the numeric core's edge cases (empty input, single row, constant signal) is the actionable scope, not exhaustive coverage of every function |
| `sklearn.utils.estimator_checks.parametrize_with_checks` | Selective conformance checks | See "use selectively" above — apply narrowly to `Encoder`/`MorphologicalEncoder` if convenient, not project-wide |
| `sklearn.base.clone` + manual `get_params`/`set_params` round-trip tests | Cheap Pipeline-compatibility net | **[NOW]** — this is the pragmatic middle ground between "nothing" and "full check_estimator"; one small test per public estimator |

## Installation

```bash
# Core (already satisfied in current venv: sklearn 1.9.0, numpy 2.4.6, scipy 1.18.0)
pip install "scikit-learn>=1.9" "numpy>=2.0" "scipy>=1.16" matplotlib syntok typing-extensions

# Test tooling (already declared in extras_require['test'])
pip install "pytest>=6.2.2" "hypothesis>=6.87.0"

# Heavy extras — unchanged from current setup.py, install only what a given task needs
pip install "infodynamics[embedding]"      # sentence-transformers
pip install "infodynamics[morphology]"     # spacy-udpipe + textdescriptives
pip install "infodynamics[clustering]"     # tslearn + scipy
pip install "infodynamics[viz-projection]" # umap-learn
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| Hand-checklist (rules 1–6) + `clone()`/`get_params()` round-trip tests | Full `sklearn.utils.estimator_checks.check_estimator` on every public class | If a later milestone wants to publish to PyPI as a general-purpose sklearn-contrib-style library and needs to advertise full conformance — not this milestone (PROJECT.md explicitly scopes this out) |
| Keep `extras_require` in `setup.py` | Migrate to `[project.optional-dependencies]` in `pyproject.toml` | The packaging-modernization milestone (deferred) — do it then, alongside build-backend and metadata modernization, not piecemeal now |
| `try/except ImportError` at point-of-use (current pattern, keep it) | `importlib.util.find_spec` presence checks | Only if the library needs a "list available optional features" introspection API — no current requirement for that |
| pytest + hypothesis (already chosen) | `unittest` + manual edge-case enumeration | Never for this codebase — hypothesis is already a declared test dependency and well-suited to the numeric-array-heavy code being reorganized |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| Importing heavy optional deps (`sentence_transformers`, `spacy_udpipe`, `textdescriptives`, `tslearn`, `umap`) at module top level anywhere in the reorganized core | Breaks the "core imports without heavy deps installed" property that makes `infodynamics.text` genuinely separable — a single top-level import defeats the whole extras structure even if 99% of the code is guarded correctly | try/except-at-point-of-use, exactly as `embedding.py`/`morphology.py` already do — audit for regressions during the reorg |
| Treating `check_estimator` as a milestone gate | It assumes tabular `(n_samples, n_features)` + `X, y` semantics that don't universally apply to this domain's estimators (raw text in, single time series in); chasing full conformance burns time on inapplicable checks and was explicitly scoped out in PROJECT.md | The targeted checklist + `clone()`/`get_params` round-trip tests described above |
| PEP 810 lazy imports / `-X lazy_imports` | Not available — that's a Python 3.15 feature (final release Oct 2026), and this project targets Python 3.14.x | The existing try/except pattern; revisit if/when the project moves to 3.15+ |
| `pyproject.toml` migration mid-reorg | Scope creep against this milestone's explicit "no packaging modernization" boundary; mixing a packaging-format change into a namespace/module reorg makes it harder to isolate what broke if tests go red | Finish the reorg on `setup.py` as-is; do the packaging migration as its own later milestone with its own verification pass |

## Stack Patterns by Variant

**If an estimator's `fit(X)` doesn't take `(n_samples, n_features)`-shaped input (e.g., `InfoDynamics.fit(raw_text)`, `Scalogram.fit(single_series)`):**
- Don't force it through `check_estimator`/`parametrize_with_checks` — it will fail checks that assume i.i.d. tabular samples for reasons that are correct-for-the-domain, not bugs.
- Still apply rules 1–6 (params-only `__init__`, trailing-underscore learned attrs, `fit` returns `self`) — those are shape-agnostic and are what actually matters for `Pipeline` and `clone()` to work.

**If a transformer wraps a heavy optional dependency (encoders, morphology):**
- Guard the import inside the method that needs it (already the pattern), with an error message naming the specific extra to install — this is scikit-learn's own convention (`check_<name>_support`), not a project-specific invention.
- Keep the heavy dep entirely out of the class's `__init__`/type signature if avoidable, so `import infodynamics` never transitively imports it.

**If a test needs array inputs with edge cases (empty, single-row, all-NaN, constant-value):**
- Reach for `hypothesis.extra.numpy.arrays()` rather than hand-enumerating cases — it's already a declared dependency and finds edge cases hand-written fixtures miss.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| scikit-learn 1.9.0 | Python 3.11–3.14 | Verified: 1.9.0 shipped CPython 3.14 wheels in June 2026; matches project's Python 3.14.x constraint and the currently installed venv |
| numpy 2.4.6 | Python 3.14 | Confirmed via pyreadiness.org checkmark; matches installed venv |
| scipy 1.18.0 | Python 3.14 | scipy 1.16.1 (July 2025) was the first stable Python-3.14-wheel release; 1.18.0 in the venv is well past that baseline |
| tslearn extras (`all_features`) | macOS Intel | tslearn's own `pyproject.toml` caps numpy <2 and keras <3.12 on macOS Intel specifically for `torch` compatibility — irrelevant to infodynamics unless the `clustering` extra's transitive deps ever pull in `torch`-based tslearn features; current usage (`dtw_barycenter_averaging`, `softdtw_barycenter`) doesn't |
| hypothesis + numpy 2.x | Compatible | `hypothesis.extra.numpy` strategies work against numpy 2.x dtypes without special handling |

## Sources

- [Developing scikit-learn estimators](https://scikit-learn.org/stable/developers/develop.html) — verified: `__init__`/params/trailing-underscore conventions
- [BaseEstimator API](https://scikit-learn.org/stable/modules/generated/sklearn.base.BaseEstimator.html) — verified: `get_params`/`set_params` contract
- [check_estimator](https://scikit-learn.org/stable/modules/generated/sklearn.utils.estimator_checks.check_estimator.html) / [parametrize_with_checks](https://scikit-learn.org/stable/modules/generated/sklearn.utils.estimator_checks.parametrize_with_checks.html) — verified: conformance-check mechanics
- [scikit-learn-contrib/project-template](https://github.com/scikit-learn-contrib/project-template) — verified: reference skeleton, not adopted wholesale
- [sktime dependency management guide](https://www.sktime.net/en/stable/developer_guide/dependencies.html) — fetched directly, HIGH confidence: core/soft/developer taxonomy, `_safe_import`, version-bound discipline
- [sktime pyproject.toml](https://github.com/sktime/sktime/blob/main/pyproject.toml) — referenced via search
- [tslearn pyproject.toml](https://raw.githubusercontent.com/tslearn-team/tslearn/main/pyproject.toml) — fetched directly, HIGH confidence: real extras structure
- [ruptures pyproject.toml](https://raw.githubusercontent.com/deepcharles/ruptures/master/pyproject.toml) — fetched directly, HIGH confidence: confirms "no extras" is a valid pattern for genuinely small libraries
- [stumpy pyproject.toml / GitHub](https://github.com/stumpy-dev/stumpy) — cross-checked via search, MEDIUM confidence
- [scikit-learn `_optional_dependencies.py`](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/utils/_optional_dependencies.py) — fetched directly, HIGH confidence: the exact lazy-check-with-message pattern already used in this codebase
- [Hypothesis: NumPy and Pandas](https://hypothesis.readthedocs.io/en/latest/numpy.html) — MEDIUM confidence, cross-checked via search
- [PEP 810 — Explicit lazy imports](https://peps.python.org/pep-0810/) — verified: confirms this is a Python 3.15+ feature, not applicable to this project's 3.14.x constraint
- [pyreadiness.org/3.14](http://pyreadiness.org/3.14/) and [scikit-learn PyPI](https://pypi.org/project/scikit-learn/) — MEDIUM confidence, cross-checked: Python 3.14 ecosystem compatibility
- [src-layout vs flat-layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) — MEDIUM confidence; noted as **[LATER]** context only, since packaging-layout changes are out of scope this milestone
- Direct repo inspection: `setup.py`, `infodynamics/embedding.py`, `infodynamics/morphology.py`, `infodynamics/clustering/barycenter.py`, installed venv (`sklearn 1.9.0`, `numpy 2.4.6`, `scipy 1.18.0`) — HIGH confidence, primary source (the actual codebase)

---
*Stack research for: infodynamics-core extraction (sklearn-compatible scientific Python library tooling)*
*Researched: 2026-07-13*

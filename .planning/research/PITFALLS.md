# Pitfalls Research

**Domain:** Package extraction from a monorepo + breaking namespace reorg + sklearn-compatible scientific Python library
**Researched:** 2026-07-13
**Confidence:** HIGH (sklearn API contract, general refactor/extraction pitfalls) / MEDIUM (project-specific severity estimates)

This research is grounded directly in the current `infodynamics` codebase (file:line citations below), not generic advice. Every "Critical Pitfall" either already exists in the code (and will bite during the reorg if not addressed) or is a well-documented failure mode of the exact operation this milestone performs (extract + rename + sklearn-ify).

## Critical Pitfalls

### Pitfall 1: Estimators that only implement `fit`/`fit_transform` are not real Pipeline steps

**What goes wrong:**
An estimator that overrides `fit_transform` directly but never defines a standalone `transform()` method can only be used as the **last** step of an `sklearn.pipeline.Pipeline`. `Pipeline._validate_steps()` requires every intermediate step to expose both `fit` (or `fit_transform`) **and** `transform`; if `transform` is missing, pipeline construction/fitting raises `TypeError: All intermediate steps should implement fit and transform...`. Even where it doesn't raise (single-estimator use), the estimator can't do the thing Pipelines exist for: fit on train data, then `.transform()` new/held-out data without refitting.

**Why it happens:**
It's tempting to write `fit_transform` as `self.fit(X); return self.<computed_attr>` because that's simpler than separating "compute state" (`fit`) from "apply state" (`transform`). This looks correct in isolation (tests call `fit_transform` directly) and only breaks once the estimator is chained as a non-terminal Pipeline step.

**Already present in this codebase — confirmed, not hypothetical:**
- `WindowedRollingDistance` (`infodynamics/time_series.py:154-224`) — `fit` + `fit_transform` only, no `transform`
- `InfoDynamics` / `MultiscaleInfoDynamics` (`infodynamics/pipeline.py`) — same pattern
- `Scalogram`, `FooteNovelty` (`infodynamics/scalogram.py`) — same pattern

Every public transformer in the current library has this gap. This is the single biggest reason "sklearn Pipeline-composable" is not yet true, and it's the core technical work this milestone must do — not an edge case to guard against.

**How to avoid:**
For every transformer, implement `transform(X)` that applies already-fitted state (reading `self.*_` attributes set in `fit`) and have the default `TransformerMixin.fit_transform` do the composition (`fit(X).transform(X)`), or explicitly keep a custom `fit_transform` **in addition to** a real `transform`. Decide per-estimator whether `transform(X)` on new data is even semantically meaningful here (e.g., "novelty of unseen text relative to a fitted window" may not be) — if it isn't, that's a legitimate design constraint to document, not a bug to silently work around forever, but it must be a conscious API decision, not an accident of "we never got around to writing transform."

**Warning signs:**
- `grep -rn "def fit_transform" infodynamics/` returns hits where the same file has no matching `def transform`
- `sklearn.pipeline.Pipeline([("a", EstimatorA()), ("b", EstimatorB())])` raises at construction/fit time when `EstimatorA` is non-terminal
- Any estimator whose `fit_transform` signature differs from `fit(X).transform(X)` composition (e.g., returns a `dict` instead of an array — see Pitfall 2)

**Phase to address:**
Dedicated "make estimators Pipeline-composable" phase, done *after* the namespace reorg lands (so `transform` methods are written once against final module locations, not twice) and *before* "tests green" is declared — this is the actual acceptance bar for the sklearn-compat requirement, not a nice-to-have.

---

### Pitfall 2: `fit_transform` returning a `dict` instead of an array-like breaks Pipeline chaining

**What goes wrong:**
`WindowedRollingDistance.fit_transform` returns `{"N_hat": ..., "T_hat": ..., "R_hat": ...}` (`infodynamics/time_series.py:205-224`), and `InfoDynamics.fit_transform` / `MultiscaleInfoDynamics.fit_transform` return dicts too (`infodynamics/pipeline.py:133-151, 261-285`). A `Pipeline` feeds one step's `.fit_transform()` output as the **X** input to the next step's `.fit()`. If step N returns a dict, step N+1's `fit(X, y)` receives a dict where it expects an array — it will either crash inside `_validate_data`/`np.asarray` or silently do the wrong thing (e.g., iterate dict keys as "samples").

**Why it happens:**
Returning a rich, self-describing dict is the *right* choice for a terminal/user-facing call (`novelty = model.fit_transform(text)`), but is wrong for a non-terminal Pipeline step, which needs a single homogeneous array. These are two different contracts and the codebase currently only serves the first one.

**How to avoid:**
Separate "the value used for Pipeline chaining" (a 2D array or the single primary signal) from "the rich result object" (dict/dataclass with named fields, `sd` estimates, etc.). Options: (a) `transform()` returns a plain array (e.g., stacked `[N_hat, T_hat, R_hat]` or just the primary novelty column) while a separate `.signal_` / `.result_` attribute (already the existing convention — see `self.signal_` in `pipeline.py:117`) holds the rich dict for direct/non-Pipeline use; (b) accept that these particular estimators are Pipeline-*terminal* by design and enforce that with a naming/doc convention rather than pretending they chain. Decide explicitly per-estimator; don't leave it implicit.

**Warning signs:**
- `fit_transform`/`transform` return type is `dict` anywhere in the public estimator surface
- A hand-built `Pipeline([...])` smoke test (add one — see "Looks Done But Isn't" below) fails or produces nonsense on the second step

**Phase to address:**
Same phase as Pitfall 1 (Pipeline-composability phase) — these two are two faces of the same design decision and should be resolved together, per-estimator, with the decision recorded (e.g., in ARCHITECTURE.md / docstrings) rather than left as an accident.

---

### Pitfall 3: Constructor doing resolution work instead of storing params as-is (get_params/set_params contract violation)

**What goes wrong:**
`WindowedRollingDistance.__init__` (`infodynamics/time_series.py:56-61`) resolves the `measure` string into a callable *inside* `__init__`:
```python
if measure in DISTANCES:
    self.measure = DISTANCES[measure]
elif callable(measure):
    self.measure = measure
else:
    raise AttributeError(...)
```
This violates scikit-learn's hard constructor contract: `__init__` must do **no validation and no logic**, and every constructor arg must be stored on `self` **verbatim**, under the exact same name. Consequences: `get_params()["measure"]` returns a resolved callable, not the string the user passed, so `repr(estimator)` and equality/introspection no longer reflect what was requested; `sklearn.base.clone()` — which rebuilds an estimator from `get_params()` — will silently produce an estimator whose `measure` param is now "some function object" rather than `"cosine"`, which is fragile the moment `DISTANCES` mapping changes independent of the callable's identity, and it means `set_params(measure="euclidean")` and `WindowedRollingDistance(measure="euclidean")` are not guaranteed equivalent if any caching/hashing assumes params are the literal user input (e.g. joblib memoization keyed on params). This also raises `AttributeError` from inside `__init__` for a bad string, which is itself a contract violation (sklearn requires validation deferred to `fit`, precisely so `set_params` — used internally by `GridSearchCV`/`clone` — never has to run untrusted-input validation logic twice).

**Why it happens:**
It's the "obviously correct" thing to do in a plain Python class — validate/normalize eagerly at construction. sklearn's constructor contract is the opposite of normal Python instincts, and is easy to violate without any test failing (nothing currently asserts on `get_params()`/`clone()` round-trips because the suite predates the Pipeline-composability requirement).

**Compare with the correct pattern already in this codebase:** `InfoDynamics.__init__` (`infodynamics/pipeline.py:73-82`) and `Scalogram.__init__` (`infodynamics/scalogram.py:88-89`) both just do `self.measure = measure` — raw storage — and resolve/validate the string inside `fit`. Use these two as the reference pattern when fixing `WindowedRollingDistance`.

**How to avoid:**
- Constructor rule: every `__init__` parameter is assigned to `self.<same_name>` with zero transformation, zero validation, zero branching.
- Move the `measure` string→callable resolution (and the `AttributeError` it currently raises) into `fit()`.
- Add a one-time automated check across all public estimators: `sklearn.utils.estimator_checks.check_parameters_default_constructible` and a manual `get_params()` round-trip test (`assert type(est)(**est.get_params()).get_params() == est.get_params()`) for each estimator, run as part of the test suite rather than ad hoc.

**Warning signs:**
- Any `if`/`elif`/`raise`/function-call (beyond a bare `self.x = x`) inside `__init__`
- `self.<attr>` set in `__init__` under a different name than the constructor argument, or set to a *derived* value
- `clone(fitted_estimator).get_params() != fitted_estimator.get_params()`

**Phase to address:**
Pipeline-composability phase (same as Pitfalls 1–2) — this is a small, mechanical fix per estimator, but must be done deliberately with a `get_params` round-trip check added to the test suite so it can't silently regress later. Flag `WindowedRollingDistance` by name in that phase's plan since it's the confirmed violator.

---

### Pitfall 4: Module-level mutable caches break estimator statelessness and reproducibility

**What goes wrong:**
Two module-level caches exist today: `_MODEL_CACHE` in `infodynamics/embedding.py:8` (caches `SentenceTransformer` instances by model name, then calls `.to(device)` **in place** on the cached object) and `_PIPELINE_CACHE` in `infodynamics/morphology.py:9` (caches spaCy/UDPipe pipelines by `(lang, feature_group, model_path)`). Already flagged in `.planning/codebase/CONCERNS.md` as fragile for the dashboard's use case; it's a bigger problem for sklearn compatibility specifically, because:
- Two `Encoder(device="cpu")` and `Encoder(device="cuda")` instances sharing the same `model_name` will fight over the same cached model object's device, so the *second* `.encode()` call silently changes behavior based on *unrelated* prior calls — a violation of the basic sklearn expectation that a fitted/configured estimator's behavior depends only on its own params and the data passed to it.
- `sklearn.base.clone()` and joblib-based parallelism (`n_jobs`, `GridSearchCV`, `cross_val_score`) assume estimators don't share hidden global state across "independent" clones; global caches undermine that assumption in ways that are very hard to debug (non-deterministic results depending on call order/thread interleaving).

**Why it happens:**
Global caches are the obvious way to avoid re-downloading/re-loading expensive models (HuggingFace, UDPipe) during a single script run — a reasonable optimization for the *dashboard's* batch-processing use case, but the wrong default for a general-purpose library whose estimators may be cloned, parallelized, or used with differing configs in the same process.

**How to avoid:**
- Key the cache by every parameter that affects returned-object behavior, not just `model_name` — at minimum include `device` in the `_MODEL_CACHE` key, and never mutate a cached object in place (`.to(device)`) — instead return a device-specific copy or construct without mutation.
- Prefer keeping the cache but making it a documented, opt-out **performance optimization** with a clearly stated invariant, or move to `functools.lru_cache`/`joblib.Memory` (disk-based) which has more predictable semantics.
- Do not let the reorg silently paper over this — it's an existing bug, not something introduced by the refactor, so the "numerical output unchanged" constraint doesn't protect it from being fixed (fixing a bug is not a numerical *drift* of the documented/intended behavior, as long as the fix target is agreed).

**Warning signs:**
- Any `Dict[..., "object"] = {}` at module scope in a file that also defines a `BaseEstimator`
- In-place mutation (`.to(...)`, `.eval()`, attribute assignment) on a cached object
- Flaky test results that depend on test execution order (a classic symptom of shared global state)

**Phase to address:**
Flag for the Pipeline-composability phase as a "should fix" (not a hard blocker for basic Pipeline chaining, since it doesn't break `get_params`/`transform`), but call it out explicitly in that phase's plan so it isn't silently deferred forever — at minimum, key the cache by `device` before closing out the milestone.

---

### Pitfall 5: Deleting `shipping.py`/`cache_contract.py` without updating `setup.py` entry_points and dependent tests in the same change

**What goes wrong:**
`setup.py` currently registers four console scripts pointing directly at code slated for deletion:
```python
entry_points={'console_scripts': [
    'infodynamics-pack=infodynamics.shipping:pack_main',
    'infodynamics-pull=infodynamics.shipping:pull_main',
    'infodynamics-verify=infodynamics.shipping:verify_main',
    'infodynamics-init-project=infodynamics.shipping:init_project_main',
]}
```
And `tests/test_manifest.py` directly imports the modules being removed:
```python
from infodynamics.cache_contract import (...)
from infodynamics.shipping import pack_project, pull_project, verify_project
```
If `infodynamics/shipping.py` and `infodynamics/cache_contract.py` are deleted without touching `setup.py` and `tests/test_manifest.py` in the *same* commit, two independent failures follow: (a) `pip install -e .` still advertises now-broken console scripts (they'll fail with `ModuleNotFoundError` the first time anyone runs `infodynamics-pack`, which for a dev environment usually isn't until much later — a silent landmine); (b) `pytest` fails at **collection** for `test_manifest.py` with an `ImportError`, which — depending on `--continue-on-collection-errors` — can either abort the whole run or report a spurious-looking single-file failure that masks whether anything else broke.

**Why it happens:**
Code deletion PRs tend to focus on "delete the module and its direct test file" and miss the *outward-facing* references: packaging metadata (`entry_points`, `install_requires`/`extras_require` referencing dropped deps), and any test file that imports the deleted module even if that test file's *name* doesn't obviously map to it (`test_manifest.py` doesn't scream "tests shipping.py").

**How to avoid:**
- Before deleting a module, `grep -rn "<module_name>" .` across the *entire* repo (not just `infodynamics/` and `tests/`) — include `setup.py`, `README.md`, any `.cfg`/`.toml`, docstrings/comments in surviving files, and CI config — and resolve every hit as part of the same change.
- Treat "delete `shipping.py`" and "delete `tests/test_manifest.py`" and "remove the four `console_scripts` entries + associated `install_requires`" as one atomic unit of work, not three tickets that might land separately.
- After deletion, `pip install -e . && infodynamics-pack --help` should fail with "command not found" (proving the stale entry point is gone), and `pytest --collect-only` should show zero collection errors.

**Warning signs:**
- `grep -rn "shipping\|cache_contract\|build_dashboard_artifacts" setup.py tests/ README.md` returns any hit after the deletion commit
- `pytest --collect-only` reports `ERROR collecting tests/...` for any file
- `pip install -e .` succeeds but `infodynamics-pack` at the shell resolves to a broken entry point rather than "command not found"

**Phase to address:**
The removal/deletion phase itself (first phase of this milestone). This should be the phase's own verification checklist, not deferred to "tests green" at the end where the root cause is harder to trace back.

---

### Pitfall 6: A single leftover import breaks `pytest` collection for the whole suite, masking real pass/fail signal

**What goes wrong:**
pytest resolves all test files at collection time before running anything. An `ImportError` in *one* test file (e.g., a leftover `from infodynamics.shipping import ...` after `shipping.py` is deleted) produces a collection error for that file. Depending on flags/CI config this can (a) still run the other 8 test files and report a clear single-file failure — the *good* outcome — or (b) if collection errors aren't isolated in the runner's reporting, get lost in noise, making it easy to eyeball a giant red CI log, see "tests failed," and not distinguish "1 broken import" from "12 estimators broke behaviorally." For a milestone whose gate is "test suite passes," an import-time failure and a genuine regression must not look the same in the report.

**Why it happens:**
Collection errors and assertion failures both show up as pytest failures; distinguishing them requires actually reading the traceback, which is easy to skip when eyeballing a large diff/refactor's CI run "green vs red."

**How to avoid:**
- Run `pytest --collect-only -q` as a fast, separate first gate before running the full suite in each phase of the reorg — if this doesn't cleanly list every test, stop and fix imports before evaluating behavioral correctness.
- After any file move/deletion, run the full suite once immediately (don't batch several deletions before testing) so an import error is attributable to a single, obvious change.
- Consider `pytest -p no:cacheprovider --continue-on-collection-errors` explicitly during the reorg (surfaces *all* broken imports across all files in one pass) but treat any collection error as a hard blocker, not a warning.

**Warning signs:**
- CI/test run reports fewer collected tests than the pre-refactor baseline (81 test functions per `.planning/codebase/TESTING.md`) without a corresponding, deliberate test deletion
- Traceback shows `ImportError`/`ModuleNotFoundError` rather than `AssertionError`

**Phase to address:**
Every phase that touches imports (deletion phase, namespace-reorg phase) should end with `pytest --collect-only -q` as an explicit, cheap verification step — cheaper than running the full suite, and it isolates this failure mode immediately.

---

### Pitfall 7: "Pure refactor" claims hide accidental numerical drift because there's no before/after golden-output check

**What goes wrong:**
PROJECT.md is explicit: "Refactor, not rewrite — no change to the numerical output of surviving analysis code." But the current test suite (per `.planning/codebase/TESTING.md`) asserts on *specific literal values* per function (`pytest.approx(0.2780719051126376)`, `np.allclose(res_array, np.array([0.54245752, -0.26438562, 0.0]))`) scattered across 9 files, not a single end-to-end "golden output" fixture for the full pipeline. During a large namespace reorg it's easy to: rename `measure="cosine"` handling, touch `_validate_data`, reorder how `signal.update()` builds dicts, or fix the `averaging_weigts` typo (Pitfall 8) — each individually "obviously fine" — and have the *combination* silently shift a downstream float by float-epsilon or reorder an array, which a scattered assertion suite might not catch if the specific function touched wasn't the one asserted on, or if a test was deleted/adapted alongside the change that would have caught it.

**Why it happens:**
Confidence in "this is a pure refactor" comes from local reasoning about each diff hunk, not from an empirical check against the pre-refactor system's actual output on a realistic input. Local reasoning is exactly what misses second-order interactions (e.g., a resolved-callable object identity change from Pitfall 3 altering `repr()`-based caching elsewhere, or a global cache key change from Pitfall 4 altering which cached model instance handles which call).

**How to avoid:**
- Before starting the reorg, capture a **golden-output snapshot**: run the current `InfoDynamics`/`MultiscaleInfoDynamics`/`WindowedRollingDistance`/`SignalClusterer`/`Scalogram`/`FooteNovelty` pipelines end-to-end on 2–3 small, fixed, checked-in inputs (e.g., the existing `TEXT`/`MULTISCALE_TEXT` constants already used in tests, per `.planning/codebase/TESTING.md`), and pickle/save the exact numeric outputs (novelty/transience/resonance arrays, SSM, scalogram matrix, cluster labels+barycenters) to a fixture file.
- After each reorg phase, re-run the same inputs and assert `np.allclose` against the golden snapshot (with the same tolerances already used in the existing suite: `atol=1e-8` style). This is a *stronger* and *cheaper* check than trusting scattered unit assertions to happen to cover whatever moved.
- Explicitly separate "bugs we're fixing on purpose during this milestone" (e.g., `averaging_weigts` typo, `_MODEL_CACHE` device bug) from "pure moves" — golden-output tests should be updated/waived *only* for the former, with the waiver called out in the phase's plan, never silently.

**Warning signs:**
- No single test asserts on the *combined* output of a full `InfoDynamics.fit_transform()` call against a snapshot saved *before* the refactor began
- A diff touches numeric computation (not just imports/location) but the phase's verification is "existing unit tests still pass" rather than "output matches pre-refactor golden snapshot"

**Phase to address:**
Set up the golden-output snapshot as a **prerequisite step before Phase 1 of the milestone** (capture baseline against the pre-refactor `HEAD`), then re-verify it at the close of every subsequent phase — this is the single highest-leverage guard against the "accidental numerical drift" risk this project explicitly worries about.

---

### Pitfall 8: Bundling opportunistic bug fixes into the "pure" reorg makes regressions hard to bisect

**What goes wrong:**
The reorg is an obvious moment to also fix the `averaging_weigts` typo (`infodynamics/time_series.py:23,45,54,65`), the unfinished `_validate_data` (same file, line 70), or the `_MODEL_CACHE` device bug (Pitfall 4) — they're right there, in files already being touched. Doing so bundled into the same commit/phase as a pure namespace move means that if the golden-output check (Pitfall 7) fails afterward, it's ambiguous whether the *move* broke something or the *fix* changed behavior as intended — `git bisect` and code review both get harder.

**Why it happens:**
Refactor fatigue + "while I'm in here" instinct; also genuinely efficient in the moment since the file is already open and under review.

**How to avoid:**
Two-lane discipline: (1) pure moves/renames — zero behavior change, verified against the golden-output snapshot — land as their own commits/phase; (2) intentional bug fixes (typo rename, cache key fix, validation completion) land as separate, individually-described commits that are *expected* to change golden output in a specific, documented way (and update the snapshot deliberately). Never mix the two in one diff hunk.

**Warning signs:**
- A commit message says "reorg X" but the diff also touches conditional logic, default values, or cache keys
- The golden-output snapshot needs updating in a commit whose stated purpose is "move module Y to package Z"

**Phase to address:**
Applies across every phase; enforce as a review/commit-hygiene rule stated once in the roadmap rather than per-phase. Worth calling out explicitly in the deletion and namespace-reorg phases since that's where the temptation is highest (`WindowedRollingDistance` gets touched heavily in both Pitfall 3's fix and any reorg move).

---

### Pitfall 9: `infodynamics/__init__.py` as a single choke point for the reorg — and a one-way dependency rule that's easy to violate

**What goes wrong:**
`infodynamics/__init__.py` currently re-exports the entire public surface from six submodules in one place (`infodynamics/__init__.py:3-8`). Two risks specific to the "modality-agnostic core + `infodynamics.text` on-ramp" split:
1. **Import-order fragility during the move**: if the reorg is done incrementally (some modules moved, some not) `__init__.py` will reference a mix of old and new paths mid-transition; any accidental circular import (e.g., a new `infodynamics/text/pipeline.py` importing from `infodynamics` top-level, while `infodynamics/__init__.py` imports from `infodynamics.text`) produces a `ImportError: cannot import name X from partially initialized module` that's confusing to debug because it only manifests depending on *which* module is imported first.
2. **Direction-of-dependency violation**: the core/on-ramp split requires `infodynamics.core` (or equivalent) to never import from `infodynamics.text` — text is an optional on-ramp *on top of* the core, not a peer. It's easy to accidentally introduce a reverse import (e.g., a shared constant or helper that "should" live in core gets referenced from a core module that got moved incorrectly, or a type hint import for `Encoder`/`MorphologicalEncoder` leaks into a core file for convenience).

**Why it happens:**
`__init__.py` re-export lists are edited by hand and don't get any tooling feedback until something actually breaks at import time; and it's tempting to reach for "just import the concrete class from wherever it's used" during a fast-moving reorg rather than route everything through public interfaces.

**How to avoid:**
- Move modules in dependency order: leaf modules with no internal `infodynamics.*` imports first (metrics, util), then modules that only depend on those, working up to `pipeline.py`-equivalents last. Update `__init__.py` only after all modules it references have landed at their final paths — don't leave it half-migrated across multiple commits.
- Add (and keep green through the reorg) a simple import-direction check: a one-line test that does `import ast` over `infodynamics/text/**/*.py` and asserts no module there is imported *by* anything under `infodynamics/core/**` (or equivalent path names once decided) — or more simply, a `grep -rn "from infodynamics.text\|import infodynamics.text" infodynamics/` (excluding the `text/` dir itself) that must return nothing.
- Run `python -c "import infodynamics"` (a full top-level import) after every reorg commit — this alone catches most circular-import breakage immediately, before running the whole test suite.

**Warning signs:**
- `ImportError: cannot import name X from partially initialized module 'infodynamics' (most likely due to a circular import)`
- Any `from infodynamics.text import ...` (or `from infodynamics import <text-only-symbol>`) appearing inside a file meant to be modality-agnostic
- `__init__.py` diff spans multiple unrelated commits instead of landing atomically once the target layout is stable

**Phase to address:**
Namespace-reorg phase, with `python -c "import infodynamics"` and the one-directional-dependency grep/check added as that phase's cheapest, fastest verification gate (run before the full test suite, same rationale as Pitfall 6).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| Keep `WindowedRollingDistance`'s eager `measure` resolution in `__init__` "for now" and defer the `get_params` fix | Less churn in this milestone | `clone()`/`GridSearchCV`/hashing-based caching remain unreliable for this estimator specifically | Never — this is the one estimator the milestone's own acceptance bar (get_params/set_params contract) directly targets; fixing it is in-scope work, not debt |
| Leave `fit_transform`-only estimators without `transform()` and document them as "Pipeline-terminal only" | Avoids deciding what `transform(X_new)` should mean for a novelty signal semantically | Silently caps composability to "last step only," which may not satisfy "chain text on-ramp → analysis" | Acceptable **only if** the decision is explicit and documented per-estimator, not an oversight |
| Keep module-level `_MODEL_CACHE`/`_PIPELINE_CACHE` unkeyed by `device` | Saves a small amount of rework in `embedding.py`/`morphology.py` | Reproducibility bugs that are extremely hard to reproduce/debug later (order-dependent, cross-instance) | Acceptable short-term only if flagged with a `# FIXME` and covered by an explicit backlog item — not something to silently carry past this milestone given it directly undermines "genuinely composable" estimators |
| Batch several file deletions/moves into one large commit "to save review overhead" | Fewer commits to review | Collection/import errors become hard to bisect to a specific change (Pitfall 6, 8) | Never during this milestone — the whole point of phased extraction is bisectable, verifiable steps |
| Fix the `averaging_weigts` typo silently while touching that file for the reorg anyway | Slightly less code churn than a separate change | Conflates "pure move" with "intentional API change" in the same diff, breaking golden-output bisectability (Pitfall 8) | Acceptable only as its own explicitly-labeled commit/phase step, with the golden-output snapshot updated deliberately alongside it |

## Integration Gotchas

Not a typical "external API" project, but the equivalent internal integration seams matter just as much here.

| Integration | Common Mistake | Correct Approach |
|-------------|-----------------|-------------------|
| `infodynamics.text` on-ramp → core analysis estimators | Text on-ramp classes (`InfoDynamics`, `MultiscaleInfoDynamics`) hard-import concrete core classes (`WindowedRollingDistance`, `Scalogram`) by class name rather than composing over the public core API | Keep the on-ramp depending only on the core's curated public exports (whatever `infodynamics/__init__.py`/`infodynamics.core.__init__` exposes), not on internal core module paths — so core internals can keep moving without touching `infodynamics.text` |
| `setup.py` `extras_require` (`embedding`, `morphology`, `clustering`, `viz-projection`) vs. deleted `shipping`-only deps | Removing `shipping.py`/`cache_contract.py` without checking whether any `install_requires`/`extras_require` entries existed only to support them (none currently do — `shipping.py` is stdlib+subprocess only per CONCERNS.md — but re-verify at deletion time) | Cross-check `setup.py` `install_requires`/`extras_require` against actual imports of surviving code after each deletion, not just entry_points |
| sklearn `Pipeline`/`GridSearchCV`/`clone()` (not literally "used" yet in this codebase, but the compatibility target) | Assuming "looks like BaseEstimator/TransformerMixin" is sufficient without ever constructing an actual `Pipeline([...])` or calling `clone()` in a test | Add at least one integration test per public estimator that builds a real 2-step `Pipeline` (e.g., a trivial `FunctionTransformer` feeding into it, or two core estimators chained) and one `clone()` round-trip test — this is the only way to catch Pitfalls 1–3 mechanically rather than by code review |

## Performance Traps

Lower priority for this milestone (no scale-up work planned), but worth a note since the reorg touches the exact files where these live.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|-----------------|
| Global model/pipeline caches unkeyed by device/config (Pitfall 4) reused across many `fit()` calls in a script/notebook | Non-deterministic timing/results depending on call order; unexpectedly slow first call per unique key | Key caches by every param that changes behavior; document cache as best-effort optimization, not a correctness guarantee | Breaks first under mixed-device usage (CPU+GPU in the same process) or parallel `n_jobs > 1` Pipeline/GridSearch usage — plausible once this library is actually plugged into a Pipeline, which is this milestone's whole point |
| `_validate_data` doing minimal validation (CONCERNS.md: "UNFINISHED") | Invalid input silently passed through with only a generic warning, failing much later with a confusing error deep in `calc_signal` | Complete validation in `fit()` (shape checks, dtype checks) per sklearn convention — validation belongs in `fit`, not `__init__` (ties into Pitfall 3) | Breaks whenever a real Pipeline feeds this estimator unexpected shapes from an upstream step — much more likely once composability lands |

## Security Mistakes

Most of the existing security-adjacent surface (`shipping.py` subprocess/tar/rclone handling, path traversal on pack/pull) is **leaving with the dashboard split** and is out of scope for the surviving core. One item is worth carrying forward:

| Mistake | Risk | Prevention |
|---------|------|------------|
| Assuming "we deleted `shipping.py` so subprocess/path risk is gone" without checking for latent copies (e.g., someone re-adds a thin bridge, or a docstring/example still shows shell-unsafe patterns) | False sense of security if any subprocess-invoking helper reappears in the core package later without the same list-args-not-shell=True discipline the original code used (per CONCERNS.md, the original code did this correctly) | If any subprocess/file-path handling is ever reintroduced in core, carry forward the existing safe pattern (list args, no `shell=True`, path validation against `..`/symlinks) rather than reinventing it |

## API/DX Pitfalls

(Adapted from "UX Pitfalls" — the "users" of this library are downstream Python callers composing it into pipelines.)

| Pitfall | User Impact | Better Approach |
|---------|--------------|-------------------|
| Curated top-level `__init__.py` exports silently change which names are importable after the reorg, with no deprecation shim | Every downstream caller (including the future dashboard repo) hits `ImportError` on upgrade with no guidance on the new path | Since backward-compatible import paths are explicitly out of scope for this milestone, at minimum ship a clear CHANGELOG/migration note listing old→new import paths for every symbol that moved — even without code-level shims, a documented mapping turns a confusing `ImportError` into a 30-second fix for consumers |
| Estimators that raise from `__init__` (e.g., `WindowedRollingDistance`'s current `AttributeError` on bad `measure`) surface errors at construction time instead of at `fit`/`set_params` time | Confusing for anyone building a `Pipeline`/`GridSearchCV` param grid — invalid combinations should fail predictably inside `fit`, not sporadically at estimator-construction time depending on where in a pipeline definition it's built | Move all validation to `fit()`, per Pitfall 3 |
| `dict`-returning `fit_transform` (Pitfall 2) looks like an array-like at a glance (has `.keys()`... not `.shape`) | Confusing `AttributeError`/`TypeError` several calls downstream in a Pipeline rather than an immediate, clear error at the point of misuse | Either return true array-likes from anything meant to chain, or raise a clear, immediate error if someone tries to use a Pipeline-terminal-only estimator as a non-terminal step (sklearn's own `_validate_steps` mostly does this already — lean into it rather than fighting it) |

## "Looks Done But Isn't" Checklist

- [ ] **"sklearn Pipeline-composable"**: Often missing an actual `Pipeline([...])` integration test — verify at least one real multi-step `Pipeline` is constructed and both `.fit_transform()` and `.transform()` (on different data than was fit) are exercised in the test suite, not just `BaseEstimator`/`TransformerMixin` inheritance
- [ ] **"get_params/set_params work"**: Often missing a round-trip check — verify `clone(estimator)` and `type(estimator)(**estimator.get_params()) == estimator.get_params()` for every public estimator, not just "it has `BaseEstimator` as a base class"
- [ ] **"Tests pass"**: Often missing the distinction between "collection succeeded and assertions passed" vs. "collection silently dropped a file" — verify `pytest --collect-only -q` test count matches expectations (no unexplained drop from the pre-refactor 81 test functions) before trusting a green run
- [ ] **"Dashboard code fully removed"**: Often missing stale references outside `infodynamics/` and `tests/` — verify `grep -rn "dashboard\|shipping\|cache_contract\|build_dashboard_artifacts" setup.py *.md .github/ 2>/dev/null` (adjust for actual CI config location) returns nothing after the removal phase
- [ ] **"Namespace reorg complete"**: Often missing a check that `infodynamics.text` never gets imported from core — verify with a one-line dependency-direction check (Pitfall 9), not just "the tests pass"
- [ ] **"No numerical drift"**: Often missing an actual before/after comparison — verify against a golden-output snapshot captured *before* the refactor began (Pitfall 7), not just "the existing unit tests, which may have moved/changed with the code they were testing, still pass"

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|-----------------|------------------|
| Estimators shipped without `transform()` (Pitfall 1) discovered late (e.g., during a downstream dashboard-repo integration attempt) | MEDIUM | Add `transform()` per estimator as a follow-up patch release; since pre-1.0 breaking changes are already accepted this milestone, this is a normal iteration, not an emergency — but it's much cheaper to catch now via a Pipeline integration test than to discover via a confused downstream consumer later |
| Golden-output snapshot reveals drift after a reorg phase already merged (Pitfall 7) | MEDIUM–HIGH depending on how many commits since | `git bisect` against the golden-output test (this is exactly why it should exist and run per-phase, not just at the end) — much cheaper if caught within the phase it was introduced in than after several more phases have layered on top |
| Stale `setup.py` entry_points / test imports discovered after merge (Pitfall 5) | LOW | Single follow-up commit removing the stale references; low cost precisely because the fix is mechanical once found — the expensive part is *discovering* it, which the `grep`/`pytest --collect-only` checks above make cheap |
| Circular import introduced mid-reorg (Pitfall 9) | LOW–MEDIUM | `python -c "import infodynamics"` immediately localizes which module pair is at fault; usually resolved by moving one import to point at the new final location or deferring it to function-local scope as a stopgap |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|--------------------|----------------|
| No `transform()` on public transformers (P1) | Pipeline-composability phase | Real `Pipeline([...])` construction + `.transform()` on unseen data, per estimator, in the test suite |
| `fit_transform` returns dict, breaks chaining (P2) | Pipeline-composability phase | Same Pipeline integration test as P1 catches this automatically |
| `WindowedRollingDistance.__init__` resolves params eagerly (P3) | Pipeline-composability phase | `get_params()`/`clone()` round-trip test per public estimator |
| Global mutable caches (`_MODEL_CACHE`, `_PIPELINE_CACHE`) (P4) | Pipeline-composability phase (flagged "should fix") | Manual review + a device-mixing regression test if time allows; at minimum documented as a known limitation if deferred |
| Stale `setup.py` entry_points + `tests/test_manifest.py` after deleting `shipping.py`/`cache_contract.py` (P5) | Removal/deletion phase (first phase) | `grep` sweep for module names repo-wide + `pytest --collect-only -q` shows zero collection errors |
| Collection-time ImportError masking real failures (P6) | Every phase that touches imports (deletion, namespace reorg) | `pytest --collect-only -q` as a fast pre-check before the full suite, every phase |
| Accidental numerical drift during "pure" reorg (P7) | Prerequisite step before Phase 1 + re-checked at close of every subsequent phase | Golden-output snapshot (`np.allclose` against pre-refactor baseline) on 2–3 fixed inputs |
| Bug fixes bundled into "pure" move commits (P8) | Cross-cutting commit-hygiene rule, called out in deletion + namespace-reorg phases | Review checklist: does this diff change conditional logic/defaults, or only import paths/file locations? |
| `__init__.py` choke point + one-directional dependency violation (P9) | Namespace-reorg phase | `python -c "import infodynamics"` + grep-based one-directional-dependency check, every reorg commit |

## Sources

- [Developing scikit-learn estimators — scikit-learn 1.9.0 documentation](https://scikit-learn.org/stable/developers/develop.html) — constructor contract (no validation/logic in `__init__`, params stored verbatim), `set_params`/`get_params`/`clone()` semantics
- [BaseEstimator — scikit-learn 1.9.0 documentation](https://scikit-learn.org/stable/modules/generated/sklearn.base.BaseEstimator.html)
- [Pipeline throws TypeError on stateless transformers · Issue #27014 · scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn/issues/27014) — confirms `_validate_steps()` requires `transform` on all non-terminal steps
- [FunctionTransformer / stateful transformer limitations — Towards Data Science](https://towardsdatascience.com/advanced-data-preparation-using-custom-transformers-in-scikit-learn-5e58d2713ac5/) — `fit`/`transform` separation rationale
- [Set and get hyperparameters in scikit-learn — Scikit-learn course](https://inria.github.io/scikit-learn-mooc/python_scripts/parameter_tuning_manual.html)
- General monorepo package-extraction practices — [Mastering Python Monorepos: A Practical Guide](https://www.ctrix.pro/blog/mastering-python-monorepos), [Python Monorepo: an Example — Tweag](https://www.tweag.io/blog/2023-04-04-python-monorepo-1/)
- Dead-code/refactor coverage-regression risk — [Refactoring 021 - Remove Dead Code, HackerNoon](https://hackernoon.com/refactoring-021-remove-dead-code)
- Direct codebase evidence (this repo, read 2026-07-13): `infodynamics/time_series.py`, `infodynamics/pipeline.py`, `infodynamics/scalogram.py`, `infodynamics/clustering/cluster.py`, `infodynamics/embedding.py`, `infodynamics/morphology.py`, `infodynamics/__init__.py`, `setup.py`, `tests/test_manifest.py`, `.planning/codebase/CONCERNS.md`, `.planning/codebase/TESTING.md`

---
*Pitfalls research for: infodynamics package extraction / sklearn-compat refactor*
*Researched: 2026-07-13*

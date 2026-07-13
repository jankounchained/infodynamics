# Phase 1: Baseline & Removal - Research

**Researched:** 2026-07-13
**Domain:** Repo surgery (golden-output regression baseline + dead-code removal) in an existing, healthy Python package. No new external libraries are introduced — this research is grounded entirely in the current codebase, verified by direct inspection and command execution, not in library documentation.
**Confidence:** HIGH — every claim below was verified by reading the actual file or running the actual command in this repo on 2026-07-13, not inferred from the codebase-mapper docs alone.

> No `CONTEXT.md` exists for this phase (user chose to plan without a discuss-phase session). `.planning/ROADMAP.md` and `.planning/REQUIREMENTS.md` are the source of truth for scope; there is no `## User Constraints` section to reproduce.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QA-01 | Golden-output baseline captured before any refactor; core numerical outputs match it at milestone completion | Constructors/signatures for all 6 target classes cataloged below (Standard Stack → "Constructors for the baseline capture"); snapshot format + comparison strategy recommended (Architecture Patterns → Pattern 2); offline-capable fixture strategy identified (cached `sentence-transformers/all-MiniLM-L6-v2`, no network dependency) |
| RM-01 | `dashboard/` removed (preserved in git history) | Full tracked + untracked file inventory of `dashboard/` (Runtime State Inventory / removal surface below) |
| RM-02 | `cache_contract.py`, `shipping.py`, `build_dashboard_artifacts.py` removed from package | Full content catalog of all three files; confirmed zero reverse-dependency from surviving core code (Common Pitfalls → "removal is one-directional") |
| RM-03 | `infodynamics-pack`/`-pull`/`-verify`/`-init-project` console-script entries removed from `setup.py`; `pip install -e .` registers no script pointing at removed code | Exact current `entry_points` block quoted verbatim; confirmed no `extras_require`/`install_requires` entries become dead; **installed shims found in `.venv/bin/` today** — reinstall step is required, not optional (Runtime State Inventory) |
| RM-04 | `tests/test_manifest.py` removed; `pytest --collect-only` reports zero collection errors | Current baseline measured: 81 tests collected, 0 errors, today, before any change; `test_manifest.py` = 13 of those 81, and exclusively imports `cache_contract`/`shipping` — confirmed no coverage of surviving code |
| RM-05 | Repo-wide grep for removed symbols returns no hits in surviving package code, `setup.py`, or docs | Full current grep enumeration provided, with an explicit scoping call-out for two ambiguous categories (`.planning/research/*.md`, untracked `BRIEF_artifact_backbone.md`) that the plan must decide how to treat |

</phase_requirements>

## Summary

This phase has two independent halves that must execute in a specific order, not two halves of one mechanism. **Half A (baseline capture)** runs the existing, unmodified pipeline classes against 2-3 fixed text inputs and serializes their outputs. **Half B (removal)** deletes `dashboard/`, `cache_contract.py`, `shipping.py`, `build_dashboard_artifacts.py`, their `setup.py` entry points, and `tests/test_manifest.py`. Half A must be captured and committed *before* Half B runs, against pre-refactor `HEAD` — this is not just a style preference, it's how CLAUDE.md's "removed code must exist in git history before deletion" constraint and the roadmap's bisectability goal are actually satisfied in practice.

The removal surface is smaller and cleaner than it looks: `cache_contract.py` and `shipping.py` have exactly one internal dependency each (on `infodynamics.__version__` and on each other), and **zero** surviving core code imports from them or from `dashboard/`. `dashboard/build_dashboard_artifacts.py` is the only file that reaches back into core code (`infodynamics.embedding`, `infodynamics.morphology`, `infodynamics.scalogram`, `infodynamics.cache_contract`), and all of those are one-directional reads — nothing in `infodynamics/` imports from `dashboard/`. This means removal is safe to do in one clean sweep without touching any surviving module's internals.

The one non-obvious risk this research surfaces is **installed console-script shims**: `pip install -e .` has already run in this repo's `.venv`, and `.venv/bin/infodynamics-pack`, `-pull`, `-verify`, `-init-project` exist on disk right now, alongside a stale `infodynamics.egg-info/entry_points.txt`. Editing `setup.py`'s `entry_points` dict alone does **not** remove these — RM-03's actual verification (`pip install -e .` registers no script pointing at removed code) requires a re-run of `pip install -e .` (or equivalent) after the `setup.py` edit, confirmed by checking `.venv/bin/` afterward.

**Primary recommendation:** Capture the golden-output baseline first (own commit, inline fixed-text fixtures, real cached embedding model, `.npz` + JSON serialization, `np.allclose`-tolerance comparison reused as a pytest test), commit it, then remove `dashboard/` + the three core files + `setup.py` entries + `test_manifest.py` (can be one commit or several, but strictly after the baseline commit), then reinstall (`pip install -e .`) and re-run `pytest --collect-only -q` and the repo-wide grep to confirm both are clean.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Golden-output capture (run pipeline, serialize results) | Library / Core (in-process script) | Test suite (comparison reuse) | Pure Python script invoking existing `infodynamics` estimators; no server/client split exists in this project — it's a library, not a service |
| Golden-output comparison (drift detection) | Test suite | — | Belongs in `tests/` so it runs on every future phase's `pytest` invocation, per STATE.md's "re-verified at close of every subsequent phase" decision |
| File/module removal (`dashboard/`, `cache_contract.py`, `shipping.py`, `build_dashboard_artifacts.py`) | Filesystem / git | Package metadata (`setup.py`) | Removal is a repo-structure operation, not a runtime concern — no tier boundary crossed, just deletion + a `setup.py` metadata edit |
| Console-script de-registration | Package metadata (`setup.py`) | Installed environment (`.venv/bin/`, `egg-info/`) | `setup.py` is the source of truth, but the *installed* shims in `.venv/bin/` are separate, already-materialized artifacts that don't auto-update — a distinct "OS-registered state" tier that must be explicitly refreshed |
| Repo-wide dangling-reference sweep | Static analysis (grep) | Docs | No runtime tier involved; a text-search verification step over the whole tree |

## Standard Stack

No new libraries are introduced in this phase. Everything needed is already an installed, in-`install_requires`/`extras_require` dependency.

### Core (already present, no version changes needed)
| Library | Installed Version | Purpose in this phase | Why |
|---------|---------|---------|--------------|
| numpy | 2.4.6 | Serialize golden-output arrays (`.npz`), `np.allclose` comparison | Already `install_requires`; stdlib-adjacent for this project |
| pytest | 9.1.1 | `pytest --collect-only -q` health check (RM-04); house the golden-output comparison as a repeatable test | Already `extras_require['test']`; existing test-suite convention |
| sentence-transformers | 5.6.0 | Real (non-mocked) embeddings for the golden-output text fixtures, so the baseline also implicitly covers segmentation+embedding determinism ahead of Phase 2's "pure move, no drift" claim | Already `extras_require['embedding']`, already installed |
| tslearn, scipy | 0.9.0 / 1.18.0 | `SignalClusterer` (DTW distance + barycenters) needed for the cluster-labels/barycenters portion of the golden baseline | Already `extras_require['clustering']`, already installed |

**Installation:** None required — `pip list` in `.venv` confirms `sentence-transformers`, `spacy-udpipe`, `textdescriptives`, `tslearn`, `scipy`, `umap-learn` are **all already installed**, not just declared as extras. No `pip install` step is needed to execute this phase's baseline capture with real (non-mocked) components.

### Constructors for the baseline capture (verified against current source, not training data)

```python
# infodynamics/pipeline.py
InfoDynamics(
    model_name: str | None = None, encoder: object | None = None,
    segment_level: Literal["word","sentence","paragraph"] = "sentence",
    chunk_size: int = 1, measure: str | Callable = "cosine",
    window_size: int = 3, jump_size: int = 0, estimate_error: bool = False,
    device: str | None = None, batch_size: int = 32,
)
# .fit_transform(text: str) -> {"novelty": ndarray, "transience": ndarray, "resonance": ndarray}

MultiscaleInfoDynamics(
    model_name=None, encoder=None, segment_level="sentence", chunk_size=1,
    scales: Sequence[int] = (2,3,5,8,13,21), radii: Sequence[int] = (3,5,8,13,21),
    measure="cosine", device=None, batch_size=32,
)
# .fit_transform(text: str) -> {"ssm": (n,n), "scalogram": (n_scales,n), "novelty": (n_radii,n), "descriptors": dict}

# infodynamics/time_series.py
WindowedRollingDistance(
    measure: str | Callable, window_size: int, jump_size: int = 0,
    inplace_constant: int | float = 0, estimate_error: bool = False,
    averaging_weigts: ArrayLike | None = None,   # NOTE: typo, QA-02 renames this in Phase 3 — Phase 1 must use `averaging_weigts` as-is
)
# .fit_transform(X: ndarray of shape (n_samples, n_features)) -> {"N_hat","T_hat","R_hat", [+ "*_sd" if estimate_error]}

# infodynamics/scalogram.py
Scalogram(scales: Sequence[int], measure="cosine")
# .fit_transform(embeddings: (n_chunks, n_features)) -> matrix_ of shape (n_scales, n_chunks); scales < n_chunks are silently dropped

FooteNovelty(radii: Sequence[int])
# .fit_transform(embeddings) -> novelty_ of shape (n_radii, n_chunks); ssm_ of shape (n_chunks, n_chunks) also available; radii where 2r+1 > n_chunks are silently dropped

structure_descriptors(embeddings, S=None, window_size=5) -> dict  # n_chunks, mean_offdiag_sim, p90_offdiag_sim, dist_var_w5, dist_mean_w5

# infodynamics/clustering/cluster.py
SignalClusterer(
    n_clusters: int | None = None, k_range: Sequence[int] = range(2,10),
    linkage: str = "average", z_normalize: bool = True,
    barycenter_method: Literal["dba","soft_dtw"] = "dba",
)
# .fit(series: Sequence[ndarray]) -> self.labels_, self.barycenters_ (dict[int, ndarray]), self.distance_matrix_, self.n_clusters_
```

**Important constructor gotcha confirmed by reading source:** `InfoDynamics`/`MultiscaleInfoDynamics` accept `encoder=<object with .encode()>` as an alternative to `model_name`. This is how `tests/test_pipeline.py`'s `FakeEncoder` avoids network calls today — but for the **golden baseline specifically**, use a real `Encoder(model_name="sentence-transformers/all-MiniLM-L6-v2", device="cpu")` (not a fake), because Phase 2's success criterion 4 needs this same snapshot to also validate that the segmentation+embedding *move* introduced zero drift — a fake encoder would silently make that check meaningless.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Real cached `all-MiniLM-L6-v2` embeddings for the text-based half of the baseline | `FakeEncoder`-style deterministic random embeddings (as in existing tests) | Faster/network-independent, but doesn't exercise real `segmentation.py`+`embedding.py` code paths — would make Phase 2's "pure move, no drift" re-check of this snapshot meaningless for those two modules. Recommend using both: real encoder for the text→signal snapshot, deterministic seeded arrays for a second, encoder-independent snapshot of the pure-numeric classes (`WindowedRollingDistance`/`Scalogram`/`FooteNovelty` on fixed `np.random.default_rng(seed)` arrays) |
| `.npz` for array data | pickle | Pickle is Python-version-coupled and less safe to eyeball/diff; `.npz` is what the rest of the codebase already uses for cached arrays (`dashboard/cache/*.npz`), so it's the idiomatic choice even though that specific usage is being removed |
| `np.allclose` tolerance comparison | Exact `==` equality | Exact equality is what "no numerical drift" sounds like, but is not achievable in practice once Phase 3 fixes real bugs (QA-02) deliberately changing numbers on purpose, and embedding models can differ in the Nth decimal across even trivial code-path changes (e.g., batch-size-dependent floating point summation order in `sentence-transformers`). Existing tests already use `np.allclose`/`pytest.approx` throughout — follow that convention |

## Package Legitimacy Audit

**Not applicable.** This phase installs zero new packages. It only *removes* `console_scripts` entries from `setup.py`; no `install_requires`/`extras_require` entries are added, and (confirmed by grep) none become dead either — `cache_contract.py`/`shipping.py` use only stdlib (`hashlib`, `json`, `subprocess`, `argparse`, `tempfile`) plus `infodynamics.__version__`; `dashboard/`'s `pandas`/`streamlit`/`pyyaml` were never declared in `setup.py` in the first place (confirmed: zero hits for `streamlit`/`pyyaml`/`import pandas` in `infodynamics/`, `tests/`, or `setup.py`).

## Architecture Patterns

### System Architecture Diagram — current dependency shape (verified by grep + import inspection)

```text
                    ┌─────────────────────────────────────────┐
                    │  SURVIVING CORE (infodynamics/)          │
                    │  pipeline.py, time_series.py,            │
                    │  scalogram.py, clustering/, metrics.py,  │
                    │  segmentation.py, embedding.py,          │
                    │  morphology.py, viz.py, util.py          │
                    └───────────────┬───────────────────────────┘
                                    │  read-only imports (one direction)
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                        │
        ▼                                                        ▼
┌───────────────────┐                              ┌─────────────────────────┐
│ infodynamics/      │                              │ dashboard/               │
│ cache_contract.py   │◄────imports───┐             │ build_dashboard_         │
│ (manifest/checksum) │                │             │ artifacts.py             │
└─────────┬───────────┘                │             │  - imports cache_contract│
          │ imports                    │             │  - imports embedding,    │
          ▼                            │             │    morphology, scalogram │
┌───────────────────┐                  │             │  - imports root-level    │
│ infodynamics/       │                │             │    scalogram_foote_      │
│ shipping.py         │────────────────┘             │    prototype (untracked!)│
│ (pack/pull/verify   │                              └───────────┬───────────────┘
│  CLI, rclone/tar)    │                                          │
└─────────┬───────────┘                                          ▼
          │ registered as                              ┌─────────────────────────┐
          ▼                                             │ dashboard/app.py         │
┌───────────────────┐                                   │  imports bench_core,     │
│ setup.py            │                                  │  taxonomy, infodynamics. │
│ entry_points        │                                  │  viz                     │
│ [console_scripts]   │                                  └───────────┬───────────────┘
└─────────┬───────────┘                                              │
          │ materializes as (already done in this .venv!)            ▼
          ▼                                             ┌─────────────────────────┐
┌───────────────────┐                                   │ dashboard/bench_core.py, │
│ .venv/bin/          │                                  │ render_overview.py,      │
│ infodynamics-pack,   │                                  │ test_bench.py, taxonomy  │
│ -pull, -verify,      │                                  └───────────────────────────┘
│ -init-project        │
│ (STALE after removal │
│  until reinstalled)  │
└───────────────────┘

tests/test_manifest.py ──imports──► cache_contract.py + shipping.py ONLY
                                     (confirmed: no other coverage overlap)
```

**Read the arrows:** every arrow points *away* from surviving core, never *into* it. Nothing in `infodynamics/` (excluding the three files being removed) imports `dashboard` or `cache_contract` or `shipping`. This is what makes the removal safe as a single sweep.

### Pattern 1: Removal-before-verification, baseline-before-removal (commit ordering)

**What:** Two hard ordering constraints, not one:
1. Golden-output baseline capture commit(s) come **before** any removal commit — captured against pre-refactor `HEAD`, per success criterion 1's explicit wording.
2. Removal commits can be one or several, but must all land strictly after the baseline commit.

**When to use:** Always, for this phase — CLAUDE.md's "removed code must exist in git history... before deletion" constraint is satisfied automatically by git's normal history (any file that was ever committed remains recoverable via `git show <sha>:<path>` even after a later commit deletes it) — but only if the baseline-capture commit happens first and is *itself* a real commit against code that still has `dashboard/`/`cache_contract.py`/`shipping.py` present, establishing a clean bisection point before vs. after removal.

**Example (commit sequence, not prescriptive about squashing):**
```
commit 1: "test: capture golden-output baseline (pre-refactor)"
  - adds tests/golden/ fixtures + capture script, still with dashboard/ present
commit 2 (or N commits): "chore: remove dashboard/, cache/shipping infra, dead entry points"
  - rm -rf dashboard/, rm infodynamics/{cache_contract,shipping}.py,
    rm dashboard/build_dashboard_artifacts.py, edit setup.py, rm tests/test_manifest.py
  - pip install -e . (regenerate egg-info, drop stale console-script shims)
```

### Pattern 2: Golden-output snapshot as a reusable pytest test, not a one-off script

**What:** A one-time *capture* script (`.npz` + JSON write) plus a permanent *comparison* test (`tests/test_golden_baseline.py`, or similar) that loads the checked-in snapshot and re-runs the same fixed inputs through the current code, asserting `np.allclose` within tolerance. The capture script is run once by hand at Phase 1 time; the comparison test runs on every `pytest` invocation from Phase 1 onward.

**When to use:** Matches STATE.md's explicit decision — "golden-output baseline captured as prerequisite work inside Phase 1, re-verified at close of every subsequent phase." A test that's already wired into `pytest` (rather than a standalone script someone has to remember to run) is what makes "re-verified at close of every subsequent phase" actually happen without manual discipline.

**Example (structure, not full implementation — planner decides exact fixture text/paths):**
```python
# tests/golden/capture_baseline.py  (run once, by hand, before removal)
import numpy as np
from infodynamics import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.clustering import SignalClusterer
from infodynamics.embedding import Encoder

FIXTURE_A = "..."  # inline, ~15-20 sentences, committed in this file — NOT the untracked
FIXTURE_B = "..."  # 260708_radomil_collection.csv (see Common Pitfalls below)
FIXTURE_C = "..."

encoder = Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")  # already cached locally, no network needed
results = {}
for name, text in [("a", FIXTURE_A), ("b", FIXTURE_B), ("c", FIXTURE_C)]:
    results[f"{name}_novelty"] = InfoDynamics(encoder=encoder, window_size=3).fit_transform(text)
    results[f"{name}_multiscale"] = MultiscaleInfoDynamics(encoder=encoder).fit_transform(text)

series = [results[f"{n}_novelty"]["novelty"] for n in ("a", "b", "c")]
clusterer = SignalClusterer(n_clusters=2).fit(series)  # 3 series, explicit k=2 avoids k_range's k < n_series requirement

np.savez("tests/golden/baseline_arrays.npz", **{...})  # all ndarray outputs
# + a sibling JSON for dict-shaped outputs (descriptors, cluster labels/barycenters)
```

```python
# tests/test_golden_baseline.py  (runs on every pytest invocation from here on)
import numpy as np

def test_novelty_signal_matches_golden_baseline():
    baseline = np.load("tests/golden/baseline_arrays.npz")
    current = ...  # re-run the same fixture through current code
    assert np.allclose(current, baseline["a_novelty"], rtol=1e-5, atol=1e-8)
```

### Recommended Structure for the new golden-baseline artifacts
```
tests/
├── golden/
│   ├── capture_baseline.py     # one-time capture script (documents how the snapshot was made)
│   ├── baseline_arrays.npz     # checked-in ndarray outputs (novelty/transience/resonance, ssm, scalogram, foote novelty, cluster labels, barycenters)
│   └── baseline_meta.json      # descriptors dicts, cluster label→barycenter key mapping, fixture text hashes
└── test_golden_baseline.py     # pytest test reusing baseline_arrays.npz, run on every future phase close
```
This is a **new pattern** for this repo (no `tests/golden/`-style precedent currently exists — `TESTING.md` confirms "no fixture files (conftest.py) used" and all existing test data is inline module-level constants). Flagging this as a recommendation the planner should make explicit, not an established convention being followed.

### Anti-Patterns to Avoid
- **Capturing the baseline with `FakeEncoder`-only, deterministic-random embeddings:** Silently defeats Phase 2's reuse of this snapshot to confirm the segmentation/embedding *move* introduced no drift (see Alternatives Considered above). Use a real cached encoder for at least the text-based half of the snapshot.
- **Editing `setup.py`'s `entry_points` without reinstalling:** Leaves stale shims in `.venv/bin/` and a stale `infodynamics.egg-info/entry_points.txt` — RM-03's actual acceptance test (`pip install -e .` registers no removed script) will silently pass-by-omission if nobody re-runs the install and checks `.venv/bin/`.
- **Squashing baseline-capture and removal into one commit:** Defeats the explicit bisectability goal in ROADMAP.md's phase-ordering rationale ("subtractive-before-additive... so numerical drift stays bisectable at every step").
- **Treating the untracked root CSV/UDPipe files as required fixtures:** `260708_radomil_collection.csv` and `czech-pdt-ud-2.5-191206.udpipe` are untracked, and REQUIREMENTS.md explicitly marks "cleanup of untracked root clutter" out of scope this milestone — see Common Pitfalls below for the concrete tradeoff.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Serializing multiple named ndarrays to one file | A custom binary format or per-array `.npy` files with manual bookkeeping | `numpy.savez`/`numpy.load` (already a project pattern via `dashboard/cache/*.npz`, even though that specific code is being removed — the *pattern* is still idiomatic numpy) | Handles heterogeneous shapes/dtypes in one file, standard library, already used elsewhere in this exact codebase |
| Floating-point regression comparison | A custom "close enough" diff function | `numpy.allclose(..., rtol=1e-5, atol=1e-8)` | This project's own tests already use exactly this idiom (`tests/test_clustering.py`: `np.allclose(np.diag(distance_matrix), 0.0, atol=1e-8)`) — reuse the established tolerance convention rather than inventing a new one |
| Detecting whether removed symbols still have live references | A bespoke AST-walker or import-graph tool | Plain repo-wide `grep -rn` for the five symbol names (`dashboard`, `shipping`, `cache_contract`, `bench_core`, `build_dashboard_artifacts`), exactly as RM-05 specifies | RM-05's own wording specifies a grep sweep, not static analysis; a grep is sufficient given the small, already-enumerated symbol set |

**Key insight:** This phase has almost no "don't hand-roll" surface because it isn't building new functionality — it's exercising existing estimators and deleting files. The one genuine build (the snapshot capture/compare harness) should lean on numpy's built-in serialization + comparison rather than inventing anything custom.

## Runtime State Inventory

> This phase is a removal, not a rename — but RM-03's console-script entry points constitute exactly the kind of already-materialized, non-source-controlled state the standard rename/migration checklist is designed to catch. Included because it directly determines whether RM-03 actually passes.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database, no cache keyed by removed-code identifiers survives outside `dashboard/cache/` (already gitignored, deleted wholesale with `dashboard/`) | None |
| Live service config | None — no external service (n8n, Datadog, etc.) references this project | None |
| OS-registered state | **`.venv/bin/infodynamics-pack`, `-pull`, `-verify`, `-init-project` exist on disk right now** (confirmed via `ls .venv/bin/`), installed by a prior `pip install -e .` | Code edit (`setup.py` `entry_points`) alone is insufficient — must re-run `pip install -e .` (or `pip uninstall infodynamics && pip install -e .`) after the `setup.py` edit, then re-check `.venv/bin/` to confirm the four scripts are gone |
| Secrets/env vars | None — no env vars reference removed code (confirmed via INTEGRATIONS.md: "No env vars required") | None |
| Build artifacts | **`infodynamics.egg-info/entry_points.txt` currently lists all four console scripts** (confirmed by reading the file) — this is stale metadata that only refreshes on reinstall | Same reinstall step as above regenerates `entry_points.txt` to match the edited `setup.py` |

**The canonical question, answered:** After `setup.py`'s `entry_points` dict is edited and the four source files are deleted, the `.venv/bin/` shims and `infodynamics.egg-info/entry_points.txt` are **not** automatically updated — Python packaging tools only regenerate these on install/reinstall, not on source-file changes. The plan must include an explicit `pip install -e .` (or `pip install --force-reinstall -e .` if editable-install caching is a concern) step as its own task, with a verification step (`ls .venv/bin/ | grep infodynamics` should show zero of the four removed names) — this is the literal mechanism by which RM-03's stated success criterion is achieved, not an incidental detail.

## Common Pitfalls

### Pitfall 1: Untracked root clutter looks like ready-made fixture data, but isn't safe to depend on
**What goes wrong:** `260708_radomil_collection.csv` (Czech text corpus) and `czech-pdt-ud-2.5-191206.udpipe` (56MB UDPipe model) sit in the repo root and are exactly the kind of realistic, already-present data a golden-baseline capture script would reach for. `dashboard/build_dashboard_artifacts.py` even has `DEFAULT_CSV = REPO_ROOT / "260708_radomil_collection.csv"` baked in.
**Why it happens:** They're real, substantial, already-on-disk data — the path of least resistance for "2-3 fixed inputs."
**How to avoid:** Both files are **untracked** (`git status` shows `??`), and REQUIREMENTS.md's Out of Scope table explicitly lists "Cleanup of untracked root clutter... addressed separately, not this milestone (user decision)." Depending on an untracked file for a *checked-in, reproducible* golden baseline is a real tradeoff: anyone who clones the repo fresh (or the CSV/model file gets cleaned up in a future pass) cannot reproduce the baseline capture. **Recommendation:** use small, inline, committed text fixtures (following the exact pattern already in `tests/test_pipeline.py`'s `TEXT`/`MULTISCALE_TEXT` module constants) for the checked-in snapshot inputs, sized for enough sentences (~15-20) that `MultiscaleInfoDynamics`'s default `scales`/`radii` aren't all silently dropped (see Pitfall 2). The CSV/UDPipe files can still be *used* transiently for ad hoc exploration if useful, but should not be a hard dependency of the committed baseline-capture script. Flag this decision explicitly to the user if the planner considers using them anyway.

### Pitfall 2: Short fixture text silently drops scales/radii instead of erroring
**What goes wrong:** `Scalogram.fit` drops any `scale >= n_chunks`; `FooteNovelty.fit` drops any `radius` where `2*radius+1 > n_chunks`. With the existing test suite's 8-sentence `MULTISCALE_TEXT` and the class defaults (`scales=(2,3,5,8,13,21)`, `radii=(3,5,8,13,21)`), most default scales/radii get silently dropped (only `2,3,5` and `3` actually fit at n=8) — no error is raised, so a too-short fixture quietly produces a golden baseline that doesn't exercise most of the multi-scale surface it's supposed to protect.
**Why it happens:** The dropping behavior is by design (documented, sensible for real documents) but easy to overlook when hand-writing a short fixture string.
**How to avoid:** Size the 2-3 fixed inputs at ~15-20+ sentences each so that the full default `scales`/`radii` tuples actually get exercised, not silently truncated. Verify by asserting `len(model.scales_) == len(scales)` (or similar) in the capture script itself as a sanity check before serializing.
**Warning signs:** `MultiscaleInfoDynamics.scales_`/`.radii_` (the *actual*, filtered attributes) coming back shorter than the constructor's `scales`/`radii` arguments.

### Pitfall 3: Embedding determinism is hardware/device-sensitive
**What goes wrong:** ARCHITECTURE.md itself flags this: "Embedding determinism depends on the HuggingFace model and hardware (floating-point rounding may differ across devices)." If the golden baseline is captured with `device=None` (defaults to the model's own default, which can be `mps` on this Mac) and later re-verified with an explicit `device="cpu"` (or on different hardware), small floating-point differences can appear even with zero code changes.
**Why it happens:** `sentence-transformers`/PyTorch floating-point summation order differs across accelerator backends.
**How to avoid:** Pin `device="cpu"` explicitly in the capture script (not `None`), so both capture and every future re-verification run on the same, most-portable backend — trading a little speed for determinism. Use `np.allclose` with a non-zero tolerance regardless (see Standard Stack → Alternatives Considered), not exact equality, as a second layer of defense.

### Pitfall 4: Removal is one-directional, but the grep sweep will pick up historical planning docs that are not "surviving package code, setup.py, or docs" in the sense RM-05 means
**What goes wrong:** A literal repo-wide `grep -rn "dashboard\|shipping\|cache_contract\|bench_core\|build_dashboard_artifacts"` today returns hits not just in the code being removed, but also in `.planning/research/{ARCHITECTURE,FEATURES,PITFALLS,SUMMARY,STACK}.md`, `.planning/codebase/*.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/PROJECT.md`, and the untracked `BRIEF_artifact_backbone.md`.
**Why it happens:** These are meta-planning documents that *describe* the removal (by design — `.planning/research/*.md` is historical record of the pre-refactor architecture; `.planning/ROADMAP.md`/`REQUIREMENTS.md` literally name the symbols being removed as part of specifying this very phase). Grep can't distinguish "documents the removal" from "a dangling reference."
**How to avoid:** RM-05's grep sweep should be scoped to **surviving package code (`infodynamics/`, `tests/`), `setup.py`, and user-facing docs** (root `README.md`, which is currently empty) — not `.planning/` (which is GSD's own meta-documentation, expected to reference the removal by name) and not the untracked `BRIEF_artifact_backbone.md` (which is itself dead documentation for the system being removed, but is out of scope for this milestone per the untracked-clutter exclusion — flag to the user whether to delete it anyway, since unlike the CSV/UDPipe files it has zero future utility once the system it documents is gone). **Recommend the plan state this scoping explicitly** rather than run an unscoped grep and either false-positive on `.planning/` or silently exclude it without saying so.

### Pitfall 5: `pytest --collect-only` is already clean today — don't let the plan "fix" a baseline that isn't broken
**What goes wrong:** A plan step written defensively ("investigate and fix pytest collection errors") could waste time chasing a problem that doesn't exist.
**Why it happens:** CONCERNS.md documents several *test-body* issues (empty stubs, a wrong assertion in `test_window_size`) that sound collection-adjacent but aren't.
**How to avoid:** Verified directly: `pytest --collect-only -q` today reports **81 tests collected, 0 errors, 2 unrelated `PytestUnknownMarkWarning` warnings** (for the unregistered `@pytest.mark.slow` marker — pre-existing, unrelated to this phase, safe to ignore). `tests/test_manifest.py` accounts for exactly 13 of those 81 (confirmed by name in the collect output) and imports only `infodynamics.cache_contract` and `infodynamics.shipping` (confirmed by reading the file's imports) — no other test file imports either module. **Expected post-removal count: 68 tests, 0 collection errors.** The plan should assert exactly this number, not an open-ended "no errors."

## Code Examples

### Verifying the current, pre-removal pytest baseline (already run, for reference)
```bash
# Source: this repo, .venv/bin/pytest --collect-only -q, run 2026-07-13
# Result: 81 tests collected in 5.21s, 0 errors, 2 PytestUnknownMarkWarning (unrelated, pre-existing)
```

### Verifying installed console-script shims (already run, for reference)
```bash
# Source: this repo, ls .venv/bin/ | grep infodynamics, run 2026-07-13
# Result: infodynamics-init-project, infodynamics-pack, infodynamics-pull, infodynamics-verify
# all present -- confirms RM-03 needs an explicit reinstall step, not just a setup.py edit
```

### Current `setup.py` entry_points block to remove (verbatim, lines 50-57)
```python
# Source: setup.py, this repo
entry_points={
    'console_scripts': [
        'infodynamics-pack=infodynamics.shipping:pack_main',
        'infodynamics-pull=infodynamics.shipping:pull_main',
        'infodynamics-verify=infodynamics.shipping:verify_main',
        'infodynamics-init-project=infodynamics.shipping:init_project_main',
    ],
},
```
Removing this entire block (and the now-empty `entry_points={}` if nothing else uses it) is sufficient for the `setup.py` half of RM-03; `extras_require` and `install_requires` need no changes (confirmed: no entries there are exclusively used by removed code).

### Existing FakeEncoder pattern (reusable knowledge for understanding how tests avoid network calls — not to be used for the golden baseline itself, see Pitfall/Alternatives above)
```python
# Source: tests/test_pipeline.py, this repo
class FakeEncoder:
    """Deterministic stand-in for infodynamics.embedding.Encoder, avoids network calls."""
    def __init__(self, *args, **kwargs):
        pass
    def encode(self, texts):
        rng = np.random.default_rng(0)
        return rng.normal(size=(len(texts), 8))
```

## State of the Art

Not applicable — this phase makes no technology choice with an "old way / new way" axis. It removes existing code and snapshots existing behavior.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `.planning/research/*.md` and `.planning/codebase/*.md` should be excluded from RM-05's grep-sweep scope (treated as historical/meta-documentation, not "docs" in the requirement's sense) | Common Pitfalls → Pitfall 4 | If the user actually wants those scrubbed too, RM-05 would need extra scope; low risk since it's a documentation-only concern, easily fixed post-hoc if the interpretation is wrong |
| A2 | The untracked `BRIEF_artifact_backbone.md` should be left alone (out of scope, same as other untracked root clutter) even though it exclusively documents the system being removed | Common Pitfalls → Pitfall 1 & 4 | Low risk — it's untracked, so leaving it is a safe no-op; deleting it later is always possible and non-destructive (git history isn't needed to "recover" an untracked file that was never committed) |
| A3 | 3 fixed documents (each ~15-20 sentences, inline literal strings) are sufficient to exercise `SignalClusterer`'s clustering (explicit `n_clusters=2`, bypassing `k_range`'s `k < n_series` constraint) as well as most default `scales`/`radii` in `MultiscaleInfoDynamics` | Architecture Patterns → Pattern 2; Common Pitfalls → Pitfall 2 | Medium — if the planner picks shorter fixtures, the baseline will silently under-cover the multi-scale surface (Pitfall 2 documents the detection method, so the risk is self-correcting if the sanity check is included) |

**If this table is empty:** N/A — see entries above; all are documentation-scope or fixture-sizing judgment calls, not technical facts about the codebase (those were all verified directly).

## Open Questions

1. **Should the golden-baseline capture script live under `tests/golden/` (proposed above) or somewhere else (e.g. `scripts/`, `.planning/baseline/`)?**
   - What we know: No existing precedent in this repo for a "golden snapshot" directory; `tests/` is the only place with an established, flat, no-fixture-files convention (per TESTING.md).
   - What's unclear: Whether the planner/user prefers keeping large `.npz` binary blobs inside `tests/` (mixed with pure-Python test code) or in a separate top-level directory.
   - Recommendation: Default to `tests/golden/` (keeps it discoverable alongside the pytest suite that consumes it) unless the plan-checker or user objects.

2. **How many separate commits should removal be split into?**
   - What we know: The one hard constraint is baseline-commit-before-any-removal-commit (Pattern 1). Nothing in ROADMAP.md/REQUIREMENTS.md mandates a specific removal commit granularity.
   - What's unclear: Whether finer-grained removal commits (e.g., one per success criterion) meaningfully improve bisectability over one combined removal commit, given removal is a pure subtraction with no surviving-code edits.
   - Recommendation: Leave to the planner's judgment at plan-write time; either is compliant with CLAUDE.md's preservation constraint since git history already satisfies it once the baseline commit exists.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| sentence-transformers | Real-encoder golden-baseline capture (QA-01) | ✓ | 5.6.0 | — |
| `sentence-transformers/all-MiniLM-L6-v2` model weights | Offline, network-independent baseline capture | ✓ (cached at `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2`, 87MB) | — | Network to huggingface.co also confirmed reachable today (HTTP 200), so this isn't a hard blocker either way |
| tslearn + scipy | `SignalClusterer` (DTW + barycenters) for cluster-label/barycenter portion of QA-01 | ✓ | 0.9.0 / 1.18.0 | — |
| pytest | RM-04 collection-health check | ✓ | 9.1.1 | — |
| git | Commit ordering (Pattern 1), history preservation | ✓ (repo is a git checkout) | — | — |
| rclone | Only relevant to the code being *removed* (`shipping.py`'s pack/pull); 3 of `test_manifest.py`'s 13 tests skip without it | Not checked (irrelevant — those tests are being deleted with `test_manifest.py` regardless) | — | N/A |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None — everything needed is already installed and/or has a working fallback path (network vs. cached model).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (installed; `setup.py extras_require['test']` declares `pytest>=6.2.2`) |
| Config file | none — no `pytest.ini`/`pyproject.toml` config exists; defaults apply |
| Quick run command | `pytest tests/test_golden_baseline.py -x` (new file this phase adds) |
| Full suite command | `pytest` (currently 81 tests, expected 68 after `test_manifest.py` removal) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QA-01 | Golden-output snapshot matches current pipeline output within tolerance | unit/regression | `pytest tests/test_golden_baseline.py -x` | ❌ Wave 0 — new file |
| RM-04 | `pytest --collect-only -q` reports zero collection errors, exactly 68 tests | smoke | `pytest --collect-only -q` | ✅ (existing pytest invocation, no new file — a plan verification step, not a new test) |
| RM-05 | Repo-wide grep for removed symbols returns no hits in scoped paths | smoke (non-pytest) | `grep -rn "dashboard\|shipping\|cache_contract\|bench_core\|build_dashboard_artifacts" infodynamics/ tests/ setup.py README.md` | N/A — shell command, not a pytest test |
| RM-03 | No console-script shim in `.venv/bin/` points at removed code | smoke (non-pytest) | `ls .venv/bin/ | grep infodynamics` should return nothing (after `pip install -e .` rerun) | N/A — shell command |

### Sampling Rate
- **Per task commit:** `pytest --collect-only -q` (fast, catches import breakage immediately after each removal step)
- **Per wave merge:** full `pytest` run + the grep sweep + the `.venv/bin/` shim check
- **Phase gate:** full suite green (68/68), golden baseline captured and passing, grep clean (scoped per Pitfall 4), zero console-script shims for removed code, before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/golden/capture_baseline.py` — one-time capture script (QA-01)
- [ ] `tests/golden/baseline_arrays.npz` + `tests/golden/baseline_meta.json` — the checked-in snapshot itself (QA-01)
- [ ] `tests/test_golden_baseline.py` — the reusable pytest comparison test (QA-01, reused by Phases 2-5 per STATE.md)
- Framework install: none — pytest already installed

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface in this project or this phase |
| V3 Session Management | No | N/A — library, not a service |
| V4 Access Control | No | N/A |
| V5 Input Validation | Marginally | The code being *removed* (`shipping.py`) was the one place CONCERNS.md flagged input-validation-adjacent risk ("No input sanitization for file paths" passed to `tar`/`rclone` subprocess calls) — this phase **eliminates** that risk surface entirely by deleting the code, rather than needing a new control |
| V6 Cryptography | Marginally | `cache_contract.py`'s SHA-256 checksums are integrity-only, not security-cryptography, and are being removed along with the rest of the shipping system |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unsanitized subprocess arguments (`tar`/`rclone` paths) in `shipping.py` | Tampering | Not a new mitigation to build — this phase's removal of `shipping.py` retires this exact, already-documented risk (CONCERNS.md → Security Considerations → "No input sanitization for file paths"). Verify via RM-05's grep sweep that no surviving code re-introduces a call to the deleted `pack_project`/`pull_project` functions. |
| Deleting files without git history preservation | Tampering / Repudiation (accidental data loss) | Use `git rm` (not filesystem `rm` outside a git-tracked, subsequently-committed state) for tracked files, so the deletion itself is captured as a commit and the pre-deletion content remains reachable via `git log --follow`/`git show <sha>^:<path>` — satisfies CLAUDE.md's explicit preservation constraint |

## Sources

### Primary (HIGH confidence — verified by direct file read or command execution in this repo, 2026-07-13)
- `setup.py` — entry_points, extras_require, install_requires (full file read)
- `infodynamics/cache_contract.py`, `infodynamics/shipping.py` — full file read, all functions cataloged
- `infodynamics/pipeline.py`, `infodynamics/time_series.py`, `infodynamics/scalogram.py`, `infodynamics/clustering/cluster.py`, `infodynamics/clustering/dtw.py`, `infodynamics/clustering/barycenter.py`, `infodynamics/embedding.py`, `infodynamics/segmentation.py`, `infodynamics/util.py` — full file reads, constructors/signatures verified
- `tests/test_manifest.py`, `tests/test_pipeline.py`, `tests/test_morphology.py`, `tests/test_clustering.py`, `tests/test_infodynamics_class.py` — full file reads
- `.venv/bin/pytest --collect-only -q` — executed directly, 81 tests / 0 errors confirmed
- `git ls-files dashboard/`, `git ls-files | grep -v ...`, `git status --porcelain` — executed directly to determine tracked vs. untracked file sets
- `grep -rIln` repo-wide sweep for the five RM-05 symbol names — executed directly
- `.venv/bin/pip list`, `ls .venv/bin/`, `cat infodynamics.egg-info/entry_points.txt`, `.venv/bin/pip show infodynamics` — executed directly to confirm installed-extras state and stale console-script shims
- `ls ~/.cache/huggingface/hub`, `du -sh` — executed directly to confirm cached model availability
- `curl -sI --max-time 3 https://huggingface.co` — executed directly, HTTP 200 confirmed network reachable
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/config.json` — full file reads

### Secondary (MEDIUM confidence)
- `.planning/codebase/{ARCHITECTURE,STRUCTURE,STACK,TESTING,CONVENTIONS,CONCERNS,INTEGRATIONS}.md` — prior codebase-mapper output, cross-checked against direct file reads above (all claims used from these docs were independently verified, not taken on faith)

### Tertiary (LOW confidence)
- None — this phase required no external/library research; everything is grounded in direct codebase inspection.

## Metadata

**Confidence breakdown:**
- Removal surface (RM-01–RM-05): HIGH — every file, import, and grep hit was independently verified by reading the file or running the command, not inferred
- Golden-baseline mechanics (QA-01): HIGH for constructors/signatures (read from source); MEDIUM for the specific fixture-sizing/format recommendations (sound engineering judgment applied to verified constraints, but no single "correct" answer exists — flagged as Open Questions/Assumptions where a judgment call was made)
- Runtime state (console-script shims): HIGH — directly observed on disk in this repo's `.venv`

**Research date:** 2026-07-13
**Valid until:** Effectively indefinite for the removal-surface findings (static facts about the current repo state) as long as no other work lands on this branch before Phase 1 executes; re-verify the pytest baseline count and `.venv/bin/` shim state immediately before planning if significant time has passed or other commits have landed.

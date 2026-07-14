# Phase 4: Curate the Public API - Context

**Gathered:** 2026-07-14
**Status:** Ready for planning

<domain>
## Phase Boundary

`infodynamics` presents one clean, intentional import surface, and downstream consumers (including the future dashboard repo) have a documented migration path. Concretely: `infodynamics/__init__.py` gets an explicit `__all__` covering only core symbols with zero `from .text import` statements, `infodynamics/text/__init__.py` gets its own explicit `__all__`, a canonical example demonstrates both core-only and full-`Pipeline` usage, and a CHANGELOG/migration note maps every symbol's old→new import path from this milestone's reorg.

Requirements in scope: API-03, API-04.

</domain>

<decisions>
## Implementation Decisions

### Core (`infodynamics`) export surface — the central gray area, fully resolved
- **D-01:** `infodynamics.__all__` is the 6 sklearn estimators only: `InfoDynamics`, `MultiscaleInfoDynamics`, `WindowedRollingDistance`, `Scalogram`, `FooteNovelty`, `SignalClusterer` — plus two scalogram module functions people realistically call standalone alongside `MultiscaleInfoDynamics` to inspect its output: `self_similarity_matrix` and `structure_descriptors`. Final top-level `__all__` = these 8 symbols.
- **D-02:** `checkerboard_kernel`, `foote_novelty`, and `rolling_gap_distance` (scalogram.py internals) stay submodule-only — reachable via `infodynamics.scalogram.*`, not re-exported at the top level.
- **D-03:** `infodynamics/viz.py` (plotting) and `infodynamics/metrics.py` (distance functions) are **submodule-only** — `infodynamics.viz.plot_ssm(...)`, `infodynamics.metrics.cos_sim(...)`. Neither appears in the top-level `__all__`. Keeps the top-level surface focused on the sklearn-Pipeline-composable core.
- **D-04:** `infodynamics.clustering` keeps its own existing `__init__.py` export surface (`SignalClusterer`, `barycenter_average`, `pairwise_distance`) unchanged. The top-level `infodynamics.__all__` re-exports only `SignalClusterer` from it — `barycenter_average`/`pairwise_distance` stay reachable via `infodynamics.clustering.*`, not promoted to the very top level.
- **D-05 (hard requirement, not a gray area — from API-03/ROADMAP criterion 1):** `infodynamics/__init__.py` must end up with **zero** `from .text import` / `from infodynamics.text import` statements. Today it re-exports `MorphologicalEncoder` (from `infodynamics.text.morphology`) and `Chunk`, `segment`, `strip_markdown` (from `infodynamics.text.segmentation`) — all four must be removed from the core `__init__.py`. They may still live in `infodynamics.text.__all__` (see Claude's Discretion below) since they're genuinely text-specific.

### Claude's Discretion
User deferred three of the four presented gray areas entirely to Claude's judgment at plan time — no discussion needed, but each still has a concrete decision baked into the phase's success criteria and existing code, which the planner should treat as the starting point:

- **Text (`infodynamics.text`) export surface:** Today `infodynamics/text/__init__.py` only exports `TextInfoDynamics`, `TextMultiscaleInfoDynamics`, `TextSegmenter` (set in Phase 3). Not yet re-exported at that level: `Encoder` (embedding.py), `MorphologicalEncoder` (morphology.py), `Chunk`/`segment`/`strip_markdown` (segmentation.py) — these are the exact four symbols D-05 removes from the core `__init__.py` and need a new home. Given ROADMAP success criterion 2 just requires "`infodynamics/text/__init__.py` defines its own explicit `__all__`" (no scope restriction stated), the natural, low-risk choice is to fold all of `Encoder`, `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown` into `infodynamics.text.__all__` alongside the three existing Text* wrappers — nothing text-specific should become unreachable as a side effect of the core cleanup.
- **Canonical example location/format:** ROADMAP criterion 3 just requires the example exist and demonstrate both core-only (`ndarray` in, no text on-ramp) and full `Pipeline` composition (text on-ramp → analysis). Repo root currently has ad hoc, untracked demo/scratch scripts (`shit.py`, `run_morphology_demo.py`, `run_multiscale_demo.py`, `run_scalogram_demo.py`, `segmentation_demo.py`, `descriptors_analysis.py`, etc.) — per REQUIREMENTS.md/PROJECT.md, cleaning those up is explicitly **out of scope this milestone** (user decision, already logged). The canonical example should be a clean, separate, tracked artifact (e.g. `examples/basic_usage.py` or similar) — not a rename/repurposing of the existing clutter, and not a claim that it replaces those scripts.
- **CHANGELOG/migration note location/format:** README.md exists but is currently empty. ROADMAP criterion 4 just requires "a CHANGELOG/migration note" mapping old→new import paths for every symbol that moved this milestone (Phase 2's `infodynamics/text/` relocation, Phase 3's `Text*` wrapper additions, this phase's `__all__` curation). A dedicated `CHANGELOG.md` (or `MIGRATION.md`) at repo root is the safer default over folding it into README, since README's future scope/ownership is undecided and out of scope here.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase & milestone scope
- `.planning/ROADMAP.md` §"Phase 4: Curate the Public API" — goal, 4 success criteria, requirements mapping
- `.planning/REQUIREMENTS.md` — API-03, API-04 (this phase's requirements)
- `.planning/PROJECT.md` — constraints (no back-compat shims/breaking changes accepted pre-1.0), Out of Scope table (root clutter cleanup explicitly deferred, not this phase)

### Prior phase context (symbols/paths this phase curates)
- `.planning/phases/03-decouple-the-pipeline/03-CONTEXT.md` — D-04 there added `TextInfoDynamics`/`TextMultiscaleInfoDynamics` under `infodynamics.text`; its "Integration Points" section explicitly flagged "curating `__all__` is explicitly Phase 4's job" — this phase is that resolution.
- `.planning/phases/02-reorganize-into-core-text-on-ramp/02-CONTEXT.md` — D-03/D-04 there deferred `infodynamics.text` export curation and the question of whether `Chunk`/`segment`/`strip_markdown`/`MorphologicalEncoder` disappear from core `__init__.py` to "Phase 4's call" — this phase makes that call (D-05 above).

### Existing code (verified during this discussion)
- `infodynamics/__init__.py` — current re-exports: `SignalClusterer`, `MorphologicalEncoder` (text), `InfoDynamics`, `MultiscaleInfoDynamics`, `FooteNovelty`, `Scalogram`, `self_similarity_matrix`, `structure_descriptors`, `Chunk`/`segment`/`strip_markdown` (text), `WindowedRollingDistance`. No `__all__` defined yet.
- `infodynamics/text/__init__.py` — current re-exports: `TextInfoDynamics`, `TextMultiscaleInfoDynamics`, `TextSegmenter` only. Docstring already notes `__all__` curation is deferred to this phase.
- `infodynamics/clustering/__init__.py` — already exports `SignalClusterer`, `barycenter_average` (aliased from `barycenter.average`), `pairwise_distance` (from `dtw.py`) — unchanged this phase per D-04.
- `infodynamics/scalogram.py` — public functions: `rolling_gap_distance`, `self_similarity_matrix`, `checkerboard_kernel`, `foote_novelty`, `structure_descriptors`; classes `Scalogram`, `FooteNovelty`.
- `infodynamics/metrics.py` — `kl_div`, `js_div`, `js_dist`, `cos_sim`, `cos_dist` (submodule-only per D-03).
- `infodynamics/viz.py` — `plot_overlay`, `plot_side_by_side`, `plot_dendrogram`, `plot_cluster_archetypes`, `plot_projection`, `plot_ssm`, `plot_scalogram`, `plot_multiscale_novelty` (submodule-only per D-03).
- `infodynamics/text/embedding.py` — `Encoder` class (not yet re-exported at `infodynamics.text` level).
- `infodynamics/text/morphology.py` — `MorphologicalEncoder` class (not yet re-exported at `infodynamics.text` level; currently only reachable via the core `__init__.py`'s about-to-be-removed re-export).
- `infodynamics/text/segmentation.py` — `Chunk` (dataclass), `segment()`, `strip_markdown()`, `TextSegmenter` (already exported).
- `README.md` — exists, currently empty.
- No `CHANGELOG.md` or `MIGRATION.md` exists yet.
- No `examples/` directory exists yet — repo root has untracked, out-of-scope demo scripts instead (not to be repurposed as the canonical example).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `infodynamics/clustering/__init__.py` — existing, working `__all__`-less-but-curated re-export pattern (`from infodynamics.clustering.barycenter import average as barycenter_average`) to model the top-level `infodynamics/__init__.py` rewrite after (including the aliasing style if the planner wants consistent naming).

### Established Patterns
- Both `infodynamics/__init__.py` and `infodynamics/text/__init__.py` currently do direct `from infodynamics.<module> import <Symbol>` re-exports with no `__all__` list — this phase adds the missing `__all__` to both, per ROADMAP criteria 1–2.

### Integration Points
- `infodynamics/__init__.py` is the one file with the hard constraint (D-05): it must lose all 4 of its current `.text` re-exports. Those symbols need a new public home at `infodynamics.text.__all__` (Claude's discretion, see above) so nothing becomes unreachable.
- `tests/` likely import some of the symbols being removed from core `__init__.py` (e.g. `from infodynamics import Chunk` or `MorphologicalEncoder`) — planner/researcher should grep for these import paths and update call sites to `infodynamics.text.*` as part of this phase, consistent with "breaking changes accepted pre-1.0" (PROJECT.md constraint).

</code_context>

<specifics>
## Specific Ideas

No specific UI/behavioral requirements (internal library API design phase). The one specific, concrete ask from the user was resolving exactly which symbols belong in the top-level `infodynamics.__all__` — captured in full as D-01 through D-05 above. All other gray areas (text export surface, example location, changelog location) were explicitly left to Claude's judgment.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Root-clutter cleanup (demo scripts, CSVs, the UDPipe model file) was already logged as out-of-scope for this milestone in PROJECT.md/REQUIREMENTS.md before this discussion; it resurfaced only as a boundary note (don't repurpose the clutter as the canonical example), not as new scope.

</deferred>

---

*Phase: 4-Curate the Public API*
*Context gathered: 2026-07-14*

# Phase 2: Reorganize Into Core + Text On-Ramp - Context

**Gathered:** 2026-07-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Pure `git mv` of `segmentation.py`, `embedding.py`, and `morphology.py` from `infodynamics/` into a new `infodynamics/text/` subpackage, with mirrored tests under `tests/text/`. Zero behavior change — this is a relocation, not a rewrite. The one deliberate, documented exception is `pipeline.py`'s import paths (see Decisions below) — its actual decoupling from text (removing `segment()`/`Encoder.encode()` calls from `fit()`) is Phase 3's job, not this phase's.

Requirements in scope: TEXT-01, TEXT-03, CORE-01.

</domain>

<decisions>
## Implementation Decisions

### pipeline.py's interim text dependency
- **D-01:** `pipeline.py` stays at `infodynamics/pipeline.py` (does NOT move to `infodynamics/text/`). Its imports are updated to full submodule paths: `from infodynamics.text.embedding import Encoder` and `from infodynamics.text.segmentation import Level, segment`. This is a **deliberate, documented interim exception** — `pipeline.py` is core per CORE-01 and per the ROADMAP's own module list, but it isn't actually decoupled from text until Phase 3 (ROADMAP Phase 3 criterion 1: "no internal `segment()`/`Encoder.encode()` calls remain"). Moving pipeline.py to `text/` and back in Phase 3 would be pure churn against the roadmap's own move-before-refactor ordering.
- **D-02:** ROADMAP.md Phase 2 success criterion 3 (grep for `infodynamics.text` imports across `infodynamics/*.py` excluding `infodynamics/text/`, expecting zero hits) needs a one-line amendment during planning to explicitly exclude `infodynamics/pipeline.py`, with a note that Phase 3 resolves it. Flag this to the planner — don't silently violate a written success criterion.

### infodynamics.text export surface
- **D-03:** `infodynamics/text/__init__.py` does NOT re-export symbols this phase (no `Chunk`/`segment`/`Encoder`/`MorphologicalEncoder` re-exports at the `infodynamics.text` level yet). All internal call sites (`pipeline.py`, `infodynamics/__init__.py`) import from full submodule paths (`infodynamics.text.segmentation`, `infodynamics.text.embedding`, `infodynamics.text.morphology`). Curating a real export surface is explicitly Phase 4's job (API-03/API-04) — inventing one now would just be redone later.
- **D-04:** `infodynamics/__init__.py`'s existing top-level re-exports (`Chunk`, `segment`, `strip_markdown`, `MorphologicalEncoder`) keep working this phase — only their import *paths* change to point at `infodynamics.text.*`. Whether these disappear from the top-level `__init__.py` entirely is Phase 4's call (API-03 says core `__init__.py` should have zero `from .text import` statements eventually), not this phase's.

### Test directory mirroring
- **D-05:** `tests/test_segmentation.py` → `tests/text/test_segmentation.py`; `tests/test_morphology.py` → `tests/text/test_morphology.py`; add `tests/text/__init__.py`.
- **D-06:** `tests/golden/capture_baseline.py`'s import (`from infodynamics.embedding import Encoder`) is updated to `from infodynamics.text.embedding import Encoder` as part of this phase's mechanical path fixes.
- **D-07:** There is no `tests/test_embedding.py` today (pre-existing test-coverage gap) — not this phase's job to add one. Not in scope.
- **D-08:** `tests/golden/` itself does NOT move under `tests/text/` — it covers all six estimators (core + text), not text-specific.

### Claude's Discretion
User delegated both primary gray areas ("You decide") and confirmed the test-layout follow-up as "obvious mirror is fine." Claude has full discretion on any remaining mechanical details not explicitly decided above (e.g., exact commit granularity, whether to squash the `git mv` + import-fix into one commit or split them) as long as the phase stays a pure move with zero numerical/behavioral drift.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase & milestone scope
- `.planning/ROADMAP.md` §"Phase 2: Reorganize Into Core + Text On-Ramp" — goal, success criteria (note D-02's flagged amendment to criterion 3), requirements mapping
- `.planning/REQUIREMENTS.md` — TEXT-01, TEXT-03, CORE-01 (this phase); CORE-02, TEXT-02 (Phase 3, do not implement early)
- `.planning/PROJECT.md` — constraints (refactor not rewrite, sklearn Pipeline-composability, no compat shims), Key Decisions table

### Codebase structure
- `.planning/codebase/STRUCTURE.md` — current file layout, naming conventions, "where to add new code" guidance
- `.planning/codebase/ARCHITECTURE.md` — component responsibilities, data flow

### Existing coupling (verified during this discussion, not yet reflected in codebase/ docs)
- `infodynamics/pipeline.py` — imports `Encoder` (embedding.py) and `Level`/`segment` (segmentation.py); calls both directly inside `InfoDynamics.fit()` and `MultiscaleInfoDynamics.fit()`. This is the exact coupling Phase 3 removes; Phase 2 only updates its import paths (D-01).
- `infodynamics/__init__.py` — re-exports `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown` at top level; import paths need updating (D-04).
- `infodynamics/clustering/barycenter.py` — imports `tslearn` lazily inside a function already; not part of this phase's scope but confirms TEXT-03's "lazy heavy imports" pattern already exists for at least one heavy dep.
- `infodynamics/embedding.py`, `infodynamics/morphology.py` — heavy deps (`sentence_transformers`, `spacy_udpipe`, `textdescriptives`) are already imported lazily inside functions/methods, not at module top level. TEXT-03 ("import infodynamics.text succeeds without heavy extras") is likely already mechanically true post-move — verify with a no-extras smoke test rather than assuming new lazy-import work is needed.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing lazy-import pattern in `embedding.py` (`sentence_transformers` imported inside `__init__`/methods), `morphology.py` (`spacy_udpipe`, `textdescriptives` imported inside functions), and `clustering/barycenter.py` (`tslearn` imported inside a function) — this pattern should be preserved as-is during the move, not reworked.

### Established Patterns
- `infodynamics/__init__.py` does direct `from infodynamics.<module> import <Symbol>` re-exports — no `__all__` yet (that's Phase 4/API-03).
- Test files follow `test_<module>.py` naming 1:1 with source modules — the `tests/text/` mirror should follow the same convention.

### Integration Points
- `infodynamics/__init__.py` is the single top-level integration point that references all three moving modules (directly or transitively via `pipeline.py`) — every import path fixed there.
- `infodynamics/pipeline.py` is the one core module with a live, uncut dependency on the moving modules — the D-01/D-02 exception.

</code_context>

<specifics>
## Specific Ideas

No specific UI/behavioral requirements — this is an internal reorganization phase with no user-facing surface. The key specific requirement volunteered by the user was resolving the pipeline.py/CORE-01 tension explicitly rather than leaving it implicit (captured as D-01/D-02).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. No scope-creep items surfaced; both delegated decisions and the test-layout confirmation were all within the phase's "pure move" boundary.

</deferred>

---

*Phase: 2-Reorganize Into Core + Text On-Ramp*
*Context gathered: 2026-07-14*

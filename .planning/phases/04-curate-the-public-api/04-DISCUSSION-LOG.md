# Phase 4: Curate the Public API - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-14
**Phase:** 4-Curate the Public API
**Areas discussed:** Core export surface

---

## Area selection

| Option | Selected |
|--------|----------|
| Core export surface | ✓ |
| Text export surface | |
| Canonical example | |
| Migration notes format | |

User selected only "Core export surface" for discussion; the other three were left to Claude's discretion at plan time.

---

## Core export surface

### Q1: Top-level `infodynamics.__all__` surface

| Option | Description | Selected |
|--------|-------------|----------|
| Just the 6 estimators | InfoDynamics, MultiscaleInfoDynamics, WindowedRollingDistance, Scalogram, FooteNovelty, SignalClusterer — matches "curated" literally | ✓ |
| Estimators + key module functions | Add self_similarity_matrix, structure_descriptors | |
| Broad re-export | Kitchen-sink style, includes viz/metrics/util | |
| Let Claude decide | | |

**User's choice:** "Just the 6 estimators" (recommended option)

### Q2: Scalogram module functions

| Option | Description | Selected |
|--------|-------------|----------|
| Only the two "primary" ones | self_similarity_matrix + structure_descriptors at top level; checkerboard_kernel/foote_novelty/rolling_gap_distance stay submodule-only | ✓ |
| Submodule-only, none at top level | | |
| All five at top level | | |
| Let Claude decide | | |

**User's choice:** "Only the two 'primary' ones" (recommended option)

*Note: this answer effectively supersedes the literal wording of Q1's selected option ("just the 6 estimators") — combined with Q2, the final top-level surface is 8 symbols (6 estimators + self_similarity_matrix + structure_descriptors). Captured as D-01 in CONTEXT.md.*

### Q3: Viz/metrics top-level exposure

| Option | Description | Selected |
|--------|-------------|----------|
| Submodule-only for both | Keeps top-level surface focused on sklearn estimators | ✓ |
| Top-level for viz only | | |
| Top-level for both | | |
| Let Claude decide | | |

**User's choice:** "Submodule-only for both" (recommended option)

### Q4: Clustering re-exports

| Option | Description | Selected |
|--------|-------------|----------|
| Just SignalClusterer | barycenter_average/pairwise_distance stay reachable via infodynamics.clustering.* | ✓ |
| All three at top level | | |
| Let Claude decide | | |

**User's choice:** "Just SignalClusterer" (recommended option)

**Notes:** User accepted the recommended option on all four questions. Area concluded with "I'm ready for context" — no further questions requested.

---

## Claude's Discretion

- **Text (`infodynamics.text`) export surface** — user did not select this area for discussion. CONTEXT.md documents the concrete starting point: fold `Encoder`, `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown` into `infodynamics.text.__all__` alongside the existing `TextInfoDynamics`/`TextMultiscaleInfoDynamics`/`TextSegmenter`, since these are exactly the symbols being removed from core `__init__.py` (D-05) and must not become unreachable.
- **Canonical example location/format** — user did not select this area. CONTEXT.md recommends a clean, separate, tracked artifact (e.g. `examples/basic_usage.py`), explicitly not a repurposing of existing untracked demo-script clutter (which is out of scope for cleanup this milestone).
- **CHANGELOG/migration note location/format** — user did not select this area. CONTEXT.md recommends a dedicated `CHANGELOG.md` or `MIGRATION.md` at repo root over folding into the currently-empty `README.md`, since README's future scope is undecided.

## Deferred Ideas

None — discussion stayed within phase scope. Root-clutter cleanup was already logged as out-of-scope for this milestone before this discussion; it only resurfaced as a boundary note for the canonical-example decision, not as new scope.

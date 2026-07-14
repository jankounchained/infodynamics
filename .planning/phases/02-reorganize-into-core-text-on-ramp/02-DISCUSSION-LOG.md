# Phase 2: Reorganize Into Core + Text On-Ramp - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-14
**Phase:** 2-Reorganize Into Core + Text On-Ramp
**Areas discussed:** Pipeline dep, Text exports, Test layout

---

## Pipeline dep

| Option | Description | Selected |
|--------|-------------|----------|
| Documented exception | pipeline.py's imports updated to infodynamics.text.embedding / infodynamics.text.segmentation, stays at infodynamics/pipeline.py. CONTEXT.md documents this as a known, deliberate interim exception that Phase 3 resolves. | |
| Relocate pipeline.py temporarily | Move pipeline.py under infodynamics/text/ for Phase 2, then Phase 3 splits/moves the decoupled core logic back. Keeps the grep criterion literally true but adds move-then-move-back churn. | |
| You decide | Let Claude pick the pragmatic option during planning/research. | ✓ |

**User's choice:** You decide
**Notes:** Claude selected "Documented exception" (D-01/D-02 in CONTEXT.md) — matches the roadmap's own move-before-refactor ordering; relocating and relocating back would be pure churn.

---

## Text exports

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror current top-level exports | Chunk, segment, strip_markdown, Encoder, MorphologicalEncoder re-exported from infodynamics/text/__init__.py. | |
| No __init__ exports yet | Leave infodynamics/text/__init__.py empty/minimal this phase; defer curated exports to Phase 4 (API-03/API-04). | |
| You decide | Let Claude pick based on what keeps infodynamics/__init__.py's existing top-level exports working with minimal churn. | ✓ |

**User's choice:** You decide
**Notes:** Claude selected "No __init__ exports yet" (D-03/D-04) — Phase 4 (API-03/API-04) owns curated exports; inventing a surface now would be redone later.

---

## Test layout

| Option | Description | Selected |
|--------|-------------|----------|
| Obvious mirror is fine | tests/text/test_segmentation.py, tests/text/test_morphology.py, tests/text/__init__.py; update tests/golden/capture_baseline.py's import path. No further discussion needed. | ✓ |
| Discuss this | Walk through test layout options before locking it in. | |

**User's choice:** Obvious mirror is fine
**Notes:** Confirmed as-is; captured as D-05 through D-08 in CONTEXT.md, including the note that tests/golden/ stays put (covers all six estimators, not text-specific) and that the missing tests/test_embedding.py is a pre-existing gap out of scope for this phase.

---

## Claude's Discretion

- Pipeline dep resolution (chose "Documented exception")
- Text export surface (chose "No __init__ exports yet")
- Any remaining mechanical details not explicitly decided (commit granularity, etc.) — bounded by the "pure move, zero behavior change" constraint

## Deferred Ideas

None — discussion stayed within phase scope.

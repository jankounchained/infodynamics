# Phase 3: Decouple the Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-14
**Phase:** 3-Decouple the Pipeline
**Areas discussed:** TextSegmenter chunk-flow contract, transform() semantics, dict vs array output, TextInfoDynamics convenience wrapper

---

## Chunk flow (TextSegmenter I/O contract)

| Option | Description | Selected |
|--------|-------------|----------|
| Plain strings through the pipe, positions on the side | `TextSegmenter.transform(text)` returns `List[str]`; position info kept as fitted attribute `self.chunks_` | ✓ (Claude's discretion) |
| Chunk objects through the pipe | `TextSegmenter.transform(text)` returns `List[Chunk]`; `Encoder`/`MorphologicalEncoder` updated to unwrap `.text` | |
| You decide | | |

**User's choice:** "You decide" — delegated to Claude.
**Notes:** Claude selected "plain strings" for smallest diff and consistency with the existing `self.chunks_` fitted-attribute pattern already in `pipeline.py`. Captured as D-01 in CONTEXT.md.

---

## transform() semantics (research flag a)

| Option | Description | Selected |
|--------|-------------|----------|
| Add real transform(X) everywhere | Recompute fresh from X for every estimator, no leakage risk since none learn fit-time-only parameters | ✓ (Claude's discretion) |
| Split: inductive steps get transform(), analysis steps are fit_transform-only | TextSegmenter/Encoder/MorphologicalEncoder get transform(); WindowedRollingDistance/Scalogram/FooteNovelty/InfoDynamics/MultiscaleInfoDynamics stay fit_transform-only | |
| You decide | | |

**User's choice:** "You decide" — delegated to Claude.
**Notes:** Claude selected uniform `transform(X)` across all public estimators, since none have leakage-prone fitted state (pure functions of input) and API-01 literally requires `fit`/`transform`/`fit_transform` on "every public estimator" — including `Scalogram`/`FooteNovelty`, which today lack a standalone `transform()` too. Captured as D-02 in CONTEXT.md.

---

## Dict output vs array output (research flag b)

| Option | Description | Selected |
|--------|-------------|----------|
| Match Scalogram/FooteNovelty's existing pattern | transform()/fit_transform() return an array; full dict preserved as fitted attribute (self.signal_/self.result_) | ✓ |
| Keep dicts, don't chain these mid-pipeline | Dict outputs stay as-is; only WindowedRollingDistance changes if used non-terminally | |
| You decide | | |

**User's choice:** "Match Scalogram/FooteNovelty's existing pattern"
**Notes:** Exact array shape for multi-output estimators (`WindowedRollingDistance`'s novelty/transience/resonance; `MultiscaleInfoDynamics`'s SSM/scalogram/novelty/descriptors) left to planner discretion — no single obvious "primary array" for `MultiscaleInfoDynamics` in particular. Captured as D-03 in CONTEXT.md.

---

## Convenience wrapper (research flag c)

| Option | Description | Selected |
|--------|-------------|----------|
| Not this phase — defer | Document the 3-step Pipeline pattern as canonical; no wrapper | |
| Add it now | Ship `infodynamics.text.TextInfoDynamics` (+ multiscale counterpart) as a thin wrapper composing TextSegmenter → Encoder → InfoDynamics | ✓ |
| You decide | | |

**User's choice:** "Add it now"
**Notes:** Not scope creep — this was one of ROADMAP's own three research-flagged questions for this phase. Captured as D-04 in CONTEXT.md.

---

## Claude's Discretion

- TextSegmenter chunk-flow contract (D-01) — fully delegated, decided plain-string flow with `chunks_` fitted attribute.
- transform() semantics (D-02) — fully delegated, decided uniform recompute-from-X `transform()` on every public estimator.
- Exact commit granularity/ordering among D-01–D-04 changes and QA-02/QA-03 bug fixes.
- Exact multi-output array stacking convention for `WindowedRollingDistance` and `MultiscaleInfoDynamics` (D-03 follow-on).

## Deferred Ideas

None — discussion stayed within phase scope. Both delegated decisions and explicit choices addressed exactly the three ROADMAP-flagged research questions plus the new TextSegmenter contract implied by TEXT-02.

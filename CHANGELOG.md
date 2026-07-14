# Changelog

This is a **pre-1.0 migration note**, not a Keep-a-Changelog release history.
`infodynamics` has not been published yet (no PyPI presence), so there is no
version history to narrate — instead, this is a one-time, mechanical
old-import-path → new-import-path table covering this milestone's reorg
(Phase 2: relocate text tooling under `infodynamics.text`; Phase 3: add
`Text*` convenience wrappers; Phase 4: curate both `__all__` surfaces).

**No backward-compatible import shims are provided.** Breaking import changes
are accepted pre-1.0 (see `.planning/PROJECT.md` constraints) — update your
imports using the table below.

## Import Migration Table

| Symbol | Old import (pre-milestone / early milestone) | New import (this milestone) |
|---|---|---|
| `MorphologicalEncoder` | `from infodynamics.morphology import MorphologicalEncoder` (pre-Phase-2) or `from infodynamics import MorphologicalEncoder` (Phase 2–3) | `from infodynamics.text import MorphologicalEncoder` |
| `Chunk` | `from infodynamics.segmentation import Chunk` (pre-Phase-2) or `from infodynamics import Chunk` (Phase 2–3) | `from infodynamics.text import Chunk` |
| `segment` | `from infodynamics.segmentation import segment` (pre-Phase-2) or `from infodynamics import segment` (Phase 2–3) | `from infodynamics.text import segment` |
| `strip_markdown` | `from infodynamics.segmentation import strip_markdown` (pre-Phase-2) or `from infodynamics import strip_markdown` (Phase 2–3) | `from infodynamics.text import strip_markdown` |
| `Encoder` | `from infodynamics.embedding import Encoder` (pre-Phase-2) | `from infodynamics.text import Encoder` (newly public at the `infodynamics.text` package root as of Phase 4) |

### New in this milestone (no old import path)

These symbols did not exist before this milestone's reorg — there is nothing
to migrate away from, only a new import path to adopt:

| Symbol | New import | Added |
|---|---|---|
| `TextSegmenter` | `from infodynamics.text import TextSegmenter` | Phase 3 |
| `TextInfoDynamics` | `from infodynamics.text import TextInfoDynamics` | Phase 3 |
| `TextMultiscaleInfoDynamics` | `from infodynamics.text import TextMultiscaleInfoDynamics` | Phase 3 |

## What Changed, Phase by Phase

- **Phase 2 — Reorganize into core + text on-ramp:** `infodynamics/segmentation.py`,
  `infodynamics/embedding.py`, and `infodynamics/morphology.py` were relocated
  (via `git mv`, byte-identical apart from call-site updates) to
  `infodynamics/text/segmentation.py`, `infodynamics/text/embedding.py`, and
  `infodynamics/text/morphology.py`. All internal call sites were repointed;
  lazy heavy-dependency guards (`sentence-transformers`, `spacy-udpipe`,
  `textdescriptives`) were preserved unchanged.
- **Phase 3 — Decouple the pipeline:** `infodynamics.pipeline.InfoDynamics` and
  `MultiscaleInfoDynamics` became strictly `ndarray`-in estimators, with zero
  `infodynamics.text` imports or `segment()`/`Encoder.encode()` calls remaining
  in `pipeline.py`. To restore one-call `fit_transform(text)` ergonomics for
  text users, `TextInfoDynamics` and `TextMultiscaleInfoDynamics` were added
  under `infodynamics.text`, each composing `TextSegmenter -> Encoder ->` the
  corresponding core estimator internally.
- **Phase 4 — Curate the public API (this phase):** Both package roots gained
  an explicit `__all__`:
  - `infodynamics.__all__` = exactly 8 core, sklearn-facing symbols:
    `InfoDynamics`, `MultiscaleInfoDynamics`, `WindowedRollingDistance`,
    `Scalogram`, `FooteNovelty`, `SignalClusterer`, `self_similarity_matrix`,
    `structure_descriptors`. **Zero `from .text import` statements remain** in
    `infodynamics/__init__.py` — `MorphologicalEncoder`, `Chunk`, `segment`,
    and `strip_markdown` were removed from the core package root.
  - `infodynamics.text.__all__` = exactly 8 text-on-ramp symbols:
    `TextInfoDynamics`, `TextMultiscaleInfoDynamics`, `TextSegmenter`,
    `Encoder`, `MorphologicalEncoder`, `Chunk`, `segment`, `strip_markdown` —
    giving the four symbols displaced from core (plus `Encoder`, not
    previously re-exported anywhere) an official public home.

## Still Importable at the Top Level

These 8 symbols remain importable from top-level `infodynamics` and are
unaffected by this migration:

```python
from infodynamics import (
    InfoDynamics,
    MultiscaleInfoDynamics,
    WindowedRollingDistance,
    Scalogram,
    FooteNovelty,
    SignalClusterer,
    self_similarity_matrix,
    structure_descriptors,
)
```

Everything else that was previously reachable via `infodynamics.viz.*`,
`infodynamics.metrics.*`, `infodynamics.scalogram.checkerboard_kernel` /
`foote_novelty` / `rolling_gap_distance`, and
`infodynamics.clustering.barycenter_average` / `pairwise_distance` remains
reachable the same way — these were never part of the top-level `__all__`
and are unaffected by this milestone.

See `examples/basic_usage.py` for a canonical, runnable demonstration of both
the core-only path and the full text-on-ramp `sklearn.pipeline.Pipeline`
composition.

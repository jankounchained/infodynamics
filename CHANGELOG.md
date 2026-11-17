# Changelog

`infodynamics` is pre-1.0 and not yet published on PyPI. Expect breaking
changes between minor versions.

## 0.5.0 (2026-07-14)

A refactor of the research code into a small library. Numerical
output is unchanged; golden-baseline tests captured before the refactor
check this.

- The analysis core now takes plain numeric arrays (`n_observations ×
  n_features`) and imports nothing text-specific.
- The text tools moved into a separate subpackage, `infodynamics.text`.
  `TextInfoDynamics` and `TextMultiscaleInfoDynamics` take raw text in one
  call.
- Every public estimator follows the scikit-learn estimator API and works
  inside a `sklearn.pipeline.Pipeline`.
- Heavy dependencies (sentence-transformers, spaCy/UDPipe, tslearn) are
  optional extras. A missing extra raises an `ImportError` that names the
  extra to install.
- The dashboard, cache and shipping code was removed. It remains in the git
  history.

### Moved imports

No compatibility shims are provided. Update imports as follows:

| Symbol | Before | Now |
|---|---|---|
| `segment`, `strip_markdown`, `Chunk` | `infodynamics.segmentation` or `infodynamics` | `infodynamics.text` |
| `Encoder` | `infodynamics.embedding` | `infodynamics.text` |
| `MorphologicalEncoder` | `infodynamics.morphology` or `infodynamics` | `infodynamics.text` |

New in `infodynamics.text`: `TextSegmenter`, `TextInfoDynamics`,
`TextMultiscaleInfoDynamics`.

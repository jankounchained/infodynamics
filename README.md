<!-- DRAFT: Jan to edit before merge. -->

# infodynamics

[![CI](https://github.com/jankounchained/infodynamics/actions/workflows/ci.yml/badge.svg)](https://github.com/jankounchained/infodynamics/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

`infodynamics` measures how much a sequence changes over time. It takes any
numeric time series, one vector per step, and returns a signal for each
step. The signal shows where something new begins, where something ends,
and whether a change lasts. It follows the scikit-learn estimator API, so it
composes with `Pipeline`. A separate text module turns documents into such
a series, one sentence embedding per step.

For each step, with a window of `w` neighbouring steps:

- **Novelty**: how different the step is from the `w` steps before it.
- **Transience**: how different the step is from the `w` steps after it.
- **Resonance**: novelty minus transience. A change that persists scores
  high; a one-off blip scores near zero.

There are also multi-scale views: a scalogram (the same distance at several
window sizes), a self-similarity matrix, Foote novelty for boundary
detection, and clustering of whole signals by shape.

<!-- TODO(D6): figure from a public-domain text, plus the committed script that regenerates it. -->

## Status

Pre-1.0. The API may change between minor versions. The package is not on
PyPI; install it from GitHub as shown below. Requires Python 3.14.

## Install

```bash
# core
pip install "infodynamics @ git+https://github.com/jankounchained/infodynamics.git"

# with the text on-ramp (adds sentence-transformers)
pip install "infodynamics[embedding] @ git+https://github.com/jankounchained/infodynamics.git"
```

From a clone, use `pip install .` or `pip install ".[embedding]"`. The
other extras are `morphology` (spaCy/UDPipe features), `clustering`
(tslearn, scipy), `viz-projection` (umap-learn), `test` and `all`.

## Quick start

**Numbers in.** Any array of shape `(n_steps, n_features)`:

```python
import numpy as np
from infodynamics import InfoDynamics

# 200 observations of a 16-dimensional signal that switches regime at row 100
rng = np.random.default_rng(0)
regime_a, regime_b = rng.normal(0, 1, (2, 16))
X = np.vstack([
    regime_a + 0.3 * rng.normal(size=(100, 16)),
    regime_b + 0.3 * rng.normal(size=(100, 16)),
])

model = InfoDynamics(window_size=5)
signals = model.fit_transform(X)      # one row per observation: novelty, transience, resonance
print(signals.shape)                            # (200, 3)
print(np.argmax(model.signal_["novelty"]))      # 100, the first observation after the switch
print(np.argmax(model.signal_["transience"]))   # 99, the last observation before it
```

**Text in.** Needs the `embedding` extra. The first run downloads a small
embedding model from the Hugging Face Hub.

```python
from infodynamics.text import TextInfoDynamics

text = (
    "The ship left the harbour at dawn. The crew raised the sails. "
    "The wind carried them out to sea. Waves broke over the bow. "
    "Meanwhile, in the capital, the parliament debated a new tax. "
    "The finance minister defended the budget. The opposition voted against it."
)
model = TextInfoDynamics(model_name="sentence-transformers/all-MiniLM-L6-v2", window_size=2)
signals = model.fit_transform(text)   # one row per sentence
print(signals.shape)                  # (7, 3)
```

[`examples/basic_usage.py`](examples/basic_usage.py) also shows the
multi-scale estimator and a full `sklearn.pipeline.Pipeline`
(segment → embed → analyse).

## Design

- **A numeric core that knows nothing about text.** `infodynamics` takes
  arrays and returns arrays. It works the same on sentence embeddings,
  sensor readings or anything else with one vector per step.
- **Text is a separate on-ramp.** `infodynamics.text` segments documents
  and embeds the pieces, then hands the core an array.
- **Heavy dependencies are optional extras.** The core installs numpy,
  scikit-learn, matplotlib and two small packages (syntok,
  typing-extensions). Using a feature whose extra is missing raises an
  `ImportError` that names the extra to install.
- **Estimators are stateless.** Nothing is learned in `fit`. `transform`
  recomputes from the data it is given, because each signal describes one
  sequence, not a model that generalises to new data.

**Cost.** `InfoDynamics` compares each step with `2 × window_size`
neighbours, so it is linear in the number of steps.
`MultiscaleInfoDynamics` builds a dense `n × n` self-similarity matrix, so
its memory grows with the square of the number of steps.

## How this was built

The library began as research code (2022–2024). In July 2026 it was
refactored into this package using a spec-driven, AI-assisted workflow.
The plans, research notes and verification reports from that work are in
[`.planning/`](https://github.com/jankounchained/infodynamics/tree/619e659/.planning).

- **No numerical output was allowed to change.** Before the refactor
  started, golden-baseline outputs were captured
  ([`tests/test_golden_baseline.py`](tests/test_golden_baseline.py)). Every
  later step had to reproduce them.
- **When that check failed on Linux CI, the cause was traced.** float32
  summation order differs between the macOS and Linux BLAS libraries. The
  diagnosis is written up in
  [`golden-baseline-ci-drift.md`](https://github.com/jankounchained/infodynamics/blob/619e659/.planning/debug/golden-baseline-ci-drift.md).
- **The resulting tolerance policy is pinned by its own test**
  (`test_golden_baseline_tolerance_policy`). Float64 paths keep a tight
  band. Only transformer-derived float32 signals get a looser one.

## Tests

```bash
pip install ".[test]"
pytest                     # full suite; downloads a small model on first run
pytest -m "not network"    # offline subset
```

CI runs ruff, the test suite, and the morphology tests (in a separate job
with the `morphology` extra).

## Where the method comes from

<!-- TODO(D6): references for novelty/transience/resonance and the other methods. -->

Signal clustering follows Wevers, Kostkan & Nielbo (2021), "Event Flow".
<!-- TODO(D6): full reference. -->

## Licence

MIT. See [LICENSE](LICENSE).

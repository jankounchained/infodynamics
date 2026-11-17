# infodynamics

[![CI](https://github.com/jankounchained/infodynamics/actions/workflows/ci.yml/badge.svg)](https://github.com/jankounchained/infodynamics/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

`infodynamics` detects novelty in time series. Given a sequence of vectors, one per step, it scores each step against the steps around it: how far it is from the recent past, how far from what follows, and whether that change persists or fades. Multi-scale tools extend this across window sizes to find boundaries and recurring structure. It follows the scikit-learn estimator API, so it composes with Pipeline. A separate text embedding module turns documents into such a series, one sentence embedding per step.

For each step, with a window of `w` neighbouring steps:

- **Novelty**: how different the step is from the `w` steps before it.
- **Transience**: how different the step is from the `w` steps after it.
- **Resonance**: novelty minus transience. A change that persists scores
  high (non-persistent steps score near zero).

There are also multi-scale views: a scalogram (the same distance at several
window sizes), a self-similarity matrix, Foote novelty for boundary
detection, and clustering of whole signals by shape.

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
- **Tools for processing text (or images or audio in the future) are in a separate submodule.** `infodynamics.text` segments documents
  and embeds the pieces, then hands the core module an array. This also makes heavy dependencies optional extras. The core installs a couple of small packages.
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
The plans, research notes and verification reports from that work are
kept at the commit that completed it, in
[`.planning/`](https://github.com/jankounchained/infodynamics/tree/619e659/.planning).

## Tests

```bash
pip install ".[test]"
pytest                     # full suite; downloads a small model on first run
pytest -m "not network"    # offline subset
```

CI runs ruff, the test suite, and the morphology tests (in a separate job
with the `morphology` extra).

## Where the method comes from

Novelty, transience and resonance come from information theory. Barron et
al. (2018) defined them to track how new ideas spread through speeches in
the French Revolution's National Constituent Assembly. Each speech was a
topic distribution, and the distance between two steps was the
Kullback–Leibler divergence, the extra information needed to describe one
distribution in terms of another. For a window of `w` steps:

$$
\begin{aligned}
N_w(i) &= \frac{1}{w}\sum_{d=1}^{w} D(x_i \,\|\, x_{i-d}) \\
T_w(i) &= \frac{1}{w}\sum_{d=1}^{w} D(x_i \,\|\, x_{i+d}) \\
R_w(i) &= N_w(i) - T_w(i)
\end{aligned}
$$

`infodynamics` keeps this structure but lets `D` be any distance/divergence metric. KL
(`measure="kld"`) and Jensen–Shannon (`"jsd"`, `"jensenshannon"`) need
non-negative vectors, such as probability distributions. The default,
cosine distance, works on unconstrained vectors such as sentence
embeddings. 

- Barron, A. T. J., Huang, J., Spang, R. L., & DeDeo, S. (2018). Individuals, institutions, and innovation in the debates of the French Revolution. *Proceedings of the National Academy of Sciences*, 115(18), 4607–4612. https://doi.org/10.1073/pnas.1717729115
- Wevers, M., Kostkan, J., & Nielbo, K. L. (2021). Event Flow – How Events Shaped the Flow of the News, 1950–1995. In *Proceedings of the Computational Humanities Research Conference 2021 (CHR 2021)*, Amsterdam, CEUR Workshop Proceedings, vol. 2989, pp. 62–76. https://ceur-ws.org/Vol-2989/long_paper16.pdf
- Lassche, A., Kostkan, J., & Nielbo, K. L. (2022). Chronicling Crises: Event Detection in Early Modern Chronicles from the Low Countries. In *Proceedings of the Computational Humanities Research Conference 2022 (CHR 2022)*, Antwerp, CEUR Workshop Proceedings, vol. 3290, pp. 215–230. https://ceur-ws.org/Vol-3290/short_paper4697.pdf
- Nielbo, K. L., Kostkan, J., & Wevers, M. (2023). Embed, Detect and Describe (EDDe): A Framework for Examining Events in Complex Sociocultural and Historical Data. *DHNB 2023*, Oslo. https://pure.au.dk/portal/en/publications/embed-detect-and-describe-edde-a-framework-for-examining-events-i/
- Nielbo, K. L., Kostkan, J., Baunvig, K. F., Borisova, E., & Geertz, A. W. (2023). Oscillation between Contemplation and Revelation – Recurrence and Change in the Life History of Teresa of Ávila. In *Proceedings of the Computational Humanities Research Conference 2023 (CHR 2023)*, Paris, CEUR Workshop Proceedings, vol. 3558, pp. 715–733. https://ceur-ws.org/Vol-3558/paper8108.pdf

## Licence

MIT. See [LICENSE](LICENSE).

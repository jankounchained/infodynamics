# Evidence bench

Turns the multi-scale structure signals (scalogram · SSM · Foote novelty) into
concrete, quotable agent failures paired with Radomil's better handling, then
exports them as rules the agent can consume.

## Pipeline

```
build_dashboard_artifacts.py   ->  cache/           (recomputable, disposable)
bench_core.py                  ->  loop logic (no UI, unit-tested)
app.py                         ->  Streamlit UI over bench_core
findings.jsonl / rules.yaml    ->  human-authored store (precious, versioned)
```

The cache is the contract between precompute and app. Candidate feeds are
*precomputed tables* (`redundant_pairs.json`, `flat_regions.json`); contrast
suggestion is a nearest-neighbour lookup over `human_index.npy`. Nothing in the
app recomputes embeddings.

## Run

```bash
pip install streamlit pyyaml pandas numpy matplotlib
pip install -e ".[embedding]"   # sentence-transformers, for the encoder
# 1. build the cache with a real HuggingFace Hub encoder model:
python build_dashboard_artifacts.py --model-name Qwen/Qwen3-Embedding-8B
# 2. launch:
streamlit run app.py
```

`--model-name` is a required argument, not an environment variable — the
command you run is self-documenting, and `cache/config.json` records exactly
which model built the cache. There is no lexical/TF-IDF fallback: the
ai-vs-human comparison and the nearest-neighbour "human contrast" search only
make sense over a real semantic embedding space. For a quick smoke run
against a small local model instead of downloading the full-size one, add
`--model-name sentence-transformers/all-MiniLM-L6-v2 --limit 5`.

**Swap points:** `encode_corpus()` in `build_dashboard_artifacts.py` — the
only function that touches either model (`infodynamics.embedding.Encoder`
for embeddings, `infodynamics.morphology.MorphologicalEncoder` for morphology).

### Optional: morphology signal

A second, optional signal — morphological/syntactic structure (e.g. POS-tag
proportions per sentence) via UDPipe + textdescriptives — computed over the
*same* sentences as the embedding signal, so the two are directly comparable.
Off by default; nothing in the app or cache format changes if you don't use it.

```bash
pip install -e ".[morphology]"   # textdescriptives, spacy-udpipe
python build_dashboard_artifacts.py --model-name Qwen/Qwen3-Embedding-8B \
    --morphology-feature-group pos_proportions --morphology-model-path czech-pdt.udpipe
```

`--morphology-feature-group` is any value in
`infodynamics.morphology.MorphologicalEncoder.FEATURE_GROUPS`. `spacy_udpipe.download()`
currently fails against LINDAT's repository (an upstream issue, not specific
to this dashboard) — see `run_morphology_demo.py`'s docstring for a working
model mirror; `--morphology-model-path` points at a manually downloaded model.

When enabled, the app additively shows a morphology section next to every
existing embedding-based view (Document detail, Pair comparison, Overview's
discriminator table, Author signature) — never a mode switch, and these
sections simply don't render if the cache wasn't built with morphology
enabled. Document detail also gets a raw per-sentence feature table
(e.g. `pos_prop_VERB` per sentence) for direct inspection, since these
features are human-interpretable, unlike embedding dimensions.

## The loop (Evidence bench page)

1. Pick a feed: Redundancy / Flatness / Pattern-first.
2. Select a candidate → see it in context.
3. "Suggest Radomil contrast" → attach the better human version.
4. Tag failure mode + diagnosis → **Keep as finding** (`findings.jsonl`).
5. Watch **coverage** to know when a pattern is saturated → **promote a rule**.
6. **Export** → `export_system_prompt.md` (paste into agent) + `export_style_guide.md`.

## Caveats baked into the design

- **Redundancy ≠ englishisms.** This geometry catches repetition/flatness well;
  englishisms need a separate signal (surprisal / LLM-judge) — slot reserved.
- **Repetition isn't always bad.** Anaphora/refrains are good copy; the bench
  surfaces *candidates* for human judgment (`intentional_ok` flag), never a verdict.
- **Length confound.** Human docs here are ~2× longer; length-sensitive
  descriptors (variance, scale-energy) partly track length. Length-control or
  compare length-normalised signals before drawing conclusions.

## Files

- `taxonomy.py` — failure-mode vocabulary (predefined, extensible)
- `test_bench.py` — headless end-to-end test of the loop
- `render_overview.py` — static PNG of the corpus views (no Streamlit)

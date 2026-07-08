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
# 1. build the cache with your real embeddings:
EMB_BACKEND=qwen python build_dashboard_artifacts.py
# 2. launch:
streamlit run app.py
```

`EMB_BACKEND` defaults to `tfidf` (a shared-vocabulary fallback that runs with
no torch/network). **Swap point:** `embed_corpus_qwen()` in
`build_dashboard_artifacts.py` — the only thing that touches the model.

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

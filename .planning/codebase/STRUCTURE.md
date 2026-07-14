# Codebase Structure

**Analysis Date:** 2026-07-13

## Directory Layout

```
infodynamics/                          # Main package
├── __init__.py                        # Exports: SignalClusterer, MorphologicalEncoder, InfoDynamics, etc.
├── clustering/
│   ├── __init__.py
│   ├── cluster.py                     # SignalClusterer (DTW + agglomerative clustering)
│   ├── dtw.py                         # Dynamic Time Warping distance calculation
│   └── barycenter.py                  # DBA/soft-DTW barycenter averaging
├── embedding.py                       # Encoder (HuggingFace SentenceTransformer wrapper)
├── morphology.py                      # MorphologicalEncoder (UDPipe + textdescriptives)
├── pipeline.py                        # InfoDynamics, MultiscaleInfoDynamics classes
├── segmentation.py                    # Text segmentation (words/sentences/paragraphs)
├── time_series.py                     # WindowedRollingDistance (sliding-window novelty/transience/resonance)
├── scalogram.py                       # Scalogram, FooteNovelty, self_similarity_matrix, structure_descriptors
├── metrics.py                         # Distance/similarity metrics (cosine, JS divergence, KL divergence)
├── viz.py                             # Matplotlib visualization utilities
├── util.py                            # Helpers (z-normalize rows)
├── cache_contract.py                  # Manifest generation, checksums, config hashing
└── shipping.py                        # Pack/pull/verify CLI for remote storage (rclone)

dashboard/                             # Streamlit dashboard
├── __init__.py
├── app.py                             # Main Streamlit UI (pages: Overview, Author signature, etc.)
├── build_dashboard_artifacts.py       # Precompute pipeline: load corpus → analyze → cache
├── bench_core.py                      # Cache reader (powers app.py)
├── render_overview.py                 # PCA corpus map visualization
├── taxonomy.py                        # Failure mode taxonomy (for Evidence bench page)
├── test_bench.py                      # Benchmark/test helpers
├── cache/                             # Precomputed cache (generated, not in git)
│   ├── manifest.json                  # Provenance + checksums
│   ├── config.json                    # PipelineConfig used to build cache
│   ├── corpus.csv                     # One row per document + descriptors
│   ├── ssm/                           # Self-similarity matrices
│   ├── emb/                           # Sentence embeddings
│   ├── curves/                        # Scalogram/novelty curves
│   ├── sentences/                     # Sentence text metadata
│   ├── morph_ssm/                     # (If morphology enabled) Morphological SSMs per feature group
│   ├── morph_curves/                  # (If morphology enabled) Morphological curves per feature group
│   ├── morph_features/                # (If morphology enabled) Raw morphological features per group
│   ├── redundant_pairs.json           # Near-duplicate sentence candidates
│   ├── flat_regions.json              # Low-novelty region candidates
│   ├── aggregates.json                # Corpus-level summaries (PCA, Cohen's d, etc.)
│   ├── human_index.npy                # Embeddings of human sentences (for contrast search)
│   └── human_index_meta.json          # Metadata parallel to human_index.npy
├── README.md                          # Dashboard usage and cache contract
├── _test_findings.jsonl               # Test data
├── _test_rules.yaml                   # Test data
├── _test_style_guide.md               # Test data
└── _test_system_prompt.md             # Test data

tests/                                 # Unit and integration tests
├── __init__.py
├── test_infodynamics_class.py         # InfoDynamics + MultiscaleInfoDynamics
├── test_pipeline.py                   # Pipeline orchestration
├── test_segmentation.py               # Text segmentation
├── test_scalogram.py                  # Scalogram + Foote novelty
├── test_morphology.py                 # MorphologicalEncoder
├── test_clustering.py                 # SignalClusterer
├── test_metrics.py                    # Distance metrics
├── test_manifest.py                   # Manifest + checksums
└── test_viz.py                        # Visualization functions

[root]
├── setup.py                           # Package setup, entry points for CLI tools
├── README.md                          # Project overview (currently empty)
├── CLAUDE.md                          # Project context (currently empty)
├── BRIEF_artifact_backbone.md         # Implementation spec for cache/shipping
├── .gitignore                         # Ignores cache/, *.tar.zst, .venv, __pycache__
├── 260708_radomil_collection.csv      # Corpus data (Czech texts)
├── czech-pdt-ud-2.5-191206.udpipe    # UDPipe model for Czech morphology
├── run_multiscale_demo.py             # Single-document analysis demo
├── run_morphology_demo.py             # Morphology encoding demo
├── run_scalogram_demo.py              # Scalogram/Foote novelty demo
├── benchmark_embedding.py             # Model performance benchmark
├── descriptors_analysis.py            # Descriptor extraction analysis
├── radomil_texts_to_csv.py            # Data preparation (texts → corpus CSV)
├── scalogram_foote_prototype.py       # Early prototype + sentence splitter (shared with build script)
└── .planning/
    └── codebase/                      # Codebase analysis documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
```

## Directory Purposes

**`infodynamics/`:**
- Purpose: Core reusable pipeline library for text information dynamics analysis
- Contains: Scikit-learn compatible estimators, encoders, signal analysis, metrics, shipping
- Key files: `pipeline.py` (main classes), `scalogram.py` (multi-scale analysis), `embedding.py`, `morphology.py`, `clustering/`

**`infodynamics/clustering/`:**
- Purpose: Time-series clustering via DTW + agglomerative clustering
- Contains: DTW distance computation, barycenter averaging (DBA, soft-DTW), SignalClusterer class
- Key files: `dtw.py`, `barycenter.py`, `cluster.py`

**`dashboard/`:**
- Purpose: Streamlit UI + precompute pipeline for the Evidence-bench dashboard
- Contains: Interactive UI pages, cache builder (expensive GPU computation), cache reader
- Key files: `app.py` (UI), `build_dashboard_artifacts.py` (precompute), `bench_core.py` (cache reader)

**`dashboard/cache/`:**
- Purpose: Precomputed analysis results (generated by `build_dashboard_artifacts.py`)
- Generated: Yes (via pipeline)
- Committed: No (in `.gitignore`)
- Structure: Hierarchical NPY/NPZ arrays, JSON metadata, per-document and corpus-level summaries
- See `dashboard/README.md` and `BRIEF_artifact_backbone.md` for full cache contract

**`tests/`:**
- Purpose: Unit and integration tests for all core modules
- Contains: pytest tests covering pipeline classes, segmentation, scalogram, morphology, clustering, manifest/checksums
- Key files: `test_infodynamics_class.py`, `test_scalogram.py`, `test_manifest.py`

**`[root]` (demo scripts & data):**
- Purpose: Reproducible examples, data preparation, prototyping
- Key files: `run_multiscale_demo.py`, `260708_radomil_collection.csv` (corpus), `czech-pdt-ud-2.5-191206.udpipe` (UDPipe model)

## Key File Locations

**Entry Points:**
- `infodynamics/__init__.py`: Exports public API (InfoDynamics, MultiscaleInfoDynamics, Encoder, MorphologicalEncoder, etc.)
- `setup.py`: Package metadata, dependency extras, console script entry points (pack/pull/verify/init-project)
- `dashboard/app.py`: Streamlit web UI
- `dashboard/build_dashboard_artifacts.py`: Cache precompute pipeline

**Configuration:**
- `dashboard/cache/config.json`: PipelineConfig (model name, corpus path, device, batch size, etc.)
- `dashboard/cache/manifest.json`: Provenance (versions, checksums, models, built_at timestamp)
- `setup.py`: Install extras (embedding, morphology, clustering, viz-projection, test)

**Core Logic:**
- `infodynamics/pipeline.py`: InfoDynamics, MultiscaleInfoDynamics (main transformers)
- `infodynamics/scalogram.py`: Scalogram, FooteNovelty, structure_descriptors (multi-scale analysis)
- `infodynamics/segmentation.py`: segment() function + Chunk dataclass
- `infodynamics/embedding.py`: Encoder class (HuggingFace wrapper)
- `infodynamics/morphology.py`: MorphologicalEncoder (UDPipe + textdescriptives)
- `infodynamics/clustering/cluster.py`: SignalClusterer (DTW clustering)

**Testing:**
- `tests/test_infodynamics_class.py`: Pipeline class API
- `tests/test_scalogram.py`: Multi-scale structure
- `tests/test_manifest.py`: Checksums + config hashing + round-trip packing
- `tests/test_morphology.py`: Morphological encoding

**Visualization:**
- `infodynamics/viz.py`: Matplotlib plot functions
- `dashboard/render_overview.py`: PCA corpus map

**Shipping & Serialization:**
- `infodynamics/cache_contract.py`: Manifest, checksum, config hash logic
- `infodynamics/shipping.py`: pack_project(), pull_project(), verify_project() + CLI

## Naming Conventions

**Files:**
- Modules: lowercase with underscores (`segmentation.py`, `time_series.py`, `cache_contract.py`)
- Classes: PascalCase (`InfoDynamics`, `MultiscaleInfoDynamics`, `Encoder`, `WindowedRollingDistance`)
- Functions: lowercase with underscores (`segment()`, `self_similarity_matrix()`, `structure_descriptors()`)
- Test files: `test_<module>.py` (e.g., `test_scalogram.py`, `test_manifest.py`)
- Cache files: doc-id keyed (`ssm/{doc_id}.npy`, `emb/{doc_id}.npy`, `curves/{doc_id}.npz`)

**Directories:**
- Package submodules: lowercase (`clustering/`, `cache/`)
- Feature group subdirs (morphology): feature-name lowercase (`quality/`, `readability/`, `pos_proportions/`, `dependency_distance/`, `descriptive_stats/`)

**Dataclass Fields:**
- `PipelineConfig` in `build_dashboard_artifacts.py`: snake_case (model_name, cache_dir, batch_size, etc.)
- `Chunk` in `segmentation.py`: snake_case (text, start, end)

## Where to Add New Code

**New Feature (Analysis Algorithm):**
- Implement as a new class inheriting from `sklearn.base.BaseEstimator` and `sklearn.base.TransformerMixin`
- Location: Create in `infodynamics/` directory or new submodule (e.g., `infodynamics/my_feature.py`)
- Tests: Add `tests/test_my_feature.py`
- Exports: Add import to `infodynamics/__init__.py` if part of public API
- Example: Look at `WindowedRollingDistance` (`infodynamics/time_series.py`) or `Scalogram` (`infodynamics/scalogram.py`) as templates

**New Visualization:**
- Location: Add function to `infodynamics/viz.py` (generic) or `dashboard/app.py` (dashboard-specific)
- Signature: Should take numpy array(s) + optional `ax` (matplotlib.axes.Axes) + kwargs
- Example: See `plot_overlay()`, `plot_ssm()` pattern in `infodynamics/viz.py:14-40`

**New Dashboard Page:**
- Location: `dashboard/app.py`
- Pattern: Add page name to `PAGES` list, add conditional block in main flow checking `page == "My Page Name"`
- Data access: Use `b.corpus`, `b.ssm(doc_id)`, `b.curves(doc_id)` (see bench_core.py for available methods)
- Example: See existing pages (Overview, Author signature, Document detail)

**New Test:**
- Location: Add to existing `tests/test_<module>.py` or create new file if testing a new module
- Framework: pytest + hypothesis (property-based testing for signal properties)
- Fixtures: Use hypothesis strategies (e.g., `@given(st.just(...))`) rather than separate fixture files
- Example: See `tests/test_segmentation.py`, `tests/test_manifest.py`

**New Utility Function:**
- For common operations (normalization, distance, etc.): Add to `infodynamics/util.py`
- For pipeline-building specifics: Add to `infodynamics/pipeline.py` or relevant module
- Example: `znorm_rows()` in `infodynamics/util.py` is used by scalogram and morphology

**New Encoding Model or Signal Type:**
- If it's a new encoder (e.g., BERT-based, LSA): Create new class in `infodynamics/embedding.py` or submodule
- Constraint: Must expose `.encode(texts: List[str]) -> np.ndarray` interface for compatibility with InfoDynamics
- Example: MorphologicalEncoder in `infodynamics/morphology.py` follows this pattern

**New CLI Command:**
- Shipping commands (pack/pull/verify/init-project) are in `infodynamics/shipping.py`
- Register in `setup.py:50-56` under `entry_points['console_scripts']`
- Example: See `pack_main()`, `pull_main()` functions

**New Cache Type or Artifact:**
- Update cache contract: `infodynamics/cache_contract.py` (bump CACHE_SCHEMA_VERSION if format changes)
- Update build logic: `dashboard/build_dashboard_artifacts.py` (add write function for new artifact)
- Update cache reader: `dashboard/bench_core.py` (add accessor method to expose new cache to app)
- Update documentation: `BRIEF_artifact_backbone.md`, `dashboard/README.md` (cache contract section)

## Special Directories

**`dashboard/cache/`:**
- Purpose: Precomputed cache for dashboard (expensive GPU computation results)
- Generated: Yes (by `build_dashboard_artifacts.py`)
- Committed: No (ignored by `.gitignore`)
- Contents: `.npy` (embeddings, SSMs), `.npz` (scalogram/novelty), `.json` (metadata, summaries), `.csv` (corpus + descriptors)
- Rebuild: `cd dashboard && python build_dashboard_artifacts.py --model-name <model> [--morphology]`

**`infodynamics.egg-info/`:**
- Purpose: Build metadata (generated by `pip install -e .`)
- Generated: Yes (by setuptools)
- Committed: No (ignored by `.gitignore`)
- Delete if stale: `rm -rf infodynamics.egg-info` then `pip install -e .`

**`tests/__pycache__/`, `infodynamics/__pycache__/`, `dashboard/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No (ignored by `.gitignore`)
- Safe to delete: Yes (regenerated on next import)

**`multiscale_demo_output/`, `morphology_demo_output/`, `multiscale_demo_segment_word/`:**
- Purpose: Demo script output (figures, cached data)
- Generated: Yes (by `run_multiscale_demo.py`, `run_morphology_demo.py`)
- Committed: No (ignored by `.gitignore`)
- Regenerate: `python run_multiscale_demo.py`, etc.

---

*Structure analysis: 2026-07-13*

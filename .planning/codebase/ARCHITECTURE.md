<!-- refreshed: 2026-07-13 -->
# Architecture

**Analysis Date:** 2026-07-13

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│             UI & Visualization Layer                        │
├──────────────────┬──────────────────┬───────────────────────┤
│   Streamlit App  │   Matplotlib     │    Visualization      │
│  `dashboard/     │   Viz Utilities  │    Rendering          │
│   app.py`        │  `infodynamics/  │  `infodynamics/viz.py`│
│                  │   viz.py`        │                       │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Cache & Dashboard Build Layer                       │
│   `dashboard/build_dashboard_artifacts.py`                  │
│   `dashboard/bench_core.py`                                 │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│         Analysis & Processing Core                          │
├──────────────────┬──────────────────┬───────────────────────┤
│ Multi-scale      │ Semantic Signal  │ Morphological Signal  │
│ Structure        │ Analysis         │ Analysis              │
│ `scalogram.py`   │ `time_series.py` │ `morphology.py`       │
│ `segmentation.py`│ `embedding.py`   │ `MorphologicalEncoder`│
│ `metrics.py`     │ `pipeline.py`    │                       │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Clustering & Aggregation                           │
│         `infodynamics/clustering/`                          │
│    DTW Distance • Agglomerative Clustering • Barycenter     │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│         Cache Layer & Serialization                         │
│   `cache_contract.py` • `shipping.py` (pack/pull/verify)    │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **InfoDynamics** | Single-scale semantic information dynamics (novelty/transience/resonance) | `infodynamics/pipeline.py` |
| **MultiscaleInfoDynamics** | Multi-scale structure: scalogram, SSM, Foote novelty, descriptors | `infodynamics/pipeline.py` |
| **Segmentation** | Split text into chunks (words/sentences/paragraphs) | `infodynamics/segmentation.py` |
| **Encoder** | HuggingFace sentence-embedding models | `infodynamics/embedding.py` |
| **MorphologicalEncoder** | UDPipe + textdescriptives feature extraction | `infodynamics/morphology.py` |
| **WindowedRollingDistance** | Sliding-window distance calculation for novelty/transience/resonance | `infodynamics/time_series.py` |
| **Scalogram** | Multi-scale rolling-gap distance stacking | `infodynamics/scalogram.py` |
| **FooteNovelty** | Multi-scale Foote novelty (checkerboard-kernel novelty) | `infodynamics/scalogram.py` |
| **SignalClusterer** | DTW-distance clustering with barycenter archetypes | `infodynamics/clustering/cluster.py` |
| **Dashboard Cache Builder** | Precompute pipeline: load corpus → encode → analyze → cache | `dashboard/build_dashboard_artifacts.py` |
| **Dashboard UI** | Streamlit app for browsing analysis results | `dashboard/app.py` |
| **Shipping** | Pack/pull/verify cache bundles via rclone | `infodynamics/shipping.py` |
| **Cache Contract** | Manifest generation, checksums, config hashing | `infodynamics/cache_contract.py` |

## Pattern Overview

**Overall:** Scikit-learn compatible estimators with sklearn's BaseEstimator/TransformerMixin.

**Key Characteristics:**
- Single data flow: text → segmentation → embedding → multi-scale analysis → visualization
- Two interchangeable signal types: semantic (embedding) and morphological (syntactic features)
- All analysis components are stateless transformers — `fit(data)` and `fit_transform(data)` return computed signals
- Expensive computation (embedding, SSM) decoupled from UI via precomputed cache
- Deterministic manifest/checksum system for shipping and verification

## Layers

**Text Segmentation Layer:**
- Purpose: Split raw text into analyzable chunks (words, sentences, paragraphs)
- Location: `infodynamics/segmentation.py`
- Contains: Chunk dataclass, segment(), strip_markdown() utilities
- Depends on: syntok (sentence splitting)
- Used by: InfoDynamics, MultiscaleInfoDynamics, build_dashboard_artifacts

**Encoding Layer:**
- Purpose: Convert text chunks into numeric feature vectors
- Location: `infodynamics/embedding.py`, `infodynamics/morphology.py`
- Contains: Encoder (HuggingFace), MorphologicalEncoder (UDPipe + textdescriptives)
- Depends on: sentence-transformers, spacy-udpipe, textdescriptives
- Used by: InfoDynamics, MultiscaleInfoDynamics, build_dashboard_artifacts

**Signal Analysis Layer:**
- Purpose: Compute information dynamics, multi-scale structure, and clustering from embeddings
- Location: `infodynamics/time_series.py`, `infodynamics/scalogram.py`, `infodynamics/clustering/`
- Contains: WindowedRollingDistance, Scalogram, FooteNovelty, SignalClusterer, structure_descriptors
- Depends on: numpy, scikit-learn, scipy, tslearn (for DTW)
- Used by: pipeline classes, build_dashboard_artifacts

**Pipeline Orchestration Layer:**
- Purpose: Wire segmentation + encoding + analysis into end-to-end transformers
- Location: `infodynamics/pipeline.py`
- Contains: InfoDynamics, MultiscaleInfoDynamics (both sklearn-compatible)
- Depends on: all layers above
- Used by: build_dashboard_artifacts, demo scripts, tests

**Cache & Persistence Layer:**
- Purpose: Precompute expensive analysis once, then read from cache in UI
- Location: `infodynamics/cache_contract.py`, `infodynamics/shipping.py`, `dashboard/build_dashboard_artifacts.py`
- Contains: Manifest generation, checksum verification, pack/pull/verify CLI
- Depends on: json, hashlib, subprocess (rclone, tar)
- Used by: Dashboard (bench_core.py), shipped projects

**Visualization Layer:**
- Purpose: Render signals and multi-scale structure as matplotlib figures
- Location: `infodynamics/viz.py`
- Contains: plot_overlay, plot_ssm, plot_scalogram, plot_multiscale_novelty, plot_dendrogram
- Depends on: matplotlib
- Used by: dashboard/app.py, demo scripts

**Dashboard UI Layer:**
- Purpose: Interactive Streamlit app for browsing corpus, comparing documents, exploring evidence
- Location: `dashboard/app.py`
- Contains: Page routing (Overview, Author signature, Document detail, Pair comparison, Evidence bench)
- Depends on: streamlit, pandas, matplotlib, bench_core (cache reader)
- Used by: End user (web browser)

## Data Flow

### Primary Request Path (Dashboard Load)

1. User opens Streamlit app (`dashboard/app.py:29`)
2. App loads pre-cached Bench object (`dashboard/app.py:33-36`, backed by `dashboard/bench_core.py`)
3. User selects page and explores corpus/documents
4. On page render, app reads cached SSM/curves/embeddings from `dashboard/cache/` (all `.npy`/`.npz`/`.json`)
5. Viz functions render matplotlib figures from cached arrays
6. Streamlit sends HTML to browser

### Cache Build Path (GPU Box, One-Time)

1. User runs `build_dashboard_artifacts.py` with corpus CSV and model name (`dashboard/build_dashboard_artifacts.py:1001-1090`)
2. `load_corpus()` reads CSV, filters documents → `pd.DataFrame` of raw text
3. `segment_corpus()` splits each document into sentences using `syntok` → list of `Chunk` objects
4. `encode_corpus()` embeds all sentences via `Encoder.encode()` (HuggingFace) or `MorphologicalEncoder.encode_all_feature_groups()` (UDPipe) → `(n_sentences, n_features)` arrays
5. `analyze_document()` per document:
   - Computes SSM via `self_similarity_matrix(embeddings)` → `(n, n)` cosine matrix
   - Computes scalogram via `Scalogram.fit(embeddings)` → `(n_scales, n)` matrix
   - Computes Foote novelty via `FooteNovelty.fit(embeddings)` → `(n_radii, n)` matrix
   - Computes structure descriptors via `structure_descriptors(embeddings, SSM)` → dict of 10+ numeric features
6. `build_corpus_aggregates()` computes author-level summaries and PCA projection
7. `write_*_cache()` persists all arrays to `dashboard/cache/` directory structure (see STRUCTURE.md)
8. `write_manifest()` computes checksums, config hash, corpus hash → `cache/manifest.json`

### Single-Document Analysis (In-Memory, e.g., Notebook)

```python
from infodynamics import MultiscaleInfoDynamics

pipeline = MultiscaleInfoDynamics(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    segment_level="sentence",
    scales=(2, 3, 5, 8, 13, 21),
)
result = pipeline.fit_transform(raw_text_string)
# result = {"ssm": (n, n), "scalogram": (n_scales, n), "novelty": (n_radii, n), "descriptors": dict}
```

### State Management

- **No global state** — all classes are pure transformers
- **Encoding cache** (singleton per model): `infodynamics/embedding.py:_MODEL_CACHE`, `infodynamics/morphology.py:_PIPELINE_CACHE`
  - Models/pipelines are cached in memory within a single Python process to avoid reloading
  - On multi-process/distributed use, each worker loads independently
- **Dashboard session state** — minimal: `dashboard/app.py:37-39` tracks selected candidate/contrast via Streamlit's `st.session_state`

## Key Abstractions

**Chunk:**
- Purpose: Represents a text segment with position information
- Definition: `infodynamics/segmentation.py:28-32` (dataclass: text, start, end)
- Examples: `segment()` returns `List[Chunk]`

**Signal:**
- Purpose: Generic numpy array representing a scalar per chunk (1D: novelty/transience/resonance, or 2D: scalogram/novelty)
- Examples: `novelty` shape `(n_chunks,)`, `scalogram` shape `(n_scales, n_chunks)`
- Pattern: All signals are z-normalized and visualized via `viz.py` functions

**Self-Similarity Matrix (SSM):**
- Purpose: Dense (n, n) pairwise cosine similarity between all chunk embeddings
- Definition: `infodynamics/scalogram.py:self_similarity_matrix()`
- Used for: Visualizing structure, computing Foote novelty

**Manifest:**
- Purpose: Immutable record of what went into a cache build (model IDs, config hash, checksums)
- Definition: `infodynamics/cache_contract.py:build_manifest()`
- Fields: pipeline_version, cache_schema_version, config_hash, corpus_hash, models, per-file checksums
- Used for: Shipping verification, reproducibility

## Entry Points

**Console Scripts (registered in `setup.py:50-56`):**

- `infodynamics-pack --project <dir> --remote <rclone_remote>`
  - Location: `infodynamics/shipping.py:pack_project()`
  - Triggers: User wants to ship a cached project to cloud storage
  - Responsibilities: Verify cache checksums, tar + zstd compress, rclone copy to remote

- `infodynamics-pull --project <dir> --remote <rclone_remote> [--archive <name>]`
  - Location: `infodynamics/shipping.py:pull_project()`
  - Triggers: User wants to download a cached project from cloud storage
  - Responsibilities: rclone copy archive, untar, verify checksums match manifest

- `infodynamics-verify --project <dir>`
  - Location: `infodynamics/shipping.py:verify_project()`
  - Triggers: User wants to check cache integrity
  - Responsibilities: Recompute checksums, confirm schema version, warn on version mismatch

- `infodynamics-init-project <dir> --config <config.json>`
  - Location: `infodynamics/shipping.py:init_project_main()`
  - Triggers: User wants to scaffold a new project directory
  - Responsibilities: Create `data/`, `config.json`, `requirements.txt`, `.gitignore`, `README.md`

**Python Entry Points:**

- `infodynamics.pipeline.InfoDynamics` (and `MultiscaleInfoDynamics`)
  - Fit-transform API for single-scale or multi-scale text analysis
  - Example: see "Single-Document Analysis" under Data Flow

- `dashboard/app.py`
  - `streamlit run dashboard/app.py` (from dashboard/ directory)
  - Serves interactive Streamlit web UI

- `dashboard/build_dashboard_artifacts.py`
  - `python dashboard/build_dashboard_artifacts.py --model-name <model> [--morphology]`
  - Precomputes cache for all documents in corpus

- Demo scripts at repo root:
  - `run_multiscale_demo.py` — Single-document multi-scale analysis + visualization
  - `run_morphology_demo.py` — Morphological encoding demo
  - `run_scalogram_demo.py` — Scalogram/Foote novelty demo

## Architectural Constraints

- **Threading:** Single-threaded event loop per process. Encoding happens in-process; no worker thread pool. GPU models (if used) serialize across the single Python interpreter.
- **Global state:** Encoding model cache in `embedding.py:_MODEL_CACHE` and morphology pipeline cache in `morphology.py:_PIPELINE_CACHE` are process-level singletons. On multi-GPU or multi-process setups, each worker loads independently; no cache sharing.
- **Circular imports:** None detected; all imports follow top-down dependency order (metrics → scalogram/time_series → pipeline).
- **Determinism:** Text segmentation is deterministic (syntok + regex). Embedding determinism depends on the HuggingFace model and hardware (floating-point rounding may differ across devices). Checksums in manifest capture the exact corpus and config; the build is reproducible given the same inputs.
- **Memory:** Scalogram stacks matrices for every scale; storing `(n_scales, n_chunks)` at once. For large documents (1000s of sentences) and many scales, memory grows quadratically. Typical corpus (17k sentences across 78 documents) fits easily in RAM.

## Anti-Patterns

### Modifying Config After Build

**What happens:** User modifies `config.json` after running `build_dashboard_artifacts.py`, then runs `infodynamics-pack`.

**Why it's wrong:** The manifest's `config_hash` no longer matches; `verify_project()` warns of a mismatch (soft warning for `pipeline_version`, but hard failure for schema incompatibility). Shipping a modified config alongside a cache built with different params can cause silent corruption if the app consumes stale cached data against new config assumptions.

**Do this instead:** Re-run the full `build_dashboard_artifacts.py` pipeline with the new config, which regenerates cache and manifest atomically. If iterating on config quickly, use `--limit N` to speed builds during testing.

### Swapping Encoding Models Mid-Stream

**What happens:** Build cache with model A, then change `config.json` to use model B without rebuilding.

**Why it's wrong:** The embeddings in `cache/emb/` were created with model A. The SSM, scalogram, and novelty were all computed over model A's embeddings. Feeding model B embeddings to the cached SSM breaks all analysis.

**Do this instead:** When changing models, rebuild the entire cache using the same `build_dashboard_artifacts.py` flow with the new `--model-name`. The manifest will capture the new model identity and checksums.

### Mixing Semantic and Morphological Signals

**What happens:** User extracts semantic (embedding-based) and morphological (syntactic) descriptors, then tries to cluster them together without normalization.

**Why it's wrong:** Descriptors are in different scales (e.g., semantic distances [0, 1], readability scores [0, 100]). Euclidean distance or DTW will be dominated by the larger-scale signal.

**Do this instead:** Z-normalize all signals before clustering (see `infodynamics/util.py:znorm_rows()`). The build pipeline normalizes before writing descriptors to cache, ensuring consistent ranges.

## Error Handling

**Strategy:** Fail fast with clear error messages.

**Patterns:**

- **Value validation:** Pipeline constructors validate parameters (e.g., `chunk_size >= 1`, `window_size` as positive int). Invalid input raises `ValueError` with explanation.
- **Missing dependencies:** If optional extras aren't installed (e.g., `sentence-transformers` for embedding), `ImportError` is raised with install instructions (see `infodynamics/embedding.py:14-18`).
- **File I/O:** Shipping commands check file existence and checksums; missing manifest or checksum mismatch raises `RuntimeError` with context (see `infodynamics/shipping.py:60-78`).
- **Manifest schema:** If `cache_schema_version` in manifest doesn't match installed pipeline, `verify_project()` raises `RuntimeError` (hard failure, not a warning) — version mismatch means the cache layout is incompatible (see `infodynamics/shipping.py:69-72`).

## Cross-Cutting Concerns

**Logging:** No logging framework (logging disabled by default in Streamlit). Print statements to stdout/stderr for CLI tools (`infodynamics-pack`, etc.). Dashboard app uses Streamlit's `st.write()` for output.

**Validation:**
- Corpus CSV must have `author`, `file_name`, `content` columns (see `build_dashboard_artifacts.py:load_corpus()`)
- Text must be non-empty after stripping
- Documents with fewer sentences than `min_sentence_count` (default 5) are dropped to avoid degenerate SSM
- Model names must resolve on HuggingFace Hub or be a local path

**Authentication:** No auth built-in. Rclone auth (pack/pull) is configured externally (user's `.config/rclone/rclone.conf`); this tool just shells out. For private models, HuggingFace token is assumed to be in HuggingFace CLI cache or environment (handled by `sentence-transformers`).

---

*Architecture analysis: 2026-07-13*

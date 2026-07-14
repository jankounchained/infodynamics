# Technology Stack

**Analysis Date:** 2026-07-13

## Languages

**Primary:**
- Python 3.14.5 - Core library and all components in `infodynamics/` and `dashboard/`

**Secondary:**
- Bash/Shell - Artifact shipping via `infodynamics-pack`, `infodynamics-pull` commands that wrap system `tar` and `rclone` binaries

## Runtime

**Environment:**
- Python 3.14.5 (via Homebrew `python@3.14`)
- Virtual environment at `.venv/`

**Package Manager:**
- pip (via setuptools)
- Lockfile: No `requirements.txt` or `Pipfile`; dependencies defined in `setup.py` via `install_requires` and `extras_require`

## Frameworks

**Core:**
- scikit-learn 1.3.0+ - ML algorithms: clustering, distance metrics, PCA for visualization
- numpy 1.19.0+ - Numerical arrays and matrix operations in `infodynamics/metrics.py`, `infodynamics/clustering/`, `infodynamics/scalogram.py`
- matplotlib 3.3.2+ - Visualization and plotting (used by `infodynamics.viz` and dashboard)

**Embedding & Language:**
- sentence-transformers 2.2+ (optional: `extras['embedding']`) - HuggingFace Hub sentence encoders loaded in `infodynamics/embedding.py`
- spacy-udpipe 1.0+ (optional: `extras['morphology']`) - UDPipe model loading for morphological parsing in `infodynamics/morphology.py`
- textdescriptives 2.7+ (optional: `extras['morphology']`) - Morphological and syntactic feature extraction via spaCy pipeline in `infodynamics/morphology.py`
- syntok 1.4.4+ - Sentence tokenization and segmentation in `infodynamics/segmentation.py`

**Clustering & Time Series:**
- tslearn 0.6+ (optional: `extras['clustering']`) - Dynamic time warping (DTW) barycenter algorithms in `infodynamics/clustering/barycenter.py`
- scipy 1.10+ (optional: `extras['clustering']`) - Hierarchical clustering and utilities in `infodynamics/clustering/dtw.py`

**Visualization:**
- umap-learn 0.5+ (optional: `extras['viz-projection']`) - UMAP dimensionality reduction for document projection in `infodynamics/viz.py` (alternative to PCA)

**Dashboard:**
- streamlit (via dashboard requirements) - Interactive web UI in `dashboard/app.py` (no version pinned in code; documented in `dashboard/app.py` docstring as dependency)
- pyyaml (via dashboard requirements) - Dashboard configuration parsing (documented in `dashboard/app.py` docstring)
- pandas - Data manipulation and CSV handling in dashboard `bench_core.py` and build scripts

**Testing:**
- pytest 6.2.2+ - Test runner for `tests/` directory
- hypothesis 6.87.0+ - Property-based testing in `tests/`

**Build/Dev:**
- setuptools - Package building and distribution in `setup.py`
- typing-extensions 4.8.0+ - Type hints for Python 3.14+ support across `infodynamics/`

## Key Dependencies

**Critical:**
- numpy 1.19.0+ - Core numerical operations; used in every signal processing module (scalogram, metrics, clustering, embedding matrix operations)
- scikit-learn 1.3.0+ - ML distance metrics (`cosine_similarity` in `metrics.py`), clustering in `clustering/cluster.py`, PCA in `viz.py`
- syntok 1.4.4+ - Sentence/word tokenization in `segmentation.py`; no fallback tokenizer provided

**Infrastructure:**
- sentence-transformers 2.2+ - HuggingFace Hub model loader; required for embedding signal in dashboard pipeline (`dashboard/build_dashboard_artifacts.py` CLI arg `--model-name`)
- matplotlib 3.3.2+ - Plotting and figure rendering in `viz.py` for scalogram/novelty curve exports
- typing-extensions 4.8.0+ - `typing.Self` support in base classes (`InfoDynamics`, `MultiscaleInfoDynamics`)

## Configuration

**Environment:**
- Python version: Specified via `.venv/pyvenv.cfg` (Python 3.14.5)
- No `.env` file; all configuration is explicit or passed as CLI arguments
- Dashboard build step takes explicit `--model-name` (HuggingFace Hub ID) and optional `--lang` for UDPipe/morphology

**Build:**
- `setup.py` - Single source of truth for dependencies, version (`__version__` read from `infodynamics/__init__.py`), entry points
- Entry points (console scripts):
  - `infodynamics-pack` - Ship cache artifacts via rclone
  - `infodynamics-pull` - Fetch cache artifacts from rclone
  - `infodynamics-verify` - Verify cache integrity
  - `infodynamics-init-project` - Scaffold new project directory
- Extras groups:
  - `embedding` - sentence-transformers for HuggingFace models
  - `morphology` - spacy-udpipe + textdescriptives for syntactic features
  - `clustering` - tslearn + scipy for DTW barycenter
  - `viz-projection` - umap-learn for UMAP projection (alternative to PCA)
  - `test` - pytest + hypothesis for testing
  - `all` - All extras combined

## Platform Requirements

**Development:**
- Python 3.14.5
- macOS (Darwin) or Linux (tested on macOS via Homebrew)
- System binaries: `tar`, `git`, `rclone` (for shipping commands in `infodynamics/shipping.py`)

**Production:**
- Python 3.14.5 (or compatible 3.14.x)
- No system database (SQLite, PostgreSQL, etc.); caching is file-based (JSON, NPY, NPZ in `cache/`)
- GPU optional: beneficial for sentence-transformers model inference (device can be specified in `infodynamics.embedding.Encoder` or dashboard config), CPU fallback available
- HuggingFace Hub internet access required at first run to download models (cached locally afterward)

---

*Stack analysis: 2026-07-13*

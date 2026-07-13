# External Integrations

**Analysis Date:** 2026-07-13

## APIs & External Services

**HuggingFace Hub:**
- Sentence embedding models (e.g., "Qwen/Qwen3-Embedding-8B", "sentence-transformers/all-MiniLM-L6-v2")
  - SDK/Client: `sentence-transformers` 2.2+
  - Integration: `infodynamics/embedding.py` → `Encoder.encode()` loads model by name via `SentenceTransformer(model_name)`
  - Model caching: Local model cache in Python package (sentence-transformers handles this)
  - Usage: Required for dashboard embedding pipeline in `dashboard/build_dashboard_artifacts.py` (CLI arg `--model-name`)
  - No auth required: Public HuggingFace Hub models

**UDPipe (via spacy-udpipe):**
- Morphological/syntactic parsing models (language-specific, e.g., Czech)
  - SDK/Client: `spacy-udpipe` 1.0+
  - Integration: `infodynamics/morphology.py` → `_load_udpipe()` downloads or loads local UDPipe model
  - Auto-download: `spacy_udpipe.download(lang)` on first use if not locally available
  - Local fallback: `spacy_udpipe.load_from_path(lang, path)` for offline use or custom models
  - Usage: Morphological feature extraction in `dashboard/build_dashboard_artifacts.py` (optional CLI arg `--lang`, default Czech via Czech UDPipe model bundled at `czech-pdt-ud-2.5-191206.udpipe`)
  - No auth required

## Data Storage

**Databases:**
- None used — project uses local file-based caching exclusively

**File Storage:**
- Local filesystem only (no cloud storage integration in Python code)
  - Embedding matrices (embeddings): `cache/emb/<doc_id>.npy`
  - Self-similarity matrices: `cache/ssm/<doc_id>.npy`
  - Scalogram/novelty curves: `cache/curves/<doc_id>.npz`
  - Morphological features: `cache/morph_features/<group>/<doc_id>.npy`
  - Corpus metadata: `cache/corpus.csv`, `cache/sentences/<doc_id>.json`
  - Aggregates: `cache/aggregates.json`
  - Human index: `cache/human_index.npy`, `cache/human_index_meta.json`
- Artifact shipping: `infodynamics/shipping.py` uses system `tar` + `rclone` to move cache bundles to remote storage (typically Google Drive or similar via rclone config)
  - No Python SDK; wraps subprocess calls to `rclone copy` and `tar --zstd`
  - Rclone remote name passed as CLI arg (`--remote`) to `infodynamics-pack` / `infodynamics-pull`

**Caching:**
- In-memory model caching:
  - HuggingFace sentence-transformers models cached by sentence-transformers library (`.cache/huggingface/hub/`)
  - spaCy+textdescriptives pipelines cached in module-level `_PIPELINE_CACHE` dict in `infodynamics/morphology.py`
- File-based caching:
  - Cache manifest/contract in `cache/manifest.json` tracked for integrity via checksums (`infodynamics/cache_contract.py`)

## Authentication & Identity

**Auth Provider:**
- None used — all external integrations (HuggingFace, UDPipe) are public/unauthenticated

**Custom:**
- No API authentication layer; project relies on public models only

## Monitoring & Observability

**Error Tracking:**
- None configured (no Sentry, Rollbar, or equivalent)

**Logs:**
- Console/stderr only:
  - Warnings printed to stderr in `infodynamics/shipping.py` (e.g., pipeline version mismatch during verify)
  - spaCy/sentence-transformers libraries emit their own warnings to stdout/stderr
  - No structured logging (no Python logging module configuration found)

**Cache Verification:**
- Manifest-based: `infodynamics/shipping.py` includes `verify_project()` that recomputes SHA256 checksums for every file in cache and confirms schema compatibility
  - Used before packing cache artifacts for shipping (guards against corruption)

## CI/CD & Deployment

**Hosting:**
- Not specified — project is a Python library installable via pip from local source or GitHub

**CI Pipeline:**
- No `.github/workflows/` detected; assumes manual testing
- Pytest can be run locally: `pytest tests/` (via `setup.py` `extras['test']` dependency)

## Environment Configuration

**Required env vars:**
- None required; all configuration is explicit or CLI-driven:
  - Embedding model: `--model-name` argument to `dashboard/build_dashboard_artifacts.py`
  - UDPipe language/model: `--lang` argument or `--udpipe-path` for local model file
  - Dashboard device (GPU/CPU): Can be configured in dashboard config or passed to `Encoder` class
  - Rclone remote name: `--remote` argument to `infodynamics-pack` / `infodynamics-pull`

**Secrets location:**
- No secrets stored in repo; rclone configuration (e.g., Google Drive credentials) external to codebase
- `setup.py` reads `README.md` for package long description; no sensitive data

**Data files:**
- CSV corpus: `260708_radomil_collection.csv` (example data in repo root, pre-committed)
- Czech UDPipe model: `czech-pdt-ud-2.5-191206.udpipe` (pre-committed; 56 MB)

## Webhooks & Callbacks

**Incoming:**
- None — project is not a web service

**Outgoing:**
- None — project reads/writes only to local filesystem and fetches public models on demand

---

*Integration audit: 2026-07-13*

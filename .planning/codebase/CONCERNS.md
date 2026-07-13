# Codebase Concerns

**Analysis Date:** 2026-07-13

## Tech Debt

**Unfinished data validation:**
- Issue: `_validate_data()` in `infodynamics/time_series.py` (line 70) is marked as "UNFINISHED" with only basic type checking and a generic warning for unknown types
- Files: `infodynamics/time_series.py:70-85`
- Impact: Input data validation is incomplete, risking silent failures or unexpected behavior with invalid input types
- Fix approach: Complete the validation to raise errors for invalid input types, check array shapes, and validate numeric ranges

**Typo in parameter name:**
- Issue: `averaging_weigts` parameter in `WindowedRollingDistance.__init__()` has a typo (should be `averaging_weights`)
- Files: `infodynamics/time_series.py:23, 45, 54, 65`
- Impact: Misspelled parameter makes the code harder to maintain and could confuse users
- Fix approach: Rename parameter to `averaging_weights` throughout the class, maintain backward compatibility if needed

**Incomplete TODO in resonance calculation:**
- Issue: Line 176 in `infodynamics/time_series.py` contains: `# TODO consider turning this off for jump calculations`
- Files: `infodynamics/time_series.py:176-177`
- Impact: Resonance signal computation may not be correct for jump size calculations; behavior is undefined
- Fix approach: Clarify if resonance should be disabled for jump > 0, implement conditional logic, add tests

## Known Bugs

**Fragile sentence span detection:**
- Symptoms: `text.index()` in `_spans_from_parts()` can fail with ValueError if a sentence part is not found after the cursor position
- Files: `infodynamics/segmentation.py:59`
- Trigger: When sentence splitting produces parts that don't appear in order in the original text (e.g., normalization side effects in `_sentence_parts()`)
- Workaround: Pre-test with documents from target corpus
- Fix approach: Use case-insensitive or fuzzy matching, or track byte offsets during segmentation instead of searching

## Test Coverage Gaps

**Empty test stubs:**
- What's not tested: Three test functions contain only `pass` statements, indicating incomplete test coverage
  - `test_transience_calculation()` at line 43 in `tests/test_infodynamics_class.py`
  - `test_negative_values_in_input_data()` at line 110 in `tests/test_metrics.py`
  - `test_very_small_numbers()` at line 114 in `tests/test_metrics.py`
- Files: `tests/test_infodynamics_class.py:43-47`, `tests/test_metrics.py:110-115`
- Risk: Untested edge cases for transience calculation, negative input values, and numerical stability with very small floats
- Priority: Medium - these are documented concerns in the test file header but unimplemented

**Missing cache validation tests:**
- What's not tested: No tests verify that loaded cache arrays have expected shapes or dtypes after unpickling
- Files: `dashboard/bench_core.py:56-71`
- Risk: Corrupt .npy/.npz files will fail at runtime during visualization, not during cache load
- Priority: Medium - could cause dashboard crashes if cache files are corrupted

**Missing error path testing:**
- What's not tested: Exception handling for missing cache files, corrupted JSON, or unreachable remote storage
- Files: `infodynamics/shipping.py` (pack/pull/verify), `dashboard/bench_core.py` (Bench.__init__)
- Risk: Unhelpful error messages on failure; unclear what went wrong
- Priority: Low - errors are raised loudly but messages could be more specific

## Fragile Areas

**Cache file I/O without validation:**
- Files: `dashboard/bench_core.py:44-52`, `dashboard/bench_core.py:56-96`
- Why fragile: Bench.__init__() and lazy loaders assume all expected files exist and are valid; no try-catch or shape validation
- Safe modification: Wrap file operations in try-except, validate array shapes on load, add size warnings for large cached embeddings
- Test coverage: Unit tests exist for manifest integrity, but not for corrupted/missing artifacts at load time

**Model caching with device switching:**
- Files: `infodynamics/embedding.py:20-22, 40-43`
- Why fragile: The global `_MODEL_CACHE` stores model instances, and `.to(device)` modifies them in place. If two Encoders with different devices are used sequentially, they'll share the same moved model
- Safe modification: Either store models per-device in the cache key (key includes device), or use context managers to restore device after use
- Test coverage: No tests for concurrent or sequential multi-device encoder usage

**Segmentation with complex documents:**
- Files: `infodynamics/segmentation.py:39-48` (sentence splitting), `dashboard/build_dashboard_artifacts.py:136` (custom sentence splitter import)
- Why fragile: `_sentence_parts()` delegates to `syntok.segmenter` which may produce edge cases (ellipsis, abbreviations); `_spans_from_parts()` then searches by string match and fails if not found
- Safe modification: Test with diverse corpus; add fallback for unfound spans; consider byte-offset tracking
- Test coverage: `tests/test_segmentation.py` exists but limited to basic cases

## Performance Bottlenecks

**Redundant model downloads on first use:**
- Problem: `_load_udpipe()` calls `spacy_udpipe.download()` in a bare exception handler if load fails, with no retry limit or timeout
- Files: `infodynamics/morphology.py:75-79`
- Cause: Download happens inside exception handler; network timeouts or transient failures will retry indefinitely
- Improvement path: Add explicit download step before load, set timeout, cache success/failure state, provide fallback model paths

**N² local redundancy computation:**
- Problem: `local_redundancy()` in `dashboard/build_dashboard_artifacts.py:516-536` iterates over every sentence and masks/searches for distal similarities — O(n²) for n sentences
- Files: `dashboard/build_dashboard_artifacts.py:516-536`
- Cause: Per-sentence max-over-distal-indices requires full row scan; could be vectorized
- Improvement path: Use numpy operations (e.g., np.maximum_accumulate with offset windows) instead of loops

**Dashboard cache reads on every run:**
- Problem: Streamlit reruns on every interaction; each rerun reloads all CSVs, JSON, and metadata via pd.read_csv/json.load in Bench.__init__
- Files: `dashboard/bench_core.py:44-52`
- Cause: Streamlit @st.cache_resource caches the Bench instance, but startup still loads if cache is cold
- Improvement path: Benchmark; if slow, cache individual DataFrames/arrays separately or use memory-mapped files for large embeddings

## Dependencies at Risk

**spacy_udpipe download broken against LINDAT:**
- Risk: `spacy_udpipe.download()` currently fails against LINDAT's repository (documented in module docstrings)
- Impact: Morphology signal cannot be auto-downloaded; users must provide `--morphology-model-path` manually
- Current mitigation: Documentation; fallback via manual model download
- Migration path: Monitor spacy_udpipe upstream; consider switching to a local huggingface model or alternative parsing library if LINDAT issue persists

**sentence-transformers optional dependency:**
- Risk: Embedding encoder requires `sentence-transformers[sentence_transformers]` but is only validated at import time in `_load_model()`
- Impact: Script fails mid-run if installed without embedding extra
- Current mitigation: Error message points to `pip install infodynamics[embedding]`
- Recommendation: Add early check in CLI entry points before expensive setup

**textdescriptives/spacy_udpipe type annotations mismatch:**
- Risk: textdescriptives passes list-typed values where confection expects Tuple; worked around via `_QUALITY_PIPE_CONFIG` hack
- Impact: Fragile; future textdescriptives release could break
- Current mitigation: Explicit tuple wrapper
- Migration path: File upstream issue; consider pinning textdescriptives version

## Security Considerations

**No input sanitization for file paths:**
- Risk: `pack_project()` and `pull_project()` pass user-supplied paths to `tar` and `rclone` via subprocess without shell escaping
- Files: `infodynamics/shipping.py:96, 128, 135`
- Current mitigation: Arguments are passed as list (not shell=True), so injection is blocked
- Recommendation: Add path validation (check for `..`, symlinks) before passing to subprocess

**No checksum verification after tar extraction:**
- Risk: `pull_project()` extracts to tempdir and verifies manifest, but doesn't validate that extracted files match their checksums before moving to final location
- Files: `infodynamics/shipping.py:115-147`
- Current mitigation: Verification happens before move, but a race condition could corrupt files between verify and move
- Recommendation: Use atomic move (rename) to ensure all-or-nothing

## Scaling Limits

**Dashboard cache size with large corpora:**
- Current capacity: Cache is all in-memory as .npy and .npz files; Bench loads corpus.csv, aggregates.json, and human embeddings at startup
- Limit: For ~15k sentences with 384-D embeddings, human_index alone is ~22 MB; full cache with all morphology groups could exceed 500 MB
- Scaling path: Implement lazy loading for morphology curves; cache only top-K human candidates; consider database backend for corpus-level queries

**Serialization time for large manifest:**
- Current: `verify_manifest()` recomputes SHA256 for every file in the cache; for 1000+ files, this is slow
- Limit: Each file read is synchronous; no parallelization
- Scaling path: Parallelize checksums with ThreadPoolExecutor; cache manifest validation results

## Missing Critical Features

**No API versioning or backward compatibility guarantees:**
- Problem: CACHE_SCHEMA_VERSION is incremented on any layout change, but there's no migration path from old schemas
- Blocks: Users with old cached projects cannot upgrade to new infodynamics version if schema changed
- Fix approach: Implement schema migration functions; document deprecation timeline; provide upgrade script

**No configuration UI for morphology feature group selection at build time:**
- Problem: Dashboard hardcodes which morphology groups to build into cache via MorphologicalEncoder.FEATURE_GROUPS; can't select a subset
- Blocks: Users can't optimize cache size for projects that only need POS proportions, not all five groups
- Fix approach: Add CLI flag `--morphology-groups <list>` to build_dashboard_artifacts.py; write selected groups to config.json

## Fragile Test Execution

**Unfinished test body:**
- Files: `tests/test_infodynamics_class.py:89-106`
- Issue: The `test_window_size()` test has a hypothesis decorator but the assertion on line 105 expects N-W+1 output shape, while WindowedRollingDistance.fit_transform() returns a dict with keys like "N_hat", not a 2D array with shape (N-W+1, W)
- Risk: Test may pass despite wrong assertion, or fail with confusing error message
- Fix: Clarify expected output shape; check if test_infodynamics_class expectations match actual output format

---

*Concerns audit: 2026-07-13*

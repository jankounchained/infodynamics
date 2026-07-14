# Phase 1: Baseline & Removal - Pattern Map

**Mapped:** 2026-07-13
**Files analyzed:** 5 (4 created, 1 edited; deletions have no pattern-mapping need)
**Analogs found:** 3 / 5 (no direct precedent exists in this repo for the golden-snapshot pattern — flagged explicitly below, per RESEARCH.md's own finding)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `tests/golden/capture_baseline.py` | utility (one-time script) | batch (run pipeline → serialize) | `tests/test_pipeline.py` (fixture/constructor usage) + `dashboard/build_dashboard_artifacts.py` (script-shape, npz-save idiom — read-only reference, being deleted) | role-match (no exact "capture script" precedent survives; closest still-alive shape is test-file fixture setup) |
| `tests/golden/baseline_arrays.npz` | config (binary data fixture) | file-I/O | none (new artifact type for this repo) | no analog |
| `tests/golden/baseline_meta.json` | config (data fixture) | file-I/O | none (new artifact type for this repo) | no analog |
| `tests/test_golden_baseline.py` | test | file-I/O + batch comparison (`np.allclose`) | `tests/test_clustering.py` (npz-free but `np.allclose` assertion idiom) + `tests/test_pipeline.py` (inline fixture constants, model construction) | role-match (assertion idiom exact; fixture-loading idiom is new) |
| `setup.py` | config | — (metadata edit) | `setup.py` itself (in-place edit, verbatim block already known) | exact (self-referential — no external analog needed) |

## Pattern Assignments

### `tests/golden/capture_baseline.py` (utility, one-time script)

**Analogs:** `tests/test_pipeline.py` (constructor/fixture conventions) and `infodynamics/embedding.py` (real `Encoder` signature)

**Fixture-constant pattern** (from `tests/test_pipeline.py` lines 7-11) — this repo's established convention for inline test text is module-level string constants, not external files:
```python
TEXT = "Cats chase mice. Dogs chase cats. The sun is bright today. Rain falls on the roof."
MULTISCALE_TEXT = (
    "Cats chase mice. Dogs chase cats. The sun is bright today. Rain falls on the roof. "
    "Birds sing at dawn. Fish swim in the sea. Wind blows through trees. Snow falls in winter."
)
```
Copy this shape for `FIXTURE_A`/`FIXTURE_B`/`FIXTURE_C` (each sized ~15-20 sentences per RESEARCH.md Pitfall 2, so default `scales`/`radii` aren't silently dropped).

**Real encoder construction** (from `infodynamics/embedding.py` lines 25-38) — do NOT use `FakeEncoder`(only pipeline text tests use that mock; this script must use the real one per RESEARCH.md):
```python
class Encoder:
    def __init__(
        self,
        model_name: str,
        device: Optional[str] = None,
        batch_size: int = 32,
        normalize: bool = True,
    ):
```
Instantiate as `Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")` — pin `device="cpu"` explicitly (RESEARCH.md Pitfall 3).

**Pipeline construction pattern** (from `tests/test_pipeline.py` lines 28, 71) — pass `encoder=` (not `model_name=`) to reuse one loaded encoder across multiple pipeline instances:
```python
model = InfoDynamics(model_name="fake-model", window_size=1)  # test uses model_name; capture script uses encoder= instead
model = MultiscaleInfoDynamics(model_name="fake-model", scales=[1, 2, 3], radii=[1, 2, 3])
```
Adapt to: `InfoDynamics(encoder=encoder, window_size=3)`, `MultiscaleInfoDynamics(encoder=encoder)` (using class defaults for `scales`/`radii` since fixtures are sized to support them).

**Clustering construction pattern** (from `tests/test_clustering.py` line 46):
```python
clusterer = SignalClusterer(n_clusters=2).fit(series)
```
Directly reusable — explicit `n_clusters=2` avoids `k_range`'s `k < n_series` constraint with only 3 fixture documents.

**Serialization idiom** — no surviving-code analog exists (the only `.npz`-writing code in this repo, `dashboard/build_dashboard_artifacts.py`'s cache writer, is itself being deleted this same phase). Use plain `numpy.savez`/`json.dump` directly per RESEARCH.md's Don't-Hand-Roll guidance; no project-specific wrapper to imitate.

---

### `tests/test_golden_baseline.py` (test, file-I/O + batch comparison)

**Analogs:** `tests/test_clustering.py` (assertion idiom), `tests/test_pipeline.py` (fixture + monkeypatch-free real-model pattern)

**File header / docstring convention** (from both analog files, line 1) — this repo's test files open with a minimal or empty module docstring:
```python
""" """
import numpy as np
```

**Tolerance-comparison idiom** (from `tests/test_clustering.py` lines 25-26) — this is the exact established convention to reuse for every `np.allclose` assertion in the new golden test, per RESEARCH.md's Don't-Hand-Roll table:
```python
assert np.allclose(distance_matrix, distance_matrix.T)
assert np.allclose(np.diag(distance_matrix), 0.0, atol=1e-8)
```
Apply as: `assert np.allclose(current, baseline["a_novelty"], rtol=1e-5, atol=1e-8)` (RESEARCH.md's recommended tolerance, matching this project's own established atol usage).

**Test function naming/shape convention** (from `tests/test_pipeline.py` lines 25-34) — one `test_*` function per assertion group, descriptive snake_case name stating the behavior:
```python
def test_fit_transform_returns_novelty_transience_resonance(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)
    model = InfoDynamics(model_name="fake-model", window_size=1)
    signal = model.fit_transform(TEXT)
    assert set(signal.keys()) == {"novelty", "transience", "resonance"}
```
The golden test does NOT monkeypatch the encoder (it must exercise the real model per RESEARCH.md) — omit the `monkeypatch` fixture and `FakeEncoder` entirely; re-run the same fixture text from `capture_baseline.py` (best practice: import the fixture constants from the capture script or duplicate them as module constants in the test file — planner's call, but duplicating as constants matches this repo's existing no-shared-conftest convention per TESTING.md's "no fixture files (conftest.py) used").

**Loading npz + json fixtures** — no repo analog; use plain `np.load(path)` (returns a lazy dict-like `NpzFile`) and `json.load(open(path))`, consistent with stdlib-first approach RESEARCH.md recommends (no wrapper to imitate).

---

### `setup.py` (config, metadata edit)

**Exact block to remove** (verbatim, current `setup.py` lines 50-57, per RESEARCH.md Code Examples):
```python
entry_points={
    'console_scripts': [
        'infodynamics-pack=infodynamics.shipping:pack_main',
        'infodynamics-pull=infodynamics.shipping:pull_main',
        'infodynamics-verify=infodynamics.shipping:verify_main',
        'infodynamics-init-project=infodynamics.shipping:init_project_main',
    ],
},
```
Remove this entire block (or replace with `entry_points={}` if the trailing key must remain syntactically for other reasons — check the surrounding `setup()` call for trailing commas/structure). No other `setup.py` section changes (`install_requires`/`extras_require` need no edits — confirmed by RESEARCH.md that nothing else depends on `shipping`/`cache_contract`).

**Follow-up required (not a code-pattern, but load-bearing):** `pip install -e .` (or `pip install --force-reinstall -e .`) must be re-run after this edit to clear stale `.venv/bin/infodynamics-{pack,pull,verify,init-project}` shims and regenerate `infodynamics.egg-info/entry_points.txt`. This is a runtime-state action, not a file to pattern-map, but the planner must sequence it as an explicit task per RESEARCH.md's Runtime State Inventory.

---

## Shared Patterns

### Real (non-mocked) encoder construction
**Source:** `infodynamics/embedding.py` lines 25-38
**Apply to:** `tests/golden/capture_baseline.py` and (indirectly, via re-running the same text) `tests/test_golden_baseline.py`
```python
Encoder(model_name: str, device: Optional[str] = None, batch_size: int = 32, normalize: bool = True)
```
Always pass `device="cpu"` explicitly for determinism (RESEARCH.md Pitfall 3).

### Tolerance-based numeric assertions
**Source:** `tests/test_clustering.py` lines 25-26
**Apply to:** every assertion in `tests/test_golden_baseline.py`
```python
np.allclose(a, b, rtol=1e-5, atol=1e-8)
```

### Inline module-level text fixtures (no external fixture files)
**Source:** `tests/test_pipeline.py` lines 7-11
**Apply to:** `tests/golden/capture_baseline.py` (fixture definitions) and `tests/test_golden_baseline.py` (re-declared or imported for re-run)
```python
TEXT = "..."  # module-level string constant, not conftest.py or external file
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md's Architecture Patterns → Pattern 2 structure instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/golden/baseline_arrays.npz` | config (binary fixture) | file-I/O | First binary snapshot artifact checked into `tests/`; no `tests/golden/`-style precedent exists anywhere in this repo (confirmed by RESEARCH.md, TESTING.md) |
| `tests/golden/baseline_meta.json` | config (data fixture) | file-I/O | Same as above — first JSON snapshot fixture in `tests/` |
| `tests/golden/capture_baseline.py` (serialization portion only) | utility | file-I/O | The only prior `.npz`-writing code in this repo lives in `dashboard/build_dashboard_artifacts.py`, which is being deleted in this same phase — not usable as a surviving analog. Use plain `numpy.savez`/`json.dump` directly (stdlib/numpy idiom, no project wrapper). |

## Metadata

**Analog search scope:** `tests/` (all `test_*.py` files), `infodynamics/embedding.py`, `infodynamics/pipeline.py`, `setup.py`
**Files scanned:** `tests/test_pipeline.py`, `tests/test_clustering.py`, `tests/test_manifest.py` (read by RESEARCH.md, confirmed being deleted, not usable as forward analog), `infodynamics/embedding.py`, `setup.py`
**Pattern extraction date:** 2026-07-13

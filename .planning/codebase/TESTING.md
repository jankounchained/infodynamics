# Testing Patterns

**Analysis Date:** 2026-07-13

## Test Framework

**Runner:**
- pytest >= 6.2.2
- Config: `setup.py` extras_require (no pytest.ini or pyproject.toml config file in project root)

**Assertion Library:**
- pytest's built-in `assert` statements
- NumPy assertions: `np.isclose()`, `np.allclose()`, `np.array_equal()`
- pytest approximation: `pytest.approx()` for floating-point comparison

**Run Commands:**
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -k <pattern>             # Run tests matching pattern
pytest -m slow                  # Run tests marked as slow
pytest --hypothesis-seed=0      # Run hypothesis tests with fixed seed
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root
- Test files co-located organization: `tests/test_<module>.py` mirrors `infodynamics/<module>.py`
- 9 test files covering core modules:
  - `test_metrics.py` → `infodynamics/metrics.py`
  - `test_segmentation.py` → `infodynamics/segmentation.py`
  - `test_pipeline.py` → `infodynamics/pipeline.py`
  - `test_infodynamics_class.py` → tests for main `WindowedRollingDistance` class
  - `test_clustering.py` → `infodynamics/clustering/`
  - `test_morphology.py` → `infodynamics/morphology.py`
  - `test_scalogram.py` → `infodynamics/scalogram.py`
  - `test_viz.py` → `infodynamics/viz.py`
  - `test_manifest.py` → manifest/shipping tests

**Naming:**
- Test files: `test_*.py`
- Test functions: `test_*` (descriptive names indicating what is tested)
- Test helpers: `_<function>` prefix for internal helper functions (e.g., `_make_series()`)

**Structure:**
```
tests/
├── test_metrics.py
├── test_segmentation.py
├── test_pipeline.py
├── test_infodynamics_class.py
├── test_clustering.py
├── test_morphology.py
├── test_scalogram.py
├── test_viz.py
└── test_manifest.py
```

## Test Structure

**Suite Organization:**

Tests are organized as flat module-level functions, not grouped in classes. Module-level constants define test data:

```python
# From test_segmentation.py
TEXT = "Hello world. This is a test! Is it working?\n\nNew paragraph here. Another sentence."

def test_segment_words():
    chunks = segment(TEXT, level="word")
    assert [c.text for c in chunks][:3] == ["Hello", "world.", "This"]
```

**Setup/Teardown:**
- No conftest.py file in project
- Fixtures not used; test data initialized at module level or within test functions
- For complex setup, helper functions like `_make_series()` create test data:

```python
# From test_clustering.py
def _make_series():
    x = np.linspace(0, 4 * np.pi, 50)
    rng = np.random.default_rng(0)
    group_a = [np.sin(x) + rng.normal(scale=0.05, size=x.shape) for _ in range(4)]
    group_b = [np.sin(x[:40] + np.pi) + rng.normal(scale=0.05, size=40) for _ in range(4)]
    return group_a + group_b
```

**Assertion Pattern:**
```python
# Standard assertions
assert result.shape == expected_shape

# Floating-point comparisons
assert np.isclose(result, expected_value)
assert result == pytest.approx(0.2780719051126376)

# Array comparisons
assert np.allclose(res_array, np.array([0.54245752, -0.26438562, 0.0]))

# Dict/Set assertions
assert set(signal.keys()) == {"novelty", "transience", "resonance"}

# Instance checks
assert isinstance(chunk, Chunk)
```

## Mocking

**Framework:** pytest's `monkeypatch` fixture

**Patterns:**

```python
# From test_pipeline.py - Mock the Encoder class
class FakeEncoder:
    """Deterministic stand-in for infodynamics.embedding.Encoder, avoids network calls."""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def encode(self, texts):
        rng = np.random.default_rng(0)
        return rng.normal(size=(len(texts), 8))


def test_fit_transform_returns_novelty_transience_resonance(monkeypatch):
    monkeypatch.setattr(pipeline_module, "Encoder", FakeEncoder)
    
    model = InfoDynamics(model_name="fake-model", window_size=1)
    signal = model.fit_transform(TEXT)
    
    assert set(signal.keys()) == {"novelty", "transience", "resonance"}
```

**Optional Dependencies:**

Use `pytest.importorskip()` to skip tests if optional dependencies aren't installed:

```python
# From test_clustering.py
tslearn = pytest.importorskip("tslearn")

def test_pairwise_distance_shape_and_symmetry():
    # Test implementation
```

**What to Mock:**
- External API calls (e.g., HuggingFace model loading)
- Network I/O operations
- File I/O when testing logic, not file handling

**What NOT to Mock:**
- NumPy/SciPy operations (unless testing around them)
- Core business logic of functions under test
- Mathematical operations

## Fixtures and Factories

**Test Data:**

Module-level constants for simple test data:
```python
TEXT = "Cats chase mice. Dogs chase cats. The sun is bright today. Rain falls on the roof."
MULTISCALE_TEXT = (
    "Cats chase mice. Dogs chase cats. The sun is bright today. Rain falls on the roof. "
    "Birds sing at dawn. Fish swim in the sea. Wind blows through trees. Snow falls in winter."
)
```

Factories for complex test data:
```python
def _make_series():
    """Creates test time series with two distinct groups."""
    # Implementation returns list of arrays
```

**Location:**
- Test data defined at module level or as helper functions at top of test files
- No fixture files (conftest.py) used

## Coverage

**Requirements:** No coverage enforcement configured

**View Coverage:**
```bash
pytest --cov=infodynamics --cov-report=html
```

Current test coverage:
- 81 test functions across 9 test files
- Tests cover: unit tests, integration tests, property-based tests
- No explicit coverage targets set in configuration

## Test Types

**Unit Tests:**
- Test individual functions in isolation (e.g., `test_rel_entr()`, `test_kl_div()`)
- Test method behavior on individual classes (e.g., `test_segment_words()`)
- Typically use simple, direct assertions
- Example: `test_relative_entropy_single_comparison()` tests entropy calculation with fixed inputs

**Integration Tests:**
- Test class methods working together (e.g., `test_fit_transform_returns_novelty_transience_resonance()`)
- Test pipeline end-to-end behavior
- Example: `test_fit_transform_returns_novelty_transience_resonance()` tests full InfoDynamics pipeline

**Property-based Tests:**
- Use hypothesis library (`hypothesis>=6.87.0`)
- Decorated with `@given` to generate random test cases
- Test invariants that must hold across many inputs
- Marked with `@pytest.mark.slow` since they're computationally intensive

```python
from hypothesis import given, strategies as st

@pytest.mark.slow
@given(
    st.lists(
        st.lists(
            st.floats(allow_nan=False, allow_infinity=False), min_size=2, max_size=2
        ),
        min_size=1,
    )
)
def test_validate_data_hypothesis(input_list):
    """Property-based test: data validation works for any list of lists."""
    i = WindowedRollingDistance(measure=js_dist, window_size=1)
    X = i._validate_data(input_list)
    
    assert isinstance(X, np.ndarray)
    assert X.shape == (len(input_list), len(input_list[0]))
```

## Common Patterns

**Async Testing:**
- Not applicable (synchronous, CPU-bound code)

**Error Testing:**
```python
# From test_segmentation.py
def test_chunk_size_must_be_positive():
    with pytest.raises(ValueError):
        segment(TEXT, chunk_size=0)

def test_invalid_level_raises():
    with pytest.raises(ValueError):
        segment(TEXT, level="paragraphs")

def test_barycenter_average_invalid_method_raises():
    with pytest.raises(ValueError):
        barycenter_average(_make_series()[:2], method="not-a-method")
```

**Comparison with Tolerance:**
```python
# For floating-point results
assert np.isclose(result, expected)
assert result == pytest.approx(expected_value)

# For arrays
assert np.allclose(array_result, expected_array)

# For very small differences
assert np.allclose(np.diag(distance_matrix), 0.0, atol=1e-8)
```

**Boundary/Edge Case Testing:**
```python
# From test_infodynamics_class.py
def test_calc_signal_data_shapes():
    """shape same as input - test with window_size=0, 1, 2"""
    i0 = WindowedRollingDistance(measure=js_dist, window_size=0)
    X0 = i0.fit_transform(X)
    # assertions...
```

**Test Markers:**
```python
@pytest.mark.slow  # Marks property-based tests that take longer
```

---

*Testing analysis: 2026-07-13*

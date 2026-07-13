# Coding Conventions

**Analysis Date:** 2026-07-13

## Naming Patterns

**Files:**
- snake_case (e.g., `metrics.py`, `time_series.py`, `segmentation.py`)
- Test files: `test_*.py` pattern

**Functions:**
- snake_case for all functions (public and private)
- Leading underscore for private/internal functions (e.g., `_rel_entr`, `_validate_data`, `_load_model`)
- Descriptive names indicating purpose

**Variables:**
- snake_case for all variables (local, global, parameters)
- Single letter variables acceptable for mathematical/mathematical convention (e.g., `p`, `q`, `x`, `y` in metrics functions)
- Trailing underscore for fitted attributes (e.g., `chunks_`, `embeddings_`, `signal_`, `labels_`)

**Types:**
- PascalCase for class names (e.g., `WindowedRollingDistance`, `InfoDynamics`, `MorphologicalEncoder`, `SignalClusterer`)
- PascalCase for type aliases (e.g., `Level = Literal["word", "sentence", "paragraph"]`)
- UPPER_CASE for module-level constants (e.g., `DISTANCES`, `_MODEL_CACHE`)

## Code Style

**Formatting:**
- No automatic formatter configured in repository (no Black, isort, or Prettier config)
- Manual code formatting; maintain readable spacing and alignment
- Default to PEP 8 conventions

**Linting:**
- No linter configuration found (no .pylintrc, .flake8, or ESLint config)
- Code follows Python conventions implicitly

**Docstrings:**
- NumPy style docstrings with Parameters and Returns sections
- Module-level docstrings present in most files (sometimes minimal)
- Function and class docstrings include parameter documentation and return value description
- Example from `infodynamics/pipeline.py`:
  ```python
  def __init__(self, model_name: Optional[str] = None, ...):
      """
      Parameters
      ----------
      model_name : str or None, default=None
          name of a HuggingFace Hub encoder model
      ...
      Returns
      -------
      signal : dict[str, np.ndarray]
          novelty, transience and resonance signals
      """
  ```

**Type Hints:**
- Type hints used throughout codebase for all function parameters and returns
- Imports from `typing` module: `Union`, `Optional`, `Callable`, `Sequence`, `List`, `Dict`, `Literal`, `Tuple`
- Imports from `typing_extensions`: `Self` for return type in methods
- Uses `numpy.typing.ArrayLike` for flexible array inputs
- Example from `infodynamics/metrics.py`:
  ```python
  def js_dist(p: np.ndarray, q: np.ndarray) -> float:
  ```

## Import Organization

**Order:**
1. Standard library imports (`os`, `sys`, `re`, `warnings`, `dataclasses`, `typing`)
2. Third-party imports (`numpy`, `scipy`, `sklearn`, `syntok`, `matplotlib`, `streamlit`)
3. Local imports (`from infodynamics...`)

**Path Aliases:**
- All imports use absolute paths from package root
- No relative imports observed (e.g., `from infodynamics.metrics import...`, not `from .metrics import...`)
- Subpackage imports documented in `__init__.py` files for public API (see `infodynamics/__init__.py`)

**Example from `infodynamics/pipeline.py`:**
```python
from typing import Callable, Optional, Sequence, Union
from typing_extensions import Self

from sklearn.base import BaseEstimator, TransformerMixin

from infodynamics.embedding import Encoder
from infodynamics.scalogram import FooteNovelty, Scalogram, structure_descriptors
```

## Error Handling

**Patterns:**
- `ValueError` raised for invalid parameter values
- `ImportError` raised for missing optional dependencies, with helpful message about how to install
- Context provided via `from e` syntax (e.g., `raise ImportError(...) from e`)
- Input validation in methods before processing (e.g., `if chunk_size < 1: raise ValueError(...)`)

**Example from `infodynamics/embedding.py`:**
```python
try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "The 'embedding' extra is required to use Encoder. "
        "Install it with `pip install infodynamics[embedding]`."
    ) from e
```

**Example from `infodynamics/segmentation.py`:**
```python
if chunk_size < 1:
    raise ValueError(f"'chunk_size' must be >= 1, got {chunk_size}.")
```

## Logging

**Framework:** Python's standard `warnings` module

**Patterns:**
- `warnings.warn()` used for non-fatal issues (e.g., unrecognized input types)
- Example from `infodynamics/time_series.py`:
  ```python
  warnings.warn(
      f"Input data type ({type(X)}) not recognized. Returning input data as is."
  )
  ```

## Comments

**When to Comment:**
- Comments used for explaining complex logic or non-obvious algorithm choices
- Example from `infodynamics/metrics.py`: "add smallest possible float to avoid RunTime warnings about zero division"
- Algorithm steps often documented via comments in mathematical functions
- Complex regex patterns documented (e.g., in `strip_markdown` function)

**JSDoc/TSDoc:**
- Not applicable (Python project; NumPy-style docstrings used instead)

## Function Design

**Size:**
- Functions generally kept to single responsibility principle
- Helper functions extracted with underscore prefix for internal use
- Private methods in classes use `self._method()` pattern

**Parameters:**
- Descriptive parameter names
- Default parameters provided for optional settings
- Type hints on all parameters
- Example from `infodynamics/time_series.py`:
  ```python
  def __init__(
      self,
      measure: Union[str, Callable],
      window_size: int,
      jump_size: int = 0,
      inplace_constant: Union[int, float] = 0,
      estimate_error: bool = False,
      averaging_weigts: Optional[ArrayLike] = None,
  ):
  ```

**Return Values:**
- Type hints on all return types
- Functions return dicts, numpy arrays, or objects as appropriate
- Fitted attributes stored as instance attributes with trailing underscore (e.g., `self.chunks_`, `self.signal_`)

## Module Design

**Exports:**
- `__init__.py` files in subpackages re-export main classes and functions
- Example from `infodynamics/__init__.py`:
  ```python
  from infodynamics.clustering import SignalClusterer
  from infodynamics.morphology import MorphologicalEncoder
  ```

**Barrel Files:**
- Used in subpackages (e.g., `infodynamics/clustering/__init__.py`) to provide clean public API
- Imports are explicit, not using `from .module import *`

## Scikit-learn Compatibility

**Class Inheritance:**
- Pipeline classes inherit from `sklearn.base.BaseEstimator` and `sklearn.base.TransformerMixin`
- Implement `fit()` and `transform()` methods following scikit-learn convention
- Example from `infodynamics/pipeline.py`:
  ```python
  class InfoDynamics(BaseEstimator, TransformerMixin):
      def fit(self, text: str, y=None) -> Self:
      def fit_transform(self, text: str, y=None) -> dict:
  ```

---

*Convention analysis: 2026-07-13*

"""
Canonical usage example for infodynamics.

Demonstrates the two supported entry points into the library:

1. core_only_demo() — feed a plain numeric ndarray straight into the core
   sklearn-compatible estimators (InfoDynamics, MultiscaleInfoDynamics).
   This path imports nothing from infodynamics.text: it is the
   modality-agnostic core, usable on any numeric time series (embeddings
   from your own pipeline, sensor readings, whatever numeric matrix you
   have). No optional extras are required.

2. pipeline_demo() — compose the text on-ramp (TextSegmenter -> Encoder)
   with MultiscaleInfoDynamics inside a real sklearn.pipeline.Pipeline,
   driving the whole thing with a single fit_transform(text) call. This
   path requires the 'embedding' extra (sentence-transformers):

       pip install ".[embedding]"

   The first run downloads a small sentence-embedding model from the
   Hugging Face Hub.

Run from a clone of the repository with:
    pip install ".[embedding]"
    python examples/basic_usage.py
"""
import numpy as np


def core_only_demo() -> None:
    """Core-only path: a numeric ndarray in, zero infodynamics.text imports."""
    from infodynamics import InfoDynamics, MultiscaleInfoDynamics

    rng = np.random.default_rng(0)
    X = rng.standard_normal((60, 16))  # (n_chunks, n_features)

    info_dynamics = InfoDynamics(window_size=3)
    signal = info_dynamics.fit_transform(X)
    print(f"InfoDynamics.fit_transform(X) -> array shape {signal.shape}")
    print(f"InfoDynamics.signal_ keys: {sorted(info_dynamics.signal_.keys())}")

    # 60 rows satisfies MultiscaleInfoDynamics' default scales/radii
    # (max scale/radius 21 requires n_chunks >= 43), so defaults are safe here.
    multiscale = MultiscaleInfoDynamics()
    scalogram = multiscale.fit_transform(X)
    print(f"MultiscaleInfoDynamics.fit_transform(X) -> scalogram shape {scalogram.shape}")
    print(f"MultiscaleInfoDynamics.result_ keys: {sorted(multiscale.result_.keys())}")


def pipeline_demo() -> None:
    """Full Pipeline path: text on-ramp -> analysis, composed via sklearn.pipeline.Pipeline."""
    from sklearn.pipeline import Pipeline

    from infodynamics import MultiscaleInfoDynamics
    from infodynamics.text import Encoder, TextSegmenter

    # 50 sentences satisfies MultiscaleInfoDynamics' default scale/radius
    # requirements (n_chunks >= 43), mirroring
    # tests/test_pipeline_composition.py::test_pipeline_with_real_encoder.
    text = " ".join(f"Sentence number {i} describes a simple event." for i in range(50))

    pipeline = Pipeline(
        [
            ("segment", TextSegmenter()),
            ("encode", Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")),
            ("analyze", MultiscaleInfoDynamics()),
        ]
    )

    scalogram = pipeline.fit_transform(text)
    print(f"Pipeline.fit_transform(text) -> scalogram shape {scalogram.shape}")


if __name__ == "__main__":
    print("=== Core-only demo (numeric ndarray, no text on-ramp) ===")
    core_only_demo()

    print("\n=== Full Pipeline demo (text on-ramp -> analysis) ===")
    pipeline_demo()

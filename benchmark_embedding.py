#!/usr/bin/env python3
"""
Benchmarks embedding throughput of one or more HuggingFace Hub encoder
models, using infodynamics.text.embedding.Encoder.

Measures, per model:
  - load_time_s     time to load the model and run one warmup batch
  - encode_time_s   best-of-`--repeats` wall-clock time to encode the full
                     text set
  - texts_per_sec / chars_per_sec

By default the text set is drawn from a small built-in sentence pool
(sampled/repeated to reach --n-texts), so the script runs standalone. Pass
--csv to benchmark on your own corpus instead.

Usage
-----
    python benchmark_embedding.py --models BAAI/bge-m3 sentence-transformers/all-MiniLM-L6-v2
    python benchmark_embedding.py --models BAAI/bge-m3 --n-texts 500 --device mps
    python benchmark_embedding.py --models BAAI/bge-m3 --csv 260708_radomil_collection.csv --out results.csv
"""
import argparse
import random
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from infodynamics.text.embedding import Encoder
from infodynamics.text.segmentation import segment

_SENTENCE_POOL = [
    "The quick brown fox jumps over the lazy dog near the riverbank.",
    "Researchers published a new study on the effects of sleep on memory consolidation.",
    "She opened the window and let the cool evening air fill the room.",
    "The stock market fell sharply after the central bank raised interest rates.",
    "He spent the afternoon repairing the old bicycle he found in the garage.",
    "Climate scientists warn that global temperatures could rise faster than expected.",
    "The recipe calls for two cups of flour, a pinch of salt, and three eggs.",
    "After years of negotiation, the two countries finally signed a trade agreement.",
    "The children built a sandcastle on the beach while their parents watched.",
    "Quantum computers use qubits instead of classical bits to perform calculations.",
    "The museum's new exhibit features artifacts from ancient Mesopotamia.",
    "Traffic was backed up for miles after the accident on the highway.",
    "The novel explores themes of memory, loss, and identity across three generations.",
    "Engineers are testing a new battery design that charges twice as fast.",
    "The orchestra performed a haunting rendition of the composer's final symphony.",
    "Local farmers reported a record harvest despite the unusually dry summer.",
    "The startup raised ten million dollars in its latest funding round.",
    "A gentle rain fell over the city as commuters hurried home from work.",
    "The committee will review the proposal and announce a decision next month.",
    "Marine biologists discovered a new species of deep-sea coral off the coast.",
]


def _sample_texts(pool: List[str], n: int, seed: int) -> List[str]:
    rng = random.Random(seed)
    if len(pool) >= n:
        return rng.sample(pool, n)
    return [rng.choice(pool) for _ in range(n)]


def load_texts(args: argparse.Namespace) -> List[str]:
    if args.csv is not None:
        df = pd.read_csv(args.csv)
        pool = []
        for doc in df[args.text_column].fillna("").astype(str):
            if not doc.strip():
                continue
            try:
                chunks = segment(doc, level=args.segment_level)
            except ValueError:
                continue  # a handful of documents can fail to segment (e.g. curly quotes)
            pool.extend(c.text for c in chunks if c.text.strip())
        if not pool:
            raise ValueError(f"No text found in '{args.csv}' column '{args.text_column}'.")
    else:
        pool = _SENTENCE_POOL

    return _sample_texts(pool, args.n_texts, args.seed)


def benchmark_model(
    model_name: str,
    texts: List[str],
    device: Optional[str],
    batch_size: int,
    repeats: int,
) -> dict:
    encoder = Encoder(model_name, device=device, batch_size=batch_size)

    # first call downloads/loads the model and moves it to `device`; time it
    # separately from steady-state throughput.
    warmup = texts[: min(batch_size, len(texts))]
    t0 = time.perf_counter()
    encoder.encode(warmup)
    load_time = time.perf_counter() - t0

    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        encoder.encode(texts)
        times.append(time.perf_counter() - t0)

    encode_time = min(times)
    n_chars = sum(len(t) for t in texts)
    return dict(
        model=model_name,
        n_texts=len(texts),
        n_chars=n_chars,
        load_time_s=load_time,
        encode_time_s=encode_time,
        encode_time_std_s=float(np.std(times)),
        texts_per_sec=len(texts) / encode_time,
        chars_per_sec=n_chars / encode_time,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="+", required=True, help="one or more HuggingFace Hub encoder model names")
    parser.add_argument("--n-texts", type=int, default=200, help="number of text snippets to embed")
    parser.add_argument("--csv", type=Path, default=None, help="optional CSV to draw text from instead of the built-in sample pool")
    parser.add_argument("--text-column", default="content", help="column of --csv to read text from")
    parser.add_argument("--segment-level", default="sentence", choices=["word", "sentence", "paragraph"], help="how to split --csv text into snippets")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default=None, help="e.g. 'cpu', 'mps', 'cuda'; defaults to sentence-transformers' auto-detection")
    parser.add_argument("--repeats", type=int, default=3, help="number of timed encode passes per model; the fastest is reported")
    parser.add_argument("--seed", type=int, default=0, help="seed for sampling the text set")
    parser.add_argument("--out", type=Path, default=None, help="optional path to save results as CSV")
    args = parser.parse_args()

    texts = load_texts(args)
    n_chars = sum(len(t) for t in texts)
    print(f"Benchmarking {len(args.models)} model(s) on {len(texts)} texts ({n_chars} chars), "
          f"batch_size={args.batch_size}, device={args.device or 'auto'}, repeats={args.repeats}")

    results = []
    for model_name in args.models:
        print(f"\n{model_name}")
        try:
            result = benchmark_model(model_name, texts, args.device, args.batch_size, args.repeats)
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {e}")
            continue
        print(
            f"  load {result['load_time_s']:.2f}s | "
            f"encode {result['encode_time_s']:.2f}s (+/-{result['encode_time_std_s']:.2f}s) | "
            f"{result['texts_per_sec']:.1f} texts/s | {result['chars_per_sec']:.0f} chars/s"
        )
        results.append(result)

    if not results:
        print("\nNo model produced a result.")
        return

    df = pd.DataFrame(results)
    print("\n=== summary ===")
    print(df.round(2).to_string(index=False))

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()

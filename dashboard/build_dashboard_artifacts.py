"""
Dashboard cache builder — turns the raw multi-author text corpus into every
artifact the Evidence-bench Streamlit app (dashboard/app.py) reads.

WHY A SEPARATE PRECOMPUTE STEP
-------------------------------
Embedding + multi-scale structure analysis (self-similarity matrix, scalogram,
Foote novelty) over the whole corpus (~15k sentences) is far too slow to redo
on every Streamlit rerun. This script runs once — whenever the corpus or the
encoder model changes — and writes a self-contained cache to
dashboard/cache/. The app (via dashboard/bench_core.py) only ever *reads*
that cache; it never recomputes anything expensive.

PIPELINE
--------
    1. load_corpus            CSV row -> kept documents (author filter, drops
                               empty content)
    2. segment_corpus         document text -> list of sentences; short docs
                               are dropped
    3. encode_corpus            every sentence in the corpus, encoded in one
                               shared call -- once for embeddings, and again
                               for morphological features if enabled
    4. analyze_document        per document, per signal: self-similarity
                               matrix, scalogram, multi-scale Foote novelty,
                               interpretable descriptors
    5. build_corpus_aggregates corpus-level views: PCA document map, which
                               descriptors most separate authors, per-author
                               mean novelty profile / scale-energy / rhythm
                               -- for embeddings, and again for morphology
    6. build_human_index       flat nearest-neighbour index over human
                               sentences (powers the app's "suggest a human
                               contrast" feature)
    7. write_*_cache            persist everything under dashboard/cache/

Each stage above is a standalone, independently testable function -- see
run_pipeline() for how they're wired together. Nothing here holds implicit
global state; every stage takes the PipelineConfig (or the specific pieces of
it needs) explicitly, so the pipeline can just as well be driven from a
notebook or a test as from the CLI.

The self-similarity matrix / scalogram / Foote novelty math is
infodynamics.scalogram (self_similarity_matrix, Scalogram, FooteNovelty,
structure_descriptors) -- the same functions run for both the embedding and
morphology signals, since both are just (n_sentences, n_features) matrices to
that code.

CACHE CONTRACT (kept in sync with dashboard/README.md)
-------------------------------------------------------
    cache/corpus.csv              one row per document + structure descriptors
                                   (embedding-based, plus morph_*-prefixed
                                   versions if morphology is enabled)
    cache/ssm/<doc_id>.npy         (n, n) cosine self-similarity matrix
    cache/emb/<doc_id>.npy         (n, dim) L2-normalized sentence embeddings
    cache/curves/<doc_id>.npz      scalogram, novelty, nov1, local_red, scales, radii
    cache/sentences/<doc_id>.json  [{"idx": int, "text": str}, ...] -- shared by
                                   both signals, since both encode the same sentences
    cache/morph_ssm/<group>/<doc_id>.npy   like ssm/, but over one morphological
                                   feature group's features (only written if
                                   morphology is enabled; one subdir per group
                                   in infodynamics.morphology.MorphologicalEncoder.FEATURE_GROUPS)
    cache/morph_curves/<group>/<doc_id>.npz  like curves/, over that group's features
    cache/morph_features/<group>/<doc_id>.npy  (n, n_group_features) RAW
                                   per-sentence morphological feature values for
                                   that group -- e.g. pos_prop_VERB per sentence
                                   -- for direct inspection in the app, not just
                                   derived signals
    cache/redundant_pairs.json     candidate near-duplicate sentence pairs
    cache/flat_regions.json        candidate low-novelty stretches
    cache/aggregates.json          corpus-level summaries (PCA, Cohen's d, ...),
                                   plus a nested "morphology" key (one entry per
                                   feature group) if enabled
    cache/human_index.npy          (n_human_sentences, dim) embeddings
    cache/human_index_meta.json    metadata parallel to human_index.npy
    cache/config.json              the PipelineConfig this cache was built with,
                                   plus morphology_feature_groups/morphology_feature_names
                                   if enabled
    cache/manifest.json            provenance for shipping this cache (pipeline
                                   version, config hash, corpus hash, model
                                   identities, per-file checksums) -- see
                                   infodynamics.cache_contract and
                                   infodynamics/shipping.py (pack/pull/verify)

SIGNALS -- THE TWO SWAP POINTS
--------------------------------
The embedding encoder is a required CLI argument (`--model-name`), not an
environment variable: the exact command you ran is then self-documenting, and
there is no hidden global deciding which model was used. Any HuggingFace Hub
sentence-embedding model works (e.g. "Qwen/Qwen3-Embedding-8B",
"sentence-transformers/all-MiniLM-L6-v2"), loaded through
infodynamics.embedding.Encoder.

There is deliberately no lexical/TF-IDF fallback here: the whole point of this
dashboard is comparing the *semantic* structure of ai vs. human writing, and
the nearest-neighbour "human contrast" search only makes sense over a real
embedding space. If you need to smoke-test the pipeline without downloading a
large model, pass a small one (e.g. `--model-name
sentence-transformers/all-MiniLM-L6-v2`) and `--limit 5`.

Morphological/syntactic structure is a second, optional signal computed over
the same sentences, via infodynamics.morphology.MorphologicalEncoder /
encode_all_feature_groups (UDPipe + textdescriptives). It's off by default;
pass `--morphology` to enable it, which computes and caches *every* group in
MorphologicalEncoder.FEATURE_GROUPS (one shared UDPipe parse, extracted once
per group -- see encode_all_feature_groups' docstring) so the app can switch
between them at runtime instead of picking one at cache-build time.
spacy_udpipe.download() currently fails against LINDAT's repository (see
run_morphology_demo.py's docstring for a working mirror); until that's fixed
upstream, fetch a model manually and pass its path via `--morphology-model-path`.

Run
---
    python dashboard/build_dashboard_artifacts.py --model-name Qwen/Qwen3-Embedding-8B
    python dashboard/build_dashboard_artifacts.py --model-name Qwen/Qwen3-Embedding-8B --device mps
    python dashboard/build_dashboard_artifacts.py --model-name sentence-transformers/all-MiniLM-L6-v2 --limit 5
    python dashboard/build_dashboard_artifacts.py --model-name Qwen/Qwen3-Embedding-8B \\
        --morphology --morphology-model-path czech-pdt.udpipe
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

# Sentence splitting is a standalone, Czech-tuned module at the repo root
# (abbreviation handling, heading/bullet-per-line splitting) with no package
# equivalent -- shared with run_multiscale_demo.py. Using the *same* sentence
# list for both signals below is what makes them directly comparable.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scalogram_foote_prototype import split_sentences  # noqa: E402
from infodynamics import __version__ as PIPELINE_VERSION  # noqa: E402
from infodynamics import cache_contract  # noqa: E402
from infodynamics.embedding import Encoder  # noqa: E402
from infodynamics.morphology import MorphologicalEncoder, encode_all_feature_groups  # noqa: E402
from infodynamics.scalogram import (  # noqa: E402
    FooteNovelty, Scalogram, rolling_gap_distance, self_similarity_matrix, structure_descriptors,
)

DASHBOARD_DIR = Path(__file__).resolve().parent
DEFAULT_CACHE_DIR = DASHBOARD_DIR / "cache"
DEFAULT_CSV = REPO_ROOT / "260708_radomil_collection.csv"

# Descriptor columns that (a) go into corpus.csv, (b) feed the Overview page's
# PCA document map, and (c) get ranked by |Cohen's d| to find what most
# separates ai from human writing. Kept as a module constant so every stage
# that touches "the descriptor columns" refers to the same list.
DESCRIPTOR_FEATURE_COLUMNS = [
    "mean_offdiag_sim", "p90_offdiag_sim", "dist_var_w5",
    "novelty_var", "mean_local_red", "boundary_rate",
]
# Same descriptors, computed over each morphological feature group's features
# instead of embeddings -- written into corpus.csv only when morphology is
# enabled (see run_pipeline()), so the Overview page's discriminator ranking
# can surface every signal in one table without a mode switch.
def morph_descriptor_columns(feature_groups: Sequence[str]) -> list:
    return [f"morph_{g}_{c}" for g in feature_groups for c in DESCRIPTOR_FEATURE_COLUMNS]


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
@dataclass
class PipelineConfig:
    """Every knob for one cache build, in a single explicit object instead of
    a module-level global dict. This is what makes the pipeline testable and
    importable: `run_pipeline(PipelineConfig(...))` works the same from a
    notebook, a unit test, or `main()`'s argparse wrapper.

    Parameters
    ----------
    model_name : str
        HuggingFace Hub sentence-embedding model, e.g. "Qwen/Qwen3-Embedding-8B".
        The only required argument -- there is no default backend to fall
        back to (see module docstring: "the only swap point").
    csv_path : Path
        corpus CSV with file_name/project/subproject/author/content columns.
    cache_dir : Path
        where to write the cache (must match dashboard/bench_core.py's CACHE).
    device : str or None
        device to load the encoder onto, e.g. "cpu", "mps", "cuda". Defaults
        to the model's own default.
    batch_size : int
        sentences per encoder batch.
    authors : Sequence[str]
        which `author` column values to keep. Defaults to ("ai", "human");
        the corpus also contains a small number of 'draft' rows that are not
        meaningful for the ai-vs-human comparison.
    min_sentences : int
        documents shorter than this are dropped: too few points for the
        requested scales/radii to fit, and not useful signal anyway.
    scales : Sequence[int]
        scalogram window sizes (in sentences). See scalogram_foote_prototype.scalogram.
    radii : Sequence[int]
        Foote novelty checkerboard-kernel radii (in sentences).
    ref_radius : int
        which radius' novelty curve stands in for "the" 1-D novelty signal
        of a document, used by aggregates/flat-region detection/autocorrelation.
    pair_min_gap : int
        minimum sentence-index distance for a redundant-pair candidate (skips
        adjacent sentences, which are similar for boring topical-continuity
        reasons rather than actual repetition).
    pair_sim_thresh : float
        minimum cosine similarity for a redundant-pair candidate.
    pair_top_k : int
        cap on redundant-pair candidates kept per document.
    flat_min_len : int
        minimum run length (sentences) for a flat-region candidate.
    flat_quantile : float
        a sentence counts as "flat" if its reference novelty falls at or
        below this per-document quantile.
    limit : int or None
        only process the first N documents. For quick smoke runs.
    morphology_enabled : bool
        whether to compute the morphology signal -- a second, optional
        signal alongside embeddings. False (the default) skips it entirely:
        no morph_* cache files are written, and the app simply doesn't
        render morphology sections. True computes and caches *every* group
        in MorphologicalEncoder.FEATURE_GROUPS, so the app can switch
        between them at runtime (see encode_all_feature_groups).
    morphology_lang : str
        UDPipe language code for the morphology signal.
    morphology_model_path : str or None
        path to a local .udpipe model file, see run_morphology_demo.py's
        docstring for why this is currently needed (spacy_udpipe.download()
        is broken against LINDAT's current repository layout).
    """
    model_name: str
    csv_path: Path = DEFAULT_CSV
    cache_dir: Path = DEFAULT_CACHE_DIR
    device: Optional[str] = None
    batch_size: int = 32
    authors: Sequence[str] = ("ai", "human")
    min_sentences: int = 12

    scales: Sequence[int] = (2, 3, 5, 8, 13, 21)
    radii: Sequence[int] = (3, 5, 8, 13, 21)
    ref_radius: int = 8

    pair_min_gap: int = 5
    pair_sim_thresh: float = 0.35
    pair_top_k: int = 40

    flat_min_len: int = 6
    flat_quantile: float = 0.30

    limit: Optional[int] = None

    morphology_enabled: bool = False
    morphology_lang: str = "cs"
    morphology_model_path: Optional[str] = None

    def to_json_dict(self) -> dict:
        """JSON-serializable view of this config (Path -> str), written into
        cache/config.json so the running dashboard can display/introspect
        exactly how its cache was built."""
        d = asdict(self)
        d["csv_path"] = str(self.csv_path)
        d["cache_dir"] = str(self.cache_dir)
        return d


def parse_args(argv: Optional[Sequence[str]] = None) -> PipelineConfig:
    """Thin CLI wrapper around PipelineConfig.

    `--model-name` is a required argument rather than an `EMB_BACKEND`
    environment variable: the command you actually run is then
    self-documenting, and there's no hidden global state deciding which
    embeddings a given cache was built with.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--model-name", required=True,
        help="HuggingFace Hub sentence-embedding model, e.g. "
             "'Qwen/Qwen3-Embedding-8B' or 'sentence-transformers/all-MiniLM-L6-v2'.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, dest="csv_path",
                        help=f"corpus CSV (default: {DEFAULT_CSV.name}).")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR,
                        help="where to write the cache (default: dashboard/cache).")
    parser.add_argument("--device", default=None,
                        help="e.g. 'cpu', 'mps', 'cuda'. Defaults to the model's own default.")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--authors", nargs="+", default=["ai", "human"],
                        help="which `author` column values to keep (default: ai human).")
    parser.add_argument("--min-sentences", type=int, default=12)
    parser.add_argument("--scales", nargs="+", type=int, default=[2, 3, 5, 8, 13, 21])
    parser.add_argument("--radii", nargs="+", type=int, default=[3, 5, 8, 13, 21])
    parser.add_argument("--ref-radius", type=int, default=8)
    parser.add_argument("--pair-min-gap", type=int, default=5)
    parser.add_argument("--pair-sim-thresh", type=float, default=0.35)
    parser.add_argument("--pair-top-k", type=int, default=40)
    parser.add_argument("--flat-min-len", type=int, default=6)
    parser.add_argument("--flat-quantile", type=float, default=0.30)
    parser.add_argument("--limit", type=int, default=None,
                        help="only process the first N documents (quick smoke run).")
    parser.add_argument("--morphology", action="store_true",
                        help="enable the morphology signal (off by default). Computes and "
                             f"caches every group in {MorphologicalEncoder.FEATURE_GROUPS} "
                             "so the app can switch between them at runtime.")
    parser.add_argument("--morphology-lang", default="cs", help="UDPipe language code.")
    parser.add_argument("--morphology-model-path", default=None,
                        help="path to a local .udpipe model file (spacy_udpipe.download() "
                             "is currently broken -- see run_morphology_demo.py's docstring).")
    args = parser.parse_args(argv)

    return PipelineConfig(
        model_name=args.model_name,
        csv_path=args.csv_path,
        cache_dir=args.cache_dir,
        device=args.device,
        batch_size=args.batch_size,
        authors=tuple(args.authors),
        min_sentences=args.min_sentences,
        scales=tuple(args.scales),
        radii=tuple(args.radii),
        ref_radius=args.ref_radius,
        pair_min_gap=args.pair_min_gap,
        pair_sim_thresh=args.pair_sim_thresh,
        pair_top_k=args.pair_top_k,
        flat_min_len=args.flat_min_len,
        flat_quantile=args.flat_quantile,
        limit=args.limit,
        morphology_enabled=args.morphology,
        morphology_lang=args.morphology_lang,
        morphology_model_path=args.morphology_model_path,
    )


# --------------------------------------------------------------------------- #
# doc_id
# --------------------------------------------------------------------------- #
def slug(*parts: str) -> str:
    """Builds an ASCII, lowercase, hyphen-separated identifier from one or
    more strings. Used as the doc_id: the filename stem for every
    per-document cache artifact (cache/ssm/<doc_id>.npy, etc).

    Diacritics are stripped (not percent-encoded), so the result stays a
    plain, filesystem- and URL-safe token.

    Parameters
    ----------
    *parts : str
        one or more strings to combine, e.g. slug(project, subproject, file_name).
        Multiple parts matter: this corpus reuses the same file_name across
        several "Koncept N.0" subprojects (distinct drafts of the same
        document), so file_name alone collides -- see segment_corpus().
    """
    raw = "-".join(str(p) for p in parts)
    ascii_text = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return cleaned or "doc"


# --------------------------------------------------------------------------- #
# corpus loading & segmentation
# --------------------------------------------------------------------------- #
@dataclass
class DocRecord:
    """One corpus document, populated in stages as it moves through the
    pipeline: segment_corpus() fills `sentences`, assign_features() later
    fills `embeddings`, and, if morphology is enabled, `morph_features` is
    filled per feature group (one entry per group in
    MorphologicalEncoder.FEATURE_GROUPS)."""
    doc_id: str
    file_name: str
    author: str
    project: str
    subproject: str
    sentences: list = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None
    morph_features: dict = field(default_factory=dict)


def load_corpus(cfg: PipelineConfig) -> pd.DataFrame:
    """Reads the corpus CSV and keeps only the requested authors.

    Parameters
    ----------
    cfg : PipelineConfig

    Returns
    -------
    pd.DataFrame
        one row per document, with at least file_name/project/subproject/
        author/content columns. Missing content is treated as empty (rather
        than dropped), so it shows up as a 0-sentence document and is
        skipped by segment_corpus()'s min_sentences check, not silently lost.
    """
    df = pd.read_csv(cfg.csv_path)
    df["content"] = df["content"].fillna("")
    df = df[df.author.isin(cfg.authors)].reset_index(drop=True)
    if cfg.limit:
        df = df.head(cfg.limit)
    return df


def segment_corpus(df: pd.DataFrame, cfg: PipelineConfig) -> tuple[list, list]:
    """Splits every document's raw text into sentences, and builds one flat
    sentence list for the whole corpus so every sentence can be embedded in
    a single shared encoder call (one batch instead of one call per document).

    Parameters
    ----------
    df : pd.DataFrame
        as returned by load_corpus().
    cfg : PipelineConfig

    Returns
    -------
    docs : list[DocRecord]
        `sentences` populated; `embeddings`/`morph_features` still None
        (filled in later by assign_features()).
    flat_sentences : list[str]
        every sentence across every doc, in doc order. encode_corpus() encodes
        this list directly; assign_features() splits the result back out
        per document using each DocRecord's sentence count.
    """
    docs: list[DocRecord] = []
    flat_sentences: list[str] = []
    n_dropped = 0

    for row in df.itertuples(index=False):
        sentences = split_sentences(row.content)
        if len(sentences) < cfg.min_sentences:
            n_dropped += 1
            continue
        # doc_id must disambiguate documents that share a file_name across
        # different subprojects (e.g. "01 - ....md" appears once per
        # "Koncept N.0" draft) -- see slug()'s docstring.
        doc_id = slug(row.project, row.subproject, row.file_name)
        docs.append(DocRecord(
            doc_id=doc_id, file_name=row.file_name, author=row.author,
            project=str(row.project), subproject=str(row.subproject),
            sentences=sentences,
        ))
        flat_sentences.extend(sentences)

    if n_dropped:
        print(f"  skipped {n_dropped} document(s) shorter than "
              f"{cfg.min_sentences} sentences")
    return docs, flat_sentences


# --------------------------------------------------------------------------- #
# encoding -- the two swap points (embedding model, morphology feature group)
# --------------------------------------------------------------------------- #
def encode_corpus(encoder, sentences: list, label: str) -> np.ndarray:
    """Encodes every sentence in the corpus with a single shared encoder call.

    Used for both the embedding signal (infodynamics.embedding.Encoder) and,
    if enabled, the morphology signal (infodynamics.morphology.MorphologicalEncoder)
    -- both expose the same `.encode(texts) -> np.ndarray` interface, so this
    is the only place either model is loaded (and, on first use, downloaded).
    Everything downstream (self-similarity matrix, scalogram, Foote novelty)
    only assumes a (n_sentences, n_features) matrix, regardless of which
    encoder produced it or whether its rows are L2-normalized.

    Parameters
    ----------
    encoder : object
        anything exposing `.encode(texts: List[str]) -> np.ndarray`.
    sentences : list[str]
        as returned by segment_corpus()'s `flat_sentences`.
    label : str
        human-readable name for the progress message.

    Returns
    -------
    np.ndarray of shape (len(sentences), n_features), float32.
    """
    print(f"Encoding {len(sentences)} sentences with {label}...")
    return np.asarray(encoder.encode(sentences), dtype=np.float32)


def assign_features(docs: list, features: np.ndarray, attr: str = "embeddings") -> None:
    """Splits a flat (total_sentences, n_features) matrix back into
    per-document arrays, in place, on each DocRecord's `attr` field.

    Relies on `docs` and `features` covering the same sentences in the same
    order that segment_corpus() produced -- i.e. this must be called with the
    exact `flat_sentences` list (or its encoding) that segment_corpus() returned.
    """
    offset = 0
    for doc in docs:
        n = len(doc.sentences)
        setattr(doc, attr, features[offset:offset + n])
        offset += n


# --------------------------------------------------------------------------- #
# per-document analysis
# --------------------------------------------------------------------------- #
@dataclass
class DocAnalysis:
    """Multi-scale structure for one document: everything analyze_document()
    computes, before it's written to disk (write_document_cache()) or folded
    into corpus-level aggregates (build_corpus_aggregates())."""
    ssm: np.ndarray                  # (n, n) cosine self-similarity matrix
    scalogram: np.ndarray             # (n_scales, n) windowed rolling-gap distance
    scales: list
    novelty: np.ndarray                # (n_radii, n) multi-scale Foote novelty
    radii: list
    novelty_ref: np.ndarray            # (n,) novelty at cfg.ref_radius -- "the" 1-D signal
    local_redundancy: np.ndarray       # (n,) per-sentence max similarity to a distant sentence
    descriptors: dict                  # scalar summary stats -- one row of corpus.csv


def local_redundancy(S: np.ndarray, gap: int) -> np.ndarray:
    """For each sentence, its max cosine similarity to any OTHER sentence at
    least `gap` positions away.

    Adjacent sentences are excluded because they're usually similar for
    boring reasons (topical continuity, not repetition); a high score here
    means "this sentence restates something said elsewhere in the document".

    Parameters
    ----------
    S : np.ndarray of shape (n, n)
        self-similarity matrix.
    gap : int
        minimum index distance to consider (typically cfg.pair_min_gap).
    """
    n = S.shape[0]
    lr = np.zeros(n)
    for k in range(n):
        mask = np.abs(np.arange(n) - k) > gap
        lr[k] = float(S[k, mask].max()) if mask.any() else 0.0
    return lr


def _select_reference_novelty(novelty: np.ndarray, radii: list, ref_radius: int) -> np.ndarray:
    """Picks the novelty row whose radius is closest to `ref_radius`, to use
    as "the" 1-D novelty curve for a document when a single scale is needed
    (aggregates, flat-region detection, autocorrelation)."""
    closest = int(np.argmin([abs(r - ref_radius) for r in radii]))
    return novelty[closest]


def document_descriptors(X: np.ndarray, S: np.ndarray, novelty_ref: np.ndarray,
                         local_red: np.ndarray) -> dict:
    """Cheap, interpretable per-document summary statistics: one row of
    corpus.csv, and the raw material for the Overview page's "most
    discriminating descriptors" ranking (see discriminative_ranking()).

    Wraps infodynamics.scalogram.structure_descriptors (redundancy/dynamism)
    with two extra dashboard-specific descriptors that have no package
    equivalent: novelty variance and topic-shift "boundary rate".

    Parameters
    ----------
    X : np.ndarray of shape (n, n_features)
        this document's per-sentence feature matrix (embeddings or
        morphological features).
    S : np.ndarray of shape (n, n)
        self-similarity matrix.
    novelty_ref : np.ndarray of shape (n,)
        reference-scale Foote novelty (see _select_reference_novelty()).
    local_red : np.ndarray of shape (n,)
        per-sentence local redundancy (see local_redundancy()).
    """
    desc = structure_descriptors(X, S=S, window_size=5)
    desc["n_sentences"] = desc.pop("n_chunks")
    # a "peak" is a sentence more novel than both neighbours -- a topic-shift proxy.
    is_peak = (novelty_ref[1:-1] > novelty_ref[:-2]) & (novelty_ref[1:-1] > novelty_ref[2:])
    desc["novelty_var"] = float(np.var(novelty_ref))
    desc["mean_local_red"] = float(local_red.mean())
    desc["boundary_rate"] = float(int(is_peak.sum()) / max(1, X.shape[0]) * 100)
    return desc


def analyze_document(X: np.ndarray, scales: Sequence[int], radii: Sequence[int],
                     ref_radius: int, pair_min_gap: int) -> DocAnalysis:
    """Computes the self-similarity matrix, scalogram, multi-scale Foote
    novelty, and scalar descriptors for one document's per-sentence feature
    matrix. Signal-agnostic: called once for embeddings and, if morphology is
    enabled, again for morphological features -- same math either way, via
    infodynamics.scalogram.

    Parameters
    ----------
    X : np.ndarray of shape (n, n_features)
        this document's per-sentence feature matrix.
    scales, radii, ref_radius, pair_min_gap : see PipelineConfig.
    """
    S = self_similarity_matrix(X)
    scal_model = Scalogram(scales=scales).fit(X)
    foote_model = FooteNovelty(radii=radii).fit(X)
    novelty_ref = _select_reference_novelty(foote_model.novelty_, foote_model.radii_, ref_radius)
    lr = local_redundancy(S, pair_min_gap)
    desc = document_descriptors(X, S, novelty_ref, lr)
    return DocAnalysis(ssm=S, scalogram=scal_model.matrix_, scales=scal_model.scales_,
                       novelty=foote_model.novelty_, radii=foote_model.radii_,
                       novelty_ref=novelty_ref, local_redundancy=lr, descriptors=desc)


# --------------------------------------------------------------------------- #
# candidate feeds (redundant pairs / flat regions)
# --------------------------------------------------------------------------- #
def extract_redundant_pairs(doc, S: np.ndarray, cfg: PipelineConfig) -> list:
    """Candidate near-duplicate sentence pairs within one document: any pair
    at least `cfg.pair_min_gap` sentences apart with cosine similarity at or
    above `cfg.pair_sim_thresh`, capped at `cfg.pair_top_k` (highest
    similarity first). Feeds the app's "Redundancy" candidate feed.
    """
    n = S.shape[0]
    candidates = []
    for i in range(n):
        for j in range(i + cfg.pair_min_gap + 1, n):
            sim = float(S[i, j])
            if sim >= cfg.pair_sim_thresh:
                candidates.append((sim, i, j))
    candidates.sort(reverse=True)

    return [
        dict(doc_id=doc.doc_id, author=doc.author, i=i, j=j, sim=round(sim, 4),
            text_i=doc.sentences[i], text_j=doc.sentences[j])
        for sim, i, j in candidates[:cfg.pair_top_k]
    ]


def _region_dict(doc, run: tuple, local_red: np.ndarray) -> dict:
    """Builds one flat_regions.json record for a closed run [start, end]."""
    start, end = run
    return dict(doc_id=doc.doc_id, author=doc.author, start=start, end=end,
               length=end - start + 1,
               mean_local_red=round(float(local_red[start:end + 1].mean()), 4))


def extract_flat_regions(doc, novelty_ref: np.ndarray, local_red: np.ndarray,
                         cfg: PipelineConfig) -> list:
    """Candidate low-novelty stretches: runs of at least `cfg.flat_min_len`
    consecutive sentences all at or below the document's `cfg.flat_quantile`
    novelty quantile. Feeds the app's "Flatness" candidate feed.
    """
    threshold = np.quantile(novelty_ref, cfg.flat_quantile)
    regions, run = [], None

    for k, v in enumerate(novelty_ref):
        if v <= threshold:
            run = (run[0], k) if run else (k, k)
            continue
        if run and run[1] - run[0] + 1 >= cfg.flat_min_len:
            regions.append(_region_dict(doc, run, local_red))
        run = None
    if run and run[1] - run[0] + 1 >= cfg.flat_min_len:  # flush a run open at doc end
        regions.append(_region_dict(doc, run, local_red))

    return regions


# --------------------------------------------------------------------------- #
# per-document cache artifacts
# --------------------------------------------------------------------------- #
def write_document_cache(cache_dir: Path, doc, analysis: DocAnalysis) -> None:
    """Persists one document's per-sentence artifacts under `cache_dir`.

    These are read directly by dashboard/bench_core.py's Bench.ssm() /
    .curves() / .sentences() / .emb() -- the array/key names and shapes here
    ARE the cache contract (see this module's docstring).
    """
    np.save(cache_dir / "ssm" / f"{doc.doc_id}.npy", analysis.ssm.astype(np.float32))
    np.save(cache_dir / "emb" / f"{doc.doc_id}.npy", doc.embeddings)
    np.savez(
        cache_dir / "curves" / f"{doc.doc_id}.npz",
        scalogram=analysis.scalogram.astype(np.float32),
        novelty=analysis.novelty.astype(np.float32),
        nov1=analysis.novelty_ref.astype(np.float32),
        local_red=analysis.local_redundancy.astype(np.float32),
        scales=np.array(analysis.scales),
        radii=np.array(analysis.radii),
    )
    sentences_path = cache_dir / "sentences" / f"{doc.doc_id}.json"
    with open(sentences_path, "w") as f:
        json.dump([{"idx": i, "text": s} for i, s in enumerate(doc.sentences)],
                  f, ensure_ascii=False)


def write_morph_document_cache(cache_dir: Path, doc, analysis: DocAnalysis, feature_group: str) -> None:
    """Persists one document's morphology-signal artifacts for one feature
    group under `cache_dir`.

    Parallel to write_document_cache(), namespaced under morph_*/<feature_group>
    so every group -- and both signals -- coexist in the same cache without
    collisions. No morph_sentences/ is needed -- cache/sentences/<doc_id>.json
    (written by write_document_cache()) already covers both signals, since
    they encode the same sentence list. cache/morph_features/<feature_group>/<doc_id>.npy
    is the RAW per-sentence feature matrix for that group (e.g. pos_prop_VERB
    per sentence), read directly by dashboard/bench_core.py's
    Bench.morph_features() for inspection in the app -- not just the derived
    ssm/scalogram/novelty signals.
    """
    np.save(cache_dir / "morph_ssm" / feature_group / f"{doc.doc_id}.npy", analysis.ssm.astype(np.float32))
    np.save(cache_dir / "morph_features" / feature_group / f"{doc.doc_id}.npy", doc.morph_features[feature_group])
    np.savez(
        cache_dir / "morph_curves" / feature_group / f"{doc.doc_id}.npz",
        scalogram=analysis.scalogram.astype(np.float32),
        novelty=analysis.novelty.astype(np.float32),
        nov1=analysis.novelty_ref.astype(np.float32),
        local_red=analysis.local_redundancy.astype(np.float32),
        scales=np.array(analysis.scales),
        radii=np.array(analysis.radii),
    )


# --------------------------------------------------------------------------- #
# corpus-level aggregates
# --------------------------------------------------------------------------- #
def pca2(M: np.ndarray) -> np.ndarray:
    """Z-scores each column, then projects onto the top-2 principal
    components. Used for the Overview page's document scatter map."""
    Z = (M - M.mean(0)) / (M.std(0) + 1e-9)
    U, singular_values, _ = np.linalg.svd(Z, full_matrices=False)
    return U[:, :2] * singular_values[:2]


def add_document_map(corpus: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """Adds a 2-D PCA projection of the structure descriptors (`mds_x`,
    `mds_y`), used for the Overview page's document scatter map."""
    coords = pca2(corpus[feature_cols].to_numpy())
    corpus = corpus.copy()
    corpus["mds_x"], corpus["mds_y"] = coords[:, 0], coords[:, 1]
    return corpus


def cohens_d(a, b) -> float:
    """Standardized mean difference (pooled sd) between two 1-D samples."""
    a, b = np.asarray(a), np.asarray(b)
    na, nb = len(a), len(b)
    pooled_sd = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1))
                        / max(1, na + nb - 2))
    return float((a.mean() - b.mean()) / (pooled_sd + 1e-12))


def auc(a, b) -> float:
    """Probability that a random draw from `a` exceeds a random draw from
    `b` (rank-based / Mann-Whitney U, normalized to [0, 1])."""
    a, b = np.asarray(a), np.asarray(b)
    ranks = np.concatenate([a, b]).argsort().argsort() + 1
    rank_sum_a = ranks[:len(a)].sum()
    return float((rank_sum_a - len(a) * (len(a) + 1) / 2) / (len(a) * len(b)))


def discriminative_ranking(corpus: pd.DataFrame, feature_cols: list) -> list:
    """Ranks descriptor columns by how well they separate 'ai' from 'human'
    documents (|Cohen's d|), for the Overview page's headline table."""
    ai = corpus[corpus.author == "ai"]
    human = corpus[corpus.author == "human"]
    rows = [
        {"feature": c, "cohens_d": round(cohens_d(ai[c], human[c]), 3),
         "auc": round(auc(ai[c], human[c]), 3),
         "ai_mean": round(float(ai[c].mean()), 4),
         "human_mean": round(float(human[c].mean()), 4)}
        for c in feature_cols
    ]
    rows.sort(key=lambda r: -abs(r["cohens_d"]))
    return rows


def _signal_aggregates(docs: list, analyses: list, scales: Sequence[int]) -> dict:
    """Per-author mean novelty profile, per-scale energy, and novelty
    autocorrelation ("rhythm") for one signal. Shared by
    build_corpus_aggregates() for both the embedding and (if enabled)
    morphology signals -- same aggregation, different `analyses`.

    Parameters
    ----------
    docs : list[DocRecord]
    analyses : list[DocAnalysis]
        must be the same length as `docs`, in the same order.
    scales : Sequence[int]
        the full requested scale list (cfg.scales) -- short documents drop
        the largest scales (see Scalogram), so per-doc entries missing a
        scale are left as NaN and skipped by nanmean below.
    """
    ref_profiles: dict = {}
    scale_energy: dict = {}
    autocorr: dict = {}

    for doc, analysis in zip(docs, analyses):
        nov1 = analysis.novelty_ref

        # resample every novelty curve to a common length (100 points) so
        # documents of different lengths can be averaged/overlaid per author.
        resampled = np.interp(np.linspace(0, 1, 100), np.linspace(0, 1, len(nov1)), nov1)
        ref_profiles.setdefault(doc.author, []).append(resampled)

        se = np.full(len(scales), np.nan)
        scale_position = {w: i for i, w in enumerate(scales)}
        for wi, w in enumerate(analysis.scales):
            se[scale_position[w]] = analysis.scalogram[wi].var()
        scale_energy.setdefault(doc.author, []).append(se)

        # novelty autocorrelation: a periodicity peak at a fixed lag reads as
        # mechanical/templated rhythm (see dashboard/app.py's caption).
        centered = nov1 - nov1.mean()
        ac = np.correlate(centered, centered, "full")
        ac = ac[ac.size // 2:][:31]
        ac = ac / ac[0] if ac[0] else ac
        autocorr.setdefault(doc.author, []).append(np.pad(ac, (0, 31 - len(ac))))

    return {
        "ref_profile": {a: {"mean": np.mean(v, 0).tolist(), "std": np.std(v, 0).tolist()}
                       for a, v in ref_profiles.items()},
        "scale_energy": {a: {"scales": list(scales), "mean": np.nanmean(v, 0).tolist()}
                        for a, v in scale_energy.items()},
        "autocorr": {a: np.mean(v, 0).tolist() for a, v in autocorr.items()},
    }


def build_corpus_aggregates(docs: list, analyses: list, corpus: pd.DataFrame,
                            cfg: PipelineConfig, morph_analyses: Optional[dict] = None) -> dict:
    """Corpus-level summaries for the Overview / Author-signature dashboard
    pages: per-author mean novelty profile, per-scale energy, novelty
    autocorrelation ("rhythm"), and which descriptors most separate ai vs.
    human writing -- for the embedding signal, and again (nested under a
    "morphology" key, one entry per feature group) for the morphology signal
    if enabled.

    Parameters
    ----------
    docs : list[DocRecord]
    analyses : list[DocAnalysis]
        embedding-signal analyses, same length/order as `docs`.
    corpus : pd.DataFrame
        one row per document, with DESCRIPTOR_FEATURE_COLUMNS (and
        morph_descriptor_columns(...) if morphology is enabled) already
        computed (see document_descriptors()).
    cfg : PipelineConfig
    morph_analyses : dict[str, list[DocAnalysis]] or None, default=None
        one entry per feature group, each a list of morphology-signal
        analyses (same length/order as `docs`). None (the default) means
        morphology is disabled: no "morphology" key is added, and its
        descriptor columns are excluded from the discriminator ranking.
    """
    aggregates = _signal_aggregates(docs, analyses, cfg.scales)

    discriminator_cols = DESCRIPTOR_FEATURE_COLUMNS + ["dist_mean_w5", "n_sentences"]
    if morph_analyses is not None:
        aggregates["morphology"] = {
            group: _signal_aggregates(docs, group_analyses, cfg.scales)
            for group, group_analyses in morph_analyses.items()
        }
        discriminator_cols = discriminator_cols + morph_descriptor_columns(list(morph_analyses))

    aggregates["discriminative"] = discriminative_ranking(corpus, discriminator_cols)
    return aggregates


def build_human_index(docs: list, analyses: list) -> tuple:
    """Flat per-sentence index of every human-authored sentence's embedding.

    Used by dashboard/bench_core.py's Bench.suggest_contrast() to
    nearest-neighbour search for a low-redundancy human sentence to contrast
    against a weak agent passage in the Evidence-bench page.

    Returns
    -------
    vectors : np.ndarray of shape (n_human_sentences, dim), float32
    meta : list[dict]
        one entry per row of `vectors`, in the same order: {doc_id, idx,
        text, local_red}.
    """
    vectors, meta = [], []
    for doc, analysis in zip(docs, analyses):
        if doc.author != "human":
            continue
        for k, sentence in enumerate(doc.sentences):
            vectors.append(doc.embeddings[k])
            meta.append({
                "doc_id": doc.doc_id, "idx": k, "text": sentence,
                "local_red": round(float(analysis.local_redundancy[k]), 4),
            })
    return np.array(vectors, dtype=np.float32), meta


# --------------------------------------------------------------------------- #
# corpus-level cache artifacts
# --------------------------------------------------------------------------- #
def write_corpus_cache(cfg: PipelineConfig, corpus: pd.DataFrame, pairs: list,
                       flat_regions: list, aggregates: dict, human_vectors: np.ndarray,
                       human_meta: list, n_docs: int, n_sentences: int, emb_dim: int,
                       morphology_feature_names: Optional[dict] = None) -> dict:
    """Writes every corpus-level artifact (as opposed to the per-document
    artifacts written by write_document_cache()/write_morph_document_cache()).

    `morphology_feature_names` (dict of {feature_group: column_names}, fixed
    for the whole corpus since every group is encoded in one shared call --
    see encode_all_feature_groups()) is written into config.json only if
    morphology is enabled, alongside "morphology_feature_groups" (its keys);
    dashboard/bench_core.py's Bench.morphology_available() checks for the
    latter's presence, and Bench.morph_features() uses the former to label
    the raw per-sentence feature table for a given group.

    Returns the config dict just written, so run_pipeline() can pass the
    exact same object into write_manifest() (config_hash is computed over
    this, not a re-derived copy).
    """
    cache = cfg.cache_dir
    corpus.to_csv(cache / "corpus.csv", index=False)
    json.dump(pairs, open(cache / "redundant_pairs.json", "w"), ensure_ascii=False)
    json.dump(flat_regions, open(cache / "flat_regions.json", "w"), ensure_ascii=False)
    json.dump(aggregates, open(cache / "aggregates.json", "w"), ensure_ascii=False)
    np.save(cache / "human_index.npy", human_vectors)
    json.dump(human_meta, open(cache / "human_index_meta.json", "w"), ensure_ascii=False)
    config = {**cfg.to_json_dict(), "n_docs": n_docs, "n_sentences": n_sentences,
             "emb_dim": emb_dim}
    if morphology_feature_names is not None:
        config["morphology_feature_groups"] = list(morphology_feature_names)
        config["morphology_feature_names"] = morphology_feature_names
    json.dump(config, open(cache / "config.json", "w"), ensure_ascii=False, indent=2)
    return config


def write_manifest(cfg: PipelineConfig, config: dict) -> None:
    """Writes cache/manifest.json: provenance for a shipped cache bundle --
    file checksums, a normalized config hash, corpus hash, and model
    identities -- so infodynamics-pack/-pull/-verify (infodynamics/shipping.py)
    can confirm a bundle is complete and byte-identical after a round trip.
    The hashing/normalization rules live in infodynamics.cache_contract,
    shared with those commands so builder and checker never disagree.

    Must run after write_corpus_cache() (and every other cache write): `files`
    is a checksum walk of cache_dir taken at call time.
    """
    models = {
        "embedding": {
            "name": cfg.model_name,
            "revision": cache_contract.resolve_hf_revision(cfg.model_name),
        },
    }
    if cfg.morphology_enabled and cfg.morphology_model_path:
        models["morphology_udpipe"] = {
            "path": cfg.morphology_model_path,
            "sha256": cache_contract.sha256_file(Path(cfg.morphology_model_path)),
        }
    manifest = cache_contract.build_manifest(
        pipeline_version=PIPELINE_VERSION,
        cache_dir=cfg.cache_dir,
        corpus_path=cfg.csv_path,
        config=config,
        n_docs=config["n_docs"],
        n_sentences=config["n_sentences"],
        models=models,
        repo_dir=REPO_ROOT,
    )
    json.dump(manifest, open(cfg.cache_dir / "manifest.json", "w"), ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #
def run_pipeline(cfg: PipelineConfig) -> None:
    """Runs the full precompute pipeline end to end and writes dashboard/cache/.

    This is the function to call directly (e.g. from a notebook or a test) if
    you want to (re)build the cache without going through the CLI --
    `main()` is a thin argparse wrapper around it.
    """
    cache = cfg.cache_dir
    subdirs = ["sentences", "ssm", "curves", "emb"]
    morphology_enabled = cfg.morphology_enabled
    if morphology_enabled:
        for sub in ("morph_ssm", "morph_curves", "morph_features"):
            for group in MorphologicalEncoder.FEATURE_GROUPS:
                subdirs.append(f"{sub}/{group}")
    for sub in subdirs:
        (cache / sub).mkdir(parents=True, exist_ok=True)

    print(f"Loading corpus from {cfg.csv_path} (authors={list(cfg.authors)})...")
    df = load_corpus(cfg)
    docs, flat_sentences = segment_corpus(df, cfg)
    print(f"{len(docs)} docs, {len(flat_sentences)} sentences.")

    encoder = Encoder(cfg.model_name, device=cfg.device, batch_size=cfg.batch_size, normalize=True)
    embeddings = encode_corpus(encoder, flat_sentences, f"'{cfg.model_name}'")
    assign_features(docs, embeddings, attr="embeddings")

    morph_feature_names = None
    if morphology_enabled:
        print(f"Encoding {len(flat_sentences)} sentences with morphology "
              f"(all {len(MorphologicalEncoder.FEATURE_GROUPS)} groups, one shared parse)...")
        morph_by_group = encode_all_feature_groups(
            flat_sentences, lang=cfg.morphology_lang, model_path=cfg.morphology_model_path)
        morph_feature_names = {group: names for group, (_, names) in morph_by_group.items()}
        for group, (matrix, _) in morph_by_group.items():
            offset = 0
            for doc in docs:
                n = len(doc.sentences)
                doc.morph_features[group] = matrix[offset:offset + n]
                offset += n

    corpus_rows, all_pairs, all_flat, analyses = [], [], [], []
    morph_analyses = {group: [] for group in MorphologicalEncoder.FEATURE_GROUPS} if morphology_enabled else None
    for doc in docs:
        analysis = analyze_document(doc.embeddings, cfg.scales, cfg.radii, cfg.ref_radius, cfg.pair_min_gap)
        analyses.append(analysis)
        write_document_cache(cache, doc, analysis)

        row = {
            "doc_id": doc.doc_id, "file_name": doc.file_name, "author": doc.author,
            "project": doc.project, "subproject": doc.subproject, **analysis.descriptors,
        }
        if morphology_enabled:
            for group in MorphologicalEncoder.FEATURE_GROUPS:
                morph_analysis = analyze_document(
                    doc.morph_features[group], cfg.scales, cfg.radii, cfg.ref_radius, cfg.pair_min_gap)
                morph_analyses[group].append(morph_analysis)
                write_morph_document_cache(cache, doc, morph_analysis, group)
                row.update({f"morph_{group}_{k}": v for k, v in morph_analysis.descriptors.items()
                           if k != "n_sentences"})

        all_pairs += extract_redundant_pairs(doc, analysis.ssm, cfg)
        all_flat += extract_flat_regions(doc, analysis.novelty_ref,
                                         analysis.local_redundancy, cfg)
        corpus_rows.append(row)
        print(f"  ok  {doc.file_name}  ({analysis.descriptors['n_sentences']} sentences)")

    corpus = pd.DataFrame(corpus_rows)
    corpus = add_document_map(corpus, DESCRIPTOR_FEATURE_COLUMNS)
    aggregates = build_corpus_aggregates(
        docs, analyses, corpus, cfg, morph_analyses=morph_analyses)
    human_vectors, human_meta = build_human_index(docs, analyses)

    config = write_corpus_cache(
        cfg, corpus, all_pairs, all_flat, aggregates, human_vectors, human_meta,
        n_docs=len(docs), n_sentences=len(flat_sentences), emb_dim=int(embeddings.shape[1]),
        morphology_feature_names=morph_feature_names,
    )
    write_manifest(cfg, config)

    print(f"\ncache -> {cache}")
    print(f"  docs={len(docs)}  pairs={len(all_pairs)}  flat={len(all_flat)}  "
          f"human_sents={len(human_vectors)}")
    if morphology_enabled:
        counts = ", ".join(f"{g}={len(n)}" for g, n in morph_feature_names.items())
        print(f"  morphology groups: {counts}")
    print("top discriminators:",
         [(d["feature"], d["cohens_d"]) for d in aggregates["discriminative"][:4]])


def main() -> None:
    cfg = parse_args()
    run_pipeline(cfg)


if __name__ == "__main__":
    main()

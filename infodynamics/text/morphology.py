"""
Parses text chunks with a local UDPipe model and extracts morphological /
syntactic features (via textdescriptives) as a numeric matrix.
"""
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from typing_extensions import Self

_PIPELINE_CACHE: Dict[Tuple[str, str, Optional[str]], "object"] = {}

# textdescriptives/quality's own default config passes list-typed values
# (e.g. [2, 4]) where its component schema declares Tuple[int, int],
# which spaCy's confection config resolver rejects outright. Passing the
# same values as tuples explicitly works around it.
_QUALITY_PIPE_CONFIG = {"top_ngram_range": (2, 4), "duplicate_n_gram_fraction_range": (5, 10)}


def _add_feature_group_pipe(nlp, feature_group: str) -> None:
    config = _QUALITY_PIPE_CONFIG if feature_group == "quality" else {}
    nlp.add_pipe(f"textdescriptives/{feature_group}", config=config)


def _clean_feature_df(df):
    """Keeps numeric/bool columns and fills NaN with 0.0.

    Some textdescriptives metrics are only defined above a length threshold
    -- e.g. readability's `smog` needs a handful of sentences to compute a
    variance term, and is NaN below that -- which is routine at
    sentence-level granularity. Downstream code (cosine similarity, PCA)
    requires finite values, and 0.0 ("no signal") is a reasonable neutral
    default for an undefined formula.
    """
    return df.select_dtypes(include=["number", "bool"]).fillna(0.0)


def _load_pipeline(lang: str, feature_group: str, model_path: Optional[str] = None):
    try:
        import spacy_udpipe
    except ImportError as e:
        raise ImportError(
            "The 'morphology' extra is required to use MorphologicalEncoder. "
            "Install it with `pip install infodynamics[morphology]`."
        ) from e
    try:
        import textdescriptives  # noqa: F401  (registers the textdescriptives/* spaCy factories)
    except ImportError as e:
        raise ImportError(
            "The 'morphology' extra is required to use MorphologicalEncoder. "
            "Install it with `pip install infodynamics[morphology]`."
        ) from e

    key = (lang, feature_group, model_path)
    if key not in _PIPELINE_CACHE:
        nlp = _load_udpipe(lang, model_path)
        if feature_group == "pos_proportions":
            # UDPipe's POS tagging happens inside spacy_udpipe's custom tokenizer, not as a
            # separate pipe component, so nlp.pipe_names is empty. pos_proportions unconditionally
            # requires a 'tagger' or 'attribute_ruler' in pipe_names before it can be added, even
            # though the tokens are already tagged -- a no-op attribute_ruler satisfies that check.
            nlp.add_pipe("attribute_ruler")
        _add_feature_group_pipe(nlp, feature_group)
        _PIPELINE_CACHE[key] = nlp
    return _PIPELINE_CACHE[key]


def _load_udpipe(lang: str, model_path: Optional[str] = None):
    """Loads a bare spacy_udpipe pipeline (no textdescriptives components
    yet), downloading the model on first use if no local path is given.
    Shared by _load_pipeline (single feature group) and
    encode_all_feature_groups (all groups, one shared parse)."""
    import spacy_udpipe

    if model_path is not None:
        return spacy_udpipe.load_from_path(lang=lang, path=model_path)
    try:
        return spacy_udpipe.load(lang)
    except Exception:
        spacy_udpipe.download(lang)
        return spacy_udpipe.load(lang)


def encode_all_feature_groups(
    texts: List[str],
    feature_groups: Sequence[str] = (),
    lang: str = "cs",
    model_path: Optional[str] = None,
    nlp: Optional[object] = None,
) -> Dict[str, Tuple[np.ndarray, List[str]]]:
    """Parses `texts` once and extracts every group in `feature_groups`,
    returning `{feature_group: (matrix, feature_names)}`.

    Far cheaper than building one MorphologicalEncoder per group when
    multiple groups are needed for the same texts: UDPipe dependency
    parsing is the expensive step and runs only once here, with every
    group's textdescriptives pipe added to the same spaCy pipeline and
    extracted from the same parsed docs (extract_df can be called once per
    group on an already-parsed doc list -- it doesn't reparse).

    Parameters
    ----------
    texts : List[str]
    feature_groups : Sequence[str], default=MorphologicalEncoder.FEATURE_GROUPS
        which textdescriptives groups to extract.
    lang, model_path : see MorphologicalEncoder.
    nlp : spaCy Language or None, default=None
        pre-built pipeline to use instead of loading one via spacy_udpipe.
        Mainly an escape hatch for tests; must already have every
        `textdescriptives/{group}` in `feature_groups` added.
    """
    try:
        import textdescriptives  # noqa: F401  (registers the textdescriptives/* spaCy factories)
    except ImportError as e:
        raise ImportError(
            "The 'morphology' extra is required to use MorphologicalEncoder. "
            "Install it with `pip install infodynamics[morphology]`."
        ) from e
    from textdescriptives import extract_df

    feature_groups = tuple(feature_groups) or MorphologicalEncoder.FEATURE_GROUPS
    for g in feature_groups:
        if g not in MorphologicalEncoder.FEATURE_GROUPS:
            raise ValueError(f"'feature_groups' must be a subset of {MorphologicalEncoder.FEATURE_GROUPS}, got {g!r}.")

    if nlp is None:
        try:
            import spacy_udpipe  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "The 'morphology' extra is required to use MorphologicalEncoder. "
                "Install it with `pip install infodynamics[morphology]`."
            ) from e
        nlp = _load_udpipe(lang, model_path)
        if "pos_proportions" in feature_groups:
            nlp.add_pipe("attribute_ruler")
        for group in feature_groups:
            _add_feature_group_pipe(nlp, group)

    docs = list(nlp.pipe(texts))

    result: Dict[str, Tuple[np.ndarray, List[str]]] = {}
    for group in feature_groups:
        df = _clean_feature_df(extract_df(docs, metrics=[group], include_text=False))
        result[group] = (df.to_numpy(dtype=float), list(df.columns))
    return result


class MorphologicalEncoder(BaseEstimator, TransformerMixin):
    """Parses text chunks with a local UDPipe model and extracts one
    textdescriptives feature group as a numeric matrix."""

    FEATURE_GROUPS = ("pos_proportions", "dependency_distance", "descriptive_stats", "readability", "quality")

    def __init__(
        self,
        feature_group: str,
        lang: str = "cs",
        model_path: Optional[str] = None,
        nlp: Optional[object] = None,
    ):
        """

        Parameters
        ----------
        feature_group : {'pos_proportions', 'dependency_distance', 'descriptive_stats', 'readability', 'quality'}
            the textdescriptives feature group to extract.

        lang : str, default='cs'
            UDPipe language code to parse texts with (see spacy_udpipe.languages_ids for options).

        model_path : str or None, default=None
            path to a local UDPipe model file, loaded via spacy_udpipe.load_from_path instead of
            spacy_udpipe.download/load. Useful for offline use or a model fetched from a mirror.

        nlp : spaCy Language or None, default=None
            pre-built pipeline to use instead of loading one via spacy_udpipe. Mainly an
            escape hatch for tests; must already have `textdescriptives/{feature_group}` added.
        """
        if feature_group not in self.FEATURE_GROUPS:
            raise ValueError(f"'feature_group' must be one of {self.FEATURE_GROUPS}, got {feature_group!r}.")
        self.feature_group = feature_group
        self.lang = lang
        self.model_path = model_path
        self.nlp = nlp

    def fit(self, texts: List[str], y=None) -> Self:
        return self

    def transform(self, texts: List[str], y=None) -> np.ndarray:
        return self.encode(texts)

    def encode(self, texts: List[str]) -> np.ndarray:
        from textdescriptives import extract_df

        nlp = self.nlp if self.nlp is not None else _load_pipeline(self.lang, self.feature_group, self.model_path)
        docs = list(nlp.pipe(texts))

        df = _clean_feature_df(extract_df(docs, metrics=[self.feature_group], include_text=False))

        self.feature_names_ = list(df.columns)
        return df.to_numpy(dtype=float)

"""
Parses text chunks with a local UDPipe model and extracts morphological /
syntactic features (via textdescriptives) as a numeric matrix.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np

_PIPELINE_CACHE: Dict[Tuple[str, str, Optional[str]], "object"] = {}


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
        if model_path is not None:
            nlp = spacy_udpipe.load_from_path(lang=lang, path=model_path)
        else:
            try:
                nlp = spacy_udpipe.load(lang)
            except Exception:
                spacy_udpipe.download(lang)
                nlp = spacy_udpipe.load(lang)
        if feature_group == "pos_proportions":
            # UDPipe's POS tagging happens inside spacy_udpipe's custom tokenizer, not as a
            # separate pipe component, so nlp.pipe_names is empty. pos_proportions unconditionally
            # requires a 'tagger' or 'attribute_ruler' in pipe_names before it can be added, even
            # though the tokens are already tagged -- a no-op attribute_ruler satisfies that check.
            nlp.add_pipe("attribute_ruler")
        nlp.add_pipe(f"textdescriptives/{feature_group}")
        _PIPELINE_CACHE[key] = nlp
    return _PIPELINE_CACHE[key]


class MorphologicalEncoder:
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

    def encode(self, texts: List[str]) -> np.ndarray:
        from textdescriptives import extract_df

        nlp = self.nlp if self.nlp is not None else _load_pipeline(self.lang, self.feature_group, self.model_path)
        docs = list(nlp.pipe(texts))

        df = extract_df(docs, metrics=[self.feature_group], include_text=False)
        df = df.select_dtypes(include=["number", "bool"])

        self.feature_names_ = list(df.columns)
        return df.to_numpy(dtype=float)

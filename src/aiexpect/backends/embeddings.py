"""Tier 2: semantic similarity without an API key.

If ``sentence-transformers`` is installed we use a small local model
(all-MiniLM-L6-v2, ~80 MB, CPU is fine). Otherwise we fall back to a purely
lexical similarity so ``pip install aiexpect`` works with zero extra
dependencies. The fallback is honest about being lexical: it reports its own
default threshold and the report labels which backend produced each score.
"""
from __future__ import annotations

import math
import re
import warnings
from collections import Counter
from typing import List, Optional

from ..config import settings

_STOPWORDS = set(
    ["a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to", "in", "on", "at", "by", "for", "with", "from", "as", "is", "are", "was", "were", "be", "been", "being", "it", "its", "this", "that", "these", "those", "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them", "my", "your", "our", "their", "do", "does", "did", "doing", "have", "has", "had", "having", "can", "could", "will", "would", "should", "may", "might", "must", "not", "no", "nor", "so", "than", "too", "very", "just", "about", "into", "over", "under", "again", "further", "there", "here", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "only", "own", "same", "s", "t", "don", "now"]
)

_WORD_RE = re.compile(r"[a-z0-9']+")


def _tokens(text: str) -> List[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS]


def _stem(w: str) -> str:
    # A deliberately tiny stemmer: enough to match refund/refunds/refunded.
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b.get(k, 0) for k in a)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


class LexicalBackend:
    """Zero-dependency fallback: blend of stemmed-word cosine and character 3-gram cosine."""

    name = "lexical"
    default_threshold = 0.45            # for to_mean / to_be_similar_to
    default_relevance_threshold = 0.15  # question vs answer share far fewer words than two answers

    def similarity(self, a: str, b: str) -> float:
        wa = Counter(_stem(t) for t in _tokens(a))
        wb = Counter(_stem(t) for t in _tokens(b))
        word_sim = _cosine(wa, wb)
        ca = Counter(_grams(a))
        cb = Counter(_grams(b))
        char_sim = _cosine(ca, cb)
        return round(0.6 * word_sim + 0.4 * char_sim, 4)


def _grams(text: str, n: int = 3) -> List[str]:
    s = re.sub(r"\s+", " ", text.lower()).strip()
    return [s[i : i + n] for i in range(max(0, len(s) - n + 1))]


class SentenceTransformerBackend:
    name = "sentence-transformers"
    default_threshold = 0.65
    default_relevance_threshold = 0.4

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.name = f"sentence-transformers:{model_name}"

    def similarity(self, a: str, b: str) -> float:
        embs = self._model.encode([a, b], normalize_embeddings=True)
        return round(float((embs[0] * embs[1]).sum()), 4)


_backend = None
_warned = False


def reset() -> None:
    global _backend
    _backend = None


def get_backend():
    """Return the configured embeddings backend, creating it on first use."""
    global _backend, _warned
    if _backend is not None:
        return _backend

    choice = settings.embeddings
    if choice == "lexical":
        _backend = LexicalBackend()
        return _backend

    model_name = "all-MiniLM-L6-v2" if choice == "auto" else choice
    try:
        _backend = SentenceTransformerBackend(model_name)
    except ImportError:
        if choice != "auto":
            raise
        if not _warned:
            warnings.warn(
                "aiexpect: sentence-transformers is not installed, using the lexical "
                "similarity fallback. For real semantic matching run: "
                "pip install 'aiexpect[embeddings]'",
                stacklevel=2,
            )
            _warned = True
        _backend = LexicalBackend()
    return _backend


def similarity(a: str, b: str) -> float:
    return get_backend().similarity(a, b)


def threshold(override: Optional[float] = None, kind: str = "similarity") -> float:
    if override is not None:
        return override
    if settings.similarity_threshold is not None:
        return settings.similarity_threshold
    b = get_backend()
    return b.default_relevance_threshold if kind == "relevance" else b.default_threshold

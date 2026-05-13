"""Immutable data models for korean-nlp-core public API.

Every model is declared with ``@dataclass(frozen=True, slots=True)`` so that
instances are hashable, immutable, and memory-efficient. This is a hard
invariant for the SDK — see ``.docs/agent-prompt.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "DictCheckResult",
    "GraphQueryResult",
    "HybridQueryResult",
    "JamoComponents",
    "LexicalQueryResult",
    "MorphToken",
    "PIIPattern",
    "QueryResult",
    "SemanticQueryResult",
]


@dataclass(frozen=True, slots=True)
class MorphToken:
    """A single morpheme produced by :class:`MeCabTokenizer.analyze`.

    Attributes:
        surface: Surface form as it appears in the original text.
        lemma: Dictionary/base form.
        pos: Sejong-style part-of-speech tag.
        start: Inclusive start offset in the original input.
        end: Exclusive end offset in the original input.
    """

    surface: str
    lemma: str
    pos: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class JamoComponents:
    """Decomposed components of a single Hangul syllable.

    ``jongseong`` is the empty string when the syllable has no final consonant.
    """

    choseong: str
    jungseong: str
    jongseong: str


@dataclass(frozen=True, slots=True)
class DictCheckResult:
    """Result of probing the MeCab dictionary availability.

    Attributes:
        available: ``True`` when MeCab can be initialized successfully.
        dict_path: Filesystem path of the active dictionary, when known.
        version: Reported dictionary version, when known.
        error: Human-readable error message when ``available`` is ``False``.
    """

    available: bool
    dict_path: str | None
    version: str | None
    error: str | None


@dataclass(frozen=True, slots=True)
class PIIPattern:
    """A named regex describing a single class of PII.

    This SDK only owns the *data*; runtime masking is the consumer's job.
    """

    name: str
    description: str
    pattern: re.Pattern[str]


@dataclass(frozen=True, slots=True)
class LexicalQueryResult:
    """Output of :class:`QueryTarget.LEXICAL`.

    Attributes:
        keywords: Tokens remaining after stopword removal.
        query: Space-joined string of ``keywords``, suitable for BM25.
    """

    keywords: tuple[str, ...]
    query: str


@dataclass(frozen=True, slots=True)
class SemanticQueryResult:
    """Output of :class:`QueryTarget.SEMANTIC`.

    Preserves the natural-language form for downstream embedding models.
    """

    query: str


@dataclass(frozen=True, slots=True)
class GraphQueryResult:
    """Output of :class:`QueryTarget.GRAPH`.

    Attributes:
        seed_nodes: Noun / entity seed labels for graph traversal.
    """

    seed_nodes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HybridQueryResult:
    """Output of :class:`QueryTarget.HYBRID` — bundles all three results."""

    lexical: LexicalQueryResult
    semantic: SemanticQueryResult
    graph: GraphQueryResult


type QueryResult = LexicalQueryResult | SemanticQueryResult | GraphQueryResult | HybridQueryResult

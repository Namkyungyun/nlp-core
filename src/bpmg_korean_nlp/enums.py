"""Enumerations for korean-nlp-core public API."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["CharType", "QueryTarget"]


class QueryTarget(StrEnum):
    """Target pipeline for :func:`bpmg_korean_nlp.analyze_query`."""

    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    GRAPH = "graph"
    HYBRID = "hybrid"


class CharType(StrEnum):
    """Classification of a single Unicode character by script/category."""

    HANGUL_SYLLABLE = "hangul_syllable"
    HANGUL_JAMO = "hangul_jamo"
    HANJA = "hanja"
    LATIN = "latin"
    NUMBER = "number"
    SYMBOL = "symbol"
    WHITESPACE = "whitespace"
    OTHER = "other"

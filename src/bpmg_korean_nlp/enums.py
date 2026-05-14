"""korean-nlp-core 공개 API 열거형."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["CharType", "QueryTarget"]


class QueryTarget(StrEnum):
    """``bpmg_korean_nlp.analyze_query``의 대상 파이프라인."""

    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    GRAPH = "graph"
    HYBRID = "hybrid"


class CharType(StrEnum):
    """단일 유니코드 문자의 스크립트/범주 분류."""

    HANGUL_SYLLABLE = "hangul_syllable"
    HANGUL_JAMO = "hangul_jamo"
    HANJA = "hanja"
    LATIN = "latin"
    NUMBER = "number"
    SYMBOL = "symbol"
    WHITESPACE = "whitespace"
    OTHER = "other"

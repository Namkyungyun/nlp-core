"""Public API for korean-nlp-core.

This module is the single public contract of the SDK (27 public symbols).
Consumers should import every name they need from ``bpmg_korean_nlp``
(not from submodules) so that internal layout can evolve without breaking
downstream code.
"""

from __future__ import annotations

from bpmg_korean_nlp.enums import CharType, QueryTarget
from bpmg_korean_nlp.exceptions import (
    InvalidInputError,
    KoreanNlpError,
    MeCabNotAvailableError,
    PIIDetectedError,
)
from bpmg_korean_nlp.jamo_utils import (
    classify_char,
    compose,
    decompose,
    extract_choseong,
)
from bpmg_korean_nlp.mecab_check import check_mecab_dict
from bpmg_korean_nlp.models import (
    DictCheckResult,
    GraphQueryResult,
    HybridQueryResult,
    JamoComponents,
    LexicalQueryResult,
    MorphToken,
    PIIPattern,
    QueryResult,
    SemanticQueryResult,
)
from bpmg_korean_nlp.normalizer import KoreanNormalizer
from bpmg_korean_nlp.pii import PII_PATTERNS
from bpmg_korean_nlp.query_analyzer import QueryAnalyzer, analyze_query
from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS, merge_stopwords
from bpmg_korean_nlp.tokenizer import MeCabTokenizer

__all__ = [
    "DEFAULT_STOPWORDS",
    "PII_PATTERNS",
    "CharType",
    "DictCheckResult",
    "GraphQueryResult",
    "HybridQueryResult",
    "InvalidInputError",
    "JamoComponents",
    "KoreanNlpError",
    "KoreanNormalizer",
    "LexicalQueryResult",
    "MeCabNotAvailableError",
    "MeCabTokenizer",
    "MorphToken",
    "PIIDetectedError",
    "PIIPattern",
    "QueryAnalyzer",
    "QueryResult",
    "QueryTarget",
    "SemanticQueryResult",
    "analyze_query",
    "check_mecab_dict",
    "classify_char",
    "compose",
    "decompose",
    "extract_choseong",
    "merge_stopwords",
]

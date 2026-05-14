"""korean-nlp-core 공개 API.

이 모듈은 SDK의 단일 공개 계약(27개 공개 심볼)입니다.
하위 모듈이 아닌 ``bpmg_korean_nlp``에서 필요한 모든 이름을 임포트해야
하위 코드의 변경 없이 내부 레이아웃을 발전시킬 수 있습니다.
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

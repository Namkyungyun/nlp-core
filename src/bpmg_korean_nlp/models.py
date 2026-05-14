"""korean-nlp-core 공개 API의 불변 데이터 모델.

모든 모델은 ``@dataclass(frozen=True, slots=True)``로 선언되어 인스턴스가
해시 가능하고 불변이며 메모리 효율적입니다. 이는 SDK의 핵심 불변 조건입니다 —
``.docs/agent-prompt.md`` 참조.
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
    """:class:`MeCabTokenizer.analyze`가 생성하는 단일 형태소.

    속성:
        surface: 원본 텍스트에서의 표층형.
        lemma: 사전형/기본형.
        pos: 세종 품사 태그.
        start: 원본 입력에서의 시작 오프셋(포함).
        end: 원본 입력에서의 종료 오프셋(제외).
    """

    surface: str
    lemma: str
    pos: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class JamoComponents:
    """단일 한글 음절의 분해된 구성 요소.

    종성이 없는 음절의 경우 ``jongseong``은 빈 문자열입니다.
    """

    choseong: str
    jungseong: str
    jongseong: str


@dataclass(frozen=True, slots=True)
class DictCheckResult:
    """MeCab 사전 가용성 확인 결과.

    속성:
        available: MeCab이 성공적으로 초기화되면 ``True``.
        dict_path: 활성 사전의 파일시스템 경로(알 수 있는 경우).
        version: 보고된 사전 버전(알 수 있는 경우).
        error: ``available``이 ``False``일 때의 사람이 읽을 수 있는 오류 메시지.
    """

    available: bool
    dict_path: str | None
    version: str | None
    error: str | None


@dataclass(frozen=True, slots=True)
class PIIPattern:
    """단일 PII 범주를 나타내는 이름 있는 정규식.

    이 SDK는 *데이터*만 소유하며, 런타임 마스킹은 소비자의 책임입니다.
    """

    name: str
    description: str
    pattern: re.Pattern[str]


@dataclass(frozen=True, slots=True)
class LexicalQueryResult:
    """:class:`QueryTarget.LEXICAL`의 출력.

    속성:
        keywords: 불용어 제거 후 남은 토큰.
        query: BM25에 적합한 ``keywords``를 공백으로 연결한 문자열.
    """

    keywords: tuple[str, ...]
    query: str


@dataclass(frozen=True, slots=True)
class SemanticQueryResult:
    """:class:`QueryTarget.SEMANTIC`의 출력.

    다운스트림 임베딩 모델을 위해 자연어 형식을 보존합니다.
    """

    query: str


@dataclass(frozen=True, slots=True)
class GraphQueryResult:
    """:class:`QueryTarget.GRAPH`의 출력.

    속성:
        seed_nodes: 그래프 탐색을 위한 명사/개체 시드 레이블.
    """

    seed_nodes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HybridQueryResult:
    """:class:`QueryTarget.HYBRID`의 출력 — 세 가지 결과를 모두 묶습니다."""

    lexical: LexicalQueryResult
    semantic: SemanticQueryResult
    graph: GraphQueryResult


type QueryResult = LexicalQueryResult | SemanticQueryResult | GraphQueryResult | HybridQueryResult

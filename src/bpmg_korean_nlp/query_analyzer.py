"""korean-nlp-core 쿼리 분석.

:class:`QueryAnalyzer`는 사용자의 자연어 쿼리를 네 가지 검색 대상 표현 중
하나로 변환하는 *순수 변환 계층*입니다:

* ``LEXICAL``   — 불용어가 제거된 BM25 준비 토큰.
* ``SEMANTIC``  — 자유 형식 텍스트를 소비하는 임베딩 모델을 위해 자연 문장을 그대로 보존.
* ``GRAPH``     — 시드 명사/개체 (세종 POS ``NNG`` / ``NNP``).
* ``HYBRID``    — 세 가지 결과를 모두 묶음; 동일한 정규화된 입력을 공유하므로
  세 파이프라인이 병렬로 실행됩니다.

BM25 스코어링, 벡터 조회, 그래프 탐색, 랭킹 등 실제 검색 단계는 모두
소비자의 책임입니다. 계약상 이 모듈은 ``retrieval_core``, ``guardrail_core``,
``chatbot_contracts``를 임포트하지 않으며 어떠한 종류의 스코어링도 수행하지 않습니다.

기본 싱글톤(:class:`KoreanNormalizer`, :class:`MeCabTokenizer`,
:data:`DEFAULT_STOPWORDS`)은 재사용되어 다운스트림 호출자가 프로세스당 최대 한 번만
사전 로드 비용을 지불합니다. 각 의존성은 테스트 또는 커스텀 배포를 위해
생성자를 통해 교체할 수 있습니다.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Final

from bpmg_korean_nlp.enums import QueryTarget
from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.models import (
    GraphQueryResult,
    HybridQueryResult,
    LexicalQueryResult,
    MorphToken,
    QueryResult,
    SemanticQueryResult,
)
from bpmg_korean_nlp.normalizer import KoreanNormalizer
from bpmg_korean_nlp.pii import check_pii
from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS
from bpmg_korean_nlp.tokenizer import MeCabTokenizer

__all__ = ["QueryAnalyzer", "analyze_query"]

_logger = logging.getLogger(__name__)

_LEXICAL_POS: Final[frozenset[str]] = frozenset({
    "NNG",  # 일반명사
    "NNP",  # 고유명사
    "NNB",  # 의존명사
    "SL",   # 외국어
    "SN",   # 숫자
    "XR",   # 어근
})
_GRAPH_POS: Final[frozenset[str]] = frozenset({"NNG", "NNP"})
_LONG_INPUT_THRESHOLD: Final[int] = 10_000


class QueryAnalyzer:
    """원시 사용자 쿼리를 검색 대상 표현으로 변환합니다.

    분석기는 의도적으로 얇게 설계되었습니다: 모든 공개 호출은 :meth:`analyze`를
    통해 라우팅되며, 입력을 한 번 정규화한 후 네 가지 대상별 헬퍼 중 하나로
    디스패치합니다. 헬퍼는 후처리 단계만 다르므로 :meth:`analyze`는 호출당
    사전 작업을 최소로 유지합니다.

    인자:
        normalizer: 선택적 :class:`KoreanNormalizer`. ``None``이면 고정된
            기본값(:meth:`KoreanNormalizer.default`)이 사용됩니다.
        tokenizer: 선택적 :class:`MeCabTokenizer`. ``None``이면
            :meth:`MeCabTokenizer.get_instance`의 프로세스 전체 싱글톤이
            사용됩니다.
        stopwords: lexical 파이프라인에 사용되는 불용어 집합의 선택적 재정의.
            ``None``이면 :data:`DEFAULT_STOPWORDS`가 사용됩니다.
    """

    __slots__ = ("_normalizer", "_stopwords", "_tokenizer")

    def __init__(
        self,
        normalizer: KoreanNormalizer | None = None,
        tokenizer: MeCabTokenizer | None = None,
        stopwords: frozenset[str] | None = None,
    ) -> None:
        self._normalizer: KoreanNormalizer = (
            normalizer if normalizer is not None else KoreanNormalizer.default()
        )
        self._tokenizer: MeCabTokenizer = (
            tokenizer if tokenizer is not None else MeCabTokenizer.get_instance()
        )
        self._stopwords: frozenset[str] = stopwords if stopwords is not None else DEFAULT_STOPWORDS

    def analyze(self, text: str, target: QueryTarget | str) -> QueryResult:
        """주어진 검색 *target*에 대해 *text*를 분석합니다.

        인자:
            text: 원시 사용자 쿼리.
            target: :class:`QueryTarget` 멤버 또는 동등한 문자열
                (``"lexical"``, ``"semantic"``, ``"graph"``, ``"hybrid"``).
                문자열 형식은 대소문자를 구분하지 않습니다.

        반환:
            *target*에 해당하는 :class:`LexicalQueryResult`,
            :class:`SemanticQueryResult`, :class:`GraphQueryResult`,
            :class:`HybridQueryResult` 중 하나.

        예외:
            InvalidInputError: *text*가 ``str``이 아니거나 *target*이
                :class:`QueryTarget`도 인식된 문자열도 아닌 경우.
            PIIDetectedError: *text*에 PII 패턴이 포함된 경우 (``guardrail-core``
                이후 2차 필터).
            MeCabNotAvailableError: MeCab이 입력을 분석할 수 없을 때(lexical,
                graph, hybrid) 토크나이저에서 전파됩니다.
        """
        if not isinstance(text, str):
            raise InvalidInputError(f"QueryAnalyzer.analyze expects str, got {type(text).__name__}")
        check_pii(text)
        resolved_target = self._resolve_target(target)

        if len(text) > _LONG_INPUT_THRESHOLD:
            _logger.warning(
                "QueryAnalyzer received input of %d characters "
                "(soft threshold %d); processing will continue.",
                len(text),
                _LONG_INPUT_THRESHOLD,
            )

        prepared = self._preprocess(text)

        if resolved_target is QueryTarget.LEXICAL:
            return self._run_lexical(prepared)
        if resolved_target is QueryTarget.SEMANTIC:
            return self._run_semantic(prepared)
        if resolved_target is QueryTarget.GRAPH:
            return self._run_graph(prepared)
        return self._run_hybrid(prepared)

    def _preprocess(self, text: str) -> str:
        """파이프라인 디스패치 전에 원시 입력 텍스트를 정규화합니다."""
        return self._normalizer.normalize(text)

    def _run_lexical(self, text: str) -> LexicalQueryResult:
        """Lexical 파이프라인: POS 필터링된 명사/외국어/숫자 + 불용어 제거.

        주 POS 태그가 :data:`_LEXICAL_POS`에 있는 토큰만 통과시켜,
        동사 어미와 조사가 BM25 색인 용어에서 제외되도록 합니다.
        """
        if not text:
            return LexicalQueryResult(keywords=(), query="")
        tokens = self._tokenizer.tokenize(
            text,
            pos_filter=_LEXICAL_POS,
            remove_stopwords=True,
            stopwords=self._stopwords,
        )
        return LexicalQueryResult(
            keywords=tuple(tokens),
            query=" ".join(tokens),
        )

    def _run_semantic(self, text: str) -> SemanticQueryResult:
        """Semantic 파이프라인: 자연 문장을 그대로 보존합니다.

        여기서 토큰화는 금지됩니다 — 임베딩 모델은 자유 형식 텍스트를 소비하며
        lexical 파이프라인이 제거하는 원래 단어 순서와 기능어로부터 이점을 얻습니다.
        """
        return SemanticQueryResult(query=text)

    def _run_graph(self, text: str) -> GraphQueryResult:
        """Graph 파이프라인: 명사/고유명사 표제어를 시드 노드로 추출합니다."""
        if not text:
            return GraphQueryResult(seed_nodes=())
        morphs: list[MorphToken] = self._tokenizer.analyze(text)
        seeds = tuple(m.lemma for m in morphs if m.pos in _GRAPH_POS)
        return GraphQueryResult(seed_nodes=seeds)

    def _run_hybrid(self, text: str) -> HybridQueryResult:
        """Hybrid 파이프라인: lexical, semantic, graph를 병렬로 실행합니다.

        세 브랜치는 동일한 전처리된 입력을 공유하지만 독립적인 MeCab/Python
        코드 경로를 호출하므로, 작은 스레드 풀이 경합 없이 작업을 겹쳐 처리합니다.
        풀은 제한적이며 호출당 해제됩니다 — hybrid 분석은 hot loop가 아닙니다.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_lex = executor.submit(self._run_lexical, text)
            f_sem = executor.submit(self._run_semantic, text)
            f_gph = executor.submit(self._run_graph, text)
            return HybridQueryResult(
                lexical=f_lex.result(),
                semantic=f_sem.result(),
                graph=f_gph.result(),
            )

    @staticmethod
    def _resolve_target(target: QueryTarget | str) -> QueryTarget:
        """*target*을 :class:`QueryTarget`으로 강제 변환하거나 예외를 발생시킵니다."""
        if isinstance(target, QueryTarget):
            return target
        if isinstance(target, str):
            try:
                return QueryTarget(target.lower())
            except ValueError as exc:
                valid = [t.value for t in QueryTarget]
                raise InvalidInputError(
                    f"Unknown query target: {target!r}. Valid targets: {valid}"
                ) from exc
        raise InvalidInputError(f"target must be QueryTarget or str, got {type(target).__name__}")


_default_analyzer: QueryAnalyzer | None = None


def _get_default_analyzer() -> QueryAnalyzer:
    """모듈 수준의 기본 분석기를 지연 생성하고 캐시합니다."""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = QueryAnalyzer()
    return _default_analyzer


def analyze_query(
    text: str,
    target: QueryTarget | str = "lexical",
) -> QueryResult:
    """기본 :class:`QueryAnalyzer`를 감싸는 편의 래퍼.

    ``QueryAnalyzer().analyze(text, target)``과 동일하지만 모듈 수준 인스턴스를
    재사용하여 하위 MeCab 싱글톤이 한 번만 초기화됩니다.

    인자:
        text: 원시 사용자 쿼리.
        target: 검색 대상; :meth:`QueryAnalyzer.analyze` 참조.

    반환:
        선택한 파이프라인이 생성한 :class:`QueryResult`.
    """
    return _get_default_analyzer().analyze(text, target)

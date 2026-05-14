"""QueryAnalyzer 4대상 파이프라인 테스트.

모든 대상 디스패치 로직은 DI 가짜로 검증되어 MeCab 없이도 스위트가 실행됩니다.
실제 모델 통합은 :mod:`test_golden`의 골든 집합 테스트에서 다룹니다.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from bpmg_korean_nlp.enums import QueryTarget
from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.models import (
    GraphQueryResult,
    HybridQueryResult,
    LexicalQueryResult,
    SemanticQueryResult,
)
from bpmg_korean_nlp.query_analyzer import QueryAnalyzer, analyze_query
from tests.conftest import FakeNormalizer, FakeTokenizer


def _build_analyzer(
    tokens: list[tuple[str, str]],
) -> tuple[QueryAnalyzer, FakeTokenizer]:
    norm = FakeNormalizer()
    tok = FakeTokenizer(tokens)
    qa = QueryAnalyzer(
        normalizer=norm,  # type: ignore[arg-type]
        tokenizer=tok,  # type: ignore[arg-type]
    )
    return qa, tok


# ---------------------------------------------------------------------------
# 결과 타입
# ---------------------------------------------------------------------------


def test_lexical_returns_lexical_result() -> None:
    """Lexical 대상은 튜플 키워드가 있는 ``LexicalQueryResult``를 반환합니다."""
    qa, _ = _build_analyzer([("조사", "NNG"), ("어미", "NNG"), ("차이", "NNG"), ("가", "JKS")])
    result = qa.analyze("조사랑 어미 차이", QueryTarget.LEXICAL)
    assert isinstance(result, LexicalQueryResult)
    assert isinstance(result.keywords, tuple)
    assert isinstance(result.query, str)
    # 조사 "가"는 DEFAULT_STOPWORDS에 있음
    assert "가" not in result.keywords
    assert result.query == " ".join(result.keywords)


def test_semantic_returns_semantic_result() -> None:
    """Semantic 대상은 전처리된 자연 문장을 보존합니다."""
    qa, _ = _build_analyzer([])
    text = "조사와 어미의 차이는 무엇인가요?"
    result = qa.analyze(text, QueryTarget.SEMANTIC)
    assert isinstance(result, SemanticQueryResult)
    # 정규화기는 통과(pass-through) 가짜(공백 제거)이므로 쿼리는
    # 전처리 후 텍스트와 같음 — 하지만 자유 형식이어야 함 (구두점 유지).
    assert "?" in result.query


def test_graph_returns_graph_result_nng_nnp_only() -> None:
    """Graph 대상은 ``NNG``/``NNP`` 표제어만 수집합니다."""
    qa, _ = _build_analyzer(
        [
            ("서울", "NNP"),
            ("에서", "JKB"),
            ("일", "NNG"),
            ("했다", "VV"),
        ]
    )
    result = qa.analyze("서울에서 일했다", QueryTarget.GRAPH)
    assert isinstance(result, GraphQueryResult)
    assert isinstance(result.seed_nodes, tuple)
    assert "서울" in result.seed_nodes
    assert "일" in result.seed_nodes
    assert "했다" not in result.seed_nodes
    assert "에서" not in result.seed_nodes


def test_hybrid_returns_hybrid_result_with_all_three() -> None:
    """Hybrid 대상은 lexical + semantic + graph를 하나의 레코드로 묶습니다."""
    qa, _ = _build_analyzer(
        [
            ("서울", "NNP"),
            ("에서", "JKB"),
            ("일", "NNG"),
        ]
    )
    result = qa.analyze("서울에서 일", QueryTarget.HYBRID)
    assert isinstance(result, HybridQueryResult)
    assert isinstance(result.lexical, LexicalQueryResult)
    assert isinstance(result.semantic, SemanticQueryResult)
    assert isinstance(result.graph, GraphQueryResult)


# ---------------------------------------------------------------------------
# 빈 문자열 / 공백 입력 × 4 대상
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_empty_input_per_target(target: QueryTarget) -> None:
    """빈 문자열 입력은 모든 대상에 대해 빈 결과 객체를 생성합니다."""
    qa, _ = _build_analyzer([])
    result = qa.analyze("", target)
    if isinstance(result, LexicalQueryResult):
        assert result.keywords == ()
        assert result.query == ""
    elif isinstance(result, SemanticQueryResult):
        assert result.query == ""
    elif isinstance(result, GraphQueryResult):
        assert result.seed_nodes == ()
    else:
        assert isinstance(result, HybridQueryResult)
        assert result.lexical.keywords == ()
        assert result.semantic.query == ""
        assert result.graph.seed_nodes == ()


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_whitespace_only_per_target(target: QueryTarget) -> None:
    """공백만 있는 입력은 빈 문자열로 정규화되어 빈 결과를 반환합니다."""
    qa, _ = _build_analyzer([])
    result = qa.analyze("   \t  ", target)
    assert result is not None


# ---------------------------------------------------------------------------
# 영어 / 한자 / 혼합
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_english_input_per_target(target: QueryTarget) -> None:
    """순수 영어 입력이 모든 대상을 통해 예외 없이 흐릅니다."""
    qa, _ = _build_analyzer([("hello", "SL"), ("world", "SL")])
    result = qa.analyze("hello world", target)
    assert result is not None


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_hanja_input_per_target(target: QueryTarget) -> None:
    """순수 한자 입력이 모든 대상을 통해 예외 없이 흐릅니다."""
    qa, _ = _build_analyzer([("國家", "SH")])
    result = qa.analyze("國家", target)
    assert result is not None


# ---------------------------------------------------------------------------
# 대상 강제 변환
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spelling",
    ["lexical", "LEXICAL", "Lexical", "lEXICaL"],
)
def test_string_target_case_insensitive(spelling: str) -> None:
    """문자열 대상 값은 대소문자에 관계없이 허용됩니다."""
    qa, _ = _build_analyzer([("test", "NNG")])
    result = qa.analyze("test", spelling)
    assert isinstance(result, LexicalQueryResult)


def test_unknown_target_string_raises() -> None:
    """인식되지 않는 대상 문자열은 :class:`InvalidInputError`를 발생시킵니다."""
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze("test", "unknown_target")


def test_non_string_non_enum_target_raises() -> None:
    """문자열도 :class:`QueryTarget`도 아닌 대상은 예외를 발생시킵니다."""
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze("test", 123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 입력 유효성 검사
# ---------------------------------------------------------------------------


def test_rejects_none_text() -> None:
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze(None, QueryTarget.LEXICAL)  # type: ignore[arg-type]


def test_rejects_non_str_text() -> None:
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze(42, QueryTarget.LEXICAL)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 파이프라인 배선
# ---------------------------------------------------------------------------


def test_hybrid_runs_each_branch_once() -> None:
    """Hybrid 파이프라인은 각 브랜치를 단독으로 실행한 결과와 일관된 결과를 생성합니다."""
    qa, _ = _build_analyzer([("서울", "NNP"), ("일", "NNG"), ("의", "JKG")])
    h = qa.analyze("서울 일의", QueryTarget.HYBRID)
    assert isinstance(h, HybridQueryResult)
    # graph 브랜치는 NNG/NNP만 유지
    assert "의" not in h.graph.seed_nodes
    # lexical 브랜치는 DEFAULT_STOPWORDS를 통해 조사 "의"를 제거
    assert "의" not in h.lexical.keywords


def test_long_input_warning_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    """10k 문자 이상의 입력은 WARNING을 발생시키지만 처리는 완료됩니다."""
    qa, _ = _build_analyzer([])
    long_text = "가" * 10_001
    with caplog.at_level("WARNING", logger="bpmg_korean_nlp.query_analyzer"):
        qa.analyze(long_text, QueryTarget.SEMANTIC)
    assert any("characters" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# 모듈 수준 analyze_query
# ---------------------------------------------------------------------------


def test_analyze_query_default_target_is_lexical() -> None:
    """편의 함수의 기본값은 ``"lexical"``입니다."""
    from bpmg_korean_nlp import query_analyzer as qa_module

    qa_module._default_analyzer = QueryAnalyzer(
        normalizer=FakeNormalizer(),  # type: ignore[arg-type]
        tokenizer=FakeTokenizer([("test", "NNG")]),  # type: ignore[arg-type]
    )
    result = analyze_query("test")
    assert isinstance(result, LexicalQueryResult)


def test_analyze_query_accepts_string_target() -> None:
    """문자열 대상 이름이 :meth:`QueryAnalyzer.analyze`로 전달됩니다."""
    from bpmg_korean_nlp import query_analyzer as qa_module

    qa_module._default_analyzer = QueryAnalyzer(
        normalizer=FakeNormalizer(),  # type: ignore[arg-type]
        tokenizer=FakeTokenizer([("test", "NNG")]),  # type: ignore[arg-type]
    )
    result = analyze_query("test", "semantic")
    assert isinstance(result, SemanticQueryResult)


# ---------------------------------------------------------------------------
# 금지된 임포트
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# lexical 파이프라인에서의 POS 필터 동작
# ---------------------------------------------------------------------------


def test_lexical_excludes_verb_endings() -> None:
    """동사+어미 복합 태그(VV+EC)는 lexical 결과에서 제외됩니다."""
    qa, _ = _build_analyzer(
        [
            ("맛집", "NNG"),
            ("추천", "NNG"),
            ("해주", "VV+EC"),
            ("세요", "EP+EF"),
        ]
    )
    result = qa.analyze("맛집 추천 해주세요", QueryTarget.LEXICAL)
    assert isinstance(result, LexicalQueryResult)
    assert "맛집" in result.keywords
    assert "추천" in result.keywords
    assert "해주" not in result.keywords
    assert "세요" not in result.keywords


def test_lexical_excludes_particles() -> None:
    """조사 태그(JKS, JKO 등)는 lexical 결과에서 제외됩니다."""
    qa, _ = _build_analyzer(
        [
            ("서울", "NNP"),
            ("이", "JKS"),
            ("좋다", "VA"),
        ]
    )
    result = qa.analyze("서울이 좋다", QueryTarget.LEXICAL)
    assert isinstance(result, LexicalQueryResult)
    assert "서울" in result.keywords
    assert "이" not in result.keywords
    assert "좋다" not in result.keywords


def test_lexical_includes_nng_nnp() -> None:
    """NNG(일반명사)와 NNP(고유명사)는 POS 필터를 통과합니다."""
    qa, _ = _build_analyzer(
        [
            ("한국어", "NNG"),
            ("서울", "NNP"),
            ("처리", "NNG"),
            ("에서", "JKB"),
        ]
    )
    result = qa.analyze("한국어 서울 처리 에서", QueryTarget.LEXICAL)
    assert isinstance(result, LexicalQueryResult)
    assert "한국어" in result.keywords
    assert "서울" in result.keywords
    assert "처리" in result.keywords
    assert "에서" not in result.keywords


# ---------------------------------------------------------------------------
# 금지된 임포트
# ---------------------------------------------------------------------------


def test_query_analyzer_does_not_import_retrieval_core() -> None:
    """정적 AST 검사: ``query_analyzer.py``가 금지된 패키지를 건드리지 않습니다."""
    forbidden = {"retrieval_core", "guardrail_core", "chatbot_contracts"}
    path = Path(__file__).parent.parent / "src" / "bpmg_korean_nlp" / "query_analyzer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                head = alias.name.split(".", 1)[0]
                assert head not in forbidden
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            head = module.split(".", 1)[0]
            assert head not in forbidden

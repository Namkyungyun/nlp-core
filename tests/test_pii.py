"""``bpmg_korean_nlp.pii`` 테스트 — 2차 PII 차단 필터."""

from __future__ import annotations

import re

import pytest

from bpmg_korean_nlp.exceptions import PIIDetectedError
from bpmg_korean_nlp.models import PIIPattern
from bpmg_korean_nlp.pii import PII_PATTERNS

# ---------------------------------------------------------------------------
# PII_PATTERNS 카탈로그
# ---------------------------------------------------------------------------


def test_pii_patterns_type() -> None:
    """카탈로그는 PIIPattern의 불변 튜플로 노출됩니다."""
    assert isinstance(PII_PATTERNS, tuple)
    for p in PII_PATTERNS:
        assert isinstance(p, PIIPattern)


def test_pii_patterns_count() -> None:
    """정확히 네 가지 정식 PII 범주가 카탈로그에 있습니다."""
    assert len(PII_PATTERNS) == 4


def test_each_pattern_is_compiled_regex() -> None:
    """모든 항목은 컴파일된 ``re.Pattern``을 노출합니다."""
    for p in PII_PATTERNS:
        assert isinstance(p.pattern, re.Pattern)


def test_pii_patterns_unique_names() -> None:
    """패턴 이름은 집합을 형성합니다 — 중복 없음."""
    names = {p.name for p in PII_PATTERNS}
    assert len(names) == len(PII_PATTERNS)


def test_pii_patterns_have_descriptions() -> None:
    """각 패턴은 비어 있지 않은 설명을 포함합니다."""
    for p in PII_PATTERNS:
        assert p.description != ""


# ---------------------------------------------------------------------------
# 패턴 매칭 정상 동작 확인
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "sample"),
    [
        ("resident_id", "900101-1234567"),
        ("mobile_phone", "010-1234-5678"),
        ("business_id", "123-45-67890"),
        ("foreign_id", "900101-5234567"),
    ],
)
def test_pattern_matches_sample(name: str, sample: str) -> None:
    """각 이름 있는 패턴이 타당한 샘플 값과 일치합니다."""
    p = next(x for x in PII_PATTERNS if x.name == name)
    assert p.pattern.search(sample) is not None


@pytest.mark.parametrize(
    "non_match",
    [
        "1234-5678",
        "not a phone",
        "abc-de-fghij",
    ],
)
def test_patterns_reject_garbage(non_match: str) -> None:
    """카탈로그의 어떤 패턴도 명백히 잘못된 입력과 완전 일치하지 않습니다."""
    for p in PII_PATTERNS:
        assert p.pattern.fullmatch(non_match) is None


# ---------------------------------------------------------------------------
# QueryAnalyzer를 통한 PIIDetectedError (자동 통합)
# di_query_analyzer는 가짜 DI를 사용 — pii 체크가 토크나이저보다 먼저 실행됨
# ---------------------------------------------------------------------------


def test_query_analyzer_blocks_mobile_phone(di_query_analyzer: object) -> None:
    """QueryAnalyzer.analyze()는 휴대전화 번호에 대해 PIIDetectedError를 발생시킵니다."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    with pytest.raises(PIIDetectedError) as exc_info:
        qa.analyze("010-1234-5678 관련 문서 찾아줘", QueryTarget.LEXICAL)
    assert "mobile_phone" in exc_info.value.matched


def test_query_analyzer_blocks_resident_id(di_query_analyzer: object) -> None:
    """QueryAnalyzer.analyze()는 주민등록번호에 대해 PIIDetectedError를 발생시킵니다."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    with pytest.raises(PIIDetectedError) as exc_info:
        qa.analyze("주민번호 900101-1234567 조회", QueryTarget.SEMANTIC)
    assert "resident_id" in exc_info.value.matched


def test_pii_error_matched_contains_all_patterns(di_query_analyzer: object) -> None:
    """여러 PII 패턴이 나타나면 모두 matched에 보고됩니다."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    # mobile_phone과 resident_id 모두 포함
    text = "연락처 010-9999-1234 주민번호 900101-1234567"
    with pytest.raises(PIIDetectedError) as exc_info:
        qa.analyze(text, QueryTarget.HYBRID)
    matched = exc_info.value.matched
    assert "mobile_phone" in matched
    assert "resident_id" in matched


def test_query_analyzer_passes_clean_input(di_query_analyzer: object) -> None:
    """PII가 없는 정상 입력은 예외 없이 통과합니다."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    result = qa.analyze("한국어 형태소 분석이란", QueryTarget.LEXICAL)
    assert result is not None


# ---------------------------------------------------------------------------
# PIIDetectedError 예외 계약
# ---------------------------------------------------------------------------


def test_pii_error_is_korean_nlp_error() -> None:
    """PIIDetectedError는 KoreanNlpError를 상속합니다."""
    from bpmg_korean_nlp.exceptions import KoreanNlpError

    assert issubclass(PIIDetectedError, KoreanNlpError)


def test_pii_detected_error_matched_attribute() -> None:
    """PIIDetectedError.matched는 트리거된 패턴 이름 목록을 보유합니다."""
    err = PIIDetectedError(["mobile_phone", "resident_id"])
    assert err.matched == ["mobile_phone", "resident_id"]
    assert "mobile_phone" in str(err)

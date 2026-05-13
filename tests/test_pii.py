"""Tests for ``bpmg_korean_nlp.pii`` — secondary PII blocking filter."""

from __future__ import annotations

import re

import pytest

from bpmg_korean_nlp.exceptions import PIIDetectedError
from bpmg_korean_nlp.models import PIIPattern
from bpmg_korean_nlp.pii import PII_PATTERNS


# ---------------------------------------------------------------------------
# PII_PATTERNS catalogue
# ---------------------------------------------------------------------------


def test_pii_patterns_type() -> None:
    """The catalogue is exposed as an immutable tuple of PIIPattern."""
    assert isinstance(PII_PATTERNS, tuple)
    for p in PII_PATTERNS:
        assert isinstance(p, PIIPattern)


def test_pii_patterns_count() -> None:
    """Exactly four canonical PII categories are catalogued."""
    assert len(PII_PATTERNS) == 4


def test_each_pattern_is_compiled_regex() -> None:
    """Every entry exposes a compiled ``re.Pattern``."""
    for p in PII_PATTERNS:
        assert isinstance(p.pattern, re.Pattern)


def test_pii_patterns_unique_names() -> None:
    """Pattern names form a set — no duplicates."""
    names = {p.name for p in PII_PATTERNS}
    assert len(names) == len(PII_PATTERNS)


def test_pii_patterns_have_descriptions() -> None:
    """Each pattern carries a non-empty description."""
    for p in PII_PATTERNS:
        assert p.description != ""


# ---------------------------------------------------------------------------
# Pattern matching sanity checks
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
    """Each named pattern matches a plausible sample value."""
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
    """None of the catalogued patterns fullmatch obviously-wrong input."""
    for p in PII_PATTERNS:
        assert p.pattern.fullmatch(non_match) is None


# ---------------------------------------------------------------------------
# PIIDetectedError via QueryAnalyzer (auto-integration)
# di_query_analyzer uses fake DI — pii check fires before tokenizer
# ---------------------------------------------------------------------------


def test_query_analyzer_blocks_mobile_phone(di_query_analyzer: object) -> None:
    """QueryAnalyzer.analyze() raises PIIDetectedError on mobile phone number."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    with pytest.raises(PIIDetectedError) as exc_info:
        qa.analyze("010-1234-5678 관련 문서 찾아줘", QueryTarget.LEXICAL)
    assert "mobile_phone" in exc_info.value.matched


def test_query_analyzer_blocks_resident_id(di_query_analyzer: object) -> None:
    """QueryAnalyzer.analyze() raises PIIDetectedError on resident registration number."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    with pytest.raises(PIIDetectedError) as exc_info:
        qa.analyze("주민번호 900101-1234567 조회", QueryTarget.SEMANTIC)
    assert "resident_id" in exc_info.value.matched


def test_pii_error_matched_contains_all_patterns(di_query_analyzer: object) -> None:
    """When multiple PII patterns appear, all are reported in matched."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    # contains both mobile_phone and resident_id
    text = "연락처 010-9999-1234 주민번호 900101-1234567"
    with pytest.raises(PIIDetectedError) as exc_info:
        qa.analyze(text, QueryTarget.HYBRID)
    matched = exc_info.value.matched
    assert "mobile_phone" in matched
    assert "resident_id" in matched


def test_query_analyzer_passes_clean_input(di_query_analyzer: object) -> None:
    """Normal input without PII passes through without raising."""
    from bpmg_korean_nlp.enums import QueryTarget
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    qa: QueryAnalyzer = di_query_analyzer  # type: ignore[assignment]
    result = qa.analyze("한국어 형태소 분석이란", QueryTarget.LEXICAL)
    assert result is not None


# ---------------------------------------------------------------------------
# PIIDetectedError exception contract
# ---------------------------------------------------------------------------


def test_pii_error_is_korean_nlp_error() -> None:
    """PIIDetectedError inherits from KoreanNlpError."""
    from bpmg_korean_nlp.exceptions import KoreanNlpError

    assert issubclass(PIIDetectedError, KoreanNlpError)


def test_pii_detected_error_matched_attribute() -> None:
    """PIIDetectedError.matched carries the list of triggered pattern names."""
    err = PIIDetectedError(["mobile_phone", "resident_id"])
    assert err.matched == ["mobile_phone", "resident_id"]
    assert "mobile_phone" in str(err)

"""한글 자모 분해/조합 계층 테스트."""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.enums import CharType
from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.jamo_utils import (
    CHOSEONG_TABLE,
    JONGSEONG_TABLE,
    JUNGSEONG_TABLE,
    classify_char,
    compose,
    decompose,
    extract_choseong,
)


def test_decompose_basic() -> None:
    """``한``은 (ㅎ, ㅏ, ㄴ)으로 분해됩니다."""
    from bpmg_korean_nlp.models import JamoComponents

    assert decompose("한") == JamoComponents(choseong="ㅎ", jungseong="ㅏ", jongseong="ㄴ")


def test_decompose_no_jongseong() -> None:
    """종성이 없는 음절의 ``jongseong``은 빈 문자열입니다."""
    components = decompose("가")
    assert components.choseong == "ㄱ"
    assert components.jungseong == "ㅏ"
    assert components.jongseong == ""


def test_compose_basic() -> None:
    """compose(ㅎ, ㅏ, ㄴ) → 한."""
    assert compose("ㅎ", "ㅏ", "ㄴ") == "한"


def test_compose_no_jongseong() -> None:
    """생략된 종성은 기본적으로 빈 문자열입니다."""
    assert compose("ㄱ", "ㅏ") == "가"


def test_compose_decompose_full_roundtrip() -> None:
    """U+AC00부터 U+D7A3 범위의 모든 음절이 손실 없이 라운드 트립합니다."""
    for code in range(0xAC00, 0xD7A3 + 1):
        syllable = chr(code)
        c = decompose(syllable)
        assert compose(c.choseong, c.jungseong, c.jongseong) == syllable


def test_decompose_rejects_non_hangul() -> None:
    with pytest.raises(InvalidInputError):
        decompose("A")


def test_decompose_rejects_multichar() -> None:
    with pytest.raises(InvalidInputError):
        decompose("한국")


def test_decompose_rejects_empty() -> None:
    with pytest.raises(InvalidInputError):
        decompose("")


def test_decompose_rejects_none() -> None:
    with pytest.raises(InvalidInputError):
        decompose(None)  # type: ignore[arg-type]


def test_decompose_rejects_non_str() -> None:
    with pytest.raises(InvalidInputError):
        decompose(123)  # type: ignore[arg-type]


def test_compose_rejects_invalid_jamo() -> None:
    with pytest.raises(InvalidInputError):
        compose("X", "ㅏ", "")
    with pytest.raises(InvalidInputError):
        compose("ㄱ", "X", "")
    with pytest.raises(InvalidInputError):
        compose("ㄱ", "ㅏ", "X")


def test_extract_choseong_korean() -> None:
    """각 음절은 초성을 제공합니다."""
    assert extract_choseong("한국어") == "ㅎㄱㅇ"


def test_extract_choseong_mixed() -> None:
    """한글이 아닌 문자는 그대로 보존됩니다."""
    assert extract_choseong("Hello 세계") == "Hello ㅅㄱ"


def test_extract_choseong_with_numbers() -> None:
    assert extract_choseong("안녕 2025년") == "ㅇㄴ 2025ㄴ"


def test_extract_choseong_empty() -> None:
    assert extract_choseong("") == ""


def test_extract_choseong_rejects_none() -> None:
    with pytest.raises(InvalidInputError):
        extract_choseong(None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("char", "expected"),
    [
        ("가", CharType.HANGUL_SYLLABLE),
        ("힣", CharType.HANGUL_SYLLABLE),
        ("ㄱ", CharType.HANGUL_JAMO),
        ("ㅎ", CharType.HANGUL_JAMO),
        ("國", CharType.HANJA),
        ("漢", CharType.HANJA),
        ("A", CharType.LATIN),
        ("z", CharType.LATIN),
        ("0", CharType.NUMBER),
        ("9", CharType.NUMBER),
        (" ", CharType.WHITESPACE),
        ("\t", CharType.WHITESPACE),
        ("\n", CharType.WHITESPACE),
        (".", CharType.SYMBOL),
        ("?", CharType.SYMBOL),
        ("!", CharType.SYMBOL),
    ],
)
def test_classify_char(char: str, expected: CharType) -> None:
    """각 스크립트 버킷이 올바르게 분류됩니다."""
    assert classify_char(char) == expected


def test_classify_char_rejects_multichar() -> None:
    with pytest.raises(InvalidInputError):
        classify_char("ab")


def test_classify_char_rejects_empty() -> None:
    with pytest.raises(InvalidInputError):
        classify_char("")


def test_classify_char_rejects_none() -> None:
    with pytest.raises(InvalidInputError):
        classify_char(None)  # type: ignore[arg-type]


def test_classify_char_fullwidth_digit() -> None:
    """전각 숫자 '０'은 NUMBER로 분류됩니다."""  # noqa: RUF002
    assert classify_char("０") == CharType.NUMBER  # noqa: RUF001


def test_tables_have_expected_sizes() -> None:
    """자모 테이블이 유니코드 한글 알고리즘 상수와 일치합니다."""
    assert len(CHOSEONG_TABLE) == 19
    assert len(JUNGSEONG_TABLE) == 21
    assert len(JONGSEONG_TABLE) == 28
    assert JONGSEONG_TABLE[0] == ""  # 인덱스 0 = 종성 없음

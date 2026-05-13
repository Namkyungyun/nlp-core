"""Tests for the Hangul jamo decomposition / composition layer."""

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
    """``한`` decomposes into (ㅎ, ㅏ, ㄴ)."""
    from bpmg_korean_nlp.models import JamoComponents

    assert decompose("한") == JamoComponents(choseong="ㅎ", jungseong="ㅏ", jongseong="ㄴ")


def test_decompose_no_jongseong() -> None:
    """A syllable without a final consonant has empty ``jongseong``."""
    components = decompose("가")
    assert components.choseong == "ㄱ"
    assert components.jungseong == "ㅏ"
    assert components.jongseong == ""


def test_compose_basic() -> None:
    """compose(ㅎ, ㅏ, ㄴ) → 한."""
    assert compose("ㅎ", "ㅏ", "ㄴ") == "한"


def test_compose_no_jongseong() -> None:
    """An omitted jongseong defaults to an empty string."""
    assert compose("ㄱ", "ㅏ") == "가"


def test_compose_decompose_full_roundtrip() -> None:
    """Every syllable in the U+AC00 to U+D7A3 range round-trips losslessly."""
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
    """Each syllable contributes its initial consonant."""
    assert extract_choseong("한국어") == "ㅎㄱㅇ"


def test_extract_choseong_mixed() -> None:
    """Non-Hangul characters are preserved verbatim."""
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
    """Each script bucket is classified correctly."""
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
    """Fullwidth digit '０' is bucketed as NUMBER."""  # noqa: RUF002
    assert classify_char("０") == CharType.NUMBER  # noqa: RUF001


def test_tables_have_expected_sizes() -> None:
    """The jamo tables match the Unicode Hangul algorithm constants."""
    assert len(CHOSEONG_TABLE) == 19
    assert len(JUNGSEONG_TABLE) == 21
    assert len(JONGSEONG_TABLE) == 28
    assert JONGSEONG_TABLE[0] == ""  # index 0 = no final consonant

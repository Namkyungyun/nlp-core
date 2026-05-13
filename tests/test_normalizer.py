"""Tests for ``bpmg_korean_nlp.normalizer.KoreanNormalizer``."""

from __future__ import annotations

import unicodedata

import pytest

from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.normalizer import KoreanNormalizer


def test_nfc_normalization(normalizer: KoreanNormalizer) -> None:
    """An NFD-decomposed string is normalized to NFC."""
    nfd = unicodedata.normalize("NFD", "한국어")
    assert nfd != "한국어"
    assert normalizer.normalize(nfd) == "한국어"


def test_idempotent_on_nfc(normalizer: KoreanNormalizer) -> None:
    """A string already in NFC is unchanged (beyond whitespace folding)."""
    assert normalizer.normalize("한국어") == "한국어"


@pytest.mark.parametrize("ws", [" ", " ", "　"])  # noqa: RUF001
def test_unicode_whitespace_folded_to_ascii(normalizer: KoreanNormalizer, ws: str) -> None:
    """Non-breaking, em-, and ideographic-space all fold to ASCII space."""
    out = normalizer.normalize(f"가{ws}나")
    assert out == "가 나"


def test_collapses_multiple_spaces(normalizer: KoreanNormalizer) -> None:
    """Runs of whitespace collapse to a single ASCII space."""
    assert normalizer.normalize("가   나     다") == "가 나 다"


def test_strips_outer_whitespace(normalizer: KoreanNormalizer) -> None:
    assert normalizer.normalize("   가   ") == "가"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ㅋㅋㅋㅋ", "ㅋㅋ"),
        ("ㅎㅎㅎㅎㅎ", "ㅎㅎ"),
        ("아아아아 좋다", "아아 좋다"),
    ],
)
def test_repeat_normalize(normalizer: KoreanNormalizer, raw: str, expected: str) -> None:
    """soynlp ``repeat_normalize`` is applied with ``num_repeats=2``."""
    assert normalizer.normalize(raw) == expected


def test_empty_string_returns_empty(normalizer: KoreanNormalizer) -> None:
    assert normalizer.normalize("") == ""


def test_whitespace_only_returns_empty(normalizer: KoreanNormalizer) -> None:
    """A whitespace-only input collapses and strips to the empty string."""
    assert normalizer.normalize("   \t  ") == ""


def test_rejects_none() -> None:
    with pytest.raises(InvalidInputError):
        KoreanNormalizer.default().normalize(None)  # type: ignore[arg-type]


def test_rejects_int() -> None:
    with pytest.raises(InvalidInputError):
        KoreanNormalizer.default().normalize(123)  # type: ignore[arg-type]


def test_rejects_bytes() -> None:
    with pytest.raises(InvalidInputError):
        KoreanNormalizer.default().normalize(b"hello")  # type: ignore[arg-type]


def test_custom_substitutions_applied_in_order() -> None:
    """Custom substitutions run after the rest of the pipeline."""
    nz = KoreanNormalizer(
        custom_substitutions=[
            (r"AAA", "BBB"),
            (r"BBB", "CCC"),
        ]
    )
    assert nz.normalize("AAA test") == "CCC test"


def test_custom_substitutions_empty_default() -> None:
    """No custom substitutions = no rewriting beyond the locked pipeline."""
    nz = KoreanNormalizer()
    assert nz.normalize("hello world") == "hello world"


def test_default_classmethod_returns_normalizer() -> None:
    nz = KoreanNormalizer.default()
    assert isinstance(nz, KoreanNormalizer)


def test_hanja_to_hangul_off_by_default(normalizer: KoreanNormalizer) -> None:
    """Default policy: hanja is preserved verbatim."""
    out = normalizer.normalize("國家")
    assert out == "國家"


def test_hanja_to_hangul_on_no_op_without_optional_pkg() -> None:
    """``hanja_to_hangul=True`` is a no-op when the optional pkg is missing.

    The flag must not raise — the implementation falls back to leaving the
    text untouched and emits a single log warning.
    """
    nz = KoreanNormalizer(hanja_to_hangul=True)
    try:
        import hanja  # noqa: F401
    except ImportError:
        # No optional package — text passes through unchanged.
        assert nz.normalize("國家") == "國家"
    else:
        # With the package installed the output is in Hangul; just assert it's a str.
        assert isinstance(nz.normalize("國家"), str)


def test_combined_pipeline(normalizer: KoreanNormalizer) -> None:
    """All locked stages run in order on a representative messy input."""
    raw = "  ㅋㅋㅋㅋ　안녕  하세요   "
    assert normalizer.normalize(raw) == "ㅋㅋ 안녕 하세요"

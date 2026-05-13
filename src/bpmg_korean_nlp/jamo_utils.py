"""Hangul jamo decomposition, composition, and character classification.

This module implements the pure-Python Hangul utility layer used across the
SDK. The decomposition formula follows the Unicode standard for the Hangul
Syllables block (``U+AC00``-``U+D7A3``) and guarantees a perfect round trip:
``compose(*decompose(c)) == c`` for every syllable in that range.
"""

from __future__ import annotations

from bpmg_korean_nlp.enums import CharType
from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.models import JamoComponents

__all__ = [
    "CHOSEONG_TABLE",
    "JONGSEONG_TABLE",
    "JUNGSEONG_TABLE",
    "classify_char",
    "compose",
    "decompose",
    "extract_choseong",
]


_HANGUL_BASE: int = 0xAC00
_HANGUL_LAST: int = 0xD7A3
_JUNG_COUNT: int = 21
_JONG_COUNT: int = 28

CHOSEONG_TABLE: tuple[str, ...] = (
    "ㄱ",
    "ㄲ",
    "ㄴ",
    "ㄷ",
    "ㄸ",
    "ㄹ",
    "ㅁ",
    "ㅂ",
    "ㅃ",
    "ㅅ",
    "ㅆ",
    "ㅇ",
    "ㅈ",
    "ㅉ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
)

JUNGSEONG_TABLE: tuple[str, ...] = (
    "ㅏ",
    "ㅐ",
    "ㅑ",
    "ㅒ",
    "ㅓ",
    "ㅔ",
    "ㅕ",
    "ㅖ",
    "ㅗ",
    "ㅘ",
    "ㅙ",
    "ㅚ",
    "ㅛ",
    "ㅜ",
    "ㅝ",
    "ㅞ",
    "ㅟ",
    "ㅠ",
    "ㅡ",
    "ㅢ",
    "ㅣ",
)

JONGSEONG_TABLE: tuple[str, ...] = (
    "",
    "ㄱ",
    "ㄲ",
    "ㄳ",
    "ㄴ",
    "ㄵ",
    "ㄶ",
    "ㄷ",
    "ㄹ",
    "ㄺ",
    "ㄻ",
    "ㄼ",
    "ㄽ",
    "ㄾ",
    "ㄿ",
    "ㅀ",
    "ㅁ",
    "ㅂ",
    "ㅄ",
    "ㅅ",
    "ㅆ",
    "ㅇ",
    "ㅈ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
)

_CHOSEONG_INDEX: dict[str, int] = {c: i for i, c in enumerate(CHOSEONG_TABLE)}
_JUNGSEONG_INDEX: dict[str, int] = {c: i for i, c in enumerate(JUNGSEONG_TABLE)}
_JONGSEONG_INDEX: dict[str, int] = {c: i for i, c in enumerate(JONGSEONG_TABLE)}


def _require_str(value: object, field: str) -> str:
    """Reject ``None`` and non-``str`` inputs with :class:`InvalidInputError`."""
    if value is None:
        raise InvalidInputError(f"{field} must not be None")
    if not isinstance(value, str):
        raise InvalidInputError(f"{field} must be str, got {type(value).__name__}")
    return value


def _is_hangul_syllable(char: str) -> bool:
    """Return ``True`` iff *char* is a single completed Hangul syllable."""
    return len(char) == 1 and _HANGUL_BASE <= ord(char) <= _HANGUL_LAST


def decompose(char: str) -> JamoComponents:
    """Decompose a single Hangul syllable into (choseong, jungseong, jongseong).

    Args:
        char: A single completed Hangul syllable in the range
            ``U+AC00``-``U+D7A3``.

    Returns:
        A :class:`JamoComponents` whose ``jongseong`` field is the empty
        string when the syllable has no final consonant.

    Raises:
        InvalidInputError: ``char`` is ``None``, not a string, not exactly one
            character long, or not a Hangul syllable.
    """
    text = _require_str(char, "char")
    if len(text) != 1:
        raise InvalidInputError(f"decompose expects a single character, got length {len(text)}")
    if not _is_hangul_syllable(text):
        raise InvalidInputError(
            f"decompose expects a Hangul syllable (U+AC00-U+D7A3), got {text!r}"
        )

    offset = ord(text) - _HANGUL_BASE
    cho_index, remainder = divmod(offset, _JUNG_COUNT * _JONG_COUNT)
    jung_index, jong_index = divmod(remainder, _JONG_COUNT)
    return JamoComponents(
        choseong=CHOSEONG_TABLE[cho_index],
        jungseong=JUNGSEONG_TABLE[jung_index],
        jongseong=JONGSEONG_TABLE[jong_index],
    )


def compose(choseong: str, jungseong: str, jongseong: str = "") -> str:
    """Compose initial, medial, and (optional) final jamo into one syllable.

    Args:
        choseong: Initial consonant jamo (must appear in :data:`CHOSEONG_TABLE`).
        jungseong: Medial vowel jamo (must appear in :data:`JUNGSEONG_TABLE`).
        jongseong: Final consonant jamo or the empty string for no final
            consonant (must appear in :data:`JONGSEONG_TABLE`).

    Returns:
        The composed Hangul syllable. ``compose(*decompose(c)) == c`` holds
        for every ``c`` in ``U+AC00``-``U+D7A3``.

    Raises:
        InvalidInputError: Any argument is missing, not a string, or not a
            valid jamo for its position.
    """
    cho = _require_str(choseong, "choseong")
    jung = _require_str(jungseong, "jungseong")
    jong = _require_str(jongseong, "jongseong")

    cho_index = _CHOSEONG_INDEX.get(cho)
    if cho_index is None:
        raise InvalidInputError(f"invalid choseong jamo: {cho!r}")
    jung_index = _JUNGSEONG_INDEX.get(jung)
    if jung_index is None:
        raise InvalidInputError(f"invalid jungseong jamo: {jung!r}")
    jong_index = _JONGSEONG_INDEX.get(jong)
    if jong_index is None:
        raise InvalidInputError(f"invalid jongseong jamo: {jong!r}")

    code_point = (
        _HANGUL_BASE + cho_index * _JUNG_COUNT * _JONG_COUNT + jung_index * _JONG_COUNT + jong_index
    )
    return chr(code_point)


def extract_choseong(text: str) -> str:
    """Return the choseong-only projection of *text*.

    Each completed Hangul syllable contributes its initial consonant; every
    other character (Latin, digits, whitespace, jamo, punctuation, etc.) is
    preserved verbatim. The result is useful for choseong search and fuzzy
    typo correction.

    Args:
        text: Arbitrary text. The empty string returns the empty string.

    Returns:
        A string of the same length as *text* where Hangul syllables are
        replaced by their choseong.

    Raises:
        InvalidInputError: ``text`` is ``None`` or not a string.
    """
    value = _require_str(text, "text")
    if not value:
        return ""

    buffer: list[str] = []
    for char in value:
        if _HANGUL_BASE <= ord(char) <= _HANGUL_LAST:
            offset = ord(char) - _HANGUL_BASE
            cho_index = offset // (_JUNG_COUNT * _JONG_COUNT)
            buffer.append(CHOSEONG_TABLE[cho_index])
        else:
            buffer.append(char)
    return "".join(buffer)


def _is_hanja(code: int) -> bool:
    """Return ``True`` when *code* lies in any of the common CJK Han blocks."""
    return (
        0x4E00 <= code <= 0x9FFF  # CJK Unified Ideographs
        or 0x3400 <= code <= 0x4DBF  # CJK Extension A
        or 0x20000 <= code <= 0x2A6DF  # CJK Extension B
        or 0x2A700 <= code <= 0x2B73F  # CJK Extension C
        or 0x2B740 <= code <= 0x2B81F  # CJK Extension D
        or 0x2B820 <= code <= 0x2CEAF  # CJK Extension E
        or 0xF900 <= code <= 0xFAFF  # CJK Compatibility Ideographs
    )


def _is_hangul_jamo(code: int) -> bool:
    """Return ``True`` for jamo blocks (not for completed syllables)."""
    return (
        0x1100 <= code <= 0x11FF  # Hangul Jamo
        or 0x3130 <= code <= 0x318F  # Hangul Compatibility Jamo
        or 0xA960 <= code <= 0xA97F  # Hangul Jamo Extended-A
        or 0xD7B0 <= code <= 0xD7FF  # Hangul Jamo Extended-B
    )


def _is_latin(code: int) -> bool:
    """Return ``True`` for ASCII letters plus the Latin extension ranges."""
    if 0x41 <= code <= 0x5A or 0x61 <= code <= 0x7A:
        return True
    return (
        0x00C0 <= code <= 0x024F  # Latin-1 Supplement, Extended-A/B
        or 0x1E00 <= code <= 0x1EFF  # Latin Extended Additional
    )


def classify_char(char: str) -> CharType:
    """Classify a single character into one of the :class:`CharType` buckets.

    Args:
        char: Exactly one Unicode code point.

    Returns:
        The matching :class:`CharType` value. ``OTHER`` is used as the
        fallthrough bucket for code points that do not match any of the
        recognised scripts.

    Raises:
        InvalidInputError: ``char`` is ``None``, not a string, or not exactly
            one character long.
    """
    text = _require_str(char, "char")
    if len(text) != 1:
        raise InvalidInputError(f"classify_char expects a single character, got length {len(text)}")

    code = ord(text)
    if _HANGUL_BASE <= code <= _HANGUL_LAST:
        return CharType.HANGUL_SYLLABLE
    if _is_hangul_jamo(code):
        return CharType.HANGUL_JAMO
    if _is_hanja(code):
        return CharType.HANJA
    if _is_latin(code):
        return CharType.LATIN
    if 0x30 <= code <= 0x39:
        return CharType.NUMBER
    if text.isspace():
        return CharType.WHITESPACE
    category = text
    if category.isalpha() or category.isdigit():
        # Non-script alpha/digit code points (e.g. fullwidth digits) — treat
        # them as their nearest neighbour.
        if category.isdigit():
            return CharType.NUMBER
        return CharType.OTHER
    if not text.isprintable():
        return CharType.OTHER
    # Punctuation / symbols / mathematical operators fall here.
    return CharType.SYMBOL

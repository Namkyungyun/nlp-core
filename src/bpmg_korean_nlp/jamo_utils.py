"""한글 자모 분해, 조합, 문자 분류.

이 모듈은 SDK 전반에서 사용하는 순수 Python 기반 한글 유틸리티 계층입니다.
분해 공식은 한글 음절 블록(``U+AC00``-``U+D7A3``)에 대한 유니코드 표준을 따르며,
해당 범위의 모든 음절에 대해 ``compose(*decompose(c)) == c``인 완전한 라운드 트립을 보장합니다.
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
    """``None`` 및 ``str``이 아닌 입력을 :class:`InvalidInputError`로 거부합니다."""
    if value is None:
        raise InvalidInputError(f"{field} must not be None")
    if not isinstance(value, str):
        raise InvalidInputError(f"{field} must be str, got {type(value).__name__}")
    return value


def _is_hangul_syllable(char: str) -> bool:
    """*char*가 완성된 한글 음절 하나인 경우 ``True``를 반환합니다."""
    return len(char) == 1 and _HANGUL_BASE <= ord(char) <= _HANGUL_LAST


def decompose(char: str) -> JamoComponents:
    """한글 음절 하나를 (초성, 중성, 종성)으로 분해합니다.

    인자:
        char: ``U+AC00``-``U+D7A3`` 범위의 완성된 한글 음절 하나.

    반환:
        종성이 없는 음절의 경우 ``jongseong`` 필드가 빈 문자열인
        :class:`JamoComponents`.

    예외:
        InvalidInputError: ``char``가 ``None``이거나 문자열이 아니거나, 정확히
            한 문자가 아니거나, 한글 음절이 아닌 경우.
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
    """초성, 중성, (선택적) 종성 자모를 하나의 음절로 조합합니다.

    인자:
        choseong: 초성 자모 (:data:`CHOSEONG_TABLE`에 존재해야 합니다).
        jungseong: 중성 자모 (:data:`JUNGSEONG_TABLE`에 존재해야 합니다).
        jongseong: 종성 자모 또는 종성 없음을 나타내는 빈 문자열
            (:data:`JONGSEONG_TABLE`에 존재해야 합니다).

    반환:
        조합된 한글 음절. ``U+AC00``-``U+D7A3`` 범위의 모든 ``c``에 대해
        ``compose(*decompose(c)) == c``가 성립합니다.

    예외:
        InvalidInputError: 인자 중 하나가 누락되었거나 문자열이 아니거나,
            해당 위치의 유효한 자모가 아닌 경우.
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
    """*text*의 초성만 추출하여 반환합니다.

    완성된 한글 음절은 초성으로 대체되며, 그 외 모든 문자(라틴, 숫자,
    공백, 자모, 구두점 등)는 그대로 유지됩니다. 초성 검색 및 오타 교정에
    유용합니다.

    인자:
        text: 임의의 텍스트. 빈 문자열을 입력하면 빈 문자열을 반환합니다.

    반환:
        *text*와 같은 길이의 문자열로, 한글 음절은 해당 초성으로 대체됩니다.

    예외:
        InvalidInputError: ``text``가 ``None``이거나 문자열이 아닌 경우.
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
    """*code*가 일반적인 CJK 한자 블록 중 하나에 속하면 ``True``를 반환합니다."""
    return (
        0x4E00 <= code <= 0x9FFF  # CJK 통합 한자
        or 0x3400 <= code <= 0x4DBF  # CJK 확장 A
        or 0x20000 <= code <= 0x2A6DF  # CJK 확장 B
        or 0x2A700 <= code <= 0x2B73F  # CJK 확장 C
        or 0x2B740 <= code <= 0x2B81F  # CJK 확장 D
        or 0x2B820 <= code <= 0x2CEAF  # CJK 확장 E
        or 0xF900 <= code <= 0xFAFF  # CJK 호환 한자
    )


def _is_hangul_jamo(code: int) -> bool:
    """자모 블록에 속하면 ``True``를 반환합니다 (완성 음절은 제외)."""
    return (
        0x1100 <= code <= 0x11FF  # 한글 자모
        or 0x3130 <= code <= 0x318F  # 한글 호환 자모
        or 0xA960 <= code <= 0xA97F  # 한글 자모 확장-A
        or 0xD7B0 <= code <= 0xD7FF  # 한글 자모 확장-B
    )


def _is_latin(code: int) -> bool:
    """ASCII 알파벳 및 라틴 확장 범위에 속하면 ``True``를 반환합니다."""
    if 0x41 <= code <= 0x5A or 0x61 <= code <= 0x7A:
        return True
    return (
        0x00C0 <= code <= 0x024F  # 라틴-1 보충, 확장-A/B
        or 0x1E00 <= code <= 0x1EFF  # 라틴 확장 추가
    )


def classify_char(char: str) -> CharType:
    """단일 문자를 :class:`CharType` 버킷 중 하나로 분류합니다.

    인자:
        char: 정확히 하나의 유니코드 코드 포인트.

    반환:
        해당하는 :class:`CharType` 값. 인식된 스크립트에 해당하지 않는
        코드 포인트는 ``OTHER``로 분류됩니다.

    예외:
        InvalidInputError: ``char``가 ``None``이거나 문자열이 아니거나,
            정확히 한 문자가 아닌 경우.
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
        # 스크립트에 속하지 않는 알파/숫자 코드 포인트 (예: 전각 숫자) — 가장 가까운 분류로 처리합니다.
        if category.isdigit():
            return CharType.NUMBER
        return CharType.OTHER
    if not text.isprintable():
        return CharType.OTHER
    # 구두점 / 기호 / 수학 연산자는 여기에 해당합니다.
    return CharType.SYMBOL

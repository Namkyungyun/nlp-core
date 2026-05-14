"""``bpmg_korean_nlp.normalizer.KoreanNormalizer`` 테스트."""

from __future__ import annotations

import unicodedata

import pytest

from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.normalizer import KoreanNormalizer


def test_nfc_normalization(normalizer: KoreanNormalizer) -> None:
    """NFD로 분해된 문자열이 NFC로 정규화됩니다."""
    nfd = unicodedata.normalize("NFD", "한국어")
    assert nfd != "한국어"
    assert normalizer.normalize(nfd) == "한국어"


def test_idempotent_on_nfc(normalizer: KoreanNormalizer) -> None:
    """이미 NFC인 문자열은 변경되지 않습니다 (공백 변환 제외)."""
    assert normalizer.normalize("한국어") == "한국어"


@pytest.mark.parametrize("ws", [" ", " ", "　"])  # noqa: RUF001
def test_unicode_whitespace_folded_to_ascii(normalizer: KoreanNormalizer, ws: str) -> None:
    """비중단 공백, em-공백, 전각 공백이 모두 ASCII 공백으로 변환됩니다."""
    out = normalizer.normalize(f"가{ws}나")
    assert out == "가 나"


def test_collapses_multiple_spaces(normalizer: KoreanNormalizer) -> None:
    """연속된 공백이 단일 ASCII 공백으로 압축됩니다."""
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
    """soynlp ``repeat_normalize``가 ``num_repeats=2``로 적용됩니다."""
    assert normalizer.normalize(raw) == expected


def test_empty_string_returns_empty(normalizer: KoreanNormalizer) -> None:
    assert normalizer.normalize("") == ""


def test_whitespace_only_returns_empty(normalizer: KoreanNormalizer) -> None:
    """공백만 있는 입력은 압축되고 제거되어 빈 문자열이 됩니다."""
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
    """사용자 정의 치환은 파이프라인의 나머지 처리 후 실행됩니다."""
    nz = KoreanNormalizer(
        custom_substitutions=[
            (r"AAA", "BBB"),
            (r"BBB", "CCC"),
        ]
    )
    assert nz.normalize("AAA test") == "CCC test"


def test_custom_substitutions_empty_default() -> None:
    """사용자 정의 치환 없음 = 고정된 파이프라인 외의 재작성 없음."""
    nz = KoreanNormalizer()
    assert nz.normalize("hello world") == "hello world"


def test_default_classmethod_returns_normalizer() -> None:
    nz = KoreanNormalizer.default()
    assert isinstance(nz, KoreanNormalizer)


def test_hanja_to_hangul_off_by_default(normalizer: KoreanNormalizer) -> None:
    """기본 정책: 한자는 그대로 보존됩니다."""
    out = normalizer.normalize("國家")
    assert out == "國家"


def test_hanja_to_hangul_on_no_op_without_optional_pkg() -> None:
    """선택적 패키지가 없으면 ``hanja_to_hangul=True``는 no-op입니다.

    이 플래그는 예외를 발생시켜서는 안 됩니다 — 구현은 텍스트를 변경 없이 두고
    단일 로그 경고를 발생시키는 방식으로 폴백합니다.
    """
    nz = KoreanNormalizer(hanja_to_hangul=True)
    try:
        import hanja  # noqa: F401
    except ImportError:
        # 선택적 패키지 없음 — 텍스트가 변경 없이 통과합니다.
        assert nz.normalize("國家") == "國家"
    else:
        # 패키지가 설치된 경우 출력은 한글이며, str인지만 확인합니다.
        assert isinstance(nz.normalize("國家"), str)


def test_combined_pipeline(normalizer: KoreanNormalizer) -> None:
    """모든 고정 단계가 대표적인 지저분한 입력에 대해 순서대로 실행됩니다."""
    raw = "  ㅋㅋㅋㅋ　안녕  하세요   "
    assert normalizer.normalize(raw) == "ㅋㅋ 안녕 하세요"


# ---------------------------------------------------------------------------
# strip_noise 옵션
# ---------------------------------------------------------------------------


def test_strip_noise_removes_punctuation() -> None:
    """``strip_noise=True``이면 구두점(!, ?, .)이 제거됩니다."""
    nz = KoreanNormalizer(strip_noise=True)
    out = nz.normalize("안녕하세요! 반갑습니다?")
    assert "!" not in out
    assert "?" not in out
    # Core text should remain
    assert "안녕하세요" in out
    assert "반갑습니다" in out


def test_strip_noise_removes_emoji() -> None:
    """``strip_noise=True``이면 이모지 문자가 제거됩니다."""
    nz = KoreanNormalizer(strip_noise=True)
    out = nz.normalize("좋아요😀 대박👍")
    assert "😀" not in out
    assert "👍" not in out
    assert "좋아요" in out
    assert "대박" in out


def test_strip_noise_removes_jamo_emoticon() -> None:
    """``strip_noise=True``이면 독립 자모(ㅋㅋ, ㅠㅠ)가 제거됩니다."""
    nz = KoreanNormalizer(strip_noise=True)
    out = nz.normalize("재밌다ㅋㅋ 슬프다ㅠㅠ")
    assert "ㅋ" not in out
    assert "ㅠ" not in out
    assert "재밌다" in out
    assert "슬프다" in out


def test_strip_noise_default_off() -> None:
    """기본 ``strip_noise=False``는 구두점, 이모지, 자모를 보존합니다."""
    nz = KoreanNormalizer()  # strip_noise 기본값은 False
    out = nz.normalize("안녕! 😀 ㅋㅋㅋ")
    assert "!" in out
    assert "😀" in out
    assert "ㅋㅋ" in out


def test_strip_noise_empty_string() -> None:
    """``strip_noise=True``에서도 빈 입력은 여전히 빈 문자열을 반환합니다."""
    nz = KoreanNormalizer(strip_noise=True)
    assert nz.normalize("") == ""

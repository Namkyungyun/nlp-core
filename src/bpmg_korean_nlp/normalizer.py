"""korean-nlp-core 텍스트 정규화.

:class:`KoreanNormalizer`는 다운스트림 토큰화 또는 쿼리 분석 전에 한국어 입력
텍스트를 정리하는 고정 순서 파이프라인을 적용합니다:

    NFC  →  유니코드 공백 변환  →  공백 압축  →
    soynlp ``repeat_normalize``  →  (선택) 한자 → 한글  →
    (선택) 사용자 정의 정규식 치환  →
    (선택) 노이즈 제거 (구두점 / 기호 / 이모지 / 자모 감탄사)

기본 설정 — ``hanja_to_hangul=False`` 및 항상 활성화된 NFC +
``repeat_normalize`` 단계 — 은 팀 합의로 고정되어 있으며, SDK 전반에 걸친
조율 없이 변경해서는 안 됩니다.
"""

from __future__ import annotations

import logging
import re
import unicodedata
import warnings
from typing import Final

import regex  # type: ignore[import-untyped]
from soynlp.normalizer import repeat_normalize

from bpmg_korean_nlp.exceptions import InvalidInputError

__all__ = ["KoreanNormalizer"]

_logger = logging.getLogger(__name__)

_REPEAT_NUM: Final[int] = 2
_MULTI_SPACE_RE: Final[re.Pattern[str]] = re.compile(r" +")
_UNICODE_WS_RE: Final[regex.Pattern[str]] = regex.compile(r"\s")

# strip_noise=True 시 적용
_PUNCT_SYMBOL_RE: Final[regex.Pattern[str]] = regex.compile(r"[\p{P}\p{S}]")
_JAMO_NOISE_RE: Final[regex.Pattern[str]] = regex.compile(
    r"[ㄱ-ㆎㅥ-ㆆ]+"  # 한글 자모 (완성 음절 제외)
)


class KoreanNormalizer:
    """결정적(deterministic) 한국어 텍스트 정규화기.

    파이프라인은 고정되어 있습니다: NFC, 유니코드 공백 변환, 다중 공백 압축,
    ``num_repeats=2``인 ``soynlp.normalize.repeat_normalize``,
    선택적 한자→한글 음역, 선택적 사용자 정규식 규칙.

    인자:
        hanja_to_hangul: ``True``이면 한자 문자를 최선 노력으로 한글로 음역합니다.
            변환이 손실될 수 있으므로 실제로 텍스트를 재작성하는 각 호출에서
            경고가 발생합니다. 선택적 :mod:`hanja` 패키지가 필요하며,
            설치되어 있지 않으면 자동으로 ``False``로 처리됩니다.
        custom_substitutions: 파이프라인의 나머지 처리 후 :func:`re.sub`으로
            적용되는 ``(pattern, replacement)`` 튜플의 선택적 순서 목록.
        strip_noise: ``True``이면 파이프라인의 나머지 처리 후 구두점, 기호,
            이모지, 독립적인 한글 자모(예: ``ㅋ``, ``ㅎ``)를 제거합니다.
            기존 동작을 보존하기 위해 기본값은 ``False``입니다.

    예외:
        InvalidInputError: :meth:`normalize`에 ``None`` 값이나 ``str``이 아닌
            입력이 주어진 경우.
    """

    __slots__ = ("_custom_substitutions", "_hanja_to_hangul", "_strip_noise")

    def __init__(
        self,
        hanja_to_hangul: bool = False,
        custom_substitutions: list[tuple[str, str]] | None = None,
        strip_noise: bool = False,
    ) -> None:
        self._hanja_to_hangul: bool = hanja_to_hangul
        self._strip_noise: bool = strip_noise
        self._custom_substitutions: tuple[tuple[str, str], ...] = (
            tuple(custom_substitutions) if custom_substitutions else ()
        )

    @classmethod
    def default(cls) -> KoreanNormalizer:
        """고정된 기본 옵션으로 구성된 정규화기를 반환합니다."""
        return cls()

    def normalize(self, text: str) -> str:
        """*text*를 전체 파이프라인으로 정규화합니다.

        인자:
            text: 원시 입력 문자열.

        반환:
            정규화된 텍스트. 빈 입력은 빈 출력을 생성합니다.

        예외:
            InvalidInputError: *text*가 ``None``이거나 ``str``이 아닌 경우.
        """
        if not isinstance(text, str):
            raise InvalidInputError(
                f"KoreanNormalizer.normalize expects str, got {type(text).__name__}"
            )
        if not text:
            return ""

        out = unicodedata.normalize("NFC", text)
        out = _UNICODE_WS_RE.sub(" ", out)
        out = _MULTI_SPACE_RE.sub(" ", out).strip()
        out = repeat_normalize(out, num_repeats=_REPEAT_NUM)

        if self._hanja_to_hangul:
            out = self._convert_hanja(out)

        for pattern, replacement in self._custom_substitutions:
            out = re.sub(pattern, replacement, out)

        if self._strip_noise:
            out = _PUNCT_SYMBOL_RE.sub(" ", out)
            out = _JAMO_NOISE_RE.sub(" ", out)
            out = _MULTI_SPACE_RE.sub(" ", out).strip()

        return out

    @staticmethod
    def _convert_hanja(text: str) -> str:
        """최선 노력(best-effort) 한자→한글 음역.

        선택적 :mod:`hanja` 패키지가 설치되어 있지 않으면 *text*를 변경 없이
        반환합니다. 실제로 재작성이 발생하면 호출당 하나의 경고를 발생시킵니다
        (변환이 손실될 수 있음).
        """
        try:
            import hanja as _hanja  # type: ignore[import-not-found, unused-ignore]
        except ImportError:
            _logger.warning(
                "hanja_to_hangul=True requested but the 'hanja' package is not "
                "installed; leaving hanja characters unchanged"
            )
            return text

        converted = _hanja.translate(text, "substitution")
        if converted != text:
            warnings.warn(
                "hanja→hangul transliteration may be lossy",
                stacklevel=3,
            )
        return str(converted)

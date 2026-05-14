"""korean-nlp-core 예외 계층.

최상위 예외는 :class:`KoreanNlpError`이며, SDK에서 발생하는 모든 오류는
이를 상속하므로 단일 ``except`` 절로 전체 예외 군을 포착할 수 있습니다.
"""

from __future__ import annotations

__all__ = [
    "InvalidInputError",
    "KoreanNlpError",
    "MeCabNotAvailableError",
    "PIIDetectedError",
]


class KoreanNlpError(Exception):
    """korean-nlp-core에서 발생하는 모든 오류의 기반 클래스."""


class MeCabNotAvailableError(KoreanNlpError):
    """MeCab 사전 또는 런타임을 불러올 수 없을 때 발생합니다."""


class InvalidInputError(KoreanNlpError):
    """입력이 ``None``이거나 ``str`` 인스턴스가 아닐 때 발생합니다.

    빈 문자열은 *유효하지 않은 입력이 아닙니다* — 파이프라인을 통과하여
    빈 결과를 반환해야 합니다.
    """


class PIIDetectedError(KoreanNlpError):
    """입력 텍스트에서 하나 이상의 PII 패턴이 발견될 때 발생합니다.

    ``guardrail-core`` 이후 2차 필터 역할을 합니다. :attr:`matched`
    속성에는 트리거된 모든 패턴의 정식 이름이 나열됩니다.

    속성:
        matched: 일치한 PII 패턴 이름 목록 (예: ``["mobile_phone"]``).
    """

    def __init__(self, matched: list[str]) -> None:
        self.matched: list[str] = matched
        super().__init__(f"PII detected in input: {', '.join(matched)}")

"""korean-nlp-core 2차 PII 필터.

한국어 PII 정규식 패턴 카탈로그와 패턴이 일치하면 :class:`PIIDetectedError`를
발생시키는 차단 헬퍼 :func:`check_pii`를 제공합니다. ``guardrail-core`` 이후
안전망 역할을 하며 — 이를 **대체하지 않습니다**.

런타임 마스킹 또는 편집 기능을 여기에 추가해서는 안 됩니다.
"""

from __future__ import annotations

import re

from bpmg_korean_nlp.exceptions import PIIDetectedError
from bpmg_korean_nlp.models import PIIPattern

__all__ = ["PII_PATTERNS"]


PII_PATTERNS: tuple[PIIPattern, ...] = (
    PIIPattern(
        name="resident_id",
        description="주민등록번호",
        pattern=re.compile(r"\d{6}-[1-4]\d{6}"),
    ),
    PIIPattern(
        name="mobile_phone",
        description="휴대전화 번호",
        pattern=re.compile(r"01[016789]-\d{3,4}-\d{4}"),
    ),
    PIIPattern(
        name="business_id",
        description="사업자등록번호",
        pattern=re.compile(r"\d{3}-\d{2}-\d{5}"),
    ),
    PIIPattern(
        name="foreign_id",
        description="외국인등록번호",
        pattern=re.compile(r"\d{6}-[5-8]\d{6}"),
    ),
)


def check_pii(text: str) -> None:
    """*text*에 PII 패턴이 포함되어 있으면 :class:`PIIDetectedError`를 발생시킵니다.

    모든 :data:`PII_PATTERNS`를 스캔하고 일치하는 모든 패턴 이름을 수집합니다.
    단일 스캔 패스이므로 첫 번째 일치에서 실패하는 대신 여러 동시 일치를
    한 번에 모두 보고합니다.

    인자:
        text: 스캔할 입력 문자열.

    예외:
        PIIDetectedError: 하나 이상의 패턴이 일치하는 경우.
    """
    matched = [p.name for p in PII_PATTERNS if p.pattern.search(text)]
    if matched:
        raise PIIDetectedError(matched)

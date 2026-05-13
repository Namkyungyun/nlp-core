"""Secondary PII filter for korean-nlp-core.

Provides a catalogue of Korean PII regex patterns and a blocking helper
:func:`check_pii` that raises :class:`PIIDetectedError` when any pattern
matches. This acts as a safety net after ``guardrail-core`` — it does **not**
replace it.

Runtime masking or redaction must not be added here.
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
    """Raise :class:`PIIDetectedError` if *text* contains any PII pattern.

    Scans all :data:`PII_PATTERNS` and collects every matching pattern name.
    A single scan pass means multiple simultaneous matches are all reported
    at once rather than failing on the first hit.

    Args:
        text: The input string to scan.

    Raises:
        PIIDetectedError: When at least one pattern matches.
    """
    matched = [p.name for p in PII_PATTERNS if p.pattern.search(text)]
    if matched:
        raise PIIDetectedError(matched)

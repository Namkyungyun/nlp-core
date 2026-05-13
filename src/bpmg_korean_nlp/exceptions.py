"""Exception hierarchy for korean-nlp-core.

The top-level exception is :class:`KoreanNlpError`; all SDK-raised errors
inherit from it so that consumers can catch the entire family with a single
``except`` clause.
"""

from __future__ import annotations

__all__ = [
    "InvalidInputError",
    "KoreanNlpError",
    "MeCabNotAvailableError",
    "PIIDetectedError",
]


class KoreanNlpError(Exception):
    """Base class for every error raised by korean-nlp-core."""


class MeCabNotAvailableError(KoreanNlpError):
    """Raised when the MeCab dictionary or runtime cannot be loaded."""


class InvalidInputError(KoreanNlpError):
    """Raised when input is ``None`` or not a ``str`` instance.

    Empty strings are *not* invalid — they must flow through the pipeline
    and produce empty results.
    """


class PIIDetectedError(KoreanNlpError):
    """Raised when one or more PII patterns are found in the input text.

    Acts as a secondary filter after ``guardrail-core``. The :attr:`matched`
    attribute lists the canonical names of every pattern that triggered.

    Attributes:
        matched: Names of the PII patterns that matched (e.g. ``["mobile_phone"]``).
    """

    def __init__(self, matched: list[str]) -> None:
        self.matched: list[str] = matched
        super().__init__(f"PII detected in input: {', '.join(matched)}")

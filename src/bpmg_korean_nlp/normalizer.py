"""Text normalization for korean-nlp-core.

:class:`KoreanNormalizer` applies a fixed-order pipeline that cleans Korean
input text before downstream tokenization, spacing restoration, or query
analysis:

    NFC  →  Unicode whitespace folding  →  whitespace collapse  →
    soynlp ``repeat_normalize``  →  (optional) hanja → hangul  →
    (optional) user-supplied regex substitutions

The default settings — ``hanja_to_hangul=False`` and an always-on NFC plus
``repeat_normalize`` step — are locked by team agreement and must not be
loosened without a coordinated change across the SDK.
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


class KoreanNormalizer:
    """Deterministic Korean text normalizer.

    The pipeline is fixed: NFC, Unicode-whitespace folding, multi-whitespace
    collapse, ``soynlp.normalize.repeat_normalize`` with ``num_repeats=2``,
    optional hanja→hangul transliteration, and optional user regex rules.

    Args:
        hanja_to_hangul: When ``True``, hanja characters are transliterated to
            hangul as a best effort. The conversion can be lossy, so a warning
            is emitted on each call that actually rewrites text. Requires the
            optional :mod:`hanja` package; when it is not installed the
            argument is silently treated as ``False``.
        custom_substitutions: Optional ordered list of ``(pattern, replacement)``
            tuples applied with :func:`re.sub` after the rest of the pipeline.

    Raises:
        InvalidInputError: If :meth:`normalize` is given a ``None`` value or
            any non-``str`` input.
    """

    __slots__ = ("_custom_substitutions", "_hanja_to_hangul")

    def __init__(
        self,
        hanja_to_hangul: bool = False,
        custom_substitutions: list[tuple[str, str]] | None = None,
    ) -> None:
        self._hanja_to_hangul: bool = hanja_to_hangul
        self._custom_substitutions: tuple[tuple[str, str], ...] = (
            tuple(custom_substitutions) if custom_substitutions else ()
        )

    @classmethod
    def default(cls) -> KoreanNormalizer:
        """Return a normalizer configured with the locked default options."""
        return cls()

    def normalize(self, text: str) -> str:
        """Normalize *text* through the full pipeline.

        Args:
            text: Raw input string.

        Returns:
            Normalized text. An empty input produces an empty output.

        Raises:
            InvalidInputError: If *text* is ``None`` or not a ``str``.
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

        return out

    @staticmethod
    def _convert_hanja(text: str) -> str:
        """Best-effort hanja→hangul transliteration.

        Returns *text* unchanged when the optional :mod:`hanja` package is not
        installed; emits a single warning per call when an actual rewrite
        occurs (the transformation may be lossy).
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

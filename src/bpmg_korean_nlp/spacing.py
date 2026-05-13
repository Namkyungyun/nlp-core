"""Spacing restoration for korean-nlp-core.

:class:`SpacingRestorer` wraps a PyKoSpacing model behind a strict singleton:
loading the model is expensive (hundreds of milliseconds and significant
memory), so the SDK guarantees exactly one instance per process.

Sentence splitting is delegated to :mod:`kss` so the deep-learning model only
sees one sentence at a time, which is its supported input shape.
"""

from __future__ import annotations

from typing import ClassVar, Protocol

from bpmg_korean_nlp.exceptions import InvalidInputError, SpacingModelLoadError

__all__ = ["SpacingRestorer"]


class _SpacingFn(Protocol):
    """Structural type for the callable returned by ``pykospacing.Spacing()``."""

    def __call__(self, text: str, /) -> str: ...


class SpacingRestorer:
    """Process-wide singleton wrapping a PyKoSpacing model.

    Use :meth:`get_instance` to obtain the singleton. The class' constructor
    is internal — direct instantiation is supported only so the singleton
    cache can populate itself.

    Raises:
        SpacingModelLoadError: When the underlying PyKoSpacing model or its
            dependencies cannot be loaded.
        InvalidInputError: When :meth:`restore` is given a non-``str``.
    """

    _instance: ClassVar[SpacingRestorer | None] = None

    __slots__ = ("_spacing_fn",)

    def __init__(self) -> None:
        try:
            from pykospacing import Spacing
        except ImportError as exc:
            raise SpacingModelLoadError(
                "Failed to import 'pykospacing'; install the PyKoSpacing package"
            ) from exc

        try:
            spacing_fn: _SpacingFn = Spacing()
        except Exception as exc:
            raise SpacingModelLoadError(f"Failed to initialize PyKoSpacing model: {exc}") from exc

        self._spacing_fn: _SpacingFn = spacing_fn

    @classmethod
    def get_instance(cls) -> SpacingRestorer:
        """Return the process-wide :class:`SpacingRestorer` singleton.

        The first call loads the PyKoSpacing model; subsequent calls return
        the cached instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def restore(self, text: str) -> str:
        """Restore spacing for *text*.

        The input is split into sentences via :mod:`kss`, each sentence is
        fed through PyKoSpacing, and the results are joined with single
        spaces.

        Args:
            text: Korean text whose spacing should be corrected.

        Returns:
            Spacing-restored text. Empty input yields an empty string.

        Raises:
            InvalidInputError: If *text* is ``None`` or not a ``str``.
        """
        if not isinstance(text, str):
            raise InvalidInputError(
                f"SpacingRestorer.restore expects str, got {type(text).__name__}"
            )
        if not text:
            return ""

        import kss

        sentences = kss.split_sentences(text)
        if not sentences:
            return self._spacing_fn(text)
        return " ".join(self._spacing_fn(sentence) for sentence in sentences)

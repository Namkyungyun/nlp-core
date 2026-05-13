"""MeCab-based Korean morphological tokenizer.

The tokenizer wraps the ``python-mecab-ko`` binding (KoNLPy is forbidden
by project policy) and exposes two surface-facing methods:

* :meth:`MeCabTokenizer.tokenize` — ``list[str]`` for BM25 lexical
  retrieval, with optional POS filter and stopwords removal.
* :meth:`MeCabTokenizer.analyze` — ``list[MorphToken]`` carrying
  ``surface`` / ``lemma`` / ``pos`` / ``(start, end)`` character offsets
  for graph extraction and explainability.

Because loading mecab-ko-dic is expensive (tens of MB, hundreds of ms),
instances are cached on the class keyed by ``(dict_path, user_dict_path)``
— the dictionary is initialized at most once per configuration per
process. Both ``MeCabTokenizer(...)`` and :meth:`get_instance` resolve
to the same cached object.
"""

from __future__ import annotations

import threading
from typing import Any, ClassVar

from bpmg_korean_nlp.exceptions import InvalidInputError, MeCabNotAvailableError
from bpmg_korean_nlp.models import MorphToken
from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS

__all__ = ["MeCabTokenizer"]


_InstanceKey = tuple[str | None, str | None]


def _ensure_str(text: object, *, name: str = "text") -> str:
    """Validate that *text* is a ``str``; raise :class:`InvalidInputError` otherwise.

    Empty strings are valid (they flow through and produce empty results).
    """
    if not isinstance(text, str):
        raise InvalidInputError(f"{name} must be a str, got {type(text).__name__}")
    return text


def _load_mecab(dict_path: str | None, user_dict_path: str | None) -> Any:
    """Construct an underlying ``mecab.MeCab`` instance or raise."""
    try:
        from mecab import MeCab as _MeCab
    except ImportError as exc:
        raise MeCabNotAvailableError(
            "python-mecab-ko is not installed. Install it with: pip install python-mecab-ko"
        ) from exc

    try:
        kwargs: dict[str, Any] = {}
        if dict_path is not None:
            kwargs["dictionary_path"] = dict_path
        if user_dict_path is not None:
            kwargs["user_dictionary_path"] = user_dict_path
        return _MeCab(**kwargs)
    except MeCabNotAvailableError:
        raise
    except Exception as exc:
        raise MeCabNotAvailableError(
            f"Failed to initialize MeCab (dict_path={dict_path!r}): {exc}"
        ) from exc


class MeCabTokenizer:
    """MeCab-based morphological tokenizer for Korean.

    Args:
        dict_path: Optional explicit path to ``mecab-ko-dic``. When
            ``None``, MeCab auto-detects the system default location.
        user_dict_path: Optional user dictionary path to merge.

    Raises:
        MeCabNotAvailableError: If the ``python-mecab-ko`` binding or
            ``mecab-ko-dic`` cannot be loaded.

    The instance is cached per ``(dict_path, user_dict_path)``; repeated
    construction returns the same object and skips re-initialization.
    """

    _instances: ClassVar[dict[_InstanceKey, MeCabTokenizer]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    _initialized: bool
    _dict_path: str | None
    _user_dict_path: str | None
    _mecab: Any

    def __new__(
        cls,
        dict_path: str | None = None,
        user_dict_path: str | None = None,
    ) -> MeCabTokenizer:
        key: _InstanceKey = (dict_path, user_dict_path)
        with cls._lock:
            cached = cls._instances.get(key)
            if cached is not None:
                return cached
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
            return instance

    def __init__(
        self,
        dict_path: str | None = None,
        user_dict_path: str | None = None,
    ) -> None:
        if self._initialized:
            return
        try:
            self._dict_path = dict_path
            self._user_dict_path = user_dict_path
            self._mecab = _load_mecab(dict_path, user_dict_path)
            self._initialized = True
        except Exception:
            key: _InstanceKey = (dict_path, user_dict_path)
            with self.__class__._lock:
                if self.__class__._instances.get(key) is self:
                    del self.__class__._instances[key]
            raise

    @classmethod
    def get_instance(
        cls,
        dict_path: str | None = None,
        user_dict_path: str | None = None,
    ) -> MeCabTokenizer:
        """Return the shared :class:`MeCabTokenizer` for the given configuration.

        Equivalent to calling the constructor; provided as a named entry
        point so callers can spell their intent ("fetch the cached
        singleton") explicitly.
        """
        return cls(dict_path=dict_path, user_dict_path=user_dict_path)

    @classmethod
    def reset_instances(cls) -> None:
        """Clear the per-config singleton cache. Test-only utility."""
        with cls._lock:
            cls._instances.clear()

    @property
    def dict_path(self) -> str | None:
        """The dictionary path this tokenizer was initialized with."""
        return self._dict_path

    @property
    def user_dict_path(self) -> str | None:
        """The user-dictionary path this tokenizer was initialized with."""
        return self._user_dict_path

    def tokenize(
        self,
        text: str,
        pos_filter: frozenset[str] | None = None,
        remove_stopwords: bool = False,
        stopwords: frozenset[str] | None = None,
    ) -> list[str]:
        """Tokenize *text* into a flat list of surface morphemes.

        Args:
            text: Input string. ``""`` is valid and returns ``[]``.
            pos_filter: If given, only morphemes whose primary Sejong POS tag is
                in the set are kept. Compound tags (e.g. ``"NNG+JKS"``) are matched
                on their first component. ``None`` keeps every POS.
            remove_stopwords: When ``True``, drop tokens whose surface
                form is in *stopwords* (or :data:`DEFAULT_STOPWORDS` if
                *stopwords* is ``None``).
            stopwords: Custom stopword set. Ignored when
                ``remove_stopwords`` is ``False``.

        Returns:
            BM25-ready list of surface tokens, in document order.

        Raises:
            InvalidInputError: If *text* is not a ``str``.
            MeCabNotAvailableError: If MeCab fails during analysis.
        """
        text = _ensure_str(text)
        if not text:
            return []

        morphs = self._mecab_pos(text)
        active_stopwords: frozenset[str] | None
        if remove_stopwords:
            active_stopwords = stopwords if stopwords is not None else DEFAULT_STOPWORDS
        else:
            active_stopwords = None

        result: list[str] = []
        for surface, pos in morphs:
            if pos_filter is not None and pos.split("+")[0] not in pos_filter:
                continue
            if active_stopwords is not None and surface in active_stopwords:
                continue
            result.append(surface)
        return result

    def analyze(self, text: str) -> list[MorphToken]:
        """Return rich morphological analysis of *text*.

        Each :class:`MorphToken` carries the surface form, a best-effort
        lemma (currently the surface itself), the Sejong POS tag, and
        the inclusive/exclusive ``(start, end)`` character offsets in
        the original input.

        Args:
            text: Input string. ``""`` is valid and returns ``[]``.

        Returns:
            Morpheme tokens in document order.

        Raises:
            InvalidInputError: If *text* is not a ``str``.
            MeCabNotAvailableError: If MeCab fails during analysis.
        """
        text = _ensure_str(text)
        if not text:
            return []

        morphs = self._mecab_pos(text)

        result: list[MorphToken] = []
        cursor = 0
        for surface, pos in morphs:
            start, end = self._locate(text, surface, cursor)
            cursor = end if start >= 0 else cursor
            if start < 0:
                start = cursor
                end = cursor + len(surface)
                cursor = end
            result.append(
                MorphToken(
                    surface=surface,
                    lemma=surface,
                    pos=pos,
                    start=start,
                    end=end,
                )
            )
        return result

    @staticmethod
    def _locate(text: str, surface: str, cursor: int) -> tuple[int, int]:
        """Find *surface* in *text* at/after *cursor*; return ``(-1, -1)`` if absent.

        Falling back to a global search keeps offsets monotone even when
        MeCab emits a morpheme whose surface form was canonicalised
        (rare with ``mecab-ko-dic`` but possible at sentence boundaries).
        """
        if not surface:
            return -1, -1
        idx = text.find(surface, cursor)
        if idx < 0:
            idx = text.find(surface)
        if idx < 0:
            return -1, -1
        return idx, idx + len(surface)

    def _mecab_pos(self, text: str) -> list[tuple[str, str]]:
        """Run MeCab POS analysis and return ``[(surface, pos_tag), ...]``.

        Normalizes the wider variety of return shapes seen across
        ``python-mecab-ko`` releases (plain tuples vs ``Morpheme``-like
        objects) into a single ``(str, str)`` tuple form. Compound POS
        tags (``"NNG+JKS"``) are preserved verbatim.
        """
        try:
            raw = self._mecab.pos(text)
        except Exception as exc:
            raise MeCabNotAvailableError(f"MeCab failed to analyze text: {exc}") from exc

        out: list[tuple[str, str]] = []
        for entry in raw:
            try:
                surface = entry[0]
                pos = entry[1]
            except (IndexError, TypeError, KeyError):
                continue
            if not isinstance(surface, str) or not isinstance(pos, str):
                continue
            out.append((surface, pos))
        return out

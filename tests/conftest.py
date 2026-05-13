"""Shared pytest fixtures for the korean-nlp-core test suite.

Most logic tests use DI fakes (see ``FakeTokenizer`` /
``FakeNormalizer``) so they run anywhere — including CI environments that
lack MeCab. Tests that genuinely require those heavy
dependencies are guarded by the ``real_mecab`` fixture,
which skips cleanly when the binding is not importable.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from bpmg_korean_nlp.models import MorphToken
    from bpmg_korean_nlp.normalizer import KoreanNormalizer
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer


def _has_mecab() -> bool:
    """Return ``True`` iff the ``python-mecab-ko`` binding imports."""
    try:
        import mecab  # noqa: F401
    except ImportError:
        return False
    return True


HAS_MECAB: bool = _has_mecab()


# ---------------------------------------------------------------------------
# Pure-Python fixtures (no heavy deps)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def normalizer() -> KoreanNormalizer:
    """Locked-default KoreanNormalizer (NFC, repeat_normalize, whitespace)."""
    from bpmg_korean_nlp.normalizer import KoreanNormalizer

    return KoreanNormalizer.default()


# ---------------------------------------------------------------------------
# Heavy-dep fixtures (skip when MeCab missing)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_tokenizer() -> MeCabTokenizer:
    """Session-scoped real MeCab tokenizer; skip when the binding is missing."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko binding not installed")
    from bpmg_korean_nlp.exceptions import MeCabNotAvailableError
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    try:
        return MeCabTokenizer.get_instance()
    except MeCabNotAvailableError as exc:
        pytest.skip(f"MeCab dictionary not available: {exc}")


@pytest.fixture(scope="session")
def real_query_analyzer(
    real_tokenizer: MeCabTokenizer,
) -> QueryAnalyzer:
    """Real QueryAnalyzer using the actual MeCab singleton."""
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    return QueryAnalyzer(
        tokenizer=real_tokenizer,
    )


# ---------------------------------------------------------------------------
# DI fakes — used wherever pipeline logic is verified independently of MeCab
# ---------------------------------------------------------------------------


class FakeNormalizer:
    """Pass-through normalizer for DI-based pipeline tests."""

    def __init__(
        self,
        transform: Callable[[str], str] | None = None,
    ) -> None:
        self._transform = transform

    def normalize(self, text: str) -> str:
        if self._transform is None:
            return text.strip()
        return self._transform(text)


class FakeTokenizer:
    """Configurable in-memory tokenizer for QueryAnalyzer pipeline tests."""

    def __init__(
        self,
        tokens: list[tuple[str, str]] | None = None,
    ) -> None:
        # tokens is a list of (surface, pos) pairs.
        self._tokens: list[tuple[str, str]] = tokens or []

    def configure(self, tokens: list[tuple[str, str]]) -> None:
        """Replace the configured (surface, pos) sequence."""
        self._tokens = tokens

    def tokenize(
        self,
        text: str,
        pos_filter: frozenset[str] | None = None,
        remove_stopwords: bool = False,
        stopwords: frozenset[str] | None = None,
    ) -> list[str]:
        from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS

        active_stop = (
            (stopwords if stopwords is not None else DEFAULT_STOPWORDS)
            if remove_stopwords
            else None
        )
        out: list[str] = []
        for surface, pos in self._tokens:
            if pos_filter is not None and pos.split("+")[0] not in pos_filter:
                continue
            if active_stop is not None and surface in active_stop:
                continue
            out.append(surface)
        return out

    def analyze(self, text: str) -> list[MorphToken]:
        from bpmg_korean_nlp.models import MorphToken

        result: list[MorphToken] = []
        cursor = 0
        for surface, pos in self._tokens:
            start = text.find(surface, cursor)
            if start < 0:
                start = cursor
            end = start + len(surface)
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


@pytest.fixture
def fake_normalizer() -> FakeNormalizer:
    """Fresh pass-through normalizer per test."""
    return FakeNormalizer()


@pytest.fixture
def fake_tokenizer() -> FakeTokenizer:
    """Fresh empty fake tokenizer per test — configure via ``.configure(...)``."""
    return FakeTokenizer()


@pytest.fixture
def di_query_analyzer(
    fake_normalizer: FakeNormalizer,
    fake_tokenizer: FakeTokenizer,
) -> QueryAnalyzer:
    """QueryAnalyzer wired entirely from fakes (MeCab not required)."""
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    return QueryAnalyzer(
        normalizer=fake_normalizer,  # type: ignore[arg-type]
        tokenizer=fake_tokenizer,  # type: ignore[arg-type]
    )


@pytest.fixture(autouse=True)
def _reset_default_analyzer() -> Iterator[None]:
    """Clear the module-level default QueryAnalyzer between tests.

    Prevents a fake-DI test from leaving a partially-mocked singleton
    behind that a later test might accidentally re-use.
    """
    yield
    try:
        from bpmg_korean_nlp import query_analyzer as qa_module

        qa_module._default_analyzer = None
    except ImportError:
        pass

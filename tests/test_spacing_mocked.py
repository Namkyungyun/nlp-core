"""Wrapper-level tests for :class:`SpacingRestorer` using a stub PyKoSpacing.

PyKoSpacing is not on PyPI in some environments; mocking the module gives
us full coverage of the wrapper logic (singleton, validation, sentence
splitting, error paths) without depending on the actual model.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import Any, ClassVar

import pytest

from bpmg_korean_nlp.exceptions import InvalidInputError, SpacingModelLoadError


class _StubSpacing:
    """An identity spacing callable that records its inputs."""

    raise_on_init: ClassVar[Exception | None] = None

    def __init__(self) -> None:
        if self.raise_on_init is not None:
            raise self.raise_on_init
        self.seen: list[str] = []

    def __call__(self, text: str) -> str:
        self.seen.append(text)
        return text.replace("X", " X ").strip()


def _make_pykospacing_module(klass: type) -> Any:
    class _StubModule:
        Spacing = klass

    return _StubModule()


def _patch_pykospacing(monkeypatch: pytest.MonkeyPatch, klass: type) -> None:
    monkeypatch.setitem(sys.modules, "pykospacing", _make_pykospacing_module(klass))


class _StubKss:
    """A trivial kss replacement that splits on the literal ``"|"`` char.

    Sentence splitting is irrelevant to the singleton/validation paths,
    so we stub it to a deterministic behaviour for these tests.
    """

    @staticmethod
    def split_sentences(text: str) -> list[str]:
        if not text:
            return []
        return text.split("|")


def _patch_kss(monkeypatch: pytest.MonkeyPatch, klass: type) -> None:
    monkeypatch.setitem(sys.modules, "kss", klass())


@pytest.fixture(autouse=True)
def _reset_spacing_singleton() -> Iterator[None]:
    """Reset the SpacingRestorer singleton so each test gets a fresh instance."""
    from bpmg_korean_nlp.spacing import SpacingRestorer

    SpacingRestorer._instance = None
    yield
    SpacingRestorer._instance = None


def test_construct_with_stub_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """A working PyKoSpacing stub allows construction."""
    _patch_pykospacing(monkeypatch, _StubSpacing)
    from bpmg_korean_nlp.spacing import SpacingRestorer

    SpacingRestorer()  # must not raise


def test_get_instance_returns_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_pykospacing(monkeypatch, _StubSpacing)
    from bpmg_korean_nlp.spacing import SpacingRestorer

    a = SpacingRestorer.get_instance()
    b = SpacingRestorer.get_instance()
    assert a is b


def test_init_failure_wraps_in_spacing_model_load_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model construction failure becomes :class:`SpacingModelLoadError`."""

    class _BoomSpacing(_StubSpacing):
        raise_on_init = RuntimeError("nope")

    _patch_pykospacing(monkeypatch, _BoomSpacing)
    from bpmg_korean_nlp.spacing import SpacingRestorer

    with pytest.raises(SpacingModelLoadError):
        SpacingRestorer()


def test_restore_empty_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_pykospacing(monkeypatch, _StubSpacing)
    from bpmg_korean_nlp.spacing import SpacingRestorer

    assert SpacingRestorer.get_instance().restore("") == ""


def test_restore_rejects_non_str(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_pykospacing(monkeypatch, _StubSpacing)
    from bpmg_korean_nlp.spacing import SpacingRestorer

    with pytest.raises(InvalidInputError):
        SpacingRestorer.get_instance().restore(None)  # type: ignore[arg-type]
    with pytest.raises(InvalidInputError):
        SpacingRestorer.get_instance().restore(42)  # type: ignore[arg-type]


def test_restore_uses_sentence_splitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sentences are routed through the model individually then joined."""
    _patch_pykospacing(monkeypatch, _StubSpacing)
    _patch_kss(monkeypatch, _StubKss)
    from bpmg_korean_nlp.spacing import SpacingRestorer

    out = SpacingRestorer.get_instance().restore("abc|def")
    assert "abc" in out
    assert "def" in out


def test_restore_handles_empty_sentence_split(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When kss returns an empty list, the model is still applied to the text."""

    class _EmptyKss:
        @staticmethod
        def split_sentences(text: str) -> list[str]:
            return []

    _patch_pykospacing(monkeypatch, _StubSpacing)
    _patch_kss(monkeypatch, _EmptyKss)
    from bpmg_korean_nlp.spacing import SpacingRestorer

    out = SpacingRestorer.get_instance().restore("abc")
    assert isinstance(out, str)

"""Mocked tests for :func:`check_mecab_dict` — exercises the success branches."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from bpmg_korean_nlp.mecab_check import check_mecab_dict


class _OkStub:
    def __init__(
        self,
        dictionary_path: str | None = None,
    ) -> None:
        self.dictionary_path = dictionary_path

    def pos(self, text: str) -> list[tuple[str, str]]:
        return [(text, "NNG")]


class _FailingPos(_OkStub):
    def pos(self, text: str) -> list[tuple[str, str]]:
        raise RuntimeError("boom")


def _module_with(klass: type) -> Any:
    class _Mod:
        MeCab = klass

    return _Mod()


@pytest.fixture(autouse=True)
def _restore_modules() -> Iterator[None]:
    saved = sys.modules.get("mecab")
    yield
    if saved is None:
        sys.modules.pop("mecab", None)
    else:
        sys.modules["mecab"] = saved


def test_success_path_reports_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """A working stub yields ``available=True`` and a clean error field."""
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_OkStub))
    result = check_mecab_dict(dict_path="/explicit/path")
    assert result.available is True
    assert result.error is None
    assert result.dict_path == "/explicit/path"


def test_pos_failure_reports_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A stub that raises in ``pos`` produces a failure result."""
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_FailingPos))
    result = check_mecab_dict(dict_path="/x")
    assert result.available is False
    assert result.error is not None


def test_version_parsed_from_dicrc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``check_mecab_dict`` reads the ``version`` field from ``dicrc``."""
    dict_dir = tmp_path / "mecab-ko-dic"
    dict_dir.mkdir()
    (dict_dir / "dicrc").write_text(
        ";\n; comment\nversion = 2.1.1-20180720\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_OkStub))
    result = check_mecab_dict(dict_path=str(dict_dir))
    assert result.available is True
    assert result.version == "2.1.1-20180720"


def test_dicrc_without_version_returns_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A ``dicrc`` without a ``version=`` line leaves ``version=None``."""
    dict_dir = tmp_path / "mecab-ko-dic"
    dict_dir.mkdir()
    (dict_dir / "dicrc").write_text(
        "; only comments\nother_key = value\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_OkStub))
    result = check_mecab_dict(dict_path=str(dict_dir))
    assert result.available is True
    assert result.version is None


def test_missing_dicrc_returns_none_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A dictionary directory without ``dicrc`` leaves ``version=None``."""
    dict_dir = tmp_path / "mecab-ko-dic"
    dict_dir.mkdir()
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_OkStub))
    result = check_mecab_dict(dict_path=str(dict_dir))
    assert result.available is True
    assert result.version is None


def test_default_dict_path_detection_with_real_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When no explicit path is given, the well-known list is probed."""
    fake_dict = tmp_path / "mecab-ko-dic"
    fake_dict.mkdir()
    (fake_dict / "dicrc").write_text("version = test-1\n", encoding="utf-8")

    # Patch the module-level default candidate list to include our fake.
    from bpmg_korean_nlp import mecab_check as mc_module

    monkeypatch.setattr(
        mc_module,
        "_DEFAULT_DICT_PATHS",
        (str(fake_dict),),
    )
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_OkStub))
    result = check_mecab_dict()
    assert result.available is True
    assert result.dict_path == str(fake_dict)
    assert result.version == "test-1"

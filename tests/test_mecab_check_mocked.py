""":func:`check_mecab_dict` 모킹 테스트 — 성공 브랜치를 검증합니다."""

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
    """동작하는 스텁은 ``available=True``와 깨끗한 오류 필드를 반환합니다."""
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_OkStub))
    result = check_mecab_dict(dict_path="/explicit/path")
    assert result.available is True
    assert result.error is None
    assert result.dict_path == "/explicit/path"


def test_pos_failure_reports_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """``pos``에서 예외를 발생시키는 스텁은 실패 결과를 생성합니다."""
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_FailingPos))
    result = check_mecab_dict(dict_path="/x")
    assert result.available is False
    assert result.error is not None


def test_version_parsed_from_dicrc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``check_mecab_dict``는 ``dicrc``에서 ``version`` 필드를 읽습니다."""
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
    """``version=`` 줄이 없는 ``dicrc``는 ``version=None``을 남깁니다."""
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
    """``dicrc``가 없는 사전 디렉터리는 ``version=None``을 남깁니다."""
    dict_dir = tmp_path / "mecab-ko-dic"
    dict_dir.mkdir()
    monkeypatch.setitem(sys.modules, "mecab", _module_with(_OkStub))
    result = check_mecab_dict(dict_path=str(dict_dir))
    assert result.available is True
    assert result.version is None


def test_default_dict_path_detection_with_real_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """명시적 경로가 주어지지 않으면 잘 알려진 목록을 탐색합니다."""
    fake_dict = tmp_path / "mecab-ko-dic"
    fake_dict.mkdir()
    (fake_dict / "dicrc").write_text("version = test-1\n", encoding="utf-8")

    # 모듈 수준의 기본 후보 목록에 가짜 경로를 포함하도록 패치합니다.
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

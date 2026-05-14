"""스텁 mecab 모듈을 사용한 :class:`MeCabTokenizer` 래퍼 수준 테스트.

실제 ``python-mecab-ko`` 바인딩은 모든 환경에서 사용 가능하지 않을 수 있는
시스템 C 의존성이 필요합니다; 래퍼 로직(POS 디스패치, 오프셋 계산, 오류 경로)의
완전한 커버리지를 위해 ``sys.modules['mecab']``에 스텁 모듈을 설치하여
래퍼가 프로덕션과 동일한 코드 경로를 실행하도록 합니다.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import Any, ClassVar

import pytest

from bpmg_korean_nlp.exceptions import InvalidInputError, MeCabNotAvailableError
from bpmg_korean_nlp.models import MorphToken


class _StubMeCabBase:
    """``pos()`` 계약을 준수하는 구성 가능한 MeCab 모조품."""

    pos_results: ClassVar[list[tuple[str, str]]] = []
    raise_on_pos: ClassVar[Exception | None] = None
    init_failure: ClassVar[Exception | None] = None

    def __init__(
        self,
        dictionary_path: str | None = None,
        user_dictionary_path: str | None = None,
    ) -> None:
        if self.init_failure is not None:
            raise self.init_failure
        self.dictionary_path = dictionary_path
        self.user_dictionary_path = user_dictionary_path

    def pos(self, text: str) -> list[tuple[str, str]]:
        if self.raise_on_pos is not None:
            raise self.raise_on_pos
        return list(self.pos_results)


def _make_stub_module(klass: type) -> Any:
    """``MeCab``을 노출하는 모듈 형태의 객체를 생성합니다."""

    class _StubModule:
        MeCab = klass

    return _StubModule()


def _patch_mecab(monkeypatch: pytest.MonkeyPatch, klass: type) -> None:
    """테스트 기간 동안 *klass*를 ``mecab.MeCab``으로 설치합니다."""
    monkeypatch.setitem(sys.modules, "mecab", _make_stub_module(klass))


@pytest.fixture(autouse=True)
def _reset_tokenizer_cache() -> Iterator[None]:
    """스텁이 적용되도록 모든 테스트 전후에 싱글톤 캐시를 초기화합니다."""
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    MeCabTokenizer.reset_instances()
    yield
    MeCabTokenizer.reset_instances()


def _make_stub(
    pos_results: list[tuple[str, str]],
    **overrides: Any,
) -> type:
    """주어진 구성으로 새 ``_StubMeCabBase`` 서브클래스를 반환합니다."""
    attrs: dict[str, Any] = {"pos_results": list(pos_results)}
    attrs.update(overrides)
    return type("_StubMeCab", (_StubMeCabBase,), attrs)


def test_tokenize_uses_mecab_pos_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """표층 토큰은 하위 ``pos()`` 출력에서 나옵니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([("한국어", "NNG"), ("처리", "NNG")]),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    tok = MeCabTokenizer()
    assert tok.tokenize("한국어 처리") == ["한국어", "처리"]


def test_tokenize_empty_string_skips_mecab(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """빈 입력은 ``pos()`` 호출 없이 ``[]``를 반환합니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([("never", "NNG")], raise_on_pos=RuntimeError("must not run")),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    assert MeCabTokenizer().tokenize("") == []


def test_tokenize_pos_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """POS 필터는 태그가 집합에 있는 형태소만 유지합니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([("서울", "NNP"), ("에서", "JKB"), ("일", "NNG")]),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    out = MeCabTokenizer().tokenize("ignored", pos_filter=frozenset({"NNG", "NNP"}))
    assert out == ["서울", "일"]


def test_tokenize_remove_stopwords_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``remove_stopwords=True``와 기본 집합으로 조사가 제거됩니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([("나", "NP"), ("는", "JX"), ("학생", "NNG")]),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    out = MeCabTokenizer().tokenize("나는 학생", remove_stopwords=True)
    assert "는" not in out


def test_tokenize_custom_stopwords(monkeypatch: pytest.MonkeyPatch) -> None:
    """호출자가 제공한 불용어 집합이 기본값을 재정의합니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([("한국어", "NNG"), ("처리", "NNG")]),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    out = MeCabTokenizer().tokenize(
        "한국어 처리",
        remove_stopwords=True,
        stopwords=frozenset({"한국어"}),
    )
    assert "한국어" not in out
    assert "처리" in out


def test_analyze_offsets(monkeypatch: pytest.MonkeyPatch) -> None:
    """오프셋은 원본 텍스트에서의 부분 문자열 위치를 반영합니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([("한국어", "NNG"), ("처리", "NNG")]),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    text = "한국어 처리"
    morphs = MeCabTokenizer().analyze(text)
    assert [(m.start, m.end) for m in morphs] == [(0, 3), (4, 6)]
    assert all(isinstance(m, MorphToken) for m in morphs)


def test_analyze_offset_fallback_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MeCab이 부분 문자열이 아닌 토큰을 출력할 때도 커서는 진행됩니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([("xyz", "NNG"), ("처리", "NNG")]),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    morphs = MeCabTokenizer().analyze("한국어 처리")
    # "xyz"가 텍스트에 없음 → start는 실행 중인 커서로 기본값이 설정되고, end가 진행됩니다.
    assert morphs[0].surface == "xyz"
    assert morphs[1].surface == "처리"
    assert morphs[1].end > morphs[1].start


def test_analyze_empty_string(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_mecab(
        monkeypatch,
        _make_stub([], raise_on_pos=RuntimeError("must not run")),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    assert MeCabTokenizer().analyze("") == []


def test_mecab_pos_failure_raises_typed_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``pos()``의 모든 예외는 :class:`MeCabNotAvailableError`가 됩니다."""
    _patch_mecab(
        monkeypatch,
        _make_stub([], raise_on_pos=RuntimeError("segfault")),
    )
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    with pytest.raises(MeCabNotAvailableError):
        MeCabTokenizer().tokenize("anything")


def test_mecab_init_failure_raises_typed_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """잘못된 초기화는 :class:`MeCabNotAvailableError`가 됩니다."""
    stub = _make_stub([], init_failure=RuntimeError("dict not found"))
    _patch_mecab(monkeypatch, stub)
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    with pytest.raises(MeCabNotAvailableError):
        MeCabTokenizer()


def test_singleton_per_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """서로 다른 ``dict_path`` 값은 서로 다른 싱글톤을 생성합니다."""
    _patch_mecab(monkeypatch, _make_stub([("a", "NNG")]))
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    a = MeCabTokenizer(dict_path=None)
    b = MeCabTokenizer(dict_path="/explicit")
    assert a is not b
    # 동일한 구성 → 동일한 인스턴스.
    a2 = MeCabTokenizer(dict_path=None)
    assert a is a2


def test_get_instance_alias_returns_same_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_mecab(monkeypatch, _make_stub([("a", "NNG")]))
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    assert MeCabTokenizer() is MeCabTokenizer.get_instance()


def test_dict_path_and_user_dict_path_properties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """구성된 경로는 프로퍼티를 통해 노출됩니다."""
    _patch_mecab(monkeypatch, _make_stub([("a", "NNG")]))
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    tok = MeCabTokenizer(dict_path="/d", user_dict_path="/u")
    assert tok.dict_path == "/d"
    assert tok.user_dict_path == "/u"


def test_input_validation_rejects_non_str(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_mecab(monkeypatch, _make_stub([]))
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    tok = MeCabTokenizer()
    with pytest.raises(InvalidInputError):
        tok.tokenize(123)  # type: ignore[arg-type]
    with pytest.raises(InvalidInputError):
        tok.analyze(None)  # type: ignore[arg-type]


def test_malformed_pos_entries_filtered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``pos()``에서 나온 잘못된 형식의 항목은 자동으로 폐기됩니다."""

    class _MisbehavingMeCab(_StubMeCabBase):
        pos_results: ClassVar[list[tuple[str, str]]] = []

        def pos(self, text: str) -> list[Any]:
            return [
                ("ok", "NNG"),
                (None, "NNG"),
                ("bad",),
                42,
                ("end", "NNG"),
            ]

    _patch_mecab(monkeypatch, _MisbehavingMeCab)
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    out = MeCabTokenizer().tokenize("...")
    assert out == ["ok", "end"]

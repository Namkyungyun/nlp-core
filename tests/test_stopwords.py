"""``bpmg_korean_nlp.stopwords`` 테스트."""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS, merge_stopwords


def test_default_stopwords_is_frozenset() -> None:
    """``DEFAULT_STOPWORDS``는 frozenset 타입을 노출합니다."""
    assert isinstance(DEFAULT_STOPWORDS, frozenset)


def test_default_stopwords_rejects_mutation_add() -> None:
    """``frozenset``에는 ``.add``가 없습니다 — 변경 시 ``AttributeError``가 발생해야 합니다."""
    with pytest.raises(AttributeError):
        DEFAULT_STOPWORDS.add("test")  # type: ignore[attr-defined]


def test_default_stopwords_rejects_mutation_remove() -> None:
    with pytest.raises(AttributeError):
        DEFAULT_STOPWORDS.remove("은")  # type: ignore[attr-defined]


def test_default_stopwords_minimum_size() -> None:
    """고정된 기본 집합은 최소 50개 항목을 포함합니다."""
    assert len(DEFAULT_STOPWORDS) >= 50


def test_default_stopwords_contains_common_particles() -> None:
    """예상되는 일부 조사가 존재합니다."""
    for w in ["은", "는", "이", "가", "을", "를", "의"]:
        assert w in DEFAULT_STOPWORDS, f"Expected {w!r} in DEFAULT_STOPWORDS"


def test_merge_stopwords_returns_new_frozenset() -> None:
    """``merge_stopwords``는 비변경적이며 새 ``frozenset``을 반환합니다."""
    extra = frozenset({"foo", "bar"})
    merged = merge_stopwords(extra)
    assert isinstance(merged, frozenset)
    assert "foo" in merged
    assert "bar" in merged
    # 원본은 변경되지 않음
    assert "foo" not in DEFAULT_STOPWORDS
    assert "bar" not in DEFAULT_STOPWORDS


def test_merge_stopwords_with_base() -> None:
    """``base=``를 사용하면 ``DEFAULT_STOPWORDS``를 완전히 우회합니다."""
    merged = merge_stopwords(frozenset({"foo"}), base=frozenset({"bar"}))
    assert merged == frozenset({"foo", "bar"})


def test_merge_stopwords_no_args() -> None:
    """``merge_stopwords()``는 기반 집합과 동등한 frozenset을 반환합니다."""
    merged = merge_stopwords()
    assert merged == DEFAULT_STOPWORDS


def test_merge_stopwords_accepts_set() -> None:
    """일반 ``set``도 입력 측에서 허용됩니다."""
    merged = merge_stopwords({"foo"})
    assert "foo" in merged


def test_merge_stopwords_multiple_sources() -> None:
    """여러 위치 인수 집합이 합집합으로 합쳐집니다."""
    merged = merge_stopwords({"a"}, {"b"}, {"c"})
    assert {"a", "b", "c"}.issubset(merged)

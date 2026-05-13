"""Tests for ``bpmg_korean_nlp.stopwords``."""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS, merge_stopwords


def test_default_stopwords_is_frozenset() -> None:
    """``DEFAULT_STOPWORDS`` exposes the frozen-set type."""
    assert isinstance(DEFAULT_STOPWORDS, frozenset)


def test_default_stopwords_rejects_mutation_add() -> None:
    """``frozenset`` has no ``.add`` — mutation must raise ``AttributeError``."""
    with pytest.raises(AttributeError):
        DEFAULT_STOPWORDS.add("test")  # type: ignore[attr-defined]


def test_default_stopwords_rejects_mutation_remove() -> None:
    with pytest.raises(AttributeError):
        DEFAULT_STOPWORDS.remove("은")  # type: ignore[attr-defined]


def test_default_stopwords_minimum_size() -> None:
    """The locked default set covers at least 50 entries."""
    assert len(DEFAULT_STOPWORDS) >= 50


def test_default_stopwords_contains_common_particles() -> None:
    """A handful of expected particles are present."""
    for w in ["은", "는", "이", "가", "을", "를", "의"]:
        assert w in DEFAULT_STOPWORDS, f"Expected {w!r} in DEFAULT_STOPWORDS"


def test_merge_stopwords_returns_new_frozenset() -> None:
    """``merge_stopwords`` is non-mutating and returns a fresh ``frozenset``."""
    extra = frozenset({"foo", "bar"})
    merged = merge_stopwords(extra)
    assert isinstance(merged, frozenset)
    assert "foo" in merged
    assert "bar" in merged
    # original unchanged
    assert "foo" not in DEFAULT_STOPWORDS
    assert "bar" not in DEFAULT_STOPWORDS


def test_merge_stopwords_with_base() -> None:
    """Using ``base=`` bypasses ``DEFAULT_STOPWORDS`` entirely."""
    merged = merge_stopwords(frozenset({"foo"}), base=frozenset({"bar"}))
    assert merged == frozenset({"foo", "bar"})


def test_merge_stopwords_no_args() -> None:
    """``merge_stopwords()`` returns an equivalent frozenset of the base."""
    merged = merge_stopwords()
    assert merged == DEFAULT_STOPWORDS


def test_merge_stopwords_accepts_set() -> None:
    """A regular ``set`` is acceptable on the input side."""
    merged = merge_stopwords({"foo"})
    assert "foo" in merged


def test_merge_stopwords_multiple_sources() -> None:
    """Multiple positional sets are unioned together."""
    merged = merge_stopwords({"a"}, {"b"}, {"c"})
    assert {"a", "b", "c"}.issubset(merged)

"""Tests for ``bpmg_korean_nlp.tokenizer.MeCabTokenizer``.

The MeCab dependency is treated as optional in CI: all tests skip cleanly
when the binding or the system dictionary is missing. Logic that does not
require MeCab (input validation, return shapes) is asserted up front.
"""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.exceptions import InvalidInputError, MeCabNotAvailableError
from bpmg_korean_nlp.models import MorphToken
from bpmg_korean_nlp.tokenizer import MeCabTokenizer
from tests.conftest import HAS_MECAB


def test_missing_binding_raises() -> None:
    """Constructing without ``python-mecab-ko`` installed raises a typed error."""
    if HAS_MECAB:
        pytest.skip("python-mecab-ko binding is installed")
    MeCabTokenizer.reset_instances()
    with pytest.raises(MeCabNotAvailableError):
        MeCabTokenizer()
    MeCabTokenizer.reset_instances()


@pytest.mark.slow
def test_singleton_same_instance(real_tokenizer: MeCabTokenizer) -> None:
    """``MeCabTokenizer()`` and ``get_instance()`` resolve to the same object."""
    assert MeCabTokenizer.get_instance() is real_tokenizer
    assert MeCabTokenizer() is real_tokenizer


@pytest.mark.slow
def test_tokenize_returns_list_of_str(real_tokenizer: MeCabTokenizer) -> None:
    """The lexical path returns ``list[str]``."""
    result = real_tokenizer.tokenize("한국어 처리")
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)
    assert len(result) > 0


@pytest.mark.slow
def test_tokenize_empty_string(real_tokenizer: MeCabTokenizer) -> None:
    """An empty string returns the empty list."""
    assert real_tokenizer.tokenize("") == []


@pytest.mark.slow
def test_tokenize_english_word(real_tokenizer: MeCabTokenizer) -> None:
    """English words pass through MeCab unchanged."""
    result = real_tokenizer.tokenize("Hello world")
    joined = " ".join(result)
    assert "Hello" in joined or "hello" in joined.lower()


@pytest.mark.slow
def test_tokenize_with_emoji(real_tokenizer: MeCabTokenizer) -> None:
    """Emoji input is tolerated and produces *some* tokens."""
    result = real_tokenizer.tokenize("안녕 😀")
    assert isinstance(result, list)


@pytest.mark.slow
def test_tokenize_with_hanja(real_tokenizer: MeCabTokenizer) -> None:
    """Hanja input is tolerated."""
    result = real_tokenizer.tokenize("國家")
    assert isinstance(result, list)


@pytest.mark.slow
def test_tokenize_pos_filter_keeps_only_matches(
    real_tokenizer: MeCabTokenizer,
) -> None:
    """A POS filter restricts the output to morphemes with those tags."""
    pos_filter = frozenset({"NNG", "NNP"})
    morphs = real_tokenizer.analyze("한국어 자연어 처리 분야")
    expected = {m.surface for m in morphs if m.pos in pos_filter}
    result = set(real_tokenizer.tokenize("한국어 자연어 처리 분야", pos_filter=pos_filter))
    assert result == expected


@pytest.mark.slow
def test_tokenize_removes_stopwords(real_tokenizer: MeCabTokenizer) -> None:
    """With ``remove_stopwords=True`` particles are dropped."""
    no_stop = real_tokenizer.tokenize("나는 학생이다", remove_stopwords=False)
    with_stop = real_tokenizer.tokenize("나는 학생이다", remove_stopwords=True)
    assert len(with_stop) <= len(no_stop)
    # particle "는" is in DEFAULT_STOPWORDS so it must not appear with stopwords on
    assert "는" not in with_stop


@pytest.mark.slow
def test_tokenize_custom_stopwords(real_tokenizer: MeCabTokenizer) -> None:
    """An explicit *stopwords* set is honored when ``remove_stopwords=True``."""
    out = real_tokenizer.tokenize(
        "한국어 처리",
        remove_stopwords=True,
        stopwords=frozenset({"한국어"}),
    )
    assert "한국어" not in out


def test_tokenize_rejects_none() -> None:
    """``None`` input is rejected without needing MeCab."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    tok = MeCabTokenizer.get_instance()
    with pytest.raises(InvalidInputError):
        tok.tokenize(None)  # type: ignore[arg-type]


def test_tokenize_rejects_non_str() -> None:
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    tok = MeCabTokenizer.get_instance()
    with pytest.raises(InvalidInputError):
        tok.tokenize(42)  # type: ignore[arg-type]


@pytest.mark.slow
def test_analyze_returns_morph_tokens(real_tokenizer: MeCabTokenizer) -> None:
    """``analyze`` returns ``list[MorphToken]``; each carries the documented fields."""
    morphs = real_tokenizer.analyze("한국어 처리")
    assert isinstance(morphs, list)
    assert len(morphs) > 0
    for m in morphs:
        assert isinstance(m, MorphToken)
        assert isinstance(m.surface, str)
        assert isinstance(m.lemma, str)
        assert isinstance(m.pos, str)
        assert isinstance(m.start, int)
        assert isinstance(m.end, int)
        assert m.start >= 0
        assert m.end >= m.start


@pytest.mark.slow
def test_analyze_offsets_monotone(real_tokenizer: MeCabTokenizer) -> None:
    """Morpheme offsets are weakly monotone within the document."""
    morphs = real_tokenizer.analyze("한국어 자연어 처리")
    prev_end = 0
    for m in morphs:
        assert m.start >= prev_end - len(m.surface), (
            f"Out-of-order start: {m.start} after prev_end {prev_end}"
        )
        prev_end = m.end


@pytest.mark.slow
def test_analyze_empty_string(real_tokenizer: MeCabTokenizer) -> None:
    assert real_tokenizer.analyze("") == []


def test_analyze_rejects_none() -> None:
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    tok = MeCabTokenizer.get_instance()
    with pytest.raises(InvalidInputError):
        tok.analyze(None)  # type: ignore[arg-type]


def test_get_instance_alias() -> None:
    """``get_instance`` is an explicit named alias for the constructor."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    a = MeCabTokenizer.get_instance()
    b = MeCabTokenizer.get_instance()
    assert a is b


def test_reset_instances_clears_cache() -> None:
    """The test-only ``reset_instances`` clears the singleton cache."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    a = MeCabTokenizer.get_instance()
    MeCabTokenizer.reset_instances()
    b = MeCabTokenizer.get_instance()
    assert a is not b

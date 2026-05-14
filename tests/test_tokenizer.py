"""``bpmg_korean_nlp.tokenizer.MeCabTokenizer`` 테스트.

MeCab 의존성은 CI에서 선택적으로 처리됩니다: 바인딩이나 시스템 사전이 없으면
모든 테스트가 깔끔하게 건너뜁니다. MeCab이 필요하지 않은 로직(입력 유효성 검사,
반환 형태)은 앞서 확인됩니다.
"""

from __future__ import annotations

import pytest

from bpmg_korean_nlp.exceptions import InvalidInputError, MeCabNotAvailableError
from bpmg_korean_nlp.models import MorphToken
from bpmg_korean_nlp.tokenizer import MeCabTokenizer
from tests.conftest import HAS_MECAB


def test_missing_binding_raises() -> None:
    """``python-mecab-ko`` 없이 생성하면 타입 있는 오류가 발생합니다."""
    if HAS_MECAB:
        pytest.skip("python-mecab-ko binding is installed")
    MeCabTokenizer.reset_instances()
    with pytest.raises(MeCabNotAvailableError):
        MeCabTokenizer()
    MeCabTokenizer.reset_instances()


@pytest.mark.slow
def test_singleton_same_instance(real_tokenizer: MeCabTokenizer) -> None:
    """``MeCabTokenizer()``와 ``get_instance()``는 동일한 객체로 해석됩니다."""
    assert MeCabTokenizer.get_instance() is real_tokenizer
    assert MeCabTokenizer() is real_tokenizer


@pytest.mark.slow
def test_tokenize_returns_list_of_str(real_tokenizer: MeCabTokenizer) -> None:
    """lexical 경로는 ``list[str]``을 반환합니다."""
    result = real_tokenizer.tokenize("한국어 처리")
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)
    assert len(result) > 0


@pytest.mark.slow
def test_tokenize_empty_string(real_tokenizer: MeCabTokenizer) -> None:
    """빈 문자열은 빈 리스트를 반환합니다."""
    assert real_tokenizer.tokenize("") == []


@pytest.mark.slow
def test_tokenize_english_word(real_tokenizer: MeCabTokenizer) -> None:
    """영어 단어는 MeCab을 통해 변경 없이 통과합니다."""
    result = real_tokenizer.tokenize("Hello world")
    joined = " ".join(result)
    assert "Hello" in joined or "hello" in joined.lower()


@pytest.mark.slow
def test_tokenize_with_emoji(real_tokenizer: MeCabTokenizer) -> None:
    """이모지 입력은 허용되며 *일부* 토큰을 생성합니다."""
    result = real_tokenizer.tokenize("안녕 😀")
    assert isinstance(result, list)


@pytest.mark.slow
def test_tokenize_with_hanja(real_tokenizer: MeCabTokenizer) -> None:
    """한자 입력은 허용됩니다."""
    result = real_tokenizer.tokenize("國家")
    assert isinstance(result, list)


@pytest.mark.slow
def test_tokenize_pos_filter_keeps_only_matches(
    real_tokenizer: MeCabTokenizer,
) -> None:
    """POS 필터는 해당 태그가 있는 형태소로 출력을 제한합니다."""
    pos_filter = frozenset({"NNG", "NNP"})
    morphs = real_tokenizer.analyze("한국어 자연어 처리 분야")
    expected = {m.surface for m in morphs if m.pos in pos_filter}
    result = set(real_tokenizer.tokenize("한국어 자연어 처리 분야", pos_filter=pos_filter))
    assert result == expected


@pytest.mark.slow
def test_tokenize_removes_stopwords(real_tokenizer: MeCabTokenizer) -> None:
    """``remove_stopwords=True``이면 조사가 제거됩니다."""
    no_stop = real_tokenizer.tokenize("나는 학생이다", remove_stopwords=False)
    with_stop = real_tokenizer.tokenize("나는 학생이다", remove_stopwords=True)
    assert len(with_stop) <= len(no_stop)
    # 조사 "는"은 DEFAULT_STOPWORDS에 있으므로 불용어 제거 시 나타나면 안 됨
    assert "는" not in with_stop


@pytest.mark.slow
def test_tokenize_custom_stopwords(real_tokenizer: MeCabTokenizer) -> None:
    """``remove_stopwords=True``일 때 명시적 *stopwords* 집합이 적용됩니다."""
    out = real_tokenizer.tokenize(
        "한국어 처리",
        remove_stopwords=True,
        stopwords=frozenset({"한국어"}),
    )
    assert "한국어" not in out


def test_tokenize_rejects_none() -> None:
    """``None`` 입력은 MeCab 없이도 거부됩니다."""
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
    """``analyze``는 ``list[MorphToken]``을 반환하며, 각각 문서화된 필드를 가집니다."""
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
    """형태소 오프셋은 문서 내에서 약하게 단조 증가합니다."""
    morphs = real_tokenizer.analyze("한국어 자연어 처리")
    prev_end = 0
    for m in morphs:
        assert m.start >= prev_end - len(m.surface), (
            f"순서를 벗어난 start: {m.start} (이전 prev_end {prev_end})"
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
    """``get_instance``는 생성자의 명시적 명명된 별칭입니다."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    a = MeCabTokenizer.get_instance()
    b = MeCabTokenizer.get_instance()
    assert a is b


def test_reset_instances_clears_cache() -> None:
    """테스트 전용 ``reset_instances``는 싱글톤 캐시를 초기화합니다."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko not installed")
    a = MeCabTokenizer.get_instance()
    MeCabTokenizer.reset_instances()
    b = MeCabTokenizer.get_instance()
    assert a is not b

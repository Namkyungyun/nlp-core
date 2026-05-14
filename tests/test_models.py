"""``bpmg_korean_nlp.models``의 공개 데이터클래스 인터페이스 테스트."""

from __future__ import annotations

import re

import pytest

from bpmg_korean_nlp.models import (
    DictCheckResult,
    GraphQueryResult,
    HybridQueryResult,
    JamoComponents,
    LexicalQueryResult,
    MorphToken,
    PIIPattern,
    SemanticQueryResult,
)

_FROZEN_MODELS: list[object] = [
    MorphToken(surface="가", lemma="가", pos="JKS", start=0, end=1),
    JamoComponents(choseong="ㅎ", jungseong="ㅏ", jongseong="ㄴ"),
    DictCheckResult(available=True, dict_path="/x", version="2.1", error=None),
    PIIPattern(name="x", description="d", pattern=re.compile(r"\d+")),
    LexicalQueryResult(keywords=("a", "b"), query="a b"),
    SemanticQueryResult(query="hi"),
    GraphQueryResult(seed_nodes=("seoul",)),
]


@pytest.mark.parametrize("instance", _FROZEN_MODELS)
def test_models_are_frozen(instance: object) -> None:
    """모든 데이터클래스 모델은 속성 변경을 거부합니다."""
    with pytest.raises((AttributeError, TypeError)):
        instance.surface = "new"  # type: ignore[attr-defined]


@pytest.mark.parametrize("instance", _FROZEN_MODELS)
def test_models_use_slots(instance: object) -> None:
    """slots=True는 알 수 없는 속성 할당을 금지합니다."""
    with pytest.raises((AttributeError, TypeError)):
        instance.bogus_field = "x"  # type: ignore[attr-defined]


def test_models_are_hashable() -> None:
    """동결된(frozen) 데이터클래스는 필드가 해시 가능할 때 해시 가능합니다."""
    a = MorphToken(surface="가", lemma="가", pos="JKS", start=0, end=1)
    b = MorphToken(surface="가", lemma="가", pos="JKS", start=0, end=1)
    assert hash(a) == hash(b)
    assert a == b


def test_hybrid_holds_sub_results() -> None:
    """``HybridQueryResult``는 세 브랜치 결과를 그대로 저장합니다."""
    lex = LexicalQueryResult(keywords=("k",), query="k")
    sem = SemanticQueryResult(query="hi")
    gph = GraphQueryResult(seed_nodes=("seoul",))
    hybrid = HybridQueryResult(lexical=lex, semantic=sem, graph=gph)
    assert hybrid.lexical is lex
    assert hybrid.semantic is sem
    assert hybrid.graph is gph


def test_pii_pattern_compiles() -> None:
    """``PIIPattern.pattern``은 실제로 컴파일된 정규식을 보유합니다."""
    p = PIIPattern(name="x", description="d", pattern=re.compile(r"\d{6}"))
    assert isinstance(p.pattern, re.Pattern)
    assert p.pattern.fullmatch("123456") is not None


def test_morph_token_offsets() -> None:
    """``start``/``end``는 일반 정수이며, 동등성은 모든 필드를 포함합니다."""
    t = MorphToken(surface="가", lemma="가", pos="JKS", start=0, end=1)
    assert t.start == 0
    assert t.end == 1
    assert t.surface == "가"
    assert t.pos == "JKS"

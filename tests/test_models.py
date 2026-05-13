"""Tests for the public dataclass surface in ``bpmg_korean_nlp.models``."""

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
    """Every dataclass model rejects attribute mutation."""
    with pytest.raises((AttributeError, TypeError)):
        instance.surface = "new"  # type: ignore[attr-defined]


@pytest.mark.parametrize("instance", _FROZEN_MODELS)
def test_models_use_slots(instance: object) -> None:
    """slots=True forbids assigning unknown attributes."""
    with pytest.raises((AttributeError, TypeError)):
        instance.bogus_field = "x"  # type: ignore[attr-defined]


def test_models_are_hashable() -> None:
    """Frozen dataclasses are hashable when their fields are hashable."""
    a = MorphToken(surface="가", lemma="가", pos="JKS", start=0, end=1)
    b = MorphToken(surface="가", lemma="가", pos="JKS", start=0, end=1)
    assert hash(a) == hash(b)
    assert a == b


def test_hybrid_holds_sub_results() -> None:
    """``HybridQueryResult`` stores the three branch results verbatim."""
    lex = LexicalQueryResult(keywords=("k",), query="k")
    sem = SemanticQueryResult(query="hi")
    gph = GraphQueryResult(seed_nodes=("seoul",))
    hybrid = HybridQueryResult(lexical=lex, semantic=sem, graph=gph)
    assert hybrid.lexical is lex
    assert hybrid.semantic is sem
    assert hybrid.graph is gph


def test_pii_pattern_compiles() -> None:
    """``PIIPattern.pattern`` holds a real compiled regex."""
    p = PIIPattern(name="x", description="d", pattern=re.compile(r"\d{6}"))
    assert isinstance(p.pattern, re.Pattern)
    assert p.pattern.fullmatch("123456") is not None


def test_morph_token_offsets() -> None:
    """``start``/``end`` are plain ints; equality covers all fields."""
    t = MorphToken(surface="가", lemma="가", pos="JKS", start=0, end=1)
    assert t.start == 0
    assert t.end == 1
    assert t.surface == "가"
    assert t.pos == "JKS"

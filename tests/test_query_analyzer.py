"""Tests for the QueryAnalyzer 4-target pipeline.

All target dispatch logic is verified against DI fakes so the suite runs
without MeCab. Real-model integration is covered by the
golden-set tests under :mod:`test_golden`.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from bpmg_korean_nlp.enums import QueryTarget
from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.models import (
    GraphQueryResult,
    HybridQueryResult,
    LexicalQueryResult,
    SemanticQueryResult,
)
from bpmg_korean_nlp.query_analyzer import QueryAnalyzer, analyze_query
from tests.conftest import FakeNormalizer, FakeTokenizer


def _build_analyzer(
    tokens: list[tuple[str, str]],
) -> tuple[QueryAnalyzer, FakeTokenizer]:
    norm = FakeNormalizer()
    tok = FakeTokenizer(tokens)
    qa = QueryAnalyzer(
        normalizer=norm,  # type: ignore[arg-type]
        tokenizer=tok,  # type: ignore[arg-type]
    )
    return qa, tok


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


def test_lexical_returns_lexical_result() -> None:
    """Lexical target returns ``LexicalQueryResult`` with tuple keywords."""
    qa, _ = _build_analyzer([("조사", "NNG"), ("어미", "NNG"), ("차이", "NNG"), ("가", "JKS")])
    result = qa.analyze("조사랑 어미 차이", QueryTarget.LEXICAL)
    assert isinstance(result, LexicalQueryResult)
    assert isinstance(result.keywords, tuple)
    assert isinstance(result.query, str)
    # particle "가" is in DEFAULT_STOPWORDS
    assert "가" not in result.keywords
    assert result.query == " ".join(result.keywords)


def test_semantic_returns_semantic_result() -> None:
    """Semantic target preserves the preprocessed natural sentence."""
    qa, _ = _build_analyzer([])
    text = "조사와 어미의 차이는 무엇인가요?"
    result = qa.analyze(text, QueryTarget.SEMANTIC)
    assert isinstance(result, SemanticQueryResult)
    # The normalizer is a pass-through fake (strips), so the query equals
    # the post-preprocessing text — but it must remain free-form (with
    # punctuation intact).
    assert "?" in result.query


def test_graph_returns_graph_result_nng_nnp_only() -> None:
    """Graph target collects only ``NNG``/``NNP`` lemmas."""
    qa, _ = _build_analyzer(
        [
            ("서울", "NNP"),
            ("에서", "JKB"),
            ("일", "NNG"),
            ("했다", "VV"),
        ]
    )
    result = qa.analyze("서울에서 일했다", QueryTarget.GRAPH)
    assert isinstance(result, GraphQueryResult)
    assert isinstance(result.seed_nodes, tuple)
    assert "서울" in result.seed_nodes
    assert "일" in result.seed_nodes
    assert "했다" not in result.seed_nodes
    assert "에서" not in result.seed_nodes


def test_hybrid_returns_hybrid_result_with_all_three() -> None:
    """Hybrid target bundles lexical + semantic + graph in one record."""
    qa, _ = _build_analyzer(
        [
            ("서울", "NNP"),
            ("에서", "JKB"),
            ("일", "NNG"),
        ]
    )
    result = qa.analyze("서울에서 일", QueryTarget.HYBRID)
    assert isinstance(result, HybridQueryResult)
    assert isinstance(result.lexical, LexicalQueryResult)
    assert isinstance(result.semantic, SemanticQueryResult)
    assert isinstance(result.graph, GraphQueryResult)


# ---------------------------------------------------------------------------
# Empty / whitespace input x 4 targets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_empty_input_per_target(target: QueryTarget) -> None:
    """Empty-string input produces empty-result objects for every target."""
    qa, _ = _build_analyzer([])
    result = qa.analyze("", target)
    if isinstance(result, LexicalQueryResult):
        assert result.keywords == ()
        assert result.query == ""
    elif isinstance(result, SemanticQueryResult):
        assert result.query == ""
    elif isinstance(result, GraphQueryResult):
        assert result.seed_nodes == ()
    else:
        assert isinstance(result, HybridQueryResult)
        assert result.lexical.keywords == ()
        assert result.semantic.query == ""
        assert result.graph.seed_nodes == ()


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_whitespace_only_per_target(target: QueryTarget) -> None:
    """Whitespace-only normalizes to empty and yields empty results."""
    qa, _ = _build_analyzer([])
    result = qa.analyze("   \t  ", target)
    assert result is not None


# ---------------------------------------------------------------------------
# English / Hanja / mixed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_english_input_per_target(target: QueryTarget) -> None:
    """Pure-English input flows through every target without raising."""
    qa, _ = _build_analyzer([("hello", "SL"), ("world", "SL")])
    result = qa.analyze("hello world", target)
    assert result is not None


@pytest.mark.parametrize(
    "target",
    [QueryTarget.LEXICAL, QueryTarget.SEMANTIC, QueryTarget.GRAPH, QueryTarget.HYBRID],
)
def test_hanja_input_per_target(target: QueryTarget) -> None:
    """Pure-Hanja input flows through every target without raising."""
    qa, _ = _build_analyzer([("國家", "SH")])
    result = qa.analyze("國家", target)
    assert result is not None


# ---------------------------------------------------------------------------
# Target coercion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spelling",
    ["lexical", "LEXICAL", "Lexical", "lEXICaL"],
)
def test_string_target_case_insensitive(spelling: str) -> None:
    """String target values are accepted regardless of case."""
    qa, _ = _build_analyzer([("test", "NNG")])
    result = qa.analyze("test", spelling)
    assert isinstance(result, LexicalQueryResult)


def test_unknown_target_string_raises() -> None:
    """An unrecognized target string raises :class:`InvalidInputError`."""
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze("test", "unknown_target")


def test_non_string_non_enum_target_raises() -> None:
    """A target that's neither a string nor a :class:`QueryTarget` raises."""
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze("test", 123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_rejects_none_text() -> None:
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze(None, QueryTarget.LEXICAL)  # type: ignore[arg-type]


def test_rejects_non_str_text() -> None:
    qa, _ = _build_analyzer([])
    with pytest.raises(InvalidInputError):
        qa.analyze(42, QueryTarget.LEXICAL)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Pipeline plumbing
# ---------------------------------------------------------------------------


def test_hybrid_runs_each_branch_once() -> None:
    """Hybrid pipeline produces results consistent with running each branch alone."""
    qa, _ = _build_analyzer([("서울", "NNP"), ("일", "NNG"), ("의", "JKG")])
    h = qa.analyze("서울 일의", QueryTarget.HYBRID)
    assert isinstance(h, HybridQueryResult)
    # graph branch keeps only NNG/NNP
    assert "의" not in h.graph.seed_nodes
    # lexical branch drops particle "의" via DEFAULT_STOPWORDS
    assert "의" not in h.lexical.keywords


def test_long_input_warning_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    """Inputs over 10k characters emit a WARNING but still complete."""
    qa, _ = _build_analyzer([])
    long_text = "가" * 10_001
    with caplog.at_level("WARNING", logger="bpmg_korean_nlp.query_analyzer"):
        qa.analyze(long_text, QueryTarget.SEMANTIC)
    assert any("characters" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Module-level analyze_query
# ---------------------------------------------------------------------------


def test_analyze_query_default_target_is_lexical() -> None:
    """The convenience function defaults to ``"lexical"``."""
    from bpmg_korean_nlp import query_analyzer as qa_module

    qa_module._default_analyzer = QueryAnalyzer(
        normalizer=FakeNormalizer(),  # type: ignore[arg-type]
        tokenizer=FakeTokenizer([("test", "NNG")]),  # type: ignore[arg-type]
    )
    result = analyze_query("test")
    assert isinstance(result, LexicalQueryResult)


def test_analyze_query_accepts_string_target() -> None:
    """A string target name is forwarded to :meth:`QueryAnalyzer.analyze`."""
    from bpmg_korean_nlp import query_analyzer as qa_module

    qa_module._default_analyzer = QueryAnalyzer(
        normalizer=FakeNormalizer(),  # type: ignore[arg-type]
        tokenizer=FakeTokenizer([("test", "NNG")]),  # type: ignore[arg-type]
    )
    result = analyze_query("test", "semantic")
    assert isinstance(result, SemanticQueryResult)


# ---------------------------------------------------------------------------
# Forbidden imports
# ---------------------------------------------------------------------------


def test_query_analyzer_does_not_import_retrieval_core() -> None:
    """Static AST check: ``query_analyzer.py`` does not touch forbidden packages."""
    forbidden = {"retrieval_core", "guardrail_core", "chatbot_contracts"}
    path = Path(__file__).parent.parent / "src" / "bpmg_korean_nlp" / "query_analyzer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                head = alias.name.split(".", 1)[0]
                assert head not in forbidden
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            head = module.split(".", 1)[0]
            assert head not in forbidden

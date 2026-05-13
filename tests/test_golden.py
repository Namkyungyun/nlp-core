"""Golden input/output regression suite.

Each line of ``tests/fixtures/golden.jsonl`` describes a deterministic
pipeline check: ``{id, type, input, expected*}``. Entries whose ``type``
needs MeCab are skipped cleanly when the binding is absent so the same
JSONL is the source of truth for both pure-Python CI runs and the full
integration build.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bpmg_korean_nlp.enums import QueryTarget
from bpmg_korean_nlp.jamo_utils import extract_choseong
from bpmg_korean_nlp.models import (
    GraphQueryResult,
    HybridQueryResult,
    LexicalQueryResult,
    SemanticQueryResult,
)
from bpmg_korean_nlp.normalizer import KoreanNormalizer
from tests.conftest import HAS_MECAB

_GOLDEN_PATH: Path = Path(__file__).parent / "fixtures" / "golden.jsonl"


def _load_golden() -> list[dict[str, Any]]:
    """Read every JSONL record from the golden file."""
    entries: list[dict[str, Any]] = []
    with _GOLDEN_PATH.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entries.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                pytest.fail(f"Malformed JSONL on line {line_no}: {exc}")
    return entries


_ENTRIES: list[dict[str, Any]] = _load_golden()


def _idfn(entry: dict[str, Any]) -> str:
    return str(entry.get("id", "unknown"))


def test_golden_set_minimum_size() -> None:
    """The on-disk golden set has the required minimum count."""
    assert len(_ENTRIES) >= 75, f"Golden set must have at least 75 entries, got {len(_ENTRIES)}"


def test_golden_set_required_categories() -> None:
    """Every required type-bucket appears with its target minimum."""
    by_type: dict[str, int] = {}
    for e in _ENTRIES:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
    requirements = {
        "tokenize": 20,
        "normalize": 15,
        "analyze_query": 25,
        "jamo_roundtrip": 10,
    }
    for key, minimum in requirements.items():
        actual = by_type.get(key, 0)
        assert actual >= minimum, f"{key}: have {actual}, need {minimum}"


# ---------------------------------------------------------------------------
# Pure-Python entry handlers (always runnable)
# ---------------------------------------------------------------------------


def _run_normalize(entry: dict[str, Any]) -> None:
    normalizer = KoreanNormalizer.default()
    out = normalizer.normalize(entry["input"])
    if "expected" in entry:
        assert out == entry["expected"], (
            f"[{entry['id']}] normalize: expected {entry['expected']!r}, got {out!r}"
        )
    if "expected_contains" in entry:
        for token in entry["expected_contains"]:
            assert token in out, f"[{entry['id']}] expected {token!r} in {out!r}"


def _run_jamo_roundtrip(entry: dict[str, Any]) -> None:
    actual = extract_choseong(entry["input"])
    expected = entry.get("expected_choseong")
    assert actual == expected, f"[{entry['id']}] choseong: expected {expected!r}, got {actual!r}"


# ---------------------------------------------------------------------------
# MeCab-bound handlers (skipped when dep missing)
# ---------------------------------------------------------------------------


def _run_tokenize(entry: dict[str, Any]) -> None:
    if not HAS_MECAB:
        pytest.skip("MeCab binding not installed")
    from bpmg_korean_nlp.exceptions import MeCabNotAvailableError
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    try:
        tokenizer = MeCabTokenizer.get_instance()
    except MeCabNotAvailableError as exc:
        pytest.skip(f"MeCab not loadable: {exc}")
    tokens = tokenizer.tokenize(entry["input"])
    if "expected_contains" in entry:
        for token in entry["expected_contains"]:
            assert token in tokens, f"[{entry['id']}] expected {token!r} in tokens {tokens!r}"
    if "expected" in entry:
        assert tokens == entry["expected"], (
            f"[{entry['id']}] tokens: expected {entry['expected']}, got {tokens}"
        )


def _run_analyze_query(entry: dict[str, Any]) -> None:
    if not HAS_MECAB:
        pytest.skip("MeCab binding not installed")
    from bpmg_korean_nlp.exceptions import MeCabNotAvailableError
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    try:
        analyzer = QueryAnalyzer()
    except MeCabNotAvailableError as exc:
        pytest.skip(f"MeCab not loadable: {exc}")

    target = entry["target"]
    result = analyzer.analyze(entry["input"], target)

    target_enum = QueryTarget(target.lower()) if isinstance(target, str) else target
    if target_enum is QueryTarget.LEXICAL:
        assert isinstance(result, LexicalQueryResult)
        for token in entry.get("expected_keywords_contains", []):
            assert token in result.keywords, (
                f"[{entry['id']}] expected {token!r} in {result.keywords}"
            )
    elif target_enum is QueryTarget.SEMANTIC:
        assert isinstance(result, SemanticQueryResult)
        substring = entry.get("expected_query_contains", "")
        if substring:
            assert substring in result.query, (
                f"[{entry['id']}] expected {substring!r} in {result.query!r}"
            )
    elif target_enum is QueryTarget.GRAPH:
        assert isinstance(result, GraphQueryResult)
        for seed in entry.get("expected_seeds_contains", []):
            assert seed in result.seed_nodes, (
                f"[{entry['id']}] expected {seed!r} in {result.seed_nodes}"
            )
    else:
        assert isinstance(result, HybridQueryResult)
        for token in entry.get("expected_keywords_contains", []):
            assert token in result.lexical.keywords, (
                f"[{entry['id']}] hybrid lex: expected {token!r}"
            )
        for seed in entry.get("expected_seeds_contains", []):
            assert seed in result.graph.seed_nodes, (
                f"[{entry['id']}] hybrid graph: expected {seed!r}"
            )
        substring = entry.get("expected_query_contains", "")
        if substring:
            assert substring in result.semantic.query


_DISPATCH = {
    "normalize": _run_normalize,
    "jamo_roundtrip": _run_jamo_roundtrip,
    "tokenize": _run_tokenize,
    "analyze_query": _run_analyze_query,
}


@pytest.mark.golden
@pytest.mark.parametrize("entry", _ENTRIES, ids=_idfn)
def test_golden_entry(entry: dict[str, Any]) -> None:
    """Each golden entry is executed by the handler for its ``type``."""
    handler = _DISPATCH.get(entry["type"])
    if handler is None:
        pytest.fail(f"Unknown golden type: {entry['type']}")
    handler(entry)

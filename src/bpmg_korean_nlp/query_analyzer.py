"""Query analysis for korean-nlp-core.

:class:`QueryAnalyzer` is a *pure transformation layer* that rewrites a
user's natural-language query into one of four retrieval-target
representations:

* ``LEXICAL``   — BM25-ready tokens with stopwords removed.
* ``SEMANTIC``  — the natural sentence preserved verbatim, for embedding
  models that consume free-form text.
* ``GRAPH``     — seed nouns/entities (Sejong POS ``NNG`` / ``NNP``).
* ``HYBRID``    — all three results bundled together; the three pipelines
  run in parallel because they share the same normalized input.

Every actual retrieval step — BM25 scoring, vector lookup, graph
traversal, ranking — is the consumer's responsibility. By contract this
module never imports ``retrieval_core``, ``guardrail_core``, or
``chatbot_contracts`` and never performs any kind of scoring.

The default singletons (:class:`KoreanNormalizer`,
:class:`MeCabTokenizer`, :class:`SpacingRestorer`,
:data:`DEFAULT_STOPWORDS`) are reused so that downstream callers pay the
dictionary- and model-loading cost at most once per process. Each
dependency can be replaced via the constructor for testing or custom
deployments.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Final

from bpmg_korean_nlp.enums import QueryTarget
from bpmg_korean_nlp.exceptions import InvalidInputError
from bpmg_korean_nlp.pii import check_pii
from bpmg_korean_nlp.models import (
    GraphQueryResult,
    HybridQueryResult,
    LexicalQueryResult,
    MorphToken,
    QueryResult,
    SemanticQueryResult,
)
from bpmg_korean_nlp.normalizer import KoreanNormalizer
from bpmg_korean_nlp.spacing import SpacingRestorer
from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS
from bpmg_korean_nlp.tokenizer import MeCabTokenizer

__all__ = ["QueryAnalyzer", "analyze_query"]

_logger = logging.getLogger(__name__)

_GRAPH_POS: Final[frozenset[str]] = frozenset({"NNG", "NNP"})
_LONG_INPUT_THRESHOLD: Final[int] = 10_000


class QueryAnalyzer:
    """Turn raw user queries into retrieval-target representations.

    The analyzer is intentionally thin: every public call routes through
    :meth:`analyze`, which normalizes and respaces the input once and
    then dispatches to one of four target-specific helpers. The helpers
    only differ in the post-processing step, so :meth:`analyze` keeps
    the per-call dictionary work to a minimum.

    Args:
        normalizer: Optional :class:`KoreanNormalizer`. When ``None`` the
            locked default (:meth:`KoreanNormalizer.default`) is used.
        tokenizer: Optional :class:`MeCabTokenizer`. When ``None`` the
            process-wide singleton from :meth:`MeCabTokenizer.get_instance`
            is used.
        spacing_restorer: Optional :class:`SpacingRestorer`. When ``None``
            the process-wide singleton from
            :meth:`SpacingRestorer.get_instance` is used.
        stopwords: Optional override for the stopword set used by the
            lexical pipeline. When ``None``, :data:`DEFAULT_STOPWORDS`
            is used.
    """

    __slots__ = ("_normalizer", "_spacing_restorer", "_stopwords", "_tokenizer")

    def __init__(
        self,
        normalizer: KoreanNormalizer | None = None,
        tokenizer: MeCabTokenizer | None = None,
        spacing_restorer: SpacingRestorer | None = None,
        stopwords: frozenset[str] | None = None,
    ) -> None:
        self._normalizer: KoreanNormalizer = (
            normalizer if normalizer is not None else KoreanNormalizer.default()
        )
        self._tokenizer: MeCabTokenizer = (
            tokenizer if tokenizer is not None else MeCabTokenizer.get_instance()
        )
        self._spacing_restorer: SpacingRestorer = (
            spacing_restorer if spacing_restorer is not None else SpacingRestorer.get_instance()
        )
        self._stopwords: frozenset[str] = stopwords if stopwords is not None else DEFAULT_STOPWORDS

    def analyze(self, text: str, target: QueryTarget | str) -> QueryResult:
        """Analyze *text* for the given retrieval *target*.

        Args:
            text: The raw user query.
            target: A :class:`QueryTarget` member or the equivalent string
                (``"lexical"``, ``"semantic"``, ``"graph"``, ``"hybrid"``).
                The string form is case-insensitive.

        Returns:
            One of :class:`LexicalQueryResult`, :class:`SemanticQueryResult`,
            :class:`GraphQueryResult`, or :class:`HybridQueryResult`,
            matching *target*.

        Raises:
            InvalidInputError: If *text* is not a ``str`` or if *target*
                is neither a :class:`QueryTarget` nor a recognized string.
            PIIDetectedError: If *text* contains any PII pattern (secondary
                filter after ``guardrail-core``).
            MeCabNotAvailableError: Propagated from the tokenizer when
                MeCab cannot analyze the input (lexical, graph, hybrid).
            SpacingModelLoadError: Propagated from the spacing restorer
                when the PyKoSpacing model fails to initialize.
        """
        if not isinstance(text, str):
            raise InvalidInputError(f"QueryAnalyzer.analyze expects str, got {type(text).__name__}")
        check_pii(text)
        resolved_target = self._resolve_target(target)

        if len(text) > _LONG_INPUT_THRESHOLD:
            _logger.warning(
                "QueryAnalyzer received input of %d characters "
                "(soft threshold %d); processing will continue.",
                len(text),
                _LONG_INPUT_THRESHOLD,
            )

        prepared = self._preprocess(text)

        if resolved_target is QueryTarget.LEXICAL:
            return self._run_lexical(prepared)
        if resolved_target is QueryTarget.SEMANTIC:
            return self._run_semantic(prepared)
        if resolved_target is QueryTarget.GRAPH:
            return self._run_graph(prepared)
        return self._run_hybrid(prepared)

    def _preprocess(self, text: str) -> str:
        """Apply the shared ``normalize → spacing`` pipeline.

        Returns the empty string immediately when normalization produces
        an empty result, avoiding an unnecessary model call on whitespace-
        only input.
        """
        normalized = self._normalizer.normalize(text)
        if not normalized:
            return ""
        return self._spacing_restorer.restore(normalized)

    def _run_lexical(self, text: str) -> LexicalQueryResult:
        """Lexical pipeline: ``tokenize + DEFAULT_STOPWORDS`` removal."""
        if not text:
            return LexicalQueryResult(keywords=(), query="")
        tokens = self._tokenizer.tokenize(
            text,
            remove_stopwords=True,
            stopwords=self._stopwords,
        )
        return LexicalQueryResult(
            keywords=tuple(tokens),
            query=" ".join(tokens),
        )

    def _run_semantic(self, text: str) -> SemanticQueryResult:
        """Semantic pipeline: preserve the natural sentence verbatim.

        Tokenization is forbidden here — embedding models consume
        free-form text and benefit from the original word ordering and
        function words that the lexical pipeline strips.
        """
        return SemanticQueryResult(query=text)

    def _run_graph(self, text: str) -> GraphQueryResult:
        """Graph pipeline: extract noun/proper-noun lemmas as seed nodes."""
        if not text:
            return GraphQueryResult(seed_nodes=())
        morphs: list[MorphToken] = self._tokenizer.analyze(text)
        seeds = tuple(m.lemma for m in morphs if m.pos in _GRAPH_POS)
        return GraphQueryResult(seed_nodes=seeds)

    def _run_hybrid(self, text: str) -> HybridQueryResult:
        """Hybrid pipeline: run lexical, semantic, and graph in parallel.

        The three branches share the same preprocessed input but call
        into independent MeCab/Python code paths, so a small thread
        pool overlaps their work without contention. The pool is bounded
        and torn down per call — hybrid analysis is not a hot loop.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_lex = executor.submit(self._run_lexical, text)
            f_sem = executor.submit(self._run_semantic, text)
            f_gph = executor.submit(self._run_graph, text)
            return HybridQueryResult(
                lexical=f_lex.result(),
                semantic=f_sem.result(),
                graph=f_gph.result(),
            )

    @staticmethod
    def _resolve_target(target: QueryTarget | str) -> QueryTarget:
        """Coerce *target* into a :class:`QueryTarget` or raise."""
        if isinstance(target, QueryTarget):
            return target
        if isinstance(target, str):
            try:
                return QueryTarget(target.lower())
            except ValueError as exc:
                valid = [t.value for t in QueryTarget]
                raise InvalidInputError(
                    f"Unknown query target: {target!r}. Valid targets: {valid}"
                ) from exc
        raise InvalidInputError(f"target must be QueryTarget or str, got {type(target).__name__}")


_default_analyzer: QueryAnalyzer | None = None


def _get_default_analyzer() -> QueryAnalyzer:
    """Lazily construct and cache the module-level default analyzer."""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = QueryAnalyzer()
    return _default_analyzer


def analyze_query(
    text: str,
    target: QueryTarget | str = "lexical",
) -> QueryResult:
    """Convenience wrapper around the default :class:`QueryAnalyzer`.

    Equivalent to ``QueryAnalyzer().analyze(text, target)`` but reuses a
    module-level instance so the underlying MeCab and spacing singletons
    are only resolved once.

    Args:
        text: Raw user query.
        target: Retrieval target; see :meth:`QueryAnalyzer.analyze`.

    Returns:
        The :class:`QueryResult` produced by the chosen pipeline.
    """
    return _get_default_analyzer().analyze(text, target)

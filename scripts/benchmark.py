#!/usr/bin/env python3
"""korean-nlp-core 성능 기준 실행기.

두 가지 핫 패스(tokenize, hybrid ``analyze_query``)의 p99 지연 시간,
1000회 tokenize 루프의 wall time, 모델+사전 로드 후 상주 메모리를 보고합니다.

목표값 (로드 후, 단일 짧은 문장):

* ``tokenize`` p99   < 5 ms
* ``hybrid``  p99    < 100 ms
* 1000회 배치 tokenize < 2 s wall time
* 사전 로드 후 상주 메모리 < 500 MB

모든 목표를 충족하면 상태 ``0``, 하나라도 미달하면 ``1``, 하나 이상의
무거운 의존성을 사용할 수 없어 해당 지표를 측정할 수 없으면 ``2``로 종료합니다.
출력은 CI 로그에 적합한 일반 텍스트입니다.
"""

from __future__ import annotations

import gc
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass

_DEFAULT_SAMPLE_TEXT = "한국어 자연어 처리 분야에서는 형태소 분석이 중요하다"
_DEFAULT_ITERATIONS = 1000
_TOKENIZE_TARGET_MS = 5.0
_HYBRID_TARGET_MS = 100.0
_BATCH_TARGET_S = 2.0
_MEMORY_TARGET_MB = 500.0


@dataclass(frozen=True, slots=True)
class _LatencyStats:
    """지연 시간 샘플의 요약 통계 (모든 값은 밀리초 단위)."""

    p50: float
    p90: float
    p99: float
    mean: float
    samples: int


def _measure(fn: Callable[[], object], iterations: int) -> _LatencyStats:
    """*fn*을 *iterations*번 호출한 지연 시간 통계를 반환합니다."""
    timings_ms: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        timings_ms.append((time.perf_counter() - start) * 1_000.0)
    quantiles = statistics.quantiles(timings_ms, n=100, method="inclusive")
    return _LatencyStats(
        p50=quantiles[49],
        p90=quantiles[89],
        p99=quantiles[98],
        mean=statistics.fmean(timings_ms),
        samples=iterations,
    )


def _format_row(label: str, stats: _LatencyStats, target_ms: float) -> str:
    flag = "OK " if stats.p99 < target_ms else "FAIL"
    return (
        f"[{flag}] {label:<10s} "
        f"p50={stats.p50:7.3f}ms  "
        f"p90={stats.p90:7.3f}ms  "
        f"p99={stats.p99:7.3f}ms  "
        f"mean={stats.mean:7.3f}ms  "
        f"target_p99<{target_ms:.0f}ms"
    )


def _import_tokenizer() -> object | None:
    try:
        from bpmg_korean_nlp.exceptions import MeCabNotAvailableError
        from bpmg_korean_nlp.tokenizer import MeCabTokenizer
    except ImportError:
        return None
    try:
        return MeCabTokenizer.get_instance()
    except MeCabNotAvailableError:
        return None


def _import_analyzer() -> object | None:
    try:
        from bpmg_korean_nlp.exceptions import MeCabNotAvailableError
        from bpmg_korean_nlp.query_analyzer import QueryAnalyzer
    except ImportError:
        return None
    try:
        return QueryAnalyzer()
    except MeCabNotAvailableError:
        return None


def main(iterations: int = _DEFAULT_ITERATIONS, text: str = _DEFAULT_SAMPLE_TEXT) -> int:
    """벤치마크를 실행하고 CI 종료 코드를 반환합니다."""
    print(f"# korean-nlp-core benchmark — text={text!r}, iterations={iterations}")
    print()

    tracemalloc.start()
    gc.collect()

    failures: list[str] = []
    missing: list[str] = []

    tokenizer = _import_tokenizer()
    if tokenizer is None:
        missing.append("tokenize")
        print("[SKIP] tokenize    — MeCab 사용 불가")
    else:
        # 첫 번째 호출 지터가 히스토그램을 지배하지 않도록 워밍업합니다.
        tokenizer.tokenize(text)  # type: ignore[attr-defined]
        stats = _measure(lambda: tokenizer.tokenize(text), iterations)  # type: ignore[attr-defined]
        print(_format_row("tokenize", stats, _TOKENIZE_TARGET_MS))
        if stats.p99 >= _TOKENIZE_TARGET_MS:
            failures.append("tokenize p99")

        batch_start = time.perf_counter()
        for _ in range(iterations):
            tokenizer.tokenize(text)  # type: ignore[attr-defined]
        batch_seconds = time.perf_counter() - batch_start
        flag = "OK " if batch_seconds < _BATCH_TARGET_S else "FAIL"
        print(
            f"[{flag}] batch1000  "
            f"wall={batch_seconds:7.3f}s  "
            f"target<{_BATCH_TARGET_S:.1f}s"
        )
        if batch_seconds >= _BATCH_TARGET_S:
            failures.append("batch tokenize")

    analyzer = _import_analyzer()
    if analyzer is None:
        missing.append("hybrid")
        print("[SKIP] hybrid      — MeCab 사용 불가")
    else:
        analyzer.analyze(text, "hybrid")  # type: ignore[attr-defined]
        stats = _measure(
            lambda: analyzer.analyze(text, "hybrid"),  # type: ignore[attr-defined]
            iterations,
        )
        print(_format_row("hybrid", stats, _HYBRID_TARGET_MS))
        if stats.p99 >= _HYBRID_TARGET_MS:
            failures.append("hybrid p99")

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak / (1024 * 1024)
    flag = "OK " if peak_mb < _MEMORY_TARGET_MB else "FAIL"
    print()
    print(f"[{flag}] memory     peak={peak_mb:7.2f}MB  target<{_MEMORY_TARGET_MB:.0f}MB")
    if peak_mb >= _MEMORY_TARGET_MB:
        failures.append("memory")

    print()
    if missing and not failures:
        print(f"PARTIAL — {len(missing)} metric(s) skipped: {', '.join(missing)}")
        return 2
    if failures:
        print(f"FAIL    — missed targets: {', '.join(failures)}")
        return 1
    print("PASS    — every baseline met.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

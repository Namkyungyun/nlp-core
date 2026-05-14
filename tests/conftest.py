"""korean-nlp-core 테스트 스위트의 공유 pytest 픽스처.

대부분의 로직 테스트는 DI 가짜(``FakeTokenizer`` / ``FakeNormalizer`` 참조)를
사용하여 MeCab이 없는 CI 환경을 포함한 어디서나 실행됩니다. 무거운 의존성이
실제로 필요한 테스트는 ``real_mecab`` 픽스처로 보호되며, 바인딩을 임포트할 수
없으면 깔끔하게 건너뜁니다.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from bpmg_korean_nlp.models import MorphToken
    from bpmg_korean_nlp.normalizer import KoreanNormalizer
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer


def _has_mecab() -> bool:
    """``python-mecab-ko`` 바인딩을 임포트할 수 있으면 ``True``를 반환합니다."""
    try:
        import mecab  # noqa: F401
    except ImportError:
        return False
    return True


HAS_MECAB: bool = _has_mecab()


# ---------------------------------------------------------------------------
# 순수 Python 픽스처 (무거운 의존성 없음)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def normalizer() -> KoreanNormalizer:
    """고정 기본값 KoreanNormalizer (NFC, repeat_normalize, 공백)."""
    from bpmg_korean_nlp.normalizer import KoreanNormalizer

    return KoreanNormalizer.default()


# ---------------------------------------------------------------------------
# 무거운 의존성 픽스처 (MeCab 없으면 건너뜀)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_tokenizer() -> MeCabTokenizer:
    """세션 범위의 실제 MeCab 토크나이저; 바인딩이 없으면 건너뜁니다."""
    if not HAS_MECAB:
        pytest.skip("python-mecab-ko binding not installed")
    from bpmg_korean_nlp.exceptions import MeCabNotAvailableError
    from bpmg_korean_nlp.tokenizer import MeCabTokenizer

    try:
        return MeCabTokenizer.get_instance()
    except MeCabNotAvailableError as exc:
        pytest.skip(f"MeCab dictionary not available: {exc}")


@pytest.fixture(scope="session")
def real_query_analyzer(
    real_tokenizer: MeCabTokenizer,
) -> QueryAnalyzer:
    """실제 MeCab 싱글톤을 사용하는 실제 QueryAnalyzer."""
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    return QueryAnalyzer(
        tokenizer=real_tokenizer,
    )


# ---------------------------------------------------------------------------
# DI 가짜 — MeCab과 독립적으로 파이프라인 로직을 검증하는 모든 곳에서 사용
# ---------------------------------------------------------------------------


class FakeNormalizer:
    """DI 기반 파이프라인 테스트를 위한 통과(pass-through) 정규화기."""

    def __init__(
        self,
        transform: Callable[[str], str] | None = None,
    ) -> None:
        self._transform = transform

    def normalize(self, text: str) -> str:
        if self._transform is None:
            return text.strip()
        return self._transform(text)


class FakeTokenizer:
    """QueryAnalyzer 파이프라인 테스트를 위한 구성 가능한 인메모리 토크나이저."""

    def __init__(
        self,
        tokens: list[tuple[str, str]] | None = None,
    ) -> None:
        # tokens는 (surface, pos) 쌍의 리스트입니다.
        self._tokens: list[tuple[str, str]] = tokens or []

    def configure(self, tokens: list[tuple[str, str]]) -> None:
        """구성된 (surface, pos) 시퀀스를 교체합니다."""
        self._tokens = tokens

    def tokenize(
        self,
        text: str,
        pos_filter: frozenset[str] | None = None,
        remove_stopwords: bool = False,
        stopwords: frozenset[str] | None = None,
    ) -> list[str]:
        from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS

        active_stop = (
            (stopwords if stopwords is not None else DEFAULT_STOPWORDS)
            if remove_stopwords
            else None
        )
        out: list[str] = []
        for surface, pos in self._tokens:
            if pos_filter is not None and pos.split("+")[0] not in pos_filter:
                continue
            if active_stop is not None and surface in active_stop:
                continue
            out.append(surface)
        return out

    def analyze(self, text: str) -> list[MorphToken]:
        from bpmg_korean_nlp.models import MorphToken

        result: list[MorphToken] = []
        cursor = 0
        for surface, pos in self._tokens:
            start = text.find(surface, cursor)
            if start < 0:
                start = cursor
            end = start + len(surface)
            cursor = end
            result.append(
                MorphToken(
                    surface=surface,
                    lemma=surface,
                    pos=pos,
                    start=start,
                    end=end,
                )
            )
        return result


@pytest.fixture
def fake_normalizer() -> FakeNormalizer:
    """테스트마다 새로운 통과(pass-through) 정규화기."""
    return FakeNormalizer()


@pytest.fixture
def fake_tokenizer() -> FakeTokenizer:
    """테스트마다 새로운 빈 가짜 토크나이저 — ``.configure(...)``으로 구성하세요."""
    return FakeTokenizer()


@pytest.fixture
def di_query_analyzer(
    fake_normalizer: FakeNormalizer,
    fake_tokenizer: FakeTokenizer,
) -> QueryAnalyzer:
    """가짜로만 구성된 QueryAnalyzer (MeCab 불필요)."""
    from bpmg_korean_nlp.query_analyzer import QueryAnalyzer

    return QueryAnalyzer(
        normalizer=fake_normalizer,  # type: ignore[arg-type]
        tokenizer=fake_tokenizer,  # type: ignore[arg-type]
    )


@pytest.fixture(autouse=True)
def _reset_default_analyzer() -> Iterator[None]:
    """테스트 간에 모듈 수준의 기본 QueryAnalyzer를 초기화합니다.

    가짜 DI 테스트가 이후 테스트에서 실수로 재사용할 수 있는 부분적으로
    모킹된 싱글톤을 남기는 것을 방지합니다.
    """
    yield
    try:
        from bpmg_korean_nlp import query_analyzer as qa_module

        qa_module._default_analyzer = None
    except ImportError:
        pass

"""MeCab 기반 한국어 형태소 토크나이저.

토크나이저는 ``python-mecab-ko`` 바인딩(프로젝트 정책상 KoNLPy는 금지)을 래핑하고
두 가지 공개 메서드를 제공합니다:

* :meth:`MeCabTokenizer.tokenize` — 선택적 POS 필터 및 불용어 제거가 있는
  BM25 lexical 검색용 ``list[str]``.
* :meth:`MeCabTokenizer.analyze` — 그래프 추출 및 설명 가능성을 위한
  ``surface`` / ``lemma`` / ``pos`` / ``(start, end)`` 문자 오프셋을 담은
  ``list[MorphToken]``.

mecab-ko-dic 로드는 비용이 큽니다(수십 MB, 수백 ms). 인스턴스는
``(dict_path, user_dict_path)``를 키로 클래스에 캐시됩니다 — 사전은 프로세스당
구성별로 최대 한 번만 초기화됩니다. ``MeCabTokenizer(...)``와 :meth:`get_instance`
모두 동일한 캐시된 객체로 해석됩니다.
"""

from __future__ import annotations

import threading
from typing import Any, ClassVar

from bpmg_korean_nlp.exceptions import InvalidInputError, MeCabNotAvailableError
from bpmg_korean_nlp.models import MorphToken
from bpmg_korean_nlp.stopwords import DEFAULT_STOPWORDS

__all__ = ["MeCabTokenizer"]


_InstanceKey = tuple[str | None, str | None]


def _ensure_str(text: object, *, name: str = "text") -> str:
    """*text*가 ``str``인지 검증하며, 그렇지 않으면 :class:`InvalidInputError`를 발생시킵니다.

    빈 문자열은 유효합니다(통과하여 빈 결과를 생성합니다).
    """
    if not isinstance(text, str):
        raise InvalidInputError(f"{name} must be a str, got {type(text).__name__}")
    return text


def _load_mecab(dict_path: str | None, user_dict_path: str | None) -> Any:
    """``mecab.MeCab`` 인스턴스를 생성하거나 예외를 발생시킵니다."""
    try:
        from mecab import MeCab as _MeCab
    except ImportError as exc:
        raise MeCabNotAvailableError(
            "python-mecab-ko is not installed. Install it with: pip install python-mecab-ko"
        ) from exc

    try:
        kwargs: dict[str, Any] = {}
        if dict_path is not None:
            kwargs["dictionary_path"] = dict_path
        if user_dict_path is not None:
            kwargs["user_dictionary_path"] = user_dict_path
        return _MeCab(**kwargs)
    except MeCabNotAvailableError:
        raise
    except Exception as exc:
        raise MeCabNotAvailableError(
            f"Failed to initialize MeCab (dict_path={dict_path!r}): {exc}"
        ) from exc


class MeCabTokenizer:
    """한국어를 위한 MeCab 기반 형태소 토크나이저.

    인자:
        dict_path: ``mecab-ko-dic``에 대한 선택적 명시적 경로. ``None``이면
            MeCab이 시스템 기본 위치를 자동으로 감지합니다.
        user_dict_path: 병합할 사용자 사전 경로(선택).

    예외:
        MeCabNotAvailableError: ``python-mecab-ko`` 바인딩이나 ``mecab-ko-dic``을
            로드할 수 없는 경우.

    인스턴스는 ``(dict_path, user_dict_path)``별로 캐시됩니다; 반복 생성 시
    동일한 객체를 반환하고 재초기화를 건너뜁니다.
    """

    _instances: ClassVar[dict[_InstanceKey, MeCabTokenizer]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    _initialized: bool
    _dict_path: str | None
    _user_dict_path: str | None
    _mecab: Any

    def __new__(
        cls,
        dict_path: str | None = None,
        user_dict_path: str | None = None,
    ) -> MeCabTokenizer:
        key: _InstanceKey = (dict_path, user_dict_path)
        with cls._lock:
            cached = cls._instances.get(key)
            if cached is not None:
                return cached
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
            return instance

    def __init__(
        self,
        dict_path: str | None = None,
        user_dict_path: str | None = None,
    ) -> None:
        if self._initialized:
            return
        try:
            self._dict_path = dict_path
            self._user_dict_path = user_dict_path
            self._mecab = _load_mecab(dict_path, user_dict_path)
            self._initialized = True
        except Exception:
            key: _InstanceKey = (dict_path, user_dict_path)
            with self.__class__._lock:
                if self.__class__._instances.get(key) is self:
                    del self.__class__._instances[key]
            raise

    @classmethod
    def get_instance(
        cls,
        dict_path: str | None = None,
        user_dict_path: str | None = None,
    ) -> MeCabTokenizer:
        """주어진 구성에 대한 공유 :class:`MeCabTokenizer`를 반환합니다.

        생성자 호출과 동일하며, 호출자가 "캐시된 싱글톤 가져오기"라는
        의도를 명시적으로 표현할 수 있도록 명명된 진입점으로 제공됩니다.
        """
        return cls(dict_path=dict_path, user_dict_path=user_dict_path)

    @classmethod
    def reset_instances(cls) -> None:
        """구성별 싱글톤 캐시를 초기화합니다. 테스트 전용 유틸리티."""
        with cls._lock:
            cls._instances.clear()

    @property
    def dict_path(self) -> str | None:
        """이 토크나이저가 초기화된 사전 경로."""
        return self._dict_path

    @property
    def user_dict_path(self) -> str | None:
        """이 토크나이저가 초기화된 사용자 사전 경로."""
        return self._user_dict_path

    def tokenize(
        self,
        text: str,
        pos_filter: frozenset[str] | None = None,
        remove_stopwords: bool = False,
        stopwords: frozenset[str] | None = None,
    ) -> list[str]:
        """*text*를 표층 형태소의 평탄한 리스트로 토큰화합니다.

        인자:
            text: 입력 문자열. ``""``은 유효하며 ``[]``을 반환합니다.
            pos_filter: 지정하면 집합 내 세종 POS 태그가 있는 형태소만 유지합니다.
                복합 태그(예: ``"NNG+JKS"``)는 첫 번째 구성요소로 매칭됩니다.
                ``None``이면 모든 POS를 유지합니다.
            remove_stopwords: ``True``이면 표층형이 *stopwords*(또는 *stopwords*가
                ``None``이면 :data:`DEFAULT_STOPWORDS`)에 있는 토큰을 제거합니다.
            stopwords: 사용자 정의 불용어 집합. ``remove_stopwords``가 ``False``이면
                무시됩니다.

        반환:
            문서 순서의 BM25 준비 표층 토큰 리스트.

        예외:
            InvalidInputError: *text*가 ``str``이 아닌 경우.
            MeCabNotAvailableError: 분석 중 MeCab이 실패한 경우.
        """
        text = _ensure_str(text)
        if not text:
            return []

        morphs = self._mecab_pos(text)
        active_stopwords: frozenset[str] | None
        if remove_stopwords:
            active_stopwords = stopwords if stopwords is not None else DEFAULT_STOPWORDS
        else:
            active_stopwords = None

        result: list[str] = []
        for surface, pos in morphs:
            if pos_filter is not None and pos.split("+")[0] not in pos_filter:
                continue
            if active_stopwords is not None and surface in active_stopwords:
                continue
            result.append(surface)
        return result

    def analyze(self, text: str) -> list[MorphToken]:
        """*text*의 풍부한 형태소 분석 결과를 반환합니다.

        각 :class:`MorphToken`은 표층형, 최선 노력 표제어(현재는 표층형 자체),
        세종 POS 태그, 원본 입력에서의 포함/제외 ``(start, end)`` 문자 오프셋을 담습니다.

        인자:
            text: 입력 문자열. ``""``은 유효하며 ``[]``을 반환합니다.

        반환:
            문서 순서의 형태소 토큰.

        예외:
            InvalidInputError: *text*가 ``str``이 아닌 경우.
            MeCabNotAvailableError: 분석 중 MeCab이 실패한 경우.
        """
        text = _ensure_str(text)
        if not text:
            return []

        morphs = self._mecab_pos(text)

        result: list[MorphToken] = []
        cursor = 0
        for surface, pos in morphs:
            start, end = self._locate(text, surface, cursor)
            cursor = end if start >= 0 else cursor
            if start < 0:
                start = cursor
                end = cursor + len(surface)
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

    @staticmethod
    def _locate(text: str, surface: str, cursor: int) -> tuple[int, int]:
        """*cursor* 위치부터 *text*에서 *surface*를 찾아 반환하며, 없으면 ``(-1, -1)``을 반환합니다.

        전역 검색으로 폴백하면 MeCab이 표층형이 정규화된 형태소를 출력하더라도
        오프셋이 단조롭게 유지됩니다 (``mecab-ko-dic``에서는 드물지만 문장 경계에서
        가능합니다).
        """
        if not surface:
            return -1, -1
        idx = text.find(surface, cursor)
        if idx < 0:
            idx = text.find(surface)
        if idx < 0:
            return -1, -1
        return idx, idx + len(surface)

    def _mecab_pos(self, text: str) -> list[tuple[str, str]]:
        """MeCab POS 분석을 실행하고 ``[(surface, pos_tag), ...]``를 반환합니다.

        ``python-mecab-ko`` 릴리스에서 볼 수 있는 다양한 반환 형태(일반 튜플 대
        ``Morpheme`` 유사 객체)를 단일 ``(str, str)`` 튜플 형태로 정규화합니다.
        복합 POS 태그(``"NNG+JKS"``)는 그대로 보존됩니다.
        """
        try:
            raw = self._mecab.pos(text)
        except Exception as exc:
            raise MeCabNotAvailableError(f"MeCab failed to analyze text: {exc}") from exc

        out: list[tuple[str, str]] = []
        for entry in raw:
            try:
                surface = entry[0]
                pos = entry[1]
            except (IndexError, TypeError, KeyError):
                continue
            if not isinstance(surface, str) or not isinstance(pos, str):
                continue
            out.append((surface, pos))
        return out

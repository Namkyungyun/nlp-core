"""Domain-agnostic Korean stopword set and helper for safe extension.

:data:`DEFAULT_STOPWORDS` is a ``frozenset`` so it is immutable at the type
level — any attempt to mutate it raises ``AttributeError`` at runtime.
Domain-specific stopwords (e.g. ``'수업'``, ``'교재'``) are intentionally
*not* included here; consumers must extend the set with
:func:`merge_stopwords`.
"""

from __future__ import annotations

__all__ = ["DEFAULT_STOPWORDS", "merge_stopwords"]


_PARTICLES: frozenset[str] = frozenset(
    {
        # 주격·보격·목적격·관형격·부사격 조사
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "의",
        "에",
        "에서",
        "에게",
        "에게서",
        "한테",
        "한테서",
        "께",
        "께서",
        "으로",
        "로",
        "으로써",
        "로써",
        "으로서",
        "로서",
        # 접속·공동·비교·도구 조사
        "와",
        "과",
        "하고",
        "이랑",
        "랑",
        "보다",
        "처럼",
        "같이",
        "만큼",
        "마냥",
        # 보조사
        "도",
        "만",
        "조차",
        "마저",
        "밖에",
        "뿐",
        "까지",
        "부터",
        "마다",
        "이나",
        "나",
        "이라도",
        "라도",
        "이며",
        "며",
        "이든",
        "든",
        "이든지",
        "든지",
        # 인용·존칭
        "라고",
        "이라고",
        "라며",
        "이라며",
    }
)


_AUX_VERBS_AND_ENDINGS: frozenset[str] = frozenset(
    {
        # 자주 쓰이는 동사·형용사 어간 (불용어 후보)
        "이다",
        "있다",
        "없다",
        "하다",
        "되다",
        "않다",
        "같다",
        "보다",
        "주다",
        "받다",
        # 의존명사·형식명사
        "것",
        "수",
        "때",
        "곳",
        "중",
        "데",
        "줄",
        "리",
        "체",
        "척",
        "등",
        "외",
        "내",
        # 부사·접속어
        "또",
        "또한",
        "그리고",
        "그러나",
        "하지만",
        "그래서",
        "따라서",
        "즉",
        "단",
        "혹은",
        "또는",
        "그런데",
        "그러므로",
        "그러면",
        "그렇지만",
        "더",
        "덜",
        "매우",
        "아주",
        "정말",
        "너무",
        "참",
        "다시",
        "이미",
        "아직",
        "곧",
        "방금",
        # 지시어·대명사
        "그",
        "이",
        "저",
        "그것",
        "이것",
        "저것",
        "여기",
        "거기",
        "저기",
        "어디",
        "언제",
        "누구",
        "무엇",
        "왜",
        # 수량·정도 표현
        "모든",
        "각",
        "어떤",
        "어느",
        "다른",
        "같은",
        "그런",
        "이런",
        "저런",
        # 수사
        "한",
        "두",
        "세",
        "네",
        "다섯",
        "여섯",
        "일곱",
        "여덟",
        "아홉",
        "열",
        # 빈도 높은 일반어 (도메인 비특화)
        "및",
        "위",
        "위해",
        "관련",
        "통해",
        "대해",
        "대한",
        "이와",
        "이러한",
        "그러한",
        "저러한",
        "본",
        "해당",
        "각종",
        "여러",
        "기타",
        "함께",
        "더욱",
        "역시",
        "결국",
    }
)


DEFAULT_STOPWORDS: frozenset[str] = _PARTICLES | _AUX_VERBS_AND_ENDINGS


def merge_stopwords(
    *additional: frozenset[str] | set[str],
    base: frozenset[str] | None = None,
) -> frozenset[str]:
    """Return a new ``frozenset`` combining *base* with every *additional* set.

    The original :data:`DEFAULT_STOPWORDS` is never modified — ``frozenset``
    union always produces a fresh object.

    Args:
        *additional: Zero or more sets of extra stopwords to union in.
        base: The starting set. When ``None`` (default),
            :data:`DEFAULT_STOPWORDS` is used.

    Returns:
        A frozen set containing every word from *base* and every word from
        every *additional* set.
    """
    starting: frozenset[str] = DEFAULT_STOPWORDS if base is None else frozenset(base)
    if not additional:
        return starting

    merged: set[str] = set(starting)
    for extra in additional:
        merged.update(extra)
    return frozenset(merged)

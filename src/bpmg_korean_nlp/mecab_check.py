"""``mecab-ko-dic`` 가용성 헬스 체크.

:class:`bpmg_korean_nlp.tokenizer.MeCabTokenizer`가 사용하는 바인딩 임포트 +
사전 로드 시퀀스를 래핑하고, 결과를 :class:`DictCheckResult` 값(성공 또는 실패,
모두 데이터로 표면화)으로 보고합니다. CI 파이프라인 및 컨테이너 시작 프로브를 위해
설계되었으며 — 사전이 없어도 예외를 발생시키지 않아 호출자가 중단 또는 저하 여부를
결정합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bpmg_korean_nlp.models import DictCheckResult

__all__ = ["check_mecab_dict"]


_DEFAULT_DICT_PATHS: tuple[str, ...] = (
    # macOS Homebrew (Intel)
    "/usr/local/lib/mecab/dic/mecab-ko-dic",
    # macOS Homebrew (Apple Silicon)
    "/opt/homebrew/lib/mecab/dic/mecab-ko-dic",
    # Ubuntu / Debian 시스템 패키지
    "/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ko-dic",
    "/usr/lib/aarch64-linux-gnu/mecab/dic/mecab-ko-dic",
    # 일반 설치 + Docker slim 이미지
    "/usr/share/mecab/dic/mecab-ko-dic",
    "/usr/local/share/mecab/dic/mecab-ko-dic",
)


def _detect_default_dict_path() -> str | None:
    """설치된 첫 번째 사전 경로를 반환하거나, 후보가 없으면 ``None``을 반환합니다."""
    for candidate in _DEFAULT_DICT_PATHS:
        if Path(candidate).is_dir():
            return candidate
    return None


def _read_dict_version(dict_path: str) -> str | None:
    """*dict_path* 아래의 ``dicrc``를 파싱하여 ``version`` 값을 반환합니다.

    파일이 없거나, 읽을 수 없거나, ``version`` 키가 없으면 ``None``을 반환합니다 —
    버전 보고는 최선 노력(best-effort)이며 가용성 체크를 차단하지 않습니다.
    """
    dicrc = Path(dict_path) / "dicrc"
    if not dicrc.is_file():
        return None
    try:
        text = dicrc.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if key.strip().lower() == "version":
            v = value.strip()
            return v or None
    return None


def check_mecab_dict(dict_path: str | None = None) -> DictCheckResult:
    """``mecab-ko-dic``이 설치되어 있고 로드 가능한지 확인합니다.

    인자:
        dict_path: 확인할 사전 경로를 명시적으로 지정합니다. ``None``이면
            잘 알려진 설치 위치 목록(macOS Homebrew, Ubuntu, Docker slim)으로
            폴백합니다.

    반환:
        :class:`DictCheckResult`. ``python-mecab-ko`` 바인딩이 정상적으로
        임포트되고 스모크 테스트 분석이 성공하면 ``available=True``.
        실패 시 ``error``에 한 줄 진단 메시지가 담깁니다.
    """
    try:
        from mecab import MeCab as _MeCab
    except ImportError as exc:
        return DictCheckResult(
            available=False,
            dict_path=None,
            version=None,
            error=f"python-mecab-ko not installed: {exc}",
        )

    resolved_path = dict_path if dict_path is not None else _detect_default_dict_path()

    try:
        kwargs: dict[str, Any] = {}
        if resolved_path is not None:
            kwargs["dictionary_path"] = resolved_path
        tagger = _MeCab(**kwargs)
        tagger.pos("테스트")
    except Exception as exc:
        return DictCheckResult(
            available=False,
            dict_path=resolved_path,
            version=None,
            error=f"MeCab init failed: {exc}",
        )

    version = _read_dict_version(resolved_path) if resolved_path is not None else None
    return DictCheckResult(
        available=True,
        dict_path=resolved_path,
        version=version,
        error=None,
    )

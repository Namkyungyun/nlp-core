"""Health check for ``mecab-ko-dic`` availability.

Wraps the binding-import + dictionary-load sequence used by
:class:`bpmg_korean_nlp.tokenizer.MeCabTokenizer` and reports the outcome
as a :class:`DictCheckResult` value (success or failure, both surfaced
as data). Designed for CI pipelines and container startup probes — it
never raises for a missing dictionary, so the caller decides whether to
abort or degrade.
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
    # Ubuntu / Debian system packages
    "/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ko-dic",
    "/usr/lib/aarch64-linux-gnu/mecab/dic/mecab-ko-dic",
    # Generic install + Docker slim image
    "/usr/share/mecab/dic/mecab-ko-dic",
    "/usr/local/share/mecab/dic/mecab-ko-dic",
)


def _detect_default_dict_path() -> str | None:
    """Return the first installed dictionary path or ``None`` if no candidate exists."""
    for candidate in _DEFAULT_DICT_PATHS:
        if Path(candidate).is_dir():
            return candidate
    return None


def _read_dict_version(dict_path: str) -> str | None:
    """Parse ``dicrc`` under *dict_path* and return its ``version`` value.

    Returns ``None`` if the file is missing, unreadable, or carries no
    ``version`` key — version reporting is best-effort and never blocks
    a successful availability check.
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
    """Probe whether ``mecab-ko-dic`` is installed and loadable.

    Args:
        dict_path: Explicit dictionary path to probe. When ``None``,
            falls back to a list of well-known install locations
            (macOS Homebrew, Ubuntu, Docker slim).

    Returns:
        A :class:`DictCheckResult`. ``available=True`` iff the
        ``python-mecab-ko`` binding imports cleanly *and* a smoke-test
        analysis succeeds. On failure, ``error`` carries a one-line
        diagnostic.
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

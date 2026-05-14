#!/usr/bin/env python3
"""금지된 패키지 간 임포트에 대한 정적 방어막.

이 스크립트는 하나 이상의 소스 루트 아래의 모든 ``.py`` 파일을 정적으로 스캔하고
아래의 금지 목록에 있는 패키지를 임포트하는 파일이 있으면 비정상 상태로 종료합니다.
위반이 빌드를 즉시 실패시키도록 테스트 실행 전 CI에서 호출됩니다.

금지된 패키지
-------------
- retrieval-core / retrieval_core
- guardrail-core / guardrail_core
- chatbot-contracts / chatbot_contracts

사용법
------
    python scripts/check_imports.py src/
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

FORBIDDEN_PACKAGES: frozenset[str] = frozenset(
    {
        "retrieval_core",
        "retrieval-core",
        "guardrail_core",
        "guardrail-core",
        "chatbot_contracts",
        "chatbot-contracts",
    }
)


def _normalize(name: str) -> str:
    """점으로 구분된 모듈 이름의 최상위 패키지를 비교 가능한 형태로 반환합니다."""
    head = name.split(".", 1)[0]
    return head.replace("-", "_")


def _iter_python_files(roots: Iterable[Path]) -> Iterator[Path]:
    """``roots`` 아래의 모든 ``.py`` 파일을 순서대로 반환합니다."""
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        if not root.is_dir():
            continue
        yield from sorted(root.rglob("*.py"))


def _violations_in_file(path: Path) -> list[tuple[int, str]]:
    """*path*에서 금지된 임포트에 대한 ``(lineno, package)`` 쌍을 반환합니다.

    파싱에 실패한 파일은 자동으로 건너뜁니다 — 구문 오류는 다른 문제이며
    다른 도구(ruff, mypy)를 통해 표면화됩니다.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return []

    forbidden_norm = {_normalize(p) for p in FORBIDDEN_PACKAGES}
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _normalize(alias.name) in forbidden_norm:
                    found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module and _normalize(module) in forbidden_norm:
                found.append((node.lineno, module))
    return found


def check(roots: Iterable[Path]) -> int:
    """*roots*를 스캔하고 정상이면 ``0``, 위반이 있으면 ``1``을 반환합니다."""
    violations: list[tuple[Path, int, str]] = []
    for file_path in _iter_python_files(roots):
        for lineno, package in _violations_in_file(file_path):
            violations.append((file_path, lineno, package))

    if not violations:
        return 0

    print("금지된 임포트가 감지됨:", file=sys.stderr)
    for file_path, lineno, package in violations:
        print(f"  {file_path}:{lineno}: {package!r} 임포트", file=sys.stderr)
    print(
        f"\n{len(violations)}개 위반. "
        f"금지된 패키지: {sorted(FORBIDDEN_PACKAGES)}",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str]) -> int:
    """CLI 진입점. 프로세스 종료 코드를 반환합니다."""
    if len(argv) < 2:
        print("사용법: check_imports.py <경로> [<경로> ...]", file=sys.stderr)
        return 2
    roots = [Path(arg) for arg in argv[1:]]
    return check(roots)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

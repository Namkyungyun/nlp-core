#!/usr/bin/env python3
"""Static guard against forbidden cross-package imports.

This script statically scans every ``.py`` file under one or more source
roots and exits with a non-zero status if any file imports a package from
the forbidden list below. It is invoked in CI before tests run so that a
violation fails the build immediately.

Forbidden packages
------------------
- retrieval-core / retrieval_core
- guardrail-core / guardrail_core
- chatbot-contracts / chatbot_contracts

Usage
-----
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
    """Return a comparable form of a dotted module name's top-level package."""
    head = name.split(".", 1)[0]
    return head.replace("-", "_")


def _iter_python_files(roots: Iterable[Path]) -> Iterator[Path]:
    """Yield every ``.py`` file beneath ``roots``."""
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        if not root.is_dir():
            continue
        yield from sorted(root.rglob("*.py"))


def _violations_in_file(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, package)`` pairs for any forbidden imports in *path*.

    Files that fail to parse are silently skipped — a syntax error is a
    different problem and is surfaced by other tools (ruff, mypy).
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
    """Scan *roots* and return ``0`` when clean, ``1`` when violations exist."""
    violations: list[tuple[Path, int, str]] = []
    for file_path in _iter_python_files(roots):
        for lineno, package in _violations_in_file(file_path):
            violations.append((file_path, lineno, package))

    if not violations:
        return 0

    print("Forbidden imports detected:", file=sys.stderr)
    for file_path, lineno, package in violations:
        print(f"  {file_path}:{lineno}: imports {package!r}", file=sys.stderr)
    print(
        f"\n{len(violations)} violation(s). "
        f"Forbidden packages: {sorted(FORBIDDEN_PACKAGES)}",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str]) -> int:
    """CLI entry point. Returns the process exit code."""
    if len(argv) < 2:
        print("usage: check_imports.py <path> [<path> ...]", file=sys.stderr)
        return 2
    roots = [Path(arg) for arg in argv[1:]]
    return check(roots)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

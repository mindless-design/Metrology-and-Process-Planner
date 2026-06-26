"""Run interrogate docstring coverage without badge-generation imports."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Optional

from interrogate.config import InterrogateConfig
from interrogate.visit import CoverageVisitor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECK_ROOTS = (PROJECT_ROOT / "python", PROJECT_ROOT / "tools")
FAIL_UNDER = 85.0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run docstring coverage and return a process code."""

    paths = tuple(Path(item) for item in argv) if argv else tuple(_iter_python_files())
    covered, total = _coverage(paths)
    percent = 100.0 if total == 0 else covered / total * 100.0
    print(f"Interrogate coverage: {percent:.2f}% ({covered}/{total})")
    if percent < FAIL_UNDER:
        print(f"Docstring coverage below {FAIL_UNDER:.0f}%.")
        return 1
    return 0


def _iter_python_files() -> Iterable[Path]:
    for root in CHECK_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" not in path.parts:
                yield path


def _coverage(paths: Iterable[Path]) -> tuple[int, int]:
    config = InterrogateConfig(
        ignore_init_method=True,
        ignore_init_module=True,
        ignore_magic=True,
        ignore_module=False,
        ignore_private=True,
        ignore_semiprivate=True,
        ignore_nested_functions=True,
        fail_under=FAIL_UNDER,
    )
    covered = 0
    total = 0
    for path in paths:
        if _skip_path(path):
            continue
        visitor = CoverageVisitor(str(path), config)
        visitor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        for node in visitor.nodes:
            total += 1
            covered += int(bool(node.covered))
    return covered, total


def _skip_path(path: Path) -> bool:
    return path.name == "__init__.py" or any(
        part in {"build", "dist", ".venv", "pymacros"} for part in path.parts
    )


if __name__ == "__main__":
    raise SystemExit(main())

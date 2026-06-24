"""Project-specific maintainability gates with no third-party dependencies."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Optional

from tools.quality_models import PROJECT_ROOT, QualityViolation

SOURCE_ROOTS = (
    PROJECT_ROOT / "python" / "metrology_process_planner",
    PROJECT_ROOT / "pymacros",
    PROJECT_ROOT / "tools",
)
TEST_ROOTS = (PROJECT_ROOT / "tests",)
MAX_SOURCE_FILE_LINES = 220
MAX_TEST_FILE_LINES = 180
MAX_FUNCTION_LINES = 50
MAX_CLASS_LINES = 140
MAX_PUBLIC_DEFS_PER_MODULE = 12
MIN_DOCSTRING_SUMMARY_CHARS = 12
PLACEHOLDER_DOCSTRING_WORDS = ("todo", "tbd", "fixme")

def run_quality_gates(paths: Optional[Sequence[Path]] = None) -> list[QualityViolation]:
    """Run all configured quality gates and return violations."""

    files = list(paths) if paths is not None else list(_iter_project_python_files())
    violations: list[QualityViolation] = []
    for path in files:
        if not _is_python_file(path):
            continue
        violations.extend(_check_file_size(path))
        violations.extend(_check_ast_rules(path))
    return sorted(violations, key=lambda item: (str(item.path), item.line, item.rule))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command-line quality gate."""

    parser = argparse.ArgumentParser(description="Run project-specific maintainability gates.")
    parser.add_argument("paths", nargs="*", type=Path, help="Optional Python files to check.")
    args = parser.parse_args(argv)

    paths = tuple(args.paths) if args.paths else None
    violations = run_quality_gates(paths)
    if violations:
        for violation in violations:
            print(violation.format())
        print(f"\nQuality gates failed with {len(violations)} violation(s).")
        return 1
    print("Quality gates passed.")
    return 0


def _iter_project_python_files() -> Iterable[Path]:
    for root in SOURCE_ROOTS + TEST_ROOTS:
        yield from sorted(root.rglob("*.py"))


def _is_python_file(path: Path) -> bool:
    return path.suffix == ".py" and "__pycache__" not in path.parts


def _check_file_size(path: Path) -> list[QualityViolation]:
    line_count = _count_lines(path)
    max_lines = MAX_TEST_FILE_LINES if _is_test_file(path) else MAX_SOURCE_FILE_LINES
    if line_count <= max_lines:
        return []
    return [
        QualityViolation(
            path=path,
            line=max_lines + 1,
            rule="MPP001",
            message=f"file has {line_count} lines; split it below {max_lines} lines",
        )
    ]


def _check_ast_rules(path: Path) -> list[QualityViolation]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    violations = _check_module_public_shape(path, tree)
    if not _is_test_file(path):
        violations.extend(_check_public_docstrings(path, tree))
    violations.extend(_check_node_lengths(path, tree))
    return violations


def _check_module_public_shape(path: Path, tree: ast.Module) -> list[QualityViolation]:
    public_defs = [
        node
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]
    if len(public_defs) <= MAX_PUBLIC_DEFS_PER_MODULE:
        return []
    return [
        QualityViolation(
            path=path,
            line=1,
            rule="MPP002",
            message=(
                f"module defines {len(public_defs)} public symbols; "
                f"split above {MAX_PUBLIC_DEFS_PER_MODULE}"
            ),
        )
    ]


def _check_public_docstrings(path: Path, tree: ast.Module) -> list[QualityViolation]:
    violations: list[QualityViolation] = []
    if not _has_good_docstring(ast.get_docstring(tree)):
        violations.append(_docstring_violation(path, 1, "module"))
    for node in _iter_public_api_nodes(tree):
        if (
            isinstance(node, ast.ClassDef)
            and not node.name.startswith("_")
            and not _has_good_docstring(ast.get_docstring(node))
        ):
            violations.append(_docstring_violation(path, node.lineno, f"class {node.name}"))
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and _requires_function_docstring(node)
            and not _has_good_docstring(ast.get_docstring(node))
        ):
            target = f"function {node.name}"
            violations.append(_docstring_violation(path, node.lineno, target))
    return violations


def _iter_public_api_nodes(tree: ast.Module) -> Iterable[ast.AST]:
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield child


def _requires_function_docstring(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return not node.name.startswith("_")


def _docstring_violation(path: Path, line: int, target: str) -> QualityViolation:
    return QualityViolation(
        path=path,
        line=line,
        rule="MPP003",
        message=f"{target} needs a real docstring summary ending with a period",
    )


def _has_good_docstring(docstring: Optional[str]) -> bool:
    if docstring is None:
        return False
    summary = docstring.strip().splitlines()[0].strip()
    if len(summary) < MIN_DOCSTRING_SUMMARY_CHARS or not summary.endswith("."):
        return False
    lowered = summary.lower()
    return not any(word in lowered for word in PLACEHOLDER_DOCSTRING_WORDS)


def _check_node_lengths(path: Path, tree: ast.Module) -> list[QualityViolation]:
    violations: list[QualityViolation] = []
    for node in ast.walk(tree):
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            continue
        line_count = int(node.end_lineno) - int(node.lineno) + 1
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and line_count > MAX_FUNCTION_LINES
        ):
            target = f"function {node.name}"
            violations.append(_length_violation(path, node.lineno, "MPP004", target, line_count))
        if isinstance(node, ast.ClassDef) and line_count > MAX_CLASS_LINES:
            violations.append(
                _length_violation(path, node.lineno, "MPP005", f"class {node.name}", line_count)
            )
    return violations


def _length_violation(
    path: Path,
    line: int,
    rule: str,
    target: str,
    line_count: int,
) -> QualityViolation:
    max_lines = MAX_FUNCTION_LINES if rule == "MPP004" else MAX_CLASS_LINES
    return QualityViolation(
        path=path,
        line=line,
        rule=rule,
        message=f"{target} has {line_count} lines; split below {max_lines}",
    )


def _is_test_file(path: Path) -> bool:
    try:
        path.relative_to(PROJECT_ROOT / "tests")
    except ValueError:
        return False
    return True


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


if __name__ == "__main__":
    raise SystemExit(main())

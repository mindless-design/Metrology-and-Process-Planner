"""Package tree rules for release artifacts."""

from __future__ import annotations

from pathlib import Path

PACKAGE_INCLUDE_ROOTS = (
    "grain.xml",
    "README.md",
    "docs",
    "pymacros",
    "python",
)

EXCLUDED_DIR_NAMES = {
    ".git",
    ".import_linter_cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}

EXCLUDED_SUFFIXES = {
    ".bak",
    ".log",
    ".pyc",
    ".tmp",
}


def is_release_file(path: Path, project_root: Path) -> bool:
    """Return whether a path should be included in a KLayout package."""

    relative = path.relative_to(project_root)
    if any(part in EXCLUDED_DIR_NAMES for part in relative.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    first_part = relative.parts[0]
    return first_part in PACKAGE_INCLUDE_ROOTS


def iter_release_files(project_root: Path) -> tuple[Path, ...]:
    """Return all package files sorted by portable relative path."""

    files = [
        path
        for path in project_root.rglob("*")
        if path.is_file() and is_release_file(path, project_root)
    ]
    return tuple(sorted(files, key=lambda path: path.relative_to(project_root).as_posix()))


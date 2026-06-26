"""Report package-boundary and deprecated import violations."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from tools.import_audit_policy import APPROVED_PYA_ROOTS, DEPRECATED_IMPORTS

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "python" / "metrology_process_planner"


@dataclass(frozen=True)
class ImportedName:
    """Imported module name with source line."""

    module: str
    line: int


@dataclass(frozen=True)
class ImportAudit:
    """Structured import audit result."""

    deprecated_imports: tuple[str, ...]
    pya_outside_klayout: tuple[str, ...]
    solver_runtime_imports: tuple[str, ...]
    domain_runtime_imports: tuple[str, ...]

    def violations(self) -> tuple[str, ...]:
        """Return all actionable violations."""

        return (
            self.deprecated_imports
            + self.pya_outside_klayout
            + self.solver_runtime_imports
            + self.domain_runtime_imports
        )


def audit_imports() -> ImportAudit:
    """Audit package imports for deprecated paths and forbidden dependencies."""

    imports_by_file = {path: _imports(path) for path in _source_files()}
    return ImportAudit(
        deprecated_imports=tuple(_deprecated_imports(imports_by_file)),
        pya_outside_klayout=tuple(_pya_outside_klayout(imports_by_file)),
        solver_runtime_imports=tuple(
            _forbidden_imports(
                imports_by_file,
                PACKAGE_ROOT / "solver",
                ("pya", "PyQt5", "PySide2", "PySide6", "metrology_process_planner.ui"),
            )
        ),
        domain_runtime_imports=tuple(
            _forbidden_imports(
                imports_by_file,
                PACKAGE_ROOT / "domains",
                (
                    "pya",
                    "PyQt5",
                    "PySide2",
                    "PySide6",
                    "metrology_process_planner.ui",
                    "metrology_process_planner.infrastructure.klayout",
                ),
            )
        ),
    )


def _deprecated_imports(imports_by_file: dict[Path, tuple[ImportedName, ...]]) -> list[str]:
    violations: list[str] = []
    for path, imports in imports_by_file.items():
        for old_path, replacement in DEPRECATED_IMPORTS.items():
            for imported in imports:
                if _matches(imported.module, old_path):
                    violations.append(
                        f"{_rel(path)}:{imported.line} imports deprecated {old_path}; "
                        f"use {replacement}"
                    )
    return violations


def _pya_outside_klayout(imports_by_file: dict[Path, tuple[ImportedName, ...]]) -> list[str]:
    violations: list[str] = []
    for path, imports in imports_by_file.items():
        if any(_is_relative_to(path, root) for root in APPROVED_PYA_ROOTS):
            continue
        if any(_matches(imported.module, "pya") for imported in imports):
            violations.append(f"{_rel(path)} imports pya outside KLayout infrastructure")
    return violations


def _forbidden_imports(
    imports_by_file: dict[Path, tuple[ImportedName, ...]],
    root: Path,
    forbidden: tuple[str, ...],
) -> list[str]:
    violations: list[str] = []
    for path, imports in imports_by_file.items():
        if not _is_relative_to(path, root):
            continue
        for imported in imports:
            if any(_matches(imported.module, prefix) for prefix in forbidden):
                violations.append(
                    f"{_rel(path)}:{imported.line} imports forbidden {imported.module}"
                )
    return violations


def _source_files() -> tuple[Path, ...]:
    roots = (ROOT / "python", ROOT / "tests", ROOT / "tools")
    return tuple(
        path
        for root in roots
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in path.parts
    )


def _imports(path: Path) -> tuple[ImportedName, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[ImportedName] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(ImportedName(alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(ImportedName(node.module, node.lineno))
    return tuple(names)


def _matches(imported: str, prefix: str) -> bool:
    return imported == prefix or imported.startswith(f"{prefix}.")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    """Print the import audit report."""

    audit = audit_imports()
    for label, values in (
        ("deprecated_imports", audit.deprecated_imports),
        ("pya_outside_klayout", audit.pya_outside_klayout),
        ("solver_runtime_imports", audit.solver_runtime_imports),
        ("domain_runtime_imports", audit.domain_runtime_imports),
    ):
        print(f"== {label} ==")
        if values:
            print("\n".join(values))
        else:
            print("OK")
    return 1 if audit.violations() else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Import boundary checks for the visible package architecture."""

from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

from tools.audit_imports import audit_imports
from tools.import_audit_policy import deprecated_shim_paths

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = ROOT / "python" / "metrology_process_planner"

class ImportBoundaryTests(unittest.TestCase):
    """Guard architectural package boundaries without importing KLayout."""

    def test_package_import_smoke(self) -> None:
        modules = (
            "metrology_process_planner.app.commands",
            "metrology_process_planner.diagnostics",
            "metrology_process_planner.domains.artifacts",
            "metrology_process_planner.domains.capture",
            "metrology_process_planner.domains.measurement",
            "metrology_process_planner.domains.modes",
            "metrology_process_planner.domains.process",
            "metrology_process_planner.domains.session",
            "metrology_process_planner.persistence.json_store",
            "metrology_process_planner.rendering.cross_section.pipeline",
            "metrology_process_planner.reporting.builder",
            "metrology_process_planner.solver",
            "metrology_process_planner.ui.session_editor.shell",
        )

        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_canonical_modules_import_cleanly(self) -> None:
        modules = (
            "metrology_process_planner.domains.session.record",
            "metrology_process_planner.domains.modes.mode_registry",
            "metrology_process_planner.domains.artifacts.artifact_registry",
            "metrology_process_planner.domains.capture.capture_geometry",
            "metrology_process_planner.domains.measurement.records",
            "metrology_process_planner.domains.warnings.warnings",
            "metrology_process_planner.workflows.measurement_workflow",
            "metrology_process_planner.persistence.json_store",
            "metrology_process_planner.solver.hybrid_solver",
            "metrology_process_planner.rendering.specs",
            "metrology_process_planner.reporting.builder",
            "metrology_process_planner.diagnostics.diagnostics_project",
        )

        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_domains_do_not_import_runtime_or_ui_frameworks(self) -> None:
        forbidden = (
            "pya",
            "PyQt5",
            "PySide2",
            "PySide6",
            "matplotlib",
            "metrology_process_planner.infrastructure.klayout",
            "metrology_process_planner.ui",
        )

        violations = _forbidden_imports(PACKAGE_ROOT / "domains", forbidden)

        self.assertEqual([], violations)

    def test_solver_stays_runtime_and_ui_independent(self) -> None:
        forbidden = (
            "pya",
            "PyQt5",
            "PySide2",
            "PySide6",
            "metrology_process_planner.infrastructure.klayout",
            "metrology_process_planner.reporting",
            "metrology_process_planner.ui",
        )

        violations = _forbidden_imports(PACKAGE_ROOT / "solver", forbidden)

        self.assertEqual([], violations)

    def test_persistence_and_reporting_do_not_import_ui(self) -> None:
        forbidden = ("metrology_process_planner.ui",)

        violations = _forbidden_imports(PACKAGE_ROOT / "persistence", forbidden)
        violations.extend(_forbidden_imports(PACKAGE_ROOT / "reporting", forbidden))

        self.assertEqual([], violations)

    def test_old_flat_paths_are_not_used_by_new_implementation(self) -> None:
        audit = audit_imports()

        self.assertEqual([], list(audit.deprecated_imports))

    def test_deprecated_shims_are_removed_from_architecture_packages(self) -> None:
        existing = [
            str(path.relative_to(ROOT)) for path in sorted(deprecated_shim_paths()) if path.exists()
        ]

        self.assertEqual([], existing)

    def test_ui_does_not_write_session_json_directly(self) -> None:
        violations = []
        for path in sorted((PACKAGE_ROOT / "ui").rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            if "json.dump(" in text or "session.json" in text or "atomic_write(" in text:
                violations.append(str(path.relative_to(ROOT)))

        self.assertEqual([], violations)


def _forbidden_imports(root: Path, forbidden: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for imported in _imports(path):
            if any(_matches(imported, prefix) for prefix in forbidden):
                relative = path.relative_to(ROOT)
                violations.append(f"{relative}: imports {imported}")
    return violations


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return tuple(names)


def _matches(imported: str, prefix: str) -> bool:
    return imported == prefix or imported.startswith(f"{prefix}.")


if __name__ == "__main__":
    unittest.main()

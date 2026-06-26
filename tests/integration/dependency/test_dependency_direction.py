"""Integration checks for package dependency direction."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PYTHON_ROOT = ROOT / "python" / "metrology_process_planner"


FORBIDDEN_IMPORTS = {
    "domains": (
        "metrology_process_planner.app",
        "metrology_process_planner.ui",
        "metrology_process_planner.infrastructure",
        "pya",
    ),
    "workflows": (
        "metrology_process_planner.app",
        "metrology_process_planner.ui",
        "metrology_process_planner.infrastructure.klayout",
        "pya",
    ),
    "persistence": (
        "metrology_process_planner.app",
        "metrology_process_planner.ui",
        "metrology_process_planner.infrastructure.klayout",
        "pya",
    ),
    "rendering": (
        "metrology_process_planner.app",
        "metrology_process_planner.ui",
        "metrology_process_planner.infrastructure.klayout",
        "pya",
    ),
    "reporting": (
        "metrology_process_planner.app",
        "metrology_process_planner.ui",
        "metrology_process_planner.infrastructure.klayout",
        "pya",
    ),
}


def test_core_layers_do_not_import_app_ui_or_klayout_adapters() -> None:
    """Keep document/workflow layers independent of UI and KLayout runtime state."""

    violations: list[str] = []
    for layer, forbidden_prefixes in FORBIDDEN_IMPORTS.items():
        for path in sorted((PYTHON_ROOT / layer).rglob("*.py")):
            for imported in _imports(path):
                if any(_matches(imported, prefix) for prefix in forbidden_prefixes):
                    relative = path.relative_to(ROOT)
                    violations.append(f"{relative}: imports {imported}")
    assert not violations, "\n".join(violations)


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

"""Run optional third-party static analysis tools."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"


@dataclass(frozen=True)
class ToolCommand:
    """One optional static-analysis command."""

    name: str
    executable: str
    args: tuple[str, ...]
    required: bool = False

    def command_line(self) -> list[str]:
        """Return a subprocess-ready command line."""

        return [self.executable, *self.args]


DEFAULT_COMMANDS: tuple[ToolCommand, ...] = (
    ToolCommand("quality gates", sys.executable, ("-m", "tools.quality_gates"), required=True),
    ToolCommand("ruff", sys.executable, ("-m", "ruff", "check", ".")),
    ToolCommand("mypy", sys.executable, ("-m", "mypy", "python", "tools")),
    ToolCommand(
        "xenon",
        "xenon",
        ("--max-absolute", "B", "--max-modules", "A", "--max-average", "A", "python", "tools"),
    ),
    ToolCommand("radon maintainability", "radon", ("mi", "-s", "python", "tools")),
    ToolCommand("interrogate", sys.executable, ("-m", "tools.interrogate_check")),
    ToolCommand("import linter", "lint-imports", ("--config", "pyproject.toml")),
    ToolCommand("vulture", "vulture", ("python", "tools", "vulture_whitelist.py")),
)


def run_static_analysis(
    commands: Sequence[ToolCommand] = DEFAULT_COMMANDS,
    *,
    fail_on_missing: bool = False,
) -> int:
    """Run configured static-analysis commands and return a process code."""

    failures = 0
    for command in commands:
        if _is_missing(command):
            failures += _handle_missing(command, fail_on_missing)
            continue
        print(f"\n== {command.name} ==")
        result = subprocess.run(
            command.command_line(),
            cwd=PROJECT_ROOT,
            check=False,
            env=_analysis_environment(),
        )
        if result.returncode != 0:
            failures += 1
    return 1 if failures else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run optional analysis tools from the command line."""

    parser = argparse.ArgumentParser(description="Run optional static-analysis tools.")
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Fail if optional tools are not installed.",
    )
    args = parser.parse_args(argv)
    return run_static_analysis(fail_on_missing=args.fail_on_missing)


def _is_missing(command: ToolCommand) -> bool:
    """Return whether an optional executable is unavailable."""

    if command.executable == sys.executable:
        return False
    return shutil.which(command.executable) is None


def _handle_missing(command: ToolCommand, fail_on_missing: bool) -> int:
    """Report a missing optional tool and return its failure code."""

    print(f"\n== {command.name} ==")
    print(f"Skipped because {command.executable!r} is not installed.")
    return 1 if fail_on_missing or command.required else 0


def _analysis_environment() -> dict[str, str]:
    """Return an environment that exposes the KLayout package python folder."""

    environment = dict(os.environ)
    existing_path = environment.get("PYTHONPATH")
    paths = [str(PYTHON_ROOT)]
    if existing_path:
        paths.append(existing_path)
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    return environment


if __name__ == "__main__":
    raise SystemExit(main())

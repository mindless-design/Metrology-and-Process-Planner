"""Run the local shippability checklist."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional

from tools.build_package import build_package, stage_package

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"


def run_release_check(*, include_klayout: bool = False) -> int:
    """Run release checks and return a process code."""

    failures = 0
    failures += _check_metadata()
    failures += _run([sys.executable, "-m", "tools.static_analysis", "--fail-on-missing"])
    failures += _run([sys.executable, "-m", "tools.project_health"])
    failures += _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."])
    failures += _run(
        [sys.executable, "-m", "compileall", "-q", "python", "tests", "tools", "pymacros"]
    )
    if include_klayout:
        failures += _run_klayout_lanes()
    failures += _check_staged_package()
    archive = build_package()
    print(f"Built package: {archive}")
    return 1 if failures else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run release checks from the command line."""

    parser = argparse.ArgumentParser(description="Run the shippability checklist.")
    parser.add_argument("--include-klayout", action="store_true")
    args = parser.parse_args(argv)
    return run_release_check(include_klayout=args.include_klayout)


def _check_metadata() -> int:
    grain_version = ET.parse(PROJECT_ROOT / "grain.xml").findtext("version")
    package_version = _read_package_version()
    if grain_version == package_version:
        return 0
    print(f"Version mismatch: grain.xml={grain_version}, package={package_version}")
    return 1


def _read_package_version() -> str:
    sys.path.insert(0, str(PYTHON_ROOT))
    import metrology_process_planner

    return metrology_process_planner.__version__


def _run(command: Sequence[str], *, env: Mapping[str, str] | None = None) -> int:
    print("\n== " + " ".join(command) + " ==")
    process_env = os.environ.copy()
    if env is not None:
        process_env.update(env)
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False, env=process_env)
    return 0 if result.returncode == 0 else 1


def _run_klayout_lanes() -> int:
    commands = (
        [sys.executable, "-m", "unittest", "tests.test_klayout_integration"],
        [sys.executable, "-m", "unittest", "tests.test_klayout_process_regression"],
        [sys.executable, "-m", "unittest", "tests.test_klayout_ui_automation"],
    )
    env = {
        "MPP_RUN_KLAYOUT_TESTS": "1",
        "MPP_RUN_KLAYOUT_UI_TESTS": "1",
    }
    return sum(_run(command, env=env) for command in commands)


def _check_staged_package() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        staged = stage_package(Path(temp_dir) / "package")
        required = ("grain.xml", "pymacros", "python/metrology_process_planner")
        missing = [item for item in required if not (staged / item).exists()]
    if not missing:
        return 0
    print("Staged package missing: " + ", ".join(missing))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

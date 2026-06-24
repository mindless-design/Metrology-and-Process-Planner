"""Helpers for running KLayout GUI automation probes."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

from tools.klayout_runner import (
    PACKAGE_PYTHON_ROOT,
    PROJECT_ROOT,
    klayout_environment,
    require_klayout_executable,
)


@dataclass(frozen=True)
class KLayoutUiRunResult:
    """Captured result from a GUI-mode KLayout UI probe."""

    executable: Path
    returncode: int
    stdout: str
    stderr: str
    report: dict[str, object]
    timed_out: bool = False


def run_klayout_ui_probe(script: str, timeout_seconds: int = 45) -> KLayoutUiRunResult:
    """Run a Python probe against a live KLayout GUI and return its report."""

    executable = require_klayout_executable()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        script_path = temp_path / "ui_probe.py"
        report_path = temp_path / "ui_report.json"
        script_path.write_text(_ui_probe_script(script, report_path), encoding="utf-8")
        try:
            process = subprocess.run(
                [str(executable), "-e", "-rm", str(script_path)],
                cwd=PROJECT_ROOT,
                env=klayout_environment(),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return _timeout_result(executable, exc, report_path)
        report = _read_probe_report(report_path)
    return KLayoutUiRunResult(
        executable=executable,
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
        report=report,
    )


def ui_tests_enabled() -> bool:
    """Return whether real KLayout GUI tests should run."""

    return os.environ.get("MPP_RUN_KLAYOUT_UI_TESTS") == "1"


def _ui_probe_script(user_script: str, report_path: Path) -> str:
    """Return a GUI-mode probe script that writes a JSON report."""

    python_root = str(PACKAGE_PYTHON_ROOT).replace("\\", "\\\\")
    report_file = str(report_path).replace("\\", "\\\\")
    indented_script = textwrap.indent(user_script.strip(), "    ")
    return (
        "import json\n"
        "import sys\n"
        "import traceback\n"
        "import pya\n"
        f"python_root = r'{python_root}'\n"
        f"report_file = r'{report_file}'\n"
        "if python_root not in sys.path:\n"
        "    sys.path.insert(0, python_root)\n"
        "def write_report(data):\n"
        "    with open(report_file, 'w', encoding='utf-8') as handle:\n"
        "        json.dump(data, handle, indent=2, sort_keys=True)\n"
        "def finish(code):\n"
        "    try:\n"
        "        pya.Application.instance().exit(code)\n"
        "    except Exception:\n"
        "        pass\n"
        "    raise SystemExit(code)\n"
        "report = {}\n"
        "try:\n"
        f"{indented_script}\n"
        "    report.setdefault('ok', True)\n"
        "    write_report(report)\n"
        "    finish(0)\n"
        "except Exception as exc:\n"
        "    write_report({'ok': False, 'error': repr(exc), 'traceback': traceback.format_exc()})\n"
        "    finish(1)\n"
    )


def _read_probe_report(report_path: Path) -> dict[str, object]:
    """Read a GUI probe report or return a structured failure."""

    if not report_path.exists():
        return {"ok": False, "error": "KLayout UI probe did not write a report."}
    with report_path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return loaded if isinstance(loaded, dict) else {"ok": False, "error": "Invalid report shape."}


def _timeout_result(
    executable: Path,
    exc: subprocess.TimeoutExpired,
    report_path: Path,
) -> KLayoutUiRunResult:
    """Return a structured result for a timed-out GUI probe."""

    return KLayoutUiRunResult(
        executable=executable,
        returncode=-1,
        stdout=_timeout_text(exc.stdout),
        stderr=_timeout_text(exc.stderr),
        report=_read_probe_report(report_path),
        timed_out=True,
    )


def _timeout_text(value: object) -> str:
    """Normalize subprocess timeout output to text."""

    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)

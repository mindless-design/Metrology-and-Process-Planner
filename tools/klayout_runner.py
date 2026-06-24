"""Helpers for running KLayout integration probes."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PYTHON_ROOT = PROJECT_ROOT / "python"


@dataclass(frozen=True)
class KLayoutRunResult:
    """Captured result from a KLayout subprocess."""

    executable: Path
    returncode: int
    stdout: str
    stderr: str


def discover_klayout_executable() -> Optional[Path]:
    """Return the best available KLayout executable path."""

    configured = os.environ.get("KLAYOUT_EXE")
    if configured:
        return _existing_path(configured)

    candidates = [
        shutil_which("klayout"),
        shutil_which("klayout_app"),
        _roaming_klayout(),
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    return None


def require_klayout_executable() -> Path:
    """Return KLayout executable path or raise a test-friendly error."""

    executable = discover_klayout_executable()
    if executable is None:
        raise RuntimeError(
            "KLayout executable not found. Set KLAYOUT_EXE to run integration tests."
        )
    return executable


def run_klayout_python_probe(script: str, timeout_seconds: int = 30) -> KLayoutRunResult:
    """Run a Python probe script inside KLayout and capture output."""

    executable = require_klayout_executable()
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "probe.py"
        script_path.write_text(_probe_script(script), encoding="utf-8")
        result = subprocess.run(
            [str(executable), "-b", "-r", str(script_path)],
            cwd=PROJECT_ROOT,
            env=klayout_environment(),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    return KLayoutRunResult(
        executable=executable,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def integration_tests_enabled() -> bool:
    """Return whether real KLayout integration tests should run."""

    return os.environ.get("MPP_RUN_KLAYOUT_TESTS") == "1"


def shutil_which(command: str) -> Optional[Path]:
    """Return a command path from PATH without importing at module load."""

    import shutil

    found = shutil.which(command)
    return Path(found) if found else None


def _existing_path(path_text: str) -> Optional[Path]:
    """Return a path only when it exists on disk."""

    path = Path(path_text).expanduser()
    try:
        return path if path.exists() else None
    except OSError:
        return None


def _roaming_klayout() -> Optional[Path]:
    """Return the default per-user Windows KLayout executable path."""

    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return _existing_path(str(Path(appdata) / "KLayout" / "klayout_app.exe"))


def klayout_environment() -> dict[str, str]:
    """Return an environment that exposes the package Python folder."""

    environment = dict(os.environ)
    existing_path = environment.get("PYTHONPATH")
    paths = [str(PACKAGE_PYTHON_ROOT)]
    if existing_path:
        paths.append(existing_path)
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    return environment


def _probe_script(user_script: str) -> str:
    """Return a KLayout batch-mode script with the package path inserted."""

    python_root = str(PACKAGE_PYTHON_ROOT).replace("\\", "\\\\")
    return (
        "import sys\n"
        f"python_root = r'{python_root}'\n"
        "if python_root not in sys.path:\n"
        "    sys.path.insert(0, python_root)\n"
        f"{user_script}\n"
    )


if __name__ == "__main__":
    executable = discover_klayout_executable()
    if executable is None:
        print("KLayout executable not found.", file=sys.stderr)
        raise SystemExit(1)
    print(executable)

"""Canonical fixture discovery for regression suites."""

from __future__ import annotations

from pathlib import Path

FIXTURE_SESSION_NAMES = (
    "simple_session",
    "batch_capture",
    "cad_review",
    "optical_metrology",
    "cdsem",
    "profilometry",
    "ellipsometry",
    "fib_planning",
    "process_flow_rendering",
)


def fixture_session_paths(root: Path) -> tuple[Path, ...]:
    """Return available canonical session fixture JSON paths."""

    session_root = root / "tests" / "fixtures" / "sessions"
    return tuple(
        session_root / name / "session.json"
        for name in FIXTURE_SESSION_NAMES
        if (session_root / name / "session.json").exists()
    )

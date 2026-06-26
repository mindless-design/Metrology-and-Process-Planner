"""File and mode helpers for session editor stores."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Union

from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    session_mode_value,
)
from metrology_process_planner.persistence.paths import SESSION_JSON_NAME

PathInput = Union[str, Path]


def resolve_session_json(path_or_folder: PathInput) -> Path:
    """Return the session JSON path for a file path or session folder."""

    path = Path(path_or_folder)
    if path.is_dir():
        return path / SESSION_JSON_NAME
    return path


def atomic_write_json(destination: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON atomically and preserve a backup of the previous file."""

    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    if destination.exists():
        shutil.copy2(destination, destination.with_suffix(destination.suffix + ".bak"))
    temp_path.replace(destination)


def allowed_modes(
    registry: ModeRegistry | None,
    session: SessionRecord | None = None,
) -> tuple[str, ...]:
    """Return registry modes plus the current session mode without duplicates."""

    modes = list(registry.mode_ids()) if registry is not None else []
    if session is not None:
        modes.append(session_mode_value(session.mode))
    return tuple(dict.fromkeys(modes))

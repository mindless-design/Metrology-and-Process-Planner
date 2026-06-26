"""Payload merge and open-warning helpers for editor document storage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.session import SessionRecord, WarningRecord


def merged_payload(
    raw_payload: Mapping[str, Any],
    session_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge preserved unknown top-level fields with canonical session payload."""

    merged = {
        key: value for key, value in raw_payload.items() if key not in _KNOWN_TOP_LEVEL_FIELDS
    }
    merged.update(session_payload)
    return merged


def with_open_warnings(
    session: SessionRecord,
    validation_warnings: tuple[str, ...],
    session_folder: Path,
) -> SessionRecord:
    """Return a session with generated schema and source-layout warnings."""

    warnings = tuple(
        warning
        for warning in session.warnings
        if not warning.id.startswith(("schema-validation-", "source-layout-"))
    )
    generated = [
        WarningRecord(
            id=f"schema-validation-{index}",
            message=message,
            severity="warning",
            source="schema_validation",
            code="SCHEMA_VALIDATION",
            repair_suggestion="Save the session to rewrite it in the current schema.",
        )
        for index, message in enumerate(validation_warnings, start=1)
    ]
    layout_path = session.source_layout.layout_path
    if layout_path and not _layout_path_exists(session_folder, layout_path):
        generated.append(
            WarningRecord(
                id="source-layout-missing",
                message=f"Source layout is not available: {layout_path}",
                severity="warning",
                source="source_layout",
                code="SOURCE_LAYOUT_MISSING",
                repair_suggestion="Open the layout or bind the current layout to the session.",
            )
        )
    return session if not generated else replace(session, warnings=warnings + tuple(generated))


def _layout_path_exists(session_folder: Path, layout_path: str) -> bool:
    candidate = Path(layout_path)
    if not candidate.is_absolute():
        candidate = session_folder / candidate
    return candidate.exists()


_KNOWN_TOP_LEVEL_FIELDS = {
    "schema",
    "schema_version",
    "session",
    "paths",
    "source_layout",
    "coordinates",
    "setup",
    "captures",
    "canvas_objects",
    "pending_captures",
    "drawings",
    "grid_datasets",
    "process_context",
    "process_outputs",
    "reports",
    "artifacts",
    "exports",
    "warnings",
    "workflow",
    "metadata",
    "extensions",
    "audit",
    "id",
    "name",
    "mode",
    "created_at",
    "updated_at",
}

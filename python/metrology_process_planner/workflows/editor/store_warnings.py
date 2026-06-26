"""Warning normalization helpers for editor session storage."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import SessionRecord, WarningRecord


def with_open_warnings(
    session: SessionRecord,
    validation_warnings: tuple[str, ...],
    session_folder: Path,
) -> SessionRecord:
    """Return a session with current schema and source-layout warnings."""

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
    if not generated:
        return session
    return replace(session, warnings=warnings + tuple(generated))


def _layout_path_exists(session_folder: Path, layout_path: str) -> bool:
    candidate = Path(layout_path)
    if not candidate.is_absolute():
        candidate = session_folder / candidate
    return candidate.exists()

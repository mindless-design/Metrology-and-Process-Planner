"""JSON session persistence."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Union

from metrology_process_planner.diagnostics.diagnostics_exceptions import emit_exception_event
from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.persistence.paths import SESSION_JSON_NAME, SessionPaths
from metrology_process_planner.persistence.repair import validate_artifact_files
from metrology_process_planner.persistence.schema import validate_session_payload

JsonPath = Union[str, Path]


class SessionJsonStore:
    """Read and write canonical human-readable session JSON."""

    def __init__(self, diagnostic_sink: DiagnosticSink | None = None) -> None:
        self._diagnostics = diagnostic_sink

    def load(self, path_or_folder: JsonPath) -> SessionRecord:
        """Load a session from a JSON file or session folder."""

        path = _resolve_session_json(path_or_folder)
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, Mapping):
                raise ValueError(f"Session JSON must contain an object: {path}")
            warnings = validate_session_payload(data)
            session = SessionRecord.from_dict(data)
            session = validate_artifact_files(session, SessionPaths.for_folder(path.parent))
            return _with_validation_warnings(session, warnings)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            emit_exception_event(
                self._diagnostics,
                "JsonReadFailed",
                exc,
                f"Session JSON load failed: {path}",
                source_component="SessionJsonStore",
                category="persistence",
                operation="load",
                related_artifact_paths=(str(path),),
                remediation_hint="Repair or restore the session JSON before reopening.",
            )
            raise

    def save(self, session: SessionRecord, paths: SessionPaths) -> Path:
        """Atomically save a session into its managed folder."""

        destination = paths.session_json
        self._emit("JsonWriteStarted", session, destination)
        try:
            paths.ensure_created()
            temp_path = destination.with_suffix(destination.suffix + ".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(session.to_dict(), handle, indent=2)
                handle.write("\n")
            if destination.exists():
                shutil.copy2(destination, destination.with_suffix(destination.suffix + ".bak"))
            temp_path.replace(destination)
        except OSError as exc:
            emit_exception_event(
                self._diagnostics,
                "JsonWriteFailed",
                exc,
                f"Session JSON save failed: {destination}",
                session_id=session.id,
                source_component="SessionJsonStore",
                category="persistence",
                operation="save",
                related_artifact_paths=(str(destination),),
                remediation_hint="Check session folder permissions and free disk space.",
            )
            raise
        self._emit("JsonWriteCompleted", session, destination)
        return destination

    def _emit(self, event_name: str, session: SessionRecord, path: Path) -> None:
        if self._diagnostics is None:
            return
        TraceContext.new(session.id, self._diagnostics).emit(
            event_name,
            {
                "message": f"{event_name}: {path}",
                "category": "persistence",
                "source_component": "SessionJsonStore",
                "session_id": session.id,
                "related_artifact_paths": (str(path),),
            },
        )


def _resolve_session_json(path_or_folder: JsonPath) -> Path:
    path = Path(path_or_folder)
    if path.is_dir():
        return path / SESSION_JSON_NAME
    return path


def _with_validation_warnings(
    session: SessionRecord,
    warnings: tuple[str, ...],
) -> SessionRecord:
    if not warnings:
        return session
    records = tuple(
        session_warning
        for session_warning in session.warnings
        if not session_warning.id.startswith("schema-validation-")
    )
    from metrology_process_planner.domains.session import WarningRecord

    return replace(
        session,
        warnings=records
        + tuple(
            WarningRecord(
                id=f"schema-validation-{index}",
                message=message,
                severity="warning",
                source="schema_validation",
                code="schema_validation",
                repair_suggestion="Save the session to rewrite it in the current schema.",
            )
            for index, message in enumerate(warnings, start=1)
        ),
    )

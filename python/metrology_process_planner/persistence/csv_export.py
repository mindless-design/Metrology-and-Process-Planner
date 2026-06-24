"""CSV export helpers for saved sessions."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.domains.session.artifact_query import artifacts_for_owner
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext

CAPTURE_SUMMARY_FIELDS: tuple[str, ...] = (
    "session_id",
    "session_name",
    "session_mode",
    "capture_id",
    "label",
    "type",
    "created_at",
    "geometry_kind",
    "left",
    "bottom",
    "right",
    "top",
    "measurement_count",
    "image_paths",
    "notes",
)


class CaptureCsvExporter:
    """Build and write spreadsheet-friendly capture summaries."""

    def __init__(self, diagnostic_sink: DiagnosticSink | None = None) -> None:
        self._diagnostics = diagnostic_sink

    def rows_for_session(self, session: SessionRecord) -> list[dict[str, Any]]:
        """Return CSV rows for all captures in a session."""

        rows: list[dict[str, Any]] = []
        for capture in session.captures:
            bounds = capture.geometry.bounds
            rows.append(
                {
                    "session_id": session.id,
                    "session_name": session.name,
                    "session_mode": session.mode.value,
                    "capture_id": capture.id,
                    "label": capture.label,
                    "type": capture.type,
                    "created_at": capture.created_at,
                    "geometry_kind": capture.geometry.kind.value,
                    "left": bounds.left if bounds is not None else "",
                    "bottom": bounds.bottom if bounds is not None else "",
                    "right": bounds.right if bounds is not None else "",
                    "top": bounds.top if bounds is not None else "",
                    "measurement_count": len(capture.measurements),
                    "image_paths": ";".join(
                        artifact.relative_path
                        for artifact in artifacts_for_owner(
                            session.artifacts or {},
                            "capture",
                            capture.id,
                        )
                        if artifact.type in {"image", "svg"}
                    ),
                    "notes": capture.notes,
                }
            )
        return rows

    def export(self, session: SessionRecord, destination: Path) -> Path:
        """Write a capture summary CSV and return the destination path."""

        self._emit("CsvWriteStarted", session, destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CAPTURE_SUMMARY_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.rows_for_session(session))
        self._emit("CsvWriteCompleted", session, destination)
        return destination

    def _emit(self, event_name: str, session: SessionRecord, path: Path) -> None:
        if self._diagnostics is None:
            return
        TraceContext.new(session.id, self._diagnostics).emit(
            event_name,
            {
                "message": f"{event_name}: {path}",
                "category": "reporting",
                "source_component": "CaptureCsvExporter",
                "session_id": session.id,
                "related_artifact_paths": (str(path),),
            },
        )

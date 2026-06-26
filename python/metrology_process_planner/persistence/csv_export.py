"""CSV export helpers for saved sessions."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.domains.session.display_units import (
    display_unit_preferences_from_session,
)
from metrology_process_planner.persistence.csv_capture_rows import capture_row
from metrology_process_planner.persistence.csv_capture_schema import CAPTURE_SUMMARY_FIELDS
from metrology_process_planner.persistence.csv_grid_rows import grid_site_rows


class CaptureCsvExporter:
    """Build and write spreadsheet-friendly capture summaries."""

    def __init__(
        self,
        diagnostic_sink: DiagnosticSink | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._diagnostics = diagnostic_sink
        self._mode_registry = mode_registry

    def rows_for_session(self, session: SessionRecord) -> list[dict[str, Any]]:
        """Return CSV rows for all captures in a session."""

        rows: list[dict[str, Any]] = []
        preferences = display_unit_preferences_from_session(session)
        for capture in session.captures:
            rows.append(capture_row(session, capture, self._mode_registry, preferences))
        rows.extend(grid_site_rows(session, self._mode_registry, preferences))
        return rows

    def export(self, session: SessionRecord, destination: Path) -> Path:
        """Write a capture summary CSV and return the destination path."""

        self._emit("CsvWriteStarted", session, destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = _fieldnames_for_session(session)
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CAPTURE_SUMMARY_FIELDS, lineterminator="\n")
            writer.writerow(
                {
                    field: fieldnames[index]
                    for index, field in enumerate(CAPTURE_SUMMARY_FIELDS)
                }
            )
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


def _fieldnames_for_session(session: SessionRecord) -> tuple[str, ...]:
    preferences = display_unit_preferences_from_session(session)
    if preferences.layout_geometry == "auto":
        return CAPTURE_SUMMARY_FIELDS
    return tuple(
        _display_header(field, preferences.layout_geometry) for field in CAPTURE_SUMMARY_FIELDS
    )


def _display_header(field: str, unit: str) -> str:
    display_fields = {
        "left",
        "right",
        "bottom",
        "top",
        "center_x",
        "center_y",
        "width",
        "height",
        "feature_start_x",
        "feature_start_y",
        "feature_end_x",
        "feature_end_y",
        "feature_point_x",
        "feature_point_y",
        "feature_midpoint_x",
        "feature_midpoint_y",
        "feature_length",
        "measurement_start_x",
        "measurement_start_y",
        "measurement_end_x",
        "measurement_end_y",
        "measurement_length",
        "target",
        "lsl",
        "usl",
        "grid_center_x",
        "grid_center_y",
    }
    return f"{field} ({unit})" if field in display_fields else field

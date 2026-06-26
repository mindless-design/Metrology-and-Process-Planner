"""Row schema and builders for capture summary CSV exports."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence import csv_capture_artifacts
from metrology_process_planner.persistence.csv_capture_features import feature_columns
from metrology_process_planner.persistence.csv_capture_measurements import (
    capture_measurement_columns,
    first_measurement,
)
from metrology_process_planner.persistence.csv_capture_schema import GRID_SUMMARY_FIELDS
from metrology_process_planner.persistence.csv_capture_warnings import capture_warning_count


def capture_row(
    session: SessionRecord,
    capture: Any,
    mode_registry: ModeRegistry | None = None,
) -> dict[str, Any]:
    """Return one spreadsheet-friendly capture summary row."""

    bounds = capture.geometry.bounds
    row = _base_columns(session, capture, mode_registry)
    row.update(_coordinate_columns(session, capture))
    row.update(_geometry_columns(bounds))
    row.update(_source_columns(session))
    row.update(feature_columns(capture))
    row.update(_mode_metadata_columns(capture))
    row.update(_review_columns(capture))
    row.update(capture_measurement_columns(capture))
    row.update(
        csv_capture_artifacts.artifact_columns(
            session,
            capture.id,
            capture.measurements,
            mode_registry,
        )
    )
    row.update(
        csv_capture_artifacts.measurement_artifact_columns(
            session,
            first_measurement(capture),
            mode_registry,
        )
    )
    row.update({field: "" for field in GRID_SUMMARY_FIELDS if field != "row_kind"})
    return row


def _base_columns(
    session: SessionRecord,
    capture: Any,
    mode_registry: ModeRegistry | None,
) -> dict[str, Any]:
    return {
        "session_id": session.id,
        "session_name": session.name,
        "session_mode": session.mode.value,
        "mode_id": session.mode.value,
        "capture_id": capture.id,
        "sequence": capture.sequence,
        "label": capture.label,
        "role": capture.role,
        "type": capture.type,
        "status": capture.status,
        "created_at": capture.created_at,
        "modified_at": capture.modified_at,
        "geometry_kind": capture.geometry.kind.value,
        "measurement_count": len(capture.measurements),
        "warning_count": capture_warning_count(session, capture, mode_registry),
        "notes": capture.notes,
        "tags": _capture_tags(capture),
        "row_kind": "capture",
    }


def _capture_tags(capture: Any) -> str:
    if not isinstance(capture.metadata, dict):
        return ""
    return _join(capture.metadata.get("tags", ()))


def _join(values: Iterable[object] | object) -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return values
    if not isinstance(values, Iterable):
        return str(values)
    return ";".join(str(value) for value in values)


def _coordinate_columns(session: SessionRecord, capture: Any) -> dict[str, Any]:
    primary = capture.geometry.primary_metadata() if capture.geometry is not None else None
    metadata = dict(capture.geometry.metadata or {}) if capture.geometry is not None else {}
    return {
        "coordinate_mode": (primary or {}).get("coordinate_mode", "global"),
        "units": (primary or {}).get("units", metadata.get("units", session.coordinates.units)),
    }


def _geometry_columns(bounds: Any) -> dict[str, Any]:
    return {
        "left": bounds.left if bounds is not None else "",
        "bottom": bounds.bottom if bounds is not None else "",
        "right": bounds.right if bounds is not None else "",
        "top": bounds.top if bounds is not None else "",
        "center_x": bounds.center.x if bounds is not None else "",
        "center_y": bounds.center.y if bounds is not None else "",
        "width": bounds.width if bounds is not None else "",
        "height": bounds.height if bounds is not None else "",
    }


def _source_columns(session: SessionRecord) -> dict[str, str]:
    layout_path = session.source_layout.layout_path
    return {
        "source_layout_path": layout_path,
        "source_layout_file": session.source_layout.layout_name or Path(layout_path).name,
        "top_cell": session.source_layout.top_cell,
    }


def _mode_metadata_columns(capture: Any) -> dict[str, str]:
    metadata = dict(capture.metadata or {})
    return {
        "feature_type": str(metadata.get("feature_type", "")),
    }


def _review_columns(capture: Any) -> dict[str, str]:
    metadata = dict(capture.metadata or {})
    return {
        "review_category": str(metadata.get("review_category", "")),
        "review_severity": str(metadata.get("severity", "")),
        "review_owner": str(metadata.get("owner", "")),
    }

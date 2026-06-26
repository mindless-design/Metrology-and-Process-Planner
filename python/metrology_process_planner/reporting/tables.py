"""Reusable declarative table builders for report sections."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.reporting.models import (
    ArtifactSummary,
    CaptureSummary,
    MeasurementSummary,
    TableModel,
    WarningSummary,
)


def capture_table(captures: tuple[CaptureSummary, ...]) -> TableModel:
    """Build a capture summary table."""

    rows = tuple(
        {
            "capture_id": capture.capture_id,
            "label": capture.label,
            "role": capture.role,
            "status": capture.status,
            "measurements": capture.measurement_count,
            "artifacts": len(capture.artifact_ids),
        }
        for capture in captures
    )
    return TableModel("captures", "Capture Summary", _capture_columns(), rows)


def measurement_table(measurements: tuple[MeasurementSummary, ...]) -> TableModel:
    """Build a measurement summary table."""

    rows = tuple(
        {
            "measurement_id": item.measurement_id,
            "capture": item.capture_id,
            "label": item.label,
            "length": f"{item.measured_length:.3f}",
            "target": _optional_number(item.target),
            "lsl": _optional_number(item.lower_spec_limit),
            "usl": _optional_number(item.upper_spec_limit),
        }
        for item in measurements
    )
    return TableModel("measurements", "Measurement Summary", _measurement_columns(), rows)


def artifact_table(artifacts: tuple[ArtifactSummary, ...]) -> TableModel:
    """Build an artifact inventory table."""

    rows = tuple(
        {
            "artifact_id": item.artifact_id,
            "label": item.label,
            "type": item.artifact_type,
            "role": item.role,
            "status": item.status,
            "path": item.relative_path,
        }
        for item in artifacts
    )
    return TableModel("artifacts", "Artifact Inventory", _artifact_columns(), rows)


def warning_table(warnings: tuple[WarningSummary, ...]) -> TableModel:
    """Build a warning inventory table."""

    rows = tuple(
        {
            "warning_id": warning.warning_id,
            "severity": warning.severity,
            "code": warning.code,
            "source": warning.source,
            "message": warning.message,
        }
        for warning in warnings
    )
    return TableModel("warnings", "Warning Summary", _warning_columns(), rows)


def setup_status_table(summary: dict[str, Any]) -> TableModel:
    """Build a setup status table from summary values."""

    rows = tuple({"field": key, "value": str(value)} for key, value in sorted(summary.items()))
    return TableModel("setup", "Setup Status", (("field", "Field"), ("value", "Value")), rows)


def grid_dataset_table(datasets: tuple[dict[str, Any], ...]) -> TableModel:
    """Build a grid dataset planning summary table."""

    rows = tuple(
        {
            "dataset_id": item.get("dataset_id", ""),
            "label": item.get("label", ""),
            "status": item.get("status", ""),
            "rows": item.get("rows", ""),
            "columns": item.get("columns", ""),
            "planned_sites": item.get("planned_sites", ""),
            "first_site": item.get("first_site", ""),
            "last_site": item.get("last_site", ""),
            "anchors": item.get("anchor_capture_ids", ""),
            "overview_status": item.get("overview_status", ""),
            "warnings": item.get("warnings", ""),
        }
        for item in datasets
    )
    return TableModel("grid_datasets", "Grid Dataset Summary", _grid_columns(), rows)


def _capture_columns() -> tuple[tuple[str, str], ...]:
    return (
        ("capture_id", "Capture ID"),
        ("label", "Label"),
        ("role", "Role"),
        ("status", "Status"),
        ("measurements", "Measurements"),
        ("artifacts", "Artifacts"),
    )


def _measurement_columns() -> tuple[tuple[str, str], ...]:
    return (
        ("measurement_id", "Measurement ID"),
        ("capture", "Capture"),
        ("label", "Label"),
        ("length", "Length"),
        ("target", "Target"),
        ("lsl", "LSL"),
        ("usl", "USL"),
    )


def _artifact_columns() -> tuple[tuple[str, str], ...]:
    return (
        ("artifact_id", "Artifact ID"),
        ("label", "Label"),
        ("type", "Type"),
        ("role", "Role"),
        ("status", "Status"),
        ("path", "Path"),
    )


def _warning_columns() -> tuple[tuple[str, str], ...]:
    return (
        ("warning_id", "Warning ID"),
        ("severity", "Severity"),
        ("code", "Code"),
        ("source", "Source"),
        ("message", "Message"),
    )


def _grid_columns() -> tuple[tuple[str, str], ...]:
    return (
        ("dataset_id", "Dataset ID"),
        ("label", "Label"),
        ("status", "Status"),
        ("rows", "Rows"),
        ("columns", "Columns"),
        ("planned_sites", "Sites"),
        ("first_site", "First Site"),
        ("last_site", "Last Site"),
        ("anchors", "Anchors"),
        ("overview_status", "Overview"),
        ("warnings", "Warnings"),
    )


def _optional_number(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"

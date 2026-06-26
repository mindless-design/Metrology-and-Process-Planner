"""Grid dataset inspector-field helpers."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    GridDatasetRecord,
    SessionRecord,
)
from metrology_process_planner.workflows.editor.view_models import MetadataField


def grid_dataset_fields(
    session: SessionRecord,
    dataset: GridDatasetRecord,
) -> tuple[MetadataField, ...]:
    """Return read-only metadata fields for one grid dataset."""

    metadata = dict(dataset.metadata or {})
    artifact = _overview_artifact(session, dataset)
    return _identity_fields(dataset, metadata) + _planning_fields(metadata) + (
        MetadataField(
            "measurement_count",
            "Measurements",
            str(len(dataset.measurements)),
            read_only=True,
        ),
        MetadataField(
            "warning_count",
            "Warnings",
            str(len(dataset.warning_ids)),
            read_only=True,
        ),
        MetadataField(
            "grid_overview_status",
            "Grid Overview",
            artifact.status.value if artifact is not None else "missing",
            read_only=True,
        ),
    )


def _identity_fields(
    dataset: GridDatasetRecord,
    metadata: dict[str, object],
) -> tuple[MetadataField, ...]:
    return (
        MetadataField("label", "Label", dataset.label, read_only=True),
        MetadataField("status", "Status", dataset.status, read_only=True),
        MetadataField(
            "anchor_capture_ids",
            "Anchor Captures",
            _join(dataset.capture_ids or metadata.get("anchor_capture_ids", ())),
            read_only=True,
        ),
    )


def _planning_fields(metadata: dict[str, object]) -> tuple[MetadataField, ...]:
    return (
        MetadataField("row_count", "Rows", _value(metadata, "rows"), read_only=True),
        MetadataField("column_count", "Columns", _value(metadata, "columns"), read_only=True),
        MetadataField(
            "planned_site_count",
            "Planned Sites",
            _value(metadata, "planned_site_count"),
            read_only=True,
        ),
        MetadataField(
            "first_planned_site_id",
            "First Site",
            _value(metadata, "first_planned_site_id"),
            read_only=True,
        ),
        MetadataField(
            "last_planned_site_id",
            "Last Site",
            _value(metadata, "last_planned_site_id"),
            read_only=True,
        ),
    )


def _overview_artifact(
    session: SessionRecord,
    dataset: GridDatasetRecord,
) -> ArtifactRecord | None:
    artifact_id = dict(dataset.artifact_refs or {}).get("grid_overview", "")
    return dict(session.artifacts or {}).get(str(artifact_id)) if artifact_id else None


def _value(metadata: dict[str, object], key: str) -> str:
    value = metadata.get(key, "")
    return "" if value is None else str(value)


def _join(values: object) -> str:
    if isinstance(values, (tuple, list)):
        return ", ".join(str(value) for value in values)
    return str(values or "")

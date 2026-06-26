"""Feature inspector-field helpers."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.adapter_capture_metadata import point_text
from metrology_process_planner.workflows.editor.adapter_metadata_lookup import mapping
from metrology_process_planner.workflows.editor.view_models import MetadataField


def feature_fields(feature: dict[str, object]) -> tuple[MetadataField, ...]:
    """Return read-only metadata fields for a compound feature."""

    geometry = mapping(feature.get("geometry"))
    if str(feature.get("kind", "")) == "point":
        point = mapping(geometry.get("point"))
        return (
            MetadataField("role", "Feature Role", str(feature.get("role", "")), read_only=True),
            MetadataField("x", "X", str(point.get("x", "")), read_only=True),
            MetadataField("y", "Y", str(point.get("y", "")), read_only=True),
        )
    return (
        MetadataField("role", "Feature Role", str(feature.get("role", "")), read_only=True),
        MetadataField("start", "Start", point_text(mapping(geometry.get("start"))), read_only=True),
        MetadataField("end", "End", point_text(mapping(geometry.get("end"))), read_only=True),
        MetadataField(
            "midpoint",
            "Midpoint",
            point_text(mapping(geometry.get("midpoint"))),
            read_only=True,
        ),
        MetadataField("length", "Length", str(geometry.get("length", "")), read_only=True),
    )

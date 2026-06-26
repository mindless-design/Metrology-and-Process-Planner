"""Measurement metadata fields for the session editor."""

from __future__ import annotations

from metrology_process_planner.domains.measurement.records import (
    EDGE_CONVENTION_OPTIONS,
    MEASUREMENT_TYPE_OPTIONS,
    MeasurementRecord,
)
from metrology_process_planner.workflows.editor.adapter_metadata_lookup import optional_number
from metrology_process_planner.workflows.editor.view_models import MetadataField


def measurement_fields(measurement: MeasurementRecord) -> tuple[MetadataField, ...]:
    """Return editable metadata fields for one measurement."""

    return (
        MetadataField("label", "Label", measurement.label, required=True),
        MetadataField(
            "measurement_type",
            "Measurement Type",
            str(dict(measurement.metadata or {}).get("measurement_type", "")),
            options=MEASUREMENT_TYPE_OPTIONS,
        ),
        MetadataField("target", "Target", optional_number(measurement.target)),
        MetadataField("lower_spec_limit", "LSL", optional_number(measurement.lower_spec_limit)),
        MetadataField("upper_spec_limit", "USL", optional_number(measurement.upper_spec_limit)),
        MetadataField("notes", "Notes", measurement.notes),
        MetadataField(
            "edge_convention",
            "Edge Convention",
            measurement.edge_detection_convention,
            options=EDGE_CONVENTION_OPTIONS,
        ),
        MetadataField("annotation_color", "Annotation Color", measurement.annotation_color),
        MetadataField("line_weight", "Line Weight", str(measurement.line_weight)),
    )

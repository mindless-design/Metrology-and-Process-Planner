"""Mode-declared metadata fields for editor view models."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.modes.mode_policies import MetadataFieldDefinition
from metrology_process_planner.domains.session import ModeRegistry, built_in_mode_registry
from metrology_process_planner.workflows.editor.view_models import MetadataField

_LABELS = {
    "capture_role": "Capture Role",
    "capture_type": "Capture Type",
    "line_label": "Line Label",
    "line_color": "Line Color",
    "line_weight_px": "Line Weight",
    "review_category": "Review Category",
    "severity": "Severity",
    "owner": "Owner / Assignee",
    "feature_type": "Feature Type",
    "measurement_type": "Measurement Type",
    "edge_convention": "Edge Convention",
    "text_scale": "Text Scale",
    "target": "Target",
    "lsl": "LSL",
    "usl": "USL",
    "point_label": "Point Label",
    "film_target": "Film / Stack of Interest",
}

_DEFAULTS = {
    "line_label": "Profile Line",
    "line_color": "#00BCD4",
    "line_weight_px": "4",
    "review_category": "layout_issue",
    "severity": "medium",
    "measurement_type": "cd",
    "edge_convention": "outer_edges",
    "text_scale": "1.0",
    "point_label": "Measurement Point",
}


def mode_metadata_fields(
    mode_id: str,
    values: Mapping[str, object],
    exclude: set[str] | None = None,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return metadata fields declared by a mode definition."""

    excluded = exclude or set()
    definition = (mode_registry or built_in_mode_registry()).definition(mode_id)
    return tuple(
        _metadata_field(field, values)
        for field in definition.metadata.capture_fields
        if field.id and field.id not in excluded
    )


def _metadata_field(
    field: MetadataFieldDefinition,
    values: Mapping[str, object],
) -> MetadataField:
    return MetadataField(
        field.id,
        field.label or _LABELS.get(field.id, field.id.replace("_", " ").title()),
        _field_value(field, values),
        required=field.required or field.id == "label",
        options=field.options,
    )


def _field_value(field: MetadataFieldDefinition, values: Mapping[str, object]) -> str:
    value = values.get(field.id, field.default or _DEFAULTS.get(field.id, ""))
    return "" if value is None else str(value)

"""Mode-declared metadata fields for editor view models."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import built_in_mode_registry
from metrology_process_planner.workflows.editor.view_models import MetadataField

_LABELS = {
    "line_label": "Line Label",
    "line_color": "Line Color",
    "line_weight_px": "Line Weight",
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
    "text_scale": "1.0",
    "point_label": "Measurement Point",
}


def mode_metadata_fields(
    mode_id: str,
    values: Mapping[str, object],
    exclude: set[str] | None = None,
) -> tuple[MetadataField, ...]:
    """Return metadata fields declared by a mode definition."""

    excluded = exclude or set()
    definition = built_in_mode_registry().definition(mode_id)
    return tuple(
        MetadataField(
            key,
            _LABELS.get(key, key.replace("_", " ").title()),
            _field_value(key, values),
            required=key == "label",
        )
        for key in definition.metadata.field_ids()
        if key not in excluded
    )


def _field_value(key: str, values: Mapping[str, object]) -> str:
    value = values.get(key, _DEFAULTS.get(key, ""))
    return "" if value is None else str(value)

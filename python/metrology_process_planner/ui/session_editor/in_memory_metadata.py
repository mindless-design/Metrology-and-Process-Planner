"""In-memory metadata-control helpers for session editor tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from metrology_process_planner.ui.session_editor.sections import MetadataRows
from metrology_process_planner.workflows.editor.view_models import (
    EditorAction,
    EditorActionType,
    MetadataField,
)

ActionCallback = Callable[[EditorAction], None]


def legacy_field_rows(fields: MetadataRows) -> tuple[tuple[str, str, str], ...]:
    """Return legacy field tuples kept for older shell assertions."""

    return tuple((field.key, field.label, field.value) for field in fields)


def metadata_controls(fields: MetadataRows) -> tuple[dict[str, Any], ...]:
    """Return serializable in-memory metadata controls."""

    return tuple(_metadata_control(field) for field in fields)


def metadata_change_callback(
    item_id: str,
    on_action: ActionCallback,
) -> Callable[[str, str], None]:
    """Return a callback that emits update-metadata editor actions."""

    def on_metadata_change(field_key: str, value: str) -> None:
        on_action(
            EditorAction(
                EditorActionType.UPDATE_METADATA_FIELD,
                "Update Metadata",
                item_id,
                payload=(("field_key", field_key), ("value", value)),
            )
        )

    return on_metadata_change


def _metadata_control(field: MetadataField) -> dict[str, Any]:
    return {
        "key": field.key,
        "label": field.label,
        "value": field.value,
        "required": field.required,
        "read_only": field.read_only,
        "warning": field.warning,
        "options": field.options,
        "control_type": _control_type(field),
    }


def _control_type(field: MetadataField) -> str:
    if field.read_only:
        return "label"
    if field.options:
        return "select"
    return "text"

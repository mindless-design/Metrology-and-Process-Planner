"""Reusable row builders for the generic session editor shell."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.workflows.editor.adapters import SessionModeAdapter
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import MetadataField

PreviewRows = tuple[tuple[str, str, str], ...]
MetadataRows = tuple[MetadataField, ...]


def preview_rows(document: SessionDocument, adapter: SessionModeAdapter) -> PreviewRows:
    """Return preview rows for the selected editor item."""

    item = document.items_by_id[document.selection.selected_item_id]
    return tuple(
        (preview.role, preview.label, preview.artifact_path or preview.placeholder)
        for preview in adapter.preview_options(document.session, item)
    )


def metadata_rows(document: SessionDocument, adapter: SessionModeAdapter) -> MetadataRows:
    """Return inspector metadata rows for the selected editor item."""

    item = document.items_by_id[document.selection.selected_item_id]
    fields = adapter.metadata_fields(document.session, item)
    edits = {
        field_key: value
        for item_id, field_key, value in document.dirty_state.unsaved_metadata_edits
        if item_id == item.item_id
    }
    if not edits:
        return fields
    return tuple(
        replace(field, value=edits[field.key]) if field.key in edits else field
        for field in fields
    )

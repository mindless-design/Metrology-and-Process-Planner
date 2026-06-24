"""Reusable row builders for the generic session editor shell."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.adapters import SessionModeAdapter
from metrology_process_planner.workflows.editor.document import SessionDocument

PreviewRows = tuple[tuple[str, str, str], ...]
MetadataRows = tuple[tuple[str, str, str], ...]


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
    return tuple(
        (field.key, field.label, field.value)
        for field in adapter.metadata_fields(document.session, item)
    )

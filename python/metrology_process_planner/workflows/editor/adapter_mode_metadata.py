"""Mode-declared metadata helpers for generic capture editor items."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    CaptureRecord,
    ModeRegistry,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.workflows.editor.adapter_mode_fields import mode_metadata_fields
from metrology_process_planner.workflows.editor.view_models import MetadataField


def capture_mode_fields(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return mode metadata fields for a saved capture."""

    values = {
        **dict(capture.metadata or {}),
        "label": capture.label,
        "notes": capture.notes,
        "capture_role": capture.role,
        "capture_type": capture.type,
    }
    return mode_metadata_fields(
        session.mode.value,
        values,
        exclude={"label", "notes", "capture_role", "capture_type"},
        mode_registry=mode_registry,
    )


def pending_mode_fields(
    session: SessionRecord,
    pending: PendingCapture,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return mode metadata fields for a pending capture."""

    return mode_metadata_fields(
        session.mode.value,
        dict(pending.metadata or {}),
        exclude={"label", "notes", "capture_role"},
        mode_registry=mode_registry,
    )

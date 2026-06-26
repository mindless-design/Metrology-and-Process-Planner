"""Pending capture metadata fields for the default editor adapter."""

from __future__ import annotations

from metrology_process_planner.domains.session import ModeRegistry, PendingCapture, SessionRecord
from metrology_process_planner.workflows.editor.adapter_mode_fields import mode_metadata_fields
from metrology_process_planner.workflows.editor.adapter_mode_metadata import pending_mode_fields
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.editor.view_models import MetadataField
from metrology_process_planner.workflows.mode_capture_defaults import capture_defaults

_CDSEM_MODES = {"cdsem_capture", "cdsem_measurement", "cdsem_planning"}


def pending_fields(
    session: SessionRecord,
    pending: PendingCapture,
    mode_registry: ModeRegistry | None,
) -> tuple[MetadataField, ...]:
    """Return metadata fields for a pending capture or pending compound capture."""

    metadata = dict(pending.metadata or {})
    compound = dict(metadata.get("compound", {}))
    if not compound:
        return _simple_pending_fields(session, pending, mode_registry, metadata)
    return _compound_pending_fields(session, pending, mode_registry, metadata, compound)


def cdsem_guidance_fields(session: SessionRecord) -> tuple[MetadataField, ...]:
    """Return CDSEM label guidance for modes that need it."""

    if session.mode.value not in _CDSEM_MODES:
        return ()
    return (
        MetadataField(
            "label_guidance",
            "Label Guidance",
            "Keep CDSEM labels at or below 32 characters for tool/job compatibility.",
            read_only=True,
        ),
    )


def _simple_pending_fields(
    session: SessionRecord,
    pending: PendingCapture,
    mode_registry: ModeRegistry | None,
    metadata: dict[str, object],
) -> tuple[MetadataField, ...]:
    defaults = capture_defaults(session, pending, "cap-001", "", mode_registry)
    fields: tuple[MetadataField, ...] = (
        MetadataField("label", "Label", str(metadata.get("label", "")), required=True),
        MetadataField("notes", "Notes", str(metadata.get("notes", ""))),
        MetadataField("capture_role", "Capture Role", defaults.role),
    )
    return fields + cdsem_guidance_fields(session) + pending_mode_fields(
        session,
        pending,
        mode_registry,
    )


def _compound_pending_fields(
    session: SessionRecord,
    pending: PendingCapture,
    mode_registry: ModeRegistry | None,
    metadata: dict[str, object],
    compound: dict[str, object],
) -> tuple[MetadataField, ...]:
    defaults = capture_defaults(session, pending, "cap-001", "", mode_registry)
    raw_feature = compound.get("feature", {})
    feature = dict(raw_feature) if isinstance(raw_feature, dict) else {}
    fields: tuple[MetadataField, ...] = (
        MetadataField("label", "Label", str(metadata.get("label", "")), required=True),
        MetadataField("notes", "Notes", str(metadata.get("notes", ""))),
        MetadataField("capture_role", "Capture Role", defaults.role),
        MetadataField("child_role", "Child Role", str(compound.get("child_role", ""))),
        MetadataField("child_kind", "Child Feature", str(compound.get("child_kind", ""))),
        MetadataField("feature_id", "Feature ID", str(feature.get("id", ""))),
    )
    if mode_is_process_aware(session, mode_registry):
        fields += (
            MetadataField("process_context_ref", "Process Context", "process_context.active"),
        )
    return fields + cdsem_guidance_fields(session) + mode_metadata_fields(
        str(compound.get("mode_id", "")),
        metadata,
        exclude={"label", "notes"},
        mode_registry=mode_registry,
    )

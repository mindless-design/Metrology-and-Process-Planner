"""Mode adapter contracts for the unified session editor."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.adapter_actions import default_actions
from metrology_process_planner.workflows.editor.adapter_metadata import (
    metadata_fields_for_item,
)
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.preview_labels import artifact_preview_label
from metrology_process_planner.workflows.editor.preview_placeholders import (
    artifact_placeholder_message,
)
from metrology_process_planner.workflows.editor.references import ArtifactRef
from metrology_process_planner.workflows.editor.view_models import (
    EditorAction,
    MetadataField,
    PreviewOption,
)

MetadataFields = tuple[MetadataField, ...]
PreviewOptions = tuple[PreviewOption, ...]


class SessionModeAdapter(Protocol):
    """Provide mode-specific editor view models without forking the shell."""

    def metadata_fields(self, session: SessionRecord, item: SessionItem) -> MetadataFields:
        """Return inspector fields for one editor item."""

    def preview_options(self, session: SessionRecord, item: SessionItem) -> PreviewOptions:
        """Return preview options for one editor item."""

    def actions(self, session: SessionRecord, item: SessionItem) -> tuple[EditorAction, ...]:
        """Return actions available for one editor item."""


class DefaultSessionModeAdapter:
    """Generic adapter for existing capture, pending, warning, and dashboard items."""

    def __init__(self, mode_registry: ModeRegistry | None = None) -> None:
        self._mode_registry = mode_registry

    def metadata_fields(self, session: SessionRecord, item: SessionItem) -> MetadataFields:
        """Return generic inspector fields for the selected item."""

        return metadata_fields_for_item(session, item, self._mode_registry)

    def preview_options(self, session: SessionRecord, item: SessionItem) -> PreviewOptions:
        """Return generic preview options for the selected item."""

        artifact_refs = tuple(
            artifact for artifact in item.artifact_refs
            if item.role != "process_output" or artifact.role != "process_output_manifest"
        )
        if not artifact_refs:
            return (
                PreviewOption("placeholder", "No preview", placeholder="No preview available."),
            )
        return tuple(_preview_for_artifact(artifact) for artifact in artifact_refs)

    def actions(self, session: SessionRecord, item: SessionItem) -> tuple[EditorAction, ...]:
        """Return generic editor actions for the selected item."""

        return default_actions(session, item, self._mode_registry)


def _preview_for_artifact(artifact: ArtifactRef) -> PreviewOption:
    label = artifact_preview_label(artifact.role, artifact.artifact_type)
    if artifact.status in {
        "missing",
        "stale",
        "failed",
        "error",
        "placeholder",
        "pending",
        "pending_solver",
    }:
        message = artifact_placeholder_message(artifact)
        return PreviewOption(
            artifact.role,
            label,
            artifact_path=artifact.path,
            placeholder=message,
            status=artifact.status,
            repair_action=artifact.repair_action,
        )
    return PreviewOption(
        artifact.role,
        label,
        artifact.path,
        repair_action=artifact.repair_action,
    )

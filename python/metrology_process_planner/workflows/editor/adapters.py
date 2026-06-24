"""Mode adapter contracts for the unified session editor."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.editor.adapter_actions import default_actions
from metrology_process_planner.workflows.editor.adapter_metadata import (
    metadata_fields_for_item,
)
from metrology_process_planner.workflows.editor.document import SessionItem
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

    def metadata_fields(self, session: SessionRecord, item: SessionItem) -> MetadataFields:
        """Return generic inspector fields for the selected item."""

        return metadata_fields_for_item(session, item)

    def preview_options(self, session: SessionRecord, item: SessionItem) -> PreviewOptions:
        """Return generic preview options for the selected item."""

        if not item.artifact_refs:
            return (
                PreviewOption("placeholder", "No preview", placeholder="No preview available."),
            )
        return tuple(_preview_for_artifact(artifact) for artifact in item.artifact_refs)

    def actions(self, session: SessionRecord, item: SessionItem) -> tuple[EditorAction, ...]:
        """Return generic editor actions for the selected item."""

        return default_actions(session, item)


def _preview_for_artifact(artifact: ArtifactRef) -> PreviewOption:
    if artifact.status in {"missing", "stale", "error"}:
        message = artifact.message or f"{artifact.status.title()} artifact: {artifact.path}"
        if artifact.status == "missing":
            message = f"Missing artifact: {artifact.path}. {artifact.message}".strip()
        return PreviewOption(
            artifact.role,
            artifact.role.replace("_", " ").title(),
            artifact_path=artifact.path,
            placeholder=message,
            status=artifact.status,
            repair_action=artifact.repair_action,
        )
    return PreviewOption(
        artifact.role,
        artifact.role.replace("_", " ").title(),
        artifact.path,
        repair_action=artifact.repair_action,
    )

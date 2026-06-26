"""Presenter helpers for reusable artifact previews."""

from __future__ import annotations

from metrology_process_planner.ui.shell import PreviewModel
from metrology_process_planner.workflows.editor.preview_labels import artifact_preview_label
from metrology_process_planner.workflows.editor.preview_placeholders import (
    artifact_placeholder_message,
)
from metrology_process_planner.workflows.editor.references import ArtifactRef


class PreviewPresenter:
    """Convert artifact refs into preview models."""

    def from_artifacts(self, artifacts: tuple[ArtifactRef, ...]) -> tuple[PreviewModel, ...]:
        """Return preview models for artifact refs."""

        if not artifacts:
            return (
                PreviewModel(
                    "placeholder",
                    "No preview",
                    status="missing",
                    placeholder="No preview available.",
                ),
            )
        return tuple(_preview(artifact) for artifact in artifacts)


def _preview(artifact: ArtifactRef) -> PreviewModel:
    placeholder = ""
    if artifact.status in {"missing", "stale", "error", "failed", "placeholder"}:
        placeholder = artifact_placeholder_message(artifact)
    return PreviewModel(
        role=artifact.role,
        label=artifact_preview_label(artifact.role, artifact.artifact_type),
        artifact_id=artifact.artifact_id,
        artifact_path=artifact.path,
        status=artifact.status,
        placeholder=placeholder,
        warning_ids=artifact.warning_ids,
        repair_action=artifact.repair_action,
        repair_suggestion=artifact.repair_suggestion,
    )

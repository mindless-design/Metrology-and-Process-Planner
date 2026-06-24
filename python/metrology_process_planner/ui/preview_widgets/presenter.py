"""Presenter helpers for reusable artifact previews."""

from __future__ import annotations

from metrology_process_planner.ui.shell import PreviewModel
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
    if artifact.status in {"missing", "stale", "error", "failed"}:
        placeholder = artifact.message or f"{artifact.status.title()} artifact"
    return PreviewModel(
        role=artifact.role,
        label=artifact.role.replace("_", " ").title(),
        artifact_id=artifact.artifact_id,
        artifact_path=artifact.path,
        status=artifact.status,
        placeholder=placeholder,
        warning_ids=artifact.warning_ids,
    )

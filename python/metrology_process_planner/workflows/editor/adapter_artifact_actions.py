"""Artifact-specific editor action helpers."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.references import ArtifactRef
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def artifact_repair_actions(
    item: SessionItem,
    regenerate_label: str,
) -> tuple[EditorAction, ...]:
    """Return artifact-id-specific regenerate and relink actions for an item."""

    refs = tuple(ref for ref in item.artifact_refs if ref.artifact_id)
    if not refs:
        return (EditorAction(EditorActionType.REGENERATE_ARTIFACT, regenerate_label, item.item_id),)
    actions: list[EditorAction] = []
    for ref in refs:
        label = regenerate_label if len(refs) == 1 else f"Regenerate {_artifact_label(ref)}"
        actions.append(
            EditorAction(
                EditorActionType.REGENERATE_ARTIFACT,
                label,
                item.item_id,
                payload=(("artifact_id", ref.artifact_id),),
            )
        )
        actions.append(
            EditorAction(
                EditorActionType.RELINK_ARTIFACT,
                f"Relink {_artifact_label(ref)}",
                item.item_id,
                payload=(("artifact_id", ref.artifact_id),),
            )
        )
    return tuple(actions)


def artifact_warning_action(
    action_type: EditorActionType,
    label: str,
    item_id: str,
    artifact_id: str,
    warning_id: str,
) -> EditorAction:
    """Return a warning action carrying artifact and warning context."""

    return EditorAction(
        action_type,
        label,
        item_id,
        payload=(("artifact_id", artifact_id), ("warning_id", warning_id)),
    )


def _artifact_label(ref: ArtifactRef) -> str:
    label = ref.role or ref.artifact_type or ref.artifact_id
    return label.replace("_", " ").title()

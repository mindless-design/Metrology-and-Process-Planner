"""Saved-capture visual artifact action builders."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType

VISUAL_ARTIFACT_ROLES = {
    "site_image_labeled",
    "site_overview_image",
    "line_annotation_image",
    "point_annotation_image",
    "measurement_annotation_image",
}

ANNOTATION_ROLES = {
    "line_annotation_image",
    "point_annotation_image",
    "measurement_annotation_image",
}


def visual_artifact_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    """Return regenerate actions for visual artifacts attached to a saved capture."""

    visual_roles = {ref.role for ref in item.artifact_refs}.intersection(VISUAL_ARTIFACT_ROLES)
    if not visual_roles:
        return ()
    actions: list[EditorAction] = []
    if "site_image_labeled" in visual_roles:
        actions.append(_regenerate_action(item, "Regenerate Labeled Site Image",
                                          "site_image_labeled"))
    if "site_overview_image" in visual_roles:
        actions.append(_regenerate_action(item, "Regenerate Site Overview",
                                          "site_overview_image"))
    if visual_roles.intersection(ANNOTATION_ROLES):
        actions.append(_regenerate_action(item, "Regenerate Annotation Image",
                                          "annotation_image"))
    actions.append(_regenerate_action(item, "Regenerate Visual Artifacts", "visual_artifacts"))
    return tuple(actions)


def _regenerate_action(item: SessionItem, label: str, role: str) -> EditorAction:
    return EditorAction(
        EditorActionType.REGENERATE_ARTIFACT,
        label,
        item.item_id,
        payload=(("role", role),),
    )

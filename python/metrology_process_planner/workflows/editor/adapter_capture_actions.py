"""Saved-capture editor action policy."""

from __future__ import annotations

from metrology_process_planner.domains.session import CaptureRecord, SessionRecord
from metrology_process_planner.workflows.editor.adapter_process import (
    process_context_actions,
)
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def saved_capture_actions(
    session: SessionRecord,
    item: SessionItem,
) -> tuple[EditorAction, ...]:
    """Return actions for a saved capture from canonical capture data."""

    capture = _capture_by_item(session, item)
    if capture is None:
        return _generic_capture_actions(item)
    feature_label = _first_feature_label(capture)
    if feature_label:
        return _site_plus_feature_actions(item, feature_label, _process_label(capture))
    return _generic_capture_actions(item)


def _site_plus_feature_actions(
    item: SessionItem,
    feature_label: str,
    process_label: str,
) -> tuple[EditorAction, ...]:
    return (
        EditorAction(EditorActionType.REPLACE_SITE_BOX, "Replace Site Box", item.item_id),
        EditorAction(
            EditorActionType.REPLACE_INNER_FEATURE,
            f"Replace {feature_label}",
            item.item_id,
            payload=(("feature_kind", feature_label.lower()),),
        ),
        EditorAction(EditorActionType.ADD_MEASUREMENT, "Add Measurement", item.item_id),
        EditorAction(
            EditorActionType.REGENERATE_ARTIFACT,
            f"Regenerate {feature_label} Annotation",
            item.item_id,
        ),
    ) + process_context_actions(item.item_id) + (
        EditorAction(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            process_label,
            item.item_id,
        ),
    )


def _generic_capture_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    return (
        EditorAction(EditorActionType.ADD_MEASUREMENT, "Add Measurement", item.item_id),
        EditorAction(EditorActionType.REGENERATE_ARTIFACT, "Regenerate Drawing", item.item_id),
    ) + process_context_actions(item.item_id) + (
        EditorAction(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            "Regenerate Process Output",
            item.item_id,
        ),
    )


def _capture_by_item(session: SessionRecord, item: SessionItem) -> CaptureRecord | None:
    if item.record_ref is None:
        return None
    for capture in session.captures:
        if capture.id == item.record_ref.record_id:
            return capture
    return None


def _first_feature_label(capture: CaptureRecord) -> str:
    if not capture.geometry.features:
        return ""
    label = str(capture.geometry.features[0].get("label", ""))
    if label:
        return label
    kind = str(capture.geometry.features[0].get("kind", "feature"))
    return kind.replace("_", " ").title()


def _process_label(capture: CaptureRecord) -> str:
    operation = _solver_operation(capture)
    if operation == "point_stack":
        return "Regenerate Point Stack"
    return "Regenerate Process Output"


def _solver_operation(capture: CaptureRecord) -> str:
    for extension in (capture.extensions or {}).values():
        if isinstance(extension, dict):
            request = extension.get("solver_request", {})
            if isinstance(request, dict):
                return str(request.get("operation", ""))
    return ""

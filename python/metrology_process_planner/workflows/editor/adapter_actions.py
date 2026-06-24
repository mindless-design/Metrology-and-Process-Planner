"""Editor action builders for the default session adapter."""

from __future__ import annotations

from metrology_process_planner.domains.session import PendingCapture, SessionRecord
from metrology_process_planner.workflows.editor.adapter_capture_actions import (
    saved_capture_actions,
)
from metrology_process_planner.workflows.editor.adapter_process_outputs import (
    process_output_actions,
)
from metrology_process_planner.workflows.editor.adapter_warning_actions import warning_actions
from metrology_process_planner.workflows.editor.dispatcher_composite import pending_id_is_composite
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def default_actions(session: SessionRecord, item: SessionItem) -> tuple[EditorAction, ...]:
    """Return generic editor actions for the selected item."""

    actions = list(_base_actions(item))
    if item.record_ref is None:
        actions.extend(_dashboard_actions(item))
    elif factory := _RECORD_ACTIONS.get(item.record_ref.record_type):
        actions.extend(factory(session, item))
    if item.warning_ids:
        actions.extend(warning_actions(session, item))
    actions.extend(_export_actions(item))
    return tuple(actions)


def _base_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    return (EditorAction(EditorActionType.SAVE_EDITS, "Save Edits", item.item_id),)


def _dashboard_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    from metrology_process_planner.workflows.editor.adapter_process import (
        dashboard_process_context_actions,
    )

    return dashboard_process_context_actions(item.item_id)


def _record_pending_actions(
    session: SessionRecord,
    item: SessionItem,
) -> tuple[EditorAction, ...]:
    if item.record_ref and pending_id_is_composite(session, item.record_ref.record_id):
        return _composite_actions(session, item)
    return _pending_actions(item)


def _pending_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    return (
        EditorAction(EditorActionType.PENDING_SAVE, "Save", item.item_id),
        EditorAction(EditorActionType.PENDING_RETAKE, "Retake", item.item_id),
        EditorAction(EditorActionType.PENDING_DISCARD, "Discard", item.item_id),
        EditorAction(EditorActionType.TAKE_MEASUREMENT, "Take Measurement", item.item_id),
        EditorAction(EditorActionType.EXIT_SESSION, "Exit Session", item.item_id),
    )


def _composite_actions(session: SessionRecord, item: SessionItem) -> tuple[EditorAction, ...]:
    label = _inner_retake_label(session, item)
    return (
        EditorAction(EditorActionType.COMPOSITE_SAVE, "Save Composite", item.item_id),
        EditorAction(EditorActionType.COMPOSITE_RETAKE_INNER, label, item.item_id),
        EditorAction(EditorActionType.COMPOSITE_RETAKE_PARENT, "Retake Site Box", item.item_id),
        EditorAction(EditorActionType.COMPOSITE_DISCARD, "Discard Composite", item.item_id),
        EditorAction(EditorActionType.COMPOSITE_EXIT, "Exit", item.item_id),
    )


def _drawing_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    return (
        EditorAction(EditorActionType.REGENERATE_ARTIFACT, "Regenerate Drawing", item.item_id),
    )


def _record_drawing_actions(
    _session: SessionRecord,
    item: SessionItem,
) -> tuple[EditorAction, ...]:
    return _drawing_actions(item)


def _measurement_actions(
    _session: SessionRecord,
    item: SessionItem,
) -> tuple[EditorAction, ...]:
    if item.status == "pending":
        return (
            EditorAction(EditorActionType.SAVE_MEASUREMENT, "Save Measurement", item.item_id),
            EditorAction(
                EditorActionType.RETAKE_MEASUREMENT_LINE,
                "Retake Measurement Line",
                item.item_id,
            ),
            EditorAction(EditorActionType.DISCARD_MEASUREMENT, "Discard Measurement", item.item_id),
            EditorAction(
                EditorActionType.SELECT_ITEM,
                "Return to Parent Capture",
                item.parent_id or "",
            ),
        )
    return (
        EditorAction(
            EditorActionType.REGENERATE_ARTIFACT,
            "Regenerate Measurement Annotation",
            item.item_id,
        ),
    )


def _export_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    return (
        EditorAction(EditorActionType.EXPORT_CSV, "Export CSV", item.item_id),
        EditorAction(
            EditorActionType.BUILD_POWERPOINT,
            "Build PowerPoint",
            item.item_id,
            enabled=False,
            disabled_reason="PowerPoint report generation is not wired yet.",
        ),
    )


def _inner_retake_label(session: SessionRecord, item: SessionItem) -> str:
    pending = _pending_by_id(session, item.record_ref.record_id) if item.record_ref else None
    compound = dict((pending.metadata or {}).get("compound", {})) if pending is not None else {}
    label = str(compound.get("child_label", ""))
    if not label:
        label = "Line" if compound.get("child_kind") == "line" else "Point"
    return f"Retake {label}"


def _pending_by_id(session: SessionRecord, pending_id: str) -> PendingCapture | None:
    for pending in session.pending_captures:
        if pending.id == pending_id:
            return pending
    return None


_RECORD_ACTIONS = {
    "pending_capture": _record_pending_actions,
    "capture": saved_capture_actions,
    "measurement": _measurement_actions,
    "session_drawing": _record_drawing_actions,
    "process_output": process_output_actions,
}

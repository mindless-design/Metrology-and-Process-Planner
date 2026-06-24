"""Capture status presenters backed by durable session workflow state."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import CanvasObjectType, SessionRecord
from metrology_process_planner.ui.capture.tools import CaptureToolPresenter
from metrology_process_planner.ui.shell import CaptureToolStatusViewModel
from metrology_process_planner.workflows.canvas_interaction_models import InteractionContext


def capture_status_from_session(session: SessionRecord) -> CaptureToolStatusViewModel:
    """Return the current modeless capture status from durable workflow state."""

    primitive = _primitive_from_workflow(session.workflow.active_primitive)
    status = CaptureToolPresenter().build(
        InteractionContext(
            armed_object_type=primitive,
            active_parent_id=session.workflow.pending_item_ref,
        )
    )
    return replace(status, message=_message(status, session.workflow.active_primitive))


def capture_status_text(session: SessionRecord) -> str:
    """Return non-blocking capture guidance for status strips."""

    return capture_status_from_session(session).message


def _primitive_from_workflow(value: str) -> CanvasObjectType | None:
    if not value:
        return None
    aliases = {
        "box": CanvasObjectType.SITE_BOX,
        "site": CanvasObjectType.SITE_BOX,
        "line": CanvasObjectType.LINE,
        "measurement_line": CanvasObjectType.MEASUREMENT,
        "point": CanvasObjectType.POINT,
    }
    if value in aliases:
        return aliases[value]
    try:
        return CanvasObjectType(value)
    except ValueError:
        return None


def _message(status: CaptureToolStatusViewModel, workflow_primitive: str) -> str:
    if not status.armed:
        if workflow_primitive:
            return (
                f"Unknown capture primitive '{workflow_primitive}'; "
                "KLayout navigation is active."
            )
        return "KLayout navigation active."
    text = f"{_label(status.primitive)} armed: {_gesture_sentence(status.primitive)}."
    if status.active_parent_id:
        text = f"{text} Active parent: {status.active_parent_id}."
    return text


def _label(primitive: str) -> str:
    if primitive == "site_box":
        return "Box capture"
    if primitive in {"line", "measurement", "profilometry_line", "multi_line"}:
        return "Line capture"
    if primitive in {"point", "ellipsometry_point"}:
        return "Point capture"
    return "Capture"


def _gesture_sentence(primitive: str) -> str:
    if primitive == "site_box":
        return "hold Left Shift and drag a box on the layout canvas"
    if primitive in {"line", "measurement", "profilometry_line", "multi_line"}:
        return "hold Left Shift and drag a line on the layout canvas"
    if primitive in {"point", "ellipsometry_point"}:
        return "hold Left Shift and click a point on the layout canvas"
    return "hold Left Shift and complete the armed capture gesture"

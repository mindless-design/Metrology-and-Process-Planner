"""Reusable canvas capture interaction tools."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CanvasObjectType, SessionRecord
from metrology_process_planner.ui.shell import CaptureToolStatusViewModel
from metrology_process_planner.workflows.canvas_interaction import CanvasInteractionEngine
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.compound_capture import (
    add_point_feature,
)
from metrology_process_planner.workflows.compound_capture_routing import active_compound_request
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


@dataclass(frozen=True)
class CaptureGesture:
    """Gesture event normalized from KLayout input."""

    gesture_type: str
    point: Point
    shift_pressed: bool = False


class CaptureGesturePolicy:
    """Validate capture gestures while preserving normal KLayout navigation."""

    def accepts(self, primitive: CanvasObjectType, gesture: CaptureGesture) -> bool:
        """Return whether a gesture belongs to the armed capture primitive."""

        if not gesture.shift_pressed:
            return False
        if primitive is CanvasObjectType.SITE_BOX:
            return gesture.gesture_type in {"drag_start", "drag_update", "drag_release"}
        if primitive in {CanvasObjectType.LINE, CanvasObjectType.MEASUREMENT}:
            return gesture.gesture_type in {"drag_start", "drag_update", "drag_release"}
        if primitive in {CanvasObjectType.POINT, CanvasObjectType.ELLIPSOMETRY_POINT}:
            return gesture.gesture_type == "click"
        return False


class BoxCaptureTool:
    """Reusable Shift-drag box capture tool."""

    primitive = CanvasObjectType.SITE_BOX

    def __init__(
        self,
        engine: CanvasInteractionEngine | None = None,
        policy: CaptureGesturePolicy | None = None,
    ) -> None:
        self._engine = engine if engine is not None else CanvasInteractionEngine()
        self._policy = policy if policy is not None else CaptureGesturePolicy()

    def arm(self, context: InteractionContext, parent_id: str | None = None) -> InteractionContext:
        """Arm box capture without affecting KLayout navigation until Shift-drag."""

        return self._engine.arm_box_capture(context, parent_id)

    def handle(
        self,
        session: SessionRecord,
        context: InteractionContext,
        gesture: CaptureGesture,
    ) -> InteractionResult:
        """Handle a normalized box gesture."""

        if not self._policy.accepts(self.primitive, gesture):
            return InteractionResult(session, context, handled=False)
        if gesture.gesture_type == "drag_start":
            return self._engine.start_drag(session, context, gesture.point, True)
        if gesture.gesture_type == "drag_update":
            return self._engine.update_drag(session, context, gesture.point, True)
        return self._engine.release_drag(session, context, gesture.point, True)

    def cancel(self, session: SessionRecord, context: InteractionContext) -> InteractionResult:
        """Cancel box capture and remove live previews."""

        return self._engine.exit_capture(session, context)


class LineCaptureTool:
    """Reusable Shift-drag line capture tool contract."""

    primitive = CanvasObjectType.MEASUREMENT

    def __init__(
        self,
        engine: CanvasInteractionEngine | None = None,
        policy: CaptureGesturePolicy | None = None,
    ) -> None:
        self._engine = engine if engine is not None else CanvasInteractionEngine()
        self._policy = policy if policy is not None else CaptureGesturePolicy()

    def arm(self, context: InteractionContext, parent_id: str | None = None) -> InteractionContext:
        """Arm line capture for a future measurement workflow controller."""

        return self._engine.arm_line_capture(context, parent_id)

    def handle(
        self,
        session: SessionRecord,
        context: InteractionContext,
        gesture: CaptureGesture,
    ) -> InteractionResult:
        """Handle a normalized measurement-line gesture."""

        if not self._policy.accepts(self.primitive, gesture):
            return InteractionResult(session, context, handled=False)
        if gesture.gesture_type == "drag_start":
            return self._engine.start_drag(session, context, gesture.point, True)
        if gesture.gesture_type == "drag_update":
            return self._engine.update_drag(session, context, gesture.point, True)
        return self._engine.release_drag(session, context, gesture.point, True)


class PointCaptureTool:
    """Reusable Shift-click point capture tool contract."""

    primitive = CanvasObjectType.POINT

    def __init__(self, policy: CaptureGesturePolicy | None = None) -> None:
        self._policy = policy if policy is not None else CaptureGesturePolicy()

    def arm(self, context: InteractionContext, parent_id: str | None = None) -> InteractionContext:
        """Arm point capture for future point-inspection workflows."""

        from dataclasses import replace

        return replace(context, armed_object_type=self.primitive, active_parent_id=parent_id)

    def handle(
        self,
        session: SessionRecord,
        context: InteractionContext,
        gesture: CaptureGesture,
    ) -> InteractionResult:
        """Handle a normalized point gesture when a compound workflow is active."""

        if not self._policy.accepts(self.primitive, gesture):
            return InteractionResult(session, context, handled=False)
        request = active_compound_request(session, "point")
        if request is not None and session.workflow.pending_item_ref:
            try:
                updated = add_point_feature(
                    session,
                    session.workflow.pending_item_ref,
                    gesture.point,
                    request,
                )
            except ValueError as exc:
                return InteractionResult(session, context, handled=True, messages=(str(exc),))
            return InteractionResult(updated, context, handled=True)
        return InteractionResult(
            session,
            context,
            handled=True,
            messages=("Point capture is not implemented yet.",),
        )


class CapturePreviewOverlay:
    """Small adapter that applies preview/object overlays from interaction results."""

    def __init__(self, manager: CanvasOverlayManager) -> None:
        self._manager = manager

    def restore(self, session: SessionRecord) -> None:
        """Restore all persistent overlays for a session."""

        self._manager.restore_session(session)


class CaptureToolPresenter:
    """Build capture-tool status view models."""

    def build(self, context: InteractionContext) -> CaptureToolStatusViewModel:
        """Return current capture-tool status."""

        primitive = context.armed_object_type.value if context.armed_object_type else "none"
        return CaptureToolStatusViewModel(
            tool_id=primitive,
            primitive=primitive,
            armed=context.armed_object_type is not None,
            gesture_hint=_hint(primitive),
            active_parent_id=context.active_parent_id or "",
        )


def _hint(primitive: str) -> str:
    if primitive == "site_box":
        return "Left Shift + drag box"
    if primitive in {"line", "measurement", "profilometry_line", "multi_line"}:
        return "Left Shift + drag line"
    if primitive in {"point", "ellipsometry_point"}:
        return "Left Shift + click point"
    return "KLayout navigation active"

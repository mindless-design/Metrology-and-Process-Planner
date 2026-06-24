"""KLayout gesture adapter for persistent canvas capture tools."""

from __future__ import annotations

from dataclasses import dataclass, replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CanvasObjectType, SessionRecord
from metrology_process_planner.ui.capture.tools import (
    BoxCaptureTool,
    CaptureGesture,
    LineCaptureTool,
    PointCaptureTool,
)
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


@dataclass(frozen=True)
class KLayoutGestureEvent:
    """Normalized KLayout pointer event for capture gestures."""

    gesture_type: str
    x: float
    y: float
    shift_pressed: bool = False


class KLayoutCaptureGestureAdapter:
    """Route KLayout gestures into pure capture tools and marker overlays."""

    def __init__(
        self,
        session: SessionRecord,
        overlay_manager: CanvasOverlayManager,
        context: InteractionContext | None = None,
        box_tool: BoxCaptureTool | None = None,
        line_tool: LineCaptureTool | None = None,
        point_tool: PointCaptureTool | None = None,
    ) -> None:
        self._session = session
        self._context = context if context is not None else InteractionContext()
        self._overlay_manager = overlay_manager
        self._box_tool = box_tool if box_tool is not None else BoxCaptureTool()
        self._line_tool = line_tool if line_tool is not None else LineCaptureTool()
        self._point_tool = point_tool if point_tool is not None else PointCaptureTool()

    @property
    def session(self) -> SessionRecord:
        """Return the latest session produced by handled gestures."""

        return self._session

    @property
    def context(self) -> InteractionContext:
        """Return the latest ephemeral capture context."""

        return self._context

    def arm_box_capture(self, parent_id: str | None = None) -> None:
        """Arm Shift-drag box capture without intercepting navigation yet."""

        self._context = self._box_tool.arm(self._context, parent_id)

    def arm_line_capture(self, parent_id: str | None = None) -> None:
        """Arm Shift-drag line capture for a saved parent capture."""

        self._context = self._line_tool.arm(self._context, parent_id)

    def arm_point_capture(self, parent_id: str | None = None) -> None:
        """Arm Shift-click point capture for future point workflows."""

        self._context = self._point_tool.arm(self._context, parent_id)

    def disarm_capture(self) -> None:
        """Return KLayout to normal navigation by clearing armed state."""

        self._context = replace(
            self._context,
            armed_object_type=None,
            live_preview_id=None,
            drag_start=None,
        )

    def handle(self, event: KLayoutGestureEvent) -> InteractionResult:
        """Handle a normalized event and restore overlays when state changes."""

        tool = self._active_tool()
        if tool is None:
            return InteractionResult(self._session, self._context, handled=False)
        previous_session = self._session
        result = tool.handle(self._session, self._context, _to_capture_gesture(event))
        self._session = result.session
        self._context = result.context
        if result.handled and result.session != previous_session:
            self._overlay_manager.restore_session(self._session)
        return result

    def _active_tool(self) -> BoxCaptureTool | LineCaptureTool | PointCaptureTool | None:
        primitive = self._context.armed_object_type
        if primitive is CanvasObjectType.SITE_BOX:
            return self._box_tool
        if primitive in {CanvasObjectType.LINE, CanvasObjectType.MEASUREMENT}:
            return self._line_tool
        if primitive is CanvasObjectType.POINT:
            return self._point_tool
        return None


def _to_capture_gesture(event: KLayoutGestureEvent) -> CaptureGesture:
    return CaptureGesture(
        event.gesture_type,
        Point(event.x, event.y),
        shift_pressed=event.shift_pressed,
    )

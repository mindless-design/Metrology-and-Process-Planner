"""KLayout GUI capture-surface probe script builders."""

from __future__ import annotations

import textwrap


def capture_surface_contract_script() -> str:
    """Return a GUI-mode probe for KLayout capture adapter contracts."""

    return "\n".join(
        (
            _imports(),
            _session_helpers(),
            _adapter_helper(),
            _scenario_steps(),
            _report_update(),
        )
    )


def _imports() -> str:
    return textwrap.dedent(
        """
        import pya
        from metrology_process_planner.domains.geometry import Box
        from metrology_process_planner.domains.session import (
            CanvasObject, CanvasObjectType, CanvasVisualFlag,
            CanvasWorkflowState, CaptureGeometry, CaptureRecord,
            SessionMode, SessionRecord,
        )
        from metrology_process_planner.infrastructure.klayout.capture_adapter import (
            KLayoutCaptureGestureAdapter, KLayoutGestureEvent,
        )
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import CanvasOverlayManager
        """
    )


def _session_helpers() -> str:
    return textwrap.dedent(
        """
        def empty_session():
            return SessionRecord(
                id="session-001", name="Demo", mode=SessionMode.SIMPLE_CAPTURE,
                created_at="2026-06-25T00:00:00Z",
                updated_at="2026-06-25T00:00:00Z",
            )

        def saved_capture_session():
            geometry = CaptureGeometry.box(Box(0, 0, 5, 5))
            return SessionRecord(
                id="session-001", name="Demo", mode=SessionMode.SIMPLE_CAPTURE,
                created_at="2026-06-25T00:00:00Z",
                updated_at="2026-06-25T00:00:00Z",
                captures=(CaptureRecord("cap-001", "Site", geometry, "2026-06-25T00:00:00Z"),),
                canvas_objects=(CanvasObject(
                    "canvas-cap", "session-001", "cap-001", CanvasObjectType.SITE_BOX,
                    None, geometry, CanvasWorkflowState.SAVED,
                    visual_state=(CanvasVisualFlag.SELECTED,),
                ),),
            )
        """
    )


def _adapter_helper() -> str:
    return textwrap.dedent(
        """
        def adapter_for(session):
            backend = KLayoutOverlayBackend(
                marker_factory=lambda command: ("marker", command.object_id)
            )
            return KLayoutCaptureGestureAdapter(session, CanvasOverlayManager(backend)), backend
        """
    )


def _scenario_steps() -> str:
    return textwrap.dedent(
        """
        box_adapter, box_backend = adapter_for(empty_session())
        box_adapter.arm_box_capture()
        box_ignored = box_adapter.handle(KLayoutGestureEvent("drag_start", 1, 1))
        box_adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))
        box_adapter.handle(KLayoutGestureEvent("drag_update", 4, 4, True))
        box_released = box_adapter.handle(KLayoutGestureEvent("drag_release", 5, 5, True))

        measurement_adapter, measurement_backend = adapter_for(saved_capture_session())
        measurement_adapter.arm_line_capture("canvas-cap")
        measurement_adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))
        measurement_adapter.handle(KLayoutGestureEvent("drag_update", 3, 1, True))
        measurement_released = measurement_adapter.handle(
            KLayoutGestureEvent("drag_release", 4, 1, True)
        )

        line_adapter, line_backend = adapter_for(saved_capture_session())
        line_adapter.arm_line_capture()
        line_adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))
        line_adapter.handle(KLayoutGestureEvent("drag_update", 3, 1, True))
        line_released = line_adapter.handle(KLayoutGestureEvent("drag_release", 4, 1, True))

        point_adapter, point_backend = adapter_for(saved_capture_session())
        point_adapter.arm_point_capture()
        point_released = point_adapter.handle(KLayoutGestureEvent("click", 2, 2, True))
        """
    )


def _report_update() -> str:
    return textwrap.dedent(
        """
        report.update({
            "main_window_type": type(pya.Application.instance().main_window()).__name__,
            "box_ignored": box_ignored.handled,
            "box_released": box_released.handled,
            "box_pending_kind": box_adapter.session.pending_captures[0].geometry.kind.value,
            "measurement_released": measurement_released.handled,
            "measurement_id": measurement_adapter.session.captures[0].measurements[0].id,
            "standalone_line_released": line_released.handled,
            "standalone_line_kind": line_adapter.session.pending_captures[0].geometry.kind.value,
            "point_released": point_released.handled,
            "point_kind": point_adapter.session.pending_captures[0].geometry.kind.value,
            "overlay_command_counts": {
                "box": len(box_backend.commands),
                "measurement": len(measurement_backend.commands),
                "line": len(line_backend.commands),
                "point": len(point_backend.commands),
            },
        })
        """
    )

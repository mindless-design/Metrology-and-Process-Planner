"""KLayout batch-mode probes for standalone capture workflows."""

from __future__ import annotations

import textwrap


def standalone_point_capture_adapter_script() -> str:
    """Return a probe script for standalone point capture in KLayout."""

    return textwrap.dedent(_STANDALONE_POINT_CAPTURE_ADAPTER_SCRIPT)


def standalone_line_capture_adapter_script() -> str:
    """Return a probe script for standalone line capture in KLayout."""

    return textwrap.dedent(_STANDALONE_LINE_CAPTURE_ADAPTER_SCRIPT)


_STANDALONE_POINT_CAPTURE_ADAPTER_SCRIPT = """
import pya
from metrology_process_planner.domains.session import SessionMode, SessionRecord
from metrology_process_planner.infrastructure.klayout.capture_adapter import (
    KLayoutCaptureGestureAdapter,
    KLayoutGestureEvent,
)
from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
from metrology_process_planner.workflows import CanvasOverlayManager

layout = pya.Layout()
cell = layout.create_cell("TOP")
layer = layout.layer(1, 0)
cell.shapes(layer).insert(pya.Box(0, 0, 1000, 1000))
before = cell.shapes(layer).size()

session = SessionRecord(
    "session-001",
    "Demo",
    SessionMode.SIMPLE_CAPTURE,
    "2026-06-25T00:00:00Z",
    "2026-06-25T00:00:00Z",
)
backend = KLayoutOverlayBackend(lambda command: ("marker", command.object_id))
adapter = KLayoutCaptureGestureAdapter(session, CanvasOverlayManager(backend))

adapter.arm_point_capture()
ignored = adapter.handle(KLayoutGestureEvent("click", 2, 2))
clicked = adapter.handle(KLayoutGestureEvent("click", 2, 2, True))

after = cell.shapes(layer).size()
pending = adapter.session.pending_captures[0]
overlay_ids = {command.object_id for command in backend.commands}
print("POINT_IGNORED=" + str(ignored.handled))
print("POINT_CLICKED=" + str(clicked.handled))
print("PENDING_KIND=" + pending.geometry.kind.value)
print("POINT_X=" + str(pending.geometry.point.x))
print("POINT_Y=" + str(pending.geometry.point.y))
print("LAYOUT_UNCHANGED=" + str(before == after))
print("OVERLAY_POINT=" + str(pending.canvas_object_id in overlay_ids))
"""


_STANDALONE_LINE_CAPTURE_ADAPTER_SCRIPT = """
import pya
from metrology_process_planner.domains.session import SessionMode, SessionRecord
from metrology_process_planner.infrastructure.klayout.capture_adapter import (
    KLayoutCaptureGestureAdapter,
    KLayoutGestureEvent,
)
from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
from metrology_process_planner.workflows import CanvasOverlayManager

layout = pya.Layout()
cell = layout.create_cell("TOP")
layer = layout.layer(1, 0)
cell.shapes(layer).insert(pya.Box(0, 0, 1000, 1000))
before = cell.shapes(layer).size()

session = SessionRecord(
    "session-001",
    "Demo",
    SessionMode.SIMPLE_CAPTURE,
    "2026-06-25T00:00:00Z",
    "2026-06-25T00:00:00Z",
)
backend = KLayoutOverlayBackend(lambda command: ("marker", command.object_id))
adapter = KLayoutCaptureGestureAdapter(session, CanvasOverlayManager(backend))

adapter.arm_line_capture()
ignored = adapter.handle(KLayoutGestureEvent("drag_start", 1, 1))
adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))
adapter.handle(KLayoutGestureEvent("drag_update", 3, 1, True))
released = adapter.handle(KLayoutGestureEvent("drag_release", 4, 1, True))

after = cell.shapes(layer).size()
pending = adapter.session.pending_captures[0]
overlay_ids = {command.object_id for command in backend.commands}
print("LINE_IGNORED=" + str(ignored.handled))
print("LINE_RELEASED=" + str(released.handled))
print("PENDING_KIND=" + pending.geometry.kind.value)
print("LINE_START_X=" + str(pending.geometry.start.x))
print("LINE_END_X=" + str(pending.geometry.end.x))
print("LAYOUT_UNCHANGED=" + str(before == after))
print("OVERLAY_LINE=" + str(pending.canvas_object_id in overlay_ids))
"""

"""KLayout batch-mode point-capture probe script builders."""

from __future__ import annotations

import textwrap


def ellipsometry_point_capture_adapter_script() -> str:
    """Return a probe script for ellipsometry compound point capture in KLayout."""

    return textwrap.dedent(_ELLIPSOMETRY_POINT_CAPTURE_ADAPTER_SCRIPT)


_ELLIPSOMETRY_POINT_CAPTURE_ADAPTER_SCRIPT = """
import pya
from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    PendingCapture,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.infrastructure.klayout.capture_adapter import (
    KLayoutCaptureGestureAdapter,
    KLayoutGestureEvent,
)
from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
from metrology_process_planner.workflows import CanvasOverlayManager
from metrology_process_planner.workflows.compound_capture import (
    arm_inner_feature_capture,
    ellipsometry_request,
)

layout = pya.Layout()
cell = layout.create_cell("TOP")
layer = layout.layer(1, 0)
cell.shapes(layer).insert(pya.Box(0, 0, 1000, 1000))
before = cell.shapes(layer).size()

geometry = CaptureGeometry.box(Box(0, 0, 10, 10))
canvas = CanvasObject(
    "canvas-parent",
    "session-001",
    "pending-001",
    CanvasObjectType.SITE_BOX,
    None,
    geometry,
    CanvasWorkflowState.PENDING,
    visual_state=(CanvasVisualFlag.ACTIVE_PARENT,),
)
pending = PendingCapture(
    "pending-001",
    "session-001",
    "canvas-parent",
    CanvasObjectType.SITE_BOX,
    geometry,
    image_artifact_path="images/pending-001.png",
)
session = SessionRecord(
    "session-001",
    "Demo",
    SessionMode.ELLIPSOMETRY_PLANNER,
    "2026-06-24T00:00:00Z",
    "2026-06-24T00:00:00Z",
    canvas_objects=(canvas,),
    pending_captures=(pending,),
)
session = arm_inner_feature_capture(session, "pending-001", ellipsometry_request())
backend = KLayoutOverlayBackend(lambda command: ("marker", command.object_id))
adapter = KLayoutCaptureGestureAdapter(session, CanvasOverlayManager(backend))

adapter.arm_point_capture("canvas-parent")
ignored = adapter.handle(KLayoutGestureEvent("click", 5, 5))
clicked = adapter.handle(KLayoutGestureEvent("click", 5, 5, True))

after = cell.shapes(layer).size()
compound = dict(adapter.session.pending_captures[0].metadata)["compound"]
feature = dict(compound)["feature"]
overlay_ids = {command.object_id for command in backend.commands}
print("POINT_IGNORED=" + str(ignored.handled))
print("POINT_CLICKED=" + str(clicked.handled))
print("FEATURE_ROLE=" + str(feature["role"]))
print("CHILD_TYPE=" + adapter.session.canvas_objects[1].object_type.value)
print("LAYOUT_UNCHANGED=" + str(before == after))
print("OVERLAY_CHILD=" + str("canvas-001" in overlay_ids))
"""

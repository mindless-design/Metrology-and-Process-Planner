from pathlib import Path

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.process import (
    CrossSectionProfile,
    MaterialInterval,
    StackColumn,
)
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    PendingCapture,
    SessionMode,
    SessionRecord,
)
from tests.artifact_helpers import capture_crop_artifact


class FakeRasterizer:
    def rasterize_svg(
        self,
        svg_text: str,
        destination: Path,
        width_px: int,
        height_px: int,
    ) -> None:
        destination.write_bytes(b"fake-png")


class FailingRasterizer:
    def rasterize_svg(
        self,
        svg_text: str,
        destination: Path,
        width_px: int,
        height_px: int,
    ) -> None:
        raise RuntimeError("qt unavailable")


class FailingDrawingStore:
    def export_capture_scene(self, paths, capture_id, scene, rasterizer=None):
        raise OSError("disk full")

    def export_owner_scene(self, paths, owner_type, owner_id, scene, rasterizer=None):
        raise OSError("disk full")


def empty_session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.PROCESS_AWARE_METROLOGY,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
    )


def session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        captures=(capture(),),
        artifacts={"capture-cap-001-crop": capture_crop_artifact()},
        canvas_objects=(
            CanvasObject(
                "canvas-cap",
                "session-001",
                "cap-001",
                CanvasObjectType.SITE_BOX,
                None,
                CaptureGeometry.box(Box(0, 0, 10, 10)),
                CanvasWorkflowState.SAVED,
            ),
            CanvasObject(
                "canvas-pending",
                "session-001",
                "pending-001",
                CanvasObjectType.SITE_BOX,
                None,
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                CanvasWorkflowState.PENDING,
            ),
        ),
        pending_captures=(
            PendingCapture(
                "pending-001",
                "session-001",
                "canvas-pending",
                CanvasObjectType.SITE_BOX,
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                image_artifact_path="images/pending-001.png",
            ),
        ),
    )


def session_without_pending() -> SessionRecord:
    item = session()
    return SessionRecord(
        id=item.id,
        name=item.name,
        mode=item.mode,
        created_at=item.created_at,
        updated_at=item.updated_at,
        captures=item.captures,
        artifacts=item.artifacts,
        canvas_objects=item.canvas_objects[:1],
    )


def session_without_box_bounds() -> SessionRecord:
    line_capture = CaptureRecord(
        id="cap-001",
        label="Line Site",
        geometry=CaptureGeometry.line(Point(0, 0), Point(1, 1)),
        created_at="2026-06-23T20:00:00Z",
    )
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        captures=(line_capture,),
    )


def capture() -> CaptureRecord:
    return CaptureRecord(
        id="cap-001",
        label="Site 1",
        geometry=CaptureGeometry.box(Box(0, 0, 10, 10)),
        created_at="2026-06-23T20:00:00Z",
        measurements=(
            MeasurementRecord("meas-001", "Gate CD", Point(1, 2), Point(9, 8)),
        ),
    )


def profile() -> CrossSectionProfile:
    return CrossSectionProfile(
        columns=(
            StackColumn(
                x=0.0,
                intervals=(MaterialInterval("si", 0.0, 1.0),),
            ),
            StackColumn(
                x=1.0,
                intervals=(MaterialInterval("si", 0.0, 1.5),),
            ),
        )
    )

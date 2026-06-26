from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    PendingCapture,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows.editor import SessionDocumentBuilder


class FailingStore:
    def save(self, document, paths):
        raise OSError("disk full")


def document():
    return SessionDocumentBuilder().build(session(), raw_payload=session().to_dict())


def session_without_pending() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
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
        canvas_objects=(
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

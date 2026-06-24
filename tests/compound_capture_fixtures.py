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


def base_session(mode: SessionMode) -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=mode,
        created_at="2026-06-24T00:00:00Z",
        updated_at="2026-06-24T00:00:00Z",
    )


def pending_parent(mode: SessionMode) -> SessionRecord:
    session = base_session(mode)
    geometry = CaptureGeometry.box(Box(0, 0, 10, 10))
    canvas = CanvasObject(
        "canvas-parent",
        session.id,
        "pending-001",
        CanvasObjectType.SITE_BOX,
        None,
        geometry,
        CanvasWorkflowState.PENDING,
        visual_state=(CanvasVisualFlag.ACTIVE_PARENT,),
    )
    pending = PendingCapture(
        "pending-001",
        session.id,
        canvas.id,
        CanvasObjectType.SITE_BOX,
        geometry,
        image_artifact_path="images/pending-001.png",
    )
    return SessionRecord(
        id=session.id,
        name=session.name,
        mode=session.mode,
        created_at=session.created_at,
        updated_at=session.updated_at,
        canvas_objects=(canvas,),
        pending_captures=(pending,),
    )

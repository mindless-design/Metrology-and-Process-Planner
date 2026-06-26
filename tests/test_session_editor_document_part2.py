import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    PendingCapture,
    SessionMode,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.artifact_helpers import capture_crop_artifact


def _session() -> SessionRecord:
    measurement = MeasurementRecord("meas-001", "Gate CD", Point(1, 1), Point(2, 1))
    capture = CaptureRecord(
        id="cap-001",
        label="Site 1",
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        created_at="2026-06-23T20:00:00Z",
        measurements=(measurement,),
    )
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        captures=(capture,),
        artifacts={"capture-cap-001-crop": capture_crop_artifact(width_px=0, height_px=0)},
        canvas_objects=(_canvas("canvas-cap", "cap-001"), _canvas("canvas-pending", "pending-001")),
        pending_captures=(
            PendingCapture(
                "pending-001",
                "session-001",
                "canvas-pending",
                CanvasObjectType.SITE_BOX,
                CaptureGeometry.box(Box(0, 0, 1, 1)),
                image_artifact_path="images/pending-001.png",
            ),
        ),
        warnings=(WarningRecord("warn-001", "Missing crop", artifact_path="images/cap-001.png"),),
    )

def _canvas(object_id: str, record_id: str) -> CanvasObject:
    return CanvasObject(
        id=object_id,
        session_id="session-001",
        record_id=record_id,
        object_type=CanvasObjectType.SITE_BOX,
        parent_id=None,
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        workflow_state=CanvasWorkflowState.SAVED,
    )

if __name__ == "__main__":
    unittest.main()


class SessionEditorDocumentTestsPart2(unittest.TestCase):
    def test_artifact_actions_include_artifact_id_payload(self) -> None:
        document = SessionDocumentBuilder().build(_session())
        capture = document.items_by_id["capture:cap-001"]
        actions = DefaultSessionModeAdapter().actions(document.session, capture)

        regenerate = next(
            action
            for action in actions
            if action.action_type.value == "regenerate_artifact"
        )

        self.assertEqual(
            "capture-cap-001-crop",
            dict(regenerate.payload)["artifact_id"],
        )

    def test_multiple_artifacts_create_distinct_repair_actions(self) -> None:
        session = _session()
        artifacts = dict(session.artifacts or {})
        artifacts["capture-cap-001-overview"] = capture_crop_artifact(
            path="images/cap-001-overview.png"
        )
        overview = artifacts["capture-cap-001-overview"]
        artifacts["capture-cap-001-overview"] = replace(
            overview,
            id="capture-cap-001-overview",
            owner=ArtifactOwnerRef("capture", "cap-001", "overview"),
        )
        document = SessionDocumentBuilder().build(replace(session, artifacts=artifacts))
        capture = document.items_by_id["capture:cap-001"]

        actions = DefaultSessionModeAdapter().actions(document.session, capture)
        artifact_ids = {
            dict(action.payload).get("artifact_id", "")
            for action in actions
            if action.action_type.value == "regenerate_artifact"
        }

        self.assertEqual(
            {"capture-cap-001-crop", "capture-cap-001-overview"},
            artifact_ids,
        )

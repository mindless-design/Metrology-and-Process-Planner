import unittest

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import (
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


class SessionEditorDocumentTests(unittest.TestCase):
    def test_builder_selects_pending_capture_and_groups_non_empty_items(self) -> None:
        document = SessionDocumentBuilder().build(_session())

        self.assertEqual("pending:pending-001", document.selection.selected_item_id)
        self.assertEqual("pending:pending-001", document.pending_capture_item_id)
        self.assertIn("canvas-pending", document.selection.selected_canvas_object_ids)
        self.assertEqual(
            ["Dashboard", "Setup", "Pending", "Saved Captures", "Measurements", "Warnings"],
            [group.label for group in document.navigator_groups],
        )

    def test_capture_measurement_and_canvas_indexes_are_normalized(self) -> None:
        document = SessionDocumentBuilder().build(_session())

        capture = document.items_by_id["capture:cap-001"]
        measurement = document.items_by_id["measurement:meas-001"]

        self.assertEqual((measurement.item_id,), capture.child_ids)
        self.assertEqual("capture:cap-001", measurement.parent_id)
        self.assertEqual(("canvas-cap",), capture.canvas_object_ids)
        self.assertEqual("capture:cap-001", document.canvas_object_to_item_id["canvas-cap"])

    def test_warning_artifact_becomes_missing_preview(self) -> None:
        document = SessionDocumentBuilder().build(_session())
        capture = document.items_by_id["capture:cap-001"]
        adapter = DefaultSessionModeAdapter()

        self.assertEqual("missing", capture.artifact_refs[0].status)
        previews = adapter.preview_options(document.session, capture)

        self.assertEqual("missing", previews[0].status)
        self.assertIn("Missing artifact", previews[0].placeholder)

    def test_adapter_supplies_metadata_and_actions_for_pending_item(self) -> None:
        document = SessionDocumentBuilder().build(_session())
        pending = document.items_by_id["pending:pending-001"]
        adapter = DefaultSessionModeAdapter()

        fields = adapter.metadata_fields(document.session, pending)
        actions = adapter.actions(document.session, pending)

        self.assertTrue(any(field.key == "label" and field.required for field in fields))
        self.assertTrue(any(action.action_type.value == "pending_save" for action in actions))


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

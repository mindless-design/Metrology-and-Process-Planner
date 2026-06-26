import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows import (
    MeasurementCompletionChoice,
    apply_measurement_completion_choice,
)
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    SessionRenderBridge,
)
from metrology_process_planner.workflows.measurement_workflow import add_pending_measurement_line
from tests.editor_render_fixtures import FakeRasterizer
from tests.measurement_child_fixtures import measurement_metadata_edits, saved_capture_session


class MeasurementCompletionTargetingTests(unittest.TestCase):
    def test_take_another_uses_newly_saved_measurement_parent(self) -> None:
        saved = _saved_second_capture_measurement_session()

        result = apply_measurement_completion_choice(
            saved,
            MeasurementCompletionChoice.TAKE_ANOTHER,
        )

        self.assertEqual("success", result.status)
        self.assertEqual("capture:cap-002", result.selected_item_id)
        self.assertEqual("capture:cap-002", result.session.workflow.pending_item_ref)
        self.assertNotIn(
            CanvasVisualFlag.ACTIVE_PARENT,
            result.session.canvas_objects[0].visual_state,
        )
        self.assertIn(
            CanvasVisualFlag.ACTIVE_PARENT,
            result.session.canvas_objects[1].visual_state,
        )


def _saved_second_capture_measurement_session():
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = SessionPaths.for_folder(Path(temp_dir))
        paths.ensure_created()
        dispatcher = EditorActionDispatcher(
            paths=paths,
            render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
        )
        pending = add_pending_measurement_line(
            _two_capture_session(),
            "canvas-cap-002",
            Point(11, 11),
            Point(14, 11),
        )
        document = measurement_metadata_edits(SessionDocumentBuilder().build(pending))
        return dispatcher.dispatch(
            document,
            EditorAction(EditorActionType.SAVE_EDITS, "Save"),
        ).document.session


def _two_capture_session():
    source = saved_capture_session()
    first_capture = replace(
        source.captures[0],
        measurements=(
            MeasurementRecord(
                "meas-000",
                "Older CD",
                Point(1, 1),
                Point(2, 1),
                metadata={"workflow_state": "saved"},
            ),
        ),
    )
    second_capture = CaptureRecord(
        "cap-002",
        "Second Site",
        CaptureGeometry.box(Box(10, 10, 15, 15)),
        "2026-06-23T20:00:00Z",
    )
    second_canvas = CanvasObject(
        "canvas-cap-002",
        source.id,
        "cap-002",
        CanvasObjectType.SITE_BOX,
        None,
        second_capture.geometry,
        CanvasWorkflowState.SAVED,
    )
    return replace(
        source,
        captures=(first_capture, second_capture),
        canvas_objects=source.canvas_objects + (second_canvas,),
    )


if __name__ == "__main__":
    unittest.main()

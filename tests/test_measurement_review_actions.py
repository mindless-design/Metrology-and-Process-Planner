import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionRenderBridge,
)
from tests.editor_render_fixtures import FakeRasterizer
from tests.measurement_child_fixtures import (
    document_with_pending_measurement,
    measurement_metadata_edits,
    saved_capture_session,
)


class MeasurementReviewActionTests(unittest.TestCase):
    def test_pending_measurement_exposes_review_actions(self) -> None:
        document = document_with_pending_measurement(saved_capture_session())
        item = document.items_by_id["measurement:meas-001"]

        actions = DefaultSessionModeAdapter().actions(document.session, item)

        self.assertEqual(
            [
                "Save Edits",
                "Save Measurement",
                "Retake Measurement Line",
                "Discard Measurement",
                "Return to Parent Capture",
                "Export CSV",
                "Build Report",
            ],
            [action.label for action in actions],
        )
        self.assertEqual(EditorActionType.SAVE_MEASUREMENT, actions[1].action_type)
        self.assertEqual("capture:cap-001", actions[4].item_id)

    def test_save_measurement_action_returns_completion_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            dispatcher = EditorActionDispatcher(
                paths=paths,
                render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
            )
            document = measurement_metadata_edits(
                document_with_pending_measurement(saved_capture_session())
            )

            result = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.SAVE_MEASUREMENT,
                    "Save Measurement",
                    "measurement:meas-001",
                ),
            )

        measurement = result.document.session.captures[0].measurements[0]
        self.assertEqual("success", result.status)
        self.assertEqual("saved", measurement.metadata["workflow_state"])
        self.assertIsNotNone(result.post_action_prompt)

    def test_retake_and_discard_are_modeless_transitions(self) -> None:
        document = document_with_pending_measurement(saved_capture_session())
        dispatcher = EditorActionDispatcher()

        retake = dispatcher.dispatch(
            document,
            EditorAction(
                EditorActionType.RETAKE_MEASUREMENT_LINE,
                "Retake",
                "measurement:meas-001",
            ),
        )
        discarded = dispatcher.dispatch(
            document,
            EditorAction(
                EditorActionType.DISCARD_MEASUREMENT,
                "Discard",
                "measurement:meas-001",
            ),
        )

        self.assertEqual("success", retake.status)
        self.assertEqual((), retake.document.session.captures[0].measurements)
        self.assertTrue(retake.document.session.workflow.active)
        self.assertEqual("measurement", retake.document.session.workflow.active_primitive)
        self.assertEqual("success", discarded.status)
        self.assertEqual((), discarded.document.session.captures[0].measurements)
        self.assertFalse(discarded.document.session.workflow.active)


if __name__ == "__main__":
    unittest.main()

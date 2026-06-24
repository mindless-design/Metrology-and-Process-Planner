import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.session import CanvasVisualFlag
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows import (
    MeasurementCompletionChoice,
    apply_measurement_completion_choice,
)
from metrology_process_planner.workflows.editor import (
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


class MeasurementCompletionPromptTests(unittest.TestCase):
    def test_save_pending_measurement_returns_only_allowed_prompt(self) -> None:
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
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        prompt = result.post_action_prompt
        self.assertEqual("success", result.status)
        self.assertIsNotNone(prompt)
        self.assertTrue(prompt.blocking_allowed)
        self.assertEqual("Do you want to take another measurement?", prompt.message)
        self.assertEqual(
            (
                ("take_another_measurement", "Take Another Measurement"),
                ("return_to_editor", "Return to Editor"),
                ("done", "Done"),
            ),
            prompt.choices,
        )

    def test_take_another_measurement_rearms_same_parent_capture(self) -> None:
        saved = _saved_measurement_session()

        result = apply_measurement_completion_choice(
            saved,
            MeasurementCompletionChoice.TAKE_ANOTHER,
        )

        self.assertEqual("success", result.status)
        self.assertEqual("capture:cap-001", result.selected_item_id)
        self.assertTrue(result.session.workflow.active)
        self.assertEqual("measurement", result.session.workflow.active_primitive)
        self.assertIn(CanvasVisualFlag.ACTIVE_PARENT, result.session.canvas_objects[0].visual_state)

    def test_return_to_editor_and_done_clear_measurement_workflow(self) -> None:
        saved = _saved_measurement_session()

        parent = apply_measurement_completion_choice(
            saved,
            MeasurementCompletionChoice.RETURN_TO_EDITOR,
        )
        done = apply_measurement_completion_choice(saved, MeasurementCompletionChoice.DONE)

        self.assertFalse(parent.session.workflow.active)
        self.assertEqual("capture:cap-001", parent.selected_item_id)
        self.assertNotIn(
            CanvasVisualFlag.ACTIVE_PARENT,
            parent.session.canvas_objects[0].visual_state,
        )
        self.assertFalse(done.session.workflow.active)
        self.assertEqual("measurement:meas-001", done.selected_item_id)


def _saved_measurement_session():
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
        return dispatcher.dispatch(
            document,
            EditorAction(EditorActionType.SAVE_EDITS, "Save"),
        ).document.session


if __name__ == "__main__":
    unittest.main()

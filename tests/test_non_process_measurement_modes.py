import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.modes.mode_non_process_builtins import non_process_modes
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    CanvasWorkflowState,
    session_mode_id,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionRenderBridge,
)
from tests.editor_render_fixtures import FakeRasterizer
from tests.measurement_child_fixtures import (
    document_with_pending_measurement,
    saved_capture_session,
)


class NonProcessMeasurementModeTests(unittest.TestCase):
    def test_measurement_save_works_across_recipe_free_modes(self) -> None:
        for mode_id in _recipe_free_mode_ids():
            with self.subTest(mode_id=mode_id), tempfile.TemporaryDirectory() as temp_dir:
                paths = SessionPaths.for_folder(Path(temp_dir))
                paths.ensure_created()
                document = document_with_pending_measurement(_session(mode_id))
                document = _measurement_metadata_edits(document)
                dispatcher = EditorActionDispatcher(
                    paths=paths,
                    render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
                )

                result = dispatcher.dispatch(
                    document,
                    EditorAction(EditorActionType.SAVE_EDITS, "Save"),
                )

                self.assertEqual("success", result.status)
                self.assertIsNotNone(result.post_action_prompt)
                self.assertEqual(
                    (
                        ("take_another_measurement", "Take Another Measurement"),
                        ("return_to_editor", "Return to Editor"),
                        ("done", "Done"),
                    ),
                    result.post_action_prompt.choices,
                )
                session = result.document.session
                measurement = session.captures[0].measurements[0]
                artifact_id = measurement.artifact_refs["measurement_annotation_svg"]
                warning_codes = {warning.code for warning in session.warnings}

                self.assertEqual("Gate CD", measurement.label)
                self.assertEqual("cd", measurement.metadata["measurement_type"])
                self.assertEqual(3.0, measurement.target)
                self.assertEqual(2.5, measurement.lower_spec_limit)
                self.assertEqual(3.5, measurement.upper_spec_limit)
                self.assertEqual("outer_edges", measurement.edge_detection_convention)
                self.assertEqual("#00aaee", measurement.annotation_color)
                self.assertEqual(4.0, measurement.line_weight)
                self.assertEqual("saved", measurement.metadata["workflow_state"])
                self.assertEqual(ArtifactStatus.PRESENT, session.artifacts[artifact_id].status)
                self.assertTrue(any(
                    item.record_id == measurement.id
                    and item.workflow_state is CanvasWorkflowState.SAVED
                    for item in session.canvas_objects
                ))
                self.assertNotIn("PROCESS_RECIPE_MISSING", warning_codes)
                self.assertNotIn("PROCESS_CONTEXT_INVALID", warning_codes)


def _session(mode_id: str):
    return replace(saved_capture_session(), mode=session_mode_id(mode_id))


def _measurement_metadata_edits(document):
    edits = (
        ("label", "Gate CD"),
        ("measurement_type", "cd"),
        ("target", "3.0"),
        ("lsl", "2.5"),
        ("usl", "3.5"),
        ("notes", "Reviewed"),
        ("edge_convention", "outer_edges"),
        ("color", "#00aaee"),
        ("line_weight_px", "4.0"),
    )
    for field, value in edits:
        document = replace_edit(document, field, value)
    return document


def replace_edit(document, field: str, value: str):
    from metrology_process_planner.workflows.editor import mark_metadata_edit

    return mark_metadata_edit(document, "measurement:meas-001", field, value)


def _recipe_free_mode_ids() -> tuple[str, ...]:
    return tuple(dict.fromkeys(definition.mode_id for definition in non_process_modes()))


if __name__ == "__main__":
    unittest.main()

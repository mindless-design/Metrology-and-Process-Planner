import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.process_context import regenerate_process_outputs
from metrology_process_planner.workflows.process_context_models import (
    RegenerateProcessOutputsCommand,
)
from tests.process_output_fixtures import profile_session_with_recipe


class ProcessOutputEditorItemTests(unittest.TestCase):
    def test_process_output_item_exposes_solver_summary_and_artifact_previews(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = regenerate_process_outputs(
                profile_session_with_recipe(Path(folder)),
                RegenerateProcessOutputsCommand("cap-001"),
            ).session

        document = SessionDocumentBuilder().build(session)
        item = document.items_by_id["process_output:process-output-cap-001"]
        fields = DefaultSessionModeAdapter().metadata_fields(document.session, item)
        previews = DefaultSessionModeAdapter().preview_options(document.session, item)
        values = {field.key: field.value for field in fields}

        self.assertEqual("line_profile", values["output_type"])
        self.assertEqual("ready", values["status"])
        self.assertEqual("cap-001", values["capture_id"])
        self.assertEqual("HybridCrossSectionSolver", values["solver_backend"])
        self.assertGreater(int(values["frame_count"]), 0)
        self.assertTrue(previews)
        self.assertTrue(all(preview.role.endswith("_image") for preview in previews))

    def test_regenerate_action_on_process_output_targets_owning_capture(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = regenerate_process_outputs(
                profile_session_with_recipe(Path(folder)),
                RegenerateProcessOutputsCommand("cap-001"),
            ).session
            document = SessionDocumentBuilder().build(session)

            result = EditorActionDispatcher().dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_PROCESS_OUTPUT,
                    "Regenerate Process Output",
                    "process_output:process-output-cap-001",
                ),
            )

        self.assertEqual("success", result.status)
        self.assertEqual(
            "cap-001",
            result.document.session.process_outputs[0].metadata["capture_id"],
        )


if __name__ == "__main__":
    unittest.main()

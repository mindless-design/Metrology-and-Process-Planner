import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus, SessionMode, SessionRecord
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.process_context import regenerate_process_outputs
from metrology_process_planner.workflows.process_context_models import (
    RegenerateProcessOutputsCommand,
)
from tests.process_output_fixtures import (
    profile_session_with_recipe,
    profile_session_without_recipe,
)
from tests.process_output_loop_fixtures import (
    line_session_with_operation,
    point_session_with_recipe,
)


class ProcessOutputLoopTests(unittest.TestCase):
    def test_ellipsometry_generates_point_stack_output_and_preview_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            result = regenerate_process_outputs(
                point_session_with_recipe(Path(folder)),
                RegenerateProcessOutputsCommand("cap-001"),
            )

        capture = result.session.captures[0]
        output = result.session.process_outputs[0]
        extension = capture.extensions["ellipsometry"]

        self.assertEqual("success", result.status)
        self.assertEqual("point_stack", output.output_type)
        self.assertEqual("point_stack_schematic", output.metadata["render_profile"])
        self.assertTrue(extension["point_stack"])
        self.assertIn("stack_image", output.artifact_refs)
        self.assertIn("point_stack_table", output.artifact_refs)
        self.assertIn("process_output_manifest", output.artifact_refs)
        self.assertIn(output.artifact_refs["stack_image"], result.updated_artifact_ids)
        self.assertEqual("show_process_output", result.next_ui_hint)

    def test_profilometry_generates_line_profile_output_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            result = regenerate_process_outputs(
                profile_session_with_recipe(Path(folder)),
                RegenerateProcessOutputsCommand("cap-001"),
            )

        loaded = SessionRecord.from_dict(result.session.to_dict())
        capture = loaded.captures[0]
        output = loaded.process_outputs[0]

        self.assertEqual("success", result.status)
        self.assertEqual("line_profile", output.output_type)
        self.assertEqual("profilometry_surface_profile", output.metadata["render_profile"])
        self.assertTrue(capture.extensions["profilometry"]["outputs"]["step_heights"])
        self.assertEqual(
            output.artifact_refs["profile_image"],
            capture.artifact_refs["profile_image"],
        )

    def test_fib_generates_full_stack_compressed_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            result = regenerate_process_outputs(
                line_session_with_operation(
                    profile_session_with_recipe(Path(folder)),
                    "fib_site_line",
                    "fib_cut",
                    "full_stack_compressed",
                    "fib_full_stack_compressed",
                ),
                RegenerateProcessOutputsCommand("cap-001"),
            )

        output = result.session.process_outputs[0]
        extension = result.session.captures[0].extensions["fib_cut"]

        self.assertEqual("success", result.status)
        self.assertEqual("full_stack_compressed", output.output_type)
        self.assertIn("full_stack_compressed_image", output.artifact_refs)
        self.assertIn("compression_metadata", extension)

    def test_process_flow_generates_changed_frame_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            result = regenerate_process_outputs(
                line_session_with_operation(
                    profile_session_with_recipe(Path(folder)),
                    "process_flow_line",
                    "process_flow",
                    "process_flow_frames",
                    "process_flow_frame",
                    mode=SessionMode.PROCESS_FLOW_SUMMARY,
                ),
                RegenerateProcessOutputsCommand("cap-001"),
            )

        output = result.session.process_outputs[0]
        extension = result.session.captures[0].extensions["process_flow"]

        self.assertEqual("success", result.status)
        self.assertEqual("process_flow_frames", output.output_type)
        self.assertIn("process_flow_frame", output.artifact_refs)
        self.assertTrue(extension["frame_sequence"])

    def test_missing_recipe_creates_warning_and_placeholder_artifacts(self) -> None:
        result = regenerate_process_outputs(
            profile_session_without_recipe(),
            RegenerateProcessOutputsCommand("cap-001"),
        )

        output = result.session.process_outputs[0]

        self.assertEqual("warning", result.status)
        self.assertEqual("PROCESS_RECIPE_MISSING", result.warnings[0].code)
        self.assertEqual("pending_solver", output.status)
        self.assertEqual(
            ArtifactStatus.PLACEHOLDER,
            result.session.artifacts[output.artifact_refs["profile_image"]].status,
        )

    def test_process_output_item_hides_non_process_actions_for_simple_mode(self) -> None:
        document = SessionDocumentBuilder().build(profile_session_without_recipe())
        item = document.items_by_id["capture:cap-001"]
        actions = DefaultSessionModeAdapter().actions(document.session, item)
        self.assertIn("regenerate_process_output", {action.action_type.value for action in actions})

        simple = replace(document.session, mode=SessionMode.SIMPLE_CAPTURE)
        simple_document = SessionDocumentBuilder().build(simple)
        simple_item = simple_document.items_by_id["capture:cap-001"]
        simple_actions = DefaultSessionModeAdapter().actions(simple_document.session, simple_item)
        self.assertNotIn(
            "regenerate_process_output",
            {action.action_type.value for action in simple_actions},
        )

if __name__ == "__main__":
    unittest.main()

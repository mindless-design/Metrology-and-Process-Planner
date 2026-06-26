import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
)
from tests.reporting_workbench_fixtures import document_with_artifact
from tests.session_editor_store_fixtures import document


class SessionEditorStoreDispatcherTestsPart2(unittest.TestCase):
    def test_build_report_action_generates_report_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            dispatcher = EditorActionDispatcher(paths=paths)

            result = dispatcher.dispatch(
                document_with_artifact(ArtifactStatus.PRESENT),
                EditorAction(EditorActionType.BUILD_POWERPOINT, "Build Report"),
            )

        self.assertEqual("success", result.status)
        self.assertIsNotNone(result.output_path)
        self.assertTrue(result.document.session.reports)
        assert result.document.session.artifacts is not None
        self.assertIn(
            "powerpoint_deck",
            {artifact.type for artifact in result.document.session.artifacts.values()},
        )

    def test_open_output_folder_without_paths_returns_structured_unavailable(self) -> None:
        result = EditorActionDispatcher().dispatch(
            document(),
            EditorAction(EditorActionType.OPEN_OUTPUT_FOLDER, "Open Output Folder"),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("No session folder", result.message)

    def test_build_report_without_paths_returns_structured_unavailable(self) -> None:
        result = EditorActionDispatcher().dispatch(
            document_with_artifact(ArtifactStatus.PRESENT),
            EditorAction(EditorActionType.BUILD_POWERPOINT, "Build Report"),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("No session folder", result.message)


if __name__ == "__main__":
    unittest.main()

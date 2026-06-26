import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.persistence.process_output_store import ProcessOutputStore
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.process_context import regenerate_process_outputs
from metrology_process_planner.workflows.process_context_models import (
    RegenerateProcessOutputsCommand,
)
from tests.process_context_fixtures import custom_process_capture_session
from tests.process_output_fixtures import (
    profile_session_with_recipe,
    profile_session_without_recipe,
)


class ProcessOutputRegenerationTests(unittest.TestCase):
    def test_regeneration_runs_hybrid_solver_and_updates_canonical_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = profile_session_with_recipe(Path(folder))

            result = regenerate_process_outputs(
                session,
                RegenerateProcessOutputsCommand("cap-001"),
            )

        output = result.session.process_outputs[0]
        self.assertEqual("success", result.status)
        self.assertEqual("ready", output.status)
        self.assertEqual("HybridCrossSectionSolver", output.metadata["solver_backend"])
        self.assertGreater(output.metadata["frame_count"], 0)
        self.assertGreater(output.metadata["cutline_sample_count"], 0)
        self.assertIn("solver_result", output.extensions)
        self.assertEqual(
            ArtifactStatus.STALE,
            result.session.artifacts["capture-cap-001-profile_image"].status,
        )

    def test_editor_regenerate_process_output_dispatches_solver_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            document = SessionDocumentBuilder().build(profile_session_with_recipe(Path(folder)))

            result = EditorActionDispatcher().dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_PROCESS_OUTPUT,
                    "Regenerate Process Output",
                    "capture:cap-001",
                ),
            )

        self.assertEqual("success", result.status)
        self.assertEqual("ready", result.document.session.process_outputs[0].status)

    def test_editor_regenerate_with_paths_exports_process_output_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            paths = SessionPaths.for_folder(Path(folder) / "session")
            document = SessionDocumentBuilder().build(profile_session_with_recipe(Path(folder)))

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_PROCESS_OUTPUT,
                    "Regenerate Process Output",
                    "capture:cap-001",
                ),
            )

            artifact = result.document.session.artifacts["capture-cap-001-profile_image"]
            output_path = paths.folder / artifact.relative_path

            self.assertEqual("success", result.status)
            self.assertEqual(ArtifactStatus.PRESENT, artifact.status)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual("profile_image", payload["role"])
            self.assertEqual("ready", payload["process_output"]["status"])

    def test_editor_process_output_export_failure_becomes_warning(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            paths = SessionPaths.for_folder(Path(folder) / "session")
            document = SessionDocumentBuilder().build(profile_session_with_recipe(Path(folder)))

            result = EditorActionDispatcher(
                paths=paths,
                process_output_store=FailingProcessOutputStore(),
            ).dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_PROCESS_OUTPUT,
                    "Regenerate Process Output",
                    "capture:cap-001",
                ),
            )

        self.assertEqual("warning", result.status)
        self.assertEqual(
            "PROCESS_OUTPUT_REGENERATION_FAILED",
            result.document.session.warnings[-1].code,
        )
        self.assertEqual(
            ArtifactStatus.STALE,
            result.document.session.artifacts["capture-cap-001-profile_image"].status,
        )

    def test_solver_unavailable_path_preserves_warning_only_behavior(self) -> None:
        session = profile_session_without_recipe()

        result = regenerate_process_outputs(
            session,
            RegenerateProcessOutputsCommand("cap-001", solver_available=False),
        )

        self.assertEqual("warning", result.status)
        self.assertEqual("SOLVER_BACKEND_UNAVAILABLE", result.warnings[0].code)
        self.assertEqual("pending_solver", result.session.process_outputs[0].status)
        self.assertEqual(
            ArtifactStatus.PLACEHOLDER,
            result.session.artifacts["capture-cap-001-profile_image"].status,
        )

    def test_custom_process_extension_is_a_regeneration_target(self) -> None:
        result = regenerate_process_outputs(
            custom_process_capture_session(),
            RegenerateProcessOutputsCommand("cap-001"),
        )

        self.assertEqual("warning", result.status)
        self.assertEqual("PROCESS_RECIPE_MISSING", result.warnings[0].code)
        self.assertNotEqual("No process output target.", result.message)

class FailingProcessOutputStore(ProcessOutputStore):
    def export_ready_outputs(self, paths, session, owner_id=""):
        raise OSError("disk full")


if __name__ == "__main__":
    unittest.main()

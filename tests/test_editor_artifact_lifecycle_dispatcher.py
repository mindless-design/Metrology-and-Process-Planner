import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.session import (
    ArtifactRepairMetadata,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.artifact_lifecycle_fixtures import artifact, session


class EditorArtifactLifecycleDispatcherTests(unittest.TestCase):
    def test_direct_scan_artifacts_updates_document(self) -> None:
        crop = replace(artifact("crop"), status=ArtifactStatus.PRESENT)
        document = SessionDocumentBuilder().build(session(artifacts={"crop": crop}))

        with TemporaryDirectory() as temp_dir:
            dispatcher = EditorActionDispatcher(paths=SessionPaths.for_folder(Path(temp_dir)))

            result = dispatcher.dispatch(
                document,
                EditorAction(EditorActionType.SCAN_ARTIFACTS, "Scan Artifacts"),
            )

        self.assertEqual("success", result.status)
        self.assertIn("Scanned 1 artifacts", result.message)
        self.assertEqual(ArtifactStatus.MISSING, result.document.session.artifacts["crop"].status)

    def test_direct_bulk_missing_repair_is_structured(self) -> None:
        crop = replace(artifact("crop"), status=ArtifactStatus.PRESENT)
        document = SessionDocumentBuilder().build(session(artifacts={"crop": crop}))

        with TemporaryDirectory() as temp_dir:
            dispatcher = EditorActionDispatcher(paths=SessionPaths.for_folder(Path(temp_dir)))

            result = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_MISSING_ARTIFACTS,
                    "Regenerate Missing",
                ),
            )

        self.assertEqual("success", result.status)
        self.assertIn("1 candidate(s)", result.message)
        self.assertIn(
            "SOURCE_LAYOUT_REQUIRED_FOR_REPAIR",
            {warning.code for warning in result.document.session.warnings},
        )

    def test_direct_bulk_missing_repair_skips_hidden_process_artifacts(self) -> None:
        visible = replace(artifact("crop"), status=ArtifactStatus.PRESENT)
        hidden = replace(
            artifact("legacy-process", "process_outputs/legacy.json"),
            type="process_output",
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                regenerable=True,
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        document = SessionDocumentBuilder().build(
            session(artifacts={"crop": visible, "legacy-process": hidden})
        )

        with TemporaryDirectory() as temp_dir:
            dispatcher = EditorActionDispatcher(paths=SessionPaths.for_folder(Path(temp_dir)))

            result = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_MISSING_ARTIFACTS,
                    "Regenerate Missing",
                ),
            )

        repaired = result.document.session.artifacts

        self.assertEqual("success", result.status)
        self.assertIn("1 candidate(s)", result.message)
        self.assertEqual(ArtifactStatus.MISSING, repaired["legacy-process"].status)
        self.assertEqual((), repaired["legacy-process"].warning_ids)
        self.assertNotIn(
            "RECIPE_REQUIRED_FOR_REPAIR",
            {warning.code for warning in result.document.session.warnings},
        )
        self.assertNotIn(
            "SOLVER_REQUIRED_FOR_REPAIR",
            {warning.code for warning in result.document.session.warnings},
        )

    def test_direct_manifest_export_uses_recipe_free_visibility(self) -> None:
        visible = replace(artifact("crop"), status=ArtifactStatus.PRESENT)
        hidden = replace(
            artifact("legacy-process", "process_outputs/legacy.json"),
            type="process_output",
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                regenerable=True,
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        document = SessionDocumentBuilder().build(
            session(artifacts={"crop": visible, "legacy-process": hidden})
        )

        with TemporaryDirectory() as temp_dir:
            dispatcher = EditorActionDispatcher(paths=SessionPaths.for_folder(Path(temp_dir)))

            result = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.EXPORT_ARTIFACT_MANIFEST,
                    "Export Artifact Manifest",
                ),
            )
            assert result.output_path is not None
            payload = json.loads(result.output_path.read_text(encoding="utf-8"))

        self.assertEqual("success", result.status)
        self.assertEqual(["crop"], sorted(payload))

    def test_direct_artifact_lifecycle_actions_without_paths_are_unavailable(self) -> None:
        document = SessionDocumentBuilder().build(session())

        for action_type in (
            EditorActionType.SCAN_ARTIFACTS,
            EditorActionType.REGENERATE_MISSING_ARTIFACTS,
            EditorActionType.REGENERATE_STALE_ARTIFACTS,
            EditorActionType.EXPORT_ARTIFACT_MANIFEST,
        ):
            with self.subTest(action=action_type.value):
                result = EditorActionDispatcher().dispatch(
                    document,
                    EditorAction(action_type, action_type.value),
                )

                self.assertEqual("unavailable", result.status)
                self.assertIn("No session folder", result.message)


if __name__ == "__main__":
    unittest.main()

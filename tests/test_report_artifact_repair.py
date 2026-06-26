import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.artifacts.requests import (
    RepairRequestStatus,
    RepairType,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.report_artifact_repair_fixtures import (
    generated_report_session as _generated_report_session,
)
from tests.report_artifact_repair_fixtures import (
    pptx_artifact as _pptx_artifact,
)

if __name__ == "__main__":
    unittest.main()


class ReportArtifactRepairTestsPart1(unittest.TestCase):
    def test_generated_report_artifacts_have_available_repair_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths)
            artifact = _pptx_artifact(report_session)
            source = replace(
                report_session,
                artifacts={
                    **dict(report_session.artifacts),
                    artifact.id: replace(artifact, status=ArtifactStatus.STALE),
                },
            )

            request = next(
                item
                for item in ArtifactRepairService().build_repair_requests(source)
                if item.artifact_id == artifact.id
            )

        self.assertEqual(RepairType.REBUILD_REPORT, request.repair_type)
        self.assertEqual(RepairRequestStatus.AVAILABLE, request.status)

    def test_powerpoint_report_repair_rebuilds_missing_deck(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths)
            artifact = _pptx_artifact(report_session)
            artifact_path_to_disk(paths.folder, artifact.relative_path).unlink()
            missing = replace(artifact, status=ArtifactStatus.MISSING)
            source = replace(
                report_session,
                artifacts={**dict(report_session.artifacts), artifact.id: missing},
            )

            repaired = ArtifactRepairService().repair_artifact(source, artifact.id, paths)
            repaired_artifact = repaired.artifacts[artifact.id]
            output_exists = artifact_path_to_disk(
                paths.folder,
                repaired_artifact.relative_path,
            ).exists()

        self.assertEqual(ArtifactStatus.PRESENT, repaired_artifact.status)
        self.assertTrue(output_exists)
        self.assertEqual(artifact.id, repaired.reports[0].artifact_refs["powerpoint_deck"])

    def test_report_item_exposes_artifact_repair_actions_in_editor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths)
            artifact = _pptx_artifact(report_session)
            source = replace(
                report_session,
                artifacts={
                    **dict(report_session.artifacts),
                    artifact.id: replace(artifact, status=ArtifactStatus.STALE),
                },
            )

            document = SessionDocumentBuilder().build(source)
            item = document.items_by_id[f"report:{source.reports[0].id}"]
            adapter = DefaultSessionModeAdapter()
            actions = adapter.actions(source, item)
            fields = adapter.metadata_fields(source, item)
            previews = adapter.preview_options(source, item)

        repair_actions = [
            action
            for action in actions
            if action.action_type is EditorActionType.REGENERATE_ARTIFACT
        ]
        relink_actions = [
            action
            for action in actions
            if action.action_type is EditorActionType.RELINK_ARTIFACT
        ]
        repair_payloads = [dict(action.payload) for action in repair_actions]
        field_values = {field.key: field.value for field in fields}

        self.assertIn({"artifact_id": artifact.id}, repair_payloads)
        self.assertTrue(relink_actions)
        self.assertIn(artifact.id, tuple(ref.artifact_id for ref in item.artifact_refs))
        self.assertEqual(source.reports[0].label, field_values["label"])
        self.assertEqual(source.reports[0].report_type, field_values["report_type"])
        self.assertEqual("ready", field_values["status"])
        self.assertEqual(str(len(source.reports[0].artifact_refs)), field_values["artifact_count"])
        self.assertIn("PowerPoint Deck", tuple(preview.label for preview in previews))
        self.assertIn("Report Manifest", tuple(preview.label for preview in previews))
        self.assertTrue(any(preview.status == "stale" for preview in previews))

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.reporting import ReportGenerationService, ReportRequest
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.artifacts.generators import built_in_generator_registry
from metrology_process_planner.workflows.artifacts.requests import (
    RepairRequestStatus,
    RepairType,
)
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.reporting_workbench_fixtures import document_with_artifact


def _generated_report_session(paths: SessionPaths, output_formats=("pptx",)):
    document = document_with_artifact(ArtifactStatus.PRESENT)
    result = ReportGenerationService().generate(
        document,
        ReportRequest(document.session.id, "metrology_report", output_formats=output_formats),
        paths.folder,
    )
    assert result.updated_session is not None
    return result.updated_session

def _pptx_artifact(session):
    return _artifact_by_type(session, "powerpoint_deck")

def _artifact_by_type(session, artifact_type):
    return next(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact.type == artifact_type
    )

if __name__ == "__main__":
    unittest.main()


class ReportArtifactRepairTestsPart2(unittest.TestCase):
    def test_report_regenerate_action_routes_through_repair_service(self) -> None:
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
            document = SessionDocumentBuilder().build(source)
            report_item_id = f"report:{source.reports[0].id}"

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_ARTIFACT,
                    "Regenerate Report",
                    report_item_id,
                    payload=(("artifact_id", artifact.id),),
                ),
            )

            repaired = result.document.session.artifacts[artifact.id]
            output_exists = artifact_path_to_disk(paths.folder, repaired.relative_path).exists()

        self.assertEqual("success", result.status)
        self.assertEqual("Regenerated report artifact.", result.message)
        self.assertEqual(ArtifactStatus.PRESENT, repaired.status)
        self.assertTrue(output_exists)

    def test_report_owned_csv_uses_report_repair_generator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths, output_formats=("csv",))
            artifact = _artifact_by_type(report_session, "csv_export")
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
            registration = built_in_generator_registry().generator_for(artifact)

        self.assertEqual("report", artifact.owner.owner_type)
        self.assertEqual("report_export", artifact.generator)
        self.assertEqual(RepairType.REBUILD_REPORT, request.repair_type)
        self.assertEqual(RepairRequestStatus.AVAILABLE, request.status)
        self.assertIsNotNone(registration)
        self.assertEqual("report_export", registration.generator_id)

    def test_report_owned_csv_repair_rebuilds_report_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths, output_formats=("csv",))
            artifact = _artifact_by_type(report_session, "csv_export")
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
        self.assertEqual("report", repaired_artifact.owner.owner_type)
        self.assertEqual("report_output", repaired_artifact.owner.role)
        self.assertTrue(output_exists)

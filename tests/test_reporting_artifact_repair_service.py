import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.reporting_artifact_repair import (
    ReportingWorkbenchArtifactRepairService,
)
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import (
    ArtifactGeneratorRegistry,
    ArtifactRepairService,
    GeneratorRegistration,
)
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending


class ReportingArtifactRepairServiceTests(unittest.TestCase):
    def test_regenerate_stale_uses_central_artifact_repair_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            artifact = _stale_report_artifact(paths)
            document = SessionDocumentBuilder().build(
                replace(session_without_pending(), artifacts={artifact.id: artifact})
            )
            service = ReportingWorkbenchArtifactRepairService(
                ArtifactRepairService(generators=_report_generator_registry())
            )

            repaired = service.regenerate_stale(document, paths)

        self.assertEqual(ArtifactStatus.PRESENT, repaired.session.artifacts[artifact.id].status)

    def test_regenerate_missing_uses_central_artifact_repair_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            artifact = replace(_stale_report_artifact(paths), status=ArtifactStatus.MISSING)
            document = SessionDocumentBuilder().build(
                replace(session_without_pending(), artifacts={artifact.id: artifact})
            )
            service = ReportingWorkbenchArtifactRepairService(
                ArtifactRepairService(generators=_report_generator_registry())
            )

            repaired = service.regenerate_missing(document, paths)

        self.assertEqual(ArtifactStatus.PRESENT, repaired.session.artifacts[artifact.id].status)


def _stale_report_artifact(paths: SessionPaths) -> ArtifactRecord:
    relative_path = "reports/report.pptx"
    destination = paths.folder / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("old report", encoding="utf-8")
    return ArtifactRecord(
        "report-001-pptx",
        "powerpoint_deck",
        "Report PPTX",
        relative_path,
        ArtifactOwnerRef("report", "report-001", "report_output"),
        status=ArtifactStatus.STALE,
        generator="test_report_generator",
        repair=ArtifactRepairMetadata(regenerable=True),
    )


def _report_generator_registry() -> ArtifactGeneratorRegistry:
    return ArtifactGeneratorRegistry(
        (
            GeneratorRegistration(
                "test_report_generator",
                ("powerpoint_deck",),
                handler=lambda _session, artifact, _paths: replace(
                    artifact,
                    status=ArtifactStatus.PRESENT,
                ),
            ),
        )
    )


if __name__ == "__main__":
    unittest.main()

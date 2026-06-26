import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus, SessionMode
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.reporting import ReportGenerationService, ReportRequest
from metrology_process_planner.workflows.artifacts import ArtifactRepairService, ArtifactScanner
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.report_artifact_repair_fixtures import (
    pptx_artifact,
    process_artifact,
    process_warning,
    recipe_free_profilometry_registry,
)
from tests.reporting_workbench_fixtures import document_with_artifact


class ReportArtifactRepairTestsPart3(unittest.TestCase):
    def test_report_artifact_signature_uses_loaded_recipe_free_registry(self) -> None:
        registry = recipe_free_profilometry_registry()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            result = _generate_loaded_recipe_free_report(paths, registry)
            artifact = pptx_artifact(result.updated_session)
            changed = replace(
                result.updated_session,
                artifacts={
                    **dict(result.updated_session.artifacts or {}),
                    "legacy-process-output": process_artifact(),
                },
                warnings=(process_warning(),),
            )

            scanned, _scan_result = ArtifactScanner().scan_session(changed, paths, registry)

        self.assertEqual(ArtifactStatus.PRESENT, scanned.artifacts[artifact.id].status)
        self.assertEqual((), scanned.artifacts[artifact.id].warning_ids)

    def test_report_artifact_repair_uses_loaded_recipe_free_registry(self) -> None:
        registry = recipe_free_profilometry_registry()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            result = _generate_loaded_recipe_free_report(paths, registry)
            artifact = pptx_artifact(result.updated_session)
            source = replace(
                result.updated_session,
                artifacts={
                    **dict(result.updated_session.artifacts or {}),
                    artifact.id: replace(artifact, status=ArtifactStatus.STALE),
                    "legacy-process-output": process_artifact(),
                },
                warnings=(process_warning(),),
            )

            repaired = ArtifactRepairService().repair_artifact(
                source,
                artifact.id,
                paths,
                registry,
            )
            scanned, _scan_result = ArtifactScanner().scan_session(repaired, paths, registry)

        self.assertEqual(ArtifactStatus.PRESENT, scanned.artifacts[artifact.id].status)
        self.assertEqual((), scanned.artifacts[artifact.id].warning_ids)


def _generate_loaded_recipe_free_report(paths, registry):
    document = document_with_artifact(ArtifactStatus.PRESENT)
    document = SessionDocumentBuilder(mode_registry=registry).build(
        replace(document.session, mode=SessionMode.PROFILOMETRY_PLANNER)
    )
    result = ReportGenerationService(mode_registry=registry).generate(
        document,
        ReportRequest(document.session.id, "engineering_review"),
        paths.folder,
    )
    assert result.updated_session is not None
    return result


if __name__ == "__main__":
    unittest.main()

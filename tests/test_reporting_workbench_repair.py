import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.reporting_artifact_repair import (
    ReportingWorkbenchArtifactRepairService,
)
from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending


class ReportingWorkbenchRepairTests(unittest.TestCase):
    def test_bootstrap_attaches_default_repair_service(self) -> None:
        services = build_app_services()

        self.assertIsNotNone(
            services.reporting_workbench_controller.artifact_repair_service
        )

    def test_regenerate_missing_uses_injected_repair_service(self) -> None:
        controller = ReportingWorkbenchController(artifact_repair_service=_FakeRepairService())
        document = _document_with_artifact(ArtifactStatus.MISSING)
        with tempfile.TemporaryDirectory() as temp_dir:
            controller.open_document(document, SessionPaths.for_folder(Path(temp_dir)))

            result = controller.dispatch("regenerate_missing")

            self.assertEqual("success", result.status)
            artifact = controller.current_document.session.artifacts["missing-image"]
            self.assertEqual(ArtifactStatus.PRESENT, artifact.status)

    def test_regenerate_stale_uses_injected_repair_service(self) -> None:
        service = _FakeRepairService()
        controller = ReportingWorkbenchController(artifact_repair_service=service)
        document = _document_with_artifact(ArtifactStatus.STALE)
        with tempfile.TemporaryDirectory() as temp_dir:
            controller.open_document(document, SessionPaths.for_folder(Path(temp_dir)))

            result = controller.dispatch("regenerate_stale")

            self.assertEqual("success", result.status)
            self.assertEqual("stale", service.last_method)
            artifact = controller.current_document.session.artifacts["missing-image"]
            self.assertEqual(ArtifactStatus.PRESENT, artifact.status)

    def test_default_repair_service_uses_loaded_recipe_free_registry(self) -> None:
        registry = ModeRegistry(
            (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
        )
        artifact = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Stack Image",
            "process_outputs/legacy-stack.png",
            ArtifactOwnerRef("process_output", "legacy-output", "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                regenerable=True,
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        session = replace(
            session_without_pending(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            artifacts={artifact.id: artifact},
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(session)
        service = ReportingWorkbenchArtifactRepairService(mode_registry=registry)

        with tempfile.TemporaryDirectory() as temp_dir:
            repaired = service.regenerate_missing(
                document,
                SessionPaths.for_folder(Path(temp_dir)),
            )

        self.assertEqual(
            ArtifactStatus.MISSING,
            repaired.session.artifacts["legacy-process-output"].status,
        )
        self.assertEqual((), repaired.session.artifacts["legacy-process-output"].warning_ids)
        self.assertEqual((), repaired.session.warnings)


def _document_with_artifact(status: ArtifactStatus):
    document = SessionDocumentBuilder().build(session_without_pending())
    artifact = ArtifactRecord(
        "missing-image",
        "image",
        "Missing Image",
        "images/missing.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=status,
    )
    session = replace(document.session, artifacts={artifact.id: artifact})
    return SessionDocumentBuilder().build(session)


class _FakeRepairService:
    def __init__(self) -> None:
        self.last_method = ""

    def regenerate_missing(self, document, _paths):
        self.last_method = "missing"
        return self._regenerate(document)

    def regenerate_stale(self, document, _paths):
        self.last_method = "stale"
        return self._regenerate(document)

    def _regenerate(self, document):
        artifact = replace(
            document.session.artifacts["missing-image"],
            status=ArtifactStatus.PRESENT,
        )
        session = replace(document.session, artifacts={"missing-image": artifact})
        return SessionDocumentBuilder().build(session)


if __name__ == "__main__":
    unittest.main()

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionModeId,
)
from metrology_process_planner.persistence.paths import SessionPaths
from tests.editor_render_fixtures import session_without_pending


class DiagnosticsArtifactRepairTests(unittest.TestCase):
    def test_repair_queue_hides_process_artifacts_for_recipe_free_modes(self) -> None:
        services = build_app_services()
        source = session_without_pending()
        artifact_id, artifact = next(iter(source.artifacts.items()))
        source = replace(
            source,
            artifacts={
                artifact_id: replace(
                    artifact,
                    type="process_output",
                    status=ArtifactStatus.MISSING,
                    repair=ArtifactRepairMetadata(
                        repair_action="regenerate_process_output",
                        regenerable=True,
                        requires_recipe=True,
                    ),
                )
            },
        )
        services.diagnostics_controller.set_active_session(source)

        result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual("0 total", summary["Artifacts"])
        self.assertEqual("0", summary["Missing Artifacts"])
        self.assertEqual("0 candidate(s)", summary["Artifact Repair Queue"])
        self.assertEqual("idle", summary["Artifact Repair"])

        validation = result.window["on_action"]("ValidateArtifactRegistry")
        self.assertEqual("success", validation.status)
        self.assertIn("artifacts=0", validation.output_text)
        self.assertIn("missing=0", validation.output_text)
        self.assertIn("repair_requests=0", validation.output_text)

    def test_scan_actions_use_loaded_recipe_free_registry(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        services = build_app_services(mode_registry=registry)
        hidden_process = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Process Output",
            "process_outputs/legacy-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            status=ArtifactStatus.PRESENT,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            artifacts={hidden_process.id: hidden_process},
        )
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.diagnostics_controller.set_active_session(source, paths)

            scan = services.diagnostics_controller.route_action("ScanArtifacts")
            health = services.diagnostics_controller.route_action("ExportArtifactHealthReport")

            health_text = Path(health.output_path).read_text(encoding="utf-8")

        self.assertEqual("success", scan.status)
        self.assertIn("0 missing", scan.message)
        self.assertIn("artifact_count=0", scan.output_text)
        self.assertEqual("success", health.status)
        self.assertIn("artifact_count=0", health_text)
        self.assertIn("missing=0", health_text)


if __name__ == "__main__":
    unittest.main()

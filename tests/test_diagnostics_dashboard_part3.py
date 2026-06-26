import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    ReportRecord,
    SessionModeId,
)
from tests.editor_render_fixtures import session_without_pending

if __name__ == "__main__":
    unittest.main()


class DiagnosticsDashboardTestsPart3(unittest.TestCase):
    def test_report_readiness_uses_loaded_recipe_free_registry(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        services = build_app_services(mode_registry=registry)
        hidden_process = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Process Output",
            "process_outputs/legacy-stack.png",
            ArtifactOwnerRef("report", "report-001", "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            reports=(
                ReportRecord(
                    "report-001",
                    "Summary",
                    "capture_catalog",
                    artifact_refs={"stack_image": hidden_process.id},
                ),
            ),
            artifacts={hidden_process.id: hidden_process},
        )
        services.diagnostics_controller.set_active_session(source)

        result = services.diagnostics_controller.open_current()
        rows = dict(result.summary_rows)

        self.assertEqual("0/1 reports have artifacts", rows["Report Readiness"])

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
    SessionModeId,
    WarningRecord,
)
from tests.editor_render_fixtures import session_without_pending

if __name__ == "__main__":
    unittest.main()


class DiagnosticsDashboardTestsPart2(unittest.TestCase):
    def test_dashboard_uses_loaded_registry_for_recipe_free_warning_and_artifact_counts(
        self,
    ) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        services = build_app_services(mode_registry=registry)
        services.diagnostics_controller.set_active_session(_external_warning_session())

        result = services.diagnostics_controller.open_current()
        rows = dict(result.summary_rows)

        self.assertEqual(1, result.warning_count)
        self.assertEqual(1, result.missing_artifact_count)
        self.assertEqual("1", rows["Warnings"])
        self.assertEqual("ARTIFACT_MISSING", rows["Warning Codes"])
        self.assertEqual("1", rows["Missing Artifacts"])
        self.assertEqual("1 total; missing=1", rows["Artifacts"])
        self.assertEqual("1 candidate(s)", rows["Artifact Repair Queue"])

    def test_artifact_registry_validation_uses_loaded_recipe_free_registry(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        services = build_app_services(mode_registry=registry)
        hidden_process = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Process Output",
            "process_outputs/legacy-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
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
            artifacts={hidden_process.id: hidden_process},
        )
        services.diagnostics_controller.set_active_session(source)

        result = services.diagnostics_controller.route_action("ValidateArtifactRegistry")

        self.assertEqual("success", result.status)
        self.assertIn("artifacts=0", result.output_text)
        self.assertIn("missing=0", result.output_text)
        self.assertIn("repair_requests=0", result.output_text)


def _external_warning_session():
    visible = ArtifactRecord(
        "capture-missing",
        "capture_image",
        "Capture Missing",
        "captures/missing.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=ArtifactStatus.MISSING,
    )
    hidden_process = ArtifactRecord(
        "legacy-process-output",
        "process_output",
        "Legacy Process Output",
        "process_outputs/legacy-stack.png",
        ArtifactOwnerRef("capture", "cap-001", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            requires_recipe=True,
            requires_solver=True,
        ),
    )
    return replace(
        session_without_pending(),
        mode=SessionModeId("external_mode"),
        artifacts={visible.id: visible, hidden_process.id: hidden_process},
        warnings=_external_warnings(visible.id),
    )


def _external_warnings(visible_id: str) -> tuple[WarningRecord, ...]:
    return (
        WarningRecord(
            "visible-artifact-warning",
            "Capture artifact missing.",
            source="artifact",
            code="ARTIFACT_MISSING",
            related_artifact_refs=(visible_id,),
        ),
        WarningRecord(
            "hidden-process-warning",
            "Recipe missing.",
            source="process_context",
            code="PROCESS_RECIPE_MISSING",
        ),
    )

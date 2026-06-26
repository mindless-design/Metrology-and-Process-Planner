import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.diagnostics import (
    DiagnosticsService,
    InMemoryDiagnosticSink,
)
from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    ProcessContext,
    SessionModeId,
    WarningRecord,
)
from tests.editor_render_fixtures import session_without_pending

if __name__ == "__main__":
    unittest.main()


class DiagnosticsVisibilityTestsPart2(unittest.TestCase):
    def test_summary_hides_process_warnings_for_recipe_free_modes(self) -> None:
        services = build_app_services()
        source = replace(
            session_without_pending(),
            warnings=(
                WarningRecord(
                    id="process-warning",
                    message="Recipe file not found.",
                    source="process_context",
                    code="PROCESS_RECIPE_FILE_NOT_FOUND",
                ),
                WarningRecord(
                    id="artifact-warning",
                    message="Capture image is missing.",
                    source="artifacts",
                    code="ARTIFACT_MISSING",
                ),
            ),
        )
        services.diagnostics_controller.set_active_session(source)

        result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual(1, result.warning_count)
        self.assertEqual("1", summary["Warnings"])
        self.assertEqual("ARTIFACT_MISSING", summary["Warning Codes"])

    def test_mode_policy_rows_ignore_stale_recipe_context_for_recipe_free_modes(self) -> None:
        services = build_app_services()
        source = replace(
            session_without_pending(),
            process_context=ProcessContext(
                recipe_id="legacy-recipe",
                solver_backend="legacy_solver",
                render_profile="legacy_stack_profile",
            ),
        )
        services.diagnostics_controller.set_active_session(source)

        result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual("false", summary["Mode Process Aware"])
        self.assertEqual("false", summary["Recipe Required"])
        self.assertEqual("none", summary["Solver Operation"])
        self.assertEqual("false", summary["Process Context Visible"])
        self.assertEqual("none", summary["Solver Backend"])
        self.assertEqual("none", summary["Renderer Backend"])

    def test_mode_policy_rows_use_injected_registry_for_external_recipe_free_modes(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_capture", "External Capture"),))
        sink = InMemoryDiagnosticSink()
        controller = AdvancedDiagnosticsController(
            sink,
            DiagnosticsService(sink),
            mode_registry=registry,
        )
        controller.set_active_session(
            replace(
                session_without_pending(),
                mode=SessionModeId("external_capture"),
                process_context=ProcessContext(recipe_id="legacy-recipe"),
            )
        )

        result = controller.open_current()

        summary = dict(result.window["summary"])
        self.assertIn("external_capture", summary["Loaded Mode Definition"])
        self.assertEqual("false", summary["Mode Process Aware"])
        self.assertEqual("false", summary["Recipe Required"])
        self.assertEqual("none", summary["Solver Operation"])
        self.assertEqual("false", summary["Process Context Visible"])

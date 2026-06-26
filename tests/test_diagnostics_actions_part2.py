import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionModeId,
    WarningRecord,
)
from tests.editor_render_fixtures import session_without_pending


def _session_with_warning_artifact():
    source = session_without_pending()
    artifact_id, artifact = next(iter(source.artifacts.items()))
    return replace(
        source,
        artifacts={artifact_id: replace(artifact, status=ArtifactStatus.MISSING)},
        warnings=(
            WarningRecord(
                "artifact-missing",
                "Missing crop",
                code="artifact_missing",
                related_artifact_refs=(artifact_id,),
            ),
        ),
    )


class DiagnosticsActionTestsPart2(unittest.TestCase):
    def test_diagnostics_validation_actions_return_structured_warnings(self) -> None:
        services = build_app_services()
        source = _session_with_warning_artifact()
        services.diagnostics_controller.set_active_session(source)
        result = services.diagnostics_controller.open_current()

        session_result = result.window["on_action"]("ValidateSession")
        mode_result = result.window["on_action"]("ValidateModes")

        self.assertEqual("warning", session_result.status)
        self.assertIn("persisted warning", session_result.message)
        self.assertEqual("success", mode_result.status)
        self.assertIn("Mode validation: ok.", mode_result.message)

    def test_validate_session_hides_process_warnings_for_recipe_free_modes(self) -> None:
        services = build_app_services()
        source = replace(
            session_without_pending(),
            warnings=(
                WarningRecord(
                    "process-warning",
                    "Recipe missing",
                    source="process_context",
                    code="PROCESS_RECIPE_FILE_NOT_FOUND",
                ),
            ),
        )
        services.diagnostics_controller.set_active_session(source)
        result = services.diagnostics_controller.open_current()

        session_result = result.window["on_action"]("ValidateSession")

        self.assertEqual("success", session_result.status)
        self.assertEqual("Session validation passed.", session_result.message)

    def test_validate_session_uses_loaded_recipe_free_warning_visibility(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        services = build_app_services(mode_registry=registry)
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            warnings=(
                WarningRecord(
                    "process-warning",
                    "Recipe missing",
                    source="process_context",
                    code="PROCESS_RECIPE_FILE_NOT_FOUND",
                ),
            ),
        )
        services.diagnostics_controller.set_active_session(source)
        result = services.diagnostics_controller.open_current()

        session_result = result.window["on_action"]("ValidateSession")

        self.assertEqual("success", session_result.status)
        self.assertEqual("Session validation passed.", session_result.message)

    def test_diagnostics_action_failure_is_recorded(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            blocked = Path(temp_dir) / "not-a-folder"
            blocked.write_text("blocked", encoding="utf-8")
            services.diagnostics_controller.set_active_session(session_without_pending())
            result = services.diagnostics_controller.open_current()

            failed = result.window["on_action"](f"ExportDiagnosticsBundle:{blocked}")

        self.assertEqual("error", failed.status)
        self.assertTrue(
            any(
                event.event_name == "DiagnosticsActionFailed"
                for event in services.diagnostics_sink.recent(10)
            )
        )

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
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


class DiagnosticsActionTestsPart1(unittest.TestCase):
    def test_diagnostics_actions_include_disabled_reasons(self) -> None:
        services = build_app_services()
        services.diagnostics_controller.set_active_session(session_without_pending())

        result = services.diagnostics_controller.open_current()
        actions = {action.action_id: action for action in result.window["actions"]}

        self.assertEqual(
            (
                "ExportDiagnosticsBundle",
                "CopyCommandTrace",
                "OpenSessionFolder",
                "ScanArtifacts",
                "ExportArtifactHealthReport",
                "CopyRepairQueue",
                "ValidateArtifactRegistry",
                "ValidateSession",
                "ValidateModes",
            ),
            tuple(actions),
        )
        self.assertFalse(actions["CopyCommandTrace"].enabled)
        self.assertEqual(
            "No command or diagnostic events are available yet.",
            actions["CopyCommandTrace"].disabled_reason,
        )
        self.assertFalse(actions["OpenSessionFolder"].enabled)
        self.assertEqual(
            "No session folder is associated with diagnostics.",
            actions["OpenSessionFolder"].disabled_reason,
        )

    def test_diagnostics_actions_enable_trace_and_folder_handoffs(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.diagnostics_controller.set_active_session(session_without_pending(), paths)
            services.command_router.route(CommandId.OPEN_SETUP_GUIDE)

            result = services.diagnostics_controller.open_current()

        actions = {action.action_id: action for action in result.window["actions"]}
        self.assertTrue(actions["CopyCommandTrace"].enabled)
        self.assertTrue(actions["OpenSessionFolder"].enabled)
        self.assertTrue(actions["ScanArtifacts"].enabled)

    def test_diagnostics_action_callback_prepares_trace_and_folder_handoff(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.diagnostics_controller.set_active_session(session_without_pending(), paths)
            services.command_router.route(CommandId.OPEN_SETUP_GUIDE)
            result = services.diagnostics_controller.open_current()

            trace = result.window["on_action"]("CopyCommandTrace")
            folder = result.window["on_action"]("OpenSessionFolder")

        self.assertEqual("success", trace.status)
        self.assertIn("open_setup_guide", trace.output_text)
        self.assertEqual("success", folder.status)
        self.assertTrue(folder.output_path.endswith(temp_dir))

    def test_diagnostics_action_callback_exports_bundle(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir) / "session")
            services.diagnostics_controller.set_active_session(session_without_pending(), paths)
            result = services.diagnostics_controller.open_current()

            exported = result.window["on_action"]("ExportDiagnosticsBundle")

            bundle = Path(exported.output_path)
            self.assertTrue((bundle / "session.json").exists())
            self.assertTrue((bundle / "diagnostics" / "events.jsonl").exists())
        self.assertEqual("success", exported.status)

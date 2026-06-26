import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
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
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.artifact_helpers import capture_crop_artifact
from tests.editor_render_fixtures import session_without_pending


class SessionEditorExportCommandTests(unittest.TestCase):
    def test_export_csv_primary_action_routes_through_command_router(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            result = services.session_editor_controller.open_document(
                _document(),
                paths,
            )

            action = _primary_action(result.window, EditorActionType.EXPORT_CSV)
            result.window["on_primary_action"](action)

            routed = services.session_editor_controller.last_command_result
            self.assertIsNotNone(routed)
            self.assertEqual(CommandId.EXPORT_CSV, routed.command_id)
            self.assertEqual("success", routed.status)
            self.assertEqual(str(paths.capture_csv), routed.output_path)

    def test_open_output_folder_command_returns_path_handoff(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.session_editor_controller.open_document(_document(), paths)

            routed = services.command_router.route(CommandId.OPEN_OUTPUT_FOLDER)

        self.assertEqual("success", routed.status)
        self.assertEqual(str(paths.folder), routed.output_path)

    def test_open_output_folder_without_document_is_unavailable(self) -> None:
        services = build_app_services()

        routed = services.command_router.route(CommandId.OPEN_OUTPUT_FOLDER)

        self.assertEqual("unavailable", routed.status)
        self.assertIn("No active session editor document", routed.message)

    def test_export_csv_command_uses_loaded_recipe_free_registry(self) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        services = build_app_services(mode_registry=registry)
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = SessionDocumentBuilder(mode_registry=registry).build(
                replace(
                    session_without_pending(),
                    mode=SessionMode.PROFILOMETRY_PLANNER,
                    artifacts=_artifacts_with_hidden_process_output(),
                )
            )
            result = services.session_editor_controller.open_document(document, paths)

            action = _primary_action(result.window, EditorActionType.EXPORT_CSV)
            result.window["on_primary_action"](action)

            routed = services.session_editor_controller.last_command_result
            exported = services.session_editor_controller.current_document
            self.assertIsNotNone(routed)
            self.assertIsNotNone(exported)
            self.assertEqual(CommandId.EXPORT_CSV, routed.command_id)
            self.assertEqual("success", routed.status)
            csv_text = paths.capture_csv.read_text(encoding="utf-8")
            fields = _dashboard_fields(exported)

            self.assertIn("crop:present", csv_text)
            self.assertNotIn("stack_image:missing", csv_text)
            self.assertNotIn("process_outputs/cap-001-stack.png", csv_text)
            self.assertEqual("0", fields["missing_artifact_count"])
            self.assertEqual("ready", fields["csv_readiness"])
            self.assertEqual("ready", fields["report_readiness"])


def _document():
    return SessionDocumentBuilder().build(session_without_pending())


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)


def _dashboard_fields(document) -> dict[str, str]:
    adapter = DefaultSessionModeAdapter(_recipe_free_registry_for(document.session.mode.value))
    return {
        field.key: field.value
        for field in adapter.metadata_fields(document.session, document.items_by_id["dashboard"])
    }


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))


def _artifacts_with_hidden_process_output() -> dict[str, ArtifactRecord]:
    visible = capture_crop_artifact()
    hidden = ArtifactRecord(
        "legacy-capture-process-output",
        "process_output",
        "Legacy Capture Stack",
        "process_outputs/cap-001-stack.png",
        ArtifactOwnerRef("capture", "cap-001", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            requires_recipe=True,
            requires_solver=True,
        ),
    )
    return {visible.id: visible, hidden.id: hidden}


if __name__ == "__main__":
    unittest.main()

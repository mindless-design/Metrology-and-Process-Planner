import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import (
    CanvasVisualFlag,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.editor_render_fixtures import empty_session
from tests.measurement_child_fixtures import saved_measurement_document


class SessionEditorCompletionCommandTests(unittest.TestCase):
    def test_take_another_measurement_rearms_active_capture_from_command(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = saved_measurement_document(paths)
            services.session_editor_controller.open_document(document)

            result = services.command_router.route(CommandId.TAKE_ANOTHER_MEASUREMENT)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", result.status)
        self.assertEqual("capture:cap-001", result.selected_item_id)
        self.assertIsNotNone(current)
        self.assertTrue(current.session.workflow.active)
        self.assertEqual("measurement", current.session.workflow.active_primitive)
        self.assertIn(
            CanvasVisualFlag.ACTIVE_PARENT,
            current.session.canvas_objects[0].visual_state,
        )

    def test_take_another_measurement_without_saved_measurement_is_unavailable(self) -> None:
        services = build_app_services()
        services.session_editor_controller.open_document(
            SessionDocumentBuilder().build(empty_session())
        )

        result = services.command_router.route(CommandId.TAKE_ANOTHER_MEASUREMENT)

        self.assertEqual("unavailable", result.status)
        self.assertIn("No saved measurement", result.message)

    def test_take_another_measurement_preserves_loaded_recipe_free_registry(self) -> None:
        registry = ModeRegistry(
            (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
        )
        services = build_app_services(mode_registry=registry)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = saved_measurement_document(paths)
            session = replace(
                document.session,
                mode=SessionMode.PROFILOMETRY_PLANNER,
                warnings=(
                    WarningRecord(
                        "process-warning",
                        "Recipe attached but hidden",
                        source="process_context",
                        code="PROCESS_CONTEXT_ATTACHED",
                    ),
                ),
            )
            services.session_editor_controller.open_document(
                SessionDocumentBuilder(mode_registry=registry).build(session),
            )

            result = services.command_router.route(CommandId.TAKE_ANOTHER_MEASUREMENT)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", result.status)
        assert current is not None
        self.assertEqual((), current.warning_view_models)


if __name__ == "__main__":
    unittest.main()

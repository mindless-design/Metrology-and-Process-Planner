import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.process_context_fixtures import recipe_path
from tests.process_context_fixtures import session as process_session


class SessionEditorProcessCommandBridgeTests(unittest.TestCase):
    def test_attach_recipe_action_preserves_payload_through_command_router(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            path = recipe_path(Path(temp_dir))
            document = SessionDocumentBuilder().build(process_session())
            result = services.session_editor_controller.open_document(document)

            result.window["on_action"](
                EditorAction(
                    EditorActionType.ATTACH_RECIPE,
                    "Attach Recipe",
                    "dashboard",
                    payload=(("recipe_path", str(path)),),
                )
            )

        routed = services.session_editor_controller.last_command_result
        current = services.session_editor_controller.current_document
        self.assertIsNotNone(routed)
        self.assertEqual(CommandId.ATTACH_RECIPE, routed.command_id)
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertEqual("recipe_gate_stack", current.session.process_context.recipe_id)

    def test_process_context_commands_use_active_editor_document(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(process_session())
        services.session_editor_controller.open_document(document)

        validated = services.command_router.route(CommandId.VALIDATE_PROCESS_CONTEXT)
        detached = services.command_router.route(CommandId.DETACH_RECIPE)

        current = services.session_editor_controller.current_document
        self.assertEqual("warning", validated.status)
        self.assertEqual("success", detached.status)
        self.assertIsNotNone(current)
        self.assertEqual("", current.session.process_context.recipe_id)


if __name__ == "__main__":
    unittest.main()

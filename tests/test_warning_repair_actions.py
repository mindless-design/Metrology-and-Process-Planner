import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.process_context_fixtures import capture_session, recipe_path


def _session_with_warning(code: str = "PROCESS_RECIPE_MISSING"):
    session = capture_session()
    warning = WarningRecord(
        id=f"warn-cap-001-{code.lower()}",
        message="Process output needs attention.",
        source="process_context",
        code=code,
        related_item_refs=("capture:cap-001",),
        repair_suggestion="Attach a recipe and regenerate process outputs.",
    )
    capture = replace(session.captures[0], warning_ids=(warning.id,))
    return replace(session, captures=(capture,), warnings=(warning,))

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class WarningRepairActionTestsPart1(unittest.TestCase):
    def test_process_warning_exposes_capture_repair_actions(self) -> None:
        document = SessionDocumentBuilder().build(_session_with_warning())
        warning_item = document.items_by_id["warning:warn-cap-001-process_recipe_missing"]
        actions = DefaultSessionModeAdapter().actions(document.session, warning_item)
        action_types = {action.action_type for action in actions}

        self.assertEqual("capture:cap-001", warning_item.parent_id)
        self.assertIn(EditorActionType.ATTACH_RECIPE, action_types)
        self.assertIn(EditorActionType.VALIDATE_PROCESS_CONTEXT, action_types)
        self.assertIn(EditorActionType.REGENERATE_PROCESS_OUTPUT, action_types)
        self.assertIn(EditorActionType.IGNORE_WARNING, action_types)
        regenerate = next(
            action
            for action in actions
            if action.action_type is EditorActionType.REGENERATE_PROCESS_OUTPUT
        )
        self.assertEqual("capture:cap-001", regenerate.item_id)

    def test_recipe_path_warning_exposes_open_recipe_file_action(self) -> None:
        session = _session_with_warning("PROCESS_RECIPE_FILE_NOT_FOUND")
        context = replace(session.process_context, recipe_path="recipes/missing.json")
        document = SessionDocumentBuilder().build(replace(session, process_context=context))
        actions = DefaultSessionModeAdapter().actions(
            document.session,
            document.items_by_id["warning:warn-cap-001-process_recipe_file_not_found"],
        )

        open_recipe = next(
            action for action in actions if action.action_type is EditorActionType.OPEN_RECIPE_FILE
        )
        self.assertEqual((("recipe_path", "recipes/missing.json"),), open_recipe.payload)

    def test_process_warning_is_hidden_in_non_process_mode(self) -> None:
        source = replace(_session_with_warning(), mode=SessionMode.SIMPLE_CAPTURE)
        document = SessionDocumentBuilder().build(source)

        self.assertNotIn("warning:warn-cap-001-process_recipe_missing", document.items_by_id)
        self.assertEqual((), document.warning_view_models)

    def test_ignore_warning_marks_status_without_deleting_warning(self) -> None:
        document = SessionDocumentBuilder().build(_session_with_warning())
        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.IGNORE_WARNING,
                "Ignore Warning",
                "warning:warn-cap-001-process_recipe_missing",
            ),
        )

        warning = result.document.session.warnings[0]
        self.assertEqual("success", result.status)
        self.assertEqual("ignored", warning.status)
        self.assertIsNotNone(warning.resolved_at)
        actions = DefaultSessionModeAdapter().actions(
            result.document.session,
            result.document.items_by_id["warning:warn-cap-001-process_recipe_missing"],
        )
        self.assertNotIn(
            EditorActionType.IGNORE_WARNING,
            {action.action_type for action in actions},
        )

    def test_open_recipe_file_returns_path_handoff_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = recipe_path(Path(folder))
            document = SessionDocumentBuilder().build(_session_with_warning())

            result = EditorActionDispatcher().dispatch(
                document,
                EditorAction(
                    EditorActionType.OPEN_RECIPE_FILE,
                    "Open Recipe File",
                    "dashboard",
                    payload=(("recipe_path", str(path)),),
                ),
            )

        self.assertEqual("success", result.status)
        self.assertEqual(path, result.output_path)

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    ProcessContext,
    SessionModeId,
)
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending
from tests.process_context_fixtures import recipe_path


class NonProcessDispatcherProcessGuardTests(unittest.TestCase):
    def test_direct_attach_recipe_action_is_unavailable_for_non_process_mode(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = recipe_path(Path(temp_dir))
            document = SessionDocumentBuilder().build(session_without_pending())

            result = EditorActionDispatcher().dispatch(
                document,
                EditorAction(
                    EditorActionType.ATTACH_RECIPE,
                    "Attach Recipe",
                    "dashboard",
                    payload=(("recipe_path", str(path)),),
                ),
            )

        self.assertEqual("unavailable", result.status)
        self.assertIn("recipe-free mode", result.message)
        self.assertEqual("", result.document.session.process_context.recipe_id)

    def test_direct_detach_recipe_action_is_unavailable_for_non_process_mode(self) -> None:
        source = replace(session_without_pending(), process_context=ProcessContext(recipe_id="old"))
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.DETACH_RECIPE, "Detach Recipe", "dashboard"),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("recipe-free mode", result.message)
        self.assertEqual("old", result.document.session.process_context.recipe_id)

    def test_direct_refresh_recipe_fingerprint_is_unavailable_for_non_process_mode(self) -> None:
        source = replace(
            session_without_pending(),
            process_context=ProcessContext(recipe_id="old", recipe_fingerprint="original"),
        )
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.REFRESH_RECIPE_FINGERPRINT,
                "Refresh Recipe Fingerprint",
                "dashboard",
            ),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("recipe-free mode", result.message)
        self.assertEqual("original", result.document.session.process_context.recipe_fingerprint)

    def test_direct_process_validation_does_not_create_recipe_warnings(self) -> None:
        document = SessionDocumentBuilder().build(session_without_pending())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.VALIDATE_PROCESS_CONTEXT, "Validate", "dashboard"),
        )

        self.assertEqual("unavailable", result.status)
        self.assertEqual((), result.document.session.process_context.warning_ids)
        self.assertEqual((), result.document.session.warnings)

    def test_direct_regenerate_process_output_is_unavailable_for_stale_non_process_records(
        self,
    ) -> None:
        source = session_without_pending()
        source = replace(source, process_context=ProcessContext(recipe_id="legacy-recipe"))
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.REGENERATE_PROCESS_OUTPUT, "Regenerate", "dashboard"),
        )

        self.assertEqual("unavailable", result.status)
        self.assertEqual((), result.document.session.process_outputs)

    def test_external_recipe_free_mode_process_actions_use_loaded_registry(self) -> None:
        registry = _external_recipe_free_registry()
        source = replace(session_without_pending(), mode=SessionModeId("external_mode"))
        document = SessionDocumentBuilder(mode_registry=registry).build(source)

        result = EditorActionDispatcher(mode_registry=registry).dispatch(
            document,
            EditorAction(EditorActionType.VALIDATE_PROCESS_CONTEXT, "Validate", "dashboard"),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("recipe-free mode", result.message)
        self.assertEqual((), result.document.session.process_context.warning_ids)
        self.assertEqual((), result.document.session.warnings)


def _external_recipe_free_registry() -> ModeRegistry:
    return ModeRegistry((ModeDefinition("external_mode", "External Mode"),))


if __name__ == "__main__":
    unittest.main()

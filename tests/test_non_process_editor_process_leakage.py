import unittest
from dataclasses import replace

from metrology_process_planner.domains.modes.mode_non_process_builtins import non_process_modes
from metrology_process_planner.domains.session import (
    ProcessOutputRecord,
    WarningRecord,
    session_mode_id,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


class NonProcessEditorProcessLeakageTests(unittest.TestCase):
    def test_recipe_free_modes_hide_stale_process_outputs_and_actions(self) -> None:
        forbidden_actions = {
            EditorActionType.ATTACH_RECIPE,
            EditorActionType.DETACH_RECIPE,
            EditorActionType.VALIDATE_PROCESS_CONTEXT,
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
        }
        for mode_id in _recipe_free_mode_ids():
            with self.subTest(mode_id=mode_id):
                document = SessionDocumentBuilder().build(_legacy_process_session(mode_id))
                adapter = DefaultSessionModeAdapter()
                dashboard = document.items_by_id["dashboard"]
                capture = document.items_by_id["capture:cap-001"]

                dashboard_fields = adapter.metadata_fields(document.session, dashboard)
                capture_fields = adapter.metadata_fields(document.session, capture)
                actions = (
                    *adapter.actions(document.session, dashboard),
                    *adapter.actions(document.session, capture),
                )

                self.assertNotIn("Cross Sections", _group_labels(document))
                self.assertNotIn("Warnings", _group_labels(document))
                self.assertFalse(
                    any(item_id.startswith("process_output:") for item_id in document.items_by_id)
                )
                self.assertFalse(any(field.key.startswith("process_")
                                     for field in dashboard_fields))
                self.assertFalse(any(field.key.startswith("process_")
                                     for field in capture_fields))
                self.assertTrue(forbidden_actions.isdisjoint(
                    {action.action_type for action in actions}
                ))


def _legacy_process_session(mode_id: str):
    return replace(
        session_without_pending(),
        mode=session_mode_id(mode_id),
        process_outputs=(
            ProcessOutputRecord(
                "out-001",
                "Profile Image",
                "profile_image",
                status="stale",
                metadata={"capture_id": "cap-001"},
            ),
        ),
        warnings=(
            WarningRecord(
                "process-warning",
                "Recipe missing",
                source="process_context",
                code="PROCESS_RECIPE_MISSING",
            ),
        ),
    )


def _recipe_free_mode_ids() -> tuple[str, ...]:
    return tuple(dict.fromkeys(definition.mode_id for definition in non_process_modes()))


def _group_labels(document: object) -> set[str]:
    return {group.label for group in document.navigator_groups}


if __name__ == "__main__":
    unittest.main()

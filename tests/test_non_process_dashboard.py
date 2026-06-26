import unittest
from dataclasses import replace

from metrology_process_planner.app.session_editor_command_map import command_for_action
from metrology_process_planner.domains.modes.mode_non_process_builtins import non_process_modes
from metrology_process_planner.domains.session import (
    SessionMode,
    SetupState,
    WorkflowState,
    session_mode_id,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.editor.adapter_actions import default_actions
from metrology_process_planner.workflows.editor.dispatcher_routes import _ACTION_HANDLERS
from metrology_process_planner.workflows.editor.view_models import EditorActionType
from tests.editor_render_fixtures import session, session_without_pending


class NonProcessDashboardTests(unittest.TestCase):
    def test_dashboard_reports_setup_and_batch_status_by_mode(self) -> None:
        adapter = DefaultSessionModeAdapter()
        fast_batch = replace(session(), mode=SessionMode.FAST_BATCH_CAPTURE)
        optical = replace(session_without_pending(), mode=SessionMode.OPTICAL_METROLOGY)

        batch_fields = _dashboard_fields(adapter, fast_batch)
        optical_fields = _dashboard_fields(adapter, optical)

        self.assertEqual("ready, 1 saved, 1 pending", batch_fields["batch_status"])
        self.assertEqual("not required", batch_fields["setup_status"])
        self.assertEqual("incomplete", optical_fields["setup_status"])
        self.assertNotIn("batch_status", optical_fields)

    def test_dashboard_reports_fast_batch_capture_armed_status(self) -> None:
        adapter = DefaultSessionModeAdapter()
        fast_batch = replace(
            session_without_pending(),
            mode=SessionMode.FAST_BATCH_CAPTURE,
            workflow=WorkflowState(active=True, stage="box_capture"),
        )

        batch_fields = _dashboard_fields(adapter, fast_batch)

        self.assertEqual("capturing, 1 saved, 0 pending", batch_fields["batch_status"])

    def test_dashboard_setup_status_rejects_stale_ready_flag(self) -> None:
        adapter = DefaultSessionModeAdapter()
        source = replace(
            session_without_pending(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(is_capture_ready=True),
        )

        fields = _dashboard_fields(adapter, source)

        self.assertEqual("incomplete", fields["setup_status"])

    def test_dashboard_overview_actions_are_mode_appropriate(self) -> None:
        simple_actions = _dashboard_action_types(session_without_pending())
        fast_batch_actions = _dashboard_action_types(
            replace(session_without_pending(), mode=SessionMode.FAST_BATCH_CAPTURE)
        )
        optical_actions = _dashboard_action_types(
            replace(session_without_pending(), mode=SessionMode.OPTICAL_METROLOGY)
        )
        grid_actions = _dashboard_action_types(
            replace(session_without_pending(), mode=SessionMode.GRID_MEASUREMENT)
        )

        self.assertIn(EditorActionType.GENERATE_SESSION_OVERVIEW, simple_actions)
        self.assertNotIn(EditorActionType.BATCH_RENAME, simple_actions)
        self.assertIn(EditorActionType.BATCH_RENAME, fast_batch_actions)
        self.assertNotIn(EditorActionType.GENERATE_METROLOGY_OVERVIEW, simple_actions)
        self.assertNotIn(EditorActionType.GENERATE_GRID_OVERVIEW, simple_actions)
        self.assertIn(EditorActionType.GENERATE_METROLOGY_OVERVIEW, optical_actions)
        self.assertNotIn(EditorActionType.GENERATE_GRID_OVERVIEW, optical_actions)
        self.assertIn(EditorActionType.GENERATE_GRID_OVERVIEW, grid_actions)
        self.assertNotIn(EditorActionType.GENERATE_METROLOGY_OVERVIEW, grid_actions)

    def test_pending_capture_actions_are_routable_without_measurement_dead_end(self) -> None:
        document = SessionDocumentBuilder().build(session())
        actions = default_actions(document.session, document.items_by_id["pending:pending-001"])

        self.assertNotIn("take_measurement", {action.action_type.value for action in actions})
        self.assertNotIn(EditorActionType.EXIT_SESSION, {action.action_type for action in actions})
        self.assertTrue(all(command_for_action(action) is not None for action in actions))

    def test_visible_recipe_free_actions_have_command_or_workflow_routes(self) -> None:
        for mode_id in _recipe_free_mode_ids():
            with self.subTest(mode=mode_id):
                source = replace(session_without_pending(), mode=session_mode_id(mode_id))
                document = SessionDocumentBuilder().build(source)
                gaps = _unrouted_actions(source, document)

                self.assertEqual((), gaps)

    def test_capture_copy_actions_return_clipboard_ready_text(self) -> None:
        document = SessionDocumentBuilder().build(session_without_pending())
        dispatcher = EditorActionDispatcher()

        center = dispatcher.dispatch(
            document,
            EditorAction(EditorActionType.COPY_CENTER_COORDINATE, "Copy", "capture:cap-001"),
        )
        bounds = dispatcher.dispatch(
            document,
            EditorAction(EditorActionType.COPY_BOUNDS, "Copy", "capture:cap-001"),
        )
        row = dispatcher.dispatch(
            document,
            EditorAction(EditorActionType.COPY_CSV_ROW, "Copy", "capture:cap-001"),
        )

        self.assertEqual("success", center.status)
        self.assertIn("5.0,5.0", center.message)
        self.assertEqual("success", bounds.status)
        self.assertIn("0,0,10,10", bounds.message)
        self.assertEqual("success", row.status)
        self.assertIn("session-001,Demo,simple_capture,simple_capture,cap-001", row.message)
        self.assertIn("capture-cap-001-crop,images/cap-001.png,present", row.message)
        self.assertIn("meas-001,Gate CD,line", row.message)


def _dashboard_fields(
    adapter: DefaultSessionModeAdapter,
    source,
) -> dict[str, str]:
    document = SessionDocumentBuilder().build(source)
    return {
        field.key: field.value
        for field in adapter.metadata_fields(source, document.items_by_id["dashboard"])
    }


def _dashboard_action_types(source) -> tuple[EditorActionType, ...]:
    document = SessionDocumentBuilder().build(source)
    return tuple(
        action.action_type
        for action in default_actions(source, document.items_by_id["dashboard"])
    )


def _unrouted_actions(source, document) -> tuple[str, ...]:
    adapter = DefaultSessionModeAdapter()
    gaps = []
    for item_id in document.items_by_id:
        for action in adapter.actions(source, document.items_by_id[item_id]):
            if not action.enabled:
                continue
            if command_for_action(action) is None and action.action_type not in _ACTION_HANDLERS:
                gaps.append(action.action_type.value)
    return tuple(sorted(set(gaps)))


def _recipe_free_mode_ids() -> tuple[str, ...]:
    return tuple(dict.fromkeys(definition.mode_id for definition in non_process_modes()))


if __name__ == "__main__":
    unittest.main()

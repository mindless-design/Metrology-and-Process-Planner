import unittest
from dataclasses import replace

from metrology_process_planner.app.session_editor_command_map import command_for_action
from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.editor.dispatcher_routes import _ACTION_HANDLERS
from metrology_process_planner.workflows.editor.view_models import EditorActionType

RECIPE_FREE_MODES = (
    SessionMode.SIMPLE_LABELED_CAPTURE,
    SessionMode.FAST_BATCH_CAPTURE,
    SessionMode.CAD_REVIEW_CAPTURE,
    SessionMode.OPTICAL_METROLOGY,
    SessionMode.CDSEM_MEASUREMENT,
    SessionMode.GRID_MEASUREMENT,
)

PROCESS_ACTIONS = {
    EditorActionType.ATTACH_RECIPE,
    EditorActionType.DETACH_RECIPE,
    EditorActionType.VALIDATE_PROCESS_CONTEXT,
    EditorActionType.REGENERATE_PROCESS_OUTPUT,
    EditorActionType.OPEN_RECIPE_FILE,
}

REQUIRED_SAVED_CAPTURE_ACTIONS = {
    EditorActionType.EDIT_METADATA,
    EditorActionType.REPLACE_SITE_BOX,
    EditorActionType.ADD_MEASUREMENT,
    EditorActionType.REGENERATE_ARTIFACT,
    EditorActionType.EXPORT_CSV,
    EditorActionType.BUILD_POWERPOINT,
}


class NonProcessSavedCaptureActionTests(unittest.TestCase):
    def test_recipe_free_saved_box_capture_actions_are_available_and_routable(self) -> None:
        for mode in RECIPE_FREE_MODES:
            with self.subTest(mode=mode.value):
                document = SessionDocumentBuilder().build(_saved_box_session(mode))

                actions = _actions(document)
                by_type = {action.action_type: action for action in actions}

                self.assertLessEqual(REQUIRED_SAVED_CAPTURE_ACTIONS, set(by_type))
                self.assertFalse(PROCESS_ACTIONS & set(by_type))
                for action_type in REQUIRED_SAVED_CAPTURE_ACTIONS:
                    self.assertTrue(
                        by_type[action_type].enabled,
                        by_type[action_type].disabled_reason,
                    )
                self.assertEqual(
                    [],
                    [
                        action.action_type.value
                        for action in actions
                        if action.enabled
                        and action.action_type not in _ACTION_HANDLERS
                        and command_for_action(action) is None
                    ],
                )

    def test_measurement_and_replacement_explain_non_box_capture_limit(self) -> None:
        document = SessionDocumentBuilder().build(_saved_point_session())

        by_type = {action.action_type: action for action in _actions(document, "capture:cap-point")}

        self.assertFalse(by_type[EditorActionType.REPLACE_SITE_BOX].enabled)
        self.assertEqual(
            "Only saved box captures can be replaced.",
            by_type[EditorActionType.REPLACE_SITE_BOX].disabled_reason,
        )
        self.assertFalse(by_type[EditorActionType.ADD_MEASUREMENT].enabled)
        self.assertEqual(
            "Measurements require a saved box capture.",
            by_type[EditorActionType.ADD_MEASUREMENT].disabled_reason,
        )

    def test_measurement_explains_missing_saved_canvas_box(self) -> None:
        source = replace(_saved_box_session(SessionMode.SIMPLE_LABELED_CAPTURE), canvas_objects=())
        document = SessionDocumentBuilder().build(source)

        by_type = {action.action_type: action for action in _actions(document)}

        self.assertFalse(by_type[EditorActionType.ADD_MEASUREMENT].enabled)
        self.assertEqual(
            "Measurements require a saved canvas box for this capture.",
            by_type[EditorActionType.ADD_MEASUREMENT].disabled_reason,
        )


def _actions(document, item_id: str = "capture:cap-001"):
    return DefaultSessionModeAdapter().actions(document.session, document.items_by_id[item_id])


def _saved_box_session(mode: SessionMode) -> SessionRecord:
    capture = CaptureRecord(
        "cap-001",
        "Site 1",
        CaptureGeometry.box(Box(0, 0, 10, 5)),
        "2026-06-25T00:00:00Z",
    )
    return SessionRecord(
        id="session-001",
        name="Recipe Free Actions",
        mode=mode,
        created_at="2026-06-25T00:00:00Z",
        updated_at="2026-06-25T00:00:00Z",
        captures=(capture,),
        canvas_objects=(
            CanvasObject(
                "canvas-cap-001",
                "session-001",
                "cap-001",
                CanvasObjectType.SITE_BOX,
                None,
                capture.geometry,
                CanvasWorkflowState.SAVED,
            ),
        ),
    )


def _saved_point_session() -> SessionRecord:
    geometry = CaptureGeometry.point_capture(Point(1, 2))
    capture = CaptureRecord(
        "cap-point",
        "Point Site",
        geometry,
        "2026-06-25T00:00:00Z",
    )
    return SessionRecord(
        id="session-001",
        name="Recipe Free Actions",
        mode=SessionMode.SIMPLE_LABELED_CAPTURE,
        created_at="2026-06-25T00:00:00Z",
        updated_at="2026-06-25T00:00:00Z",
        captures=(capture,),
        canvas_objects=(
            CanvasObject(
                "canvas-point",
                "session-001",
                "cap-point",
                CanvasObjectType.POINT,
                None,
                geometry,
                CanvasWorkflowState.SAVED,
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()

import unittest

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows import (
    CanvasOverlayManager,
    OverlayCommand,
    OverlayCommandKind,
    SelectionCoordinator,
)


class CanvasOverlayAndSelectionTests(unittest.TestCase):
    def test_overlay_manager_emits_preview_commit_and_remove_commands(self) -> None:
        backend = FakeOverlayBackend()
        manager = CanvasOverlayManager(backend)
        canvas_object = _canvas_object()

        manager.show_live_preview(canvas_object)
        manager.update_live_preview(canvas_object)
        manager.commit_object(canvas_object)
        manager.remove_object(canvas_object.id)

        self.assertEqual(
            [
                OverlayCommandKind.CREATE_PREVIEW,
                OverlayCommandKind.UPDATE_PREVIEW,
                OverlayCommandKind.COMMIT_OBJECT,
                OverlayCommandKind.REMOVE_OBJECT,
            ],
            [command.kind for command in backend.commands],
        )

    def test_restore_session_replays_flags_for_saved_objects(self) -> None:
        backend = FakeOverlayBackend()
        manager = CanvasOverlayManager(backend)
        session = _session(
            _canvas_object(
                flags=(
                    CanvasVisualFlag.SELECTED,
                    CanvasVisualFlag.ACTIVE_PARENT,
                    CanvasVisualFlag.STALE,
                    CanvasVisualFlag.INVALID,
                )
            )
        )

        manager.restore_session(session)

        self.assertEqual(
            [
                OverlayCommandKind.RESTORE_OBJECT,
                OverlayCommandKind.SELECT_OBJECT,
                OverlayCommandKind.ACTIVE_PARENT,
                OverlayCommandKind.MARK_STALE,
                OverlayCommandKind.MARK_INVALID,
            ],
            [command.kind for command in backend.commands],
        )

    def test_hidden_restore_hides_object(self) -> None:
        backend = FakeOverlayBackend()
        manager = CanvasOverlayManager(backend)

        manager.restore_session(_session(_canvas_object(flags=(CanvasVisualFlag.HIDDEN,))))

        self.assertEqual([OverlayCommandKind.HIDE_OBJECT], [item.kind for item in backend.commands])

    def test_editor_selection_updates_session_and_canvas_overlay(self) -> None:
        backend = FakeOverlayBackend()
        session = _session(_canvas_object())

        result = SelectionCoordinator(CanvasOverlayManager(backend)).select_from_editor(
            session,
            "canvas-001",
        )

        self.assertTrue(result.handled)
        self.assertIn(CanvasVisualFlag.SELECTED, result.session.canvas_objects[0].visual_state)
        self.assertEqual(OverlayCommandKind.SELECT_OBJECT, backend.commands[-1].kind)

    def test_canvas_selection_notifies_editor_sink(self) -> None:
        backend = FakeOverlayBackend()
        sink = FakeEditorSink()
        session = _session(_canvas_object())

        SelectionCoordinator(CanvasOverlayManager(backend), sink).select_from_canvas(
            session,
            "canvas-001",
        )

        self.assertEqual(("canvas-001",), sink.selected_ids)


class FakeOverlayBackend:
    def __init__(self) -> None:
        self.commands: list[OverlayCommand] = []

    def apply(self, command: OverlayCommand) -> None:
        self.commands.append(command)


class FakeEditorSink:
    def __init__(self) -> None:
        self.selected_ids: tuple[str, ...] = ()

    def select_object(self, object_id: str) -> None:
        self.selected_ids = self.selected_ids + (object_id,)


def _canvas_object(
    flags: tuple[CanvasVisualFlag, ...] = (),
) -> CanvasObject:
    return CanvasObject(
        id="canvas-001",
        session_id="session-001",
        record_id="cap-001",
        object_type=CanvasObjectType.SITE_BOX,
        parent_id=None,
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        workflow_state=CanvasWorkflowState.SAVED,
        visual_state=flags,
    )


def _session(canvas_object: CanvasObject) -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo Session",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        canvas_objects=(canvas_object,),
    )


if __name__ == "__main__":
    unittest.main()

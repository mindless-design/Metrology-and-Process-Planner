import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    PendingCapture,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    SessionDocumentStore,
    mark_metadata_edit,
)


class SessionEditorStoreDispatcherTests(unittest.TestCase):
    def test_document_store_preserves_unknown_top_level_fields_on_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            payload = _session().to_dict()
            payload["legacy_field"] = {"kept": True}
            paths.session_json.write_text(json.dumps(payload), encoding="utf-8")

            store = SessionDocumentStore()
            document = mark_metadata_edit(store.load(paths.folder), "dashboard", "name", "Demo")
            saved = store.save(document, paths)
            raw = json.loads(paths.session_json.read_text(encoding="utf-8"))

        self.assertFalse(saved.dirty_state.is_dirty)
        self.assertEqual({"kept": True}, raw["legacy_field"])

    def test_dispatcher_save_failure_preserves_dirty_document(self) -> None:
        document = mark_metadata_edit(_document(), "dashboard", "name", "Demo")
        dispatcher = EditorActionDispatcher(
            paths=SessionPaths.for_folder(Path("unused")),
            document_store=FailingStore(),
        )

        result = dispatcher.dispatch(document, EditorAction(EditorActionType.SAVE_EDITS, "Save"))

        self.assertEqual("error", result.status)
        self.assertTrue(result.document.dirty_state.is_dirty)

    def test_pending_save_promotes_capture_and_rebuilds_document(self) -> None:
        document = _document()
        action = EditorAction(
            EditorActionType.PENDING_SAVE,
            "Save",
            "pending:pending-001",
            payload=(("label", "Saved Site"), ("notes", "Reviewed")),
        )

        result = EditorActionDispatcher().dispatch(document, action)

        self.assertEqual("success", result.status)
        self.assertEqual((), result.document.session.pending_captures)
        self.assertEqual("Saved Site", result.document.session.captures[0].label)
        self.assertIn("capture:cap-001", result.document.items_by_id)

    def test_dispatcher_selects_canvas_object_through_document_index(self) -> None:
        result = EditorActionDispatcher().dispatch(
            _document(),
            EditorAction(
                EditorActionType.SELECT_CANVAS_OBJECT,
                "Select",
                payload=(("canvas_object_id", "canvas-pending"),),
            ),
        )

        self.assertEqual("pending:pending-001", result.document.selection.selected_item_id)

    def test_export_csv_and_deferred_action_results_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            dispatcher = EditorActionDispatcher(paths=paths)
            exported = dispatcher.dispatch(
                _document(),
                EditorAction(EditorActionType.EXPORT_CSV, "CSV"),
            )
            unavailable = dispatcher.dispatch(
                _document(),
                EditorAction(EditorActionType.BUILD_POWERPOINT, "Build PowerPoint"),
            )

        self.assertEqual("success", exported.status)
        self.assertEqual(paths.capture_csv, exported.output_path)
        self.assertEqual("unavailable", unavailable.status)


class FailingStore:
    def save(self, document, paths):
        raise OSError("disk full")


def _document():
    return SessionDocumentBuilder().build(_session(), raw_payload=_session().to_dict())


def _session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        canvas_objects=(
            CanvasObject(
                "canvas-pending",
                "session-001",
                "pending-001",
                CanvasObjectType.SITE_BOX,
                None,
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                CanvasWorkflowState.PENDING,
            ),
        ),
        pending_captures=(
            PendingCapture(
                "pending-001",
                "session-001",
                "canvas-pending",
                CanvasObjectType.SITE_BOX,
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                image_artifact_path="images/pending-001.png",
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()

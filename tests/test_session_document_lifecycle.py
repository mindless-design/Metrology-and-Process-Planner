import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.domains.session import (
    SessionMode,
    SessionRecord,
    SourceLayoutContext,
)
from metrology_process_planner.workflows.editor import (
    NewSessionRequest,
    SessionDocumentBuilder,
    SessionDocumentStore,
    mark_metadata_edit,
)


class SessionDocumentLifecycleTests(unittest.TestCase):
    def test_new_session_creates_valid_session_json_and_standard_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = SessionEditorController()
            result = controller.new_session(
                NewSessionRequest(Path(temp_dir), "Document Demo", SessionMode.SIMPLE_CAPTURE)
            )
            payload = json.loads((Path(temp_dir) / "session.json").read_text(encoding="utf-8"))

        self.assertEqual("opened", result.status)
        self.assertEqual("Document Demo", payload["session"]["name"])
        self.assertEqual([], payload["captures"])
        self.assertEqual({}, payload["artifacts"])
        self.assertEqual([], payload["warnings"])
        self.assertEqual("relative_to_session_json", payload["paths"]["path_mode"])

    def test_open_existing_session_tracks_loaded_path_and_populates_editor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "session.json"
            path.write_text(json.dumps(_session().to_dict()), encoding="utf-8")
            controller = SessionEditorController()
            result = controller.open_session_path(path)

        self.assertEqual("opened", result.status)
        self.assertEqual(path, result.document.loaded_path)
        self.assertIn("dashboard", result.document.items_by_id)
        self.assertEqual((path,), controller.recent_session_paths())

    def test_save_is_atomic_preserves_unknown_fields_and_clears_dirty_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = Path(temp_dir)
            payload = _session().to_dict()
            payload["unknown_future_block"] = {"kept": True}
            (paths / "session.json").write_text(json.dumps(payload), encoding="utf-8")
            controller = SessionEditorController()
            controller.open_session_path(paths)
            dirty = mark_metadata_edit(
                controller.current_document,
                "dashboard",
                "name",
                "Renamed",
            )
            controller.replace_current_document(dirty)
            result = controller.save_current_session()
            saved = json.loads((paths / "session.json").read_text(encoding="utf-8"))
            backup_exists = (paths / "session.json.bak").exists()

        self.assertEqual("saved", result.status)
        self.assertFalse(result.document.dirty_state.is_dirty)
        self.assertTrue(backup_exists)
        self.assertEqual("Renamed", saved["session"]["name"])
        self.assertEqual({"kept": True}, saved["unknown_future_block"])

    def test_save_as_writes_new_document_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source"
            target = Path(temp_dir) / "target"
            source.mkdir()
            (source / "session.json").write_text(json.dumps(_session().to_dict()), encoding="utf-8")
            controller = SessionEditorController()
            controller.open_session_path(source)
            result = controller.save_current_session_as(target)
            target_exists = (target / "session.json").exists()

        self.assertIn(result.status, {"opened", "raised"})
        self.assertTrue(target_exists)
        self.assertEqual(target / "session.json", result.document.loaded_path)

    def test_dirty_close_blocks_until_save_or_discard_choice(self) -> None:
        controller = SessionEditorController()
        controller.open_document(SessionDocumentBuilder().build(_session()))
        dirty = mark_metadata_edit(controller.current_document, "dashboard", "name", "Dirty")
        controller.replace_current_document(dirty)

        blocked = controller.close_current_session()
        discarded = controller.close_current_session("discard")

        self.assertEqual("blocked", blocked.status)
        self.assertEqual("closed", discarded.status)
        self.assertIsNone(controller.current_document)

    def test_missing_source_layout_adds_warning_without_blocking_open(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session = _session(
                source_layout=SourceLayoutContext(layout_path="missing_layout.gds")
            )
            (Path(temp_dir) / "session.json").write_text(
                json.dumps(session.to_dict()),
                encoding="utf-8",
            )
            document = SessionDocumentStore().load(temp_dir)

        self.assertTrue(
            any(warning.code == "SOURCE_LAYOUT_MISSING" for warning in document.warnings)
        )

    def test_invalid_session_json_produces_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "session.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Session JSON must contain an object"):
                SessionDocumentStore().load(path)

    def test_open_editor_with_no_active_session_shows_start_screen(self) -> None:
        controller = SessionEditorController()

        result = controller.open_current_session()

        self.assertEqual("start_screen", result.status)
        self.assertEqual(
            ("New Session", "Open Existing Session JSON", "Open Recent"),
            result.window["actions"],
        )


def _session(source_layout: SourceLayoutContext | None = None) -> SessionRecord:
    source_layout = source_layout if source_layout is not None else SourceLayoutContext()
    return SessionRecord(
        id="session-001",
        name="Document Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-24T00:00:00Z",
        updated_at="2026-06-24T00:00:00Z",
        source_layout=source_layout,
    )


if __name__ == "__main__":
    unittest.main()

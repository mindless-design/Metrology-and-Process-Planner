import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_path_adapter import (
    NewSessionSelection,
    PathSelection,
)
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending
from tests.session_lifecycle_command_fixtures import (
    FakePathAdapter,
    document_store,
    paths_for,
)


class SessionDocumentPathCommandTests(unittest.TestCase):
    def test_new_session_command_uses_selected_folder_and_mode(self) -> None:
        with TemporaryDirectory() as temp_dir:
            adapter = FakePathAdapter(new_session=NewSessionSelection.selected(temp_dir, "Demo"))
            services = build_app_services(path_adapter=adapter)

            result = services.command_router.route(CommandId.NEW_SESSION)

            self.assertEqual("opened", result.status)
            self.assertTrue((Path(temp_dir) / "session.json").exists())
            document = services.session_editor_controller.current_document
            self.assertIsNotNone(document)
            self.assertEqual("Demo", document.session.name)

    def test_open_session_command_uses_selected_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "session.json"
            source = SessionDocumentBuilder().build(session_without_pending())
            source = document_store().save(source, paths_for(temp_dir))
            self.assertEqual(path, source.loaded_path)
            adapter = FakePathAdapter(open_session=PathSelection.selected(path))
            services = build_app_services(path_adapter=adapter)

            result = services.command_router.route(CommandId.OPEN_SESSION)

            self.assertEqual("opened", result.status)
            self.assertEqual(path, services.session_editor_controller.current_document.loaded_path)

    def test_open_recent_command_uses_selected_recent_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "session.json"
            source = SessionDocumentBuilder().build(session_without_pending())
            document_store().save(source, paths_for(temp_dir))
            adapter = FakePathAdapter(recent_session=PathSelection.selected(path))
            services = build_app_services(path_adapter=adapter)
            services.session_editor_controller.open_session_path(path)

            result = services.command_router.route(CommandId.OPEN_RECENT_SESSION)

            self.assertIn(result.status, {"opened", "raised"})
            self.assertEqual(
                (path.resolve(),),
                services.session_editor_controller.recent_session_paths(),
            )

    def test_save_as_command_uses_selected_destination(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source_folder = Path(temp_dir) / "source"
            target_folder = Path(temp_dir) / "target"
            adapter = FakePathAdapter(save_as=PathSelection.selected(target_folder))
            services = build_app_services(path_adapter=adapter)
            new_session = NewSessionSelection.selected(source_folder).to_request()
            services.session_editor_controller.new_session(new_session)

            result = services.command_router.route(CommandId.SAVE_SESSION_AS)

            self.assertIn(result.status, {"opened", "raised"})
            self.assertTrue((target_folder / "session.json").exists())
            self.assertEqual(
                target_folder / "session.json",
                services.session_editor_controller.current_document.loaded_path,
            )

    def test_cancelled_lifecycle_picker_does_not_mutate_document(self) -> None:
        services = build_app_services(path_adapter=FakePathAdapter())

        result = services.command_router.route(CommandId.NEW_SESSION)

        self.assertEqual("cancelled", result.status)
        self.assertIsNone(services.session_editor_controller.current_document)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from metrology_process_planner.domains.modes.mode_registry import ModeDefinition, ModeRegistry
from metrology_process_planner.domains.session import SessionMode, SessionModeId
from metrology_process_planner.infrastructure.klayout.recipe_path_adapter import (
    KLayoutRecipePathAdapter,
)
from metrology_process_planner.infrastructure.klayout.report_output_adapter import (
    KLayoutReportOutputAdapter,
)
from metrology_process_planner.infrastructure.klayout.session_path_adapter import (
    KLayoutSessionPathAdapter,
)


class KLayoutSessionPathAdapterTests(unittest.TestCase):
    def test_new_session_selection_uses_folder_name_and_mode_choice(self) -> None:
        adapter = KLayoutSessionPathAdapter(
            _FakePya(folder="C:/tmp/demo", item="optical_metrology")
        )

        selection = adapter.select_new_session()

        self.assertEqual("selected", selection.status)
        self.assertEqual("demo", selection.label)
        self.assertEqual(SessionMode.OPTICAL_METROLOGY, selection.mode)

    def test_new_session_picker_rejects_hidden_legacy_mode_choice(self) -> None:
        adapter = KLayoutSessionPathAdapter(_FakePya(folder="C:/tmp/demo", item="cdsem_capture"))

        selection = adapter.select_new_session()

        self.assertEqual("selected", selection.status)
        self.assertEqual(SessionMode.SIMPLE_CAPTURE, selection.mode)

    def test_new_session_picker_accepts_registered_external_mode_ids(self) -> None:
        registry = ModeRegistry(
            (
                ModeDefinition(SessionMode.SIMPLE_CAPTURE.value, "Simple"),
                ModeDefinition("external_mode", "External Mode"),
            )
        )
        adapter = KLayoutSessionPathAdapter(
            _FakePya(folder="C:/tmp/demo", item="external_mode"),
            registry,
        )

        selection = adapter.select_new_session()

        self.assertIsInstance(selection.mode, SessionModeId)
        self.assertEqual("external_mode", selection.mode.value)

    def test_open_save_and_recent_paths_are_selected(self) -> None:
        adapter = KLayoutSessionPathAdapter(
            _FakePya(
                open_path="C:/tmp/a/session.json",
                save_path="C:/tmp/b/session.json",
                item="C:/tmp/a/session.json",
            )
        )

        opened = adapter.select_open_session()
        saved = adapter.select_save_as_destination()
        recent = adapter.select_recent_session((opened.path,))

        self.assertEqual("selected", opened.status)
        self.assertEqual("selected", saved.status)
        self.assertEqual("selected", recent.status)
        self.assertEqual(opened.path, recent.path)

    def test_cancelled_dialog_returns_cancelled_selection(self) -> None:
        adapter = KLayoutSessionPathAdapter(_FakePya())

        selection = adapter.select_open_session()

        self.assertEqual("cancelled", selection.status)

    def test_report_output_adapter_selects_folder(self) -> None:
        adapter = KLayoutReportOutputAdapter(_FakePya(folder="C:/tmp/reports"))

        selection = adapter.select_report_output_dir(Path("C:/tmp/default"))

        self.assertEqual("selected", selection.status)
        self.assertEqual(Path("C:/tmp/reports"), selection.path)

    def test_recipe_path_adapter_selects_open_save_and_attach_paths(self) -> None:
        adapter = KLayoutRecipePathAdapter(
            _FakePya(
                open_path="C:/tmp/recipes/input.json",
                save_path="C:/tmp/recipes/output.json",
            )
        )

        opened = adapter.select_open_recipe()
        saved = adapter.select_save_recipe_as()
        attached = adapter.select_attach_recipe()

        self.assertEqual(Path("C:/tmp/recipes/input.json"), opened.path)
        self.assertEqual(Path("C:/tmp/recipes/output.json"), saved.path)
        self.assertEqual(Path("C:/tmp/recipes/input.json"), attached.path)


class _FakePya:
    def __init__(
        self,
        folder: str = "",
        open_path: str = "",
        save_path: str = "",
        item: str = "simple_capture",
    ) -> None:
        self.QFileDialog = _FakeFileDialog(folder, open_path, save_path)
        self.QInputDialog = _FakeInputDialog(item)


class _FakeFileDialog:
    def __init__(self, folder: str, open_path: str, save_path: str) -> None:
        self._folder = folder
        self._open_path = open_path
        self._save_path = save_path

    def getExistingDirectory(self, parent, title: str, folder: str) -> str:  # noqa: N802
        return self._folder

    def getOpenFileName(  # noqa: N802
        self, parent, title: str, folder: str, filter_text: str
    ):
        return (self._open_path, filter_text)

    def getSaveFileName(  # noqa: N802
        self, parent, title: str, path: str, filter_text: str
    ):
        return (self._save_path, filter_text)


class _FakeInputDialog:
    def __init__(self, item: str) -> None:
        self._item = item

    def getItem(  # noqa: N802
        self,
        parent,
        title: str,
        label: str,
        items: tuple[str, ...],
        current: int,
        editable: bool,
    ):
        return (self._item, True)


if __name__ == "__main__":
    unittest.main()

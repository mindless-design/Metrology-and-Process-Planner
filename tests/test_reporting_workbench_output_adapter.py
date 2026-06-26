import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController
from metrology_process_planner.app.session_path_adapter import PathSelection
from metrology_process_planner.domains.session import ArtifactStatus
from metrology_process_planner.persistence.paths import SessionPaths
from tests.reporting_workbench_fixtures import document_with_artifact


class ReportingWorkbenchOutputAdapterTests(unittest.TestCase):
    def test_choose_output_updates_request_and_export_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir) / "session")
            selected = Path(temp_dir) / "chosen-reports"
            controller = ReportingWorkbenchController(
                output_adapter=_FakeOutputAdapter(selected),
            )
            controller.open_document(document_with_artifact(ArtifactStatus.MISSING), paths)

            chosen = controller.dispatch("choose_output")
            exported = controller.dispatch("export_pptx")

        self.assertEqual("success", chosen.status)
        self.assertEqual(str(selected), chosen.output_path)
        self.assertTrue(str(exported.output_path).startswith(str(selected)))

    def test_choose_output_cancel_is_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            controller = ReportingWorkbenchController(
                output_adapter=_FakeOutputAdapter(None),
            )
            controller.open_document(document_with_artifact(ArtifactStatus.MISSING), paths)
            before = controller.current_request

            chosen = controller.dispatch("choose_output")

        self.assertEqual("cancelled", chosen.status)
        self.assertIs(before, controller.current_request)


class _FakeOutputAdapter:
    def __init__(self, path: Path | None) -> None:
        self._path = path

    def select_report_output_dir(self, _current_dir: Path) -> PathSelection:
        if self._path is None:
            return PathSelection(message="cancelled")
        return PathSelection.selected(self._path)


if __name__ == "__main__":
    unittest.main()

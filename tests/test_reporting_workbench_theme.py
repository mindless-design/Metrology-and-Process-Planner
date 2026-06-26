import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.persistence.paths import SessionPaths
from tests.reporting_workbench_fixtures import document as base_document


class ReportingWorkbenchThemeTests(unittest.TestCase):
    def test_theme_selection_refreshes_request_and_header(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.reporting_workbench_controller.open_document(base_document(), paths)

            window = services.reporting_workbench_controller.current_window
            assert window is not None
            window["on_select_theme"]("dark")

            model = window["model"]
            request = services.reporting_workbench_controller.current_request
            assert request is not None
            self.assertEqual("dark", model.selected_theme_id)
            self.assertEqual("dark", request.theme_id)
            self.assertIn(("Theme", "dark"), model.header)


if __name__ == "__main__":
    unittest.main()

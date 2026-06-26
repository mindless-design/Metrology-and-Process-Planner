import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.mode_registry_config import (
    MODE_DEFINITION_DIRS_ENV,
    configured_mode_folders,
    load_configured_mode_registry,
)
from metrology_process_planner.domains.session import ModeDefinition, ModeRegistry
from tests.editor_render_fixtures import session_without_pending


class ModeRegistryConfigTests(unittest.TestCase):
    def test_configured_mode_folders_uses_environment_path_separator(self) -> None:
        folders = configured_mode_folders(
            {MODE_DEFINITION_DIRS_ENV: f"C:/modes-a{_pathsep()}C:/modes-b"}
        )

        self.assertEqual((Path("C:/modes-a"), Path("C:/modes-b")), folders)

    def test_load_configured_mode_registry_accumulates_modes_and_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "custom.json").write_text(
                json.dumps({"mode_id": "custom_review", "label": "Custom Review"}),
                encoding="utf-8",
            )
            missing = folder / "missing"

            result = load_configured_mode_registry((folder, missing))

        self.assertIn("custom_review", result.registry.mode_ids())
        self.assertTrue(any("Mode definition folder not found" in item for item in result.warnings))

    def test_bootstrap_diagnostics_reports_external_mode_load_warnings(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        services = build_app_services(
            mode_registry=registry,
            mode_load_warnings=("bad mode file",),
        )
        services.diagnostics_controller.set_active_session(session_without_pending())

        result = services.diagnostics_controller.open_current()

        rows = dict(result.summary_rows)
        self.assertIn("external_mode", rows["Loaded Modes"])
        self.assertEqual("bad mode file", rows["Mode Load Warnings"])

def _pathsep() -> str:
    import os

    return os.pathsep


if __name__ == "__main__":
    unittest.main()

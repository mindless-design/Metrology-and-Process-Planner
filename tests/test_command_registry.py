import unittest

from metrology_process_planner.app.commands import (
    DEFAULT_COMMANDS,
    CommandId,
    CoverageLane,
)


class CommandRegistryMetadataTests(unittest.TestCase):
    def test_every_command_id_has_one_spec(self) -> None:
        command_ids = [spec.command_id for spec in DEFAULT_COMMANDS]

        self.assertEqual(set(CommandId), set(command_ids))
        self.assertEqual(len(command_ids), len(set(command_ids)))

    def test_command_specs_have_stable_ui_selectors(self) -> None:
        for spec in DEFAULT_COMMANDS:
            with self.subTest(command_id=spec.command_id):
                self.assertTrue(spec.menu_item_name.startswith("mpp_"))
                self.assertEqual("tools_menu.metrology_process_planner", spec.menu_path)
                self.assertTrue(spec.title)
                self.assertTrue(spec.description.endswith("."))

    def test_command_specs_have_coverage_lanes(self) -> None:
        for spec in DEFAULT_COMMANDS:
            with self.subTest(command_id=spec.command_id):
                self.assertIsInstance(spec.coverage_lane, CoverageLane)


if __name__ == "__main__":
    unittest.main()


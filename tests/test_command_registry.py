import unittest

from metrology_process_planner.app.commands import (
    ALL_COMMANDS,
    MENU_COMMANDS,
    CommandId,
    CommandRegistry,
    CoverageLane,
    command_id_from_view_action,
)


class CommandRegistryMetadataTests(unittest.TestCase):
    def test_every_command_id_has_one_spec(self) -> None:
        command_ids = [spec.command_id for spec in ALL_COMMANDS]

        self.assertEqual(set(CommandId), set(command_ids))
        self.assertEqual(len(command_ids), len(set(command_ids)))

    def test_menu_commands_have_stable_ui_selectors(self) -> None:
        for spec in MENU_COMMANDS:
            with self.subTest(command_id=spec.command_id):
                self.assertTrue(spec.menu_item_name.startswith("mpp_"))
                self.assertEqual("tools_menu.metrology_process_planner", spec.menu_path)
                self.assertTrue(spec.title)
                self.assertTrue(spec.description.endswith("."))
                self.assertTrue(spec.appears_in_menu)

    def test_registry_covers_all_commands_but_menu_is_primary_subset(self) -> None:
        registry = CommandRegistry()

        self.assertEqual(set(CommandId), set(registry.specs))
        self.assertEqual(
            (
                CommandId.OPEN_SETUP_GUIDE,
                CommandId.OPEN_SESSION_EDITOR,
                CommandId.OPEN_RECIPE_EDITOR,
                CommandId.END_ACTIVE_SESSION,
                CommandId.OPEN_DIAGNOSTICS,
            ),
            tuple(spec.command_id for spec in MENU_COMMANDS),
        )

    def test_command_specs_have_coverage_lanes(self) -> None:
        for spec in ALL_COMMANDS:
            with self.subTest(command_id=spec.command_id):
                self.assertIsInstance(spec.coverage_lane, CoverageLane)

    def test_view_model_action_ids_normalize_to_typed_commands(self) -> None:
        self.assertEqual(CommandId.SAVE_RECIPE, command_id_from_view_action("SaveRecipe"))
        self.assertEqual(
            CommandId.ADD_PROCESS_STEP,
            command_id_from_view_action("AddProcessStep:patterned_deposition"),
        )
        self.assertEqual(
            CommandId.START_ORIGIN_POINT_CAPTURE,
            command_id_from_view_action("StartOriginPointCapture"),
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.workflows import RecipeEditorActionDispatcher


class RecipeEditorMaterialActionTests(unittest.TestCase):
    def test_add_material_marks_dirty_and_selects_new_card(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(_recipe(), "AddMaterial")

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.ADD_MATERIAL, result.command_id)
        self.assertEqual(("si", "oxide", "material"), _material_ids(result.recipe))
        self.assertEqual("material:material", result.selected_card_id)
        self.assertTrue(result.recipe.metadata["dirty"])

    def test_duplicate_material_marks_dirty_and_selects_copy(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _recipe(),
            "DuplicateMaterial:oxide",
        )

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.DUPLICATE_MATERIAL, result.command_id)
        self.assertEqual(("si", "oxide", "oxide_copy"), _material_ids(result.recipe))
        self.assertEqual("material:oxide_copy", result.selected_card_id)
        self.assertTrue(result.recipe.metadata["dirty"])

    def test_toggle_visibility_keeps_material_selected(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _recipe(),
            "ToggleMaterialVisibility:oxide",
        )

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.TOGGLE_MATERIAL_VISIBILITY, result.command_id)
        oxide = result.recipe.materials[1]
        self.assertFalse(oxide.visible)
        self.assertEqual("material:oxide", result.recipe.metadata["selected_card_id"])

    def test_find_usage_returns_inline_step_list_without_dirtying_recipe(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _recipe(),
            "FindMaterialUsage:oxide",
        )

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.FIND_MATERIAL_USAGE, result.command_id)
        self.assertIn("oxide-deposit", result.message)
        self.assertNotIn("dirty", result.recipe.metadata)

    def test_edit_material_updates_domain_fields_and_marks_dirty(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _recipe(),
            "EditMaterial:oxide:name:Field Oxide",
        )

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.EDIT_MATERIAL, result.command_id)
        self.assertEqual("Field Oxide", result.recipe.materials[1].name)
        self.assertEqual("material:oxide", result.selected_card_id)
        self.assertTrue(result.recipe.metadata["dirty"])

    def test_edit_material_updates_metadata_backed_detail_fields(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _recipe(),
            "EditMaterial:oxide:category:dielectric",
        )

        self.assertEqual("success", result.status)
        self.assertEqual(
            "dielectric",
            result.recipe.metadata["material_categories"]["oxide"],
        )

        notes = RecipeEditorActionDispatcher().dispatch(
            result.recipe,
            "EditMaterial:oxide:notes:Used for STI and gate dielectric",
        )

        self.assertEqual(
            "Used for STI and gate dielectric",
            notes.recipe.metadata["material_notes"]["oxide"],
        )

    def test_edit_material_rejects_bad_payload_modelessly(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(_recipe(), "EditMaterial:oxide")

        self.assertEqual("error", result.status)
        self.assertEqual(CommandId.EDIT_MATERIAL, result.command_id)
        self.assertIn("payload", result.message)


def _material_ids(recipe: ProcessRecipe) -> tuple[str, ...]:
    return tuple(material.id for material in recipe.materials)


def _recipe() -> ProcessRecipe:
    return ProcessRecipe(
        "recipe-materials",
        "Materials",
        (Material("si", "Silicon", "#aaa"), Material("oxide", "Oxide", "#88ccff")),
        (
            ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),
            ProcessStep("oxide-deposit", ProcessStepKind.BLANKET_DEPOSITION, "oxide"),
        ),
    )


if __name__ == "__main__":
    unittest.main()

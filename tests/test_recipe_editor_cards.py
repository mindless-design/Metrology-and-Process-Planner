import unittest

from metrology_process_planner.domains.process import (
    LayerReference,
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
    ThicknessSpec,
)
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter


class RecipeEditorCardsTests(unittest.TestCase):
    def test_recipe_editor_builds_tabs_cards_actions_and_preview(self) -> None:
        view_model = RecipeEditorPresenter().build(_recipe())

        self.assertEqual(
            (
                "Materials",
                "Process Steps",
                "Layers / Masks",
                "Preview / Summary",
                "Validation",
            ),
            view_model.tabs,
        )
        self.assertEqual("recipe-001", view_model.recipe_id)
        self.assertEqual("material:oxide", view_model.selected_card_id)
        self.assertEqual("unavailable", view_model.preview.status)
        self.assertIn("SaveRecipe", [action.action_id for action in view_model.header_actions])
        self.assertEqual(
            ("AddMaterial",),
            tuple(action.action_id for action in view_model.material_actions),
        )
        self.assertIn(
            "AddProcessStep:patterned_deposition",
            [template.action_id for template in view_model.step_templates],
        )

    def test_material_cards_show_usage_warning_badges_and_selection(self) -> None:
        view_model = RecipeEditorPresenter().build(_recipe())
        cards = {card.material_id: card for card in view_model.material_cards}

        self.assertEqual(2, cards["oxide"].used_by_step_count)
        self.assertEqual("dielectric", cards["oxide"].category)
        self.assertTrue(cards["oxide"].selected)
        self.assertEqual(1, cards["metal"].warning_count)

    def test_selected_material_detail_shows_editable_material_fields(self) -> None:
        view_model = RecipeEditorPresenter().build(_recipe())
        detail = view_model.selected_detail

        self.assertIsNotNone(detail)
        self.assertEqual("material:oxide", detail.card_id)
        self.assertEqual("material", detail.card_type)
        self.assertIn(("category", "Category", "dielectric"), _field_rows(detail))
        self.assertIn(("visible", "Visible", "yes"), _field_rows(detail))
        self.assertIn("Find Usage", [action.label for action in detail.actions])

    def test_step_cards_show_plain_language_summary_and_layer(self) -> None:
        view_model = RecipeEditorPresenter().build(_recipe())
        step = view_model.step_cards[1]

        self.assertEqual(2, step.step_number)
        self.assertEqual("Patterned deposition", step.operation_type)
        self.assertEqual("Gate", step.layer_label)
        self.assertEqual("80 nm target", step.thickness_summary)
        self.assertIn("where Gate is active", step.plain_language_summary)

    def test_selected_step_detail_shows_operation_specific_fields(self) -> None:
        recipe = ProcessRecipe(
            "recipe-003",
            "Selected Step",
            (Material("oxide", "Oxide", "#88ccff"),),
            (
                ProcessStep(
                    "step-pattern",
                    ProcessStepKind.PATTERNED_DEPOSITION,
                    "oxide",
                    ThicknessSpec(80, unit="nm"),
                    LayerReference("layout", 10, 0, "Gate"),
                    notes="Use gate mask.",
                ),
            ),
            metadata={"selected_card_id": "step:step-pattern"},
        )

        detail = RecipeEditorPresenter().build(recipe).selected_detail

        self.assertIsNotNone(detail)
        self.assertEqual("step:step-pattern", detail.card_id)
        self.assertIn(("kind", "Operation Type", "Patterned deposition"), _field_rows(detail))
        self.assertIn(("layer", "Layer / Mask", "Gate"), _field_rows(detail))
        self.assertIn(
            ("thickness", "Thickness / Depth / Plane", "80 nm target"),
            _field_rows(detail),
        )
        self.assertIn("Duplicate Step", [action.label for action in detail.actions])

    def test_layers_and_inline_validation_are_clickable_view_models(self) -> None:
        view_model = RecipeEditorPresenter().build(_recipe())

        self.assertEqual("Gate", view_model.layer_cards[0].label)
        self.assertEqual(("step-pattern",), view_model.layer_cards[0].used_by_step_ids)
        messages = {message.message for message in view_model.validation_messages}
        self.assertIn("Material metal is unused.", messages)
        unused = [
            message
            for message in view_model.validation_messages
            if "metal is unused" in message.message
        ][0]
        self.assertEqual("material:metal", unused.related_card_id)
        self.assertEqual("SelectRecipeCard:material:metal", unused.action_id)
        self.assertIn("assign it", unused.repair_suggestion)

    def test_summary_tab_tracks_unused_materials_and_disabled_steps(self) -> None:
        recipe = ProcessRecipe(
            "recipe-002",
            "Disabled Flow",
            (Material("si", "Silicon", "#aaa"),),
            (
                ProcessStep(
                    "note",
                    ProcessStepKind.ANNOTATION_ONLY,
                    parameters={"enabled": False},
                    notes="Review only.",
                ),
            ),
        )

        view_model = RecipeEditorPresenter().build(recipe)

        self.assertEqual(("si",), view_model.summary.unused_material_ids)
        self.assertEqual(("note",), view_model.summary.disabled_step_ids)
        self.assertEqual("1. Review only.", view_model.summary.lines[0])


def _recipe() -> ProcessRecipe:
    return ProcessRecipe(
        "recipe-001",
        "Gate Stack",
        (
            Material("oxide", "Oxide", "#88ccff"),
            Material("metal", "Gate Metal", "#ffcc00"),
        ),
        (
            ProcessStep(
                "step-blanket",
                ProcessStepKind.BLANKET_DEPOSITION,
                "oxide",
                ThicknessSpec(100, unit="nm"),
            ),
            ProcessStep(
                "step-pattern",
                ProcessStepKind.PATTERNED_DEPOSITION,
                "oxide",
                ThicknessSpec(80, unit="nm"),
                LayerReference("layout", 10, 0, "Gate"),
            ),
        ),
        metadata={
            "selected_card_id": "material:oxide",
            "material_categories": {"oxide": "dielectric", "metal": "metal"},
        },
    )


def _field_rows(detail):
    return tuple((field.key, field.label, field.value) for field in detail.fields)


if __name__ == "__main__":
    unittest.main()

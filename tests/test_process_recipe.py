import unittest

from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
    ProcessWindow,
    RecipeValidationService,
    ThicknessSpec,
)


class ProcessRecipeTests(unittest.TestCase):
    def test_valid_recipe_has_no_warnings(self) -> None:
        recipe = ProcessRecipe(
            id="demo",
            name="Demo",
            materials=(Material(id="oxide", name="Oxide", color="#99ccee"),),
            steps=(
                ProcessStep(
                    id="deposit-oxide",
                    kind=ProcessStepKind.BLANKET_DEPOSITION,
                    material_id="oxide",
                    thickness=ThicknessSpec(target=0.5, lower=0.45, upper=0.55),
                ),
            ),
        )

        self.assertEqual((), recipe.validate())

    def test_unknown_material_is_reported(self) -> None:
        recipe = ProcessRecipe(
            id="demo",
            name="Demo",
            materials=(Material(id="oxide", name="Oxide", color="#99ccee"),),
            steps=(
                ProcessStep(
                    id="deposit-metal",
                    kind=ProcessStepKind.BLANKET_DEPOSITION,
                    material_id="metal",
                    thickness=ThicknessSpec(target=0.2),
                ),
            ),
        )

        self.assertIn(
            "Step deposit-metal references unknown material metal.",
            recipe.validate(),
        )

    def test_recipe_round_trips_rich_editor_fields_and_fingerprint_is_stable(self) -> None:
        recipe = ProcessRecipe(
            id="demo",
            name="Demo",
            version="1.0",
            materials=(
                Material(
                    "oxide",
                    "Oxide",
                    "#99ccee",
                    category="dielectric",
                    hatch_style="dense",
                    physical_role="film",
                    notes="Gate oxide",
                ),
            ),
            steps=(
                ProcessStep(
                    id="deposit-oxide",
                    name="Deposit oxide",
                    kind=ProcessStepKind.BLANKET_DEPOSITION,
                    material_id="oxide",
                    thickness=ThicknessSpec(target=0.5),
                ),
            ),
            metadata={"owner": "unit"},
        )

        loaded = ProcessRecipe.from_dict(recipe.to_dict())

        self.assertEqual("dielectric", loaded.materials[0].category)
        self.assertEqual("Deposit oxide", loaded.steps[0].name)
        self.assertEqual(recipe.fingerprint(), loaded.fingerprint())
        self.assertEqual(1, loaded.minimal_summary()["step_count"])

    def test_structured_validation_reports_duplicates_windows_and_links(self) -> None:
        recipe = ProcessRecipe(
            id="demo",
            name="Demo",
            materials=(
                Material("oxide", "Oxide", "#99ccee"),
                Material("oxide", "Duplicate", "#ffffff"),
            ),
            steps=(
                ProcessStep(
                    id="deposit",
                    kind=ProcessStepKind.PATTERNED_DEPOSITION,
                    material_id="metal",
                    thickness=ThicknessSpec(target=0.5),
                ),
                ProcessStep(
                    id="deposit",
                    kind=ProcessStepKind.BLANKET_DEPOSITION,
                    material_id="oxide",
                ),
            ),
            process_windows=(ProcessWindow("etch", lower=2.0, target=1.0, upper=3.0),),
        )

        messages = RecipeValidationService().validate(recipe)
        by_id = {message.id: message for message in messages}

        self.assertEqual("blocking", by_id["material-duplicate-oxide"].severity)
        self.assertEqual("deposit", by_id["step-material-unknown-deposit-metal"].related_step_id)
        self.assertIn("step-layer-required-deposit", by_id)
        self.assertIn("window-etch-0", by_id)


if __name__ == "__main__":
    unittest.main()

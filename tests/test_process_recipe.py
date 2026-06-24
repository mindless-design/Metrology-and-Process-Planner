import unittest

from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
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


if __name__ == "__main__":
    unittest.main()


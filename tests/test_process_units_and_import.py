import unittest

from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
    RecipeValidationService,
    ThicknessSpec,
)
from metrology_process_planner.domains.process.materials import material_style, resolve_material
from metrology_process_planner.domains.process.recipe_import import import_recipe_table
from metrology_process_planner.domains.units import (
    UnitParseError,
    format_length,
    length_diagnostics,
    parse_length,
)


class ProcessUnitsAndImportTests(unittest.TestCase):
    def test_unit_parser_accepts_supported_spellings_and_equivalent_values(self) -> None:
        expected = parse_length("120 nm").value_um

        for value in ("0.12 um", "0.12 \u00b5m", "1200 A", "1200 \u00c5", "0.00012 mm"):
            parsed = parse_length(value, allow_plain_angstrom=True)
            self.assertAlmostEqual(expected, parsed.value_um)

        self.assertAlmostEqual(expected, parse_length({"value": 120, "unit": "nm"}).value_um)
        self.assertEqual("nm", parse_length("120 nm").display_unit)

    def test_unit_diagnostics_cover_invalid_and_legacy_unitless_values(self) -> None:
        legacy = parse_length(0.12, default_unit="um")

        self.assertEqual(0.12, legacy.value_um)
        self.assertEqual("um", legacy.display_unit)
        with self.assertRaises(UnitParseError):
            parse_length("5 furlongs")
        messages = length_diagnostics("-5 nm", allow_negative=False)
        self.assertEqual("LENGTH_NEGATIVE", messages[0].code)

    def test_auto_length_formatting_chooses_readable_units(self) -> None:
        self.assertEqual("120 nm", format_length(0.12, display_unit="auto"))
        self.assertEqual("1.2 mm", format_length(1200.0, display_unit="auto"))

    def test_material_library_resolves_aliases_and_unknown_style(self) -> None:
        oxide = resolve_material("silicon dioxide")
        unknown = resolve_material("mystery-film")

        self.assertEqual("SiO2", oxide.id)
        self.assertEqual("unknown", unknown.id)
        self.assertEqual("#ff4d4d", material_style("mystery-film")["fill"])

    def test_recipe_csv_import_normalizes_mixed_units_and_reports_rows(self) -> None:
        recipe, diagnostics = import_recipe_table(
            """step,operation,material,thickness,unit,target,stop,notes
1,substrate,Si,500,um,,,
2,deposit,oxide,120,nm,,,
3,etch,SiO2,80,nm,SiO2,Si,stop on silicon
4,deposit,mystery,1,furlong,,,
5,,Cu,20,nm,,,
"""
        )

        by_id = {step.id: step for step in recipe.steps}
        self.assertAlmostEqual(0.12, by_id["step-002"].thickness.target)
        self.assertEqual(("SiO2",), by_id["step-003"].target_material_ids)
        self.assertEqual(("Si",), by_id["step-003"].stop_material_ids)
        self.assertIn("SiO2", {material.id for material in recipe.materials})
        self.assertTrue(any(item.code == "RECIPE_IMPORT_UNSUPPORTED_UNIT" for item in diagnostics))
        self.assertTrue(any(item.row_number == 6 for item in diagnostics))

    def test_recipe_loads_legacy_unitless_thickness_as_micrometers(self) -> None:
        loaded = ProcessRecipe.from_dict(
            {
                "id": "legacy",
                "materials": [{"id": "oxide", "name": "Oxide", "color": "#99ccee"}],
                "steps": [
                    {
                        "id": "deposit-oxide",
                        "kind": "blanket_deposition",
                        "material_id": "oxide",
                        "thickness": {"target": 0.12},
                    }
                ],
            }
        )

        thickness = loaded.steps[0].thickness

        self.assertIsNotNone(thickness)
        self.assertEqual("um", thickness.unit)
        self.assertAlmostEqual(0.12, thickness.target)

    def test_recipe_normalizes_mixed_thickness_units(self) -> None:
        recipe = ProcessRecipe.from_dict(
            {
                "id": "mixed",
                "materials": [{"id": "oxide", "name": "Oxide", "color": "#99ccee"}],
                "steps": [
                    {
                        "id": "nm",
                        "kind": "blanket_deposition",
                        "material_id": "oxide",
                        "thickness": {"target": 120, "unit": "nm"},
                    },
                    {
                        "id": "angstrom",
                        "kind": "blanket_deposition",
                        "material_id": "oxide",
                        "thickness": {"target": "1200 \u00c5"},
                    },
                    {
                        "id": "mm",
                        "kind": "blanket_deposition",
                        "material_id": "oxide",
                        "thickness": {"target": 0.00012, "unit": "mm"},
                    },
                ],
            }
        )

        targets = [step.thickness.target for step in recipe.steps if step.thickness is not None]
        messages = RecipeValidationService().validate(recipe)

        self.assertFalse(any("unit" in message.message.lower() for message in messages))
        self.assertEqual(["um", "um", "um"], [step.thickness.unit for step in recipe.steps])
        for target in targets:
            self.assertAlmostEqual(0.12, target)

    def test_recipe_validation_flags_unsupported_thickness_unit(self) -> None:
        recipe = ProcessRecipe(
            id="bad-units",
            name="Bad units",
            materials=(Material("oxide", "Oxide", "#99ccee"),),
            steps=(
                ProcessStep(
                    id="deposit",
                    kind=ProcessStepKind.BLANKET_DEPOSITION,
                    material_id="oxide",
                    thickness=ThicknessSpec(1.0, unit="parsec"),
                ),
            ),
        )

        messages = RecipeValidationService().validate(recipe)

        self.assertTrue(any("Unsupported length unit" in message.message for message in messages))
        self.assertTrue(any(message.repair_suggestion for message in messages))


if __name__ == "__main__":
    unittest.main()

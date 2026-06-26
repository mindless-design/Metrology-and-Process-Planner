import unittest

from metrology_process_planner.domains.process import (
    CrossSectionProfile,
    MaterialInterval,
    ProcessFrame,
    SolverResult,
    StackColumn,
)
from metrology_process_planner.rendering.cross_section import (
    build_cross_section_scene,
    built_in_render_profile,
)
from tests.cross_section_rendering_fixtures import MATERIALS, simple_stack_result


class CrossSectionAxesUnitsTests(unittest.TestCase):
    def test_physical_scene_exposes_engineering_axes(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)

        metal = next(shape for shape in scene.material_shapes if shape.material_id == "metal")

        self.assertEqual("proportional_physical", scene.render_mode_id)
        self.assertEqual(metal.physical_bounds, metal.visual_bounds)
        self.assertTrue(scene.scale_bars)
        self.assertEqual("x", scene.axes[0]["orientation"])
        self.assertTrue(scene.axes[0]["ticks"])
        self.assertIn(scene.physical_units, scene.axes[0]["label"])

    def test_scene_axes_and_labels_format_canonical_micrometers(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(_thin_film_result(), profile, materials=MATERIALS)

        self.assertEqual("um", scene.coordinate_frame["canonical_units"])
        self.assertEqual("nm", scene.physical_units)
        self.assertTrue(all(axis["unit"] == "nm" for axis in scene.axes))
        self.assertTrue(any("120 nm" in label.text for label in scene.labels))


def _thin_film_result() -> SolverResult:
    return SolverResult(
        (
            ProcessFrame(
                "thin-film",
                "Thin film",
                CrossSectionProfile(
                    (
                        StackColumn(
                            0.0,
                            (
                                MaterialInterval("si", 0.0, 1.0),
                                MaterialInterval("oxide", 1.0, 1.12),
                            ),
                        ),
                    )
                ),
            ),
        )
    )


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.rendering.cross_section import (
    CrossSectionOutputSpec,
    SvgCrossSectionRenderer,
    build_cross_section_scene,
    build_render_artifact_record,
    built_in_render_profile,
)
from metrology_process_planner.reporting.formatting import figure_caption
from metrology_process_planner.reporting.gallery import gallery_figures
from metrology_process_planner.reporting.models import ArtifactSummary
from tests.cross_section_rendering_fixtures import (
    MATERIALS,
    profilometry_surface_result,
    simple_stack_result,
)

if __name__ == "__main__":
    unittest.main()


class CrossSectionMeasurementAnnotationTests(unittest.TestCase):
    def test_scene_extracts_measurement_annotations_from_geometry(self) -> None:
        profile = built_in_render_profile("profilometry_surface_profile")
        scene = build_cross_section_scene(
            profilometry_surface_result(),
            profile,
            materials=MATERIALS,
        )

        measurements = {item.kind: item for item in scene.measurement_annotations}

        self.assertAlmostEqual(50.0, measurements["step_height"].value)
        self.assertEqual("nm", measurements["step_height"].unit)
        self.assertEqual("50 nm", measurements["step_height"].formatted_value)
        self.assertTrue(measurements["layer_thickness"].physical_span)

    def test_svg_backend_renders_measurement_dimension_arrows(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)

        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "cross.svg"
            result = SvgCrossSectionRenderer().render(
                scene,
                CrossSectionOutputSpec(output_path=str(target), artifact_id="artifact-001"),
            )
            svg = target.read_text(encoding="utf-8")

        self.assertIn('marker-start="url(#arrow)"', svg)
        self.assertIn("Oxide thickness", svg)
        self.assertTrue(result.render_metadata["measurement_annotations"])

    def test_svg_backend_exports_axis_and_result_metadata(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)

        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "cross.svg"
            result = SvgCrossSectionRenderer().render(
                scene,
                CrossSectionOutputSpec(output_path=str(target), artifact_id="artifact-axes"),
            )
            svg = target.read_text(encoding="utf-8")

        self.assertIn(f"x distance ({scene.physical_units})", svg)
        self.assertIn(f"height ({scene.physical_units})", svg)
        self.assertEqual("artifact-axes", result.artifact_id)
        self.assertEqual("engineering_dark", result.render_metadata["theme_id"])

    def test_report_caption_uses_cross_section_measurement_summary(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)
        artifact = build_render_artifact_record(
            "capture",
            "cap-001",
            "cross_section_image",
            "cross_section",
            "process/cross.svg",
            scene,
        )
        summary = ArtifactSummary(
            artifact.id,
            artifact.label,
            artifact.type,
            artifact.owner.role,
            artifact.status.value,
            artifact.relative_path,
            artifact.owner.owner_type,
            artifact.owner.owner_id,
            extensions=dict(artifact.extensions or {}),
        )

        figure = gallery_figures((summary,))[0]

        self.assertIn("Oxide thickness", figure.notes)
        self.assertIn("Oxide thickness", figure_caption(figure))

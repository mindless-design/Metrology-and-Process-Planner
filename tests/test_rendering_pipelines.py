import unittest

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.process import (
    CrossSectionProfile,
    Material,
    MaterialInterval,
    StackColumn,
)
from metrology_process_planner.domains.session import CaptureGeometry, CaptureRecord
from metrology_process_planner.rendering import (
    CanvasSpec,
    CanvasTransform,
    DrawingScene,
    DrawingStyle,
    LineMark,
    TextMark,
    build_cross_section_drawing_scene,
    build_layout_annotation_scene,
    render_scene_to_svg,
    scene_from_dict,
    scene_to_dict,
)
from metrology_process_planner.rendering.primitives import CanvasPoint, RectangleMark
from tests.artifact_helpers import capture_crop_artifact


class RenderingPipelineTests(unittest.TestCase):
    def test_canvas_transform_maps_y_axis_down(self) -> None:
        transform = CanvasTransform(Box(0, 0, 10, 10), CanvasSpec(100, 80))

        top_center = transform.map_point(Point(5, 10))
        bottom_center = transform.map_point(Point(5, 0))

        self.assertEqual(CanvasPoint(50, 0), top_center)
        self.assertEqual(CanvasPoint(50, 80), bottom_center)

    def test_layout_annotation_scene_contains_measurement_markup(self) -> None:
        capture = _capture_with_measurement()

        scene = build_layout_annotation_scene(capture, capture_crop_artifact())
        line = next(mark for mark in scene.primitives if isinstance(mark, LineMark))

        self.assertEqual("layout_annotation", scene.role)
        self.assertEqual(800, scene.canvas.width_px)
        self.assertEqual(600, scene.canvas.height_px)
        self.assertEqual("images/cap-001.png", scene.image_layers[0].path)
        self.assertEqual(CanvasPoint(80, 480), line.start)
        self.assertAlmostEqual(720, line.end.x)
        self.assertAlmostEqual(120, line.end.y)
        self.assertEqual("#00aaee", line.style.stroke)
        self.assertEqual("arrow", line.end_marker)

    def test_cross_section_scene_contains_material_regions_and_legend(self) -> None:
        scene = build_cross_section_drawing_scene(
            _profile(),
            (
                Material(id="si", name="Silicon", color="#999999"),
                Material(id="ox", name="Oxide", color="#88ccff"),
            ),
            scene_id="cross-001",
            title="Etch profile",
        )

        rectangles = [mark for mark in scene.primitives if isinstance(mark, RectangleMark)]
        labels = [mark for mark in scene.primitives if isinstance(mark, TextMark)]

        self.assertEqual("cross_section", scene.role)
        self.assertEqual("#999999", rectangles[0].style.fill)
        self.assertTrue(any(label.text == "Etch profile" for label in labels))
        self.assertTrue(any(label.text == "ox" for label in labels))

    def test_scene_serializes_and_renders_svg_with_escaped_text(self) -> None:
        scene = DrawingScene(
            id="svg-001",
            role="test",
            canvas=CanvasSpec(100, 50),
            primitives=(
                LineMark(
                    start=CanvasPoint(1, 2),
                    end=CanvasPoint(8, 9),
                    style=DrawingStyle(stroke="#123456"),
                    end_marker="arrow",
                ),
                TextMark(
                    position=CanvasPoint(10, 20),
                    text="A < B & C",
                    style=DrawingStyle(stroke="#111111", fill="#111111"),
                ),
            ),
        )

        loaded = scene_from_dict(scene_to_dict(scene))
        svg = render_scene_to_svg(loaded)

        self.assertIn('marker-end="url(#arrow)"', svg)
        self.assertIn("A &lt; B &amp; C", svg)
        self.assertEqual(svg, render_scene_to_svg(loaded))


def _capture_with_measurement() -> CaptureRecord:
    measurement = MeasurementRecord(
        id="meas-001",
        label="Gate CD",
        start=Point(1, 2),
        end=Point(9, 8),
        annotation_color="#00aaee",
        line_weight=3.0,
    )
    return CaptureRecord(
        id="cap-001",
        label="Site 1",
        geometry=CaptureGeometry.box(Box(0, 0, 10, 10)),
        created_at="2026-06-23T20:00:00Z",
        measurements=(measurement,),
    )


def _profile() -> CrossSectionProfile:
    return CrossSectionProfile(
        columns=(
            StackColumn(
                x=0.0,
                intervals=(
                    MaterialInterval(material_id="si", z_min=0.0, z_max=1.0),
                    MaterialInterval(material_id="ox", z_min=1.0, z_max=2.0),
                ),
            ),
            StackColumn(
                x=1.0,
                intervals=(
                    MaterialInterval(material_id="si", z_min=0.0, z_max=0.5),
                    MaterialInterval(material_id="ox", z_min=0.5, z_max=2.0),
                ),
            ),
        )
    )


if __name__ == "__main__":
    unittest.main()

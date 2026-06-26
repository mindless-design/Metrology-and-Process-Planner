import unittest

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import CaptureGeometry, SessionMode
from metrology_process_planner.rendering.coordinates import LayoutToImageTransform
from metrology_process_planner.rendering.primitives import CanvasPoint
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    add_point_feature,
    arm_inner_feature_capture,
    ellipsometry_request,
    profilometry_request,
    save_composite_capture,
)
from tests.compound_capture_fixtures import pending_parent


class CaptureGeometryMetadataPipelineTests(unittest.TestCase):
    def test_box_geometry_exports_primary_center_and_extents(self) -> None:
        geometry = CaptureGeometry.box(Box(160, 250, 100, 200))

        primary = geometry.to_dict()["primary"]

        self.assertEqual({"left": 100, "bottom": 200, "right": 160, "top": 250}, primary["bounds"])
        self.assertEqual({"x": 130, "y": 225}, primary["center"])
        self.assertEqual(60, primary["width"])
        self.assertEqual(50, primary["height"])
        self.assertEqual("global", primary["coordinate_mode"])

    def test_line_and_point_features_export_complete_geometry(self) -> None:
        line_session = arm_inner_feature_capture(
            pending_parent(SessionMode.PROFILOMETRY_PLANNER),
            "pending-001",
            profilometry_request(),
        )
        line_session = add_line_feature(
            line_session,
            "pending-001",
            Point(1, 2),
            Point(9, 8),
            profilometry_request(),
        )
        saved = save_composite_capture(
            line_session,
            SaveCompositeCaptureCommand("pending-001", "Profile Site 001"),
        ).session

        geometry = saved.captures[0].geometry.features[0]["geometry"]

        self.assertEqual({"x": 5, "y": 5}, geometry["midpoint"])
        self.assertAlmostEqual(10.0, geometry["length"])
        self.assertEqual("primary", saved.captures[0].geometry.features[0]["parent_geometry_id"])

        point_capture = self._saved_point_capture()

        self.assertEqual({"x": 4, "y": 4}, point_capture.geometry.features[0]["geometry"]["point"])

    def test_layout_to_image_transform_maps_bounds_center_and_origin(self) -> None:
        transform = LayoutToImageTransform(Box(100, 200, 160, 250), 600, 500)

        self.assertEqual(CanvasPoint(300, 250), transform.layout_point_to_pixel(Point(130, 225)))
        self.assertEqual(CanvasPoint(0, 500), transform.layout_point_to_pixel(Point(100, 200)))
        self.assertEqual(CanvasPoint(600, 0), transform.layout_point_to_pixel(Point(160, 250)))

        origin_transform = LayoutToImageTransform(
            Box(0, 0, 60, 50),
            600,
            500,
            origin_ref=Point(100, 200),
        )
        self.assertEqual(
            CanvasPoint(300, 250),
            origin_transform.layout_point_to_pixel(Point(130, 225)),
        )
        self.assertEqual(
            Point(130, 225),
            origin_transform.pixel_point_to_layout(CanvasPoint(300, 250)),
        )

    def _saved_point_capture(self):
        point_session = arm_inner_feature_capture(
            pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
            "pending-001",
            ellipsometry_request(),
        )
        point_session = add_point_feature(
            point_session,
            "pending-001",
            Point(4, 4),
            ellipsometry_request(),
        )
        return save_composite_capture(
            point_session,
            SaveCompositeCaptureCommand("pending-001", "Film Site 001"),
        ).session.captures[0]


if __name__ == "__main__":
    unittest.main()

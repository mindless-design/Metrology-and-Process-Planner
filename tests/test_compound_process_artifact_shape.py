import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode, built_in_mode_registry
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


class CompoundProcessArtifactShapeTests(unittest.TestCase):
    def test_builtin_modes_declare_all_process_placeholder_roles(self) -> None:
        registry = built_in_mode_registry()

        self.assertIn(
            "full_stack_compressed_image",
            registry.definition("profilometry_planner").artifacts.roles_on_capture_save(),
        )
        self.assertIn(
            "film_thickness_summary",
            registry.definition("ellipsometry_planner").artifacts.roles_on_capture_save(),
        )

    def test_profile_extension_uses_line_feature_and_output_placeholders(self) -> None:
        result = save_composite_capture(
            _pending_profile_session(),
            SaveCompositeCaptureCommand("pending-001", "Profile Site 01"),
        )
        capture = result.session.captures[0]
        extension = capture.extensions["profilometry"]

        self.assertEqual("feat-001", extension["line_feature_id"])
        self.assertEqual({"stack_change_windows": [], "step_heights": []}, extension["outputs"])
        self.assertIn("capture-cap-001-full_stack_compressed_image", result.session.artifacts)
        self.assertIn("full_stack_compressed_image", capture.artifact_refs)

    def test_point_extension_uses_point_feature_and_output_placeholders(self) -> None:
        result = save_composite_capture(
            _pending_point_session(),
            SaveCompositeCaptureCommand("pending-001", "Film Site 01"),
        )
        capture = result.session.captures[0]
        extension = capture.extensions["ellipsometry"]

        self.assertEqual("feat-001", extension["point_feature_id"])
        self.assertEqual([], extension["point_stack"])
        self.assertIn("capture-cap-001-film_thickness_summary", result.session.artifacts)
        self.assertIn("film_thickness_summary", capture.artifact_refs)


def _pending_profile_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.PROFILOMETRY_PLANNER),
        "pending-001",
        profilometry_request(),
    )
    return add_line_feature(
        session,
        "pending-001",
        Point(1, 1),
        Point(9, 9),
        profilometry_request(),
    )


def _pending_point_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
        "pending-001",
        ellipsometry_request(),
    )
    return add_point_feature(session, "pending-001", Point(5, 5), ellipsometry_request())


if __name__ == "__main__":
    unittest.main()

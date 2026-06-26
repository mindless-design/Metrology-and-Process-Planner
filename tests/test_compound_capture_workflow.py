import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.modes.mode_output_policies import ProcessPolicy
from metrology_process_planner.domains.modes.mode_policies import (
    CaptureSequenceDefinition,
)
from metrology_process_planner.domains.modes.mode_registry import (
    ModeDefinition,
    built_in_mode_registry,
)
from metrology_process_planner.domains.session import (
    CanvasWorkflowState,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    add_point_feature,
    arm_inner_feature_capture,
    begin_compound_capture,
    ellipsometry_request,
    profilometry_request,
    save_composite_capture,
)
from tests.compound_capture_fixtures import base_session, pending_parent


class CompoundCaptureWorkflowTests(unittest.TestCase):
    def test_process_aware_modes_are_registered_and_valid(self) -> None:
        registry = built_in_mode_registry()

        self.assertIn("profilometry_planner", registry.mode_ids())
        self.assertIn("ellipsometry_planner", registry.mode_ids())
        self.assertEqual((), registry.validation_warnings())
        self.assertEqual(
            "site_then_line",
            registry.definition("profilometry_planner").capture.primitive_type,
        )
        self.assertEqual(
            "point_stack",
            registry.definition("ellipsometry_planner").process.solver_operation,
        )

    def test_invalid_compound_mode_definition_warns(self) -> None:
        definition = ModeDefinition(
            "bad_compound",
            "Bad Compound",
            capture=registry_capture("site_then_point", ("site_box",), "line"),
            process=registry_process("line_profile"),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("compound modes must declare" in warning for warning in warnings))
        self.assertTrue(any("solver operation should match" in warning for warning in warnings))

    def test_site_then_line_saves_composite_with_placeholders_and_warning(self) -> None:
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.PROFILOMETRY_PLANNER),
            "pending-001",
            profilometry_request(),
        )
        session = add_line_feature(
            session,
            "pending-001",
            Point(1, 2),
            Point(9, 8),
            profilometry_request(),
            {"target": 5.0, "lsl": 1.0, "usl": 10.0},
        )

        result = save_composite_capture(
            session,
            SaveCompositeCaptureCommand("pending-001", "Profile Site 01"),
        )
        loaded = SessionRecord.from_dict(result.session.to_dict())
        capture = loaded.captures[0]

        self.assertEqual("site_plus_line", capture.type)
        self.assertEqual("profilometry_site", capture.role)
        self.assertEqual("profilometry_line", capture.geometry.features[0]["role"])
        self.assertEqual("PROCESS_RECIPE_MISSING", loaded.warnings[0].code)
        self.assertIn("capture-cap-001-line_annotation", loaded.artifacts)
        self.assertIn("capture-cap-001-profile_image", loaded.artifacts)
        self.assertEqual((), loaded.pending_captures)
        self.assertEqual(CanvasWorkflowState.SAVED, loaded.canvas_objects[0].workflow_state)
        self.assertEqual(CanvasWorkflowState.SAVED, loaded.canvas_objects[1].workflow_state)

    def test_site_then_point_saves_composite_with_stack_placeholders(self) -> None:
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
            "pending-001",
            ellipsometry_request(),
        )
        session = add_point_feature(
            session,
            "pending-001",
            Point(4, 4),
            ellipsometry_request(),
        )

        result = save_composite_capture(
            session,
            SaveCompositeCaptureCommand("pending-001", "Film Site 01"),
        )
        capture = result.session.captures[0]

        self.assertEqual("site_plus_point", capture.type)
        self.assertEqual("ellipsometry_point", capture.geometry.features[0]["role"])
        self.assertIn("capture-cap-001-point_annotation", result.session.artifacts)
        self.assertIn("capture-cap-001-stack_image", result.session.artifacts)
        self.assertIn("capture-cap-001-point_stack_table", result.session.artifacts)
        self.assertEqual("point_stack", result.session.process_outputs[0].output_type)

    def test_child_geometry_must_be_inside_parent(self) -> None:
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.PROFILOMETRY_PLANNER),
            "pending-001",
            profilometry_request(),
        )

        with self.assertRaisesRegex(ValueError, "inside the parent"):
            add_line_feature(
                session,
                "pending-001",
                Point(-1, 2),
                Point(9, 8),
                profilometry_request(),
            )

        point_session = arm_inner_feature_capture(
            pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
            "pending-001",
            ellipsometry_request(),
        )
        with self.assertRaisesRegex(ValueError, "inside the parent"):
            add_point_feature(point_session, "pending-001", Point(20, 20), ellipsometry_request())

    def test_begin_compound_capture_sets_workflow_state(self) -> None:
        session = begin_compound_capture(
            base_session(SessionMode.PROFILOMETRY_PLANNER),
            profilometry_request(),
        )

        self.assertTrue(session.workflow.active)
        self.assertEqual("site_then_line:parent", session.workflow.stage)
        self.assertEqual("site_box", session.workflow.active_primitive)


def registry_capture(
    primitive_type: str,
    primitives: tuple[str, ...],
    inner_kind: str,
) -> CaptureSequenceDefinition:
    return CaptureSequenceDefinition(
        primitive_type=primitive_type,
        supported_primitives=primitives,
        inner_feature_kind=inner_kind,
    )


def registry_process(operation: str) -> ProcessPolicy:
    return ProcessPolicy("recommended", operation)


if __name__ == "__main__":
    unittest.main()

import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.workflows import (
    DiscardCompositeCommand,
    ExitCompositeCommand,
    RetakeInnerFeatureCommand,
    RetakeParentCommand,
    discard_composite_capture,
    exit_composite_capture,
    retake_inner_feature,
    retake_parent_capture,
)
from metrology_process_planner.workflows.compound_capture import (
    add_line_feature,
    arm_inner_feature_capture,
    profilometry_request,
)
from tests.compound_capture_fixtures import pending_parent


class CompoundReviewCommandTests(unittest.TestCase):
    def test_review_workflows_accept_typed_commands(self) -> None:
        session = _pending_profile()

        retake_inner = retake_inner_feature(
            session,
            RetakeInnerFeatureCommand("pending-001"),
        )
        retake_parent = retake_parent_capture(
            session,
            RetakeParentCommand("pending-001"),
        )
        discarded = discard_composite_capture(
            session,
            DiscardCompositeCommand("pending-001"),
        )
        exited = exit_composite_capture(session, ExitCompositeCommand("pending-001"))

        self.assertEqual(("canvas-parent",), tuple(item.id for item in retake_inner.canvas_objects))
        self.assertEqual("site_then_line:parent", retake_parent.workflow.stage)
        self.assertEqual((), discarded.pending_captures)
        self.assertFalse(exited.workflow.active)


def _pending_profile():
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


if __name__ == "__main__":
    unittest.main()

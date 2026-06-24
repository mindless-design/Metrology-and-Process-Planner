import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    add_point_feature,
    arm_inner_feature_capture,
    ellipsometry_request,
    profilometry_request,
    save_composite_capture,
)
from metrology_process_planner.workflows.editor import (
    SessionDocumentBuilder,
    SessionDocumentStore,
)
from tests.compound_capture_fixtures import pending_parent


class CompoundSessionReloadTests(unittest.TestCase):
    def test_saved_profilometry_composite_reload_restores_editor_canvas_indexes(self) -> None:
        reloaded = _save_and_reload(_saved_profile_session())

        capture = reloaded.session.captures[0]
        extension = capture.extensions["profilometry"]

        capture_item = reloaded.items_by_id["capture:cap-001"]
        feature_item = reloaded.items_by_id["feature:feat-001"]

        self.assertEqual(("canvas-parent", "canvas-001"), capture_item.canvas_object_ids)
        self.assertEqual(("canvas-001",), feature_item.canvas_object_ids)
        self.assertEqual("feature:feat-001", reloaded.canvas_object_to_item_id["canvas-001"])
        self.assertEqual("process_context.active", extension["process_context_ref"])
        self.assertEqual(
            "capture-cap-001-line_annotation",
            capture.artifact_refs["line_annotation"],
        )
        self.assertIn("warn-cap-001-missing-recipe", capture.warning_ids)

    def test_saved_ellipsometry_composite_reload_restores_editor_canvas_indexes(self) -> None:
        reloaded = _save_and_reload(_saved_point_session())

        capture = reloaded.session.captures[0]
        extension = capture.extensions["ellipsometry"]

        capture_item = reloaded.items_by_id["capture:cap-001"]
        feature_item = reloaded.items_by_id["feature:feat-001"]

        self.assertEqual(("canvas-parent", "canvas-001"), capture_item.canvas_object_ids)
        self.assertEqual(("canvas-001",), feature_item.canvas_object_ids)
        self.assertEqual("feature:feat-001", reloaded.canvas_object_to_item_id["canvas-001"])
        self.assertEqual("process_context.active", extension["process_context_ref"])
        self.assertEqual(
            "capture-cap-001-point_annotation",
            capture.artifact_refs["point_annotation"],
        )
        self.assertIn("warn-cap-001-missing-recipe", capture.warning_ids)


def _save_and_reload(session):
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = SessionPaths.for_folder(Path(temp_dir))
        store = SessionDocumentStore()
        document = SessionDocumentBuilder().build(session, raw_payload=session.to_dict())
        store.save(document, paths)
        return store.load(paths.folder)


def _saved_profile_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.PROFILOMETRY_PLANNER),
        "pending-001",
        profilometry_request(),
    )
    session = add_line_feature(
        session,
        "pending-001",
        Point(1, 1),
        Point(9, 9),
        profilometry_request(),
    )
    return save_composite_capture(
        session,
        SaveCompositeCaptureCommand("pending-001", "Profile Site 01"),
    ).session


def _saved_point_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
        "pending-001",
        ellipsometry_request(),
    )
    session = add_point_feature(session, "pending-001", Point(5, 5), ellipsometry_request())
    return save_composite_capture(
        session,
        SaveCompositeCaptureCommand("pending-001", "Film Site 01"),
    ).session


if __name__ == "__main__":
    unittest.main()

"""Characterization tests for saved-capture child measurement workflow."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    ModeDefinition,
    ModeRegistry,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    SessionDocumentStore,
    SessionRenderBridge,
)
from metrology_process_planner.workflows.measurement_workflow import add_pending_measurement_line
from tests.editor_render_fixtures import FakeRasterizer
from tests.measurement_child_fixtures import (
    document_with_pending_measurement,
    measurement_metadata_edits,
    measurement_svg_path,
    saved_capture_session,
    saved_measurement_document,
)


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class MeasurementChildWorkflowTestsPart1(unittest.TestCase):
    def test_shift_drag_line_adds_pending_measurement_under_active_parent(self) -> None:
        engine = CanvasInteractionEngine()
        context = engine.arm_line_capture(InteractionContext(), "canvas-cap")

        started = engine.start_drag(saved_capture_session(), context, Point(1, 1), True)
        released = engine.release_drag(started.session, started.context, Point(4, 1), True)

        measurement = released.session.captures[0].measurements[0]
        line = released.session.canvas_objects[1]
        parent = released.session.canvas_objects[0]
        self.assertEqual("meas-001", measurement.id)
        self.assertEqual("pending", measurement.metadata["workflow_state"])
        self.assertEqual("meas-001", line.record_id)
        self.assertEqual(CanvasObjectType.MEASUREMENT, line.object_type)
        self.assertEqual("canvas-cap", line.parent_id)
        self.assertIn(CanvasVisualFlag.ACTIVE_PARENT, parent.visual_state)

    def test_repeated_pending_measurements_use_stable_unique_ids_before_save(self) -> None:
        first = add_pending_measurement_line(
            saved_capture_session(),
            "canvas-cap",
            Point(1, 1),
            Point(4, 1),
        )
        second = add_pending_measurement_line(
            first,
            "canvas-cap",
            Point(1, 2),
            Point(4, 2),
        )

        measurement_ids = tuple(
            measurement.id for measurement in second.captures[0].measurements
        )
        canvas_record_ids = tuple(
            item.record_id
            for item in second.canvas_objects
            if item.object_type is CanvasObjectType.MEASUREMENT
        )

        self.assertEqual(("meas-001", "meas-002"), measurement_ids)
        self.assertEqual(("meas-001", "meas-002"), canvas_record_ids)

    def test_add_measurement_then_save_promotes_child_measurement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = SessionDocumentBuilder().build(saved_capture_session())
            dispatcher = EditorActionDispatcher(
                paths=paths,
                render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
            )
            armed = dispatcher.dispatch(
                document,
                EditorAction(EditorActionType.ADD_MEASUREMENT, "Add", "capture:cap-001"),
            )
            dirty = measurement_metadata_edits(
                document_with_pending_measurement(armed.document.session)
            )

            saved = dispatcher.dispatch(dirty, EditorAction(EditorActionType.SAVE_EDITS, "Save"))
            reloaded = SessionDocumentStore().load(paths.folder)
            svg_path = Path(temp_dir) / measurement_svg_path(saved.document.session)
            svg_exists = svg_path.exists()

        measurement = saved.document.session.captures[0].measurements[0]
        canvas_object = saved.document.session.canvas_objects[1]
        self.assertEqual("success", saved.status)
        self.assertEqual("saved", measurement.metadata["workflow_state"])
        self.assertEqual("cd", measurement.metadata["measurement_type"])
        self.assertEqual("Gate CD", measurement.label)
        self.assertEqual(3.0, measurement.target)
        self.assertEqual(2.5, measurement.lower_spec_limit)
        self.assertEqual(3.5, measurement.upper_spec_limit)
        self.assertEqual("outer_edges", measurement.edge_detection_convention)
        self.assertEqual("#00aaee", measurement.annotation_color)
        self.assertEqual(4.0, measurement.line_weight)
        self.assertEqual(CanvasWorkflowState.SAVED, canvas_object.workflow_state)
        self.assertIn("annotation", measurement.artifact_refs)
        self.assertIn("measurement_detail", measurement.artifact_refs)
        self.assertIn("measurement_annotation_svg", measurement.artifact_refs)
        self.assertTrue(svg_exists)
        self.assertIn("measurement:meas-001", saved.document.items_by_id)
        self.assertEqual("saved", saved.document.items_by_id["measurement:meas-001"].status)
        self.assertFalse(saved.document.session.warnings)
        self.assertIn("capture:cap-001", reloaded.items_by_id)
        self.assertIn("measurement:meas-001", reloaded.items_by_id)
        self.assertEqual(2, len(reloaded.session.canvas_objects))

    def test_regenerate_measurement_annotation_action_refreshes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            dispatcher = EditorActionDispatcher(
                paths=paths,
                render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
            )

            result = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_ARTIFACT,
                    "Regenerate",
                    "measurement:meas-001",
                ),
            )
            svg_path = Path(temp_dir) / measurement_svg_path(result.document.session)
            svg_exists = svg_path.exists()

        self.assertEqual("success", result.status)
        self.assertTrue(svg_exists)
        measurement = result.document.session.captures[0].measurements[0]
        roles = {
            artifact.role
            for artifact in result.document.items_by_id["measurement:meas-001"].artifact_refs
        }
        self.assertIn("measurement_detail", measurement.artifact_refs)
        self.assertIn("measurement_annotation_svg", roles)

"""Fixtures for child measurement workflow tests."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    SessionRenderBridge,
    mark_metadata_edit,
)
from metrology_process_planner.workflows.measurement_workflow import add_pending_measurement_line
from tests.editor_render_fixtures import FakeRasterizer


def measurement_metadata_edits(document):
    edits = (
        ("label", "Gate CD"),
        ("target", "3.0"),
        ("lower_spec_limit", "2.5"),
        ("upper_spec_limit", "3.5"),
        ("notes", "Reviewed"),
        ("edge_detection_convention", "outer_edges"),
        ("annotation_color", "#00aaee"),
        ("line_weight", "4.0"),
    )
    for field, value in edits:
        document = mark_metadata_edit(document, "measurement:meas-001", field, value)
    return document


def measurement_svg_path(session: SessionRecord) -> str:
    measurement = session.captures[0].measurements[0]
    artifact_id = measurement.artifact_refs["measurement_annotation_svg"]
    return str(session.artifacts[artifact_id].relative_path)


def document_with_pending_measurement(session):
    updated = add_pending_measurement_line(session, "canvas-cap", Point(1, 1), Point(4, 1))
    return SessionDocumentBuilder().build(updated, raw_payload=updated.to_dict())


def saved_measurement_document(paths: SessionPaths):
    document = document_with_pending_measurement(saved_capture_session())
    document = measurement_metadata_edits(document)
    dispatcher = EditorActionDispatcher(
        paths=paths,
        render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
    )
    return dispatcher.dispatch(document, EditorAction(EditorActionType.SAVE_EDITS, "Save")).document


def saved_capture_session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        captures=(
            CaptureRecord(
                "cap-001",
                "Site",
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                "2026-06-23T20:00:00Z",
            ),
        ),
        canvas_objects=(
            CanvasObject(
                "canvas-cap",
                "session-001",
                "cap-001",
                CanvasObjectType.SITE_BOX,
                None,
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                CanvasWorkflowState.SAVED,
                visual_state=(CanvasVisualFlag.SELECTED,),
            ),
        ),
    )

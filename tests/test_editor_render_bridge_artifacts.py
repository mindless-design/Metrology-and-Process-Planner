import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DrawingOwnerRef,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    RenderRefreshResult,
    RenderTarget,
    SessionDocumentBuilder,
    select_item,
)
from tests.editor_render_fixtures import session


class _RecordingRenderBridge:
    def __init__(self) -> None:
        self.requests = ()

    def refresh(self, source, request):
        self.requests = self.requests + (request,)
        return RenderRefreshResult("success", source)

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class EditorRenderBridgeArtifactTestsPart1(unittest.TestCase):
    def test_regenerate_selected_capture_artifact_uses_registry_role(self) -> None:
        source = session()
        source = replace(
            source,
            artifacts={
                "capture-cap-001-line_annotation_svg": ArtifactRecord(
                    "capture-cap-001-line_annotation_svg",
                    "svg",
                    "Line annotation",
                    "images/cap-001-line.svg",
                    ArtifactOwnerRef("capture", "cap-001", "line_annotation_svg"),
                    status=ArtifactStatus.MISSING,
                )
            },
        )
        document = select_item(SessionDocumentBuilder().build(source), "capture:cap-001")
        bridge = _RecordingRenderBridge()
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatcher = EditorActionDispatcher(
                paths=SessionPaths.for_folder(Path(temp_dir)),
                render_bridge=bridge,
            )

            result = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_ARTIFACT,
                    "Regenerate Line Annotation",
                    "capture:cap-001",
                    payload=(("artifact_id", "capture-cap-001-line_annotation_svg"),),
                ),
            )

        self.assertEqual("success", result.status)
        self.assertEqual(
            (RenderTarget(DrawingOwnerRef("capture", "cap-001"), "line_annotation"),),
            bridge.requests[0].targets,
        )

    def test_regenerate_selected_measurement_artifact_uses_registry_role(self) -> None:
        source = session()
        source = replace(
            source,
            artifacts={
                "measurement-meas-001-measurement_annotation_png": ArtifactRecord(
                    "measurement-meas-001-measurement_annotation_png",
                    "image",
                    "Measurement annotation",
                    "images/meas-001-measurement.png",
                    ArtifactOwnerRef("measurement", "meas-001", "measurement_annotation_png"),
                    status=ArtifactStatus.MISSING,
                )
            },
        )
        document = select_item(SessionDocumentBuilder().build(source), "measurement:meas-001")
        bridge = _RecordingRenderBridge()
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatcher = EditorActionDispatcher(
                paths=SessionPaths.for_folder(Path(temp_dir)),
                render_bridge=bridge,
            )

            result = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_ARTIFACT,
                    "Regenerate Measurement Annotation",
                    "measurement:meas-001",
                    payload=(("artifact_id", "measurement-meas-001-measurement_annotation_png"),),
                ),
            )

        self.assertEqual("success", result.status)
        self.assertEqual(
            (RenderTarget(DrawingOwnerRef("measurement", "meas-001"), "measurement_annotation"),),
            bridge.requests[0].targets,
        )

import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.diagnostics import InMemoryDiagnosticSink
from metrology_process_planner.domains.session import SessionRecord, WarningRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderTarget,
    SessionDocumentBuilder,
    SessionRenderBridge,
)
from tests.artifact_helpers import capture_crop_artifact
from tests.editor_render_fixtures import (
    FailingDrawingStore,
    FailingRasterizer,
    session_without_box_bounds,
    session_without_pending,
)


class EditorRenderBridgeFailureTests(unittest.TestCase):
    def test_render_failures_become_stable_warnings_without_duplicate_drawings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge = SessionRenderBridge(SessionPaths.for_folder(Path(temp_dir)))
            request = RenderRefreshRequest(
                targets=(RenderTarget(DrawingOwnerRef("capture", "cap-001")),)
            )

            first = bridge.refresh(session_without_box_bounds(), request)
            second = bridge.refresh(first.session, request)

        self.assertEqual("warning", first.status)
        self.assertNotIn("capture-cap-001-layout_annotation_spec", first.session.artifacts)
        self.assertEqual(1, len(second.session.warnings))
        self.assertEqual(
            "render-capture-cap-001-layout_annotation-validation",
            first.warnings[0].id,
        )

    def test_export_and_rasterizer_failures_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            sink = InMemoryDiagnosticSink()
            target = RenderRefreshRequest(
                targets=(RenderTarget(DrawingOwnerRef("capture", "cap-001")),)
            )
            export_failed = SessionRenderBridge(
                paths,
                drawing_store=FailingDrawingStore(),
                diagnostic_sink=sink,
            ).refresh(session_without_pending(), target)
            raster_failed = SessionRenderBridge(
                paths,
                rasterizer=FailingRasterizer(),
            ).refresh(session_without_pending(), target)

        self.assertEqual("error", export_failed.status)
        self.assertNotIn(
            "capture-cap-001-layout_annotation_spec",
            export_failed.session.artifacts,
        )
        self.assertEqual("ArtifactExportFailed", sink.recent(1)[0].event_name)
        self.assertEqual("warning", raster_failed.status)
        self.assertIn("capture-cap-001-layout_annotation_spec", raster_failed.session.artifacts)
        self.assertIn("capture-cap-001-layout_annotation_svg", raster_failed.session.artifacts)
        self.assertNotIn("capture-cap-001-layout_annotation_png", raster_failed.session.artifacts)
        self.assertIn("PNG rasterization failed", raster_failed.warnings[0].message)

    def test_measurement_annotation_failures_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            target = RenderRefreshRequest(
                targets=(
                    RenderTarget(
                        DrawingOwnerRef("measurement", "meas-001"),
                        "measurement_annotation",
                    ),
                )
            )
            export_failed = SessionRenderBridge(
                paths,
                drawing_store=FailingDrawingStore(),
            ).refresh(session_without_pending(), target)
            raster_failed = SessionRenderBridge(
                paths,
                rasterizer=FailingRasterizer(),
            ).refresh(session_without_pending(), target)

        measurement = export_failed.session.captures[0].measurements[0]
        self.assertEqual("error", export_failed.status)
        self.assertEqual("meas-001", measurement.id)
        self.assertIn("disk full", export_failed.warnings[0].message)
        self.assertEqual("warning", raster_failed.status)
        self.assertIn("PNG rasterization failed", raster_failed.warnings[0].message)

    def test_warning_artifact_status_maps_to_preview_status(self) -> None:
        source = session_without_pending()
        session = SessionRecord(
            id=source.id,
            name=source.name,
            mode=source.mode,
            created_at=source.created_at,
            updated_at=source.updated_at,
            captures=source.captures,
            artifacts={"capture-cap-001-crop": capture_crop_artifact()},
            warnings=(
                WarningRecord(
                    "warn-error",
                    "Cannot read artifact",
                    severity="error",
                    artifact_path="images/cap-001.png",
                ),
            ),
        )

        document = SessionDocumentBuilder().build(session)
        previews = DefaultSessionModeAdapter().preview_options(
            document.session,
            document.items_by_id["capture:cap-001"],
        )

        self.assertEqual("error", previews[0].status)
        self.assertIn("Cannot read artifact", previews[0].placeholder)


if __name__ == "__main__":
    unittest.main()

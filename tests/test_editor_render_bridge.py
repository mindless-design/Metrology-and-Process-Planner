import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    RenderRefreshResult,
    SessionDocumentBuilder,
    SessionRenderBridge,
    apply_metadata_edits,
    mark_metadata_edit,
    select_item,
)
from tests.editor_render_fixtures import FakeRasterizer, session


class EditorRenderBridgeTests(unittest.TestCase):
    def test_metadata_edits_apply_before_render_refresh(self) -> None:
        document = SessionDocumentBuilder().build(session())
        document = mark_metadata_edit(document, "dashboard", "session_name", "Renamed")
        document = mark_metadata_edit(document, "capture:cap-001", "label", "Edited Site")
        document = mark_metadata_edit(document, "pending:pending-001", "label", "Pending Label")
        document = mark_metadata_edit(document, "measurement:meas-001", "label", "Edited CD")

        applied = apply_metadata_edits(document)

        self.assertEqual("Renamed", applied.session.name)
        self.assertEqual("Edited Site", applied.session.captures[0].label)
        self.assertEqual("Pending Label", applied.session.pending_captures[0].metadata["label"])
        self.assertEqual("Edited CD", applied.session.captures[0].measurements[0].label)

    def test_save_refreshes_capture_layout_annotation_and_preserves_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = select_item(SessionDocumentBuilder().build(session()), "capture:cap-001")
            dispatcher = EditorActionDispatcher(
                paths=paths,
                render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
            )

            result = dispatcher.dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )
            capture = result.document.session.captures[0]
            previews = DefaultSessionModeAdapter().preview_options(
                result.document.session,
                result.document.items_by_id["capture:cap-001"],
            )

            self.assertEqual("success", result.status)
            self.assertEqual("capture:cap-001", result.document.selection.selected_item_id)
            self.assertEqual(
                "capture-cap-001-layout_annotation_svg",
                capture.artifact_refs["layout_annotation_svg"],
            )
            artifacts = result.document.session.artifacts
            self.assertIn("capture-cap-001-layout_annotation_spec", artifacts)
            self.assertIn("capture-cap-001-layout_annotation_svg", artifacts)
            self.assertIn("capture-cap-001-layout_annotation_png", artifacts)
            self.assertTrue(
                (Path(temp_dir) / artifacts["capture-cap-001-layout_annotation_spec"].relative_path)
                .exists()
            )
            self.assertTrue(
                (Path(temp_dir) / artifacts["capture-cap-001-layout_annotation_svg"].relative_path)
                .exists()
            )
            self.assertTrue(
                (Path(temp_dir) / artifacts["capture-cap-001-layout_annotation_png"].relative_path)
                .exists()
            )
            self.assertTrue(any(preview.role == "layout_annotation_svg" for preview in previews))

    def test_render_refresh_ignores_hidden_process_display_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            source = session()
            hidden = ArtifactRecord(
                "legacy-process-crop",
                "process_output",
                "Legacy Process Crop",
                "process_outputs/cap-001-crop.png",
                ArtifactOwnerRef("capture", "cap-001", "crop"),
                status=ArtifactStatus.MISSING,
            )
            source = replace(
                source,
                artifacts={"legacy-process-crop": hidden, **dict(source.artifacts or {})},
            )
            document = select_item(SessionDocumentBuilder().build(source), "capture:cap-001")
            dispatcher = EditorActionDispatcher(
                paths=paths,
                render_bridge=SessionRenderBridge(paths, rasterizer=FakeRasterizer()),
            )

            result = dispatcher.dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

            artifact = result.document.session.artifacts[
                "capture-cap-001-layout_annotation_spec"
            ]
            spec = json.loads((Path(temp_dir) / artifact.relative_path).read_text())
            self.assertEqual("images/cap-001.png", spec["image_layers"][0]["path"])

    def test_regenerate_selected_artifact_rejects_mismatched_owner(self) -> None:
        source = session()
        source = replace(
            source,
            artifacts={
                "capture-cap-002-layout_annotation_svg": ArtifactRecord(
                    "capture-cap-002-layout_annotation_svg",
                    "svg",
                    "Other capture annotation",
                    "images/cap-002-layout.svg",
                    ArtifactOwnerRef("capture", "cap-002", "layout_annotation_svg"),
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
                    "Regenerate Other Artifact",
                    "capture:cap-001",
                    payload=(("artifact_id", "capture-cap-002-layout_annotation_svg"),),
                ),
            )

        self.assertEqual("unavailable", result.status)
        self.assertEqual((), bridge.requests)


class _RecordingRenderBridge:
    def __init__(self) -> None:
        self.requests = ()

    def refresh(self, source, request):
        self.requests = self.requests + (request,)
        return RenderRefreshResult("success", source)


if __name__ == "__main__":
    unittest.main()

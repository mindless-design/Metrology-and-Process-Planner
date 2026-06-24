import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.process import Material
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    CrossSectionRenderInput,
    DefaultSessionModeAdapter,
    DrawingOwnerRef,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    RenderRefreshRequest,
    SessionDocumentBuilder,
    SessionRenderBridge,
    apply_metadata_edits,
    mark_metadata_edit,
    select_item,
)
from tests.editor_render_fixtures import FakeRasterizer, empty_session, profile, session


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

    def test_cross_section_refresh_persists_session_level_drawing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            source = CrossSectionRenderInput(
                owner=DrawingOwnerRef("process_frame", "frame-001"),
                profile=profile(),
                materials=(Material("si", "Silicon", "#999999"),),
                title="Etch frame",
            )

            result = SessionRenderBridge(paths, rasterizer=FakeRasterizer()).refresh(
                empty_session(),
                RenderRefreshRequest(cross_sections=(source,)),
            )
            SessionJsonStore().save(result.session, paths)
            loaded = SessionJsonStore().load(paths.folder)
            document = SessionDocumentBuilder().build(loaded)

            self.assertEqual("success", result.status)
            self.assertEqual("5.0.0", loaded.schema_version)
            self.assertIn("process_frame-frame-001-cross_section_svg", loaded.artifacts)
            self.assertIn("drawing:process_frame:frame-001:cross_section", document.items_by_id)
            self.assertTrue(
                (
                    Path(temp_dir)
                    / loaded.artifacts[
                        "process_frame-frame-001-cross_section_svg"
                    ].relative_path
                ).exists()
            )


if __name__ == "__main__":
    unittest.main()

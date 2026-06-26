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
    SessionMode,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    SessionRenderBridge,
    select_item,
)
from tests.editor_render_fixtures import FakeRasterizer, session


class DrawingStoreVisibilityTests(unittest.TestCase):
    def test_capture_ref_sync_excludes_hidden_process_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            hidden = ArtifactRecord(
                "legacy-capture-process-output",
                "process_output",
                "Legacy Capture Process Output",
                "process_outputs/cap-001-stack.png",
                ArtifactOwnerRef("capture", "cap-001", "stack_image"),
                status=ArtifactStatus.MISSING,
            )
            source = session()
            source = replace(
                source,
                artifacts={**dict(source.artifacts or {}), hidden.id: hidden},
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
            refs = result.document.session.captures[0].artifact_refs

            self.assertEqual("success", result.status)
            self.assertIn("layout_annotation_svg", refs)
            self.assertNotIn("stack_image", refs)
            self.assertNotIn(hidden.id, set(refs.values()))

    def test_capture_ref_sync_uses_loaded_recipe_free_registry_for_builtin_override(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            registry = _recipe_free_registry()
            hidden = _hidden_process_artifact()
            source = _recipe_free_session_with(hidden)
            document = select_item(
                SessionDocumentBuilder(mode_registry=registry).build(source),
                "capture:cap-001",
            )
            dispatcher = EditorActionDispatcher(
                paths=paths,
                render_bridge=SessionRenderBridge(
                    paths,
                    rasterizer=FakeRasterizer(),
                    mode_registry=registry,
                ),
                mode_registry=registry,
            )

            result = dispatcher.dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )
            refs = result.document.session.captures[0].artifact_refs

            self.assertEqual("success", result.status)
            self.assertIn("layout_annotation_svg", refs)
            self.assertNotIn("stack_image", refs)
            self.assertNotIn(hidden.id, set(refs.values()))


def _recipe_free_registry() -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                SessionMode.PROFILOMETRY_PLANNER.value,
                "Recipe Free Override",
            ),
        )
    )


def _hidden_process_artifact() -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-capture-process-output",
        "process_output",
        "Legacy Capture Process Output",
        "process_outputs/cap-001-stack.png",
        ArtifactOwnerRef("capture", "cap-001", "stack_image"),
        status=ArtifactStatus.MISSING,
    )


def _recipe_free_session_with(hidden: ArtifactRecord):
    source = replace(session(), mode=SessionMode.PROFILOMETRY_PLANNER)
    return replace(
        source,
        artifacts={**dict(source.artifacts or {}), hidden.id: hidden},
    )


if __name__ == "__main__":
    unittest.main()

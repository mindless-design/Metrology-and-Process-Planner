import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.process import Material
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
)
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    CrossSectionRenderInput,
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderRefreshResult,
    SessionDocumentBuilder,
    SessionRenderBridge,
)
from metrology_process_planner.workflows.editor.render_bridge_artifacts import (
    first_visible_display_artifact,
)
from tests.editor_render_fixtures import FakeRasterizer, empty_session, profile, session


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


class EditorRenderBridgeArtifactTestsPart2(unittest.TestCase):
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
                    / loaded.artifacts["process_frame-frame-001-cross_section_svg"].relative_path
                ).exists()
            )

    def test_display_artifact_selection_uses_loaded_recipe_free_registry(self) -> None:
        source = replace(session(), mode=SessionMode.PROFILOMETRY_PLANNER)
        hidden = ArtifactRecord(
            "legacy-site-image-process-output",
            "process_output",
            "Legacy Process Site Image",
            "process_outputs/cap-001-site.png",
            ArtifactOwnerRef("capture", "cap-001", "site_image"),
            status=ArtifactStatus.PRESENT,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        visible = ArtifactRecord(
            "capture-cap-001-crop",
            "image",
            "Capture Crop",
            "images/cap-001.png",
            ArtifactOwnerRef("capture", "cap-001", "crop"),
            status=ArtifactStatus.PRESENT,
        )
        registry = _recipe_free_registry_for(source.mode.value)
        source = replace(source, artifacts={hidden.id: hidden, visible.id: visible})

        artifact = first_visible_display_artifact(
            source,
            "capture",
            "cap-001",
            registry,
        )

        self.assertIsNotNone(artifact)
        self.assertEqual(visible.id, artifact.id)

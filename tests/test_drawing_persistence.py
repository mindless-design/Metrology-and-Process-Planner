import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.drawing_store import SessionDrawingStore
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.rendering import CanvasSpec, DrawingScene

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class DrawingPersistenceTests(unittest.TestCase):
    def test_v1_session_loads_as_v5_with_empty_drawings(self) -> None:
        session = SessionJsonStore().load(FIXTURES / "sessions" / "simple_session")

        self.assertEqual("5.0.0", session.schema_version)
        self.assertIn("capture-cap-001-crop", session.artifacts)

    def test_drawing_artifact_round_trip_preserves_paths(self) -> None:
        session = _session_with_drawing()

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            SessionJsonStore().save(session, paths)
            loaded = SessionJsonStore().load(paths.folder)

        self.assertEqual("5.0.0", loaded.schema_version)
        self.assertIn("capture-cap-001-layout_annotation_svg", loaded.artifacts)
        self.assertTrue(any(warning.code == "artifact_missing" for warning in loaded.warnings))

    def test_session_drawing_store_writes_spec_svg_and_png(self) -> None:
        scene = DrawingScene(
            id="drawing-001",
            role="layout_annotation",
            canvas=CanvasSpec(320, 240),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            stored = SessionDrawingStore().export_capture_scene(
                paths,
                capture_id="cap-001",
                scene=scene,
                rasterizer=FakeRasterizer(),
            )

            by_role = {artifact.owner.role: artifact for artifact in stored.artifacts}
            spec_path = Path(temp_dir) / by_role["layout_annotation_spec"].relative_path
            svg_path = Path(temp_dir) / by_role["layout_annotation_svg"].relative_path
            png_path = Path(temp_dir) / by_role["layout_annotation_png"].relative_path

            self.assertTrue(spec_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertEqual(b"fake-png", png_path.read_bytes())

        self.assertEqual(
            {
                "layout_annotation_spec",
                "layout_annotation_svg",
                "layout_annotation_png",
            },
            {artifact.owner.role for artifact in stored.artifacts},
        )
        self.assertIn("drawings/cap-001-layout_annotation.json", stored.paths)
        self.assertIn("images/cap-001-layout_annotation.svg", stored.paths)
        self.assertIn("images/cap-001-layout_annotation.png", stored.paths)


class FakeRasterizer:
    def rasterize_svg(
        self,
        svg_text: str,
        destination: Path,
        width_px: int,
        height_px: int,
    ) -> None:
        destination.write_bytes(b"fake-png")


def _session_with_drawing() -> SessionRecord:
    capture = CaptureRecord(
        id="cap-001",
        label="Site 1",
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        created_at="2026-06-23T20:00:00Z",
    )
    artifacts = {
        "capture-cap-001-layout_annotation_svg": ArtifactRecord(
            id="capture-cap-001-layout_annotation_svg",
            type="svg",
            label="layout_annotation SVG",
            relative_path="images/cap-001-layout_annotation.svg",
            owner=ArtifactOwnerRef("capture", "cap-001", "layout_annotation_svg"),
            status=ArtifactStatus.PRESENT,
            file=ArtifactFileMetadata(width_px=320, height_px=240, content_type="image/svg+xml"),
        )
    }
    return SessionRecord(
        id="session-001",
        name="Demo Session",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        captures=(capture,),
        artifacts=artifacts,
    )


if __name__ == "__main__":
    unittest.main()

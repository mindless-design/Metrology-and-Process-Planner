import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.capture.capture_geometry import CaptureGeometry
from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
    generate_annotation_artifact,
    generate_labeled_site_artifact,
    generate_site_overview_artifact,
    generate_visual_artifacts_for_capture,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.capture_metadata_pipeline_fixtures import (
    line_feature_capture,
    session_with_capture,
    simple_capture,
)


class VisualArtifactPolishTests(unittest.TestCase):
    def test_labeled_site_artifact_is_created_and_raw_site_image_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            session = generate_labeled_site_artifact(
                session_with_capture(simple_capture()),
                simple_capture(),
                paths,
            )

            capture = session.captures[0]
            self.assertIn("capture-cap-001-site_image", session.artifacts)
            self.assertIn("site_image_labeled", capture.artifact_refs)
            artifact = session.artifacts[capture.artifact_refs["site_image_labeled"]]
            self.assertEqual("site_image_labeled", artifact.type)
            self.assertTrue((paths.folder / artifact.relative_path).exists())

    def test_site_overview_expands_region_and_uses_site_label_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            session = generate_site_overview_artifact(
                session_with_capture(line_feature_capture()),
                line_feature_capture(),
                paths,
            )

            artifact = session.artifacts[session.captures[0].artifact_refs["site_overview_image"]]
            svg = (paths.folder / artifact.relative_path).read_text(encoding="utf-8")
            region = artifact.extensions["overview_region"]
            self.assertLess(region["left"], 0)
            self.assertGreater(region["right"], 10)
            self.assertIn("Profile Site 001", svg)
            self.assertIn("<polyline", svg)
            self.assertIn("#0b1120", svg)
            self.assertIn("#67e8f9", svg)

    def test_missing_overview_source_creates_warning_placeholder(self) -> None:
        capture = replace(simple_capture(), geometry=CaptureGeometry.box(Box(0, 0, 10, 10)))
        capture = replace(capture, geometry=replace(capture.geometry, bounds=None))
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            session = generate_site_overview_artifact(session_with_capture(capture), capture, paths)

            artifact = session.artifacts[session.captures[0].artifact_refs["site_overview_image"]]
            self.assertEqual("placeholder", artifact.status.value)
            self.assertTrue(artifact.warning_ids)
            svg = (paths.folder / artifact.relative_path).read_text(encoding="utf-8")
            self.assertIn("#0b1120", svg)

    def test_line_and_point_annotation_artifacts_are_registered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            session = generate_annotation_artifact(
                session_with_capture(line_feature_capture()),
                line_feature_capture(),
                paths,
                "line_annotation_image",
            )

            self.assertIn("line_annotation_image", session.captures[0].artifact_refs)

        point_capture = replace(
            simple_capture(),
            geometry=CaptureGeometry(
                kind=simple_capture().geometry.kind,
                bounds=simple_capture().geometry.bounds,
                features=(
                    {
                        "id": "point-001",
                        "kind": "point",
                        "label": "Film Stack Point",
                        "geometry": {"shape": "point", "point": {"x": 5, "y": 5}},
                    },
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            session = generate_annotation_artifact(
                session_with_capture(point_capture),
                point_capture,
                paths,
                "point_annotation_image",
            )

            self.assertIn("point_annotation_image", session.captures[0].artifact_refs)

    def test_editor_preview_modes_and_visual_regenerate_action_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            session = generate_visual_artifacts_for_capture(
                session_with_capture(line_feature_capture()),
                "cap-001",
                paths,
            )
            document = SessionDocumentBuilder().build(session)
            item = document.items_by_id["capture:cap-001"]
            adapter = DefaultSessionModeAdapter()

            preview_labels = tuple(
                option.label for option in adapter.preview_options(session, item)
            )
            action_labels = tuple(action.label for action in adapter.actions(session, item))

            self.assertIn("Labeled Site Image", preview_labels)
            self.assertIn("Site Overview", preview_labels)
            self.assertIn("Annotated Line/Point", preview_labels)
            self.assertIn("Regenerate Visual Artifacts", action_labels)

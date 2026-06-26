import unittest
from dataclasses import replace

from metrology_process_planner.domains.capture.capture_geometry import CaptureGeometry
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.rendering.visual_labels import SiteLabelBuilder
from tests.capture_metadata_pipeline_fixtures import (
    line_feature_capture,
    session_with_capture,
    simple_capture,
)


class VisualArtifactLabelTests(unittest.TestCase):
    def test_label_content_generated_for_simple_capture(self) -> None:
        session = replace(session_with_capture(simple_capture()), mode=SessionMode.SIMPLE_CAPTURE)

        label = SiteLabelBuilder().build(session, simple_capture())

        self.assertEqual("Site 001", label.text_lines[0])
        self.assertIn("Center: (5 um, 5 um)", label.text_lines)
        self.assertIn("Size: 10 x 10 um", label.text_lines)

    def test_label_content_generated_for_cad_review(self) -> None:
        capture = replace(
            simple_capture(),
            role="cad_review",
            metadata={"issue_id": "005", "category": "Process Risk"},
            notes="Dense gate region near contact array",
        )
        session = replace(session_with_capture(capture), mode=SessionMode.CAD_REVIEW)

        label = SiteLabelBuilder().build(session, capture)

        self.assertEqual("Issue 005 - Process Risk", label.text_lines[0])
        self.assertIn("Dense gate region near contact array", label.text_lines)

    def test_label_content_generated_for_profilometry(self) -> None:
        capture = line_feature_capture()
        session = session_with_capture(capture)

        label = SiteLabelBuilder().build(session, capture)

        self.assertEqual("Profile Site 001", label.text_lines[0])
        self.assertIn("Profile Line", label.text_lines)

    def test_label_content_generated_for_ellipsometry(self) -> None:
        capture = replace(
            simple_capture(),
            type="ellipsometry",
            geometry=CaptureGeometry(
                kind=simple_capture().geometry.kind,
                bounds=simple_capture().geometry.bounds,
                features=(
                    {
                        "id": "point-001",
                        "kind": "ellipsometry_point",
                        "label": "ALD oxide point",
                    },
                ),
            ),
        )
        session = replace(session_with_capture(capture), mode=SessionMode.ELLIPSOMETRY_PLANNER)

        label = SiteLabelBuilder().build(session, capture)

        self.assertEqual("Film Site 001", label.text_lines[0])
        self.assertIn("ALD oxide point", label.text_lines)

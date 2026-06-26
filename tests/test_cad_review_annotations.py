import unittest
from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    SessionMode,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


class CadReviewAnnotationTests(unittest.TestCase):
    def test_review_annotation_is_capture_annotation_in_editor_and_csv(self) -> None:
        session = _cad_review_session_with_annotation()
        document = SessionDocumentBuilder().build(session)
        capture = document.items_by_id["capture:cap-001"]

        fields = DefaultSessionModeAdapter().metadata_fields(document.session, capture)
        row = CaptureCsvExporter().rows_for_session(document.session)[0]

        values = {field.key: field.value for field in fields}
        self.assertEqual("present", values["annotation_status"])
        self.assertEqual("capture-cap-001-review_annotation", row["annotation_artifact_id"])
        self.assertEqual("present", row["annotation_artifact_status"])


def _cad_review_session_with_annotation():
    source = replace(session_without_pending(), mode=SessionMode.CAD_REVIEW)
    annotation = ArtifactRecord(
        id=artifact_id("capture", "cap-001", "review_annotation"),
        type="layout_annotation",
        label="Review Annotation",
        relative_path="images/cap-001-review.svg",
        owner=ArtifactOwnerRef("capture", "cap-001", "review_annotation"),
        status=ArtifactStatus.PRESENT,
    )
    return replace(
        source,
        artifacts={**dict(source.artifacts or {}), annotation.id: annotation},
    )


if __name__ == "__main__":
    unittest.main()

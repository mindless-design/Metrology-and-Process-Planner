import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactOwnerRef,
    ArtifactRepairMetadata,
    ArtifactStatus,
)
from metrology_process_planner.workflows.artifacts import ArtifactRepairService, ArtifactScanner
from metrology_process_planner.workflows.artifacts.signatures import current_signature
from tests.artifact_lifecycle_fixtures import artifact as make_artifact
from tests.artifact_lifecycle_fixtures import scan_with_file, temp_paths
from tests.artifact_lifecycle_fixtures import session as make_session


class ArtifactLifecycleTests(unittest.TestCase):
    def test_artifact_registry_validates_owner_references(self) -> None:
        source = replace(
            make_session(),
            artifacts={
                "orphan": make_artifact(
                    "orphan",
                    owner=ArtifactOwnerRef("capture", "missing", "crop"),
                )
            },
        )

        scanned, _result = ArtifactScanner().scan_session(source, temp_paths())

        self.assertIn("ARTIFACT_OWNER_MISSING", {warning.code for warning in scanned.warnings})

    def test_missing_file_changes_artifact_status_to_missing(self) -> None:
        source = make_session(artifacts={"crop": make_artifact("crop")})

        scanned, _result = ArtifactScanner().scan_session(source, temp_paths())

        self.assertEqual(ArtifactStatus.MISSING, scanned.artifacts["crop"].status)
        self.assertIn("ARTIFACT_MISSING", {warning.code for warning in scanned.warnings})

    def test_stale_dependency_marks_artifact_stale(self) -> None:
        source = make_session()
        signature = current_signature(source, "capture_metadata", "cap-001")
        target = make_artifact(
            "crop",
            dependencies=(
                ArtifactDependencyRef(kind="capture_metadata", id="cap-001", signature=signature),
            ),
        )
        changed = replace(
            source,
            captures=(replace(source.captures[0], notes="changed"),),
            artifacts={"crop": target},
        )

        scanned, _result = scan_with_file(changed, target.relative_path)

        self.assertEqual(ArtifactStatus.STALE, scanned.artifacts["crop"].status)

    def test_failed_artifact_generation_creates_warning(self) -> None:
        source = make_session(
            artifacts={
                "crop": replace(
                    make_artifact("crop"),
                    status=ArtifactStatus.FAILED,
                    repair=ArtifactRepairMetadata(last_error="renderer crashed"),
                )
            }
        )

        scanned, _result = ArtifactScanner().scan_session(source, temp_paths())

        self.assertIn("ARTIFACT_FAILED", {warning.code for warning in scanned.warnings})

    def test_csv_artifact_becomes_stale_after_capture_metadata_edit(self) -> None:
        source = make_session()
        signature = current_signature(source, "capture_metadata", "cap-001")
        csv_artifact = replace(
            make_artifact("csv", path="reports/captures.csv"),
            type="csv_export",
            dependencies=(
                ArtifactDependencyRef(kind="capture_metadata", id="cap-001", signature=signature),
            ),
        )
        changed = replace(
            source,
            captures=(replace(source.captures[0], notes="edited"),),
            artifacts={"csv": csv_artifact},
        )

        scanned, _result = scan_with_file(changed, "reports/captures.csv")

        self.assertEqual(ArtifactStatus.STALE, scanned.artifacts["csv"].status)
        self.assertIn("CSV_STALE", {warning.code for warning in scanned.warnings})

    def test_report_artifact_becomes_stale_after_dependent_image_changes(self) -> None:
        source = make_session()
        signature = current_signature(source, "capture_metadata", "cap-001")
        report = replace(
            make_artifact("deck", path="reports/session.pptx"),
            type="powerpoint_export",
            dependencies=(
                ArtifactDependencyRef(kind="capture_metadata", id="cap-001", signature=signature),
            ),
        )
        changed = replace(
            source,
            captures=(replace(source.captures[0], notes="image metadata changed"),),
            artifacts={"deck": report},
        )

        scanned, _result = scan_with_file(changed, "reports/session.pptx")

        self.assertEqual(ArtifactStatus.STALE, scanned.artifacts["deck"].status)
        self.assertIn("REPORT_STALE", {warning.code for warning in scanned.warnings})

    def test_artifact_scan_result_counts_statuses(self) -> None:
        source = make_session(
            artifacts={
                "present": replace(make_artifact("present"), status=ArtifactStatus.PRESENT),
                "missing": replace(make_artifact("missing"), status=ArtifactStatus.MISSING),
                "failed": replace(make_artifact("failed"), status=ArtifactStatus.FAILED),
                "placeholder": replace(
                    make_artifact("placeholder"),
                    status=ArtifactStatus.PLACEHOLDER,
                ),
            }
        )

        _scanned, result = ArtifactScanner().scan_session(source, temp_paths())

        self.assertEqual(4, result.artifact_count)
        self.assertEqual(1, result.failed_count)
        self.assertEqual(1, result.placeholder_count)

    def test_ignored_warning_remains_ignored_after_rescan(self) -> None:
        service = ArtifactRepairService()
        source = make_session(artifacts={"crop": make_artifact("crop")})
        scanned, _result = service.scan_session(source, temp_paths())
        ignored = service.mark_ignored(scanned, scanned.warnings[0].id)

        rescanned, _result = service.scan_session(ignored, temp_paths())

        self.assertEqual("ignored", rescanned.warnings[0].status)


if __name__ == "__main__":
    unittest.main()

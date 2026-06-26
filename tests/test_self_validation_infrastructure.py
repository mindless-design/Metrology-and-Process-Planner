import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.project_health import build_diagnostics_bundle, build_health_report

from metrology_process_planner.devtools import build_developer_catalog
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ProcessContext,
    ProcessOutputRecord,
    SessionMode,
    SessionRecord,
    utc_now_iso,
)
from metrology_process_planner.infrastructure.project_validators import (
    validate_commands,
    validate_modes,
    validate_render_profiles,
    validate_session_json,
    validate_session_record,
)
from metrology_process_planner.persistence.artifact_audit import audit_artifacts
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.persistence.session_repair import (
    apply_session_repairs,
    preview_session_repairs,
)
from metrology_process_planner.testing.fixture_library import (
    FIXTURE_SESSION_NAMES,
    fixture_session_paths,
)
from metrology_process_planner.testing.visual_regression import compare_json

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SelfValidationInfrastructureTests(unittest.TestCase):
    def test_validation_issue_shape_includes_repair_suggestion(self) -> None:
        report = validate_session_json({"schema_version": 999})

        self.assertTrue(report.issues)
        issue = report.issues[0].to_dict()
        self.assertIn("severity", issue)
        self.assertIn("category", issue)
        self.assertIn("location", issue)
        self.assertIn("message", issue)
        self.assertIn("repair_suggestion", issue)

    def test_core_registry_validators_pass(self) -> None:
        reports = (validate_modes(), validate_commands(), validate_render_profiles())

        self.assertTrue(all(report.ok for report in reports))

    def test_artifact_audit_detects_missing_and_orphaned_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            (paths.images_dir / "orphan.png").write_text("unused", encoding="utf-8")
            session = _session_with_artifact("missing-image", "images/missing.png")

            result = audit_artifacts(session, paths)

        messages = [item.message for item in result.report.issues]
        self.assertIn("Missing artifact file: images/missing.png", messages)
        self.assertIn("Orphaned artifact file.", messages)

    def test_session_repair_is_previewable_before_apply(self) -> None:
        data = {"schema_version": 1, "captures": [{"id": "cap-1"}, {"id": "cap-1"}]}

        preview = preview_session_repairs(data)
        repaired = apply_session_repairs(data, preview)

        self.assertTrue(preview.has_repairs)
        self.assertEqual("cap-repaired-002", repaired["captures"][1]["id"])
        self.assertNotIn("schema", data)

    def test_fixture_library_includes_requested_session_families(self) -> None:
        paths = fixture_session_paths(PROJECT_ROOT)

        self.assertEqual(len(FIXTURE_SESSION_NAMES), len(paths))
        self.assertTrue(all(path.exists() for path in paths))

    def test_visual_json_comparison_ignores_volatile_metadata(self) -> None:
        expected = {"id": "one", "updated_at": "old"}
        actual = {"id": "one", "updated_at": "new"}

        self.assertTrue(compare_json(expected, actual).matched)

    def test_developer_catalog_exposes_tools_data(self) -> None:
        catalog = build_developer_catalog().to_dict()

        self.assertTrue(catalog["modes"])
        self.assertTrue(catalog["commands"])
        self.assertTrue(catalog["render_profiles"])

    def test_project_health_and_bundle_are_exportable(self) -> None:
        health = build_health_report(PROJECT_ROOT)
        bundle = build_diagnostics_bundle(PROJECT_ROOT)

        self.assertEqual(100, health.score)
        self.assertEqual(100, bundle.health.score)
        json.dumps(bundle.to_dict())

    def test_recipe_free_session_validation_ignores_hidden_process_context(self) -> None:
        source = replace(
            _session_with_artifact("cap-image", "images/cap.png"),
            process_context=ProcessContext(render_profile="missing-profile"),
            process_outputs=(
                ProcessOutputRecord(
                    "out-001",
                    "Legacy Stack",
                    "stack",
                    artifact_refs={"stack_image": "missing-stack"},
                ),
            ),
        )

        report = validate_session_record(source)

        messages = {(item.location, item.message) for item in report.issues}
        self.assertNotIn(("process_context.render_profile", "Unknown render profile."), messages)
        self.assertNotIn(("outputs.out-001.stack_image", "Broken artifact reference."), messages)

    def test_process_aware_session_validation_keeps_process_checks(self) -> None:
        source = replace(
            _session_with_artifact("cap-image", "images/cap.png"),
            mode=SessionMode.PROCESS_AWARE_METROLOGY,
            process_context=ProcessContext(render_profile="missing-profile"),
            process_outputs=(
                ProcessOutputRecord(
                    "out-001",
                    "Stack",
                    "stack",
                    artifact_refs={"stack_image": "missing-stack"},
                ),
            ),
        )

        report = validate_session_record(source)

        messages = {(item.location, item.message) for item in report.issues}
        self.assertIn(("process_context.render_profile", "Unknown render profile."), messages)
        self.assertIn(("outputs.out-001.stack_image", "Broken artifact reference."), messages)


def _session_with_artifact(artifact_id: str, relative_path: str) -> SessionRecord:
    now = utc_now_iso()
    artifact = ArtifactRecord(
        id=artifact_id,
        type="image",
        label="Missing image",
        relative_path=relative_path,
        owner=ArtifactOwnerRef("session", "session-audit", "preview"),
    )
    return SessionRecord(
        id="session-audit",
        name="Audit",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at=now,
        updated_at=now,
        artifacts={artifact_id: artifact},
    )


if __name__ == "__main__":
    unittest.main()

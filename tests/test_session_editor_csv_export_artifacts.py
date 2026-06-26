import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import ArtifactScanner
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


class SessionEditorCsvExportArtifactTests(unittest.TestCase):
    def test_export_csv_registers_session_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            exported = _export(paths)
            csv_text = paths.capture_csv.read_text(encoding="utf-8")

        csv_artifact = exported.session.artifacts[_csv_id()]
        self.assertEqual("csv_export", csv_artifact.type)
        self.assertEqual("captures.csv", csv_artifact.relative_path)
        self.assertEqual(ArtifactStatus.PRESENT, csv_artifact.status)
        self.assertEqual("text/csv", csv_artifact.file.content_type)
        self.assertEqual("session", csv_artifact.owner.owner_type)
        self.assertEqual("rebuild_csv", csv_artifact.repair.repair_action)
        self.assertIn("session_id", csv_text)

    def test_exported_csv_artifact_becomes_stale_after_session_data_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            exported = _export(paths)
            edited_session = replace(exported.session, name="Edited")

            scanned, _result = ArtifactScanner().scan_session(edited_session, paths)

        self.assertEqual(ArtifactStatus.STALE, scanned.artifacts[_csv_id()].status)
        self.assertIn("CSV_STALE", {warning.code for warning in scanned.warnings})

    def test_recipe_free_csv_freshness_ignores_hidden_process_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            exported = _export(paths)
            hidden = ArtifactRecord(
                "legacy-process-output",
                "process_output",
                "Legacy Process Output",
                "process_outputs/legacy.json",
                ArtifactOwnerRef("capture", "cap-001", "stack_image"),
                status=ArtifactStatus.MISSING,
            )
            capture = replace(
                exported.session.captures[0],
                artifact_refs={
                    **dict(exported.session.captures[0].artifact_refs or {}),
                    "stack_image": hidden.id,
                },
            )
            edited_session = replace(
                exported.session,
                captures=(capture,),
                artifacts={**dict(exported.session.artifacts or {}), hidden.id: hidden},
                warnings=(
                    WarningRecord(
                        "process-warning",
                        "Recipe missing",
                        source="process_context",
                        code="PROCESS_RECIPE_MISSING",
                    ),
                ),
            )

            scanned, _result = ArtifactScanner().scan_session(edited_session, paths)

        self.assertEqual(ArtifactStatus.PRESENT, scanned.artifacts[_csv_id()].status)


def _export(paths: SessionPaths):
    document = SessionDocumentBuilder().build(session_without_pending())
    result = EditorActionDispatcher(paths=paths).dispatch(
        document,
        EditorAction(EditorActionType.EXPORT_CSV, "CSV"),
    )
    return result.document


def _csv_id() -> str:
    return artifact_id("session", "session-001", "csv_export")


if __name__ == "__main__":
    unittest.main()

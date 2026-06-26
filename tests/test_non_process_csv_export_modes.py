import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.modes.mode_non_process_builtins import non_process_modes
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    WarningRecord,
    session_mode_id,
)
from metrology_process_planner.domains.session import artifact_id as make_artifact_id
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


class NonProcessCsvExportModeTests(unittest.TestCase):
    def test_csv_export_works_without_recipe_for_all_recipe_free_modes(self) -> None:
        for mode_id in _recipe_free_mode_ids():
            with self.subTest(mode_id=mode_id), tempfile.TemporaryDirectory() as temp_dir:
                paths = SessionPaths.for_folder(Path(temp_dir))
                session = replace(session_without_pending(), mode=session_mode_id(mode_id))
                document = SessionDocumentBuilder().build(session)

                result = EditorActionDispatcher(paths=paths).dispatch(
                    document,
                    EditorAction(EditorActionType.EXPORT_CSV, "Export CSV"),
                )

                self.assertEqual("success", result.status)
                self.assertEqual(paths.capture_csv, result.output_path)
                csv_text = paths.capture_csv.read_text(encoding="utf-8")
                csv_artifact = result.document.session.artifacts[_csv_id()]
                warning_codes = {warning.code for warning in result.document.session.warnings}

                self.assertIn(f",{mode_id},", csv_text)
                self.assertEqual("csv_export", csv_artifact.type)
                self.assertEqual(ArtifactStatus.PRESENT, csv_artifact.status)
                self.assertEqual("session", csv_artifact.owner.owner_type)
                self.assertEqual("csv_export", csv_artifact.owner.role)
                self.assertEqual("rebuild_csv", csv_artifact.repair.repair_action)
                self.assertNotIn("PROCESS_RECIPE_MISSING", warning_codes)
                self.assertNotIn("PROCESS_CONTEXT_INVALID", warning_codes)

    def test_capture_warning_count_ignores_hidden_process_artifact_refs(self) -> None:
        hidden = _hidden_process_artifact()
        warning = WarningRecord(
            "legacy-stack-missing",
            "Legacy stack image is missing.",
            source="artifact",
            code="ARTIFACT_MISSING",
            related_artifact_refs=(hidden.id,),
        )
        capture = replace(
            session_without_pending().captures[0],
            artifact_refs={"stack_image": hidden.id},
        )
        session = replace(
            session_without_pending(),
            captures=(capture,),
            artifacts={hidden.id: hidden},
            warnings=(warning,),
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual("0", str(row["warning_count"]))
        self.assertEqual("", row["artifact_statuses"])
        self.assertNotIn("process_outputs", row["image_paths"])


def _recipe_free_mode_ids() -> tuple[str, ...]:
    return tuple(dict.fromkeys(definition.mode_id for definition in non_process_modes()))


def _csv_id() -> str:
    return make_artifact_id("session", "session-001", "csv_export")


def _hidden_process_artifact() -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-capture-process-output",
        "process_output",
        "Legacy Capture Stack",
        "process_outputs/cap-001-stack.png",
        ArtifactOwnerRef("capture", "cap-001", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            requires_recipe=True,
            requires_solver=True,
        ),
    )
if __name__ == "__main__":
    unittest.main()

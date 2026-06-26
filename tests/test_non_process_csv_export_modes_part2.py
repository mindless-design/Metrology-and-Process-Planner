import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.domains.session import artifact_id as make_artifact_id
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import ArtifactRepairService, ArtifactScanner
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


class NonProcessCsvExportModeTestsPart2(unittest.TestCase):
    def test_dispatcher_csv_export_uses_loaded_recipe_free_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
            session = replace(
                session_without_pending(),
                mode=SessionMode.PROFILOMETRY_PLANNER,
                artifacts=_artifacts_with_hidden_process_output(),
            )
            document = SessionDocumentBuilder(mode_registry=registry).build(session)

            result = EditorActionDispatcher(paths=paths, mode_registry=registry).dispatch(
                document,
                EditorAction(EditorActionType.EXPORT_CSV, "Export CSV"),
            )

            self.assertEqual("success", result.status)
            csv_text = paths.capture_csv.read_text(encoding="utf-8")
            self.assertIn("crop:present", csv_text)
            self.assertNotIn("stack_image:missing", csv_text)
            self.assertNotIn("process_outputs/cap-001-stack.png", csv_text)

    def test_dispatcher_csv_export_signature_uses_loaded_recipe_free_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
            document = SessionDocumentBuilder(mode_registry=registry).build(
                replace(session_without_pending(), mode=SessionMode.PROFILOMETRY_PLANNER)
            )

            result = EditorActionDispatcher(paths=paths, mode_registry=registry).dispatch(
                document,
                EditorAction(EditorActionType.EXPORT_CSV, "Export CSV"),
            )
            changed = replace(
                result.document.session,
                artifacts={
                    **dict(result.document.session.artifacts or {}),
                    "legacy-capture-process-output": _hidden_process_artifact(),
                },
                warnings=(_process_warning(),),
            )
            scanned, _scan_result = ArtifactScanner().scan_session(changed, paths, registry)
            csv_artifact = scanned.artifacts[_csv_id()]

        self.assertEqual(ArtifactStatus.PRESENT, csv_artifact.status)
        self.assertEqual((), csv_artifact.warning_ids)

    def test_csv_repair_uses_loaded_recipe_free_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
            document = SessionDocumentBuilder(mode_registry=registry).build(
                replace(session_without_pending(), mode=SessionMode.PROFILOMETRY_PLANNER)
            )
            result = EditorActionDispatcher(paths=paths, mode_registry=registry).dispatch(
                document,
                EditorAction(EditorActionType.EXPORT_CSV, "Export CSV"),
            )
            csv_artifact = result.document.session.artifacts[_csv_id()]
            source = replace(
                result.document.session,
                artifacts={
                    **dict(result.document.session.artifacts or {}),
                    _csv_id(): replace(csv_artifact, status=ArtifactStatus.STALE),
                    "legacy-capture-process-output": _hidden_process_artifact(),
                },
                warnings=(_process_warning(),),
            )

            repaired = ArtifactRepairService().repair_artifact(source, _csv_id(), paths, registry)
            csv_text = paths.capture_csv.read_text(encoding="utf-8")
            scanned, _scan_result = ArtifactScanner().scan_session(repaired, paths, registry)
            repaired_artifact = scanned.artifacts[_csv_id()]

        self.assertIn("crop:present", csv_text)
        self.assertNotIn("stack_image", csv_text)
        self.assertEqual(ArtifactStatus.PRESENT, repaired_artifact.status)
        self.assertEqual((), repaired_artifact.warning_ids)

    def test_copy_csv_row_uses_loaded_recipe_free_registry(self) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        session = replace(
            session_without_pending(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            artifacts=_artifacts_with_hidden_process_output(),
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(session)

        result = EditorActionDispatcher(mode_registry=registry).dispatch(
            document,
            EditorAction(EditorActionType.COPY_CSV_ROW, "Copy CSV Row", "capture:cap-001"),
        )

        self.assertEqual("success", result.status)
        self.assertIn("crop:present", result.message)
        self.assertNotIn("stack_image:missing", result.message)
        self.assertNotIn("process_outputs/cap-001-stack.png", result.message)


def _csv_id() -> str:
    return make_artifact_id("session", "session-001", "csv_export")


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))


def _artifacts_with_hidden_process_output() -> dict[str, ArtifactRecord]:
    visible = ArtifactRecord(
        "artifact-cap-001-crop",
        "image",
        "Capture Crop",
        "captures/cap-001.png",
        ArtifactOwnerRef("capture", "cap-001", "crop"),
        status=ArtifactStatus.PRESENT,
    )
    hidden = _hidden_process_artifact()
    return {visible.id: visible, hidden.id: hidden}


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


def _process_warning() -> WarningRecord:
    return WarningRecord(
        "legacy-process-warning",
        "Legacy process output is stale.",
        source="process_output",
        code="PROCESS_OUTPUT_STALE",
        related_artifact_refs=("legacy-capture-process-output",),
    )


if __name__ == "__main__":
    unittest.main()

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import ArtifactScanner
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


def _dashboard_fields(source) -> dict[str, str]:
    adapter = DefaultSessionModeAdapter()
    document = SessionDocumentBuilder().build(source)
    return {
        field.key: field.value
        for field in adapter.metadata_fields(source, document.items_by_id["dashboard"])
    }

def _dashboard_actions(document) -> dict[EditorActionType, EditorAction]:
    actions = DefaultSessionModeAdapter().actions(
        document.session,
        document.items_by_id["dashboard"],
    )
    return {action.action_type: action for action in actions}

def _export_csv(paths: SessionPaths):
    document = SessionDocumentBuilder().build(session_without_pending())
    return EditorActionDispatcher(paths=paths).dispatch(
        document,
        EditorAction(EditorActionType.EXPORT_CSV, "Export CSV"),
    ).document

def _visible_missing_artifact() -> ArtifactRecord:
    return _visible_artifact("capture-missing", ArtifactStatus.MISSING)

def _visible_artifact(artifact_id: str, status: ArtifactStatus) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id,
        "capture_image",
        artifact_id.replace("-", " ").title(),
        f"captures/{artifact_id}.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=status,
    )

def _hidden_process_artifact() -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-process-output",
        "process_output",
        "Legacy Process Output",
        "process_outputs/legacy-stack.png",
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


class NonProcessDashboardArtifactTestsPart2(unittest.TestCase):
    def test_dashboard_repair_actions_ignore_hidden_process_artifacts(self) -> None:
        hidden = _hidden_process_artifact()
        source = replace(session_without_pending(), artifacts={hidden.id: hidden})
        document = SessionDocumentBuilder().build(source)

        actions = _dashboard_actions(document)

        self.assertFalse(actions[EditorActionType.REGENERATE_MISSING_ARTIFACTS].enabled)
        self.assertEqual(
            "No visible missing artifacts need repair.",
            actions[EditorActionType.REGENERATE_MISSING_ARTIFACTS].disabled_reason,
        )
        self.assertFalse(actions[EditorActionType.REGENERATE_STALE_ARTIFACTS].enabled)
        self.assertEqual(
            "No visible stale artifacts need repair.",
            actions[EditorActionType.REGENERATE_STALE_ARTIFACTS].disabled_reason,
        )

    def test_dashboard_repair_actions_enable_for_visible_missing_and_stale_artifacts(self) -> None:
        missing = _visible_missing_artifact()
        stale = _visible_artifact("stale-artifact", ArtifactStatus.STALE)
        source = replace(
            session_without_pending(),
            artifacts={missing.id: missing, stale.id: stale},
        )
        document = SessionDocumentBuilder().build(source)

        actions = _dashboard_actions(document)

        self.assertTrue(actions[EditorActionType.REGENERATE_MISSING_ARTIFACTS].enabled)
        self.assertTrue(actions[EditorActionType.REGENERATE_STALE_ARTIFACTS].enabled)

    def test_dashboard_csv_readiness_tracks_export_artifact_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            exported = _export_csv(paths)
            edited = replace(exported.session, name="Edited")
            stale, _result = ArtifactScanner().scan_session(edited, paths)

        self.assertEqual(
            "not exported",
            _dashboard_fields(session_without_pending())["csv_readiness"],
        )
        self.assertEqual("ready", _dashboard_fields(exported.session)["csv_readiness"])
        self.assertEqual("stale", _dashboard_fields(stale)["csv_readiness"])

    def test_dashboard_report_readiness_ignores_stale_csv_export(self) -> None:
        csv_artifact = ArtifactRecord(
            "session-session-001-csv_export",
            "csv_export",
            "Capture CSV",
            "exports/captures.csv",
            ArtifactOwnerRef("session", "session-001", "csv_export"),
            status=ArtifactStatus.STALE,
        )
        stale = replace(session_without_pending(), artifacts={csv_artifact.id: csv_artifact})

        fields = _dashboard_fields(stale)

        self.assertEqual("stale", fields["csv_readiness"])
        self.assertEqual("ready", fields["report_readiness"])

    def test_dashboard_keeps_report_csv_out_of_capture_csv_readiness(self) -> None:
        report_csv = ArtifactRecord(
            "report-001-csv",
            "csv_export",
            "Report CSV",
            "reports/report-001.csv",
            ArtifactOwnerRef("report", "report-001", "report_output"),
            status=ArtifactStatus.STALE,
        )
        source = replace(session_without_pending(), artifacts={report_csv.id: report_csv})

        fields = _dashboard_fields(source)

        self.assertEqual("not exported", fields["csv_readiness"])
        self.assertEqual("stale outputs", fields["report_readiness"])

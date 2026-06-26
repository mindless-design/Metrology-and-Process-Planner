import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths
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


class NonProcessDashboardArtifactTestsPart1(unittest.TestCase):
    def test_dashboard_counts_only_visible_missing_artifacts(self) -> None:
        visible = _visible_missing_artifact()
        hidden = _hidden_process_artifact()
        source = replace(
            session_without_pending(),
            artifacts={visible.id: visible, hidden.id: hidden},
        )

        fields = _dashboard_fields(source)

        self.assertEqual("1", fields["missing_artifact_count"])
        self.assertEqual("1", fields["artifact_attention_count"])
        self.assertEqual("missing required artifacts", fields["report_readiness"])

    def test_dashboard_separates_missing_from_repair_attention(self) -> None:
        source = replace(
            session_without_pending(),
            artifacts={
                "placeholder-artifact": _visible_artifact(
                    "placeholder-artifact",
                    ArtifactStatus.PLACEHOLDER,
                ),
                "stale-artifact": _visible_artifact("stale-artifact", ArtifactStatus.STALE),
                "failed-artifact": _visible_artifact("failed-artifact", ArtifactStatus.FAILED),
            },
        )

        fields = _dashboard_fields(source)

        self.assertEqual("0", fields["missing_artifact_count"])
        self.assertEqual("3", fields["artifact_attention_count"])
        self.assertEqual("artifact repair required", fields["report_readiness"])

    def test_dashboard_reports_placeholder_and_stale_readiness_distinctly(self) -> None:
        placeholder = replace(
            session_without_pending(),
            artifacts={
                "placeholder-artifact": _visible_artifact(
                    "placeholder-artifact",
                    ArtifactStatus.PLACEHOLDER,
                ),
            },
        )
        stale = replace(
            session_without_pending(),
            artifacts={
                "stale-artifact": _visible_artifact("stale-artifact", ArtifactStatus.STALE),
            },
        )

        self.assertEqual(
            "ready with warnings",
            _dashboard_fields(placeholder)["report_readiness"],
        )
        self.assertEqual("stale outputs", _dashboard_fields(stale)["report_readiness"])

    def test_dashboard_reports_pending_artifacts_as_attention(self) -> None:
        pending = replace(
            session_without_pending(),
            artifacts={
                "pending-artifact": _visible_artifact(
                    "pending-artifact",
                    ArtifactStatus.PENDING,
                ),
                "pending-solver-artifact": _visible_artifact(
                    "pending-solver-artifact",
                    ArtifactStatus.PENDING_SOLVER,
                ),
            },
        )

        fields = _dashboard_fields(pending)

        self.assertEqual("0", fields["missing_artifact_count"])
        self.assertEqual("2", fields["artifact_attention_count"])
        self.assertEqual("artifact generation pending", fields["report_readiness"])

    def test_dashboard_readiness_ignores_hidden_process_artifacts(self) -> None:
        hidden = _hidden_process_artifact()
        source = replace(session_without_pending(), artifacts={hidden.id: hidden})

        fields = _dashboard_fields(source)

        self.assertEqual("0", fields["missing_artifact_count"])
        self.assertEqual("0", fields["artifact_attention_count"])
        self.assertEqual("ready", fields["report_readiness"])

"""Report inspector-field helpers."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, ReportRecord, SessionRecord
from metrology_process_planner.workflows.editor.view_models import MetadataField
from metrology_process_planner.workflows.editor.warning_visibility import (
    editor_visible_warnings,
)


def report_fields(
    session: SessionRecord,
    report: ReportRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return read-only metadata fields for one generated report."""

    return (
        MetadataField("label", "Label", report.label, read_only=True),
        MetadataField("report_type", "Report Type", report.report_type, read_only=True),
        MetadataField("status", "Status", report.status, read_only=True),
        MetadataField("generated_at", "Generated", report.generated_at, read_only=True),
        MetadataField(
            "artifact_count",
            "Artifacts",
            str(_visible_report_artifact_count(session, report, mode_registry)),
            read_only=True,
        ),
        MetadataField(
            "warning_count",
            "Warnings",
            str(_visible_report_warning_count(session, report, mode_registry)),
            read_only=True,
        ),
    )


def _visible_report_artifact_count(
    session: SessionRecord,
    report: ReportRecord,
    mode_registry: ModeRegistry | None,
) -> int:
    artifacts = session.artifacts or {}
    return sum(
        1
        for artifact_id in (report.artifact_refs or {}).values()
        if (artifact := artifacts.get(artifact_id)) is not None
        and artifact_visible_for_session(session, artifact, mode_registry)
    )


def _visible_report_warning_count(
    session: SessionRecord,
    report: ReportRecord,
    mode_registry: ModeRegistry | None,
) -> int:
    visible_warning_ids = {
        warning.id
        for warning in editor_visible_warnings(session, mode_registry)
    }
    return sum(1 for warning_id in report.warning_ids if warning_id in visible_warning_ids)

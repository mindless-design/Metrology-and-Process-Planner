"""Build canonical report documents from session documents."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    WarningRecord,
    built_in_mode_registry,
    utc_now_iso,
)
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)
from metrology_process_planner.reporting.builder_summaries import (
    capture_summary,
    measurement_summaries,
)
from metrology_process_planner.reporting.grid_summary import grid_dataset_summaries
from metrology_process_planner.reporting.models import (
    ArtifactSummary,
    ReportDocument,
    ReportMetadata,
    WarningSummary,
)
from metrology_process_planner.reporting.numbering import ReportNumberer
from metrology_process_planner.reporting.section_visibility import (
    effective_report_sections,
    merged_report_sections,
)
from metrology_process_planner.reporting.sections import SectionGenerator
from metrology_process_planner.reporting.session_summary import (
    process_context_summary,
    session_summary,
)
from metrology_process_planner.reporting.templates import ReportTemplate
from metrology_process_planner.reporting.validation import ReportValidationFinding
from metrology_process_planner.workflows.editor.document import SessionDocument


class ReportModelBuilder:
    """Build renderer-neutral report documents from in-memory session documents."""

    def __init__(
        self,
        section_generator: SectionGenerator | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._section_generator = section_generator or SectionGenerator()
        self._mode_registry = mode_registry or built_in_mode_registry()

    def build(
        self,
        session_document: SessionDocument,
        template: ReportTemplate,
        findings: tuple[ReportValidationFinding, ...] = (),
        requested_sections: tuple[str, ...] = (),
        theme_id: str = "light",
    ) -> ReportDocument:
        """Build and number a report document."""

        base = _base_document(
            session_document,
            template,
            findings,
            theme_id,
            self._mode_registry,
        )
        section_ids = effective_report_sections(
            session_document.session,
            merged_report_sections(
                template.ordered_sections(requested_sections),
                self._mode_sections(session_document),
            ),
            self._mode_registry,
        )
        sections = tuple(
            self._section_generator.generate(section_id, base)
            for section_id in section_ids
        )
        return ReportNumberer().number(replace(base, sections=sections))

    def _mode_sections(self, document: SessionDocument) -> tuple[str, ...]:
        return self._mode_registry.definition(document.session.mode.value).reporting.sections


def _base_document(
    document: SessionDocument,
    template: ReportTemplate,
    findings: tuple[ReportValidationFinding, ...],
    theme_id: str,
    mode_registry: ModeRegistry,
) -> ReportDocument:
    session = document.session
    artifacts = tuple(
        _artifact_summary(item)
        for item in (session.artifacts or {}).values()
        if artifact_visible_for_session(session, item, mode_registry)
    )
    visible_warnings = tuple(
        warning
        for warning in session.warnings
        if warning_visible_for_session(session, warning, mode_registry)
    )
    warnings = (
        tuple(_warning_summary(item) for item in visible_warnings)
        + _finding_warnings(findings)
    )
    return ReportDocument(
        ReportMetadata(
            _report_id(session.id, template.template_id),
            template.name,
            template.template_id,
            template.name,
            utc_now_iso(),
            session.id,
            session.name,
            theme_id=theme_id,
        ),
        {str(key): str(value) for key, value in (session.metadata or {}).items()},
        session_summary(document, mode_registry),
        tuple(capture_summary(session, capture, mode_registry) for capture in session.captures),
        tuple(measurement_summaries(document, mode_registry)),
        artifacts,
        warnings,
        process_context_summary(session, mode_registry),
        (),
        {
            "setup": session.setup.to_dict(),
            "mode": session.mode.value,
            "grid_datasets": grid_dataset_summaries(session, mode_registry),
        },
    )


def _artifact_summary(artifact: ArtifactRecord) -> ArtifactSummary:
    status = artifact.status.value
    return ArtifactSummary(
        artifact.id,
        artifact.label,
        artifact.type,
        artifact.owner.role,
        status,
        artifact.relative_path,
        artifact.owner.owner_type,
        artifact.owner.owner_id,
        artifact.status != ArtifactStatus.PRESENT,
        dict(artifact.extensions or {}),
    )


def _warning_summary(warning: WarningRecord) -> WarningSummary:
    return WarningSummary(
        warning.id,
        warning.severity,
        warning.message,
        warning.source,
        warning.code,
    )


def _finding_warnings(findings: tuple[ReportValidationFinding, ...]) -> tuple[WarningSummary, ...]:
    return tuple(
        WarningSummary(item.code, item.severity, item.message, "report_validation", item.code)
        for item in findings
    )


def _report_id(session_id: str, template_id: str) -> str:
    return f"{session_id}-{template_id}"

"""Build Reporting Workbench view models from session documents."""

from __future__ import annotations

from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.reporting import ReportModelBuilder, ReportReadinessService
from metrology_process_planner.reporting.models import ReportSection
from metrology_process_planner.reporting.readiness import ReadinessStatus, ReportReadiness
from metrology_process_planner.reporting.requests import ReportRequest
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.ui.reporting_workbench.actions import (
    primary_action_id,
    workbench_actions,
)
from metrology_process_planner.ui.reporting_workbench.status import (
    readiness_groups,
    readiness_label,
    route_result_fields,
)
from metrology_process_planner.ui.reporting_workbench.view_models import (
    ReportingWorkbenchModel,
    ReportPreviewModel,
    SectionPreviewModel,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.document import SessionDocument


class ReportingWorkbenchPresenter:
    """Build view models for the Reporting Workbench."""

    def __init__(self, mode_registry: ModeRegistry | None = None) -> None:
        self._mode_registry = mode_registry

    def build(
        self,
        document: SessionDocument,
        request: ReportRequest,
        selected_section_id: str = "",
        last_result: CommandRouteResult | None = None,
    ) -> ReportingWorkbenchModel:
        """Return a workbench model for the current request."""

        templates = built_in_report_templates()
        template = templates[request.template_id]
        readiness = ReportReadinessService(mode_registry=self._mode_registry).assess_request(
            document,
            request,
        )
        report = ReportModelBuilder(mode_registry=self._mode_registry).build(
            document,
            template,
            readiness.all_findings(),
            request.normalized_sections(),
            request.theme_id,
        )
        selected = selected_section_id or (report.sections[0].section_id if report.sections else "")
        sections = tuple(_section_model(section) for section in report.sections)
        return ReportingWorkbenchModel(
            f"Report Workbench: {document.session.name}",
            _header(document, request, readiness.status),
        tuple((item.template_id, item.name) for item in templates.values()),
        request.template_id,
        (("light", "Light"), ("dark", "Dark")),
        request.theme_id,
        primary_action_id(readiness),
            workbench_actions(readiness, last_result),
            sections,
            _preview(report.sections, selected),
            _inspector(readiness),
            _status(readiness),
            route_result_fields(last_result),
        )


def _header(
    document: SessionDocument,
    request: ReportRequest,
    readiness: ReadinessStatus,
) -> tuple[tuple[str, str], ...]:
    return (
        ("Session", document.session.name),
        ("Mode", document.session.mode.value),
        ("Template", request.template_id),
        ("Theme", request.theme_id),
        ("Readiness", readiness_label(readiness)),
        ("Warnings", str(len(document.warning_view_models))),
        ("Output", str(request.output_dir or document.session.paths.reports)),
        ("Dirty", "Unsaved" if document.dirty_state.is_dirty else "Saved"),
    )


def _section_model(section: ReportSection) -> SectionPreviewModel:
    return SectionPreviewModel(
        section.section_id,
        section.title,
        _section_type(section.section_id),
        section.body,
        tuple(table.title for table in section.tables),
        tuple(figure.title for figure in section.figures),
    )


def _section_type(section_id: str) -> str:
    if "gallery" in section_id:
        return "image_gallery"
    if "table" in section_id or "summary" in section_id:
        return "table"
    if section_id == "cover_page":
        return "cover"
    if section_id == "appendix":
        return "appendix"
    return "summary"


def _preview(sections: tuple[ReportSection, ...], selected_id: str) -> ReportPreviewModel:
    section = next((item for item in sections if item.section_id == selected_id), None)
    if section is None:
        return ReportPreviewModel("", "empty", ("No section selected.",))
    lines = section.body + tuple(table.title for table in section.tables)
    lines += tuple(figure.notes or figure.title for figure in section.figures)
    return ReportPreviewModel(
        section.section_id,
        _section_type(section.section_id),
        lines or (section.title,),
    )


def _inspector(readiness: ReportReadiness) -> tuple[tuple[str, str], ...]:
    return readiness_groups(readiness)


def _status(readiness: ReportReadiness) -> str:
    if readiness.blocking_issues:
        return readiness.blocking_issues[0].message
    if readiness.warnings:
        return f"{len(readiness.warnings)} report warning(s)."
    return readiness_label(readiness.status)

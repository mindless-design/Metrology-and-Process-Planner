"""Headless report generation service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.reporting.artifacts import ReportArtifactRegistrar
from metrology_process_planner.reporting.backends import (
    ExportedReport,
    ReportBackend,
    ReportExporter,
)
from metrology_process_planner.reporting.builder import ReportModelBuilder
from metrology_process_planner.reporting.csv_backend import CsvReportBackend
from metrology_process_planner.reporting.image_backend import ImagePackageBackend
from metrology_process_planner.reporting.pdf_backend import PdfReportBackend
from metrology_process_planner.reporting.pptx_backend import PowerPointReportBackend
from metrology_process_planner.reporting.readiness import ReportReadiness
from metrology_process_planner.reporting.requests import ReportRequest
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.workflows.editor.document import SessionDocument


@dataclass(frozen=True)
class ReportGenerationResult:
    """Result of a report generation run."""

    readiness: ReportReadiness
    exported: ExportedReport | None = None
    updated_session: SessionRecord | None = None
    message: str = ""


class ReportGenerationService:
    """Generate reports from session documents without KLayout dependencies."""

    def __init__(
        self,
        registrar: ReportArtifactRegistrar | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._registrar = registrar or ReportArtifactRegistrar()
        self._mode_registry = mode_registry

    def generate(
        self,
        document: SessionDocument,
        request: ReportRequest,
        session_folder: Path,
    ) -> ReportGenerationResult:
        """Validate, export, and register a report."""

        templates = built_in_report_templates()
        output_dir = request.resolved_output_dir(session_folder / "reports")
        readiness = _readiness(document, request, session_folder, self._mode_registry)
        if not readiness.can_generate():
            return ReportGenerationResult(readiness, message="Report export is blocked.")
        template = templates[request.template_id]
        report = ReportModelBuilder(mode_registry=self._mode_registry).build(
            document,
            template,
            readiness.all_findings(),
            request.normalized_sections(),
            request.theme_id,
        )
        exporter = ReportExporter(_backends(request, session_folder))
        exported = exporter.export(report, output_dir)
        updated = self._registrar.register(
            document.session,
            report,
            exported,
            session_folder,
            self._mode_registry,
        )
        return ReportGenerationResult(readiness, exported, updated, "Report exported.")


def _readiness(
    document: SessionDocument,
    request: ReportRequest,
    session_folder: Path,
    mode_registry: ModeRegistry | None = None,
) -> ReportReadiness:
    from metrology_process_planner.reporting.readiness import ReportReadinessService

    return ReportReadinessService(mode_registry=mode_registry).assess_request(
        document,
        request,
        session_folder,
    )


def _backends(request: ReportRequest, session_folder: Path) -> tuple[ReportBackend, ...]:
    backends: list[ReportBackend] = []
    for format_name in request.output_formats:
        if format_name == "pptx":
            backends.append(PowerPointReportBackend(session_folder))
        if format_name == "pdf":
            backends.append(PdfReportBackend())
        if format_name == "csv":
            backends.append(CsvReportBackend())
        if format_name in {"images", "images.zip"}:
            backends.append(ImagePackageBackend(session_folder))
    return tuple(backends)

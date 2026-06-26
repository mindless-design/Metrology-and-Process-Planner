"""Request-specific report readiness checks."""

from __future__ import annotations

from pathlib import Path

from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.reporting.requests import ReportRequest
from metrology_process_planner.reporting.section_visibility import effective_report_sections
from metrology_process_planner.reporting.templates import ReportTemplate
from metrology_process_planner.reporting.validation import ReportValidationFinding
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.editor.document import SessionDocument


def request_findings(
    document: SessionDocument,
    request: ReportRequest,
    template: ReportTemplate,
    artifact_root: Path | None,
    mode_registry: ModeRegistry | None = None,
) -> tuple[ReportValidationFinding, ...]:
    """Return validation findings tied to a concrete report request."""

    findings = list(_template_findings(document, template))
    findings.extend(
        _section_findings(
            document,
            effective_report_sections(
                document.session,
                template.ordered_sections(request.normalized_sections()),
                mode_registry,
            ),
            mode_registry,
        )
    )
    findings.extend(_output_findings(request, artifact_root))
    findings.extend(_exporter_findings(request))
    return tuple(findings)


def _template_findings(
    document: SessionDocument,
    template: ReportTemplate,
) -> tuple[ReportValidationFinding, ...]:
    if not template.supports_mode(document.session.mode.value):
        return (
            ReportValidationFinding(
                "unsupported_template",
                f"Template {template.template_id} does not support {document.session.mode.value}.",
                "error",
            ),
        )
    return ()


def _section_findings(
    document: SessionDocument,
    sections: tuple[str, ...],
    mode_registry: ModeRegistry | None,
) -> tuple[ReportValidationFinding, ...]:
    if not mode_is_process_aware(document.session, mode_registry):
        return ()
    if "process_context" in sections and not document.session.process_context.recipe_reference:
        return (
            ReportValidationFinding(
                "missing_process_context",
                "Process context is required for the selected report sections.",
                "error",
            ),
        )
    return ()


def _output_findings(
    request: ReportRequest,
    artifact_root: Path | None,
) -> tuple[ReportValidationFinding, ...]:
    output_dir = request.resolved_output_dir(artifact_root or Path("."))
    if output_dir.exists() and not output_dir.is_dir():
        return (
            ReportValidationFinding(
                "invalid_output_path",
                "Report output path is not a folder.",
                "error",
            ),
        )
    return ()


def _exporter_findings(request: ReportRequest) -> tuple[ReportValidationFinding, ...]:
    supported = {"pptx", "pdf", "csv", "images", "images.zip"}
    unknown = tuple(
        format_name for format_name in request.output_formats if format_name not in supported
    )
    return tuple(
        ReportValidationFinding("exporter_unavailable", f"Exporter unavailable: {item}", "error")
        for item in unknown
    )

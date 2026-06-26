"""Report readiness service for user-visible export status."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.reporting.readiness_requests import request_findings
from metrology_process_planner.reporting.requests import (
    PlaceholderPolicy,
    ReportRequest,
)
from metrology_process_planner.reporting.templates import ReportTemplate
from metrology_process_planner.reporting.validation import ReportValidationFinding, ReportValidator
from metrology_process_planner.workflows.editor.document import SessionDocument


class ReadinessStatus(str, Enum):
    """High-level report generation readiness states."""

    READY = "ready"
    READY_WITH_WARNINGS = "ready_with_warnings"
    MISSING_REQUIRED_ARTIFACTS = "missing_required_artifacts"
    STALE_OUTPUTS = "stale_outputs"
    INVALID_SESSION = "invalid_session"
    EXPORT_BLOCKED = "export_blocked"
    VALIDATION_FAILED = "validation_failed"


@dataclass(frozen=True)
class ReportReadiness:
    """Structured report readiness result."""

    status: ReadinessStatus
    blocking_issues: tuple[ReportValidationFinding, ...] = ()
    warnings: tuple[ReportValidationFinding, ...] = ()
    missing_required_artifacts: tuple[str, ...] = ()
    missing_optional_artifacts: tuple[str, ...] = ()
    stale_artifacts: tuple[str, ...] = ()
    suggested_repairs: tuple[str, ...] = ()

    def can_generate(self) -> bool:
        """Return whether export may proceed."""

        return self.status in {ReadinessStatus.READY, ReadinessStatus.READY_WITH_WARNINGS}

    @property
    def findings(self) -> tuple[ReportValidationFinding, ...]:
        """Return all readiness findings for backward-compatible callers."""

        return self.blocking_issues + self.warnings

    def all_findings(self) -> tuple[ReportValidationFinding, ...]:
        """Return all readiness findings."""

        return self.findings


class ReportReadinessService:
    """Assess whether a report can be generated."""

    def __init__(
        self,
        validator: ReportValidator | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._mode_registry = mode_registry
        self._validator = validator or ReportValidator(mode_registry=mode_registry)

    def assess(
        self,
        document: SessionDocument,
        template: ReportTemplate,
        artifact_root: Path | None = None,
    ) -> ReportReadiness:
        """Return report readiness for a session and template."""

        findings = self._validator.validate(document, template.required_sections, artifact_root)
        return _readiness_from_findings(findings)

    def assess_request(
        self,
        document: SessionDocument,
        request: ReportRequest,
        artifact_root: Path | None = None,
    ) -> ReportReadiness:
        """Return readiness for a full report request."""

        from metrology_process_planner.reporting.templates import built_in_report_templates

        templates = built_in_report_templates()
        template = templates.get(request.template_id)
        if template is None:
            finding = ReportValidationFinding(
                "unsupported_template",
                f"Unsupported report template: {request.template_id}",
                "error",
            )
            return _blocked(ReadinessStatus.EXPORT_BLOCKED, (finding,))
        findings = list(
            self._validator.validate(document, template.required_sections, artifact_root)
        )
        findings.extend(
            request_findings(
                document,
                request,
                template,
                artifact_root,
                self._mode_registry,
            )
        )
        if request.placeholder_policy is PlaceholderPolicy.PLACEHOLDER_REQUIRED:
            findings = _downgrade_missing_artifacts(findings)
            return _readiness_from_findings(tuple(findings), block_missing_warnings=False)
        if request.placeholder_policy is PlaceholderPolicy.STRICT:
            findings = _upgrade_missing_artifacts(findings)
        return _readiness_from_findings(tuple(findings))


def _readiness_from_findings(
    findings: tuple[ReportValidationFinding, ...],
    block_missing_warnings: bool = True,
) -> ReportReadiness:
    blocking = tuple(item for item in findings if item.severity == "error")
    warnings = tuple(item for item in findings if item.severity != "error")
    missing = tuple(item.artifact_id for item in findings if item.code == "missing_artifact")
    stale = tuple(item.artifact_id for item in findings if item.code == "stale_artifact")
    if blocking:
        return _blocked(ReadinessStatus.VALIDATION_FAILED, blocking, warnings, missing, stale)
    status = _readiness_status(warnings, missing, stale, block_missing_warnings)
    return ReportReadiness(
        status,
        (),
        warnings,
        missing_required_artifacts=missing,
        stale_artifacts=stale,
        suggested_repairs=_repairs(findings),
    )


def _readiness_status(
    warnings: tuple[ReportValidationFinding, ...],
    missing: tuple[str, ...],
    stale: tuple[str, ...],
    block_missing_warnings: bool,
) -> ReadinessStatus:
    if missing and block_missing_warnings:
        return ReadinessStatus.MISSING_REQUIRED_ARTIFACTS
    if stale:
        return ReadinessStatus.STALE_OUTPUTS
    return ReadinessStatus.READY_WITH_WARNINGS if warnings else ReadinessStatus.READY


def _blocked(
    status: ReadinessStatus,
    blocking: tuple[ReportValidationFinding, ...],
    warnings: tuple[ReportValidationFinding, ...] = (),
    missing: tuple[str, ...] = (),
    stale: tuple[str, ...] = (),
) -> ReportReadiness:
    return ReportReadiness(
        status,
        blocking,
        warnings,
        missing_required_artifacts=missing,
        stale_artifacts=stale,
        suggested_repairs=_repairs(blocking + warnings),
    )


def _downgrade_missing_artifacts(
    findings: list[ReportValidationFinding],
) -> list[ReportValidationFinding]:
    return [
        ReportValidationFinding(item.code, item.message, "warning", item.item_id, item.artifact_id)
        if item.code == "missing_artifact"
        else item
        for item in findings
    ]


def _upgrade_missing_artifacts(
    findings: list[ReportValidationFinding],
) -> list[ReportValidationFinding]:
    return [
        ReportValidationFinding(item.code, item.message, "error", item.item_id, item.artifact_id)
        if item.code == "missing_artifact"
        else item
        for item in findings
    ]


def _repairs(findings: tuple[ReportValidationFinding, ...]) -> tuple[str, ...]:
    repairs = []
    if any(item.code in {"missing_artifact", "invalid_image_path"} for item in findings):
        repairs.append("Regenerate missing artifacts or keep report placeholders.")
    if any(item.code == "stale_artifact" for item in findings):
        repairs.append("Regenerate stale artifacts before export.")
    return tuple(repairs)

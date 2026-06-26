"""Report readiness validation with structured findings."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ArtifactRecord, ArtifactStatus, ModeRegistry
from metrology_process_planner.workflows.editor.document import SessionDocument


@dataclass(frozen=True)
class ReportValidationFinding:
    """One structured report validation finding."""

    code: str
    message: str
    severity: str = "warning"
    item_id: str = ""
    artifact_id: str = ""


class ReportValidator:
    """Validate session data before export."""

    def __init__(self, mode_registry: ModeRegistry | None = None) -> None:
        self._mode_registry = mode_registry

    def validate(
        self,
        document: SessionDocument,
        required_sections: tuple[str, ...],
        artifact_root: Path | None = None,
    ) -> tuple[ReportValidationFinding, ...]:
        """Return structured validation findings for report generation."""

        findings: list[ReportValidationFinding] = []
        findings.extend(_metadata_findings(document))
        findings.extend(_duplicate_findings(document))
        findings.extend(_required_capture_findings(document, required_sections))
        findings.extend(_artifact_findings(document, artifact_root, self._mode_registry))
        return tuple(findings)


def _metadata_findings(document: SessionDocument) -> list[ReportValidationFinding]:
    session = document.session
    findings = []
    if not session.id:
        findings.append(
            ReportValidationFinding("missing_session_id", "Session id is required.", "error")
        )
    if not session.name:
        findings.append(
            ReportValidationFinding("missing_session_name", "Session name is required.")
        )
    return findings


def _duplicate_findings(document: SessionDocument) -> list[ReportValidationFinding]:
    findings: list[ReportValidationFinding] = []
    capture_ids = tuple(capture.id for capture in document.session.captures)
    findings.extend(_duplicates("duplicate_capture_id", capture_ids))
    artifact_ids = tuple((document.session.artifacts or {}).keys())
    findings.extend(_duplicates("duplicate_artifact_id", artifact_ids))
    return findings


def _required_capture_findings(
    document: SessionDocument,
    required_sections: tuple[str, ...],
) -> list[ReportValidationFinding]:
    if "capture_table" not in required_sections and "artifact_gallery" not in required_sections:
        return []
    if document.session.captures:
        return []
    return [
        ReportValidationFinding("missing_captures", "At least one capture is required.", "error")
    ]


def _artifact_findings(
    document: SessionDocument,
    artifact_root: Path | None,
    mode_registry: ModeRegistry | None,
) -> list[ReportValidationFinding]:
    findings: list[ReportValidationFinding] = []
    for artifact in (document.session.artifacts or {}).values():
        if not artifact_visible_for_session(document.session, artifact, mode_registry):
            continue
        findings.extend(_findings_for_artifact(artifact, artifact_root))
    return findings


def _findings_for_artifact(
    artifact: ArtifactRecord,
    artifact_root: Path | None,
) -> list[ReportValidationFinding]:
    findings = _artifact_status_findings(artifact)
    if _artifact_path_missing(artifact, artifact_root):
        findings.append(
            _artifact_finding(
                "invalid_image_path",
                artifact.id,
                "Artifact path does not exist.",
            )
        )
    return findings


def _artifact_status_findings(artifact: ArtifactRecord) -> list[ReportValidationFinding]:
    findings: list[ReportValidationFinding] = []
    if not artifact.label:
        findings.append(
            _artifact_finding("missing_artifact_label", artifact.id, "Artifact label is missing.")
        )
    if artifact.status in {ArtifactStatus.MISSING, ArtifactStatus.FAILED}:
        findings.append(
            _artifact_finding("missing_artifact", artifact.id, "Required artifact is not present.")
        )
    if artifact.status is ArtifactStatus.PLACEHOLDER:
        findings.append(
            _artifact_finding(
                "placeholder_artifact",
                artifact.id,
                "Report will use a placeholder artifact.",
            )
        )
    if artifact.status is ArtifactStatus.STALE:
        findings.append(_artifact_finding("stale_artifact", artifact.id, "Artifact is stale."))
    return findings


def _artifact_path_missing(artifact: ArtifactRecord, artifact_root: Path | None) -> bool:
    return bool(
        artifact_root is not None
        and artifact.relative_path
        and not (artifact_root / artifact.relative_path).exists()
    )


def _duplicates(code: str, values: Iterable[str]) -> list[ReportValidationFinding]:
    seen: set[str] = set()
    findings: list[ReportValidationFinding] = []
    for value in values:
        item = str(value)
        if item in seen:
            findings.append(
                ReportValidationFinding(code, f"Duplicate id: {item}", "error", item_id=item)
            )
        seen.add(item)
    return findings


def _artifact_finding(code: str, artifact_id: str, message: str) -> ReportValidationFinding:
    return ReportValidationFinding(code, message, "warning", artifact_id=artifact_id)

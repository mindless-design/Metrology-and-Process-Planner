"""Filesystem-backed artifact integrity auditing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactRecord, ArtifactStatus, SessionRecord
from metrology_process_planner.infrastructure.validation_models import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    issue,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk


@dataclass(frozen=True)
class ArtifactAuditResult:
    """Structured artifact audit report with repair hints."""

    report: ValidationReport
    scanned_files: tuple[str, ...]
    orphaned_files: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Serialize the audit result to JSON-compatible data."""

        return {
            "report": self.report.to_dict(),
            "scanned_files": list(self.scanned_files),
            "orphaned_files": list(self.orphaned_files),
        }


def audit_artifacts(session: SessionRecord, paths: SessionPaths) -> ArtifactAuditResult:
    """Audit session artifact registry entries against files on disk."""

    managed_files = _managed_files(paths)
    referenced_paths = _referenced_paths(session)
    issues: list[ValidationIssue] = []
    for artifact_id, artifact in (session.artifacts or {}).items():
        issues.extend(_artifact_issues(artifact_id, artifact, paths))
    duplicates = _duplicate_paths(session)
    for relative_path in duplicates:
        issues.append(_warning(f"artifacts.{relative_path}", "Duplicate artifact path."))
    orphaned = tuple(sorted(managed_files.difference(referenced_paths)))
    for relative_path in orphaned:
        issues.append(_warning(relative_path, "Orphaned artifact file."))
    return ArtifactAuditResult(
        ValidationReport(f"artifact_audit:{session.id}", tuple(issues)),
        tuple(sorted(managed_files)),
        orphaned,
    )


def _artifact_issues(
    artifact_id: str,
    artifact: ArtifactRecord,
    paths: SessionPaths,
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    location = f"artifacts.{artifact_id}"
    if not artifact.relative_path:
        issues.append(_error(location, "Artifact path is missing."))
        return tuple(issues)
    if artifact.status is ArtifactStatus.FAILED:
        issues.append(_warning(location, "Artifact generation previously failed."))
    if artifact.path_mode.value == "external":
        return tuple(issues)
    try:
        disk_path = artifact_path_to_disk(paths.folder, artifact.relative_path)
    except ValueError as exc:
        return (_error(location, str(exc)),)
    if not disk_path.exists():
        issues.append(_warning(location, f"Missing artifact file: {artifact.relative_path}"))
        return tuple(issues)
    issues.extend(_checksum_issues(location, artifact, disk_path))
    return tuple(issues)


def _checksum_issues(
    location: str,
    artifact: ArtifactRecord,
    disk_path: Path,
) -> tuple[ValidationIssue, ...]:
    expected = artifact.file.sha256
    if not expected:
        return ()
    actual = _sha256(disk_path)
    if actual == expected:
        return ()
    return (_warning(location, "Checksum mismatch."),)


def _managed_files(paths: SessionPaths) -> set[str]:
    roots = (paths.images_dir, paths.drawings_dir, paths.reports_dir, paths.process_outputs_dir)
    files: set[str] = set()
    for root in roots:
        if root.exists():
            files.update(
                str(path.relative_to(paths.folder)).replace("\\", "/")
                for path in root.rglob("*")
                if path.is_file()
            )
    return files


def _referenced_paths(session: SessionRecord) -> set[str]:
    return {
        artifact.relative_path
        for artifact in (session.artifacts or {}).values()
        if artifact.relative_path
    }


def _duplicate_paths(session: SessionRecord) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for artifact in (session.artifacts or {}).values():
        if artifact.relative_path in seen:
            duplicates.add(artifact.relative_path)
        seen.add(artifact.relative_path)
    return tuple(sorted(duplicates))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _error(location: str, message: str) -> ValidationIssue:
    return issue(
        ValidationSeverity.ERROR,
        "artifact_registry",
        location,
        message,
        "Fix the artifact metadata.",
    )


def _warning(location: str, message: str) -> ValidationIssue:
    return issue(
        ValidationSeverity.WARNING,
        "artifact_registry",
        location,
        message,
        "Regenerate or remove the artifact.",
    )

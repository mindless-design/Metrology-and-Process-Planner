"""Structured artifact warning helpers."""

from __future__ import annotations

from metrology_process_planner.domains.session import ArtifactRecord, WarningRecord

ARTIFACT_MISSING = "ARTIFACT_MISSING"
ARTIFACT_STALE = "ARTIFACT_STALE"
ARTIFACT_FAILED = "ARTIFACT_FAILED"
ARTIFACT_OWNER_MISSING = "ARTIFACT_OWNER_MISSING"
ARTIFACT_DEPENDENCY_MISSING = "ARTIFACT_DEPENDENCY_MISSING"
ARTIFACT_REPAIR_UNAVAILABLE = "ARTIFACT_REPAIR_UNAVAILABLE"
ARTIFACT_REGENERATION_FAILED = "ARTIFACT_REGENERATION_FAILED"
ARTIFACT_RELINK_REQUIRED = "ARTIFACT_RELINK_REQUIRED"
SOURCE_LAYOUT_REQUIRED_FOR_REPAIR = "SOURCE_LAYOUT_REQUIRED_FOR_REPAIR"
PARENT_IMAGE_REQUIRED_FOR_REPAIR = "PARENT_IMAGE_REQUIRED_FOR_REPAIR"
RECIPE_REQUIRED_FOR_REPAIR = "RECIPE_REQUIRED_FOR_REPAIR"
SOLVER_REQUIRED_FOR_REPAIR = "SOLVER_REQUIRED_FOR_REPAIR"
CSV_STALE = "CSV_STALE"
REPORT_STALE = "REPORT_STALE"


def warning_id(artifact_id: str, code: str) -> str:
    """Return a stable artifact warning id."""

    return f"artifact-{artifact_id}-{code.lower()}"


def artifact_warning(
    artifact: ArtifactRecord,
    code: str,
    message: str,
    details: str,
    suggestion: str,
    severity: str = "warning",
) -> WarningRecord:
    """Build an advisory warning linked to one artifact."""

    return WarningRecord(
        id=warning_id(artifact.id, code),
        message=message,
        severity=severity,
        artifact_path=artifact.relative_path,
        source="artifact",
        code=code,
        related_item_refs=_related_items(artifact),
        related_artifact_refs=(artifact.id,),
        technical_details=details,
        repair_suggestion=suggestion,
    )


def upsert_warning(
    warnings: dict[str, WarningRecord],
    warning: WarningRecord,
) -> WarningRecord:
    """Store a warning unless the user has intentionally ignored it."""

    existing = warnings.get(warning.id)
    if existing is not None and existing.status == "ignored":
        return existing
    warnings[warning.id] = warning
    return warning


def clear_open_warning(warnings: dict[str, WarningRecord], warning_id_value: str) -> None:
    """Remove an unresolved warning while preserving ignored warning history."""

    existing = warnings.get(warning_id_value)
    if existing is not None and existing.status != "ignored":
        warnings.pop(warning_id_value)


def _related_items(artifact: ArtifactRecord) -> tuple[str, ...]:
    owner = artifact.owner
    if not owner.owner_type or not owner.owner_id:
        return ()
    return (f"{owner.owner_type}:{owner.owner_id}",)

"""Result and warning helpers for editor/rendering refresh."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
    WarningRecord,
    utc_now_iso,
)
from metrology_process_planner.persistence.drawing_store import (
    StoredDrawingExport,
    upsert_drawing_artifacts,
)
from metrology_process_planner.workflows.editor.render_bridge_models import (
    DrawingOwnerRef,
    RenderRefreshResult,
)


def _capture_success(
    session: SessionRecord,
    capture_id: str,
    stored: StoredDrawingExport,
    mode_registry: ModeRegistry | None = None,
) -> RenderRefreshResult:
    owner = DrawingOwnerRef("capture", capture_id)
    session = _without_render_warnings(session, owner, stored.role)
    warnings = tuple(
        _warning(owner, stored.role, f"output-{index}", message)
        for index, message in enumerate(stored.export_result.warnings, start=1)
    )
    session = _upsert_warnings(
        upsert_drawing_artifacts(session, stored, mode_registry),
        warnings,
    )
    return RenderRefreshResult(
        status="warning" if warnings else "success",
        session=session,
        updated_artifact_paths=stored.paths,
        warnings=warnings,
    )


def _session_drawing_success(
    session: SessionRecord,
    owner: DrawingOwnerRef,
    role: str,
    stored: StoredDrawingExport,
    mode_registry: ModeRegistry | None = None,
) -> RenderRefreshResult:
    session = _without_render_warnings(session, owner, role)
    warnings = tuple(
        _warning(owner, role, f"output-{index}", message)
        for index, message in enumerate(stored.export_result.warnings, start=1)
    )
    session = _upsert_warnings(
        upsert_drawing_artifacts(session, stored, mode_registry),
        warnings,
    )
    return RenderRefreshResult(
        status="warning" if warnings else "success",
        session=session,
        updated_artifact_paths=stored.paths,
        warnings=warnings,
    )


def _with_warning(
    session: SessionRecord,
    owner: DrawingOwnerRef,
    role: str,
    warning: WarningRecord,
    status: str,
) -> RenderRefreshResult:
    session = _upsert_warnings(_without_render_warnings(session, owner, role), (warning,))
    session = _upsert_failed_artifact(session, owner, role, warning)
    return RenderRefreshResult(status=status, session=session, warnings=(warning,))


def _warning(
    owner: DrawingOwnerRef,
    role: str,
    kind: str,
    message: str,
    severity: str = "warning",
    artifact_path: Optional[str] = None,
) -> WarningRecord:
    return WarningRecord(
        id=_warning_id(owner, role, kind),
        message=message,
        severity=severity,
        artifact_path=artifact_path,
        source="render_bridge",
        code=_warning_code(role, kind),
        related_item_refs=(f"{owner.owner_type}:{owner.owner_id}",),
        technical_details=message,
        repair_suggestion="Regenerate the artifact from the session editor.",
    )


def _warning_code(role: str, kind: str) -> str:
    if "annotation" not in role and "line_image" not in role:
        return f"render_{kind}"
    if kind == "validation":
        return "ANNOTATION_TRANSFORM_FAILED"
    if kind == "missing-owner":
        return "ANNOTATION_SOURCE_IMAGE_MISSING"
    if kind == "export":
        return "ANNOTATION_RENDER_FAILED"
    return "ANNOTATION_RENDER_FAILED"


def _message(status: str, updated_count: int, warning_count: int) -> str:
    if status == "error":
        return "One or more drawings failed to refresh."
    if status == "warning":
        return "Refreshed drawings with warnings."
    if updated_count:
        return "Refreshed drawing artifacts."
    if warning_count:
        return "Drawing refresh produced warnings."
    return "No drawing refresh was needed."


def _warning_id(owner: DrawingOwnerRef, role: str, kind: str) -> str:
    return "render-" + _safe_id(f"{owner.owner_type}-{owner.owner_id}-{role}-{kind}")


def _without_render_warnings(
    session: SessionRecord,
    owner: DrawingOwnerRef,
    role: str,
) -> SessionRecord:
    prefix = _warning_id(owner, role, "")
    return replace(
        session,
        warnings=tuple(
            warning for warning in session.warnings if not warning.id.startswith(prefix)
        ),
    )


def _upsert_warnings(
    session: SessionRecord,
    warnings: Iterable[WarningRecord],
) -> SessionRecord:
    incoming = tuple(warnings)
    if not incoming:
        return session
    incoming_ids = {warning.id for warning in incoming}
    return replace(
        session,
        warnings=tuple(warning for warning in session.warnings if warning.id not in incoming_ids)
        + incoming,
    )


def _upsert_failed_artifact(
    session: SessionRecord,
    owner: DrawingOwnerRef,
    role: str,
    warning: WarningRecord,
) -> SessionRecord:
    artifact = _failed_svg_artifact(owner, role, warning)
    artifacts = dict(session.artifacts or {})
    artifacts[artifact.id] = artifact
    return replace(session, artifacts=artifacts)


def _failed_svg_artifact(
    owner: DrawingOwnerRef,
    role: str,
    warning: WarningRecord,
) -> ArtifactRecord:
    owner_role = f"{role}_svg"
    return ArtifactRecord(
        id=artifact_id(owner.owner_type, owner.owner_id, owner_role),
        type="svg",
        label=f"{role} SVG",
        relative_path=_expected_svg_path(owner, role),
        owner=ArtifactOwnerRef(owner.owner_type, owner.owner_id, owner_role),
        status=ArtifactStatus.FAILED,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_artifact",
            repair_suggestion="Regenerate the artifact from the session editor.",
            last_attempt_at=utc_now_iso(),
            last_error=warning.message,
        ),
        warning_ids=(warning.id,),
    )


def _expected_svg_path(owner: DrawingOwnerRef, role: str) -> str:
    if owner.owner_type == "capture":
        stem = _safe_id(f"{owner.owner_id}-{role}")
    else:
        stem = _safe_id(f"{owner.owner_type}-{owner.owner_id}-{role}")
    return f"images/{stem}.svg"


def _safe_id(text: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_" else "-" for char in text)
    return cleaned.strip("-")

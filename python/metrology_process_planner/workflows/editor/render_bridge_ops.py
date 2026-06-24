"""Target-specific render refresh operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from metrology_process_planner.domains.session import CaptureRecord, SessionRecord
from metrology_process_planner.domains.session.artifact_query import first_display_artifact
from metrology_process_planner.persistence.drawing_store import StoredDrawingExport
from metrology_process_planner.rendering import (
    build_cross_section_drawing_scene,
    build_layout_annotation_scene,
)
from metrology_process_planner.workflows.editor.render_bridge_models import (
    CrossSectionRenderInput,
    RenderRefreshResult,
    RenderTarget,
)
from metrology_process_planner.workflows.editor.render_bridge_results import (
    _capture_success,
    _session_drawing_success,
    _warning,
    _with_warning,
)

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge


def refresh_target(
    bridge: SessionRenderBridge,
    session: SessionRecord,
    target: RenderTarget,
) -> RenderRefreshResult:
    """Refresh one capture-owned render target."""

    invalid = _invalid_target(session, target)
    if invalid is not None:
        return invalid
    capture = _capture_by_id(session, target.owner.owner_id)
    if capture is None:
        warning = _warning(
            target.owner,
            target.role,
            "missing-owner",
            f"Cannot refresh {target.role}; capture {target.owner.owner_id} was not found.",
            severity="error",
        )
        return _with_warning(session, target.owner, target.role, warning, "error")
    try:
        bridge.emit_render_event(
            "ArtifactRegenerationStarted",
            target.owner.owner_id,
            target.role,
        )
        scene = build_layout_annotation_scene(
            capture,
            first_display_artifact(session.artifacts or {}, "capture", capture.id),
        )
    except ValueError as exc:
        warning = _warning(target.owner, target.role, "validation", str(exc))
        bridge.emit_render_failure("ArtifactRegenerationFailed", target.owner.owner_id, exc)
        return _with_warning(session, target.owner, target.role, warning, "warning")
    try:
        stored = bridge.export_capture_scene(capture.id, scene)
    except OSError as exc:
        warning = _warning(target.owner, target.role, "export", str(exc), severity="error")
        bridge.emit_render_failure("ArtifactExportFailed", target.owner.owner_id, exc)
        return _with_warning(session, target.owner, target.role, warning, "error")
    _emit_export_diagnostics(
        bridge,
        "ArtifactRasterizationWarning",
        target.owner.owner_id,
        target.role,
        stored,
    )
    bridge.emit_render_event("ArtifactRegistered", target.owner.owner_id, target.role)
    return _capture_success(session, capture.id, stored)


def _emit_export_diagnostics(
    bridge: SessionRenderBridge,
    event_name: str,
    record_id: str,
    role: str,
    stored: StoredDrawingExport,
) -> None:
    diagnostics = stored.export_result.diagnostics
    if diagnostics:
        for diagnostic in diagnostics:
            bridge.emit_export_diagnostic(
                event_name,
                record_id,
                role,
                diagnostic.message,
                diagnostic.exception_type,
                diagnostic.exception_message,
                diagnostic.stack_trace,
            )
        return
    for message in stored.export_result.warnings:
        bridge.emit_render_event(
            "ArtifactRasterizationWarning",
            record_id,
            role,
            message,
            "warning",
        )


def refresh_cross_section(
    bridge: SessionRenderBridge,
    session: SessionRecord,
    source: CrossSectionRenderInput,
) -> RenderRefreshResult:
    """Refresh one session-owned cross-section drawing."""

    role = "cross_section"
    try:
        bridge.emit_render_event("ArtifactRegenerationStarted", source.owner.owner_id, role)
        scene = build_cross_section_drawing_scene(
            source.profile,
            source.materials,
            scene_id=source.scene_id or f"{source.owner.owner_id}-cross-section",
            title=source.title,
            include_legend=source.include_legend,
        )
    except ValueError as exc:
        warning = _warning(source.owner, role, "validation", str(exc))
        bridge.emit_render_failure("ArtifactRegenerationFailed", source.owner.owner_id, exc)
        return _with_warning(session, source.owner, role, warning, "warning")
    try:
        stored = bridge.export_owner_scene(
            source.owner.owner_type,
            source.owner.owner_id,
            scene,
        )
    except OSError as exc:
        warning = _warning(source.owner, role, "export", str(exc), severity="error")
        bridge.emit_render_failure("ArtifactExportFailed", source.owner.owner_id, exc)
        return _with_warning(session, source.owner, role, warning, "error")
    _emit_export_diagnostics(
        bridge,
        "ArtifactRasterizationWarning",
        source.owner.owner_id,
        role,
        stored,
    )
    bridge.emit_render_event("ArtifactRegistered", source.owner.owner_id, role)
    return _session_drawing_success(session, source.owner, role, stored)


def _invalid_target(session: SessionRecord, target: RenderTarget) -> RenderRefreshResult | None:
    if target.owner.owner_type != "capture":
        warning = _warning(target.owner, target.role, "unsupported-owner", "Unsupported owner.")
        return _with_warning(session, target.owner, target.role, warning, "error")
    if target.role != "layout_annotation":
        warning = _warning(target.owner, target.role, "unsupported-role", "Unsupported role.")
        return _with_warning(session, target.owner, target.role, warning, "error")
    return None


def _capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    for capture in session.captures:
        if capture.id == capture_id:
            return capture
    return None

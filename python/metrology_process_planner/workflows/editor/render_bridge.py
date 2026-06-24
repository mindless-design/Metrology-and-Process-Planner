"""Synchronize editor state with editable drawing/rendering artifacts."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import SessionRecord, utc_now_iso
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext
from metrology_process_planner.persistence.drawing_store import (
    SessionDrawingStore,
    StoredDrawingExport,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.rendering import SvgRasterizer
from metrology_process_planner.rendering.scene import DrawingScene
from metrology_process_planner.workflows.editor.render_bridge_models import (
    RenderRefreshRequest,
    RenderRefreshResult,
)
from metrology_process_planner.workflows.editor.render_bridge_refresh import refresh_request_targets
from metrology_process_planner.workflows.editor.render_bridge_results import _message


class SessionRenderBridge:
    """Refresh session drawing artifacts through pure planners and a store."""

    def __init__(
        self,
        paths: SessionPaths,
        drawing_store: SessionDrawingStore | None = None,
        rasterizer: SvgRasterizer | None = None,
        diagnostic_sink: DiagnosticSink | None = None,
    ) -> None:
        self._paths = paths
        self._store = drawing_store if drawing_store is not None else SessionDrawingStore()
        self._rasterizer = rasterizer
        self._diagnostics = diagnostic_sink

    def export_capture_scene(
        self,
        capture_id: str,
        scene: DrawingScene,
    ) -> StoredDrawingExport:
        """Export a capture-owned scene through the configured drawing store."""

        return self._store.export_capture_scene(
            self._paths,
            capture_id,
            scene,
            self._rasterizer,
        )

    def export_owner_scene(
        self,
        owner_type: str,
        owner_id: str,
        scene: DrawingScene,
    ) -> StoredDrawingExport:
        """Export a non-capture owned scene through the configured drawing store."""

        return self._store.export_owner_scene(
            self._paths,
            owner_type,
            owner_id,
            scene,
            self._rasterizer,
        )

    def emit_render_event(
        self,
        event_name: str,
        record_id: str,
        role: str,
        message: str = "",
        severity: str = "info",
    ) -> None:
        """Emit a render bridge diagnostic event when diagnostics are configured."""

        if self._diagnostics is None:
            return
        TraceContext.new(sink=self._diagnostics).emit(
            event_name,
            {
                "message": message or f"{role} artifact refresh event.",
                "severity": severity,
                "category": "artifact",
                "source_component": "SessionRenderBridge",
                "related_record_ids": (record_id,),
            },
        )

    def emit_render_failure(self, event_name: str, record_id: str, exc: BaseException) -> None:
        """Emit a structured render failure diagnostic event."""

        if self._diagnostics is None:
            return
        from metrology_process_planner.infrastructure.diagnostics_exceptions import (
            exception_payload,
        )

        TraceContext.new(sink=self._diagnostics).emit(
            event_name,
            exception_payload(
                exc,
                str(exc),
                severity="error",
                category="artifact",
                source_component="SessionRenderBridge",
                related_record_ids=(record_id,),
                remediation_hint="Review the render warning and regenerate the artifact.",
            ),
        )

    def emit_export_diagnostic(
        self,
        event_name: str,
        record_id: str,
        role: str,
        message: str,
        exception_type: str = "",
        exception_message: str = "",
        stack_trace: str = "",
    ) -> None:
        """Emit structured non-fatal export diagnostic details."""

        if self._diagnostics is None:
            return
        TraceContext.new(sink=self._diagnostics).emit(
            event_name,
            {
                "message": message,
                "severity": "warning",
                "category": "artifact",
                "source_component": "SessionRenderBridge",
                "operation": role,
                "related_record_ids": (record_id,),
                "exception_type": exception_type,
                "exception_message": exception_message,
                "stack_trace": stack_trace,
                "remediation_hint": "SVG/spec artifacts are available; rerun PNG rasterization.",
            },
        )

    def refresh(
        self,
        session: SessionRecord,
        request: RenderRefreshRequest,
    ) -> RenderRefreshResult:
        """Refresh requested drawing targets and return an updated session."""

        state = refresh_request_targets(self, session, request)
        current = state.session
        if state.updated_paths or state.warnings:
            current = replace(current, updated_at=utc_now_iso())
        status = state.status
        message = _message(status, len(state.updated_paths), len(state.warnings))
        return RenderRefreshResult(
            status=status,
            session=current,
            message=message,
            updated_artifact_paths=tuple(state.updated_paths),
            warnings=tuple(state.warnings),
        )

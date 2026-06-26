"""Dispatch modeless Advanced Diagnostics actions."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.app.diagnostics_action_core import (
    copy_command_trace,
    export_bundle,
    open_session_folder,
    validate_modes,
    validate_session,
)
from metrology_process_planner.app.diagnostics_action_results import DiagnosticsActionResult
from metrology_process_planner.app.diagnostics_artifacts import (
    copy_repair_queue,
    export_artifact_health_report,
    scan_artifacts,
    validate_artifact_registry,
)
from metrology_process_planner.diagnostics import (
    DiagnosticEvent,
    DiagnosticSink,
    DiagnosticsService,
)
from metrology_process_planner.diagnostics.diagnostics_exceptions import emit_exception_event
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths


@dataclass(frozen=True)
class DiagnosticsActionContext:
    """Runtime context used to handle diagnostics actions."""

    session: SessionRecord
    paths: SessionPaths | None
    events: tuple[DiagnosticEvent, ...]
    mode_registry: ModeRegistry
    service: DiagnosticsService


class DiagnosticsActionDispatcher:
    """Handle diagnostics actions without coupling widgets to services."""

    def __init__(self, sink: DiagnosticSink) -> None:
        self._sink = sink

    def dispatch(
        self,
        action_id: str,
        context: DiagnosticsActionContext,
    ) -> DiagnosticsActionResult:
        """Route one action and convert failures into diagnostics results."""

        try:
            result = self._dispatch(action_id, context)
        except Exception as exc:  # noqa: BLE001 - diagnostics must not drop action failures.
            emit_exception_event(
                self._sink,
                "DiagnosticsActionFailed",
                exc,
                "Advanced diagnostics action failed.",
                session_id=context.session.id,
                source_component="advanced_diagnostics",
                operation=action_id,
                remediation_hint="Review diagnostics action inputs and retry.",
            )
            result = DiagnosticsActionResult(
                action_id,
                "error",
                "Advanced diagnostics action failed.",
                next_ui_hint="Open diagnostics and review the captured exception event.",
            )
        self._emit_action_event(context.session.id, result)
        return result

    def _dispatch(
        self,
        action_id: str,
        context: DiagnosticsActionContext,
    ) -> DiagnosticsActionResult:
        if action_id == "CopyCommandTrace":
            return copy_command_trace(action_id, context.events)
        if action_id == "OpenSessionFolder":
            return open_session_folder(action_id, context.paths)
        if action_id == "ScanArtifacts":
            return scan_artifacts(action_id, context)
        if action_id == "CopyRepairQueue":
            return copy_repair_queue(action_id, context)
        if action_id == "ValidateArtifactRegistry":
            return validate_artifact_registry(action_id, context)
        if action_id.startswith("ExportArtifactHealthReport"):
            return export_artifact_health_report(action_id, context)
        if action_id == "ValidateSession":
            return validate_session(action_id, context)
        if action_id == "ValidateModes":
            return validate_modes(action_id, context)
        if action_id.startswith("ExportDiagnosticsBundle"):
            return export_bundle(action_id, context)
        return DiagnosticsActionResult(action_id, "unavailable", "Unknown diagnostics action.")

    def _emit_action_event(self, session_id: str, result: DiagnosticsActionResult) -> None:
        self._sink.emit(
            DiagnosticEvent(
                result.message,
                severity="warning" if result.status in {"blocked", "error"} else "info",
                source="advanced_diagnostics",
                event_name="DiagnosticsActionRouted",
                category="diagnostics",
                operation=result.action_id,
                session_id=session_id,
                actual={"status": result.status, "output_path": result.output_path},
            )
        )


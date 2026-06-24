"""Dispatch modeless Advanced Diagnostics actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from metrology_process_planner.app import diagnostics_summary as diag_summary
from metrology_process_planner.app.diagnostics_action_results import DiagnosticsActionResult
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.infrastructure.diagnostics import (
    DiagnosticEvent,
    DiagnosticSink,
    DiagnosticsService,
)
from metrology_process_planner.infrastructure.diagnostics_exceptions import emit_exception_event
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
            return _copy_command_trace(action_id, context.events)
        if action_id == "OpenSessionFolder":
            return _open_session_folder(action_id, context.paths)
        if action_id == "ScanArtifacts":
            return _scan_artifacts(action_id, context)
        if action_id == "ValidateSession":
            return _validate_session(action_id, context)
        if action_id == "ValidateModes":
            return _validate_modes(action_id, context)
        if action_id.startswith("ExportDiagnosticsBundle"):
            return _export_bundle(action_id, context)
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


def _copy_command_trace(
    action_id: str,
    events: tuple[DiagnosticEvent, ...],
) -> DiagnosticsActionResult:
    if not events:
        return DiagnosticsActionResult(
            action_id,
            "unavailable",
            "No command or diagnostic events are available yet.",
        )
    lines = tuple(_event_trace_line(event) for event in events[-50:])
    return DiagnosticsActionResult(
        action_id,
        "success",
        f"Prepared {len(lines)} diagnostic trace lines.",
        output_text="\n".join(lines),
    )


def _open_session_folder(action_id: str, paths: SessionPaths | None) -> DiagnosticsActionResult:
    if paths is None:
        return DiagnosticsActionResult(
            action_id,
            "unavailable",
            "No session folder is associated with diagnostics.",
        )
    return DiagnosticsActionResult(
        action_id,
        "success",
        "Session folder path resolved.",
        output_path=str(paths.folder),
    )


def _scan_artifacts(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    if context.paths is None:
        return DiagnosticsActionResult(
            action_id,
            "unavailable",
            "No session folder is available for artifact scanning.",
        )
    total = len(context.session.artifacts or {})
    missing = diag_summary.missing_artifact_count(context.session)
    text = f"session_folder={context.paths.folder}\nartifacts={total}\nmissing={missing}"
    message = f"Scanned {total} artifact records; {missing} missing."
    return DiagnosticsActionResult(action_id, "success", message, text)


def _validate_session(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    warnings = context.session.validation_warnings()
    status = "warning" if warnings or context.session.warnings else "success"
    message = _validation_message(warnings, len(context.session.warnings))
    return DiagnosticsActionResult(action_id, status, message, output_text="\n".join(warnings))


def _validate_modes(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    warnings = context.mode_registry.validation_warnings()
    summary = diag_summary.mode_validation_summary(context.session)
    status = "warning" if warnings or summary != "ok" else "success"
    text = "\n".join((f"session_mode={summary}", *warnings))
    return DiagnosticsActionResult(action_id, status, f"Mode validation: {summary}.", text)


def _export_bundle(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    destination = _export_destination(action_id, context.paths)
    if destination is None:
        return DiagnosticsActionResult(
            action_id,
            "unavailable",
            "Diagnostics bundle export needs a destination path.",
        )
    bundle = context.service.export_debug_bundle(context.session, destination, context.paths)
    return DiagnosticsActionResult(
        "ExportDiagnosticsBundle",
        "success",
        "Diagnostics bundle exported.",
        output_path=str(bundle),
    )


def _event_trace_line(event: DiagnosticEvent) -> str:
    return " | ".join(
        item
        for item in (
            event.timestamp,
            event.severity,
            event.category,
            event.operation or event.event_name,
            event.message,
        )
        if item
    )


def _validation_message(warnings: tuple[str, ...], warning_records: int) -> str:
    if warnings:
        return f"Session validation found {len(warnings)} structural warning(s)."
    if warning_records:
        return f"Session has {warning_records} persisted warning record(s)."
    return "Session validation passed."


def _export_destination(action_id: str, paths: SessionPaths | None) -> Path | None:
    if ":" in action_id:
        return Path(action_id.split(":", 1)[1]).expanduser().resolve()
    if paths is None:
        return None
    return paths.folder / "diagnostics_bundle"

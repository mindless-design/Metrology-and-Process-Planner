"""Core Advanced Diagnostics action helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from metrology_process_planner.app import diagnostics_summary as diag_summary
from metrology_process_planner.app.diagnostics_action_results import DiagnosticsActionResult
from metrology_process_planner.diagnostics import DiagnosticEvent
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)
from metrology_process_planner.persistence.paths import SessionPaths

if TYPE_CHECKING:
    from metrology_process_planner.app.diagnostics_action_dispatch import DiagnosticsActionContext


def copy_command_trace(
    action_id: str,
    events: tuple[DiagnosticEvent, ...],
) -> DiagnosticsActionResult:
    """Prepare recent diagnostic events as text."""

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


def open_session_folder(action_id: str, paths: SessionPaths | None) -> DiagnosticsActionResult:
    """Resolve the active session folder for diagnostics."""

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


def validate_session(action_id: str, context: DiagnosticsActionContext) -> DiagnosticsActionResult:
    """Validate the active session record."""

    warnings = context.session.validation_warnings()
    visible_warning_count = _visible_warning_count(context)
    status = "warning" if warnings or visible_warning_count else "success"
    message = _validation_message(warnings, visible_warning_count)
    return DiagnosticsActionResult(action_id, status, message, output_text="\n".join(warnings))


def validate_modes(action_id: str, context: DiagnosticsActionContext) -> DiagnosticsActionResult:
    """Validate mode compatibility for the active session."""

    warnings = context.mode_registry.validation_warnings()
    summary = diag_summary.mode_validation_summary(context.session)
    status = "warning" if warnings or summary != "ok" else "success"
    text = "\n".join((f"session_mode={summary}", *warnings))
    return DiagnosticsActionResult(action_id, status, f"Mode validation: {summary}.", text)


def export_bundle(action_id: str, context: DiagnosticsActionContext) -> DiagnosticsActionResult:
    """Export a diagnostics bundle."""

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


def _visible_warning_count(context: DiagnosticsActionContext) -> int:
    return sum(
        1
        for warning in context.session.warnings
        if warning_visible_for_session(context.session, warning, context.mode_registry)
    )


def _export_destination(action_id: str, paths: SessionPaths | None) -> Path | None:
    if ":" in action_id:
        return Path(action_id.split(":", 1)[1]).expanduser().resolve()
    if paths is None:
        return None
    return paths.folder / "diagnostics_bundle"

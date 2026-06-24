"""UI command router sitting between widgets and application services."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.app.commands import CommandBlockedError, CommandId, CommandRegistry
from metrology_process_planner.infrastructure.diagnostics_exceptions import exception_payload
from metrology_process_planner.infrastructure.diagnostics_models import DiagnosticEvent
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink


@dataclass(frozen=True)
class CommandRouteResult:
    """Result of routing one UI command intent."""

    command_id: CommandId
    status: str
    message: str = ""
    updated_document_id: str = ""
    selected_item_id: str = ""
    warning_ids: tuple[str, ...] = ()
    next_ui_hint: str = ""


class CommandRouter:
    """Route UI command intents through application-owned handlers."""

    def __init__(
        self,
        registry: CommandRegistry,
        diagnostic_sink: DiagnosticSink | None = None,
    ) -> None:
        self._registry = registry
        self._diagnostics = diagnostic_sink

    def route(self, command_id: CommandId) -> CommandRouteResult:
        """Dispatch one command and return a structured route result."""

        try:
            self._registry.dispatch(command_id)
        except NotImplementedError as exc:
            result = CommandRouteResult(
                command_id,
                "unavailable",
                str(exc),
                next_ui_hint="This command is known but not wired to a workflow yet.",
            )
            self._emit(result, exc)
            return result
        except CommandBlockedError as exc:
            result = CommandRouteResult(
                command_id,
                "blocked",
                str(exc),
                next_ui_hint=exc.next_ui_hint,
            )
            self._emit(result, exc)
            return result
        except RuntimeError as exc:
            result = CommandRouteResult(
                command_id,
                "error",
                str(exc),
                next_ui_hint="Open diagnostics and review the command handler.",
            )
            self._emit(result, exc)
            return result
        except Exception as exc:  # noqa: BLE001 - UI command boundaries must report failures.
            result = CommandRouteResult(
                command_id,
                "error",
                str(exc),
                next_ui_hint="Open diagnostics and review the command handler.",
            )
            self._emit(result, exc)
            return result
        result = CommandRouteResult(command_id, "success", next_ui_hint="Command completed.")
        self._emit(result, None)
        return result

    def _emit(self, result: CommandRouteResult, exc: BaseException | None) -> None:
        if self._diagnostics is None:
            return
        payload = _command_payload(result, exc)
        self._diagnostics.emit(
            DiagnosticEvent(
                message=str(payload["message"]),
                severity=str(payload["severity"]),
                source="CommandRouter",
                event_name="CommandRouted",
                category="command",
                operation=result.command_id.value,
                actual={"status": result.status, "message": result.message},
                exception_type=str(payload.get("exception_type", "")),
                exception_message=str(payload.get("exception_message", "")),
                stack_trace=str(payload.get("stack_trace", "")),
                remediation_hint=str(payload.get("remediation_hint", "")),
            )
        )


def _command_payload(
    result: CommandRouteResult,
    exc: BaseException | None,
) -> dict[str, object]:
    message = f"Command routed: {result.command_id.value} -> {result.status}"
    if exc is None:
        return {"message": message, "severity": "info"}
    severity = "warning" if result.status in {"blocked", "unavailable"} else "error"
    return exception_payload(
        exc,
        message,
        severity=severity,
        category="command",
        source_component="CommandRouter",
        operation=result.command_id.value,
        remediation_hint="Open diagnostics and review the command handler failure.",
    )

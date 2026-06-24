"""Public command API for app and adapter layers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from metrology_process_planner.app.command_catalog import ALL_COMMANDS, MENU_COMMANDS
from metrology_process_planner.app.command_types import (
    CommandBlockedError,
    CommandGroup,
    CommandHandler,
    CommandId,
    CommandSpec,
    CoverageLane,
)


class CommandRegistry:
    """Command registry used by UI widgets and KLayout menu adapters."""

    def __init__(self, specs: Iterable[CommandSpec] = ALL_COMMANDS) -> None:
        self._specs: dict[CommandId, CommandSpec] = {spec.command_id: spec for spec in specs}
        self._handlers: dict[CommandId, CommandHandler] = {}

    @property
    def specs(self) -> Mapping[CommandId, CommandSpec]:
        """Return immutable command metadata for all routable intents."""

        return dict(self._specs)

    def register(self, command_id: CommandId, handler: CommandHandler) -> None:
        """Attach a callable handler to a known command."""

        if command_id not in self._specs:
            raise KeyError(f"Unknown command id: {command_id}")
        self._handlers[command_id] = handler

    def dispatch(self, command_id: CommandId) -> None:
        """Run the handler registered for a command."""

        try:
            handler = self._handlers[command_id]
        except KeyError as exc:
            raise RuntimeError(f"No handler registered for command: {command_id.value}") from exc
        handler()


def build_default_registry() -> CommandRegistry:
    """Build a registry with unavailable handlers for every command intent."""

    registry = CommandRegistry()
    for command_id in CommandId:
        registry.register(command_id, _missing_ui_handler(command_id))
    return registry


def command_id_from_view_action(action_id: str) -> CommandId:
    """Normalize view-model action IDs into typed command IDs."""

    command_name = action_id.split(":", 1)[0]
    normalized = []
    for index, char in enumerate(command_name):
        if char.isupper() and index:
            normalized.append("_")
        normalized.append(char.lower())
    return CommandId("".join(normalized))


def _missing_ui_handler(command_id: CommandId) -> CommandHandler:
    def handler() -> None:
        raise NotImplementedError(
            f"{command_id.value} is registered, but its UI controller is not implemented yet."
        )

    return handler


__all__ = [
    "ALL_COMMANDS",
    "MENU_COMMANDS",
    "CommandGroup",
    "CommandHandler",
    "CommandBlockedError",
    "CommandId",
    "CommandRegistry",
    "CommandSpec",
    "CoverageLane",
    "build_default_registry",
    "command_id_from_view_action",
]

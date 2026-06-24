"""Command routing for app and adapter layers."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum


class CommandId(str, Enum):
    """Stable identifiers for user-facing plugin commands."""

    START_OR_RESUME_SETUP = "start_or_resume_setup"
    OPEN_SESSION_EDITOR = "open_session_editor"
    END_ACTIVE_SESSION = "end_active_session"
    EDIT_RECIPE = "edit_recipe"
    OPEN_DIAGNOSTICS = "open_diagnostics"


class CommandGroup(str, Enum):
    """Top-level product area for command coverage tracking."""

    SESSION = "session"
    RECIPE = "recipe"
    DIAGNOSTICS = "diagnostics"


class CoverageLane(str, Enum):
    """Expected test lane for a command entrypoint."""

    UNIT = "unit"
    KLAYOUT_BATCH = "klayout_batch"
    KLAYOUT_UI = "klayout_ui"


CommandHandler = Callable[[], None]


@dataclass(frozen=True)
class CommandSpec:
    """Menu and help metadata for a command."""

    command_id: CommandId
    menu_item_name: str
    menu_path: str
    title: str
    description: str
    group: CommandGroup
    coverage_lane: CoverageLane


DEFAULT_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec(
        CommandId.START_OR_RESUME_SETUP,
        "mpp_start_or_resume_setup",
        "tools_menu.metrology_process_planner",
        "Start / Resume Measurement Setup",
        "Create or resume a guided setup and capture session.",
        CommandGroup.SESSION,
        CoverageLane.KLAYOUT_UI,
    ),
    CommandSpec(
        CommandId.OPEN_SESSION_EDITOR,
        "mpp_open_session_editor",
        "tools_menu.metrology_process_planner",
        "Session Editor",
        "Open the saved-session editor and repair surface.",
        CommandGroup.SESSION,
        CoverageLane.KLAYOUT_UI,
    ),
    CommandSpec(
        CommandId.EDIT_RECIPE,
        "mpp_edit_recipe",
        "tools_menu.metrology_process_planner",
        "Edit Recipe",
        "Open the process recipe editor.",
        CommandGroup.RECIPE,
        CoverageLane.KLAYOUT_UI,
    ),
    CommandSpec(
        CommandId.END_ACTIVE_SESSION,
        "mpp_end_active_session",
        "tools_menu.metrology_process_planner",
        "End Active Session",
        "Close the current workflow after saving or discarding pending state.",
        CommandGroup.SESSION,
        CoverageLane.KLAYOUT_UI,
    ),
    CommandSpec(
        CommandId.OPEN_DIAGNOSTICS,
        "mpp_open_diagnostics",
        "tools_menu.metrology_process_planner",
        "Advanced Diagnostics",
        "Open diagnostics for adapters, session artifacts, and exports.",
        CommandGroup.DIAGNOSTICS,
        CoverageLane.KLAYOUT_UI,
    ),
)


class CommandRegistry:
    """Small command registry used by UI and KLayout menu adapters."""

    def __init__(self, specs: Iterable[CommandSpec] = DEFAULT_COMMANDS) -> None:
        self._specs: dict[CommandId, CommandSpec] = {spec.command_id: spec for spec in specs}
        self._handlers: dict[CommandId, CommandHandler] = {}

    @property
    def specs(self) -> Mapping[CommandId, CommandSpec]:
        """Return immutable command metadata for menu registration."""

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
    """Build a registry with placeholder handlers for early integration."""

    registry = CommandRegistry()
    for command_id in CommandId:
        registry.register(command_id, _missing_ui_handler(command_id))
    return registry


def _missing_ui_handler(command_id: CommandId) -> CommandHandler:
    def handler() -> None:
        raise NotImplementedError(
            f"{command_id.value} is registered, but its UI controller is not implemented yet."
        )

    return handler

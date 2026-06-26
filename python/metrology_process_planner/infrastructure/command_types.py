"""Neutral command metadata records shared by app and tooling."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from metrology_process_planner.domains.commands import CommandId, command_id_from_view_action


class CommandGroup(str, Enum):
    """Top-level product area for command coverage tracking."""

    SESSION = "session"
    SETUP = "setup"
    CAPTURE = "capture"
    MEASUREMENT = "measurement"
    RECIPE = "recipe"
    PROCESS = "process"
    ARTIFACT = "artifact"
    DIAGNOSTICS = "diagnostics"


class CoverageLane(str, Enum):
    """Expected test lane for a command entrypoint."""

    UNIT = "unit"
    KLAYOUT_BATCH = "klayout_batch"
    KLAYOUT_UI = "klayout_ui"


CommandHandler = Callable[[], object]


class CommandBlockedError(RuntimeError):
    """Raised when a known command is temporarily blocked by workflow state."""

    def __init__(self, message: str, next_ui_hint: str = "") -> None:
        super().__init__(message)
        self.next_ui_hint = next_ui_hint


@dataclass(frozen=True)
class CommandSpec:
    """Metadata for a command intent and optional KLayout menu entry."""

    command_id: CommandId
    title: str
    description: str
    group: CommandGroup
    coverage_lane: CoverageLane = CoverageLane.UNIT
    menu_item_name: str = ""
    menu_path: str = ""

    @property
    def appears_in_menu(self) -> bool:
        """Return whether this command should be installed in KLayout menus."""

        return bool(self.menu_item_name and self.menu_path)


__all__ = [
    "CommandBlockedError",
    "CommandGroup",
    "CommandHandler",
    "CommandId",
    "CommandSpec",
    "CoverageLane",
    "command_id_from_view_action",
]

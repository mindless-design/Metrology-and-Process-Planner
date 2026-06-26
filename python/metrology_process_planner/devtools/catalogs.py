"""Data catalogs for developer inspector tools."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.app.command_catalog import ALL_COMMANDS
from metrology_process_planner.app.command_types import CommandSpec
from metrology_process_planner.domains.modes.mode_registry import built_in_mode_registry
from metrology_process_planner.rendering import built_in_render_profiles


@dataclass(frozen=True)
class DeveloperCatalog:
    """Serializable backing data for developer explorer windows."""

    modes: tuple[dict[str, object], ...]
    commands: tuple[dict[str, object], ...]
    render_profiles: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        """Serialize catalog data for debug UIs."""

        return {
            "modes": list(self.modes),
            "commands": list(self.commands),
            "render_profiles": list(self.render_profiles),
        }


def build_developer_catalog() -> DeveloperCatalog:
    """Build catalogs for session, mode, command, and render explorers."""

    registry = built_in_mode_registry()
    return DeveloperCatalog(
        modes=tuple(_mode_row(mode) for mode in registry.definitions()),
        commands=tuple(_command_row(command) for command in ALL_COMMANDS),
        render_profiles=tuple(
            _render_profile_row(profile_id, profile)
            for profile_id, profile in built_in_render_profiles().items()
        ),
    )


def _mode_row(mode: object) -> dict[str, object]:
    return {
        "mode_id": getattr(mode, "mode_id", ""),
        "display_name": getattr(mode, "display_name", ""),
        "family": getattr(mode, "family", ""),
        "visible": getattr(mode, "visible", False),
    }


def _command_row(command: CommandSpec) -> dict[str, object]:
    return {
        "command_id": command.command_id.value,
        "title": command.title,
        "group": command.group.value,
        "coverage_lane": command.coverage_lane.value,
        "menu_path": command.menu_path,
        "menu_item_name": command.menu_item_name,
    }


def _render_profile_row(profile_id: str, profile: object) -> dict[str, object]:
    return {
        "profile_id": profile_id,
        "display_name": getattr(profile, "display_name", ""),
        "render_mode_id": getattr(profile, "render_mode_id", ""),
        "feature_filter_policy": getattr(profile, "feature_filter_policy", ""),
        "export_formats": list(getattr(profile, "export_formats", ())),
    }

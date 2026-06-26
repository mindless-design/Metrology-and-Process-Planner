"""Shared UI state-machine value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UiStateSnapshot:
    """Renderable state-machine output for editor, diagnostics, and status strips."""

    machine: str
    state: str
    message: str
    active_item_ref: str = ""
    action_ids: tuple[str, ...] = ()
    warning_ids: tuple[str, ...] = ()

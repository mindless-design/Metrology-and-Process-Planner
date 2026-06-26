"""Operator layout binding contracts for session document commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from metrology_process_planner.domains.session import SourceLayoutContext


@dataclass(frozen=True)
class LayoutBindingSelection:
    """Result from a host adapter that inspects the current layout view."""

    source_layout: SourceLayoutContext | None = None
    status: str = "cancelled"
    message: str = "Layout binding cancelled."

    @classmethod
    def selected(cls, source_layout: SourceLayoutContext) -> LayoutBindingSelection:
        """Return a successful current-layout selection."""

        return cls(source_layout, "selected", "Current layout selected.")


class SessionLayoutAdapter(Protocol):
    """Boundary implemented by KLayout hosts for current-layout metadata."""

    def select_current_layout(self) -> LayoutBindingSelection:
        """Return metadata for the currently active layout/view."""


class UnavailableSessionLayoutAdapter:
    """Default adapter for hosts that have not supplied live layout access."""

    def select_current_layout(self) -> LayoutBindingSelection:
        """Report that current-layout binding is not connected."""

        return LayoutBindingSelection(
            status="unavailable",
            message="Bind Current Layout requires a live KLayout layout adapter.",
        )

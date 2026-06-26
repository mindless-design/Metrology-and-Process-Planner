"""Operator path selection contracts for session document commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from metrology_process_planner.domains.session import (
    SessionMode,
    SessionModeId,
    SourceLayoutContext,
)
from metrology_process_planner.workflows.editor import NewSessionRequest


@dataclass(frozen=True)
class PathSelection:
    """Result from an operator path picker."""

    path: Path | None = None
    status: str = "cancelled"
    message: str = "No path selected."

    @classmethod
    def selected(cls, path: str | Path) -> PathSelection:
        """Return a successful path selection."""

        return cls(Path(path), "selected", "Path selected.")


@dataclass(frozen=True)
class NewSessionSelection:
    """Result from an operator new-session picker."""

    output_folder: Path | None = None
    label: str = "Untitled session"
    mode: SessionMode | SessionModeId = SessionMode.SIMPLE_CAPTURE
    source_layout: SourceLayoutContext = field(default_factory=SourceLayoutContext)
    status: str = "cancelled"
    message: str = "New session cancelled."

    @classmethod
    def selected(
        cls,
        output_folder: str | Path,
        label: str = "Untitled session",
        mode: SessionMode | SessionModeId = SessionMode.SIMPLE_CAPTURE,
        source_layout: SourceLayoutContext | None = None,
    ) -> NewSessionSelection:
        """Return a successful new-session selection."""

        layout = source_layout if source_layout is not None else SourceLayoutContext()
        return cls(Path(output_folder), label, mode, layout, "selected", "Session selected.")

    def to_request(self) -> NewSessionRequest:
        """Convert the selection into a durable new-session request."""

        if self.output_folder is None:
            raise ValueError("New session selection has no output folder.")
        return NewSessionRequest(
            self.output_folder,
            self.label,
            self.mode,
            self.source_layout,
        )


class SessionPathAdapter(Protocol):
    """Boundary implemented by UI/KLayout shells for session paths."""

    def select_new_session(self) -> NewSessionSelection:
        """Return operator inputs for a new session."""

    def select_open_session(self) -> PathSelection:
        """Return an existing session JSON file or session folder."""

    def select_recent_session(self, recent_paths: tuple[Path, ...]) -> PathSelection:
        """Return one of the known recent session paths."""

    def select_save_as_destination(self) -> PathSelection:
        """Return a destination session JSON file or folder."""


class UnavailableSessionPathAdapter:
    """Default adapter for hosts that have not supplied picker UI yet."""

    def select_new_session(self) -> NewSessionSelection:
        """Report that new-session picker UI is not connected."""

        return NewSessionSelection(message="New Session requires a path and mode picker.")

    def select_open_session(self) -> PathSelection:
        """Report that open-session picker UI is not connected."""

        return PathSelection(message="Open Session requires a session path picker.")

    def select_recent_session(self, recent_paths: tuple[Path, ...]) -> PathSelection:
        """Report that recent-session picker UI is not connected."""

        if not recent_paths:
            return PathSelection(status="unavailable", message="No recent sessions are known.")
        return PathSelection(message="Open Recent requires a recent-session picker.")

    def select_save_as_destination(self) -> PathSelection:
        """Report that save-as picker UI is not connected."""

        return PathSelection(message="Save Session As requires a destination picker.")

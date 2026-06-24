"""Result and context models for canvas interaction workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CanvasObjectType, SessionRecord


@dataclass(frozen=True)
class InteractionContext:
    """Ephemeral interaction state that should not be written to session JSON."""

    armed_object_type: Optional[CanvasObjectType] = None
    active_parent_id: Optional[str] = None
    live_preview_id: Optional[str] = None
    drag_start: Optional[Point] = None


@dataclass(frozen=True)
class InteractionResult:
    """Result from one pure canvas interaction transition."""

    session: SessionRecord
    context: InteractionContext
    handled: bool = True
    messages: tuple[str, ...] = ()
    artifact_requests: tuple[str, ...] = ()
    artifact_paths_to_remove: tuple[str, ...] = ()

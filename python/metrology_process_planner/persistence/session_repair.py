"""Previewable raw session JSON repair actions."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from metrology_process_planner.domains.session import SESSION_SCHEMA_VERSION


@dataclass(frozen=True)
class RepairAction:
    """One previewable session repair operation."""

    action_id: str
    location: str
    message: str
    replacement: object

    def to_dict(self) -> dict[str, object]:
        """Serialize the repair action."""

        return {
            "action_id": self.action_id,
            "location": self.location,
            "message": self.message,
            "replacement": self.replacement,
        }


@dataclass(frozen=True)
class RepairPreview:
    """A dry-run session repair result."""

    actions: tuple[RepairAction, ...]

    @property
    def has_repairs(self) -> bool:
        """Return whether at least one repair action is available."""

        return bool(self.actions)

    def to_dict(self) -> dict[str, object]:
        """Serialize the preview."""

        return {"actions": [action.to_dict() for action in self.actions]}


def preview_session_repairs(data: dict[str, Any]) -> RepairPreview:
    """Return repair actions for missing ids, duplicates, and obsolete schema."""

    actions: list[RepairAction] = []
    if "schema" not in data:
        actions.append(_action("schema.upgrade", "schema", "Upgrade legacy schema.", _schema()))
    _append_missing_top_id(actions, data)
    _append_capture_id_repairs(actions, data)
    return RepairPreview(tuple(actions))


def apply_session_repairs(
    data: dict[str, Any],
    preview: RepairPreview | None = None,
) -> dict[str, Any]:
    """Apply a repair preview to a copy of the raw session data."""

    repaired = deepcopy(data)
    preview = preview or preview_session_repairs(repaired)
    for action in preview.actions:
        if action.location == "schema":
            repaired["schema"] = action.replacement
        elif action.location == "id":
            repaired["id"] = action.replacement
        elif action.location.startswith("captures["):
            index = int(action.location.split("[", 1)[1].split("]", 1)[0])
            repaired.setdefault("captures", [])[index]["id"] = action.replacement
    return repaired


def _append_missing_top_id(actions: list[RepairAction], data: dict[str, Any]) -> None:
    if data.get("id"):
        return
    actions.append(_action("session.id", "id", "Add missing session id.", "session-repaired"))


def _append_capture_id_repairs(actions: list[RepairAction], data: dict[str, Any]) -> None:
    captures = data.get("captures", [])
    if not isinstance(captures, list):
        return
    seen: set[str] = set()
    for index, capture in enumerate(captures):
        if not isinstance(capture, dict):
            continue
        capture_id = str(capture.get("id", ""))
        if capture_id and capture_id not in seen:
            seen.add(capture_id)
            continue
        replacement = f"cap-repaired-{index + 1:03d}"
        actions.append(
            _action(
                "capture.id",
                f"captures[{index}].id",
                "Repair missing or duplicate capture id.",
                replacement,
            )
        )
        seen.add(replacement)


def _schema() -> dict[str, object]:
    return {
        "name": "metrology_process_planner.session",
        "version": SESSION_SCHEMA_VERSION,
    }


def _action(action_id: str, location: str, message: str, replacement: object) -> RepairAction:
    return RepairAction(action_id, location, message, replacement)

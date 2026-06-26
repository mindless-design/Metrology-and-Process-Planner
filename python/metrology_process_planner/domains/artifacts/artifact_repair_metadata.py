"""Artifact repair metadata records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.session.record_values import optional_str


@dataclass(frozen=True)
class ArtifactRepairMetadata:
    """Repair metadata surfaced by editor and diagnostics workflows."""

    repair_action: str = ""
    repair_suggestion: str = ""
    last_attempt_at: Optional[str] = None
    last_error: str = ""
    regenerable: bool = False
    requires_live_layout: bool = False
    requires_parent_image: bool = False
    requires_recipe: bool = False
    requires_solver: bool = False
    placeholder_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize repair metadata."""

        return {
            "repair_action": self.repair_action,
            "repair_suggestion": self.repair_suggestion,
            "last_attempt_at": self.last_attempt_at,
            "last_error": self.last_error,
            "regenerable": self.regenerable,
            "requires_live_layout": self.requires_live_layout,
            "requires_parent_image": self.requires_parent_image,
            "requires_recipe": self.requires_recipe,
            "requires_solver": self.requires_solver,
            "placeholder_reason": self.placeholder_reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactRepairMetadata:
        """Build repair metadata from JSON-compatible data."""

        return cls(
            repair_action=str(data.get("repair_action", "")),
            repair_suggestion=str(data.get("repair_suggestion", "")),
            last_attempt_at=optional_str(data.get("last_attempt_at")),
            last_error=str(data.get("last_error", "")),
            regenerable=bool(data.get("regenerable", False)),
            requires_live_layout=bool(data.get("requires_live_layout", False)),
            requires_parent_image=bool(data.get("requires_parent_image", False)),
            requires_recipe=bool(data.get("requires_recipe", False)),
            requires_solver=bool(data.get("requires_solver", False)),
            placeholder_reason=str(data.get("placeholder_reason", "")),
        )

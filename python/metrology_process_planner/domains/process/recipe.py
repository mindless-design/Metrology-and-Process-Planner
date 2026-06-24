"""Process recipe aggregate and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.process.materials import Material
from metrology_process_planner.domains.process.steps import ProcessStep, ProcessWindow
from metrology_process_planner.domains.process.validation import validate_recipe


@dataclass(frozen=True)
class ProcessRecipe:
    """Ordered process recipe used by solver and rendering workflows."""

    id: str
    name: str
    materials: tuple[Material, ...]
    steps: tuple[ProcessStep, ...]
    process_windows: tuple[ProcessWindow, ...] = ()
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    def validate(self) -> tuple[str, ...]:
        """Return warnings for missing references and invalid step settings."""

        return validate_recipe(self.materials, self.steps, self.process_windows)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the recipe to JSON-compatible data."""

        return {
            "id": self.id,
            "name": self.name,
            "materials": [material.to_dict() for material in self.materials],
            "steps": [step.to_dict() for step in self.steps],
            "process_windows": [window.to_dict() for window in self.process_windows],
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessRecipe:
        """Build a process recipe from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            materials=tuple(Material.from_dict(item) for item in data.get("materials", ())),
            steps=tuple(ProcessStep.from_dict(item) for item in data.get("steps", ())),
            process_windows=tuple(
                ProcessWindow.from_dict(item) for item in data.get("process_windows", ())
            ),
            metadata=dict(data.get("metadata", {})),
        )


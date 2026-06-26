"""Process recipe aggregate and validation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.process.materials import Material
from metrology_process_planner.domains.process.step_specs import ProcessWindow
from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.domains.process.validation import validate_recipe
from metrology_process_planner.domains.process.validation_messages import RecipeValidationMessage
from metrology_process_planner.domains.process.validation_service import RecipeValidationService

RECIPE_SCHEMA_VERSION = "process_recipe.v1"


@dataclass(frozen=True)
class ProcessRecipe:
    """Ordered process recipe used by solver and rendering workflows."""

    id: str
    name: str
    materials: tuple[Material, ...]
    steps: tuple[ProcessStep, ...]
    process_windows: tuple[ProcessWindow, ...] = ()
    version: str = ""
    schema_version: str = RECIPE_SCHEMA_VERSION
    metadata: Optional[Mapping[str, Any]] = None
    extensions: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.extensions is None:
            object.__setattr__(self, "extensions", {})

    def validate(self) -> tuple[str, ...]:
        """Return warnings for missing references and invalid step settings."""

        return validate_recipe(self.materials, self.steps, self.process_windows)

    def validation_messages(self) -> tuple[RecipeValidationMessage, ...]:
        """Return structured validation messages for editor and solver consumers."""

        return RecipeValidationService().validate(self)

    def fingerprint(self) -> str:
        """Return a stable sha256 fingerprint for the canonical recipe payload."""

        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def minimal_summary(self) -> dict[str, Any]:
        """Return a small process-context snapshot for session JSON."""

        return {
            "recipe_id": self.id,
            "name": self.name,
            "version": self.version,
            "materials": [
                {"id": material.id, "name": material.name, "color": material.color}
                for material in self.materials
            ],
            "step_count": len(self.steps),
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the recipe to JSON-compatible data."""

        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "schema_version": self.schema_version,
            "materials": [material.to_dict() for material in self.materials],
            "steps": [step.to_dict() for step in self.steps],
            "process_windows": [window.to_dict() for window in self.process_windows],
            "metadata": dict(self.metadata or {}),
            "extensions": dict(self.extensions or {}),
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
            version=str(data.get("version", "")),
            schema_version=str(data.get("schema_version", RECIPE_SCHEMA_VERSION)),
            metadata=dict(data.get("metadata", {})),
            extensions=dict(data.get("extensions", {})),
        )

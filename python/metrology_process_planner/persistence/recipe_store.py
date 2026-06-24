"""JSON persistence for process recipe documents."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Union

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.infrastructure.diagnostics_exceptions import emit_exception_event
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink

JsonPath = Union[str, Path]


class ProcessRecipeJsonStore:
    """Read and write human-readable process recipe JSON."""

    def __init__(self, diagnostic_sink: DiagnosticSink | None = None) -> None:
        self._diagnostics = diagnostic_sink

    def load(self, path: JsonPath) -> ProcessRecipe:
        """Load a process recipe from JSON."""

        recipe_path = Path(path)
        try:
            with recipe_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, Mapping):
                raise ValueError(f"Recipe JSON must contain an object: {recipe_path}")
            return ProcessRecipe.from_dict(data)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            emit_exception_event(
                self._diagnostics,
                "RecipeJsonReadFailed",
                exc,
                f"Recipe JSON load failed: {recipe_path}",
                source_component="ProcessRecipeJsonStore",
                category="persistence",
                operation="load",
                related_artifact_paths=(str(recipe_path),),
                remediation_hint="Repair or choose another recipe JSON file.",
            )
            raise

    def save(self, recipe: ProcessRecipe, path: JsonPath) -> Path:
        """Atomically save a process recipe JSON file."""

        destination = Path(path)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp_path = destination.with_suffix(destination.suffix + ".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(recipe.to_dict(), handle, indent=2)
                handle.write("\n")
            if destination.exists():
                shutil.copy2(destination, destination.with_suffix(destination.suffix + ".bak"))
            temp_path.replace(destination)
        except OSError as exc:
            emit_exception_event(
                self._diagnostics,
                "RecipeJsonWriteFailed",
                exc,
                f"Recipe JSON save failed: {destination}",
                source_component="ProcessRecipeJsonStore",
                category="persistence",
                operation="save",
                related_artifact_paths=(str(destination),),
                remediation_hint="Check recipe folder permissions and free disk space.",
            )
            raise
        return destination

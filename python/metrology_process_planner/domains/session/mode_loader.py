"""Data-only loading for external session mode definitions."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from metrology_process_planner.domains.session.mode_registry import (
    ModeDefinition,
    ModeRegistry,
    built_in_mode_registry,
)


@dataclass(frozen=True)
class ModeRegistryLoadResult:
    """Result of loading mode definitions from JSON files."""

    registry: ModeRegistry
    warnings: tuple[str, ...] = ()


def load_mode_registry_from_folder(
    folder: Path,
    base_registry: Optional[ModeRegistry] = None,
) -> ModeRegistryLoadResult:
    """Load all JSON mode definitions from a folder without executing code."""

    if not folder.exists():
        return _result(base_registry, (), (f"Mode definition folder not found: {folder}",))
    return load_mode_registry_from_paths(sorted(folder.glob("*.json")), base_registry)


def load_mode_registry_from_paths(
    paths: Iterable[Path],
    base_registry: Optional[ModeRegistry] = None,
) -> ModeRegistryLoadResult:
    """Load JSON mode definitions from explicit paths without executing code."""

    warnings: list[str] = []
    definitions: list[ModeDefinition] = []
    for path in paths:
        loaded, file_warnings = _definitions_from_file(path)
        definitions.extend(loaded)
        warnings.extend(file_warnings)
    return _result(base_registry, definitions, tuple(warnings))


def _definitions_from_file(path: Path) -> tuple[tuple[ModeDefinition, ...], tuple[str, ...]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return (), (f"{path}: {exc}",)
    except json.JSONDecodeError as exc:
        return (), (f"{path}: Invalid JSON: {exc.msg}",)
    return _definitions_from_payload(path, payload)


def _definitions_from_payload(
    path: Path,
    payload: object,
) -> tuple[tuple[ModeDefinition, ...], tuple[str, ...]]:
    if isinstance(payload, Mapping):
        modes = payload.get("modes")
        if modes is None:
            return (ModeDefinition.from_mapping(payload),), ()
        if isinstance(modes, list):
            return _definitions_from_items(path, modes)
    if isinstance(payload, list):
        return _definitions_from_items(path, payload)
    return (), (f"{path}: Expected a mode object, a mode list, or an object with modes.",)


def _definitions_from_items(
    path: Path,
    items: Iterable[Any],
) -> tuple[tuple[ModeDefinition, ...], tuple[str, ...]]:
    definitions = []
    warnings = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, Mapping):
            definitions.append(ModeDefinition.from_mapping(item))
        else:
            warnings.append(f"{path}: Mode entry {index} is not an object.")
    return tuple(definitions), tuple(warnings)


def _result(
    base_registry: Optional[ModeRegistry],
    definitions: Iterable[ModeDefinition],
    warnings: tuple[str, ...],
) -> ModeRegistryLoadResult:
    base = base_registry if base_registry is not None else built_in_mode_registry()
    registry = ModeRegistry(base.definitions() + tuple(definitions))
    return ModeRegistryLoadResult(registry, warnings + registry.validation_warnings())

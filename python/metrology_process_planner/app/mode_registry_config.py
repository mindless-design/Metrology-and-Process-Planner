"""Application-level mode registry discovery."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from metrology_process_planner.domains.session import (
    ModeRegistry,
    ModeRegistryLoadResult,
    load_mode_registry_from_folder,
)

MODE_DEFINITION_DIRS_ENV = "MPP_MODE_DEFINITION_DIRS"


def configured_mode_folders(env: Mapping[str, str] | None = None) -> tuple[Path, ...]:
    """Return configured external mode folders from environment-like data."""

    values = env if env is not None else os.environ
    raw = values.get(MODE_DEFINITION_DIRS_ENV, "")
    if not raw.strip():
        return ()
    return tuple(Path(item) for item in raw.split(os.pathsep) if item.strip())


def load_configured_mode_registry(
    folders: tuple[Path, ...] | None = None,
    base_registry: ModeRegistry | None = None,
) -> ModeRegistryLoadResult:
    """Load configured external mode folders into one registry."""

    selected = folders if folders is not None else configured_mode_folders()
    registry = base_registry
    warnings: list[str] = []
    for folder in selected:
        result = load_mode_registry_from_folder(folder, registry)
        registry = result.registry
        warnings.extend(result.warnings)
    if registry is None:
        result = load_mode_registry_from_folder(Path("__mpp_no_external_modes__"), base_registry)
        return ModeRegistryLoadResult(result.registry, ())
    return ModeRegistryLoadResult(registry, tuple(warnings))

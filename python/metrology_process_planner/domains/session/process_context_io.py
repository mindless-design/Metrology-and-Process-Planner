"""JSON mapping helpers for the active process context block."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def process_context_to_dict(context: object) -> dict[str, Any]:
    """Serialize internal process context fields as canonical ``active`` JSON."""

    return {
        "active": {
            "recipe": _recipe_block(context),
            "solver": _solver_block(context),
            "render_profile": _render_profile_block(context),
            "process_window_variant": getattr(context, "process_window_variant", ""),
            "warning_ids": list(getattr(context, "warning_ids", ())),
        }
    }


def active_process_context_data(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return flat constructor data from canonical active process context JSON."""

    active = data.get("active")
    if not isinstance(active, Mapping):
        return {}
    return _active_context_data(active)


def legacy_process_context_data(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return flat constructor data from integer-schema process context JSON."""

    active = data.get("active")
    if isinstance(active, Mapping):
        return _active_context_data(active)
    return data


def _active_context_data(active: Mapping[str, Any]) -> Mapping[str, Any]:
    recipe = _mapping(active.get("recipe"))
    solver = _mapping(active.get("solver"))
    render_profile = active.get("render_profile")
    solver_options = dict(_mapping(solver.get("options")))
    if solver.get("status"):
        solver_options["status"] = str(solver.get("status", ""))
    return {
        "recipe_reference": str(recipe.get("reference", recipe.get("path", ""))),
        "recipe_id": str(recipe.get("recipe_id", recipe.get("id", ""))),
        "recipe_name": str(recipe.get("name", "")),
        "recipe_version": str(recipe.get("version", "")),
        "recipe_path": str(recipe.get("path", "")),
        "recipe_fingerprint": _fingerprint_value(recipe.get("fingerprint")),
        "recipe_snapshot_policy": str(recipe.get("snapshot_policy", "embed_minimal_summary")),
        "recipe_snapshot": dict(_mapping(recipe.get("snapshot"))),
        "solver_backend": str(solver.get("backend", "")),
        "solver_version": str(solver.get("backend_version", solver.get("version", ""))),
        "solver_options": solver_options,
        "render_profile": _render_profile_id(render_profile),
        "process_window_variant": str(active.get("process_window_variant", "")),
        "warning_ids": tuple(str(item) for item in active.get("warning_ids", ())),
    }


def _recipe_block(context: object) -> dict[str, Any] | None:
    recipe_id = getattr(context, "recipe_id", "")
    recipe_path = getattr(context, "recipe_path", "")
    recipe_name = getattr(context, "recipe_name", "")
    if not (recipe_id or recipe_path or recipe_name):
        return None
    fingerprint = getattr(context, "recipe_fingerprint", "")
    return {
        "recipe_id": recipe_id,
        "name": recipe_name,
        "version": getattr(context, "recipe_version", ""),
        "path": recipe_path,
        "fingerprint": {
            "method": "sha256",
            "value": fingerprint,
            "status": "computed" if fingerprint else "not_computed",
        },
        "snapshot_policy": getattr(context, "recipe_snapshot_policy", ""),
        "snapshot": dict(getattr(context, "recipe_snapshot", {}) or {}),
    }


def _solver_block(context: object) -> dict[str, Any]:
    options = dict(getattr(context, "solver_options", {}) or {})
    status = str(options.pop("status", "")) or _solver_status(context)
    return {
        "backend": getattr(context, "solver_backend", ""),
        "backend_version": getattr(context, "solver_version", ""),
        "status": status,
        "options": options,
    }


def _render_profile_block(context: object) -> dict[str, str] | None:
    render_profile = getattr(context, "render_profile", "")
    if not render_profile:
        return None
    return {
        "id": render_profile,
        "name": render_profile.replace("_", " ").title(),
        "material_display": "recipe_default",
    }


def _solver_status(context: object) -> str:
    return "available_or_unavailable" if getattr(context, "solver_backend", "") else (
        "unavailable_or_not_configured"
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _fingerprint_value(value: object) -> str:
    if isinstance(value, Mapping):
        return str(value.get("value", ""))
    return "" if value is None else str(value)


def _render_profile_id(value: object) -> str:
    if isinstance(value, Mapping):
        return str(value.get("id", ""))
    return "" if value is None else str(value)

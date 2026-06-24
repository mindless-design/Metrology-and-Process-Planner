"""Session schema validation helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.domains.session import SESSION_SCHEMA_VERSION

REQUIRED_SESSION_FIELDS = {
    "schema",
    "session",
    "paths",
    "source_layout",
    "coordinates",
    "setup",
    "captures",
    "grid_datasets",
    "process_context",
    "process_outputs",
    "reports",
    "artifacts",
    "warnings",
    "workflow",
    "extensions",
    "audit",
}
SUPPORTED_LEGACY_SESSION_SCHEMA_VERSIONS = frozenset(range(1, 5))


def validate_session_payload(data: Mapping[str, Any]) -> tuple[str, ...]:
    """Return schema validation warnings for a session JSON payload."""

    if "schema" not in data:
        return _legacy_warnings(data)
    return _v5_warnings(data)


def _v5_warnings(data: Mapping[str, Any]) -> tuple[str, ...]:
    warnings: list[str] = []
    missing_fields = sorted(REQUIRED_SESSION_FIELDS.difference(data))
    if missing_fields:
        warnings.append("Missing session fields: " + ", ".join(missing_fields))
    _append_schema_version_warning(warnings, data.get("schema", {}))
    _append_shape_warning(warnings, data, "captures", list, "Session captures must be a list.")
    _append_shape_warning(
        warnings,
        data,
        "artifacts",
        Mapping,
        "Session artifacts must be an object keyed by artifact id.",
    )
    return tuple(warnings)


def _append_schema_version_warning(warnings: list[str], schema: object) -> None:
    schema_version = schema.get("version") if isinstance(schema, Mapping) else None
    if schema_version != SESSION_SCHEMA_VERSION:
        warnings.append(
            f"Unsupported schema.version {schema_version}; expected {SESSION_SCHEMA_VERSION}."
        )


def _append_shape_warning(
    warnings: list[str],
    data: Mapping[str, Any],
    key: str,
    expected_type: type[Any] | tuple[type[Any], ...],
    message: str,
) -> None:
    if not isinstance(data.get(key), expected_type):
        warnings.append(message)


def _legacy_warnings(data: Mapping[str, Any]) -> tuple[str, ...]:
    required = {
        "schema_version",
        "id",
        "name",
        "mode",
        "created_at",
        "updated_at",
        "setup",
        "captures",
        "grid_datasets",
        "exports",
        "warnings",
        "metadata",
    }
    warnings: list[str] = []
    missing_fields = sorted(required.difference(data))
    if missing_fields:
        warnings.append("Missing session fields: " + ", ".join(missing_fields))
    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_LEGACY_SESSION_SCHEMA_VERSIONS:
        warnings.append(
            f"Unsupported schema_version {schema_version}; expected one of "
            f"{sorted(SUPPORTED_LEGACY_SESSION_SCHEMA_VERSIONS)}."
        )
    if not isinstance(data.get("captures", []), list):
        warnings.append("Session captures must be a list.")
    return tuple(warnings)

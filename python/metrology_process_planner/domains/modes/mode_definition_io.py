"""Mode definition JSON normalization helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from metrology_process_planner.domains.modes.mode_output_policies import (
    ArtifactPolicy,
    EditorPolicy,
    ProcessPolicy,
    ReportingPolicy,
)
from metrology_process_planner.domains.modes.mode_policies import (
    CaptureSequenceDefinition,
    MeasurementPolicy,
    MetadataSchema,
    ModeCapabilities,
    SetupDefinition,
)


def mode_kwargs_from_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return normalized constructor kwargs for a mode definition."""

    primitives = _strings(data.get("primitives", ("site_box",)))
    return {
        "mode_id": str(data.get("mode_id", data.get("id", ""))),
        "display_name": str(data.get("display_name", data.get("label", ""))),
        "version": str(data.get("version", "1.0.0")),
        "family": str(data.get("family", "generic_capture")),
        "description": str(data.get("description", "")),
        "visible": bool(data.get("visible", True)),
        "category": str(data.get("category", "")),
        "capabilities": _capabilities(data),
        "setup": SetupDefinition.from_mapping(_mapping(data.get("setup"))),
        "capture": _capture_policy(data, primitives),
        "metadata": _metadata_schema(data),
        "measurements": _measurement_policy(data),
        "artifacts": _artifact_policy(data),
        "process": _process_policy(data),
        "editor": _editor_policy(data),
        "reporting": ReportingPolicy.from_mapping(_mapping(data.get("reporting"))),
        "validation": _mapping(data.get("validation")),
        "extensions": _mapping(data.get("extensions")),
    }


def _capture_policy(
    data: Mapping[str, Any],
    primitives: tuple[str, ...],
) -> CaptureSequenceDefinition:
    capture_data = dict(_mapping(data.get("capture")))
    if "primitive" not in capture_data:
        capture_sequence = str(data.get("capture_sequence", "site_box"))
        capture_data["primitive"] = {"type": capture_sequence}
    return CaptureSequenceDefinition.from_mapping(capture_data, primitives)


def _capabilities(data: Mapping[str, Any]) -> ModeCapabilities:
    capabilities = dict(_mapping(data.get("capabilities")))
    if "supports_measurements" in data:
        capabilities["supports_measurements"] = data.get("supports_measurements")
    if _mapping(data.get("process")):
        capabilities["supports_process_solver"] = True
    return ModeCapabilities.from_mapping(capabilities)


def _metadata_schema(data: Mapping[str, Any]) -> MetadataSchema:
    metadata = dict(_mapping(data.get("metadata")))
    if "capture_fields" not in metadata:
        metadata["capture_fields"] = data.get("metadata_fields", ())
    return MetadataSchema.from_mapping(metadata)


def _measurement_policy(data: Mapping[str, Any]) -> MeasurementPolicy:
    measurement = dict(_mapping(data.get("measurements")))
    if "enabled" not in measurement and "supports_measurements" in data:
        measurement["enabled"] = data.get("supports_measurements")
    return MeasurementPolicy.from_mapping(measurement)


def _artifact_policy(data: Mapping[str, Any]) -> ArtifactPolicy:
    artifacts = dict(_mapping(data.get("artifacts")))
    if "on_capture_save" not in artifacts:
        artifacts["on_capture_save"] = data.get("artifact_roles", ())
    return ArtifactPolicy.from_mapping(artifacts)


def _process_policy(data: Mapping[str, Any]) -> ProcessPolicy:
    process = dict(_mapping(data.get("process")))
    if "recipe_policy" not in process:
        process["recipe_policy"] = data.get("recipe_policy", "forbidden")
    if "solver_request" not in process:
        process["solver_request"] = {"operation": data.get("solver_operation", "none")}
    return ProcessPolicy.from_mapping(process)


def _editor_policy(data: Mapping[str, Any]) -> EditorPolicy:
    editor = dict(_mapping(data.get("editor")))
    if "navigator_groups" not in editor:
        editor["navigator_groups"] = data.get(
            "editor_groups",
            ("dashboard", "setup", "captures", "warnings"),
        )
    return EditorPolicy.from_mapping(editor)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _strings(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return ()

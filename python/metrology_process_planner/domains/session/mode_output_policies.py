"""Artifact, process, editor, and reporting mode policies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ArtifactOutputDefinition:
    """One artifact output declared by a mode."""

    artifact_type: str
    role: str
    required: bool = False
    generator: str = ""
    dependencies: tuple[str, ...] = ()

    @classmethod
    def from_value(cls, value: object) -> ArtifactOutputDefinition:
        """Build an artifact output from JSON-compatible mode data."""

        if isinstance(value, Mapping):
            return cls(
                str(value.get("artifact_type", value.get("type", ""))),
                str(value.get("role", "")),
                bool(value.get("required", False)),
                str(value.get("generator", "")),
                _strings(value.get("dependencies", ())),
            )
        text = str(value)
        return cls(text, text)


@dataclass(frozen=True)
class ArtifactPolicy:
    """Artifact generation policy for a mode."""

    on_capture_save: tuple[ArtifactOutputDefinition, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ArtifactPolicy:
        """Build an artifact policy from mode data."""

        outputs = tuple(
            ArtifactOutputDefinition.from_value(item)
            for item in data.get("on_capture_save", ())
        )
        return cls(outputs)

    def roles_on_capture_save(self) -> tuple[str, ...]:
        """Return declared capture-save artifact roles."""

        return tuple(item.role for item in self.on_capture_save if item.role)

    def annotation_role_on_capture_save(self) -> str:
        """Return the declared layout-annotation role for capture save."""

        for item in self.on_capture_save:
            if item.artifact_type == "layout_annotation" and item.role:
                return item.role
        return ""

    def process_roles_on_capture_save(self) -> tuple[str, ...]:
        """Return declared process-output roles for capture save."""

        return tuple(
            item.role
            for item in self.on_capture_save
            if item.artifact_type == "process_output" and item.role
        )


@dataclass(frozen=True)
class ProcessPolicy:
    """Process-solver policy for a mode."""

    recipe_policy: str = "optional"
    solver_operation: str = "none"
    render_profile: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ProcessPolicy:
        """Build a process policy from mode data."""

        solver = _mapping(data.get("solver_request"))
        return cls(
            str(data.get("recipe_policy", "optional")),
            str(solver.get("operation", "none")),
            str(solver.get("render_profile", "")),
        )


@dataclass(frozen=True)
class EditorPolicy:
    """Session editor policy for a mode."""

    navigator_groups: tuple[str, ...] = ("dashboard", "setup", "captures", "warnings")
    preview_modes: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> EditorPolicy:
        """Build an editor policy from mode data."""

        return cls(
            _strings(data.get("navigator_groups", cls.navigator_groups)),
            _strings(data.get("preview_modes", ())),
            _strings(data.get("actions", ())),
        )


@dataclass(frozen=True)
class ReportingPolicy:
    """Report generation policy for a mode."""

    enabled: bool = False
    sections: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ReportingPolicy:
        """Build a reporting policy from mode data."""

        return cls(bool(data.get("enabled", False)), _strings(data.get("sections", ())))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _strings(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ()

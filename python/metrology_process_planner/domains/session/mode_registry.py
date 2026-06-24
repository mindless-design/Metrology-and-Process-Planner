"""Declarative session mode definitions and registry helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from metrology_process_planner.domains.session.mode_output_policies import (
    ArtifactPolicy,
    EditorPolicy,
    ProcessPolicy,
    ReportingPolicy,
)
from metrology_process_planner.domains.session.mode_policies import (
    CaptureSequenceDefinition,
    MeasurementPolicy,
    MetadataSchema,
    ModeCapabilities,
    SetupDefinition,
)
from metrology_process_planner.domains.session.mode_validation import (
    ModeCompatibilityReport,
    ModeValidator,
)


@dataclass(frozen=True)
class ModeDefinition:
    """Declarative configuration for one workflow mode."""

    mode_id: str
    display_name: str
    version: str = "1.0.0"
    family: str = "generic_capture"
    description: str = ""
    visible: bool = True
    category: str = ""
    capabilities: ModeCapabilities = ModeCapabilities()
    setup: SetupDefinition = SetupDefinition()
    capture: CaptureSequenceDefinition = CaptureSequenceDefinition()
    metadata: MetadataSchema = MetadataSchema()
    measurements: MeasurementPolicy = MeasurementPolicy()
    artifacts: ArtifactPolicy = ArtifactPolicy()
    process: ProcessPolicy = ProcessPolicy()
    editor: EditorPolicy = EditorPolicy()
    reporting: ReportingPolicy = ReportingPolicy()
    validation: Mapping[str, Any] | None = None
    extensions: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ModeDefinition:
        """Build a mode definition from JSON-compatible data."""

        from metrology_process_planner.domains.session.mode_definition_io import (
            mode_kwargs_from_mapping,
        )

        return cls(**mode_kwargs_from_mapping(data))

    def compatibility_report(self) -> ModeCompatibilityReport:
        """Return a structured compatibility report."""

        return ModeValidator().validate(self)

    def validation_warnings(self) -> tuple[str, ...]:
        """Return user-facing validation messages."""

        return self.compatibility_report().messages()


class ModeRegistry:
    """Registry of declarative mode definitions."""

    def __init__(self, definitions: Iterable[ModeDefinition]) -> None:
        self._definitions = tuple(definitions)

    def definitions(self) -> tuple[ModeDefinition, ...]:
        """Return registered definitions in declaration order."""

        return self._definitions

    def mode_ids(self) -> tuple[str, ...]:
        """Return registered definition ids in declaration order."""

        return tuple(definition.mode_id for definition in self._definitions if definition.mode_id)

    def definition(self, mode_id: str) -> ModeDefinition:
        """Return one mode definition or a safe unsupported placeholder."""

        for definition in self._definitions:
            if definition.mode_id == mode_id:
                return definition
        return ModeDefinition(mode_id, f"Unsupported Mode: {mode_id}", visible=False)

    def compatibility_reports(self) -> tuple[ModeCompatibilityReport, ...]:
        """Return validation reports for all registered definitions."""

        validator = ModeValidator()
        return tuple(validator.validate(definition) for definition in self._definitions)

    def validation_warnings(self) -> tuple[str, ...]:
        """Return registry-level and definition-level validation warnings."""

        warnings: list[str] = []
        seen: set[str] = set()
        for definition in self._definitions:
            warnings.extend(definition.validation_warnings())
            if definition.mode_id and definition.mode_id in seen:
                warnings.append(f"Duplicate mode id: {definition.mode_id}")
            seen.add(definition.mode_id)
        return tuple(warnings)


def built_in_mode_registry() -> ModeRegistry:
    """Return declarative definitions for built-in session modes."""

    from metrology_process_planner.domains.session.mode_builtins import (
        built_in_mode_registry as _built_in_mode_registry,
    )

    return _built_in_mode_registry()

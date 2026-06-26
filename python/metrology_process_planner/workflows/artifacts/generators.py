"""Artifact generator registry contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from metrology_process_planner.domains.session import ArtifactRecord, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths


class ArtifactGenerator(Protocol):
    """Callable artifact generator contract used by repair services."""

    def __call__(
        self,
        session: SessionRecord,
        artifact: ArtifactRecord,
        paths: SessionPaths,
    ) -> ArtifactRecord | ArtifactGenerationResult:
        """Generate an artifact and return the updated artifact record."""


@dataclass(frozen=True)
class ArtifactGenerationResult:
    """Result returned by generators that update session-owned references."""

    artifact: ArtifactRecord
    session: SessionRecord | None = None


@dataclass(frozen=True)
class GeneratorRegistration:
    """Declared generator capabilities."""

    generator_id: str
    artifact_types_supported: tuple[str, ...]
    required_inputs: tuple[str, ...] = ()
    requires_live_layout: bool = False
    requires_recipe: bool = False
    requires_solver: bool = False
    requires_parent_image: bool = False
    can_run_headless: bool = True
    output_formats: tuple[str, ...] = ()
    handler: ArtifactGenerator | None = None


class ArtifactGeneratorRegistry:
    """Registry of artifact generators and their repair capabilities."""

    def __init__(
        self,
        registrations: tuple[GeneratorRegistration, ...] = (),
    ) -> None:
        self._registrations: dict[str, GeneratorRegistration] = {
            item.generator_id: item for item in registrations
        }

    def register(self, registration: GeneratorRegistration) -> None:
        """Register or replace one generator declaration."""

        self._registrations[registration.generator_id] = registration

    def generator_for(self, artifact: ArtifactRecord) -> GeneratorRegistration | None:
        """Return the preferred generator for an artifact."""

        if artifact.generator in self._registrations:
            return self._registrations[artifact.generator]
        owner_role = artifact.owner.role
        if owner_role:
            for registration in self._registrations.values():
                if owner_role in registration.artifact_types_supported:
                    return registration
        for registration in self._registrations.values():
            if artifact.type in registration.artifact_types_supported:
                return registration
        return None

    def registrations(self) -> tuple[GeneratorRegistration, ...]:
        """Return all known registrations."""

        return tuple(self._registrations.values())

    def summary(self) -> Mapping[str, str]:
        """Return compact diagnostics metadata."""

        return {
            item.generator_id: ",".join(item.artifact_types_supported)
            for item in self._registrations.values()
        }


def built_in_generator_registry() -> ArtifactGeneratorRegistry:
    """Return generator declarations known to the artifact lifecycle system."""

    from metrology_process_planner.workflows.artifacts.generator_builtins import (
        built_in_registrations,
    )

    return ArtifactGeneratorRegistry(built_in_registrations())

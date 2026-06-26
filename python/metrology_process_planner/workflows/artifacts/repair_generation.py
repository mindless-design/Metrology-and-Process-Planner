"""Artifact generation call helpers used by repair services."""

from __future__ import annotations

import inspect
from typing import Protocol, cast

from metrology_process_planner.domains.session import ArtifactRecord, ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.generators import (
    ArtifactGenerationResult,
    ArtifactGenerator,
)


class _ModeRegistryArtifactGenerator(Protocol):
    def __call__(
        self,
        session: SessionRecord,
        artifact: ArtifactRecord,
        paths: SessionPaths,
        *,
        mode_registry: ModeRegistry | None,
    ) -> ArtifactRecord | ArtifactGenerationResult:
        """Generate an artifact with active mode visibility context."""


def call_handler(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
    handler: ArtifactGenerator,
    mode_registry: ModeRegistry | None,
) -> ArtifactRecord | ArtifactGenerationResult:
    """Call a generator, passing mode registry only when supported."""

    if handler_accepts_mode_registry(handler):
        handler_with_registry = cast(_ModeRegistryArtifactGenerator, handler)
        return handler_with_registry(session, artifact, paths, mode_registry=mode_registry)
    return handler(session, artifact, paths)


def handler_accepts_mode_registry(handler: ArtifactGenerator) -> bool:
    """Return whether a generator accepts a mode registry keyword."""

    try:
        signature = inspect.signature(handler)
    except (TypeError, ValueError):
        return False
    parameters = tuple(signature.parameters.values())
    if "mode_registry" in signature.parameters:
        return True
    return any(parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters)


def generation_result(
    session: SessionRecord,
    generated: ArtifactRecord | ArtifactGenerationResult,
) -> tuple[SessionRecord, ArtifactRecord]:
    """Normalize direct artifact and session-aware generation results."""

    if isinstance(generated, ArtifactGenerationResult):
        return generated.session or session, generated.artifact
    return session, generated

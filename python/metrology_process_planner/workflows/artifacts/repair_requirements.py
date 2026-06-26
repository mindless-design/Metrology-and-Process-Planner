"""Generator registration requirement checks for artifact repair."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.artifacts.generators import GeneratorRegistration
from metrology_process_planner.workflows.artifacts.requests import (
    RepairRequest,
    RepairRequestStatus,
)
from metrology_process_planner.workflows.artifacts.warnings import (
    RECIPE_REQUIRED_FOR_REPAIR,
    SOLVER_REQUIRED_FOR_REPAIR,
    SOURCE_LAYOUT_REQUIRED_FOR_REPAIR,
)


def with_registration_requirements(
    session: SessionRecord,
    request: RepairRequest,
    registration: GeneratorRegistration | None,
) -> RepairRequest:
    """Apply generator-declared context requirements to a repair request."""

    if registration is None:
        return request
    requirements = _registration_requirements(session, registration)
    if not requirements:
        return request
    return replace(
        request,
        status=RepairRequestStatus.UNAVAILABLE,
        requirements=request.requirements + requirements,
        user_message=_registration_requirement_message(requirements),
        technical_details="; ".join(request.requirements + requirements),
    )


def _registration_requirements(
    session: SessionRecord,
    registration: GeneratorRegistration,
) -> tuple[str, ...]:
    requirements: list[str] = []
    if registration.requires_live_layout and not session.source_layout.layout_path:
        requirements.append(SOURCE_LAYOUT_REQUIRED_FOR_REPAIR)
    if registration.requires_recipe and not session.process_context.recipe_path:
        requirements.append(RECIPE_REQUIRED_FOR_REPAIR)
    if registration.requires_solver and not session.process_context.solver_backend:
        requirements.append(SOLVER_REQUIRED_FOR_REPAIR)
    return tuple(requirements)


def _registration_requirement_message(requirements: tuple[str, ...]) -> str:
    if SOURCE_LAYOUT_REQUIRED_FOR_REPAIR in requirements:
        return "Reopen the source layout before regenerating this artifact."
    return "Artifact repair is blocked by missing generator context."

"""Built-in compound capture requests."""

from __future__ import annotations

from typing import cast

from metrology_process_planner.domains.modes.mode_execution import ModeWorkflowPlanner
from metrology_process_planner.domains.session import built_in_mode_registry
from metrology_process_planner.workflows.compound_capture_models import CompoundCaptureRequest


def profilometry_request() -> CompoundCaptureRequest:
    """Return the built-in profilometry site-then-line request."""

    return _request("profilometry_planner")


def ellipsometry_request() -> CompoundCaptureRequest:
    """Return the built-in ellipsometry site-then-point request."""

    return _request("ellipsometry_planner")


def _request(mode_id: str) -> CompoundCaptureRequest:
    definition = built_in_mode_registry().definition(mode_id)
    return cast(CompoundCaptureRequest, ModeWorkflowPlanner().compound_capture_request(definition))

"""Mode-policy routing helpers for active compound capture workflows."""

from __future__ import annotations

from typing import Any, cast

from metrology_process_planner.domains.modes.mode_execution import ModeWorkflowPlanner
from metrology_process_planner.domains.modes.mode_registry import ModeRegistry
from metrology_process_planner.domains.session import SessionRecord, built_in_mode_registry
from metrology_process_planner.workflows.compound_capture_models import CompoundCaptureRequest


def active_compound_request(
    session: SessionRecord,
    expected_child_kind: str,
    registry: ModeRegistry | None = None,
) -> CompoundCaptureRequest | None:
    """Return the active compound request when workflow state matches mode policy."""

    workflow = session.workflow
    if not _workflow_has_compound_context(session):
        return None
    active_registry = registry if registry is not None else built_in_mode_registry()
    definition = active_registry.definition(workflow.active_mode)
    capture = definition.capture
    if not _capture_matches_workflow(session, capture, expected_child_kind):
        return None
    request = ModeWorkflowPlanner().compound_capture_request(definition)
    return cast(CompoundCaptureRequest, request)


def _workflow_has_compound_context(session: SessionRecord) -> bool:
    workflow = session.workflow
    return bool(workflow.active_mode and workflow.pending_item_ref)


def _capture_matches_workflow(
    session: SessionRecord,
    capture: Any,
    expected_child_kind: str,
) -> bool:
    return (
        capture.inner_feature_kind == expected_child_kind
        and session.workflow.stage == f"{capture.primitive_type}:child"
    )

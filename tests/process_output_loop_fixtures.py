"""Fixtures for process-output loop tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_point_feature,
    arm_inner_feature_capture,
    ellipsometry_request,
    save_composite_capture,
)
from metrology_process_planner.workflows.process_context import attach_recipe
from metrology_process_planner.workflows.process_context_models import AttachRecipeCommand
from tests.compound_capture_fixtures import pending_parent
from tests.process_context_fixtures import recipe_path


def point_session_with_recipe(folder: Path):
    """Return an ellipsometry session with an attached process recipe."""

    saved = point_session_without_recipe()
    return attach_recipe(saved, AttachRecipeCommand(str(recipe_path(folder)))).session


def point_session_without_recipe():
    """Return an ellipsometry point-stack capture without a recipe."""

    session = arm_inner_feature_capture(
        pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
        "pending-001",
        ellipsometry_request(),
    )
    session = add_point_feature(session, "pending-001", Point(5, 5), ellipsometry_request())
    return save_composite_capture(
        session,
        SaveCompositeCaptureCommand("pending-001", "Film Site 01"),
    ).session


def line_session_with_operation(
    session,
    capture_type: str,
    extension_key: str,
    operation: str,
    render_profile: str,
    mode=None,
):
    """Return a line capture retargeted to one process-output operation."""

    capture = session.captures[0]
    extension = {
        "line_feature_id": "feat-001",
        "process_context_ref": "process_context.active",
        "solver_request": {
            "operation": operation,
            "process_window_variant": "target",
            "render_profile": render_profile,
        },
        "solver_result_id": None,
        "artifact_refs": {},
        "warning_ids": [],
    }
    updated_capture = replace(
        capture,
        type=capture_type,
        extensions={extension_key: extension},
    )
    return replace(
        session,
        mode=mode or session.mode,
        captures=(updated_capture,),
        process_outputs=(),
    )

"""Post-save measurement completion prompt workflow."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from metrology_process_planner.domains.session import (
    CanvasObjectType,
    CanvasVisualFlag,
    CaptureRecord,
    SessionRecord,
)
from metrology_process_planner.workflows.measurement_workflow import begin_measurement_line


class MeasurementCompletionChoice(str, Enum):
    """Allowed post-measurement completion choices."""

    TAKE_ANOTHER = "take_another_measurement"
    RETURN_TO_EDITOR = "return_to_editor"
    DONE = "done"


@dataclass(frozen=True)
class PostActionPrompt:
    """One action-oriented prompt that a UI shell may render."""

    prompt_id: str
    title: str
    message: str
    choices: tuple[tuple[str, str], ...]
    related_item_id: str = ""
    blocking_allowed: bool = False


@dataclass(frozen=True)
class MeasurementCompletionResult:
    """Result from applying a post-measurement choice."""

    status: str
    session: SessionRecord
    message: str
    selected_item_id: str = ""


def measurement_completion_prompt(session: SessionRecord) -> PostActionPrompt | None:
    """Return the allowed post-measurement prompt when a measurement was just saved."""

    measurement = _last_saved_measurement(session)
    if measurement is None:
        return None
    measurement_id, capture_id = measurement
    return PostActionPrompt(
        "post_measurement_completion",
        "Measurement saved",
        "Do you want to take another measurement?",
        (
            (MeasurementCompletionChoice.TAKE_ANOTHER.value, "Take Another Measurement"),
            (MeasurementCompletionChoice.RETURN_TO_EDITOR.value, "Return to Editor"),
            (MeasurementCompletionChoice.DONE.value, "Done"),
        ),
        f"measurement:{measurement_id}",
        blocking_allowed=True,
    )


def apply_measurement_completion_choice(
    session: SessionRecord,
    choice: MeasurementCompletionChoice,
) -> MeasurementCompletionResult:
    """Apply one allowed post-measurement completion choice."""

    latest = _last_saved_measurement(session)
    if latest is None:
        return MeasurementCompletionResult(
            "unavailable",
            session,
            "No saved measurement is available for a completion choice.",
        )
    measurement_id, capture_id = latest
    if choice is MeasurementCompletionChoice.TAKE_ANOTHER:
        return MeasurementCompletionResult(
            "success",
            begin_measurement_line(session, capture_id),
            "Ready to take another measurement.",
            f"capture:{capture_id}",
        )
    if choice is MeasurementCompletionChoice.RETURN_TO_EDITOR:
        return MeasurementCompletionResult(
            "success",
            _clear_measurement_workflow(session),
            "Returned to the parent capture.",
            f"capture:{capture_id}",
        )
    return MeasurementCompletionResult(
        "success",
        _clear_measurement_workflow(session),
        "Measurement workflow complete.",
        f"measurement:{measurement_id}",
    )


def pending_measurement_count(session: SessionRecord) -> int:
    """Return the number of nested pending measurements."""

    return sum(
        1
        for capture in session.captures
        for measurement in capture.measurements
        if dict(measurement.metadata or {}).get("workflow_state") == "pending"
    )


def _last_saved_measurement(session: SessionRecord) -> tuple[str, str] | None:
    for capture in session.captures:
        latest = _latest_saved_measurement(capture)
        if latest is not None:
            return latest, capture.id
    return None


def _latest_saved_measurement(capture: CaptureRecord) -> str | None:
    for measurement in reversed(capture.measurements):
        if dict(measurement.metadata or {}).get("workflow_state") == "saved":
            return measurement.id
    return None


def _clear_measurement_workflow(session: SessionRecord) -> SessionRecord:
    workflow = replace(session.workflow, active=False, stage="", active_primitive="")
    objects = tuple(
        replace(
            item,
            visual_state=tuple(
                flag for flag in item.visual_state if flag is not CanvasVisualFlag.ACTIVE_PARENT
            ),
        )
        if item.object_type is not CanvasObjectType.MEASUREMENT
        else item
        for item in session.canvas_objects
    )
    return replace(session, workflow=workflow, canvas_objects=objects)

"""Pure state-machine evaluators for modeless UI surfaces."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.session import (
    ArtifactStatus,
    CanvasObjectType,
    SessionRecord,
)
from metrology_process_planner.workflows.canvas_interaction_models import InteractionContext


@dataclass(frozen=True)
class UiStateSnapshot:
    """Renderable state-machine output for editor, diagnostics, and status strips."""

    machine: str
    state: str
    message: str
    active_item_ref: str = ""
    action_ids: tuple[str, ...] = ()
    warning_ids: tuple[str, ...] = ()


class SessionUIStateMachine:
    """Summarize top-level session UI state without inspecting widgets."""

    def evaluate(self, session: SessionRecord | None) -> UiStateSnapshot:
        """Return the active session state for modeless surfaces."""

        if session is None:
            return UiStateSnapshot("session_ui", "no_session", "No active session.")
        if session.pending_captures:
            pending = session.pending_captures[0]
            return UiStateSnapshot(
                "session_ui",
                "pending_review",
                "Pending capture is waiting for review.",
                f"pending:{pending.id}",
                ("SavePendingCapture", "RetakePendingCapture", "DiscardPendingCapture"),
            )
        if session.workflow.active:
            return UiStateSnapshot(
                "session_ui",
                session.workflow.stage or "active",
                "Workflow is active.",
                session.workflow.pending_item_ref or "",
            )
        return UiStateSnapshot("session_ui", "idle", "Session is ready.")


class CaptureInteractionStateMachine:
    """Summarize armed canvas capture state from interaction context."""

    def evaluate(
        self,
        context: InteractionContext,
        session: SessionRecord | None = None,
    ) -> UiStateSnapshot:
        """Return the capture state and user-facing gesture hint."""

        if session is not None and session.pending_captures:
            return UiStateSnapshot(
                "capture_interaction",
                "pending_review",
                "Capture is waiting for review.",
                f"pending:{session.pending_captures[0].id}",
            )
        if context.live_preview_id and context.drag_start is not None:
            return UiStateSnapshot(
                "capture_interaction",
                "dragging_preview",
                "Release to validate the preview geometry.",
                context.live_preview_id,
            )
        return _armed_capture_state(context)


class PendingReviewStateMachine:
    """Summarize pending capture review state and available decisions."""

    def evaluate(self, session: SessionRecord) -> UiStateSnapshot:
        """Return pending review state for simple or child captures."""

        if not session.pending_captures:
            return UiStateSnapshot("pending_review", "idle", "No pending capture.")
        pending = session.pending_captures[0]
        actions = ("SavePendingCapture", "RetakePendingCapture", "DiscardPendingCapture")
        if pending.parent_id:
            actions = ("SaveCompositeCapture", "RetakeInnerFeature", "DiscardPendingCapture")
        return UiStateSnapshot(
            "pending_review",
            "pending_review",
            "Review pending capture metadata and artifacts.",
            f"pending:{pending.id}",
            actions,
        )


class MeasurementWorkflowStateMachine:
    """Summarize modeless measurement workflow and post-save prompt policy."""

    def evaluate(self, session: SessionRecord) -> UiStateSnapshot:
        """Return measurement state derived from workflow and nested records."""

        pending = _pending_measurement_ref(session)
        if pending:
            return UiStateSnapshot(
                "measurement_workflow",
                "pending_measurement",
                "Pending measurement is ready for review.",
                pending,
                ("SaveMeasurement", "RetakeMeasurementLine", "DiscardMeasurement"),
            )
        if session.workflow.stage == "measurement_line":
            return UiStateSnapshot(
                "measurement_workflow",
                "armed_line",
                "Draw measurement line inside selected capture.",
                session.workflow.pending_item_ref or "",
                ("CancelCapture",),
            )
        return UiStateSnapshot("measurement_workflow", "idle", "No measurement is active.")


class RecipeContextStateMachine:
    """Summarize process recipe context without blocking capture save."""

    def evaluate(self, session: SessionRecord) -> UiStateSnapshot:
        """Return recipe/process context status for editor headers."""

        context = session.process_context
        if context.warning_ids:
            return UiStateSnapshot(
                "recipe_context",
                "warning",
                "Recipe context has warnings.",
                context.recipe_id,
                ("AttachRecipe", "ValidateProcessContext"),
                context.warning_ids,
            )
        if context.recipe_id or context.recipe_path:
            return UiStateSnapshot(
                "recipe_context",
                "attached",
                "Recipe is attached.",
                context.recipe_id or context.recipe_path,
                ("DetachRecipe", "ValidateProcessContext"),
            )
        return UiStateSnapshot(
            "recipe_context",
            "none",
            "No recipe is attached.",
            action_ids=("AttachRecipe",),
        )


class ArtifactRepairStateMachine:
    """Summarize missing, stale, failed, and pending artifact repair work."""

    def evaluate(self, session: SessionRecord) -> UiStateSnapshot:
        """Return artifact repair state for diagnostics and editor warnings."""

        artifacts = tuple((session.artifacts or {}).values())
        repairable = tuple(
            artifact
            for artifact in artifacts
            if artifact.status
            in {
                ArtifactStatus.MISSING,
                ArtifactStatus.STALE,
                ArtifactStatus.FAILED,
                ArtifactStatus.PENDING,
                ArtifactStatus.PENDING_SOLVER,
            }
        )
        if not repairable:
            return UiStateSnapshot("artifact_repair", "idle", "No artifact repair tasks.")
        warning_ids = tuple(
            dict.fromkeys(item for artifact in repairable for item in artifact.warning_ids)
        )
        return UiStateSnapshot(
            "artifact_repair",
            "open_tasks",
            f"{len(repairable)} artifact repair task(s).",
            repairable[0].id,
            ("RegenerateArtifact", "RegenerateProcessOutput"),
            warning_ids,
        )


def _armed_capture_state(context: InteractionContext) -> UiStateSnapshot:
    primitive = context.armed_object_type
    if primitive is CanvasObjectType.SITE_BOX:
        return UiStateSnapshot("capture_interaction", "armed_box", "Hold Left Shift and drag.")
    if primitive in {CanvasObjectType.LINE, CanvasObjectType.MEASUREMENT}:
        return UiStateSnapshot("capture_interaction", "armed_line", "Hold Left Shift and drag.")
    if primitive in {CanvasObjectType.POINT, CanvasObjectType.ELLIPSOMETRY_POINT}:
        return UiStateSnapshot("capture_interaction", "armed_point", "Hold Left Shift and click.")
    return UiStateSnapshot("capture_interaction", "idle", "No capture tool is armed.")


def _pending_measurement_ref(session: SessionRecord) -> str:
    for capture in session.captures:
        for measurement in capture.measurements:
            if dict(measurement.metadata or {}).get("workflow_state") == "pending":
                return f"measurement:{measurement.id}"
    return ""

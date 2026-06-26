"""Auto-save helpers for modes that skip pending capture review."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.capture_review_policy import mode_requires_capture_review
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService


def should_auto_save_capture(
    session: SessionRecord,
    metadata: dict[str, object],
    mode_registry: ModeRegistry | None = None,
) -> bool:
    """Return whether one committed pending capture should be promoted immediately."""

    requires_review = mode_requires_capture_review(session, mode_registry)
    return not requires_review and "replacement_for" not in metadata


def auto_save_pending_capture(
    session: SessionRecord,
    context: InteractionContext,
    pending_id: str,
    image_path: str,
    mode_registry: ModeRegistry | None = None,
) -> InteractionResult:
    """Promote a pending capture while preserving the crop request."""

    result = PendingCaptureReviewService(mode_registry=mode_registry).save_pending_box(
        session,
        context,
        pending_id,
    )
    return replace(result, artifact_requests=(image_path,))

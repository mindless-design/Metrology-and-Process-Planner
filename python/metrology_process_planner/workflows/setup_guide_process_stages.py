"""Setup-guide stages for process context and readiness."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupStageSnapshot,
    SetupStageStatus,
)


def recipe_stage(session: SessionRecord) -> SetupStageSnapshot:
    """Return the process recipe setup card."""

    has_recipe = bool(session.process_context.recipe_id or session.process_context.recipe_path)
    return SetupStageSnapshot(
        "recipe_context",
        "recipe_select",
        "Attach recipe",
        SetupStageStatus.COMPLETE if has_recipe else SetupStageStatus.WARNING,
        required=False,
        description="Attach a process recipe before process-aware outputs are generated.",
        primary_action=SetupGuideAction("AttachRecipe", "Attach Recipe"),
        secondary_actions=(SetupGuideAction("ValidateRecipeContext", "Validate"),),
        warning_ids=session.process_context.warning_ids,
    )

"""Setup-guide recipe attachment through operator-selected paths."""

from __future__ import annotations

from metrology_process_planner.app.command_types import CommandBlockedError, CommandId
from metrology_process_planner.app.recipe_path_adapter import RecipePathAdapter
from metrology_process_planner.app.session_document_command_results import selection_result
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.process_context import attach_recipe
from metrology_process_planner.workflows.process_context_models import AttachRecipeCommand


def attach_selected_recipe(
    session: SessionRecord,
    adapter: RecipePathAdapter,
    mode_registry: ModeRegistry | None = None,
) -> tuple[SessionRecord, CommandRouteResult]:
    """Attach a picker-selected recipe path to a process-aware session."""

    if not mode_is_process_aware(session, mode_registry):
        raise CommandBlockedError(
            "Recipe attachment is not available for this recipe-free mode.",
            "Continue setup without attaching a process recipe.",
        )
    selection = adapter.select_attach_recipe()
    if selection.status != "selected" or selection.path is None:
        return (
            session,
            selection_result(CommandId.ATTACH_RECIPE, selection.status, selection.message),
        )
    result = attach_recipe(session, AttachRecipeCommand(str(selection.path)))
    return (
        result.session,
        CommandRouteResult(
            CommandId.ATTACH_RECIPE,
            result.status,
            result.message,
            updated_document_id=result.session.id,
            warning_ids=tuple(warning.id for warning in result.warnings),
            next_ui_hint="Recipe process context updated.",
        ),
    )

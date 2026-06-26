"""Recipe editor command handlers with host path-picker adapters."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.recipe_path_adapter import (
    RecipePathAdapter,
    RecipePathSelection,
    UnavailableRecipePathAdapter,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


class RecipeCommandService:
    """Route app-level recipe commands through controller and path adapters."""

    def __init__(
        self,
        controller: RecipeEditorController,
        path_adapter: RecipePathAdapter | None = None,
    ) -> None:
        self._controller = controller
        self._path_adapter = path_adapter or UnavailableRecipePathAdapter()

    def new_recipe(self) -> CommandRouteResult:
        """Create a new modeless recipe through the recipe controller."""

        return _route_result(CommandId.NEW_RECIPE, self._controller.new_current())

    def open_recipe(self) -> CommandRouteResult:
        """Open a recipe selected by the host path adapter."""

        selection = self._path_adapter.select_open_recipe()
        if selection.path is None:
            return _selection_result(CommandId.OPEN_RECIPE, selection)
        return _route_result(
            CommandId.OPEN_RECIPE,
            self._controller.open_recipe_path(str(selection.path)),
        )

    def save_recipe(self) -> CommandRouteResult:
        """Save the current recipe through the recipe controller."""

        return _route_result(CommandId.SAVE_RECIPE, self._controller.save_current())

    def save_recipe_as(self) -> CommandRouteResult:
        """Save the current recipe to a host-selected destination."""

        selection = self._path_adapter.select_save_recipe_as()
        if selection.path is None:
            return _selection_result(CommandId.SAVE_RECIPE_AS, selection)
        return _route_result(
            CommandId.SAVE_RECIPE_AS,
            self._controller.save_current(str(selection.path), CommandId.SAVE_RECIPE_AS),
        )

    def attach_recipe_to_active_session(self) -> CommandRouteResult:
        """Attach the loaded recipe to the active process-aware session."""

        return _route_result(
            CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION,
            self._controller.dispatch_action("AttachRecipeToActiveSession"),
        )


def register_recipe_command_handlers(
    command_registry: CommandRegistry,
    recipe_commands: RecipeCommandService,
) -> None:
    """Register recipe command handlers."""

    command_registry.register(CommandId.NEW_RECIPE, recipe_commands.new_recipe)
    command_registry.register(CommandId.OPEN_RECIPE, recipe_commands.open_recipe)
    command_registry.register(CommandId.SAVE_RECIPE, recipe_commands.save_recipe)
    command_registry.register(CommandId.SAVE_RECIPE_AS, recipe_commands.save_recipe_as)
    command_registry.register(
        CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION,
        recipe_commands.attach_recipe_to_active_session,
    )


def _route_result(
    command_id: CommandId,
    result: RecipeEditorActionResult,
) -> CommandRouteResult:
    return CommandRouteResult(
        result.command_id or command_id,
        result.status,
        result.message,
        selected_item_id=result.selected_card_id,
        warning_ids=result.warning_ids,
        next_ui_hint=result.next_ui_hint,
        output_path=_recipe_path(result),
    )


def _selection_result(
    command_id: CommandId,
    selection: RecipePathSelection,
) -> CommandRouteResult:
    return CommandRouteResult(command_id, selection.status, selection.message)


def _recipe_path(result: RecipeEditorActionResult) -> str:
    if result.recipe is None:
        return ""
    return str(dict(result.recipe.metadata or {}).get("recipe_path", ""))

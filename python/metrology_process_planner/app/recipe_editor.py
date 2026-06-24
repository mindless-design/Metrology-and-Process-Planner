"""Application controller for the recipe editor surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.recipe_editor_opening import (
    dirty_switch_block,
    new_recipe,
    open_recipe,
)
from metrology_process_planner.app.recipe_editor_saving import save_recipe
from metrology_process_planner.app.window_registry import WindowOpenStatus, WindowRegistry
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.persistence.recipe_store import ProcessRecipeJsonStore
from metrology_process_planner.ui.modeless import (
    InMemoryModelessSurfaceFactory,
    ModelessSurfaceShell,
)
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter
from metrology_process_planner.ui.recipe_editor.view_models import RecipeEditorViewModel
from metrology_process_planner.workflows.recipe_editor_actions import RecipeEditorActionDispatcher
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


@dataclass(frozen=True)
class RecipeEditorOpenResult:
    """Result of opening or refreshing the recipe editor."""

    status: str
    view_model: RecipeEditorViewModel
    message: str = ""
    window: Any | None = None


class RecipeEditorController:
    """Resolve recipe editor commands without saving recipe files directly."""

    def __init__(
        self,
        presenter: RecipeEditorPresenter | None = None,
        dispatcher: RecipeEditorActionDispatcher | None = None,
        recipe_store: ProcessRecipeJsonStore | None = None,
        shell: ModelessSurfaceShell | None = None,
        window_registry: WindowRegistry[Any] | None = None,
    ) -> None:
        self._presenter = presenter if presenter is not None else RecipeEditorPresenter()
        self._dispatcher = dispatcher if dispatcher is not None else RecipeEditorActionDispatcher()
        self._recipe_store = recipe_store if recipe_store is not None else ProcessRecipeJsonStore()
        self._shell = shell or ModelessSurfaceShell(InMemoryModelessSurfaceFactory())
        self._window_registry = window_registry if window_registry is not None else WindowRegistry()
        self.current_recipe: ProcessRecipe | None = None
        self.last_action_result: RecipeEditorActionResult | None = None

    def set_recipe(self, recipe: ProcessRecipe | None) -> None:
        """Set the recipe currently shown by the editor."""

        self.current_recipe = recipe

    def open_current(self) -> RecipeEditorOpenResult:
        """Return a recipe editor view model for the current recipe."""

        view_model = self._presenter.build(self.current_recipe)
        registry_result = self._window_registry.open_or_raise(
            _window_key(self.current_recipe),
            _window_title(view_model),
            lambda: self._shell.open(_window_title(view_model), view_model),
            refresh_existing=lambda window: self._shell.render(window, view_model),
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return RecipeEditorOpenResult("failed", view_model, registry_result.message)
        if registry_result.window is not None:
            self._attach_action_callback(registry_result.window)
        status = _status(registry_result.status, self.current_recipe)
        return RecipeEditorOpenResult(status, view_model, window=registry_result.window)

    def dispatch_action(self, action_id: str) -> RecipeEditorActionResult:
        """Dispatch a recipe editor action and refresh the modeless window."""

        if action_id.startswith("CloseRecipeEditor"):
            return self.close_current(force_discard=action_id.endswith(":discard"))
        if action_id.startswith("NewRecipe"):
            return self.new_current(force_discard=action_id.endswith(":discard"))
        if action_id.startswith("OpenRecipe"):
            force_discard, payload = _discard_payload(action_id)
            return self.open_recipe_path(payload, force_discard)
        if action_id == "SaveRecipe":
            return self.save_current()
        if action_id.startswith("SaveRecipeAs"):
            return self.save_current(_action_payload(action_id), CommandId.SAVE_RECIPE_AS)
        result = self._dispatcher.dispatch(self.current_recipe, action_id)
        self.last_action_result = result
        if result.recipe is not None:
            self.current_recipe = result.recipe
        self.open_current()
        return result

    def close_current(self, force_discard: bool = False) -> RecipeEditorActionResult:
        """Close the modeless recipe editor or block on unsaved edits."""

        if _is_dirty(self.current_recipe) and not force_discard:
            result = RecipeEditorActionResult(
                "blocked",
                CommandId.CLOSE_RECIPE_EDITOR,
                "Recipe has unsaved edits.",
                self.current_recipe,
                next_ui_hint="Save the recipe or confirm discard before closing.",
            )
            self.last_action_result = result
            return result
        self._window_registry.close(_window_key(self.current_recipe))
        result = RecipeEditorActionResult(
            "success",
            CommandId.CLOSE_RECIPE_EDITOR,
            _close_message(force_discard),
            self.current_recipe,
            next_ui_hint="Return to the session editor when ready.",
        )
        self.last_action_result = result
        return result

    def new_current(self, force_discard: bool = False) -> RecipeEditorActionResult:
        """Create a new in-memory recipe or block on unsaved edits."""

        recipe = self.current_recipe
        if _is_dirty(recipe) and not force_discard and recipe is not None:
            return self._remember(dirty_switch_block(CommandId.NEW_RECIPE, recipe))
        return self._replace_current(new_recipe())

    def open_recipe_path(
        self,
        path_text: str,
        force_discard: bool = False,
    ) -> RecipeEditorActionResult:
        """Open a recipe path or block on unsaved edits."""

        recipe = self.current_recipe
        if _is_dirty(recipe) and not force_discard and recipe is not None:
            return self._remember(dirty_switch_block(CommandId.OPEN_RECIPE, recipe))
        return self._replace_current(open_recipe(path_text, self._recipe_store))

    def save_current(
        self,
        path_override: str = "",
        command_id: CommandId = CommandId.SAVE_RECIPE,
    ) -> RecipeEditorActionResult:
        """Save the current recipe and refresh the modeless window on success."""

        outcome = save_recipe(
            self.current_recipe,
            self._recipe_store,
            command_id,
            path_override,
        )
        if outcome.recipe is not None:
            self.current_recipe = outcome.recipe
        if outcome.result.status == "success":
            self.open_current()
        return self._remember(outcome.result)

    def _attach_action_callback(self, window: Any) -> None:
        if isinstance(window, dict):
            window["on_action"] = self.dispatch_action

    def _remember(self, result: RecipeEditorActionResult) -> RecipeEditorActionResult:
        self.last_action_result = result
        return result

    def _replace_current(self, result: RecipeEditorActionResult) -> RecipeEditorActionResult:
        if result.recipe is not None:
            self._window_registry.close(_window_key(self.current_recipe))
            self.current_recipe = result.recipe
            self.open_current()
        return self._remember(result)


def _window_key(recipe: ProcessRecipe | None) -> str:
    recipe_id = recipe.id if recipe is not None else "no-recipe"
    return f"recipe-editor:{recipe_id}"


def _window_title(view_model: RecipeEditorViewModel) -> str:
    return f"Recipe Editor - {view_model.title}"


def _is_dirty(recipe: ProcessRecipe | None) -> bool:
    return bool(recipe is not None and dict(recipe.metadata or {}).get("dirty", False))


def _close_message(force_discard: bool) -> str:
    if force_discard:
        return "Recipe editor closed and unsaved edits were discarded."
    return "Recipe editor closed."


def _status(status: WindowOpenStatus, recipe: ProcessRecipe | None) -> str:
    if status is WindowOpenStatus.RAISED:
        return "raised"
    return "opened" if recipe is not None else "unavailable"


def _action_payload(action_id: str) -> str:
    if ":" not in action_id:
        return ""
    return action_id.split(":", 1)[1]


def _discard_payload(action_id: str) -> tuple[bool, str]:
    payload = _action_payload(action_id)
    if payload.startswith("discard:"):
        return True, payload.removeprefix("discard:")
    return False, payload

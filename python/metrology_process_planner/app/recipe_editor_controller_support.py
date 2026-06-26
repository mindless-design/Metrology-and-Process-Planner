"""Small helpers for the recipe editor controller."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.ui.recipe_editor.view_models import RecipeEditorViewModel


def recipe_id(recipe: ProcessRecipe | None) -> str:
    """Return the modeless registry id for a recipe."""

    return recipe.id if recipe is not None else "no-recipe"


def window_title(view_model: RecipeEditorViewModel) -> str:
    """Return the recipe editor window title."""

    return f"Recipe Editor - {view_model.title}"


def is_dirty(recipe: ProcessRecipe | None) -> bool:
    """Return whether a recipe has unsaved editor edits."""

    return bool(recipe is not None and dict(recipe.metadata or {}).get("dirty", False))


def action_payload(action_id: str) -> str:
    """Return the optional payload after an action id delimiter."""

    if ":" not in action_id:
        return ""
    return action_id.split(":", 1)[1]


def discard_payload(action_id: str) -> tuple[bool, str]:
    """Return discard confirmation state and the remaining action payload."""

    payload = action_payload(action_id)
    if payload.startswith("discard:"):
        return True, payload.removeprefix("discard:")
    return False, payload

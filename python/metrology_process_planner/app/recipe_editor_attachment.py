"""Attach recipe-editor recipes to the active session through workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.process_context import attach_recipe
from metrology_process_planner.workflows.process_context_models import AttachRecipeCommand
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


class SessionProvider(Protocol):
    """Return the active session, when one is loaded."""

    def __call__(self) -> SessionRecord | None:
        """Return the active session."""


class SessionUpdater(Protocol):
    """Persist an updated active session back into the app model."""

    def __call__(self, session: SessionRecord) -> None:
        """Update the active session."""


def attach_recipe_to_session(
    recipe: ProcessRecipe | None,
    session_provider: SessionProvider | None,
    session_updater: SessionUpdater | None,
) -> RecipeEditorActionResult:
    """Attach the current saved recipe to the active session."""

    if recipe is None:
        return _result("unavailable", "No recipe is loaded.", recipe, "Open a recipe first.")
    if dict(recipe.metadata or {}).get("dirty", False):
        return _result("blocked", "Recipe has unsaved edits.", recipe, "Save the recipe first.")
    path_text = str(dict(recipe.metadata or {}).get("recipe_path", ""))
    if not path_text:
        return _result("unavailable", "Recipe has not been saved.", recipe, "Use Save As first.")
    if session_provider is None or session_updater is None:
        return _result("unavailable", "No active session binding is available.", recipe)
    session = session_provider()
    if session is None:
        return _result("unavailable", "No active session is loaded.", recipe)
    process_result = attach_recipe(session, AttachRecipeCommand(str(Path(path_text))))
    if process_result.status == "success":
        session_updater(process_result.session)
    return RecipeEditorActionResult(
        process_result.status,
        CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION,
        process_result.message,
        recipe,
        warning_ids=tuple(warning.id for warning in process_result.warnings),
        next_ui_hint=_hint(process_result.status),
    )


def _result(
    status: str,
    message: str,
    recipe: ProcessRecipe | None,
    hint: str = "Open a session in the unified editor before attaching a recipe.",
) -> RecipeEditorActionResult:
    return RecipeEditorActionResult(
        status,
        CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION,
        message,
        recipe,
        next_ui_hint=hint,
    )


def _hint(status: str) -> str:
    if status == "success":
        return "The active session process context now references this recipe."
    return "Review the warning in the editor and choose a valid recipe file."

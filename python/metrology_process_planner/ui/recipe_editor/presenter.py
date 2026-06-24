"""Presenter for the recipe editor workflow surface."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.ui.recipe_editor.cards import (
    header_actions,
    layer_cards,
    material_cards,
    preview_model,
    step_cards,
    step_templates,
    summary_model,
)
from metrology_process_planner.ui.recipe_editor.validation_view import validation_messages
from metrology_process_planner.ui.recipe_editor.view_models import RecipeEditorViewModel
from metrology_process_planner.ui.shell import (
    MetadataFieldViewModel,
    SessionNavigatorItem,
    WarningViewModel,
)


class RecipeEditorPresenter:
    """Build recipe editor view models from process recipes."""

    def build(self, recipe: ProcessRecipe | None) -> RecipeEditorViewModel:
        """Return the recipe editor view model."""

        if recipe is None:
            return RecipeEditorViewModel(
                "",
                "No recipe loaded",
                (),
                (),
                (WarningViewModel("recipe-unloaded", "info", "No recipe is loaded."),),
                tabs=_tabs(),
                header_actions=header_actions(),
                preview=None,
            )
        metadata = dict(recipe.metadata or {})
        return RecipeEditorViewModel(
            recipe.id,
            recipe.name,
            _sections(recipe),
            (
                MetadataFieldViewModel("name", "Name", recipe.name, required=True),
                MetadataFieldViewModel("material_count", "Materials", str(len(recipe.materials))),
                MetadataFieldViewModel("step_count", "Steps", str(len(recipe.steps))),
            ),
            _warnings(recipe),
            dirty=bool(metadata.get("dirty", False)),
            tabs=_tabs(),
            header_actions=header_actions(),
            material_cards=material_cards(recipe),
            step_cards=step_cards(recipe),
            layer_cards=layer_cards(recipe),
            validation_messages=validation_messages(recipe),
            summary=summary_model(recipe),
            preview=preview_model(recipe),
            step_templates=step_templates(),
            selected_card_id=str(metadata.get("selected_card_id", "")),
        )


def _sections(recipe: ProcessRecipe) -> tuple[SessionNavigatorItem, ...]:
    return (
        SessionNavigatorItem("materials", "Materials", "recipe_section"),
        SessionNavigatorItem("steps", "Steps", "recipe_section"),
        SessionNavigatorItem("process_windows", "Process Windows", "recipe_section"),
        SessionNavigatorItem("summary", recipe.name, "recipe_summary"),
    )


def _tabs() -> tuple[str, ...]:
    return (
        "Materials",
        "Process Steps",
        "Layers / Masks",
        "Preview / Summary",
        "Validation",
    )


def _warnings(recipe: ProcessRecipe) -> tuple[WarningViewModel, ...]:
    return tuple(
        WarningViewModel(f"recipe-warning-{index}", "warning", warning)
        for index, warning in enumerate(recipe.validate(), start=1)
    )

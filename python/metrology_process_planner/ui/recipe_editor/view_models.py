"""Card-based recipe editor view models."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.ui.shell.view_models import (
    EditorActionViewModel,
    MetadataFieldViewModel,
    SessionNavigatorItem,
    WarningViewModel,
)


@dataclass(frozen=True)
class RecipeEditorViewModel:
    """View model for the recipe editor workflow window."""

    recipe_id: str
    title: str
    sections: tuple[SessionNavigatorItem, ...]
    fields: tuple[MetadataFieldViewModel, ...]
    validation_warnings: tuple[WarningViewModel, ...] = ()
    dirty: bool = False
    tabs: tuple[str, ...] = ()
    header_actions: tuple[EditorActionViewModel, ...] = ()
    material_actions: tuple[EditorActionViewModel, ...] = ()
    material_cards: tuple[RecipeMaterialCardViewModel, ...] = ()
    step_cards: tuple[RecipeStepCardViewModel, ...] = ()
    layer_cards: tuple[RecipeLayerCardViewModel, ...] = ()
    validation_messages: tuple[RecipeValidationMessageViewModel, ...] = ()
    summary: RecipeSummaryViewModel | None = None
    preview: RecipePreviewViewModel | None = None
    step_templates: tuple[EditorActionViewModel, ...] = ()
    selected_card_id: str = ""
    selected_detail: RecipeDetailPanelViewModel | None = None
    header: RecipeHeaderViewModel | None = None


@dataclass(frozen=True)
class RecipeHeaderViewModel:
    """Header/status model for the modeless recipe editor."""

    recipe_id: str
    recipe_name: str
    recipe_path: str = ""
    dirty: bool = False
    validation_status: str = "unloaded"
    warning_count: int = 0
    attachment_status: str = "not_loaded"
    status_text: str = "No recipe is loaded."


@dataclass(frozen=True)
class RecipeMaterialCardViewModel:
    """Card model for one process recipe material."""

    material_id: str
    name: str
    category: str
    color: str
    visible: bool
    used_by_step_count: int = 0
    warning_count: int = 0
    selected: bool = False
    dirty: bool = False


@dataclass(frozen=True)
class RecipeStepCardViewModel:
    """Card model for one ordered process step."""

    step_id: str
    step_number: int
    name: str
    operation_type: str
    enabled: bool
    material_label: str = ""
    layer_label: str = ""
    thickness_summary: str = ""
    plain_language_summary: str = ""
    warning_count: int = 0
    selected: bool = False
    dirty: bool = False


@dataclass(frozen=True)
class RecipeLayerCardViewModel:
    """Card model for one layer or mask reference used by a recipe."""

    layer_id: str
    label: str
    source: str
    layer: int
    datatype: int
    used_by_step_ids: tuple[str, ...] = ()
    warning_count: int = 0


@dataclass(frozen=True)
class RecipeValidationMessageViewModel:
    """Inline validation message tied to a material, step, or layer card."""

    message_id: str
    severity: str
    source: str
    message: str
    related_card_id: str = ""
    repair_suggestion: str = ""
    action_id: str = ""


@dataclass(frozen=True)
class RecipeSummaryViewModel:
    """Human-readable recipe summary for preview and review tabs."""

    lines: tuple[str, ...]
    material_count: int
    step_count: int
    unused_material_ids: tuple[str, ...] = ()
    disabled_step_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecipePreviewViewModel:
    """Recipe preview state when solver/render preview is not embedded."""

    status: str
    placeholder: str = ""
    selected_step_id: str = ""


@dataclass(frozen=True)
class RecipeDetailPanelViewModel:
    """Editable details for the selected material, step, or layer card."""

    card_id: str
    card_type: str
    title: str
    fields: tuple[MetadataFieldViewModel, ...]
    actions: tuple[EditorActionViewModel, ...] = ()
    warning_ids: tuple[str, ...] = ()
    summary: str = ""

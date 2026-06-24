"""Command catalog data for menu and modeless workflow actions."""

from __future__ import annotations

from metrology_process_planner.app.command_types import (
    CommandGroup,
    CommandId,
    CommandSpec,
    CoverageLane,
)

MENU_PATH = "tools_menu.metrology_process_planner"

_MENU_ROWS = (
    (
        CommandId.OPEN_SETUP_GUIDE,
        "mpp_start_or_resume_setup",
        "Start / Resume Measurement Setup",
        "Create or resume a guided setup and capture session.",
        CommandGroup.SETUP,
    ),
    (
        CommandId.OPEN_SESSION_EDITOR,
        "mpp_open_session_editor",
        "Session Editor",
        "Open the saved-session editor and repair surface.",
        CommandGroup.SESSION,
    ),
    (
        CommandId.OPEN_RECIPE_EDITOR,
        "mpp_edit_recipe",
        "Edit Recipe",
        "Open the process recipe editor.",
        CommandGroup.RECIPE,
    ),
    (
        CommandId.END_ACTIVE_SESSION,
        "mpp_end_active_session",
        "End Active Session",
        "Close the current workflow after saving or discarding pending state.",
        CommandGroup.SESSION,
    ),
    (
        CommandId.OPEN_DIAGNOSTICS,
        "mpp_open_diagnostics",
        "Advanced Diagnostics",
        "Open diagnostics for adapters, session artifacts, and exports.",
        CommandGroup.DIAGNOSTICS,
    ),
)

_WORKFLOW_ROWS = (
    (CommandId.START_CAPTURE, "Start Capture", CommandGroup.CAPTURE),
    (CommandId.START_BOX_CAPTURE, "Start Box Capture", CommandGroup.CAPTURE),
    (CommandId.START_LINE_CAPTURE, "Start Line Capture", CommandGroup.CAPTURE),
    (CommandId.START_POINT_CAPTURE, "Start Point Capture", CommandGroup.CAPTURE),
    (CommandId.CANCEL_CAPTURE, "Cancel Capture", CommandGroup.CAPTURE),
    (CommandId.SAVE_PENDING_CAPTURE, "Save Pending Capture", CommandGroup.CAPTURE),
    (CommandId.SAVE_COMPOSITE_CAPTURE, "Save Composite Capture", CommandGroup.CAPTURE),
    (CommandId.RETAKE_PENDING_CAPTURE, "Retake Pending Capture", CommandGroup.CAPTURE),
    (CommandId.RETAKE_PARENT_CAPTURE, "Retake Parent Capture", CommandGroup.CAPTURE),
    (CommandId.RETAKE_INNER_FEATURE, "Retake Inner Feature", CommandGroup.CAPTURE),
    (CommandId.DISCARD_PENDING_CAPTURE, "Discard Pending Capture", CommandGroup.CAPTURE),
    (CommandId.ADD_MEASUREMENT, "Add Measurement", CommandGroup.MEASUREMENT),
    (CommandId.SAVE_MEASUREMENT, "Save Measurement", CommandGroup.MEASUREMENT),
    (CommandId.RETAKE_MEASUREMENT_LINE, "Retake Measurement Line", CommandGroup.MEASUREMENT),
    (CommandId.DISCARD_MEASUREMENT, "Discard Measurement", CommandGroup.MEASUREMENT),
    (CommandId.TAKE_ANOTHER_MEASUREMENT, "Take Another Measurement", CommandGroup.MEASUREMENT),
    (CommandId.ATTACH_RECIPE, "Attach Recipe", CommandGroup.PROCESS),
    (CommandId.DETACH_RECIPE, "Detach Recipe", CommandGroup.PROCESS),
    (CommandId.VALIDATE_PROCESS_CONTEXT, "Validate Process Context", CommandGroup.PROCESS),
    (CommandId.REGENERATE_ARTIFACT, "Regenerate Artifact", CommandGroup.ARTIFACT),
    (CommandId.REGENERATE_PROCESS_OUTPUT, "Regenerate Process Output", CommandGroup.PROCESS),
    (CommandId.SAVE_SESSION_EDITS, "Save Session Edits", CommandGroup.SESSION),
    (CommandId.DISCARD_UNSAVED_EDITS, "Discard Unsaved Edits", CommandGroup.SESSION),
)

_SETUP_ROWS = (
    (CommandId.USE_GLOBAL_COORDINATES, "Use Global Coordinates"),
    (CommandId.USE_ORIGIN_COORDINATES, "Use Origin Coordinates"),
    (CommandId.START_ORIGIN_POINT_CAPTURE, "Start Origin Point Capture"),
    (CommandId.START_ORIGIN_REFERENCE_CAPTURE, "Start Origin Reference Capture"),
    (CommandId.START_ALIGNMENT_CAPTURE, "Start Alignment Capture"),
    (CommandId.START_SEM_ALIGNMENT_CAPTURE, "Start SEM Alignment Capture"),
    (CommandId.SKIP_OPTIONAL_SETUP_STAGE, "Skip Optional Setup Stage"),
    (CommandId.VALIDATE_RECIPE_CONTEXT, "Validate Recipe Context"),
    (CommandId.MARK_SETUP_COMPLETE, "Mark Setup Complete"),
    (CommandId.RETURN_TO_EDITOR, "Return to Editor"),
    (CommandId.CLOSE_SETUP_GUIDE, "Close Setup Guide"),
)

_RECIPE_ROWS = (
    (CommandId.NEW_RECIPE, "New Recipe"),
    (CommandId.OPEN_RECIPE, "Open Recipe"),
    (CommandId.SAVE_RECIPE, "Save Recipe"),
    (CommandId.SAVE_RECIPE_AS, "Save Recipe As"),
    (CommandId.VALIDATE_RECIPE, "Validate Recipe"),
    (CommandId.ADD_MATERIAL, "Add Material"),
    (CommandId.DUPLICATE_MATERIAL, "Duplicate Material"),
    (CommandId.DELETE_MATERIAL, "Delete Material"),
    (CommandId.TOGGLE_MATERIAL_VISIBILITY, "Toggle Material Visibility"),
    (CommandId.FIND_MATERIAL_USAGE, "Find Material Usage"),
    (CommandId.EDIT_MATERIAL, "Edit Material"),
    (CommandId.ADD_PROCESS_STEP, "Add Process Step"),
    (CommandId.DUPLICATE_PROCESS_STEP, "Duplicate Process Step"),
    (CommandId.DELETE_PROCESS_STEP, "Delete Process Step"),
    (CommandId.MOVE_PROCESS_STEP_UP, "Move Process Step Up"),
    (CommandId.MOVE_PROCESS_STEP_DOWN, "Move Process Step Down"),
    (CommandId.ENABLE_PROCESS_STEP, "Enable Process Step"),
    (CommandId.DISABLE_PROCESS_STEP, "Disable Process Step"),
    (CommandId.EDIT_PROCESS_STEP, "Edit Process Step"),
    (CommandId.SELECT_LAYER_REFERENCE, "Select Layer Reference"),
    (CommandId.PREVIEW_RECIPE, "Preview Recipe"),
    (CommandId.PREVIEW_RECIPE_THROUGH_STEP, "Preview Recipe Through Step"),
    (CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION, "Attach Recipe to Active Session"),
    (CommandId.CLOSE_RECIPE_EDITOR, "Close Recipe Editor"),
)


def _menu_spec(
    command_id: CommandId,
    menu_item_name: str,
    title: str,
    description: str,
    group: CommandGroup,
) -> CommandSpec:
    return CommandSpec(
        command_id,
        title,
        description,
        group,
        CoverageLane.KLAYOUT_UI,
        menu_item_name,
        MENU_PATH,
    )


def _workflow_spec(command_id: CommandId, title: str, group: CommandGroup) -> CommandSpec:
    return CommandSpec(command_id, title, f"{title}.", group)


ALL_COMMANDS: tuple[CommandSpec, ...] = (
    *tuple(_menu_spec(*row) for row in _MENU_ROWS),
    *tuple(_workflow_spec(*row) for row in _WORKFLOW_ROWS),
    *tuple(
        _workflow_spec(command_id, title, CommandGroup.SETUP)
        for command_id, title in _SETUP_ROWS
    ),
    *tuple(
        _workflow_spec(command_id, title, CommandGroup.RECIPE)
        for command_id, title in _RECIPE_ROWS
    ),
)

MENU_COMMANDS: tuple[CommandSpec, ...] = tuple(
    spec for spec in ALL_COMMANDS if spec.appears_in_menu
)

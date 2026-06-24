"""Action view models shared by recipe editor cards and details."""

from __future__ import annotations

from metrology_process_planner.ui.shell.view_models import EditorActionViewModel


def material_card_actions(material_id: str) -> tuple[EditorActionViewModel, ...]:
    """Return modeless card actions for a material."""

    return (
        _action(
            f"DuplicateMaterial:{material_id}",
            "Duplicate Material",
            f"material:{material_id}",
        ),
        _action(f"DeleteMaterial:{material_id}", "Delete Material", f"material:{material_id}"),
        _action(
            f"ToggleMaterialVisibility:{material_id}",
            "Toggle Visibility",
            f"material:{material_id}",
        ),
        _action(f"FindMaterialUsage:{material_id}", "Find Usage", f"material:{material_id}"),
    )


def process_step_card_actions(
    step_id: str,
    enabled: bool,
) -> tuple[EditorActionViewModel, ...]:
    """Return modeless card actions for a process step."""

    toggle = (
        _action(f"DisableProcessStep:{step_id}", "Disable Step", f"step:{step_id}")
        if enabled
        else _action(f"EnableProcessStep:{step_id}", "Enable Step", f"step:{step_id}")
    )
    return (
        _action(f"DuplicateProcessStep:{step_id}", "Duplicate Step", f"step:{step_id}"),
        _action(f"DeleteProcessStep:{step_id}", "Delete Step", f"step:{step_id}"),
        _action(f"MoveProcessStepUp:{step_id}", "Move Up", f"step:{step_id}"),
        _action(f"MoveProcessStepDown:{step_id}", "Move Down", f"step:{step_id}"),
        toggle,
        _action(
            f"PreviewRecipeThroughStep:{step_id}",
            "Preview Through This Step",
            f"step:{step_id}",
        ),
    )


def _action(action_id: str, label: str, target: str) -> EditorActionViewModel:
    return EditorActionViewModel(action_id, label, target)

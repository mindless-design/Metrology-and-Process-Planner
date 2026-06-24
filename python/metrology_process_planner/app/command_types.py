"""Typed command identifiers and metadata records."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class CommandId(str, Enum):
    """Stable identifiers for user-facing plugin command intents."""

    OPEN_SESSION_EDITOR = "open_session_editor"
    OPEN_SETUP_GUIDE = "open_setup_guide"
    OPEN_RECIPE_EDITOR = "open_recipe_editor"
    OPEN_DIAGNOSTICS = "open_diagnostics"
    START_CAPTURE = "start_capture"
    START_BOX_CAPTURE = "start_box_capture"
    START_LINE_CAPTURE = "start_line_capture"
    START_POINT_CAPTURE = "start_point_capture"
    CANCEL_CAPTURE = "cancel_capture"
    SAVE_PENDING_CAPTURE = "save_pending_capture"
    SAVE_COMPOSITE_CAPTURE = "save_composite_capture"
    RETAKE_PENDING_CAPTURE = "retake_pending_capture"
    RETAKE_PARENT_CAPTURE = "retake_parent_capture"
    RETAKE_INNER_FEATURE = "retake_inner_feature"
    DISCARD_PENDING_CAPTURE = "discard_pending_capture"
    ADD_MEASUREMENT = "add_measurement"
    SAVE_MEASUREMENT = "save_measurement"
    RETAKE_MEASUREMENT_LINE = "retake_measurement_line"
    DISCARD_MEASUREMENT = "discard_measurement"
    TAKE_ANOTHER_MEASUREMENT = "take_another_measurement"
    ATTACH_RECIPE = "attach_recipe"
    DETACH_RECIPE = "detach_recipe"
    VALIDATE_PROCESS_CONTEXT = "validate_process_context"
    REGENERATE_ARTIFACT = "regenerate_artifact"
    REGENERATE_PROCESS_OUTPUT = "regenerate_process_output"
    SAVE_SESSION_EDITS = "save_session_edits"
    DISCARD_UNSAVED_EDITS = "discard_unsaved_edits"
    END_ACTIVE_SESSION = "end_active_session"
    USE_GLOBAL_COORDINATES = "use_global_coordinates"
    USE_ORIGIN_COORDINATES = "use_origin_coordinates"
    START_ORIGIN_POINT_CAPTURE = "start_origin_point_capture"
    START_ORIGIN_REFERENCE_CAPTURE = "start_origin_reference_capture"
    START_ALIGNMENT_CAPTURE = "start_alignment_capture"
    START_SEM_ALIGNMENT_CAPTURE = "start_sem_alignment_capture"
    SKIP_OPTIONAL_SETUP_STAGE = "skip_optional_setup_stage"
    VALIDATE_RECIPE_CONTEXT = "validate_recipe_context"
    MARK_SETUP_COMPLETE = "mark_setup_complete"
    RETURN_TO_EDITOR = "return_to_editor"
    CLOSE_SETUP_GUIDE = "close_setup_guide"
    NEW_RECIPE = "new_recipe"
    OPEN_RECIPE = "open_recipe"
    SAVE_RECIPE = "save_recipe"
    SAVE_RECIPE_AS = "save_recipe_as"
    VALIDATE_RECIPE = "validate_recipe"
    ADD_MATERIAL = "add_material"
    DUPLICATE_MATERIAL = "duplicate_material"
    DELETE_MATERIAL = "delete_material"
    EDIT_MATERIAL = "edit_material"
    ADD_PROCESS_STEP = "add_process_step"
    DUPLICATE_PROCESS_STEP = "duplicate_process_step"
    DELETE_PROCESS_STEP = "delete_process_step"
    MOVE_PROCESS_STEP_UP = "move_process_step_up"
    MOVE_PROCESS_STEP_DOWN = "move_process_step_down"
    ENABLE_PROCESS_STEP = "enable_process_step"
    DISABLE_PROCESS_STEP = "disable_process_step"
    EDIT_PROCESS_STEP = "edit_process_step"
    SELECT_LAYER_REFERENCE = "select_layer_reference"
    PREVIEW_RECIPE = "preview_recipe"
    PREVIEW_RECIPE_THROUGH_STEP = "preview_recipe_through_step"
    ATTACH_RECIPE_TO_ACTIVE_SESSION = "attach_recipe_to_active_session"
    CLOSE_RECIPE_EDITOR = "close_recipe_editor"


class CommandGroup(str, Enum):
    """Top-level product area for command coverage tracking."""

    SESSION = "session"
    SETUP = "setup"
    CAPTURE = "capture"
    MEASUREMENT = "measurement"
    RECIPE = "recipe"
    PROCESS = "process"
    ARTIFACT = "artifact"
    DIAGNOSTICS = "diagnostics"


class CoverageLane(str, Enum):
    """Expected test lane for a command entrypoint."""

    UNIT = "unit"
    KLAYOUT_BATCH = "klayout_batch"
    KLAYOUT_UI = "klayout_ui"


CommandHandler = Callable[[], None]


@dataclass(frozen=True)
class CommandSpec:
    """Metadata for a command intent and optional KLayout menu entry."""

    command_id: CommandId
    title: str
    description: str
    group: CommandGroup
    coverage_lane: CoverageLane = CoverageLane.UNIT
    menu_item_name: str = ""
    menu_path: str = ""

    @property
    def appears_in_menu(self) -> bool:
        """Return whether this command should be installed in KLayout menus."""

        return bool(self.menu_item_name and self.menu_path)

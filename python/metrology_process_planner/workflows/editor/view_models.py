"""Preview, metadata, warning, and action view models for the editor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EditorActionType(str, Enum):
    """Action identifiers dispatched by the unified session editor."""

    SAVE_EDITS = "save_edits"
    EXPORT_CSV = "export_csv"
    SELECT_ITEM = "select_item"
    SELECT_CANVAS_OBJECT = "select_canvas_object"
    PENDING_SAVE = "pending_save"
    PENDING_RETAKE = "pending_retake"
    PENDING_DISCARD = "pending_discard"
    COMPOSITE_SAVE = "composite_save"
    COMPOSITE_RETAKE_PARENT = "composite_retake_parent"
    COMPOSITE_RETAKE_INNER = "composite_retake_inner"
    COMPOSITE_DISCARD = "composite_discard"
    COMPOSITE_EXIT = "composite_exit"
    EXIT_SESSION = "exit_session"
    ADD_MEASUREMENT = "add_measurement"
    SAVE_MEASUREMENT = "save_measurement"
    RETAKE_MEASUREMENT_LINE = "retake_measurement_line"
    DISCARD_MEASUREMENT = "discard_measurement"
    TAKE_MEASUREMENT = "take_measurement"
    BUILD_POWERPOINT = "build_powerpoint"
    REOPEN_SETUP = "reopen_setup"
    REGENERATE_ARTIFACT = "regenerate_artifact"
    OPEN_OUTPUT_FOLDER = "open_output_folder"
    OPEN_RECIPE_FILE = "open_recipe_file"
    ATTACH_RECIPE = "attach_recipe"
    DETACH_RECIPE = "detach_recipe"
    REFRESH_RECIPE_FINGERPRINT = "refresh_recipe_fingerprint"
    VALIDATE_PROCESS_CONTEXT = "validate_process_context"
    REGENERATE_PROCESS_OUTPUT = "regenerate_process_output"
    IGNORE_WARNING = "ignore_warning"
    REPLACE_SITE_BOX = "replace_site_box"
    REPLACE_INNER_FEATURE = "replace_inner_feature"


@dataclass(frozen=True)
class PreviewOption:
    """One preview candidate for the selected editor item."""

    role: str
    label: str
    artifact_path: str = ""
    placeholder: str = ""
    status: str = "available"
    repair_action: str = ""


@dataclass(frozen=True)
class MetadataField:
    """Editable or read-only metadata field shown by the inspector."""

    key: str
    label: str
    value: str = ""
    required: bool = False
    read_only: bool = False
    warning: str = ""


@dataclass(frozen=True)
class EditorAction:
    """A user action available for the selected editor item."""

    action_type: EditorActionType
    label: str
    item_id: str = ""
    payload: tuple[tuple[str, str], ...] = ()
    enabled: bool = True


@dataclass(frozen=True)
class WarningViewModel:
    """Editor-visible warning with optional artifact and item links."""

    warning_id: str
    message: str
    severity: str = "warning"
    item_id: str = ""
    artifact_path: str = ""

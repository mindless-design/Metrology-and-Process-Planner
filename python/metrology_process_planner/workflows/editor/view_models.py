"""Preview, metadata, warning, and action view models for the editor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EditorActionType(str, Enum):
    """Action identifiers dispatched by the unified session editor."""

    SAVE_EDITS = "save_edits"
    EDIT_METADATA = "edit_metadata"
    UPDATE_METADATA_FIELD = "update_metadata_field"
    ADD_CAPTURE = "add_capture"
    CANCEL_CAPTURE = "cancel_capture"
    BATCH_RENAME = "batch_rename"
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
    TAKE_ANOTHER_MEASUREMENT = "take_another_measurement"
    RETURN_TO_EDITOR = "return_to_editor"
    DONE = "done"
    RETAKE_MEASUREMENT_LINE = "retake_measurement_line"
    DISCARD_MEASUREMENT = "discard_measurement"
    BUILD_POWERPOINT = "build_powerpoint"
    GENERATE_SESSION_OVERVIEW = "generate_session_overview"
    GENERATE_METROLOGY_OVERVIEW = "generate_metrology_overview"
    GENERATE_GRID_OVERVIEW = "generate_grid_overview"
    CREATE_GRID_DATASET = "create_grid_dataset"
    REGENERATE_OVERVIEW = "regenerate_overview"
    ADD_USER_LABEL = "add_user_label"
    REOPEN_SETUP = "reopen_setup"
    REGENERATE_ARTIFACT = "regenerate_artifact"
    SCAN_ARTIFACTS = "scan_artifacts"
    REGENERATE_MISSING_ARTIFACTS = "regenerate_missing_artifacts"
    REGENERATE_STALE_ARTIFACTS = "regenerate_stale_artifacts"
    RELINK_ARTIFACT = "relink_artifact"
    EXPORT_ARTIFACT_MANIFEST = "export_artifact_manifest"
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
    COPY_CENTER_COORDINATE = "copy_center_coordinate"
    COPY_BOUNDS = "copy_bounds"
    COPY_CSV_ROW = "copy_csv_row"


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
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class EditorAction:
    """A user action available for the selected editor item."""

    action_type: EditorActionType
    label: str
    item_id: str = ""
    payload: tuple[tuple[str, str], ...] = ()
    enabled: bool = True
    disabled_reason: str = ""


@dataclass(frozen=True)
class WarningViewModel:
    """Editor-visible warning with optional artifact and item links."""

    warning_id: str
    message: str
    severity: str = "warning"
    item_id: str = ""
    artifact_path: str = ""


@dataclass(frozen=True)
class ArtifactHealthViewModel:
    """Dashboard summary for canonical artifact health."""

    present: int = 0
    missing: int = 0
    stale: int = 0
    failed: int = 0
    placeholder: int = 0
    pending: int = 0
    external: int = 0
    superseded: int = 0
    intentionally_ignored: int = 0


@dataclass(frozen=True)
class ArtifactDetailViewModel:
    """Inspector row for one artifact owned by the selected item."""

    artifact_id: str
    label: str
    artifact_type: str
    status: str
    path: str
    generator: str = ""
    generated_at: str = ""
    dependency_count: int = 0
    repair_available: bool = False
    warning_ids: tuple[str, ...] = ()

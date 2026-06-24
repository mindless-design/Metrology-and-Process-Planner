"""Reusable UI view models for KLayout-facing surfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SetupStageViewModel:
    """One row in the modeless setup guide."""

    stage_id: str
    label: str
    status: str = "pending"
    next_action: str = ""
    stage_type: str = ""
    required: bool = True
    description: str = ""
    primary_action: str = ""
    secondary_actions: tuple[str, ...] = ()
    disabled_reason: str = ""
    warning_count: int = 0


@dataclass(frozen=True)
class SetupGuideViewModel:
    """Compact workflow state for the modeless setup guide."""

    session_name: str
    active_stage_id: str
    stages: tuple[SetupStageViewModel, ...]
    available_commands: tuple[str, ...]
    status: str = "ready"
    mode_display_name: str = ""
    current_stage_label: str = ""
    next_action: str = ""
    warning_count: int = 0


@dataclass(frozen=True)
class SessionNavigatorItem:
    """Flat navigator item rendered by the generic editor shell."""

    item_id: str
    label: str
    kind: str
    status: str = "ready"
    parent_id: str = ""
    warning_count: int = 0


@dataclass(frozen=True)
class PreviewModel:
    """Artifact preview model consumed by reusable preview widgets."""

    role: str
    label: str
    artifact_id: str = ""
    artifact_path: str = ""
    status: str = "available"
    placeholder: str = ""
    warning_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class MetadataFieldViewModel:
    """Inspector metadata field rendered by editor or review panels."""

    key: str
    label: str
    value: str
    required: bool = False
    read_only: bool = False


@dataclass(frozen=True)
class EditorActionViewModel:
    """Command/action button model emitted as an intent by UI widgets."""

    action_id: str
    label: str
    target_item_id: str = ""
    enabled: bool = True
    status: str = "available"


@dataclass(frozen=True)
class PendingCaptureViewModel:
    """Pending capture review view model shown inside the session editor."""

    pending_id: str
    label: str
    preview: PreviewModel
    metadata_fields: tuple[MetadataFieldViewModel, ...]
    actions: tuple[EditorActionViewModel, ...]


@dataclass(frozen=True)
class WarningViewModel:
    """Shared warning row for status strips and diagnostics surfaces."""

    warning_id: str
    severity: str
    message: str
    repair_suggestion: str = ""
    status: str = "open"


@dataclass(frozen=True)
class SessionEditorViewModel:
    """Generic document/view model consumed by the unified session editor shell."""

    session_name: str
    selected_item_id: str
    navigator_items: tuple[SessionNavigatorItem, ...]
    previews: tuple[PreviewModel, ...]
    metadata_fields: tuple[MetadataFieldViewModel, ...]
    actions: tuple[EditorActionViewModel, ...]
    warnings: tuple[WarningViewModel, ...]
    dirty: bool = False


@dataclass(frozen=True)
class CaptureToolStatusViewModel:
    """Current status of an armed or idle canvas capture tool."""

    tool_id: str
    primitive: str
    armed: bool
    gesture_hint: str
    active_parent_id: str = ""
    message: str = ""

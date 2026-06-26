"""Unified session editor document, adapter, and action contracts."""

from metrology_process_planner.workflows.editor.adapters import (
    DefaultSessionModeAdapter,
    SessionModeAdapter,
)
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import (
    DirtyState,
    EditorSelectionState,
    SessionDocument,
    SessionItem,
    SessionItemGroup,
    SessionItemKind,
)
from metrology_process_planner.workflows.editor.editing import (
    apply_metadata_edits,
    mark_clean,
    mark_metadata_edit,
    mark_pending_dirty,
    select_canvas_object,
    select_item,
)
from metrology_process_planner.workflows.editor.references import ArtifactRef, RecordRef
from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge
from metrology_process_planner.workflows.editor.render_bridge_models import (
    CrossSectionRenderInput,
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderRefreshResult,
    RenderTarget,
)
from metrology_process_planner.workflows.editor.store import (
    NewSessionRequest,
    RecentSessionRegistry,
    SessionDocumentLoader,
    SessionDocumentStore,
    SessionDocumentWriter,
    SessionMigrationService,
    SessionStore,
    SessionValidationService,
)
from metrology_process_planner.workflows.editor.view_models import (
    ArtifactDetailViewModel,
    ArtifactHealthViewModel,
    EditorAction,
    EditorActionType,
    MetadataField,
    PreviewOption,
    WarningViewModel,
)

__all__ = [
    "ArtifactRef",
    "ArtifactDetailViewModel",
    "ArtifactHealthViewModel",
    "CrossSectionRenderInput",
    "DefaultSessionModeAdapter",
    "DirtyState",
    "DrawingOwnerRef",
    "EditorAction",
    "EditorActionDispatcher",
    "EditorActionResult",
    "EditorActionType",
    "EditorSelectionState",
    "MetadataField",
    "PreviewOption",
    "RecordRef",
    "RenderRefreshRequest",
    "RenderRefreshResult",
    "RenderTarget",
    "NewSessionRequest",
    "RecentSessionRegistry",
    "SessionDocument",
    "SessionDocumentBuilder",
    "SessionDocumentLoader",
    "SessionDocumentStore",
    "SessionDocumentWriter",
    "SessionItem",
    "SessionItemGroup",
    "SessionItemKind",
    "SessionMigrationService",
    "SessionModeAdapter",
    "SessionRenderBridge",
    "SessionStore",
    "SessionValidationService",
    "WarningViewModel",
    "apply_metadata_edits",
    "mark_clean",
    "mark_metadata_edit",
    "mark_pending_dirty",
    "select_canvas_object",
    "select_item",
]

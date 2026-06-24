"""Workflow state machines and user intent contracts."""

from metrology_process_planner.workflows.canvas_interaction import CanvasInteractionEngine
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.compound_capture import (
    CompoundCaptureRequest,
    SaveCompositeCaptureCommand,
    add_line_feature,
    add_point_feature,
    arm_inner_feature_capture,
    begin_compound_capture,
    ellipsometry_request,
    profilometry_request,
    save_composite_capture,
)
from metrology_process_planner.workflows.compound_capture_models import (
    CompositeReviewIntent,
    CompoundCaptureState,
    DiscardCompositeCommand,
    ExitCompositeCommand,
    RetakeInnerFeatureCommand,
    RetakeParentCommand,
)
from metrology_process_planner.workflows.compound_capture_review import (
    discard_composite_capture,
    exit_composite_capture,
    retake_inner_feature,
    retake_parent_capture,
)
from metrology_process_planner.workflows.measurement_completion import (
    MeasurementCompletionChoice,
    MeasurementCompletionResult,
    PostActionPrompt,
    apply_measurement_completion_choice,
    measurement_completion_prompt,
)
from metrology_process_planner.workflows.measurement_review import (
    discard_pending_measurement,
    retake_pending_measurement_line,
)
from metrology_process_planner.workflows.overlays import (
    CanvasOverlayBackend,
    CanvasOverlayManager,
    OverlayCommand,
    OverlayCommandKind,
)
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService
from metrology_process_planner.workflows.process_context import (
    attach_recipe,
    detach_recipe,
    refresh_recipe_fingerprint,
    regenerate_process_outputs,
    validate_process_context,
)
from metrology_process_planner.workflows.process_context_models import (
    AttachRecipeCommand,
    DetachRecipeCommand,
    RefreshRecipeFingerprintCommand,
    RegenerateProcessOutputsCommand,
    ValidateProcessContextCommand,
)
from metrology_process_planner.workflows.recipe_editor_actions import (
    RecipeEditorActionDispatcher,
)
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult
from metrology_process_planner.workflows.selection import (
    EditorSelectionSink,
    SelectionCoordinator,
    SelectionSyncResult,
)
from metrology_process_planner.workflows.ui_state_machines import (
    ArtifactRepairStateMachine,
    CaptureInteractionStateMachine,
    MeasurementWorkflowStateMachine,
    PendingReviewStateMachine,
    RecipeContextStateMachine,
    SessionUIStateMachine,
    UiStateSnapshot,
)

__all__ = [
    "ArtifactRepairStateMachine",
    "CanvasInteractionEngine",
    "CanvasOverlayBackend",
    "CanvasOverlayManager",
    "CaptureInteractionStateMachine",
    "CompositeReviewIntent",
    "CompoundCaptureState",
    "CompoundCaptureRequest",
    "DiscardCompositeCommand",
    "EditorSelectionSink",
    "ExitCompositeCommand",
    "InteractionContext",
    "InteractionResult",
    "MeasurementCompletionChoice",
    "MeasurementCompletionResult",
    "MeasurementWorkflowStateMachine",
    "OverlayCommand",
    "OverlayCommandKind",
    "PendingCaptureReviewService",
    "PendingReviewStateMachine",
    "PostActionPrompt",
    "RecipeContextStateMachine",
    "RecipeEditorActionDispatcher",
    "RecipeEditorActionResult",
    "AttachRecipeCommand",
    "DetachRecipeCommand",
    "RefreshRecipeFingerprintCommand",
    "RegenerateProcessOutputsCommand",
    "RetakeInnerFeatureCommand",
    "RetakeParentCommand",
    "SaveCompositeCaptureCommand",
    "SelectionCoordinator",
    "SelectionSyncResult",
    "SessionUIStateMachine",
    "UiStateSnapshot",
    "ValidateProcessContextCommand",
    "add_line_feature",
    "add_point_feature",
    "apply_measurement_completion_choice",
    "arm_inner_feature_capture",
    "attach_recipe",
    "begin_compound_capture",
    "discard_composite_capture",
    "discard_pending_measurement",
    "detach_recipe",
    "ellipsometry_request",
    "exit_composite_capture",
    "measurement_completion_prompt",
    "profilometry_request",
    "refresh_recipe_fingerprint",
    "regenerate_process_outputs",
    "retake_inner_feature",
    "retake_pending_measurement_line",
    "retake_parent_capture",
    "save_composite_capture",
    "validate_process_context",
]

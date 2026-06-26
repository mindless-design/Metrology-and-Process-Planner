"""Process-context action dispatch helpers."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.persistence.process_output_store import ProcessOutputStore
from metrology_process_planner.workflows.editor.adapter_process_outputs import (
    capture_id_for_process_output,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import (
    _payload_value,
    _record_id,
)
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction
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
    ProcessContextResult,
    RefreshRecipeFingerprintCommand,
    RegenerateProcessOutputsCommand,
    ValidateProcessContextCommand,
)
from metrology_process_planner.workflows.process_context_support import (
    process_warning,
    with_warnings,
)


class _DocumentRebuilder(Protocol):
    """Editor dispatcher capability needed by process-context actions."""

    _mode_registry: ModeRegistry | None

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after a workflow mutation."""


class _ProcessOutputExporter(_DocumentRebuilder, Protocol):
    """Dispatcher capability needed to persist generated process outputs."""

    _paths: SessionPaths | None
    _process_output_store: ProcessOutputStore


def attach_recipe_action(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Dispatch an attach-recipe action from an explicit payload path."""

    unavailable = _non_process_unavailable(dispatcher, document)
    if unavailable is not None:
        return unavailable
    recipe_path = _payload_value(action, "recipe_path")
    if not recipe_path:
        return EditorActionResult("unavailable", document, "No recipe path was provided.")
    return process_result(
        dispatcher,
        document,
        attach_recipe(document.session, AttachRecipeCommand(recipe_path)),
    )


def detach_recipe_action(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
) -> EditorActionResult:
    """Dispatch detach recipe."""

    unavailable = _non_process_unavailable(dispatcher, document)
    if unavailable is not None:
        return unavailable
    return process_result(
        dispatcher,
        document,
        detach_recipe(document.session, DetachRecipeCommand()),
    )


def refresh_recipe_fingerprint_action(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
) -> EditorActionResult:
    """Dispatch recipe fingerprint refresh."""

    unavailable = _non_process_unavailable(dispatcher, document)
    if unavailable is not None:
        return unavailable
    return process_result(
        dispatcher,
        document,
        refresh_recipe_fingerprint(document.session, RefreshRecipeFingerprintCommand()),
    )


def validate_process_context_action(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
) -> EditorActionResult:
    """Dispatch process-context validation."""

    unavailable = _non_process_unavailable(dispatcher, document)
    if unavailable is not None:
        return unavailable
    return process_result(
        dispatcher,
        document,
        validate_process_context(document.session, ValidateProcessContextCommand()),
    )


def regenerate_process_output_action(
    dispatcher: _ProcessOutputExporter,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Dispatch process-output regeneration."""

    unavailable = _non_process_unavailable(dispatcher, document)
    if unavailable is not None:
        return unavailable
    owner_id = _process_output_owner_id(document, action)
    result = regenerate_process_outputs(
        document.session,
        RegenerateProcessOutputsCommand(owner_id),
    )
    if result.status == "success" and dispatcher._paths is not None:
        result = _export_process_outputs(dispatcher, dispatcher._paths, result, owner_id)
    return process_result(dispatcher, document, result)


def _process_output_owner_id(document: SessionDocument, action: EditorAction) -> str:
    item = document.items_by_id.get(action.item_id)
    record_id = _record_id(document, action.item_id)
    if item is None or item.record_ref is None:
        return record_id
    if item.record_ref.record_type == "process_output":
        return capture_id_for_process_output(document.session, record_id)
    return record_id


def _export_process_outputs(
    dispatcher: _ProcessOutputExporter,
    paths: SessionPaths,
    result: ProcessContextResult,
    owner_id: str,
) -> ProcessContextResult:
    try:
        session = dispatcher._process_output_store.export_ready_outputs(
            paths,
            result.session,
            owner_id,
        )
    except OSError as exc:
        warning = process_warning(
            "PROCESS_OUTPUT_REGENERATION_FAILED",
            f"Process output artifact export failed: {exc}",
            "Check the session folder permissions and regenerate process outputs.",
            owner_id,
        )
        return with_warnings(result.session, (warning,), "warning", "Process output export failed.")
    return ProcessContextResult(
        session,
        result.warnings,
        result.status,
        "Regenerated and exported process outputs.",
    )


def process_result(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
    result: ProcessContextResult,
) -> EditorActionResult:
    """Convert a process-context result into an editor action result."""

    return EditorActionResult(
        result.status,
        dispatcher._rebuild(result.session, document),
        result.message,
    )


def _non_process_unavailable(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
) -> EditorActionResult | None:
    from metrology_process_planner.workflows.editor.builder_basics import (
        mode_is_process_aware,
    )

    if mode_is_process_aware(document.session, getattr(dispatcher, "_mode_registry", None)):
        return None
    return EditorActionResult(
        "unavailable",
        document,
        "Process context actions are not available for this recipe-free mode.",
    )

"""Dashboard metadata fields for the default editor adapter."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.domains.warnings.warning_visibility import session_is_process_aware
from metrology_process_planner.workflows.editor.adapter_dashboard_process import (
    open_process_warnings,
    process_output_status_counts,
    recipe_status,
    solver_status,
)
from metrology_process_planner.workflows.editor.adapter_dashboard_readiness import (
    artifact_attention_count,
    csv_readiness_for_dashboard,
    missing_artifact_count_for_dashboard,
    report_readiness_for_dashboard,
)
from metrology_process_planner.workflows.editor.view_models import MetadataField
from metrology_process_planner.workflows.editor.warning_visibility import (
    editor_visible_warning_count,
)
from metrology_process_planner.workflows.setup_guide_requirements import (
    incomplete_required_setup_labels,
)


def dashboard_fields(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return dashboard metadata fields."""

    if not _mode_is_process_aware(session, mode_registry):
        return _non_process_dashboard_fields(session, mode_registry)
    context = session.process_context
    return (
        MetadataField("session_name", "Session", session.name),
        MetadataField("process_recipe", "Recipe", recipe_status(session), read_only=True),
        MetadataField("process_solver", "Solver", solver_status(session), read_only=True),
        MetadataField("render_profile", "Render Profile", context.render_profile or "default"),
        MetadataField(
            "process_outputs",
            "Process Outputs",
            process_output_status_counts(session),
            read_only=True,
        ),
        MetadataField(
            "process_warning_count",
            "Process Warnings",
            str(len(open_process_warnings(session))),
        ),
    )


def _non_process_dashboard_fields(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[MetadataField, ...]:
    fields = list(_base_non_process_dashboard_fields(session, mode_registry))
    batch_status = _batch_status(session, mode_registry)
    if batch_status:
        fields.insert(
            4,
            MetadataField("batch_status", "Batch Status", batch_status, read_only=True),
        )
    return tuple(fields)


def _base_non_process_dashboard_fields(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[MetadataField, ...]:
    measurement_count = sum(len(capture.measurements) for capture in session.captures)
    return (
        MetadataField("session_name", "Session", session.name),
        MetadataField("mode", "Mode", session.mode.value, read_only=True),
        MetadataField(
            "output_folder", "Output Folder", session.paths.artifact_root, read_only=True
        ),
        MetadataField(
            "setup_status",
            "Setup Status",
            _setup_status(session, mode_registry),
            read_only=True,
        ),
        MetadataField("capture_count", "Capture Count", str(len(session.captures)), read_only=True),
        MetadataField(
            "measurement_count", "Measurement Count", str(measurement_count), read_only=True
        ),
        MetadataField(
            "missing_artifact_count",
            "Missing Artifact Count",
            str(missing_artifact_count_for_dashboard(session, mode_registry)),
            read_only=True,
        ),
        MetadataField(
            "artifact_attention_count",
            "Artifact Attention Count",
            str(artifact_attention_count(session, mode_registry)),
            read_only=True,
        ),
        _warning_count_field(session, mode_registry),
        *_readiness_fields(session, mode_registry),
        MetadataField("last_modified", "Last Modified", session.updated_at, read_only=True),
    )


def _warning_count_field(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> MetadataField:
    return MetadataField(
        "warning_count",
        "Warning Count",
        str(editor_visible_warning_count(session, mode_registry)),
        read_only=True,
    )


def _readiness_fields(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[MetadataField, ...]:
    return (
        MetadataField(
            "csv_readiness",
            "CSV Readiness",
            csv_readiness_for_dashboard(session, mode_registry),
            read_only=True,
        ),
        MetadataField(
            "report_readiness",
            "Report Readiness",
            report_readiness_for_dashboard(session, mode_registry),
            read_only=True,
        ),
    )


def _setup_status(session: SessionRecord, mode_registry: ModeRegistry | None) -> str:
    definition = _definition(session, mode_registry)
    if not definition.capabilities.uses_setup_guide:
        return "not required"
    if session.setup.is_capture_ready and not incomplete_required_setup_labels(session, definition):
        return "ready"
    return "incomplete"


def _batch_status(session: SessionRecord, mode_registry: ModeRegistry | None) -> str:
    definition = _definition(session, mode_registry)
    if not definition.capabilities.supports_batch_capture:
        return ""
    state = "capturing" if session.workflow.active else "ready"
    return f"{state}, {len(session.captures)} saved, {len(session.pending_captures)} pending"


def _definition(session: SessionRecord, mode_registry: ModeRegistry | None) -> ModeDefinition:
    return (mode_registry or built_in_mode_registry()).definition(session.mode.value)


def _mode_is_process_aware(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    if mode_registry is None:
        return session_is_process_aware(session)
    mode = mode_registry.definition(session.mode.value)
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
    )


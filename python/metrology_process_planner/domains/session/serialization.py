"""Canonical session JSON serialization and migration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any, cast

from metrology_process_planner.domains.session.canonical import (
    CoordinateContext,
    SchemaRecord,
    SessionIdentity,
    SessionPathsRecord,
    SourceLayoutContext,
)
from metrology_process_planner.domains.session.canvas import CanvasObject, PendingCapture
from metrology_process_planner.domains.session.captures import CaptureRecord
from metrology_process_planner.domains.session.constants import (
    LEGACY_SESSION_SCHEMA_VERSION,
    SESSION_SCHEMA_VERSION,
    utc_now_iso,
)
from metrology_process_planner.domains.session.grids import GridDatasetRecord
from metrology_process_planner.domains.session.legacy_artifacts import legacy_artifacts
from metrology_process_planner.domains.session.migration import migration_audit
from metrology_process_planner.domains.session.mode_fallback import apply_mode_fallback
from metrology_process_planner.domains.session.process_outputs import (
    ProcessContext,
    ProcessOutputRecord,
    ReportRecord,
)
from metrology_process_planner.domains.session.serialization_support import (
    artifact_records,
    canvas_objects_from_extensions,
    pending_captures_from_extensions,
)
from metrology_process_planner.domains.session.setup import SetupState
from metrology_process_planner.domains.session.warnings import WarningRecord
from metrology_process_planner.domains.session.workflow import AuditEvent, WorkflowState


def session_to_dict(session: Any) -> dict[str, Any]:
    """Serialize a session in canonical v5 shape."""

    artifacts = session.artifacts or {}
    return {
        "schema": session.schema.to_dict(),
        "session": _identity(session).to_dict(),
        "paths": session.paths.to_dict(),
        "source_layout": session.source_layout.to_dict(),
        "coordinates": session.coordinates.to_dict(),
        "setup": session.setup.to_dict(),
        "captures": [capture.to_dict() for capture in session.captures],
        "grid_datasets": [dataset.to_dict() for dataset in session.grid_datasets],
        "process_context": session.process_context.to_dict(),
        "process_outputs": [output.to_dict() for output in session.process_outputs],
        "reports": [report.to_dict() for report in session.reports],
        "artifacts": {
            artifact_id: artifact.to_dict()
            for artifact_id, artifact in sorted(artifacts.items())
        },
        "warnings": [warning.to_dict() for warning in session.warnings],
        "workflow": _workflow_with_pending(session).to_dict(),
        "extensions": _extensions_with_runtime_state(session),
        "audit": [event.to_dict() for event in session.audit],
    }


def session_from_dict(record_type: Any, mode_type: Any, data: Mapping[str, Any]) -> Any:
    """Build a SessionRecord from v5 or legacy JSON-compatible data."""

    if "schema" in data:
        return _from_v5_dict(record_type, mode_type, data)
    return _from_legacy_dict(record_type, mode_type, data)


def _from_legacy_dict(record_type: Any, mode_type: Any, data: Mapping[str, Any]) -> Any:
    source_schema_version = int(data.get("schema_version", 1))
    if source_schema_version > LEGACY_SESSION_SCHEMA_VERSION:
        raise ValueError(
            f"Session schema {source_schema_version} is newer than supported legacy "
            f"schema {LEGACY_SESSION_SCHEMA_VERSION}."
        )
    requested_mode = str(data.get("mode", "simple_capture"))
    warnings = tuple(WarningRecord.from_dict(item) for item in data.get("warnings", ()))
    audit = (migration_audit(source_schema_version),)
    fallback = apply_mode_fallback(mode_type, requested_mode, warnings, audit)
    return record_type(
        schema_version=SESSION_SCHEMA_VERSION,
        schema=SchemaRecord(
            version=SESSION_SCHEMA_VERSION,
            previous_version=str(source_schema_version),
            migrated_from=str(source_schema_version),
        ),
        id=str(data["id"]),
        name=str(data.get("name", "Untitled session")),
        mode=fallback.mode,
        created_at=str(data.get("created_at", utc_now_iso())),
        updated_at=str(data.get("updated_at", utc_now_iso())),
        setup=SetupState.from_dict(data.get("setup", {})),
        captures=tuple(
            CaptureRecord.from_dict(_legacy_capture_payload(item))
            for item in data.get("captures", ())
        ),
        canvas_objects=tuple(
            CanvasObject.from_dict(item) for item in data.get("canvas_objects", ())
        ),
        pending_captures=tuple(
            PendingCapture.from_dict(item) for item in data.get("pending_captures", ())
        ),
        grid_datasets=tuple(
            GridDatasetRecord.from_dict(item) for item in data.get("grid_datasets", ())
        ),
        process_context=ProcessContext.from_legacy_dict(data.get("process_context", {})),
        artifacts=legacy_artifacts(data),
        warnings=fallback.warnings,
        metadata=dict(data.get("metadata", {})),
        extensions=fallback.extensions,
        audit=fallback.audit,
    )


def _from_v5_dict(record_type: Any, mode_type: Any, data: Mapping[str, Any]) -> Any:
    schema = SchemaRecord.from_dict(data.get("schema", {}))
    if schema.version > SESSION_SCHEMA_VERSION:
        raise ValueError(
            f"Session schema {schema.version} is newer than supported schema "
            f"{SESSION_SCHEMA_VERSION}."
        )
    identity = SessionIdentity.from_dict(data.get("session", {}))
    artifacts = artifact_records(data.get("artifacts", {}))
    captures = tuple(CaptureRecord.from_dict(item) for item in data.get("captures", ()))
    warnings = tuple(WarningRecord.from_dict(item) for item in data.get("warnings", ()))
    audit = tuple(AuditEvent.from_dict(item) for item in data.get("audit", ()))
    extensions = dict(data.get("extensions", {}))
    fallback = apply_mode_fallback(mode_type, identity.mode, warnings, audit, extensions)
    return record_type(
        schema_version=schema.version,
        schema=schema,
        id=identity.id,
        name=identity.name,
        mode=fallback.mode,
        created_at=identity.created_at,
        updated_at=identity.updated_at,
        paths=SessionPathsRecord.from_dict(data.get("paths", {})),
        source_layout=SourceLayoutContext.from_dict(data.get("source_layout", {})),
        coordinates=CoordinateContext.from_dict(data.get("coordinates", {})),
        setup=SetupState.from_dict(data.get("setup", {})),
        captures=captures,
        grid_datasets=tuple(
            GridDatasetRecord.from_dict(item) for item in data.get("grid_datasets", ())
        ),
        process_context=ProcessContext.from_dict(data.get("process_context", {})),
        process_outputs=tuple(
            ProcessOutputRecord.from_dict(item) for item in data.get("process_outputs", ())
        ),
        reports=tuple(ReportRecord.from_dict(item) for item in data.get("reports", ())),
        artifacts=artifacts,
        canvas_objects=canvas_objects_from_extensions(data),
        pending_captures=pending_captures_from_extensions(data),
        warnings=fallback.warnings,
        workflow=WorkflowState.from_dict(data.get("workflow", {})),
        extensions=fallback.extensions,
        audit=fallback.audit,
    )


def _legacy_capture_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    if "type" not in payload and "capture_type" in payload:
        payload["type"] = payload["capture_type"]
    return payload


def _identity(session: Any) -> SessionIdentity:
    return SessionIdentity(
        session.id,
        session.name,
        session.mode.value,
        session.created_at,
        session.updated_at,
    )


def _workflow_with_pending(session: Any) -> WorkflowState:
    workflow = cast(WorkflowState, session.workflow)
    if workflow.pending_item_ref or not session.pending_captures:
        return workflow
    return replace(workflow, pending_item_ref=session.pending_captures[0].id)


def _extensions_with_runtime_state(session: Any) -> dict[str, Any]:
    extensions = dict(session.extensions or {})
    canvas_extension = dict(extensions.get("canvas", {}))
    if session.canvas_objects:
        canvas_extension["canvas_objects"] = [item.to_dict() for item in session.canvas_objects]
    if session.pending_captures:
        canvas_extension["pending_captures"] = [item.to_dict() for item in session.pending_captures]
    if canvas_extension:
        extensions["canvas"] = canvas_extension
    return extensions

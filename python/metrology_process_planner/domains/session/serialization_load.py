"""Session JSON load and migration helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.domains.artifacts.legacy_artifacts import legacy_artifacts
from metrology_process_planner.domains.capture.canvas import CanvasObject, PendingCapture
from metrology_process_planner.domains.capture.captures import CaptureRecord
from metrology_process_planner.domains.capture.grids import GridDatasetRecord
from metrology_process_planner.domains.modes.mode_fallback import apply_mode_fallback
from metrology_process_planner.domains.session.canonical import (
    CoordinateContext,
    SchemaRecord,
    SessionIdentity,
    SessionPathsRecord,
    SourceLayoutContext,
)
from metrology_process_planner.domains.session.constants import (
    LEGACY_SESSION_SCHEMA_VERSION,
    SESSION_SCHEMA_VERSION,
    utc_now_iso,
)
from metrology_process_planner.domains.session.migration import migration_audit
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
from metrology_process_planner.domains.session.workflow import AuditEvent, WorkflowState
from metrology_process_planner.domains.warnings.warnings import WarningRecord


def session_from_dict(
    record_type: Any,
    mode_type: Any,
    data: Mapping[str, Any],
    allowed_mode_ids: tuple[str, ...] = (),
) -> Any:
    """Build a SessionRecord from v5 or legacy JSON-compatible data."""

    if "schema" in data:
        return _from_v5_dict(record_type, mode_type, data, allowed_mode_ids)
    return _from_legacy_dict(record_type, mode_type, data, allowed_mode_ids)


def _from_legacy_dict(
    record_type: Any,
    mode_type: Any,
    data: Mapping[str, Any],
    allowed_mode_ids: tuple[str, ...],
) -> Any:
    source_schema_version = int(data.get("schema_version", 1))
    _raise_if_legacy_schema_too_new(source_schema_version)
    fallback = _legacy_mode_fallback(mode_type, data, source_schema_version, allowed_mode_ids)
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


def _from_v5_dict(
    record_type: Any,
    mode_type: Any,
    data: Mapping[str, Any],
    allowed_mode_ids: tuple[str, ...],
) -> Any:
    schema = SchemaRecord.from_dict(data.get("schema", {}))
    _raise_if_schema_too_new(schema)
    identity = SessionIdentity.from_dict(data.get("session", {}))
    fallback = _v5_mode_fallback(mode_type, identity.mode, data, allowed_mode_ids)
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
        captures=tuple(CaptureRecord.from_dict(item) for item in data.get("captures", ())),
        grid_datasets=tuple(
            GridDatasetRecord.from_dict(item) for item in data.get("grid_datasets", ())
        ),
        process_context=ProcessContext.from_dict(data.get("process_context", {})),
        process_outputs=tuple(
            ProcessOutputRecord.from_dict(item) for item in data.get("process_outputs", ())
        ),
        reports=tuple(ReportRecord.from_dict(item) for item in data.get("reports", ())),
        artifacts=artifact_records(data.get("artifacts", {})),
        canvas_objects=canvas_objects_from_extensions(data),
        pending_captures=pending_captures_from_extensions(data),
        warnings=fallback.warnings,
        workflow=WorkflowState.from_dict(data.get("workflow", {})),
        extensions=fallback.extensions,
        audit=fallback.audit,
    )


def _legacy_mode_fallback(
    mode_type: Any,
    data: Mapping[str, Any],
    source_schema_version: int,
    allowed_mode_ids: tuple[str, ...],
) -> Any:
    requested_mode = str(data.get("mode", "simple_capture"))
    warnings = tuple(WarningRecord.from_dict(item) for item in data.get("warnings", ()))
    audit = (migration_audit(source_schema_version),)
    return apply_mode_fallback(
        mode_type,
        requested_mode,
        warnings,
        audit,
        allowed_mode_ids=allowed_mode_ids,
    )


def _v5_mode_fallback(
    mode_type: Any,
    requested_mode: str,
    data: Mapping[str, Any],
    allowed_mode_ids: tuple[str, ...],
) -> Any:
    warnings = tuple(WarningRecord.from_dict(item) for item in data.get("warnings", ()))
    audit = tuple(AuditEvent.from_dict(item) for item in data.get("audit", ()))
    return apply_mode_fallback(
        mode_type,
        requested_mode,
        warnings,
        audit,
        dict(data.get("extensions", {})),
        allowed_mode_ids,
    )


def _raise_if_legacy_schema_too_new(source_schema_version: int) -> None:
    if source_schema_version > LEGACY_SESSION_SCHEMA_VERSION:
        raise ValueError(
            f"Session schema {source_schema_version} is newer than supported legacy "
            f"schema {LEGACY_SESSION_SCHEMA_VERSION}."
        )


def _raise_if_schema_too_new(schema: SchemaRecord) -> None:
    if schema.version > SESSION_SCHEMA_VERSION:
        raise ValueError(
            f"Session schema {schema.version} is newer than supported schema "
            f"{SESSION_SCHEMA_VERSION}."
        )


def _legacy_capture_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    if "type" not in payload and "capture_type" in payload:
        payload["type"] = payload["capture_type"]
    return payload

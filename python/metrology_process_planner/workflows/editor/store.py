"""Load and save editor documents while preserving raw session payload fields."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionMode,
    SessionModeId,
    SessionRecord,
    SourceLayoutContext,
    utc_now_iso,
)
from metrology_process_planner.persistence.paths import SESSION_JSON_NAME, SessionPaths
from metrology_process_planner.persistence.repair import validate_artifact_files
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.document import DirtyState, SessionDocument
from metrology_process_planner.workflows.editor.editing import apply_metadata_edits
from metrology_process_planner.workflows.editor.store_io import (
    PathInput,
    allowed_modes,
    atomic_write_json,
    resolve_session_json,
)
from metrology_process_planner.workflows.editor.store_payload import merged_payload
from metrology_process_planner.workflows.editor.store_recent import RecentSessionRegistry
from metrology_process_planner.workflows.editor.store_services import (
    SessionMigrationService,
    SessionValidationService,
)
from metrology_process_planner.workflows.editor.store_warnings import with_open_warnings

__all__ = ("NewSessionRequest", "RecentSessionRegistry", "SessionDocumentLoader",
           "SessionDocumentStore", "SessionDocumentWriter", "SessionMigrationService",
           "SessionStore", "SessionValidationService")


class SessionDocumentStore:
    """Read and write editor documents with top-level unknown field preservation."""

    def __init__(
        self,
        builder: SessionDocumentBuilder | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._builder = (
            builder if builder is not None else SessionDocumentBuilder(mode_registry)
        )
        self._mode_registry = mode_registry

    def load(self, path_or_folder: PathInput) -> SessionDocument:
        """Load a session JSON file or folder into a normalized editor document."""
        return SessionDocumentLoader(self._builder, self._mode_registry).load(path_or_folder)

    def save(self, document: SessionDocument, paths: SessionPaths) -> SessionDocument:
        """Save a document session and return a clean rebuilt document."""
        return SessionDocumentWriter(self._builder, self._mode_registry).save(document, paths)


class SessionDocumentLoader:
    """Load, migrate, validate, and normalize session JSON documents."""

    def __init__(
        self,
        builder: SessionDocumentBuilder | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._builder = (
            builder if builder is not None else SessionDocumentBuilder(mode_registry)
        )
        self._migration = SessionMigrationService(mode_registry)

    def load(self, path_or_folder: PathInput) -> SessionDocument:
        """Load a session JSON file or folder into a normalized editor document."""
        path = resolve_session_json(path_or_folder)
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, Mapping):
            raise ValueError(f"Session JSON must contain an object: {path}")
        warnings = SessionValidationService().validate_payload(raw)
        session = self._migration.migrate(raw)
        session = validate_artifact_files(session, SessionPaths.for_folder(path.parent))
        session = with_open_warnings(session, warnings, path.parent)
        document = self._builder.build(session, raw_payload=raw)
        return replace(
            document,
            loaded_path=path,
            dirty_state=DirtyState(last_saved_revision=1),
            revision=1,
        )


class SessionDocumentWriter:
    """Validate and atomically write normalized session JSON documents."""

    def __init__(
        self,
        builder: SessionDocumentBuilder | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._builder = (
            builder if builder is not None else SessionDocumentBuilder(mode_registry)
        )
        self._mode_registry = mode_registry

    def save(self, document: SessionDocument, paths: SessionPaths) -> SessionDocument:
        """Save a document session and return a clean rebuilt document."""
        document = apply_metadata_edits(document, self._mode_registry)
        paths.ensure_created()
        session = replace(document.session, updated_at=utc_now_iso())
        payload = merged_payload(document.raw_payload, session.to_dict())
        SessionValidationService().validate_for_save(payload)
        destination = paths.session_json
        atomic_write_json(destination, payload)
        clean_document = self._builder.build(
            SessionRecord.from_dict(payload, allowed_modes(self._mode_registry, session)),
            raw_payload=payload,
        )
        revision = max(document.revision + 1, document.dirty_state.last_saved_revision + 1)
        return replace(
            clean_document,
            loaded_path=destination,
            dirty_state=DirtyState(last_saved_revision=revision),
            revision=revision,
        )


@dataclass(frozen=True)
class NewSessionRequest:
    """Inputs required to create a durable editable session document."""

    output_folder: Path
    label: str = "Untitled session"
    mode: SessionMode | SessionModeId = SessionMode.SIMPLE_CAPTURE
    source_layout: SourceLayoutContext = SourceLayoutContext()


class SessionStore:
    """High-level document store for new, open, save, and save-as flows."""

    def __init__(
        self,
        document_store: SessionDocumentStore | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._documents = (
            document_store
            if document_store is not None
            else SessionDocumentStore(mode_registry=mode_registry)
        )
        self._mode_registry = mode_registry

    def new_session(self, request: NewSessionRequest) -> SessionDocument:
        """Create a valid minimal session.json and return its loaded document."""
        now = utc_now_iso()
        session = SessionRecord(
            id=f"sess_{uuid4().hex[:12]}",
            name=request.label,
            mode=request.mode,
            created_at=now,
            updated_at=now,
            source_layout=request.source_layout,
        )
        paths = SessionPaths.for_folder(request.output_folder)
        document = SessionDocumentBuilder(self._mode_registry).build(
            session,
            raw_payload=session.to_dict(),
        )
        return self._documents.save(document, paths)

    def open_session(self, path_or_folder: PathInput) -> SessionDocument:
        """Open an existing session JSON file or folder."""
        return self._documents.load(path_or_folder)

    def save(self, document: SessionDocument, paths: SessionPaths) -> SessionDocument:
        """Save an existing loaded document."""

        return self._documents.save(document, paths)

    def save_as(self, document: SessionDocument, destination: PathInput) -> SessionDocument:
        """Save a loaded document to a new session folder or session.json path."""

        destination_path = Path(destination)
        paths = SessionPaths.for_folder(
            destination_path.parent
            if destination_path.name == SESSION_JSON_NAME
            else destination_path
        )
        return self._documents.save(document, paths)

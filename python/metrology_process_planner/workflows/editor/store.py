"""Load and save editor documents while preserving raw session payload fields."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, Optional, Union

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.persistence.paths import SESSION_JSON_NAME, SessionPaths
from metrology_process_planner.persistence.repair import validate_artifact_files
from metrology_process_planner.persistence.schema import validate_session_payload
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.document import DirtyState, SessionDocument
from metrology_process_planner.workflows.editor.editing import apply_metadata_edits

PathInput = Union[str, Path]


class SessionDocumentStore:
    """Read and write editor documents with top-level unknown field preservation."""

    def __init__(self, builder: Optional[SessionDocumentBuilder] = None) -> None:
        self._builder = builder if builder is not None else SessionDocumentBuilder()

    def load(self, path_or_folder: PathInput) -> SessionDocument:
        """Load a session JSON file or folder into a normalized editor document."""

        path = _resolve_session_json(path_or_folder)
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, Mapping):
            raise ValueError(f"Session JSON must contain an object: {path}")
        validate_session_payload(raw)
        session = validate_artifact_files(
            SessionRecord.from_dict(raw),
            SessionPaths.for_folder(path.parent),
        )
        return self._builder.build(session, raw_payload=raw)

    def save(self, document: SessionDocument, paths: SessionPaths) -> SessionDocument:
        """Save a document session and return a clean rebuilt document."""

        document = apply_metadata_edits(document)
        paths.ensure_created()
        payload = _merged_payload(document.raw_payload, document.session.to_dict())
        destination = paths.session_json
        temp_path = destination.with_suffix(destination.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        if destination.exists():
            shutil.copy2(destination, destination.with_suffix(destination.suffix + ".bak"))
        temp_path.replace(destination)
        clean_document = self._builder.build(SessionRecord.from_dict(payload), raw_payload=payload)
        return replace(clean_document, dirty_state=DirtyState(last_saved_revision=1))


def _resolve_session_json(path_or_folder: PathInput) -> Path:
    path = Path(path_or_folder)
    if path.is_dir():
        return path / SESSION_JSON_NAME
    return path


def _merged_payload(
    raw_payload: Mapping[str, Any],
    session_payload: Mapping[str, Any],
) -> dict[str, Any]:
    merged = {
        key: value
        for key, value in raw_payload.items()
        if key not in _KNOWN_TOP_LEVEL_FIELDS
    }
    merged.update(session_payload)
    return merged


_KNOWN_TOP_LEVEL_FIELDS = {
    "schema",
    "schema_version",
    "session",
    "paths",
    "source_layout",
    "coordinates",
    "setup",
    "captures",
    "canvas_objects",
    "pending_captures",
    "drawings",
    "grid_datasets",
    "process_context",
    "process_outputs",
    "reports",
    "artifacts",
    "exports",
    "warnings",
    "workflow",
    "metadata",
    "extensions",
    "audit",
    "id",
    "name",
    "mode",
    "created_at",
    "updated_at",
}

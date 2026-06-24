"""Artifact-backed drawing editor item builders."""

from __future__ import annotations

from metrology_process_planner.domains.session import ArtifactRecord, SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_refs import (
    _artifact_refs_for_owner,
)
from metrology_process_planner.workflows.editor.document import SessionItem, SessionItemKind
from metrology_process_planner.workflows.editor.references import RecordRef


def artifact_owned_drawing_items(session: SessionRecord) -> tuple[SessionItem, ...]:
    """Return editor items for drawing artifacts without concrete owner records."""

    artifact_groups: dict[tuple[str, str, str], None] = {}
    existing_record_refs = _existing_record_refs(session)
    for artifact in (session.artifacts or {}).values():
        if not _is_artifact_owned_drawing(artifact, existing_record_refs):
            continue
        drawing_role = artifact.owner.role.rsplit("_", 1)[0]
        artifact_groups[(artifact.owner.owner_type, artifact.owner.owner_id, drawing_role)] = None
    return tuple(
        _artifact_owned_drawing_item(session, owner_type, owner_id, role)
        for owner_type, owner_id, role in sorted(artifact_groups)
    )


def _existing_record_refs(session: SessionRecord) -> set[tuple[str, str]]:
    return {("process_output", output.id) for output in session.process_outputs} | {
        ("report", report.id) for report in session.reports
    }


def _is_artifact_owned_drawing(
    artifact: ArtifactRecord,
    existing_refs: set[tuple[str, str]],
) -> bool:
    owner = artifact.owner
    owner_key = (owner.owner_type, owner.owner_id)
    return (
        owner.role.endswith(("_spec", "_svg", "_png"))
        and owner_key not in existing_refs
        and owner.owner_type not in {"capture", "measurement"}
    )


def _artifact_owned_drawing_item(
    session: SessionRecord,
    owner_type: str,
    owner_id: str,
    role: str,
) -> SessionItem:
    kind = SessionItemKind.CROSS_SECTION if role == "cross_section" else SessionItemKind.REPORT
    return SessionItem(
        item_id=f"drawing:{owner_type}:{owner_id}:{role}",
        kind=kind,
        label=owner_id,
        role=role,
        record_ref=RecordRef(owner_type, owner_id),
        artifact_refs=tuple(
            ref
            for ref in _artifact_refs_for_owner(session, owner_type, owner_id)
            if ref.role.startswith(f"{role}_")
        ),
    )

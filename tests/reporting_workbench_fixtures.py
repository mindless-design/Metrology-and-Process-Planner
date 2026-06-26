from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.document import SessionDocument
from tests.editor_render_fixtures import session_without_pending


def document() -> SessionDocument:
    return SessionDocumentBuilder().build(session_without_pending())


def document_with_artifact(status: ArtifactStatus) -> SessionDocument:
    source = document()
    artifact = ArtifactRecord(
        "missing-image",
        "image",
        "Missing Image",
        "images/missing.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=status,
    )
    session = replace(source.session, artifacts={artifact.id: artifact})
    return SessionDocumentBuilder().build(session)


class FakeRepairService:
    def regenerate_missing(
        self,
        source: SessionDocument,
        _paths: SessionPaths,
    ) -> SessionDocument:
        return self._regenerate(source)

    def regenerate_stale(
        self,
        source: SessionDocument,
        _paths: SessionPaths,
    ) -> SessionDocument:
        return self._regenerate(source)

    def _regenerate(self, source: SessionDocument) -> SessionDocument:
        assert source.session.artifacts is not None
        artifact = replace(
            source.session.artifacts["missing-image"],
            status=ArtifactStatus.PRESENT,
        )
        session = replace(source.session, artifacts={"missing-image": artifact})
        return SessionDocumentBuilder().build(session)

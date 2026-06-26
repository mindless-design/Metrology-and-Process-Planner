"""Session artifact health scanner."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.scan_result import ArtifactScanResult
from metrology_process_planner.workflows.artifacts.scanner_references import (
    with_reference_warnings,
)
from metrology_process_planner.workflows.artifacts.scanner_status import (
    failure_warning,
    with_file_status,
    with_stale_status,
    with_warning,
)
from metrology_process_planner.workflows.artifacts.scanner_summary import paths_from, scan_result


class ArtifactScanner:
    """Inspect session artifact records and update their health statuses."""

    def scan_session(
        self,
        session: SessionRecord,
        paths: SessionPaths | Path | str,
        mode_registry: ModeRegistry | None = None,
    ) -> tuple[SessionRecord, ArtifactScanResult]:
        """Return an updated session and scan summary."""

        resolved = paths_from(paths)
        warnings = {warning.id: warning for warning in session.warnings}
        artifacts: dict[str, ArtifactRecord] = {}
        for artifact_id, artifact in (session.artifacts or {}).items():
            if not artifact_visible_for_session(session, artifact, mode_registry):
                artifacts[artifact_id] = artifact
                continue
            artifacts[artifact_id] = self._scan_artifact(
                session,
                artifact,
                resolved,
                warnings,
                mode_registry,
            )
        updated = replace(session, artifacts=artifacts, warnings=tuple(warnings.values()))
        result = scan_result(updated, mode_registry)
        return updated, result

    def _scan_artifact(
        self,
        session: SessionRecord,
        artifact: ArtifactRecord,
        paths: SessionPaths,
        warnings: dict[str, WarningRecord],
        mode_registry: ModeRegistry | None,
    ) -> ArtifactRecord:
        checked = with_reference_warnings(session, artifact, warnings)
        if checked.status in {ArtifactStatus.SUPERSEDED, ArtifactStatus.INTENTIONALLY_IGNORED}:
            return checked
        checked = with_file_status(checked, paths, warnings)
        checked = with_stale_status(session, checked, warnings, mode_registry)
        if checked.status is ArtifactStatus.FAILED:
            return with_warning(
                checked,
                failure_warning(checked),
                warnings,
            )
        return checked

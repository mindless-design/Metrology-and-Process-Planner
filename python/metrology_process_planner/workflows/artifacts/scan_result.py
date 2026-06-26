"""Artifact scan result models."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.session import ArtifactStatus


@dataclass(frozen=True)
class ArtifactScanResult:
    """Summary of a session artifact health scan."""

    session_id: str
    checked_at: str
    artifact_count: int
    present_count: int = 0
    missing_count: int = 0
    stale_count: int = 0
    failed_count: int = 0
    placeholder_count: int = 0
    warning_ids: tuple[str, ...] = ()
    repair_candidates: tuple[str, ...] = ()

    @classmethod
    def from_statuses(
        cls,
        session_id: str,
        checked_at: str,
        statuses: tuple[tuple[str, ArtifactStatus], ...],
        warning_ids: tuple[str, ...],
        repair_candidates: tuple[str, ...],
    ) -> ArtifactScanResult:
        """Build counts from scanned artifact statuses."""

        return cls(
            session_id=session_id,
            checked_at=checked_at,
            artifact_count=len(statuses),
            present_count=_count(statuses, ArtifactStatus.PRESENT),
            missing_count=_count(statuses, ArtifactStatus.MISSING),
            stale_count=_count(statuses, ArtifactStatus.STALE),
            failed_count=_count(statuses, ArtifactStatus.FAILED),
            placeholder_count=_count(statuses, ArtifactStatus.PLACEHOLDER),
            warning_ids=warning_ids,
            repair_candidates=repair_candidates,
        )


def _count(
    statuses: tuple[tuple[str, ArtifactStatus], ...],
    status: ArtifactStatus,
) -> int:
    return sum(1 for _artifact_id, item_status in statuses if item_status is status)

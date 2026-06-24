"""Process context, output, and report session records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.session.constants import utc_now_iso
from metrology_process_planner.domains.session.process_context_io import (
    active_process_context_data,
    legacy_process_context_data,
    process_context_to_dict,
)


@dataclass(frozen=True)
class ProcessContext:
    """Process recipe and solver context captured with a session."""

    recipe_reference: str = ""
    recipe_id: str = ""
    recipe_name: str = ""
    recipe_version: str = ""
    recipe_path: str = ""
    recipe_fingerprint: str = ""
    recipe_snapshot_policy: str = "embed_minimal_summary"
    recipe_snapshot: Optional[Mapping[str, Any]] = None
    solver_backend: str = ""
    solver_version: str = ""
    solver_options: Optional[Mapping[str, Any]] = None
    render_profile: str = ""
    process_window_variant: str = ""
    warning_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.recipe_snapshot is None:
            object.__setattr__(self, "recipe_snapshot", {})
        if self.solver_options is None:
            object.__setattr__(self, "solver_options", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize process context."""

        return process_context_to_dict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessContext:
        """Build process context from saved data."""

        data = active_process_context_data(data)
        return cls.from_flat_data(data)

    @classmethod
    def from_legacy_dict(cls, data: Mapping[str, Any]) -> ProcessContext:
        """Build process context from integer-schema migration data."""

        return cls.from_flat_data(legacy_process_context_data(data))

    @classmethod
    def from_flat_data(cls, data: Mapping[str, Any]) -> ProcessContext:
        """Build process context from normalized constructor data."""

        return cls(
            recipe_reference=str(data.get("recipe_reference", "")),
            recipe_id=str(data.get("recipe_id", "")),
            recipe_name=str(data.get("recipe_name", "")),
            recipe_version=str(data.get("recipe_version", "")),
            recipe_path=str(data.get("recipe_path", "")),
            recipe_fingerprint=str(data.get("recipe_fingerprint", "")),
            recipe_snapshot_policy=str(data.get("recipe_snapshot_policy", "embed_minimal_summary")),
            recipe_snapshot=dict(data.get("recipe_snapshot", {})),
            solver_backend=str(data.get("solver_backend", "")),
            solver_version=str(data.get("solver_version", "")),
            solver_options=dict(data.get("solver_options", {})),
            render_profile=str(data.get("render_profile", "")),
            process_window_variant=str(data.get("process_window_variant", "")),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
        )


@dataclass(frozen=True)
class ProcessOutputRecord:
    """Process-rendered output or solver result owned by a session."""

    id: str
    label: str
    output_type: str
    status: str = "ready"
    artifact_refs: Optional[Mapping[str, str]] = None
    metadata: Optional[Mapping[str, Any]] = None
    extensions: Optional[Mapping[str, Any]] = None
    warning_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.artifact_refs is None:
            object.__setattr__(self, "artifact_refs", {})
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.extensions is None:
            object.__setattr__(self, "extensions", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize process output."""

        return {
            "id": self.id,
            "label": self.label,
            "output_type": self.output_type,
            "status": self.status,
            "artifact_refs": dict(self.artifact_refs or {}),
            "metadata": dict(self.metadata or {}),
            "extensions": dict(self.extensions or {}),
            "warning_ids": list(self.warning_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessOutputRecord:
        """Build process output from saved data."""

        return cls(
            id=str(data["id"]),
            label=str(data.get("label", "")),
            output_type=str(data.get("output_type", "")),
            status=str(data.get("status", "ready")),
            artifact_refs=dict(data.get("artifact_refs", {})),
            metadata=dict(data.get("metadata", {})),
            extensions=dict(data.get("extensions", {})),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
        )


@dataclass(frozen=True)
class ReportRecord:
    """Report artifact group generated from canonical session data."""

    id: str
    label: str
    report_type: str
    status: str = "ready"
    artifact_refs: Optional[Mapping[str, str]] = None
    generated_at: str = ""
    warning_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.artifact_refs is None:
            object.__setattr__(self, "artifact_refs", {})
        if not self.generated_at:
            object.__setattr__(self, "generated_at", utc_now_iso())

    def to_dict(self) -> dict[str, Any]:
        """Serialize report record."""

        return {
            "id": self.id,
            "label": self.label,
            "report_type": self.report_type,
            "status": self.status,
            "artifact_refs": dict(self.artifact_refs or {}),
            "generated_at": self.generated_at,
            "warning_ids": list(self.warning_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ReportRecord:
        """Build report record from saved data."""

        return cls(
            id=str(data["id"]),
            label=str(data.get("label", "")),
            report_type=str(data.get("report_type", "")),
            status=str(data.get("status", "ready")),
            artifact_refs=dict(data.get("artifact_refs", {})),
            generated_at=str(data.get("generated_at", "")),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
        )

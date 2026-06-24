"""Session schema migration helpers."""

from __future__ import annotations

from metrology_process_planner.domains.session.constants import SESSION_SCHEMA_VERSION, utc_now_iso
from metrology_process_planner.domains.session.workflow import AuditEvent


def migration_audit(source_schema_version: int) -> AuditEvent:
    """Return the audit event for an in-memory schema migration."""

    return AuditEvent(
        id=f"migration-{source_schema_version}-to-{SESSION_SCHEMA_VERSION}",
        event_type="schema_migration",
        message=(
            f"Migrated session schema {source_schema_version} to "
            f"{SESSION_SCHEMA_VERSION} in memory."
        ),
        created_at=utc_now_iso(),
        source="persistence",
        details={"source_schema_version": source_schema_version},
    )

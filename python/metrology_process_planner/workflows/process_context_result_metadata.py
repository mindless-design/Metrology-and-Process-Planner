"""Result metadata helpers for process-context commands."""

from __future__ import annotations

from collections.abc import Iterator, Mapping

from metrology_process_planner.domains.session import ProcessOutputRecord, SessionRecord


def updated_process_artifact_ids(session: SessionRecord, owner_id: str) -> tuple[str, ...]:
    """Return process artifact ids updated by a command."""

    ids: list[str] = []
    for output in _matching_outputs(session, owner_id):
        ids.extend(str(artifact_id) for artifact_id in dict(output.artifact_refs or {}).values())
    return tuple(dict.fromkeys(ids))


def updated_process_diagnostic_ids(session: SessionRecord, owner_id: str) -> tuple[str, ...]:
    """Return solver diagnostic ids attached to updated outputs."""

    ids: list[str] = []
    for output in _matching_outputs(session, owner_id):
        ids.extend(_diagnostic_ids(output.extensions or {}))
    return tuple(dict.fromkeys(ids))


def _matching_outputs(
    session: SessionRecord,
    owner_id: str,
) -> Iterator[ProcessOutputRecord]:
    for output in session.process_outputs:
        if not owner_id or dict(output.metadata or {}).get("capture_id") == owner_id:
            yield output


def _diagnostic_ids(extensions: object) -> tuple[str, ...]:
    extension_data = _mapping(extensions)
    solver_result = _mapping(extension_data.get("solver_result", {}))
    diagnostics = solver_result.get("diagnostics", ())
    if not isinstance(diagnostics, list):
        return ()
    return tuple(_diagnostic_id(item) for item in diagnostics if _diagnostic_id(item))


def _diagnostic_id(item: object) -> str:
    if not isinstance(item, Mapping):
        return ""
    code = str(item.get("code", ""))
    if not code:
        return ""
    step_id = str(item.get("step_id", "solver"))
    return f"{step_id}:{code}"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}

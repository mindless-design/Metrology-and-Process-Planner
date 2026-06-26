"""Placeholder text helpers for editor artifact previews."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.references import ArtifactRef


def artifact_placeholder_message(artifact: ArtifactRef) -> str:
    """Return user-facing placeholder detail for a missing or blocked artifact."""

    problem = _artifact_problem(artifact)
    owner = artifact.artifact_id or artifact.role
    repair = (
        artifact.repair_suggestion
        or artifact.repair_action
        or "Regenerate the artifact from the editor."
    )
    return (
        f"{problem} Belongs to {owner} ({artifact.role}). "
        f"{_artifact_impact()} Repair: {repair}"
    )


def _artifact_problem(artifact: ArtifactRef) -> str:
    """Return the problem sentence for an artifact preview placeholder."""

    status = artifact.status.replace("_", " ")
    problem = artifact.message or f"{status.title()} artifact: {artifact.path}"
    if artifact.status == "missing" and "missing artifact" not in problem.lower():
        return f"Missing artifact: {problem}"
    if artifact.status == "placeholder" and "placeholder" not in problem.lower():
        return f"Placeholder artifact: {problem}"
    return problem


def _artifact_impact() -> str:
    """Return the report/export impact sentence for artifact placeholders."""

    return "CSV export can continue; reports may use this placeholder."

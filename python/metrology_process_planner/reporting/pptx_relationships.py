"""OOXML relationship helpers for PowerPoint exports."""

from __future__ import annotations


def relationship(relationship_id: str, relationship_type: str, target: str) -> str:
    """Return one package relationship XML fragment."""

    return (
        f'<Relationship Id="{relationship_id}" '
        f'Type="{relationship_type}" Target="{target}"/>'
    )


def rels(relationships: tuple[str, ...]) -> str:
    """Return a relationships XML part."""

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(relationships)
        + "</Relationships>"
    )

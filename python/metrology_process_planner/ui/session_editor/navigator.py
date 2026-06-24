"""Navigator filtering for the generic session editor shell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from metrology_process_planner.workflows.editor.document import SessionDocument, SessionItem

NavigatorRows = tuple[tuple[str, tuple[tuple[str, str], ...]], ...]
NavigatorFilterCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class NavigatorFilterState:
    """Search and warning filter state for the editor navigator."""

    query: str = ""
    warning_filter: str = "all"


def navigator_groups(
    document: SessionDocument,
    state: NavigatorFilterState | None = None,
) -> NavigatorRows:
    """Return grouped navigator rows after applying search/filter state."""

    filter_state = state or NavigatorFilterState()
    rows = []
    for group in document.navigator_groups:
        items = tuple(
            (item_id, document.items_by_id[item_id].label)
            for item_id in group.item_ids
            if _matches(document.items_by_id[item_id], filter_state)
        )
        if items:
            rows.append((group.label, items))
    return tuple(rows)


def _matches(item: SessionItem, state: NavigatorFilterState) -> bool:
    if not _matches_query(item, state.query):
        return False
    return _matches_warning_filter(item, state.warning_filter)


def _matches_query(item: SessionItem, query: str) -> bool:
    text = query.strip().casefold()
    if not text:
        return True
    haystack = " ".join((item.item_id, item.label, item.role, item.status)).casefold()
    return text in haystack


def _matches_warning_filter(item: SessionItem, warning_filter: str) -> bool:
    normalized = warning_filter.strip().casefold()
    if normalized in {"", "all"}:
        return True
    if normalized == "warnings_only":
        return item.role == "warning" or bool(item.warning_ids)
    if item.role != "warning":
        return True
    return item.status.casefold() == normalized

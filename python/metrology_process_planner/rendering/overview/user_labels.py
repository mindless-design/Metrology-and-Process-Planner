"""Session-extension helpers for durable arbitrary overview labels."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.rendering.overview.models import UserLabelRecord

OVERVIEW_EXTENSION_KEY = "overview"
USER_LABELS_KEY = "user_labels"


def user_labels_from_session(session: SessionRecord) -> tuple[UserLabelRecord, ...]:
    """Return persisted user labels from the non-breaking overview extension."""

    overview = dict((session.extensions or {}).get(OVERVIEW_EXTENSION_KEY, {}))
    return tuple(
        UserLabelRecord.from_dict(item)
        for item in overview.get(USER_LABELS_KEY, ())
        if isinstance(item, dict)
    )


def with_user_label(session: SessionRecord, label: UserLabelRecord) -> SessionRecord:
    """Return a session with the label upserted into overview extensions."""

    labels = [item for item in user_labels_from_session(session) if item.label_id != label.label_id]
    labels.append(label)
    return with_user_labels(session, tuple(labels))


def without_user_label(session: SessionRecord, label_id: str) -> SessionRecord:
    """Return a session with one user label removed from overview extensions."""

    return with_user_labels(
        session,
        tuple(item for item in user_labels_from_session(session) if item.label_id != label_id),
    )


def with_user_labels(
    session: SessionRecord,
    labels: tuple[UserLabelRecord, ...],
) -> SessionRecord:
    """Return a session with the provided overview user-label records."""

    extensions = dict(session.extensions or {})
    overview = dict(extensions.get(OVERVIEW_EXTENSION_KEY, {}))
    overview[USER_LABELS_KEY] = [label.to_dict() for label in labels]
    extensions[OVERVIEW_EXTENSION_KEY] = overview
    return replace(session, extensions=extensions)


"""Presenter for pending capture review inside the unified editor."""

from __future__ import annotations

from metrology_process_planner.ui.preview_widgets import PreviewPresenter
from metrology_process_planner.ui.shell import (
    EditorActionViewModel,
    MetadataFieldViewModel,
    PendingCaptureViewModel,
)
from metrology_process_planner.workflows.editor import DefaultSessionModeAdapter
from metrology_process_planner.workflows.editor.document import SessionDocument, SessionItemKind


class PendingCaptureReviewPresenter:
    """Build pending capture review models from editor documents."""

    def __init__(
        self,
        preview_presenter: PreviewPresenter | None = None,
        adapter: DefaultSessionModeAdapter | None = None,
    ) -> None:
        self._preview = preview_presenter if preview_presenter is not None else PreviewPresenter()
        self._adapter = adapter if adapter is not None else DefaultSessionModeAdapter()

    def build_selected(self, document: SessionDocument) -> PendingCaptureViewModel | None:
        """Return a review model when the selected editor item is pending."""

        item = document.items_by_id[document.selection.selected_item_id]
        if item.kind is not SessionItemKind.PENDING_CAPTURE or item.record_ref is None:
            return None
        previews = self._preview.from_artifacts(item.artifact_refs)
        fields = self._adapter.metadata_fields(document.session, item)
        actions = self._adapter.actions(document.session, item)
        return PendingCaptureViewModel(
            item.record_ref.record_id,
            item.label,
            previews[0],
            tuple(
                MetadataFieldViewModel(field.key, field.label, field.value, field.required)
                for field in fields
            ),
            tuple(
                EditorActionViewModel(action.action_type.value, action.label, action.item_id)
                for action in actions
            ),
        )

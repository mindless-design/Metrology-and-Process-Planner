import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionModeId,
)
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.editor.view_models import EditorActionType
from tests.editor_render_fixtures import session_without_pending


class FastBatchRenameTests(unittest.TestCase):
    def test_action_generates_stable_labels_from_payload(self) -> None:
        source = replace(
            session_without_pending(),
            mode=SessionMode.FAST_BATCH_CAPTURE,
            captures=(
                _capture("cap-001", "Old A", 1),
                _capture("cap-002", "Old B", 2),
            ),
        )
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.BATCH_RENAME,
                "Batch Rename",
                "dashboard",
                payload=(("prefix", "Review"), ("start", "5"), ("padding", "2")),
            ),
        )

        self.assertEqual("success", result.status)
        self.assertEqual(
            ("Review 05", "Review 06"),
            tuple(capture.label for capture in result.document.session.captures),
        )

    def test_action_keeps_capture_metadata_label_aligned(self) -> None:
        source = replace(
            session_without_pending(),
            mode=SessionMode.FAST_BATCH_CAPTURE,
            captures=(
                replace(
                    _capture("cap-001", "Old A", 1),
                    metadata={"label": "Old A", "capture_role": "site"},
                ),
                replace(
                    _capture("cap-002", "Old B", 2),
                    metadata={"label": "Old B", "notes": "keep me"},
                ),
            ),
        )
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.BATCH_RENAME,
                "Batch Rename",
                "dashboard",
                payload=(("prefix", "Batch"),),
            ),
        )

        captures = result.document.session.captures
        self.assertEqual(("Batch 001", "Batch 002"), tuple(item.label for item in captures))
        self.assertEqual(
            ("Batch 001", "Batch 002"),
            tuple(str(item.metadata["label"]) for item in captures),
        )
        self.assertEqual("keep me", captures[1].metadata["notes"])

    def test_action_accepts_open_mode_id_for_fast_batch(self) -> None:
        source = replace(
            session_without_pending(),
            mode=SessionModeId("fast_batch_capture"),
            captures=(_capture("cap-001", "Old A", 1),),
        )
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.BATCH_RENAME, "Batch Rename", "dashboard"),
        )

        self.assertEqual("success", result.status)
        self.assertEqual("Capture 001", result.document.session.captures[0].label)

    def test_action_is_unavailable_outside_fast_batch_mode(self) -> None:
        document = SessionDocumentBuilder().build(session_without_pending())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.BATCH_RENAME, "Batch Rename", "dashboard"),
        )

        self.assertEqual("unavailable", result.status)


def _capture(capture_id: str, label: str, sequence: int) -> CaptureRecord:
    return CaptureRecord(
        id=capture_id,
        label=label,
        sequence=sequence,
        geometry=CaptureGeometry.box(Box(0, 0, 10, 10)),
        created_at="2026-06-23T20:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()

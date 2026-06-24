import unittest

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    SessionRecord,
)


class LegacyCaptureMigrationBoundaryTests(unittest.TestCase):
    def test_v5_capture_record_uses_canonical_type_only(self) -> None:
        payload = _capture_payload()
        payload["capture_type"] = "old_embedded_key"
        payload.pop("type", None)

        loaded = CaptureRecord.from_dict(payload)

        self.assertEqual("layout_region", loaded.type)

    def test_integer_schema_migration_maps_legacy_capture_type_at_boundary(self) -> None:
        loaded = SessionRecord.from_dict(_legacy_session_payload("old_special_capture"))

        self.assertEqual("old_special_capture", loaded.captures[0].type)


def _legacy_session_payload(capture_type: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "id": "session-legacy",
        "name": "Legacy",
        "mode": "simple_capture",
        "created_at": "2026-06-23T20:00:00Z",
        "updated_at": "2026-06-23T20:00:00Z",
        "captures": [_capture_payload(capture_type)],
    }


def _capture_payload(capture_type: str = "layout_region") -> dict[str, object]:
    return {
        "id": "cap-legacy",
        "label": "Legacy Capture",
        "capture_type": capture_type,
        "geometry": CaptureGeometry.box(Box(0, 0, 5, 5)).to_dict(),
        "created_at": "2026-06-23T20:00:00Z",
    }


if __name__ == "__main__":
    unittest.main()

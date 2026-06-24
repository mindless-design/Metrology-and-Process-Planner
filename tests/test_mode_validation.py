import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SESSION_JSON_NAME
from tests.test_session_round_trip import _sample_session


class ModeValidationTests(unittest.TestCase):
    def test_unknown_v5_mode_loads_with_warning_and_fallback(self) -> None:
        payload = _sample_session().to_dict()
        payload["session"]["mode"] = "profilometry_plus_magic"

        loaded = _load_payload(payload)

        self.assertEqual(SessionMode.SIMPLE_CAPTURE, loaded.mode)
        self.assertEqual(
            "profilometry_plus_magic",
            loaded.extensions["mode_validation"]["requested_mode"],
        )
        self.assertTrue(any(warning.code == "unsupported_mode" for warning in loaded.warnings))
        self.assertTrue(any(event.event_type == "mode_fallback" for event in loaded.audit))

    def test_unknown_legacy_mode_loads_with_warning_and_fallback(self) -> None:
        session = _sample_session()
        payload = {
            "schema_version": 4,
            "id": session.id,
            "name": session.name,
            "mode": "site_then_star",
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "setup": {},
            "captures": [],
            "grid_datasets": [],
            "exports": [],
            "warnings": [],
            "metadata": {},
        }

        loaded = _load_payload(payload)

        self.assertEqual(SessionMode.SIMPLE_CAPTURE, loaded.mode)
        self.assertEqual(
            "site_then_star",
            loaded.extensions["mode_validation"]["requested_mode"],
        )
        self.assertTrue(any(warning.code == "unsupported_mode" for warning in loaded.warnings))


def _load_payload(payload: dict) -> object:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / SESSION_JSON_NAME
        path.write_text(json.dumps(payload), encoding="utf-8")
        return SessionJsonStore().load(path)


if __name__ == "__main__":
    unittest.main()

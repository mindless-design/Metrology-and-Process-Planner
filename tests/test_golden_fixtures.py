import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.schema import validate_session_payload

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class GoldenFixtureTests(unittest.TestCase):
    def test_simple_session_json_loads_and_round_trips(self) -> None:
        session_path = FIXTURES / "sessions" / "simple_session" / "session.json"
        session = SessionJsonStore().load(session_path)

        self.assertEqual("session-001", session.id)
        self.assertEqual("cap-001", session.captures[0].id)
        self.assertEqual([], list(session.validation_warnings()))

    def test_simple_session_csv_matches_golden(self) -> None:
        fixture_folder = FIXTURES / "sessions" / "simple_session"
        session = SessionJsonStore().load(fixture_folder / "session.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            actual = CaptureCsvExporter().export(session, Path(temp_dir) / "captures.csv")
            actual_text = actual.read_text(encoding="utf-8")

        expected = (fixture_folder / "captures.csv").read_text(encoding="utf-8")
        self.assertEqual(expected, actual_text)

    def test_simple_recipe_fixture_validates(self) -> None:
        recipe_path = FIXTURES / "recipes" / "simple_recipe.json"
        recipe = ProcessRecipe.from_dict(_read_json_dict(recipe_path))

        self.assertEqual((), recipe.validate())

    def test_session_schema_reports_missing_fields(self) -> None:
        warnings = validate_session_payload({"schema_version": 1})

        self.assertTrue(any("Missing session fields" in warning for warning in warnings))


def _read_json_dict(path: Path) -> dict[str, object]:
    import json

    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise TypeError("Fixture must contain a JSON object.")
    return loaded


if __name__ == "__main__":
    unittest.main()


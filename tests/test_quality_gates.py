import tempfile
import unittest
from pathlib import Path

from tools.quality_gates import run_quality_gates


class QualityGateTests(unittest.TestCase):
    def test_missing_public_docstring_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.py"
            path.write_text(
                '"""Module summary is long enough."""\n\n\ndef public():\n    return 1\n'
            )

            violations = run_quality_gates((path,))

        self.assertTrue(any(violation.rule == "MPP003" for violation in violations))

    def test_oversized_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "large.py"
            path.write_text('"""Module summary is long enough."""\n' + "\n" * 221)

            violations = run_quality_gates((path,))

        self.assertTrue(any(violation.rule == "MPP001" for violation in violations))


if __name__ == "__main__":
    unittest.main()

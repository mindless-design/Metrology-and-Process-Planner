import unittest

from tools.quality_gates import run_quality_gates


class ProjectQualityTests(unittest.TestCase):
    def test_project_quality_gates_pass(self) -> None:
        violations = run_quality_gates()

        self.assertEqual(
            [],
            [violation.format() for violation in violations],
        )


if __name__ == "__main__":
    unittest.main()


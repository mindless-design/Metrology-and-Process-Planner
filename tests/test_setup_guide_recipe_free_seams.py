import unittest
from pathlib import Path


class SetupGuideRecipeFreeSeamTests(unittest.TestCase):
    def test_recipe_free_setup_builder_uses_neutral_ready_stage(self) -> None:
        source = Path("python/metrology_process_planner/workflows/setup_guide_stages.py")
        text = source.read_text(encoding="utf-8")

        self.assertNotIn("setup_guide_process_stages import ready_stage", text)
        self.assertIn("setup_guide_ready_stage import ready_stage", text)


if __name__ == "__main__":
    unittest.main()

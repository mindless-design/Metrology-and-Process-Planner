import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class KLayoutPackageStructureTests(unittest.TestCase):
    def test_grain_xml_exists_at_package_root(self) -> None:
        grain = PROJECT_ROOT / "grain.xml"

        self.assertTrue(grain.exists())
        root = ET.parse(grain).getroot()
        self.assertEqual("salt-grain", root.tag)

    def test_klayout_package_folders_exist_at_package_root(self) -> None:
        self.assertTrue((PROJECT_ROOT / "pymacros").is_dir())
        self.assertTrue((PROJECT_ROOT / "python" / "metrology_process_planner").is_dir())

    def test_bootstrap_macro_lives_in_root_pymacros(self) -> None:
        macro = PROJECT_ROOT / "pymacros" / "metrology_process_planner_bootstrap.py"

        self.assertTrue(macro.exists())


if __name__ == "__main__":
    unittest.main()


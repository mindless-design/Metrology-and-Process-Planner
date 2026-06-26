import unittest

from metrology_process_planner.domains.units import UnitParseError, format_length, parse_length


class UnitParserTests(unittest.TestCase):
    def test_common_length_units_normalize_to_micrometers(self) -> None:
        values = (
            parse_length("120 nm").value_um,
            parse_length("0.12 um").value_um,
            parse_length("1200 A", allow_plain_angstrom=True).value_um,
            parse_length("1200 Å").value_um,
            parse_length("0.00012 mm").value_um,
        )

        for value in values:
            self.assertAlmostEqual(0.12, value)

    def test_unitless_length_uses_context_default(self) -> None:
        self.assertAlmostEqual(120.0, parse_length("120").value_um)
        self.assertAlmostEqual(0.12, parse_length("120", default_unit="nm").value_um)

    def test_plain_a_is_rejected_when_context_is_ambiguous(self) -> None:
        with self.assertRaises(UnitParseError):
            parse_length("12 A")

    def test_invalid_units_raise_clear_error(self) -> None:
        with self.assertRaises(UnitParseError):
            parse_length("12 parsecs")

    def test_formatter_displays_from_canonical_micrometers(self) -> None:
        self.assertEqual("120 nm", format_length(0.12, display_unit="nm"))
        self.assertEqual("0.12 um", format_length(0.12, display_unit="um"))


if __name__ == "__main__":
    unittest.main()

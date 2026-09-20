"""fraction_util 的格式化与解析测试。"""

import unittest
from fractions import Fraction

from four_ops.fraction_util import format_fraction, parse_fraction


class FormatFractionTests(unittest.TestCase):
    def test_integer(self):
        self.assertEqual(format_fraction(Fraction(7)), "7")

    def test_zero(self):
        self.assertEqual(format_fraction(Fraction(0)), "0")

    def test_proper_fraction(self):
        self.assertEqual(format_fraction(Fraction(3, 5)), "3/5")

    def test_improper_fraction_becomes_mixed_number(self):
        self.assertEqual(format_fraction(Fraction(19, 8)), "2’3/8")

    def test_negative_integer(self):
        self.assertEqual(format_fraction(Fraction(-7)), "-7")

    def test_negative_proper_fraction(self):
        self.assertEqual(format_fraction(Fraction(-1, 2)), "-1/2")

    def test_negative_mixed_number(self):
        self.assertEqual(format_fraction(Fraction(-19, 8)), "-2’3/8")

    def test_reduces_before_formatting(self):
        self.assertEqual(format_fraction(Fraction(2, 4)), "1/2")


class ParseFractionTests(unittest.TestCase):
    def test_integer(self):
        self.assertEqual(parse_fraction("42"), Fraction(42))

    def test_integer_with_surrounding_whitespace(self):
        self.assertEqual(parse_fraction("  42  "), Fraction(42))

    def test_proper_fraction(self):
        self.assertEqual(parse_fraction("3/5"), Fraction(3, 5))

    def test_improper_fraction(self):
        self.assertEqual(parse_fraction("19/8"), Fraction(19, 8))

    def test_mixed_number_accepts_three_quote_characters(self):
        for text in ("2’3/8", "2'3/8", "2`3/8"):
            with self.subTest(text=text):
                self.assertEqual(parse_fraction(text), Fraction(19, 8))

    def test_negative_forms(self):
        self.assertEqual(parse_fraction("-7"), Fraction(-7))
        self.assertEqual(parse_fraction("-2’3/8"), Fraction(-19, 8))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            parse_fraction("   ")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_fraction("abc")

    def test_zero_denominator_raises(self):
        with self.assertRaises(ValueError):
            parse_fraction("1/0")

    def test_round_trip(self):
        values = [
            Fraction(0), Fraction(7), Fraction(3, 5), Fraction(19, 8),
            Fraction(-7), Fraction(-1, 2), Fraction(-19, 8), Fraction(7, 24),
        ]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(parse_fraction(format_fraction(value)), value)


if __name__ == "__main__":
    unittest.main()

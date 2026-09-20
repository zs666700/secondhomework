"""表达式文本 -> 表达式树。"""

import unittest
from fractions import Fraction

from four_ops.expression import BinOp, Num, evaluate, render
from four_ops.parser import ExpressionSyntaxError, parse_expression


def num(value):
    return Num(value if isinstance(value, Fraction) else Fraction(value))


class ParseExpressionTests(unittest.TestCase):
    def test_single_number(self):
        self.assertEqual(parse_expression("5"), num(5))

    def test_single_fraction(self):
        self.assertEqual(parse_expression("3/5"), num(Fraction(3, 5)))

    def test_addition(self):
        self.assertEqual(parse_expression("1 + 2"), BinOp("+", num(1), num(2)))

    def test_multiplication_binds_tighter_than_addition(self):
        self.assertEqual(
            parse_expression("1 + 2 × 3"),
            BinOp("+", num(1), BinOp("*", num(2), num(3))),
        )

    def test_addition_is_left_associative(self):
        self.assertEqual(
            parse_expression("1 + 2 + 3"),
            BinOp("+", BinOp("+", num(1), num(2)), num(3)),
        )

    def test_subtraction_is_left_associative(self):
        self.assertEqual(
            parse_expression("1 - 2 - 3"),
            BinOp("-", BinOp("-", num(1), num(2)), num(3)),
        )

    def test_parentheses_override_precedence(self):
        self.assertEqual(
            parse_expression("( 1 + 2 ) × 3"),
            BinOp("*", BinOp("+", num(1), num(2)), num(3)),
        )

    def test_division_operator(self):
        self.assertEqual(parse_expression("1 ÷ 2"), BinOp("/", num(1), num(2)))

    def test_minus_sign_variants(self):
        self.assertEqual(parse_expression("1 − 2"), parse_expression("1 - 2"))
        self.assertEqual(parse_expression("1 – 2"), parse_expression("1 - 2"))

    def test_asterisk_is_accepted_as_multiplication(self):
        self.assertEqual(parse_expression("1 * 2"), BinOp("*", num(1), num(2)))

    def test_mixed_number_operand(self):
        self.assertEqual(parse_expression("2’3/8 + 1"), BinOp("+", num(Fraction(19, 8)), num(1)))


class ParseExpressionErrorTests(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ExpressionSyntaxError):
            parse_expression("   ")

    def test_unclosed_parenthesis(self):
        with self.assertRaises(ExpressionSyntaxError):
            parse_expression("( 1 + 2")

    def test_stray_closing_parenthesis(self):
        with self.assertRaises(ExpressionSyntaxError):
            parse_expression("1 + 2 )")

    def test_bare_slash_is_rejected(self):
        # / 只作分数分隔符，不作除号
        with self.assertRaises(ExpressionSyntaxError):
            parse_expression("1 / 2")

    def test_trailing_equals_sign_is_rejected(self):
        # 等号由判分模块负责剥掉，解析器本身不接受
        with self.assertRaises(ExpressionSyntaxError):
            parse_expression("1 + 2 =")

    def test_dangling_operator(self):
        with self.assertRaises(ExpressionSyntaxError):
            parse_expression("1 +")

    def test_illegal_character(self):
        with self.assertRaises(ExpressionSyntaxError):
            parse_expression("1 # 2")


class RenderParseRoundTripTests(unittest.TestCase):
    CASES = [
        BinOp("+", num(1), num(2)),
        BinOp("+", BinOp("+", num(1), num(2)), num(3)),
        BinOp("+", num(1), BinOp("+", num(2), num(3))),
        BinOp("*", BinOp("+", num(1), num(2)), num(3)),
        BinOp("+", BinOp("*", num(1), num(2)), num(3)),
        BinOp("+", num(1), BinOp("*", num(2), num(3))),
        BinOp("-", num(1), BinOp("-", num(2), num(3))),
        BinOp("-", BinOp("-", num(1), num(2)), num(3)),
        BinOp("/", BinOp("/", num(1), num(2)), num(3)),
        BinOp("/", num(1), BinOp("*", num(2), num(3))),
        BinOp("-", BinOp("+", num(1), num(2)), BinOp("*", num(3), num(4))),
        BinOp("+", num(Fraction(1, 2)), num(Fraction(3, 4))),
        BinOp("/", num(Fraction(19, 8)), num(3)),
        BinOp("*", num(Fraction(1, 2)), BinOp("+", num(Fraction(3, 4)), num(2))),
    ]

    def test_round_trip_preserves_structure(self):
        for expr in self.CASES:
            with self.subTest(text=render(expr)):
                self.assertEqual(parse_expression(render(expr)), expr)

    def test_round_trip_preserves_value(self):
        for expr in self.CASES:
            with self.subTest(text=render(expr)):
                self.assertEqual(
                    evaluate(parse_expression(render(expr))), evaluate(expr)
                )


if __name__ == "__main__":
    unittest.main()

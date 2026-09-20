"""表达式树：求值、合法性、规范键、渲染。"""

import unittest
from fractions import Fraction

from four_ops.expression import (
    BinOp,
    Num,
    canonical_key,
    evaluate,
    is_legal,
    legal_operand_values,
    operator_count,
    render,
)


def num(value):
    return Num(value if isinstance(value, Fraction) else Fraction(value))


class EvaluateTests(unittest.TestCase):
    def test_single_number(self):
        self.assertEqual(evaluate(num(5)), Fraction(5))

    def test_fraction_addition_from_spec(self):
        # 需求原文的例子：1/6 + 1/8 = 7/24
        expr = BinOp("+", num(Fraction(1, 6)), num(Fraction(1, 8)))
        self.assertEqual(evaluate(expr), Fraction(7, 24))

    def test_multiplication_of_parenthesised_sum(self):
        expr = BinOp("*", BinOp("+", num(1), num(2)), num(3))
        self.assertEqual(evaluate(expr), Fraction(9))

    def test_division_yields_fraction(self):
        expr = BinOp("/", num(Fraction(1, 2)), num(Fraction(3, 4)))
        self.assertEqual(evaluate(expr), Fraction(2, 3))

    def test_division_by_zero_raises(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate(BinOp("/", num(1), num(0)))


class CanonicalKeyTests(unittest.TestCase):
    """需求原文明确给出的四个判定例子，逐条断言。"""

    def test_23_plus_45_equals_45_plus_23(self):
        self.assertEqual(
            canonical_key(BinOp("+", num(23), num(45))),
            canonical_key(BinOp("+", num(45), num(23))),
        )

    def test_6_times_8_equals_8_times_6(self):
        self.assertEqual(
            canonical_key(BinOp("*", num(6), num(8))),
            canonical_key(BinOp("*", num(8), num(6))),
        )

    def test_3_plus_2_plus_1_equals_1_plus_2_plus_3(self):
        # 1+2+3 即 ((1+2)+3)；3+(2+1) 交换外层再交换内层即可得到
        lhs = BinOp("+", BinOp("+", num(1), num(2)), num(3))
        rhs = BinOp("+", num(3), BinOp("+", num(2), num(1)))
        self.assertEqual(canonical_key(lhs), canonical_key(rhs))

    def test_1_plus_2_plus_3_differs_from_3_plus_2_plus_1(self):
        # 需求原文明确说这两道题**不重复**
        lhs = BinOp("+", BinOp("+", num(1), num(2)), num(3))
        rhs = BinOp("+", BinOp("+", num(3), num(2)), num(1))
        self.assertNotEqual(canonical_key(lhs), canonical_key(rhs))

    def test_subtraction_is_order_sensitive(self):
        self.assertNotEqual(
            canonical_key(BinOp("-", num(5), num(3))),
            canonical_key(BinOp("-", num(3), num(5))),
        )

    def test_division_is_order_sensitive(self):
        self.assertNotEqual(
            canonical_key(BinOp("/", num(1), num(2))),
            canonical_key(BinOp("/", num(2), num(1))),
        )

    def test_commutativity_reaches_nested_subexpressions(self):
        # (1+2)-3 与 (2+1)-3 是同一道题
        self.assertEqual(
            canonical_key(BinOp("-", BinOp("+", num(1), num(2)), num(3))),
            canonical_key(BinOp("-", BinOp("+", num(2), num(1)), num(3))),
        )

    def test_key_is_hashable(self):
        self.assertEqual(len({canonical_key(num(1)), canonical_key(num(1))}), 1)


class RenderTests(unittest.TestCase):
    def test_plain_chain_has_no_parentheses(self):
        expr = BinOp("+", BinOp("+", num(1), num(2)), num(3))
        self.assertEqual(render(expr), "1 + 2 + 3")

    def test_lower_precedence_left_child_gets_parentheses(self):
        expr = BinOp("*", BinOp("+", num(1), num(2)), num(3))
        self.assertEqual(render(expr), "(1 + 2) × 3")

    def test_lower_precedence_right_child_gets_parentheses(self):
        expr = BinOp("*", num(3), BinOp("+", num(1), num(2)))
        self.assertEqual(render(expr), "3 × (1 + 2)")

    def test_higher_precedence_left_child_has_no_parentheses(self):
        expr = BinOp("+", BinOp("*", num(1), num(2)), num(3))
        self.assertEqual(render(expr), "1 × 2 + 3")

    def test_higher_precedence_right_child_has_no_parentheses(self):
        expr = BinOp("+", num(1), BinOp("*", num(2), num(3)))
        self.assertEqual(render(expr), "1 + 2 × 3")

    def test_same_precedence_left_child_has_no_parentheses(self):
        expr = BinOp("-", BinOp("-", num(1), num(2)), num(3))
        self.assertEqual(render(expr), "1 - 2 - 3")

    def test_same_precedence_right_child_gets_parentheses(self):
        expr = BinOp("-", num(1), BinOp("-", num(2), num(3)))
        self.assertEqual(render(expr), "1 - (2 - 3)")

    def test_division_chain(self):
        expr = BinOp("/", BinOp("/", num(1), num(2)), num(3))
        self.assertEqual(render(expr), "1 ÷ 2 ÷ 3")

    def test_division_by_product_gets_parentheses(self):
        expr = BinOp("/", num(1), BinOp("*", num(2), num(3)))
        self.assertEqual(render(expr), "1 ÷ (2 × 3)")

    def test_fraction_operands_use_fraction_notation(self):
        expr = BinOp("+", num(Fraction(1, 2)), num(Fraction(3, 4)))
        self.assertEqual(render(expr), "1/2 + 3/4")

    def test_mixed_number_operand(self):
        expr = BinOp("/", num(Fraction(19, 8)), num(3))
        self.assertEqual(render(expr), "2’3/8 ÷ 3")


class LegalityTests(unittest.TestCase):
    def test_legal_operand_values_for_r_10(self):
        values = legal_operand_values(10)
        self.assertIn(Fraction(0), values)
        self.assertIn(Fraction(9), values)
        self.assertIn(Fraction(1, 2), values)
        self.assertIn(Fraction(8, 9), values)
        self.assertNotIn(Fraction(10), values)
        self.assertNotIn(Fraction(3, 2), values)
        self.assertNotIn(Fraction(1, 10), values)

    def test_r_1_has_only_zero(self):
        self.assertEqual(legal_operand_values(1), frozenset({Fraction(0)}))

    def test_r_2_has_no_fractions(self):
        self.assertEqual(legal_operand_values(2), frozenset({Fraction(0), Fraction(1)}))

    def test_legal_expression(self):
        self.assertTrue(is_legal(BinOp("+", num(1), num(3)), 10))

    def test_sum_reaching_r_is_illegal(self):
        self.assertFalse(is_legal(BinOp("+", num(8), num(9)), 10))

    def test_negative_difference_is_illegal(self):
        self.assertFalse(is_legal(BinOp("-", num(3), num(5)), 10))

    def test_product_reaching_r_is_illegal(self):
        self.assertFalse(is_legal(BinOp("*", num(4), num(3)), 10))
        self.assertTrue(is_legal(BinOp("*", num(2), num(4)), 10))

    def test_division_must_yield_proper_fraction(self):
        self.assertFalse(is_legal(BinOp("/", num(6), num(2)), 10))
        self.assertFalse(is_legal(BinOp("/", num(3), num(2)), 10))
        self.assertFalse(is_legal(BinOp("/", num(0), num(3)), 10))
        self.assertTrue(is_legal(BinOp("/", num(1), num(3)), 10))
        self.assertTrue(
            is_legal(BinOp("/", num(Fraction(1, 2)), num(Fraction(3, 4))), 10)
        )

    def test_improper_fraction_operand_is_illegal(self):
        self.assertFalse(is_legal(BinOp("+", num(Fraction(3, 2)), num(1)), 10))

    def test_nested_violation_is_caught(self):
        # 内层 8+9 已经越界
        expr = BinOp("*", BinOp("+", num(8), num(9)), num(0))
        self.assertFalse(is_legal(expr, 10))


class OperatorCountTests(unittest.TestCase):
    def test_leaf_has_none(self):
        self.assertEqual(operator_count(num(1)), 0)

    def test_single_operator(self):
        self.assertEqual(operator_count(BinOp("+", num(1), num(2))), 1)

    def test_nested(self):
        expr = BinOp("+", num(1), BinOp("*", num(2), num(3)))
        self.assertEqual(operator_count(expr), 2)


if __name__ == "__main__":
    unittest.main()

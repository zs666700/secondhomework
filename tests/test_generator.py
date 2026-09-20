"""生成器：不变量、可复现性、题目耗尽。"""

import random
import unittest

from four_ops.expression import BinOp, Num, canonical_key, evaluate, operator_count, render
from four_ops.generator import MAX_OPERATORS, generate


def iter_subexpressions(expr):
    """深度优先产出表达式自身与它的所有子表达式。"""
    yield expr
    if isinstance(expr, BinOp):
        yield from iter_subexpressions(expr.left)
        yield from iter_subexpressions(expr.right)


def all_divisions(expr):
    return [
        node
        for node in iter_subexpressions(expr)
        if isinstance(node, BinOp) and node.op == "/"
    ]


def all_fraction_leaves(expr):
    return [
        node
        for node in iter_subexpressions(expr)
        if isinstance(node, Num) and node.value.denominator != 1
    ]


class GenerateInvariantTests(unittest.TestCase):
    def test_respects_requested_count(self):
        result = generate(10, 50, random.Random(1))
        self.assertEqual(len(result.problems), 50)
        self.assertFalse(result.exhausted)
        self.assertEqual(result.requested, 50)

    def test_problems_are_unique(self):
        result = generate(10, 500, random.Random(2))
        keys = [canonical_key(problem.expr) for problem in result.problems]
        self.assertEqual(len(keys), len(set(keys)))

    def test_operator_count_within_limit(self):
        result = generate(10, 300, random.Random(3))
        for problem in result.problems:
            with self.subTest(text=problem.text):
                count = operator_count(problem.expr)
                self.assertGreaterEqual(count, 1)
                self.assertLessEqual(count, MAX_OPERATORS)

    def test_all_values_stay_in_range(self):
        r = 10
        result = generate(r, 300, random.Random(4))
        for problem in result.problems:
            for sub in iter_subexpressions(problem.expr):
                value = evaluate(sub)
                with self.subTest(text=problem.text, sub=render(sub)):
                    self.assertGreaterEqual(value, 0)
                    self.assertLess(value, r)

    def test_division_always_yields_proper_fraction(self):
        for seed in range(5):
            result = generate(10, 200, random.Random(seed))
            for problem in result.problems:
                for node in all_divisions(problem.expr):
                    quotient = evaluate(node)
                    with self.subTest(seed=seed, text=problem.text):
                        self.assertGreater(quotient, 0)
                        self.assertLess(quotient, 1)

    def test_division_does_occur(self):
        total = sum(
            len(all_divisions(problem.expr))
            for seed in range(5)
            for problem in generate(10, 200, random.Random(seed)).problems
        )
        self.assertGreater(total, 0, "1000 道题里至少应出现一道除法题")

    def test_fraction_operands_do_occur(self):
        has_fraction = any(
            all_fraction_leaves(problem.expr)
            for problem in generate(10, 200, random.Random(7)).problems
        )
        self.assertTrue(has_fraction, "样本中应出现真分数操作数")

    def test_answer_matches_expression(self):
        result = generate(10, 100, random.Random(8))
        for problem in result.problems:
            with self.subTest(text=problem.text):
                self.assertEqual(problem.answer, evaluate(problem.expr))

    def test_text_matches_rendered_expression(self):
        result = generate(10, 100, random.Random(9))
        for problem in result.problems:
            with self.subTest(text=problem.text):
                self.assertEqual(problem.text, f"{render(problem.expr)} =")


class GenerateReproducibilityTests(unittest.TestCase):
    def test_same_seed_gives_same_problems(self):
        first = generate(10, 30, random.Random(42))
        second = generate(10, 30, random.Random(42))
        self.assertEqual(
            [problem.text for problem in first.problems],
            [problem.text for problem in second.problems],
        )

    def test_different_seeds_give_different_problems(self):
        first = generate(10, 30, random.Random(1))
        second = generate(10, 30, random.Random(2))
        self.assertNotEqual(
            [problem.text for problem in first.problems],
            [problem.text for problem in second.problems],
        )


class GenerateExhaustionTests(unittest.TestCase):
    # r=1 时操作数只有 0，一道题的差异只可能来自树形与运算符。运算符个数为 k 时
    # 有 4^k 种运算符组合、二叉树形分别有 1/2/5 种，故题目总数的上界是
    # 1*4 + 2*16 + 5*64 = 356 道（规范键还会把其中一些合并，实际更少）。
    # 所以请求 5000 道必然触发耗尽；请求 100 道则有可能真的凑够，断言会不稳定。
    def test_r_1_cannot_fill_many_problems(self):
        result = generate(1, 5000, random.Random(11))
        self.assertTrue(result.exhausted)
        self.assertLess(len(result.problems), 5000)
        self.assertGreaterEqual(len(result.problems), 1)

    def test_r_1_problems_are_still_unique(self):
        result = generate(1, 5000, random.Random(11))
        keys = [canonical_key(problem.expr) for problem in result.problems]
        self.assertEqual(len(keys), len(set(keys)))

    def test_r_2_never_produces_division(self):
        result = generate(2, 20, random.Random(12))
        for problem in result.problems:
            with self.subTest(text=problem.text):
                self.assertEqual(all_divisions(problem.expr), [])

    def test_r_3_can_still_produce_problems(self):
        result = generate(3, 20, random.Random(13))
        self.assertGreater(len(result.problems), 0)


if __name__ == "__main__":
    unittest.main()

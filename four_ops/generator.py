"""生成不重复的四则运算题目。

策略是自底向上随机合并：先撒 k+1 个叶子，再合并 k 次。每次合并只在**满足约束的
候选**里挑，而不是先随便造一个再校验丢弃，所以命中率高。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction

from four_ops.expression import (
    DIVIDE,
    MINUS,
    PLUS,
    TIMES,
    BinOp,
    Expr,
    Num,
    canonical_key,
    evaluate,
    render,
)

#: 每道题的运算符个数范围
MIN_OPERATORS = 1
MAX_OPERATORS = 3

#: 取操作数时，是「真分数」而不是「自然数」的概率
FRACTION_RATIO = 0.4

#: 连续失败多少次就判定题目空间已耗尽。取规格 §6 指定的 200000——这个信号的价值
#: 在于可信，调小它会让生成器过早宣告耗尽、少出题（实测 r=3 时少 2 道）。
MAX_STALL = 200_000


@dataclass(frozen=True)
class Problem:
    """一道题：表达式树、题面文本（含末尾等号）、答案。"""

    expr: Expr
    text: str
    answer: Fraction


@dataclass(frozen=True)
class GenerationResult:
    """一次生成的结果。exhausted 为真表示没能凑够 requested 道。"""

    problems: list
    requested: int
    exhausted: bool


def random_operand(r: int, rng: random.Random) -> Fraction:
    """随机取一个合法操作数：自然数 0..r-1，或真分数（分子 < 分母 < r）。"""
    if r >= 3 and rng.random() < FRACTION_RATIO:
        denominator = rng.randint(2, r - 1)
        numerator = rng.randint(1, denominator - 1)
        return Fraction(numerator, denominator)
    return Fraction(rng.randint(0, r - 1))


def merge_candidates(left: Expr, right: Expr, r: int) -> list:
    """列出把 left、right 合并成一次运算的所有合法方案。

    返回 [(op, 左, 右, 结果值), ...]。减法和除法会同时考虑两个方向，
    但用 >= / > 的严格性保证 a==b 时不会产生重复候选。
    """
    left_value = evaluate(left)
    right_value = evaluate(right)
    candidates = []

    if left_value + right_value < r:
        candidates.append((PLUS, left, right, left_value + right_value))
    if left_value >= right_value:
        candidates.append((MINUS, left, right, left_value - right_value))
    if right_value > left_value:
        candidates.append((MINUS, right, left, right_value - left_value))
    if 0 < left_value < right_value:
        candidates.append((DIVIDE, left, right, left_value / right_value))
    if 0 < right_value < left_value:
        candidates.append((DIVIDE, right, left, right_value / left_value))
    if left_value * right_value < r:
        candidates.append((TIMES, left, right, left_value * right_value))

    return candidates


def build(r: int, rng: random.Random):
    """尝试构造一个满足约束的表达式；中途卡住则返回 None。"""
    operator_total = rng.randint(MIN_OPERATORS, MAX_OPERATORS)
    nodes: list = [Num(random_operand(r, rng)) for _ in range(operator_total + 1)]

    for _ in range(operator_total):
        first, second = rng.sample(range(len(nodes)), 2)
        candidates = merge_candidates(nodes[first], nodes[second], r)
        if not candidates:
            return None
        op, left, right, _ = rng.choice(candidates)
        merged = BinOp(op, left, right)
        # 先删下标大的，免得删掉小的之后大的下标失效
        for index in sorted((first, second), reverse=True):
            nodes.pop(index)
        nodes.append(merged)

    return nodes[0]


def generate(r: int, count: int, rng: random.Random | None = None) -> GenerationResult:
    """生成 count 道互不重复的题目。

    若在 r 范围内可选题目已耗尽（连续 MAX_STALL 次都没拿到新的），提前返回，
    并把 exhausted 置为 True——绝不死循环。
    """
    if rng is None:
        rng = random.Random()

    problems: list = []
    seen: set = set()
    stall = 0

    while len(problems) < count and stall < MAX_STALL:
        expr = build(r, rng)
        if expr is None:
            stall += 1
            continue
        key = canonical_key(expr)
        if key in seen:
            stall += 1
            continue
        seen.add(key)
        problems.append(
            Problem(expr=expr, text=f"{render(expr)} =", answer=evaluate(expr))
        )
        stall = 0

    return GenerationResult(
        problems=problems, requested=count, exhausted=len(problems) < count
    )

"""表达式树：构造、求值、合法性校验、规范键、渲染。"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Union

from four_ops.fraction_util import format_fraction

PLUS = "+"
MINUS = "-"
TIMES = "*"
DIVIDE = "/"

#: 渲染时用的运算符字符
DISPLAY_OP = {PLUS: "+", MINUS: "-", TIMES: "×", DIVIDE: "÷"}

#: 运算符优先级，用于决定是否加括号
PRECEDENCE = {PLUS: 1, MINUS: 1, TIMES: 2, DIVIDE: 2}


@dataclass(frozen=True)
class Num:
    """叶子节点：一个自然数或真分数。"""

    value: Fraction


@dataclass(frozen=True)
class BinOp:
    """内部节点：一次二元运算。"""

    op: str
    left: "Expr"
    right: "Expr"


Expr = Union[Num, BinOp]


def evaluate(expr: Expr) -> Fraction:
    """求值。不校验 §4.1 的约束——判分模式要能算出任意合法算式的值。"""
    if isinstance(expr, Num):
        return expr.value
    left = evaluate(expr.left)
    right = evaluate(expr.right)
    if expr.op == PLUS:
        return left + right
    if expr.op == MINUS:
        return left - right
    if expr.op == TIMES:
        return left * right
    if expr.op == DIVIDE:
        if right == 0:
            raise ZeroDivisionError("除数不能为零")
        return left / right
    raise ValueError(f"未知运算符: {expr.op!r}")


def operator_count(expr: Expr) -> int:
    """表达式中运算符的个数。"""
    if isinstance(expr, Num):
        return 0
    return 1 + operator_count(expr.left) + operator_count(expr.right)


def legal_operand_values(r: int) -> frozenset:
    """给定 r 时所有合法的操作数：自然数 0..r-1，以及真分数（分子 < 分母 < r）。"""
    values = {Fraction(n) for n in range(r)}
    for denominator in range(2, r):
        for numerator in range(1, denominator):
            values.add(Fraction(numerator, denominator))
    return frozenset(values)


def is_legal(expr: Expr, r: int) -> bool:
    """检查表达式是否满足生成约束：操作数合法、中间结果与答案都在 [0, r)。"""
    operands = legal_operand_values(r)

    def check(node: Expr) -> bool:
        if isinstance(node, Num):
            return node.value in operands
        if not (check(node.left) and check(node.right)):
            return False
        left = evaluate(node.left)
        right = evaluate(node.right)
        if node.op == PLUS:
            return left + right < r
        if node.op == MINUS:
            return left >= right
        if node.op == TIMES:
            return left * right < r
        if node.op == DIVIDE:
            return 0 < left < right
        return False

    return check(expr)


def canonical_key(expr: Expr):
    """去重用的规范键。

    需求只允许交换 + 和 × 的左右操作数，**不允许重新结合**，所以不能把加法链
    展平排序——那会把 1+2+3 和 3+2+1 误判成同一道题。这里的做法是：+ 和 × 的
    两个子键排序，- 和 ÷ 保持左右有序。
    """
    if isinstance(expr, Num):
        return ("n", expr.value)
    left = canonical_key(expr.left)
    right = canonical_key(expr.right)
    if expr.op in (PLUS, TIMES) and right < left:
        left, right = right, left
    return (expr.op, left, right)


def render(expr: Expr) -> str:
    """渲染成最小括号的表达式文本。"""
    if isinstance(expr, Num):
        return format_fraction(expr.value)

    precedence = PRECEDENCE[expr.op]

    left = render(expr.left)
    if isinstance(expr.left, BinOp) and PRECEDENCE[expr.left.op] < precedence:
        left = f"({left})"

    # 运算符左结合，右子节点同级时必须加括号才能保持语义
    right = render(expr.right)
    if isinstance(expr.right, BinOp) and PRECEDENCE[expr.right.op] <= precedence:
        right = f"({right})"

    return f"{left} {DISPLAY_OP[expr.op]} {right}"

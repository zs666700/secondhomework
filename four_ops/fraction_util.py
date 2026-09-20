"""分数文本与 Fraction 之间的相互转换。

输出格式遵循需求：
    真分数五分之三 -> "3/5"
    真分数二又八分之三 -> "2’3/8"（分隔符是 U+2019）
"""

from __future__ import annotations

import re
from fractions import Fraction

# 带分数分隔符：U+2019 是需求原文用的字符，另外两个是手写时常见的替代
_MIXED_RE = re.compile(r"^(\d+)['’`](\d+)/(\d+)$")
_FRACTION_RE = re.compile(r"^(\d+)/(\d+)$")
_INTEGER_RE = re.compile(r"^\d+$")


def format_fraction(value: Fraction) -> str:
    """把 Fraction 格式化成需求要求的文本。

    整数直接输出；真分数输出 "分子/分母"；假分数输出带分数 "整数’分子/分母"。
    负号整体前置——生成模式不会产生负数，该分支只为判分模式容错。
    """
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    if magnitude.denominator == 1:
        return f"{sign}{magnitude.numerator}"
    if magnitude < 1:
        return f"{sign}{magnitude.numerator}/{magnitude.denominator}"
    whole = magnitude.numerator // magnitude.denominator
    remainder = magnitude.numerator % magnitude.denominator
    return f"{sign}{whole}’{remainder}/{magnitude.denominator}"


def parse_fraction(text: str) -> Fraction:
    """把文本解析成 Fraction，失败抛 ValueError。

    接受整数 "42"、分数 "3/5"、"19/8"、带分数 "2’3/8"（三种引号都认），
    以及它们前面的正负号。
    """
    body = text.strip()
    if not body:
        raise ValueError("空的分数文本")

    sign = 1
    if body[0] in "+-":
        if body[0] == "-":
            sign = -1
        body = body[1:].strip()

    mixed = _MIXED_RE.match(body)
    if mixed:
        whole, numerator, denominator = (int(group) for group in mixed.groups())
        if denominator == 0:
            raise ValueError(f"分母不能为零: {text!r}")
        return sign * Fraction(whole * denominator + numerator, denominator)

    fraction = _FRACTION_RE.match(body)
    if fraction:
        numerator, denominator = (int(group) for group in fraction.groups())
        if denominator == 0:
            raise ValueError(f"分母不能为零: {text!r}")
        return sign * Fraction(numerator, denominator)

    if _INTEGER_RE.match(body):
        return sign * Fraction(int(body))

    raise ValueError(f"无法解析为数值: {text!r}")

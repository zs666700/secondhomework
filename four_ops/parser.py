"""把表达式文本解析成表达式树。

文法（左结合）：
    expr   := term (('+' | '-') term)*
    term   := factor (('×' | '*') factor)*
    factor := NUMBER | '(' expr ')'

NUMBER 的词法是一整块：整数、分数或带分数。
关键点：'/' 不作为除号，只作为分数的一部分，这样 "1/2 + 3/4" 里的 '/' 就没有歧义。
"""

from __future__ import annotations

import re

from four_ops.expression import BinOp, Expr, Num
from four_ops.fraction_util import parse_fraction

#: 数字记号：整数、带分数（三种引号）、分数
_NUMBER_RE = re.compile(r"\d+(?:['’`]\d+/\d+|/\d+)?")

#: 文本运算符 -> 内部运算符
_OPERATOR_CHARS = {
    "+": "+",
    "-": "-",
    "−": "-",  # − 减号
    "–": "-",  # – 短破折号
    "*": "*",
    "×": "*",  # × 乘号
    "÷": "/",  # ÷ 除号
}

_ADDITIVE = ("+", "-")
_MULTIPLICATIVE = ("*", "/")


class ExpressionSyntaxError(ValueError):
    """表达式文本不符合文法。"""


class Token:
    """词法记号。kind ∈ {"num", "op", "(", ")"}。"""

    __slots__ = ("kind", "text")

    def __init__(self, kind: str, text: str) -> None:
        self.kind = kind
        self.text = text

    def __repr__(self) -> str:
        return f"Token({self.kind!r}, {self.text!r})"


def tokenize(text: str) -> list:
    """把文本切成记号列表，遇到无法识别的字符抛 ExpressionSyntaxError。"""
    tokens = []
    position = 0
    length = len(text)
    while position < length:
        char = text[position]
        if char.isspace():
            position += 1
            continue
        if char in "()":
            tokens.append(Token(char, char))
            position += 1
            continue
        if char in _OPERATOR_CHARS:
            tokens.append(Token("op", _OPERATOR_CHARS[char]))
            position += 1
            continue
        match = _NUMBER_RE.match(text, position)
        if match:
            tokens.append(Token("num", match.group()))
            position = match.end()
            continue
        raise ExpressionSyntaxError(f"无法识别的字符 {char!r}（位置 {position}）")
    return tokens


class _Parser:
    def __init__(self, tokens: list, source: str) -> None:
        self.tokens = tokens
        self.source = source
        self.position = 0

    def _peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def parse_expr(self) -> Expr:
        node = self.parse_term()
        while True:
            token = self._peek()
            if token is not None and token.kind == "op" and token.text in _ADDITIVE:
                self.position += 1
                node = BinOp(token.text, node, self.parse_term())
            else:
                return node

    def parse_term(self) -> Expr:
        node = self.parse_factor()
        while True:
            token = self._peek()
            if (
                token is not None
                and token.kind == "op"
                and token.text in _MULTIPLICATIVE
            ):
                self.position += 1
                node = BinOp(token.text, node, self.parse_factor())
            else:
                return node

    def parse_factor(self) -> Expr:
        token = self._peek()
        if token is None:
            raise ExpressionSyntaxError(f"表达式意外结束: {self.source!r}")
        if token.kind == "(":
            self.position += 1
            node = self.parse_expr()
            closing = self._peek()
            if closing is None or closing.kind != ")":
                raise ExpressionSyntaxError(f"括号未闭合: {self.source!r}")
            self.position += 1
            return node
        if token.kind == "num":
            self.position += 1
            return Num(parse_fraction(token.text))
        raise ExpressionSyntaxError(f"意外的记号 {token.text!r}: {self.source!r}")


def parse_expression(text: str) -> Expr:
    """解析表达式文本，失败抛 ExpressionSyntaxError。"""
    tokens = tokenize(text)
    if not tokens:
        raise ExpressionSyntaxError("表达式为空")
    parser = _Parser(tokens, text)
    expr = parser.parse_expr()
    if parser.position != len(tokens):
        remaining = tokens[parser.position].text
        raise ExpressionSyntaxError(f"表达式在 {remaining!r} 处有多余内容: {text!r}")
    return expr

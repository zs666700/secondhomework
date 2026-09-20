"""判分：读题目文件与答案文件，逐题比对，产出 Grade.txt 的内容。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from four_ops.expression import evaluate
from four_ops.fraction_util import parse_fraction
from four_ops.parser import ExpressionSyntaxError, parse_expression


@dataclass(frozen=True)
class GradeResult:
    """判分结果。correct / wrong 里存的是题号（从 1 开始）。"""

    correct: list
    wrong: list
    total: int
    warnings: list = field(default_factory=list)


def format_grade_line(label: str, ids: list) -> str:
    joined = ", ".join(str(identifier) for identifier in ids)
    return f"{label}: {len(ids)} ({joined})"


def format_grade(result: GradeResult) -> str:
    """按需求格式输出两行统计。"""
    return (
        format_grade_line("Correct", result.correct)
        + "\n"
        + format_grade_line("Wrong", result.wrong)
        + "\n"
    )


def _read_non_blank_lines(path: Path) -> list:
    # utf-8-sig 而不是 utf-8：Windows 记事本、PowerShell 的 Set-Content -Encoding UTF8
    # 都会给文件加 BOM。带 BOM 时第一行会读成 "﻿2/3"，导致第 1 题恒被判错。
    # utf-8-sig 在无 BOM 时与 utf-8 完全等价，所以自家生成的文件不受影响。
    text = path.read_text(encoding="utf-8-sig")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _strip_equals(line: str) -> str:
    if line.endswith("="):
        return line[:-1].strip()
    return line


def grade(exercise_path: Path, answer_path: Path) -> GradeResult:
    """比对题目文件与答案文件。

    空行一律跳过，题号按非空行的顺序从 1 开始。答案不足的题计错，
    多出来的答案忽略并记一条警告。
    """
    exercise_lines = _read_non_blank_lines(Path(exercise_path))
    answer_lines = _read_non_blank_lines(Path(answer_path))

    warnings: list = []
    if len(answer_lines) > len(exercise_lines):
        warnings.append(
            f"答案文件有 {len(answer_lines)} 行，题目文件只有 {len(exercise_lines)} 行，"
            "多余的作答被忽略。"
        )

    correct: list = []
    wrong: list = []

    for index, line in enumerate(exercise_lines, start=1):
        source = _strip_equals(line)
        try:
            expected = evaluate(parse_expression(source))
        except (ExpressionSyntaxError, ZeroDivisionError, ValueError) as error:
            warnings.append(f"第 {index} 题无法解析（{error}），计为错误：{line!r}")
            wrong.append(index)
            continue

        if index > len(answer_lines):
            warnings.append(f"第 {index} 题缺少作答，计为错误。")
            wrong.append(index)
            continue

        raw_answer = answer_lines[index - 1]
        try:
            given = parse_fraction(raw_answer)
        except ValueError as error:
            warnings.append(
                f"第 {index} 题作答无法解析（{error}），计为错误：{raw_answer!r}"
            )
            wrong.append(index)
            continue

        if given == expected:
            correct.append(index)
        else:
            wrong.append(index)

    return GradeResult(
        correct=correct, wrong=wrong, total=len(exercise_lines), warnings=warnings
    )

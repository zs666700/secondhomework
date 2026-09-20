"""命令行入口：参数校验、模式分派、文件读写。

这是唯一做 I/O 的模块。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from four_ops.fraction_util import format_fraction
from four_ops.generator import generate
from four_ops.grader import format_grade, grade

PROG = "Myapp.py"

EXERCISE_FILE = "Exercises.txt"
ANSWER_FILE = "Answers.txt"
GRADE_FILE = "Grade.txt"

DEFAULT_COUNT = 10

EPILOG = """\
示例:
  python myapp.py -n 10 -r 10                     生成 10 道 10 以内的题目
  python myapp.py -r 20                           生成 10 道 20 以内的题目
  python myapp.py -e Exercises.txt -a Answers.txt 判分
"""


class UsageError(Exception):
    """命令行参数不合法。"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="小学四则运算题目生成器",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-n", type=int, default=None, metavar="N",
        help=f"生成题目的个数，默认 {DEFAULT_COUNT}",
    )
    parser.add_argument(
        "-r", type=int, default=None, metavar="R",
        help="题目中数值的范围上界（不含），生成模式下必须给定",
    )
    parser.add_argument(
        "-e", default=None, metavar="exercisefile",
        help="题目文件，与 -a 一起用于判分",
    )
    parser.add_argument(
        "-a", default=None, metavar="answerfile",
        help="答案文件，与 -e 一起用于判分",
    )
    return parser


def validate(args: argparse.Namespace) -> None:
    """校验参数组合，不合法抛 UsageError。"""
    grading = args.e is not None or args.a is not None
    if grading:
        if args.e is None or args.a is None:
            raise UsageError("-e 和 -a 必须同时给定")
        if args.n is not None or args.r is not None:
            raise UsageError("判分模式（-e / -a）不能与 -n / -r 同时使用")
        return

    if args.r is None:
        raise UsageError("生成模式必须用 -r 给定数值范围")
    if args.r < 1:
        raise UsageError(f"-r 必须是自然数（>= 1），收到 {args.r}")
    if args.n is not None and args.n < 1:
        raise UsageError(f"-n 必须是正整数（>= 1），收到 {args.n}")


def _run_generate(args: argparse.Namespace) -> int:
    count = DEFAULT_COUNT if args.n is None else args.n
    result = generate(args.r, count)

    cwd = Path.cwd()
    exercise_path = cwd / EXERCISE_FILE
    answer_path = cwd / ANSWER_FILE

    exercise_path.write_text(
        "".join(f"{problem.text}\n" for problem in result.problems), encoding="utf-8"
    )
    answer_path.write_text(
        "".join(f"{format_fraction(problem.answer)}\n" for problem in result.problems),
        encoding="utf-8",
    )

    produced = len(result.problems)
    print(f"已生成 {produced} 道题目 -> {exercise_path}")
    print(f"已生成 {produced} 个答案 -> {answer_path}")

    if result.exhausted:
        print(
            f"错误：在 -r {args.r} 范围内无法生成 {count} 道不重复的题目，"
            f"实际生成 {produced} 道。",
            file=sys.stderr,
        )
        return 1
    return 0


def _run_grade(args: argparse.Namespace) -> int:
    exercise_path = Path(args.e)
    answer_path = Path(args.a)
    for path in (exercise_path, answer_path):
        if not path.is_file():
            print(f"错误：文件不存在 {path}", file=sys.stderr)
            return 2

    # grade() 内部用 Path.read_text 读文件：文件存在也不代表读得动——可能是
    # GBK（Windows 记事本存的中文）或读取途中的竞态。让它冒出去就是崩溃，而
    # 需求要求文件错误一律 stderr 报错 + 退出码 2。
    try:
        result = grade(exercise_path, answer_path)
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"错误：无法读取 {exercise_path} 或 {answer_path}（{error}）",
            file=sys.stderr,
        )
        return 2

    grade_path = Path.cwd() / GRADE_FILE
    grade_path.write_text(format_grade(result), encoding="utf-8")

    for warning in result.warnings:
        print(f"警告：{warning}", file=sys.stderr)

    print(f"判分完成：对 {len(result.correct)} 题，错 {len(result.wrong)} 题 -> {grade_path}")
    return 0


def main(argv=None) -> int:
    """程序入口，返回退出码。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        validate(args)
    except UsageError as error:
        print(f"错误：{error}", file=sys.stderr)
        print(file=sys.stderr)
        parser.print_help(sys.stderr)
        return 2

    if args.e is not None:
        return _run_grade(args)
    return _run_generate(args)

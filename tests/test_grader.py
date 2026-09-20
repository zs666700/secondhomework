"""判分：比对题目与答案，生成 Grade.txt 的内容。"""

import tempfile
import unittest
from pathlib import Path

from four_ops.grader import GradeResult, format_grade, grade


class GraderTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write(self, name, lines):
        path = self.tmp / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def write_with_bom(self, name, lines):
        """模拟 Windows 记事本 / PowerShell Set-Content -Encoding UTF8 存盘的结果。"""
        path = self.tmp / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
        return path


class GradeTests(GraderTestCase):
    def test_all_correct(self):
        exercise = self.write("Exercises.txt", ["1 + 2 =", "3/4 + 1/4 ="])
        answer = self.write("Answers.txt", ["3", "1"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [1, 2])
        self.assertEqual(result.wrong, [])
        self.assertEqual(result.total, 2)

    def test_all_wrong(self):
        exercise = self.write("Exercises.txt", ["1 + 2 =", "1 + 3 ="])
        answer = self.write("Answers.txt", ["4", "9"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [])
        self.assertEqual(result.wrong, [1, 2])

    def test_partial(self):
        exercise = self.write("Exercises.txt", ["1 + 2 =", "1 + 3 =", "1 + 4 ="])
        answer = self.write("Answers.txt", ["3", "0", "5"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [1, 3])
        self.assertEqual(result.wrong, [2])

    def test_fraction_answer_from_spec(self):
        # 需求原文：1/6 + 1/8 = 7/24
        exercise = self.write("Exercises.txt", ["1/6 + 1/8 ="])
        answer = self.write("Answers.txt", ["7/24"])
        self.assertEqual(grade(exercise, answer).correct, [1])

    def test_mixed_number_answer(self):
        exercise = self.write("Exercises.txt", ["3/8 + 1/4 + 1 ="])
        answer = self.write("Answers.txt", ["1’5/8"])
        self.assertEqual(grade(exercise, answer).correct, [1])

    def test_equivalent_answer_forms_are_accepted(self):
        exercise = self.write("Exercises.txt", ["3/8 + 1/4 + 1 ="])
        for form in ("1’5/8", "1'5/8", "13/8"):
            with self.subTest(form=form):
                answer = self.write("Answers.txt", [form])
                self.assertEqual(grade(exercise, answer).correct, [1])

    def test_blank_lines_are_skipped(self):
        exercise = self.write("Exercises.txt", ["1 + 2 =", "", "   ", "1 + 3 ="])
        answer = self.write("Answers.txt", ["3", "4"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [1, 2])
        self.assertEqual(result.total, 2)

    def test_missing_answer_counts_as_wrong(self):
        exercise = self.write("Exercises.txt", ["1 + 2 =", "1 + 3 ="])
        answer = self.write("Answers.txt", ["3"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [1])
        self.assertEqual(result.wrong, [2])
        self.assertTrue(result.warnings)

    def test_extra_answers_are_ignored_with_warning(self):
        exercise = self.write("Exercises.txt", ["1 + 2 ="])
        answer = self.write("Answers.txt", ["3", "99"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [1])
        self.assertTrue(result.warnings)

    def test_unparsable_answer_counts_as_wrong(self):
        exercise = self.write("Exercises.txt", ["1 + 2 ="])
        answer = self.write("Answers.txt", ["不知道"])
        result = grade(exercise, answer)
        self.assertEqual(result.wrong, [1])
        self.assertTrue(result.warnings)

    def test_unparsable_exercise_counts_as_wrong(self):
        exercise = self.write("Exercises.txt", ["1 + + 2 ="])
        answer = self.write("Answers.txt", ["3"])
        result = grade(exercise, answer)
        self.assertEqual(result.wrong, [1])
        self.assertTrue(result.warnings)

    def test_line_without_trailing_equals_still_works(self):
        exercise = self.write("Exercises.txt", ["1 + 2"])
        answer = self.write("Answers.txt", ["3"])
        self.assertEqual(grade(exercise, answer).correct, [1])

    def test_answer_file_with_utf8_bom(self):
        # 记事本 / PowerShell 存盘会加 BOM。不剥离时第一行会读成 "﻿3"，
        # 解析失败，第 1 题被恒判错。
        exercise = self.write("Exercises.txt", ["1 + 2 =", "1 + 3 ="])
        answer = self.write_with_bom("Answers.txt", ["3", "4"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [1, 2])
        self.assertEqual(result.wrong, [])
        self.assertEqual(result.warnings, [])

    def test_exercise_file_with_utf8_bom(self):
        exercise = self.write_with_bom("Exercises.txt", ["1 + 2 =", "1 + 3 ="])
        answer = self.write("Answers.txt", ["3", "4"])
        result = grade(exercise, answer)
        self.assertEqual(result.correct, [1, 2])
        self.assertEqual(result.wrong, [])
        self.assertEqual(result.warnings, [])


class FormatGradeTests(unittest.TestCase):
    def test_matches_required_layout(self):
        result = GradeResult(
            correct=[1, 3, 5, 7, 9], wrong=[2, 4, 6, 8, 10], total=10, warnings=[]
        )
        self.assertEqual(
            format_grade(result),
            "Correct: 5 (1, 3, 5, 7, 9)\nWrong: 5 (2, 4, 6, 8, 10)\n",
        )

    def test_empty_category_uses_empty_parentheses(self):
        result = GradeResult(correct=[1], wrong=[], total=1, warnings=[])
        self.assertEqual(format_grade(result), "Correct: 1 (1)\nWrong: 0 ()\n")

    def test_all_wrong(self):
        result = GradeResult(correct=[], wrong=[1, 2], total=2, warnings=[])
        self.assertEqual(format_grade(result), "Correct: 0 ()\nWrong: 2 (1, 2)\n")


if __name__ == "__main__":
    unittest.main()

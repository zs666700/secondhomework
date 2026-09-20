"""命令行：参数校验与端到端流程。"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from four_ops import cli


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


class CliValidationTests(unittest.TestCase):
    def test_generate_without_r_is_usage_error(self):
        code, _, err = run_cli(["-n", "5"])
        self.assertEqual(code, 2)
        self.assertIn("-r", err)

    def test_r_zero_is_usage_error(self):
        code, _, err = run_cli(["-r", "0"])
        self.assertEqual(code, 2)
        self.assertIn("-r", err)

    def test_r_negative_is_usage_error(self):
        code, _, err = run_cli(["-r", "-3"])
        self.assertEqual(code, 2)
        self.assertIn("-r", err)

    def test_n_zero_is_usage_error(self):
        code, _, err = run_cli(["-n", "0", "-r", "10"])
        self.assertEqual(code, 2)
        self.assertIn("-n", err)

    def test_e_without_a_is_usage_error(self):
        code, _, _ = run_cli(["-e", "Exercises.txt"])
        self.assertEqual(code, 2)

    def test_a_without_e_is_usage_error(self):
        code, _, _ = run_cli(["-a", "Answers.txt"])
        self.assertEqual(code, 2)

    def test_mixing_modes_is_usage_error(self):
        code, _, _ = run_cli(
            ["-e", "Exercises.txt", "-a", "Answers.txt", "-r", "10"]
        )
        self.assertEqual(code, 2)

    def test_missing_grade_input_file_is_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.txt"
            other = Path(tmp) / "nope2.txt"
            code, _, err = run_cli(["-e", str(missing), "-a", str(other)])
        self.assertEqual(code, 2)
        self.assertIn("不存在", err)

    def test_undecodable_exercise_file_is_reported_not_raised(self):
        """文件存在但不是 UTF-8（这里是 GBK）时，报错退出而不是抛异常。"""
        # 注意纯 ASCII 内容的 GBK 文件与 UTF-8 兼容，触发不了这条分支——必须带
        # 一个非 ASCII 字符。U+2019（带分数分隔符）在 GBK 里编码为 0xA1 0xAF，
        # 不是合法的 UTF-8 序列。
        with tempfile.TemporaryDirectory() as tmp:
            exercise = Path(tmp) / "Exercises.txt"
            answer = Path(tmp) / "Answers.txt"
            exercise.write_bytes("1 + 2 =\n2’1/2\n".encode("gbk"))
            answer.write_text("3\n7/2\n", encoding="utf-8")
            code, _, err = run_cli(["-e", str(exercise), "-a", str(answer)])
        self.assertEqual(code, 2)
        self.assertIn("错误", err)
        self.assertIn("Exercises.txt", err)

    def test_help_is_printed_on_usage_error(self):
        _, _, err = run_cli([])
        self.assertIn("usage", err.lower())


class CliEndToEndTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._previous_cwd = Path.cwd()
        os.chdir(self._tmp.name)
        self.addCleanup(os.chdir, str(self._previous_cwd))

    def read(self, name):
        return Path(name).read_text(encoding="utf-8").splitlines()

    def test_generate_creates_both_files_with_requested_count(self):
        code, _, _ = run_cli(["-n", "30", "-r", "10"])
        self.assertEqual(code, 0)
        self.assertEqual(len(self.read("Exercises.txt")), 30)
        self.assertEqual(len(self.read("Answers.txt")), 30)

    def test_generate_defaults_to_ten_problems(self):
        code, _, _ = run_cli(["-r", "10"])
        self.assertEqual(code, 0)
        self.assertEqual(len(self.read("Exercises.txt")), 10)

    def test_every_exercise_line_ends_with_equals(self):
        run_cli(["-n", "20", "-r", "10"])
        for line in self.read("Exercises.txt"):
            self.assertTrue(line.endswith(" ="), line)

    def test_generated_problem_texts_are_unique(self):
        run_cli(["-n", "50", "-r", "10"])
        lines = self.read("Exercises.txt")
        self.assertEqual(len(lines), len(set(lines)))

    def test_generate_then_grade_all_correct(self):
        run_cli(["-n", "30", "-r", "10"])
        code, _, _ = run_cli(["-e", "Exercises.txt", "-a", "Answers.txt"])
        self.assertEqual(code, 0)
        grade_text = Path("Grade.txt").read_text(encoding="utf-8")
        self.assertTrue(grade_text.startswith("Correct: 30 ("), grade_text)
        self.assertIn("Wrong: 0 ()", grade_text)

    def test_grade_detects_a_deliberate_mistake(self):
        run_cli(["-n", "5", "-r", "10"])
        answers = self.read("Answers.txt")
        answers[2] = "999999"
        Path("Answers.txt").write_text("\n".join(answers) + "\n", encoding="utf-8")
        code, _, _ = run_cli(["-e", "Exercises.txt", "-a", "Answers.txt"])
        self.assertEqual(code, 0)
        grade_text = Path("Grade.txt").read_text(encoding="utf-8")
        self.assertIn("Wrong: 1 (3)", grade_text)

    # r=1 的题目总数上界是 356 道（见 test_generator 里的推导），请求 5000 道必然耗尽
    def test_exhaustion_returns_exit_code_one(self):
        code, _, err = run_cli(["-n", "5000", "-r", "1"])
        self.assertEqual(code, 1)
        self.assertIn("实际生成", err)

    def test_exhaustion_still_writes_partial_files(self):
        run_cli(["-n", "5000", "-r", "1"])
        self.assertGreater(len(self.read("Exercises.txt")), 0)


if __name__ == "__main__":
    unittest.main()

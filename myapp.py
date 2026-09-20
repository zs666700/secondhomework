#!/usr/bin/env python3
"""小学四则运算题目生成器 —— 命令行入口。

用法:
    python myapp.py -n 10 -r 10                      生成题目与答案
    python myapp.py -e Exercises.txt -a Answers.txt  判分
"""

import sys

from four_ops.cli import main

if __name__ == "__main__":
    sys.exit(main())

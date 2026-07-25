"""ATK 自然语言二次开发代码生成 Demo 的命令行入口。"""

from __future__ import annotations

import argparse

from src.demo_runner import DEFAULT_REQUEST, run_demo


def build_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="将自然语言任务转换为受约束的 ATK Connect Python 二次开发代码。"
    )
    parser.add_argument(
        "request",
        nargs="?",
        help="用户输入的自然语言任务描述。",
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="使用内置示例请求运行 Demo。",
    )
    return parser


def main() -> None:
    """解析用户输入并启动演示流程。"""
    arguments = build_parser().parse_args()
    request = DEFAULT_REQUEST if arguments.example else arguments.request

    if not request:
        raise SystemExit("请提供自然语言任务，或使用 --example。")

    result = run_demo(request)
    print(result)


if __name__ == "__main__":
    main()

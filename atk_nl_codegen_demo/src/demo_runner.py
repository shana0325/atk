"""串联自然语言解析、校验、代码生成和自主验证流程。"""

from __future__ import annotations

import json
from pathlib import Path

from .code_generator import generate_connect_code
from .nlp_parser import parse_natural_language
from .validators import build_execution_plan, validate_task
from .verifier import build_validation_report, verify_generated_code


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "connect_inclination_change.py.j2"
GENERATED_DIR = PROJECT_ROOT / "generated"

DEFAULT_REQUEST = (
    "创建一个倾角改变轨道机动规划场景，从2022年11月5日开始，"
    "初始轨道半长轴6570000米，偏心率0，倾角28度，"
    "先抬升远地点到42160000米，再圆化轨道，最后在升交点把倾角降到0度，并运行MCS。"
)


def run_demo(request: str) -> str:
    """运行完整 Dry Run Demo，并把结果写入 generated 目录。"""
    GENERATED_DIR.mkdir(exist_ok=True)

    task = parse_natural_language(request)
    task_errors, task_warnings = validate_task(task)
    execution_plan = build_execution_plan(task)
    generated_code = generate_connect_code(task, TEMPLATE_PATH)
    code_passed, code_failed = verify_generated_code(task, generated_code)
    validation_report = build_validation_report(
        task=task,
        task_errors=task_errors,
        task_warnings=task_warnings,
        code_passed=code_passed,
        code_failed=code_failed,
    )

    write_text("structured_task.json", json.dumps(task.to_dict(), ensure_ascii=False, indent=2))
    write_text("execution_plan.md", execution_plan)
    write_text("generated_connect_inclination_change.py", generated_code)
    write_text("validation_report.md", validation_report)

    status = "通过" if not task_errors and not code_failed else "存在问题"
    return "\n".join(
        [
            "ATK 自然语言二次开发代码生成 Demo 已完成。",
            f"验证状态：{status}",
            "",
            "已生成文件：",
            str(GENERATED_DIR / "structured_task.json"),
            str(GENERATED_DIR / "execution_plan.md"),
            str(GENERATED_DIR / "generated_connect_inclination_change.py"),
            str(GENERATED_DIR / "validation_report.md"),
        ]
    )


def write_text(filename: str, content: str) -> None:
    """以 UTF-8 编码写入生成结果。"""
    (GENERATED_DIR / filename).write_text(content + "\n", encoding="utf-8")

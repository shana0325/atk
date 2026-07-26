"""串联自然语言解析、校验、代码生成和自主验证流程。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .code_generator import generate_connect_code
from .nlp_parser import TASK_TYPE_OPTIONS, parse_natural_language
from .time_interpreter import apply_time_understanding, interpret_time_with_deepseek
from .validators import build_execution_plan, validate_task
from .verifier import build_validation_report, verify_generated_code


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = PROJECT_ROOT / "generated"
TEMPLATE_PATHS = {
    "inclination_change_transfer": PROJECT_ROOT / "templates" / "connect_inclination_change.py.j2",
    "single_satellite_orbit": PROJECT_ROOT / "templates" / "connect_single_satellite_orbit.py.j2",
}
GENERATED_FILENAMES = {
    "inclination_change_transfer": "generated_connect_inclination_change.py",
    "single_satellite_orbit": "generated_connect_single_satellite_orbit.py",
    "satellite_orbit_visualization": "generated_connect_satellite_orbit_visualization.py",
    "ground_facility_setup": "generated_connect_ground_facility_setup.py",
    "satellite_facility_access": "generated_connect_satellite_facility_access.py",
}

DEFAULT_REQUEST = (
    "创建一个倾角改变轨道机动规划场景，从2022年11月5日开始，"
    "初始轨道半长轴6570000米，偏心率0，倾角28度，"
    "先抬升远地点到42160000米，再圆化轨道，最后在升交点把倾角降到0度，并运行MCS。"
)


def run_demo_artifacts(request: str, task_type: str = "auto") -> dict[str, Any]:
    """运行完整 Dry Run Demo，并返回网页可展示的结构化结果。"""
    GENERATED_DIR.mkdir(exist_ok=True)

    task = parse_natural_language(request, task_type=task_type)
    time_understanding = interpret_time_with_deepseek(request, task.intent)
    task = apply_time_understanding(task, time_understanding)
    task_errors, task_warnings = validate_task(task)
    execution_plan = build_execution_plan(task)
    template_path = get_template_path(task.intent)
    generated_filename = get_generated_filename(task.intent)
    generated_code = generate_connect_code(task, template_path)
    code_passed, code_failed = verify_generated_code(task, generated_code)
    validation_report = build_validation_report(
        task=task,
        task_errors=task_errors,
        task_warnings=task_warnings,
        code_passed=code_passed,
        code_failed=code_failed,
    )

    task_dict = task.to_dict()
    status = "通过" if not task_errors and not code_failed else "存在问题"
    clarification = build_clarification_prompt(task_dict)

    write_text("structured_task.json", json.dumps(task_dict, ensure_ascii=False, indent=2))
    write_text("execution_plan.md", execution_plan)
    write_text(generated_filename, generated_code)
    write_text("generated_connect_latest.py", generated_code)
    write_text("validation_report.md", validation_report)

    return {
        "status": status,
        "request": request,
        "structured_task": task_dict,
        "execution_plan": execution_plan,
        "generated_code": generated_code,
        "validation_report": validation_report,
        "time_understanding": time_understanding,
        "task_errors": task_errors,
        "task_warnings": task_warnings,
        "code_passed": code_passed,
        "code_failed": code_failed,
        "clarification": clarification,
        "files": {
            "structured_task": str(GENERATED_DIR / "structured_task.json"),
            "execution_plan": str(GENERATED_DIR / "execution_plan.md"),
            "generated_code": str(GENERATED_DIR / generated_filename),
            "latest_generated_code": str(GENERATED_DIR / "generated_connect_latest.py"),
            "validation_report": str(GENERATED_DIR / "validation_report.md"),
        },
    }


def run_demo(request: str, task_type: str = "auto") -> str:
    """运行 Demo 并返回命令行摘要。"""
    artifacts = run_demo_artifacts(request, task_type=task_type)
    return "\n".join(
        [
            "ATK 自然语言二次开发代码生成 Demo 已完成。",
            f"验证状态：{artifacts['status']}",
            "",
            "已生成文件：",
            artifacts["files"]["structured_task"],
            artifacts["files"]["execution_plan"],
            artifacts["files"]["generated_code"],
            artifacts["files"]["validation_report"],
        ]
    )


def build_clarification_prompt(task_dict: dict[str, Any]) -> dict[str, Any]:
    """生成预留追问信息，供后续多轮交互使用。"""
    missing_fields = task_dict.get("missing_fields", [])
    assumptions = task_dict.get("assumptions", [])
    questions: list[str] = []

    if missing_fields:
        questions.append("以下字段没有明确识别，请补充或确认：" + "、".join(missing_fields))
    if assumptions:
        questions.append("系统使用了默认假设，请确认这些默认值是否符合你的意图。")
    if not questions:
        questions.append("当前任务参数较完整，暂不需要追问。")

    return {
        "enabled": False,
        "note": "当前版本预留追问区，尚未实现多轮对话状态机。",
        "questions": questions,
        "assumptions": assumptions,
        "missing_fields": missing_fields,
    }


def get_template_path(intent: str) -> Path:
    """根据任务类型选择受控代码模板。"""
    return TEMPLATE_PATHS.get(intent, PROJECT_ROOT / "templates" / "command_list_builder")


def get_generated_filename(intent: str) -> str:
    """根据任务类型选择生成文件名。"""
    if intent not in GENERATED_FILENAMES:
        raise ValueError(f"未配置生成文件名：{intent}")
    return GENERATED_FILENAMES[intent]


def write_text(filename: str, content: str) -> None:
    """以 UTF-8 编码写入生成结果。"""
    (GENERATED_DIR / filename).write_text(content + "\n", encoding="utf-8")

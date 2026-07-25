"""验证生成的 ATK Connect 代码是否满足任务模板要求。"""

from __future__ import annotations

from .models import StructuredTask


REQUIRED_SNIPPETS = {
    "建立 Connect 连接": "atkOpen",
    "创建场景": "New\", \"/ Scenario",
    "创建卫星": "New\", \"/ Satellite",
    "设置分析时间": "SetAnalysisTimePeriod",
    "启用 Astrogator": "SetProp",
    "插入预报段": "InsertSegment MainSequence.SegmentList.- Propagate",
    "插入瞄准序列": "InsertSegment MainSequence.SegmentList.- Target_Sequence",
    "插入机动段": "SegmentList.- Maneuver",
    "设置初始半长轴": "Keplerian.sma",
    "设置初始偏心率": "Keplerian.ecc",
    "设置初始倾角": "Keplerian.inc",
    "设置远地点约束": "StateCalcRadiusOfApoapsis",
    "设置偏心率约束": "StateCalcEccentricity",
    "设置倾角约束": "StateCalcInclination",
    "运行 MCS": "RunMCS",
    "关闭连接": "atkClose",
}


def verify_generated_code(task: StructuredTask, code: str) -> tuple[list[str], list[str]]:
    """检查生成代码中是否包含必要命令和参数。"""
    passed: list[str] = []
    failed: list[str] = []

    for label, snippet in REQUIRED_SNIPPETS.items():
        if snippet in code:
            passed.append(label)
        else:
            failed.append(label)

    parameter_checks = {
        f"场景名 {task.scenario_name}": task.scenario_name,
        f"卫星名 {task.satellite_name}": task.satellite_name,
        f"初始半长轴 {format_number(task.initial_orbit.sma.value)}": format_number(task.initial_orbit.sma.value),
        f"目标远地点 {format_number(task.targets.apoapsis_radius.value)}": format_number(task.targets.apoapsis_radius.value),
        f"目标倾角 {format_number(task.targets.final_inclination.value)}": format_number(task.targets.final_inclination.value),
    }
    for label, expected_text in parameter_checks.items():
        if expected_text in code:
            passed.append(label)
        else:
            failed.append(label)

    return passed, failed


def format_number(value: float) -> str:
    """用普通十进制格式展示验证用数值。"""
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def build_validation_report(
    task: StructuredTask,
    task_errors: list[str],
    task_warnings: list[str],
    code_passed: list[str],
    code_failed: list[str],
) -> str:
    """生成 Markdown 格式的自主验证报告。"""
    lines = [
        "# ATK 二次开发代码自主验证报告",
        "",
        "## 任务识别",
        "",
        f"- 任务类型：`{task.intent}`",
        f"- 场景名称：`{task.scenario_name}`",
        f"- 卫星名称：`{task.satellite_name}`",
        f"- 原始输入：{task.source_text}",
        "",
        "## 参数假设",
        "",
    ]

    if task.assumptions:
        lines.extend(f"- ⚠️ {assumption}" for assumption in task.assumptions)
    else:
        lines.append("- ✅ 未使用默认假设。")

    lines.extend(["", "## 参数校验", ""])
    if task_errors:
        lines.extend(f"- ❌ {error}" for error in task_errors)
    else:
        lines.append("- ✅ 结构化任务参数校验通过。")

    if task_warnings:
        lines.extend(f"- ⚠️ {warning}" for warning in task_warnings)

    lines.extend(["", "## 代码流程验证", ""])
    lines.extend(f"- ✅ {item}" for item in code_passed)

    if code_failed:
        lines.extend(f"- ❌ 缺少：{item}" for item in code_failed)
    else:
        lines.append("- ✅ 生成代码包含所有关键步骤。")

    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- 当前验证类型：Dry Run / 代码级验证。",
            "- 真实执行前需要确认 ATK 已启动、Connect 端口已开启，并且当前 ATK 版本支持模板中的命令。",
        ]
    )
    return "\n".join(lines)

"""验证生成的 ATK Connect 代码是否满足任务模板要求。"""

from __future__ import annotations

from .models import StructuredTask


INCLINATION_CHANGE_REQUIRED_SNIPPETS = {
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

SINGLE_SATELLITE_REQUIRED_SNIPPETS = {
    "建立 Connect 连接": "atkOpen",
    "创建场景": "New\", \"/ Scenario",
    "创建卫星": "New\", \"/ Satellite",
    "设置分析时间": "SetAnalysisTimePeriod",
    "设置经典轨道": "SetState",
    "使用两体预报器": "Classical TwoBody",
    "重置动画": "Animate",
    "关闭连接": "atkClose",
}

SATELLITE_ORBIT_REQUIRED_SNIPPETS = {
    "建立 Connect 连接": "atkOpen",
    "创建场景": '"New"',
    "创建卫星": "*/Satellite",
    "设置经典轨道": '"SetState"',
    "使用两体预报器": "Classical TwoBody",
    "重置动画": '"Animate"',
    "关闭连接": "atkClose",
}

GROUND_FACILITY_REQUIRED_SNIPPETS = {
    "建立 Connect 连接": "atkOpen",
    "创建场景": '"New"',
    "创建地面站": "*/Facility",
    "设置地面站位置": '"SetPosition"',
    "使用地理坐标": "Geodetic",
    "关闭连接": "atkClose",
}

SATELLITE_FACILITY_ACCESS_REQUIRED_SNIPPETS = {
    **SATELLITE_ORBIT_REQUIRED_SNIPPETS,
    "创建地面站": "*/Facility",
    "设置地面站位置": '"SetPosition"',
    "计算可见性": '"Access"',
}


def verify_generated_code(task: StructuredTask, code: str) -> tuple[list[str], list[str]]:
    """检查生成代码中是否包含必要命令和参数。"""
    passed: list[str] = []
    failed: list[str] = []
    required_snippets = get_required_snippets(task.intent)

    for label, snippet in required_snippets.items():
        if snippet in code:
            passed.append(label)
        else:
            failed.append(label)

    parameter_checks = {
        f"场景名 {task.scenario_name}": task.scenario_name,
    }
    if task.satellite_name:
        parameter_checks[f"卫星名 {task.satellite_name}"] = task.satellite_name
    if task.intent == "inclination_change_transfer":
        parameter_checks[f"初始半长轴 {format_number(task.initial_orbit.sma.value)}"] = format_number(
            task.initial_orbit.sma.value
        )
    for satellite in task.satellites:
        parameter_checks[f"卫星名 {satellite.name}"] = satellite.name
        parameter_checks[f"{satellite.name} 半长轴 {format_number(satellite.sma.value)}"] = format_number(
            satellite.sma.value
        )
    for facility in task.facilities:
        parameter_checks[f"地面站名 {facility.name}"] = facility.name
    if task.targets:
        parameter_checks.update(
            {
                f"目标远地点 {format_number(task.targets.apoapsis_radius.value)}": format_number(
                    task.targets.apoapsis_radius.value
                ),
                f"目标倾角 {format_number(task.targets.final_inclination.value)}": format_number(
                    task.targets.final_inclination.value
                ),
            }
        )
    for label, expected_text in parameter_checks.items():
        if expected_text in code:
            passed.append(label)
        else:
            failed.append(label)

    return passed, failed


def get_required_snippets(intent: str) -> dict[str, str]:
    """根据任务类型返回代码验证片段。"""
    if intent == "single_satellite_orbit":
        return SINGLE_SATELLITE_REQUIRED_SNIPPETS
    if intent == "satellite_orbit_visualization":
        return SATELLITE_ORBIT_REQUIRED_SNIPPETS
    if intent == "ground_facility_setup":
        return GROUND_FACILITY_REQUIRED_SNIPPETS
    if intent == "satellite_facility_access":
        return SATELLITE_FACILITY_ACCESS_REQUIRED_SNIPPETS
    return INCLINATION_CHANGE_REQUIRED_SNIPPETS


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

    lines.extend(["", "## DeepSeek 时间理解", ""])
    time_understanding = task.time_understanding or {}
    if time_understanding.get("status") == "ok":
        lines.append(f"- ✅ 已启用：{time_understanding.get('explanation', '已抽取时间字段。')}")
        lines.append(f"- 置信度：`{time_understanding.get('confidence', 0)}`")
    elif time_understanding.get("status") == "skipped":
        lines.append(f"- ⚠️ 已跳过：{time_understanding.get('reason')}")
    elif time_understanding:
        lines.append(f"- ⚠️ 时间理解失败：{time_understanding.get('reason')}")
    else:
        lines.append("- ⚠️ 未记录时间理解结果。")

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

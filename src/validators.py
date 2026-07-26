"""校验结构化任务的完整性、参数范围和风险提示。"""

from __future__ import annotations

from .models import StructuredTask


SUPPORTED_INTENTS = {
    "inclination_change_transfer",
    "single_satellite_orbit",
    "satellite_orbit_visualization",
    "ground_facility_setup",
    "satellite_facility_access",
}


def validate_task(task: StructuredTask) -> tuple[list[str], list[str]]:
    """返回结构化任务的错误列表和警告列表。"""
    errors: list[str] = []
    warnings: list[str] = []

    if task.intent not in SUPPORTED_INTENTS:
        errors.append(f"不支持的任务类型：{task.intent}")

    if not task.scenario_name:
        errors.append("缺少场景名称。")
    if task.intent in {"inclination_change_transfer", "single_satellite_orbit"} and not task.satellite_name:
        errors.append("缺少卫星名称。")

    if task.intent in {"inclination_change_transfer", "single_satellite_orbit"} and task.initial_orbit.sma.unit != "m":
        errors.append("当前模板要求初始半长轴单位为 m。")
    if task.intent in {"inclination_change_transfer", "single_satellite_orbit"} and task.initial_orbit.sma.value <= 6_371_000:
        errors.append("初始半长轴应大于地球平均半径，当前值不合理。")

    if not 0 <= task.initial_orbit.ecc < 1:
        errors.append("初始偏心率应位于 [0, 1) 范围。")

    if not 0 <= task.initial_orbit.inc.value <= 180:
        errors.append("初始倾角应位于 [0, 180] 度范围。")

    if task.intent in {"satellite_orbit_visualization", "satellite_facility_access"}:
        if not task.satellites:
            errors.append("至少需要一颗卫星。")
        for satellite in task.satellites:
            if satellite.sma.value <= 6_371_000:
                errors.append(f"{satellite.name} 的半长轴应大于地球平均半径。")
            if not 0 <= satellite.ecc < 1:
                errors.append(f"{satellite.name} 的偏心率应位于 [0, 1) 范围。")
            if not 0 <= satellite.inc.value <= 180:
                errors.append(f"{satellite.name} 的倾角应位于 [0, 180] 度范围。")

    if task.intent in {"ground_facility_setup", "satellite_facility_access"}:
        if not task.facilities:
            errors.append("至少需要一个地面站。")
        for facility in task.facilities:
            if not -90 <= facility.latitude.value <= 90:
                errors.append(f"{facility.name} 的纬度应位于 [-90, 90] 度范围。")
            if not -180 <= facility.longitude.value <= 180:
                errors.append(f"{facility.name} 的经度应位于 [-180, 180] 度范围。")

    if task.intent == "inclination_change_transfer":
        if task.targets is None:
            errors.append("倾角改变转移任务缺少目标约束。")
        else:
            if task.targets.apoapsis_radius.unit != "m":
                errors.append("当前模板要求目标远地点半径单位为 m。")
            if task.targets.apoapsis_radius.value <= task.initial_orbit.sma.value:
                errors.append("目标远地点半径应大于初始半长轴。")

            if not 0 <= task.targets.final_eccentricity < 1:
                errors.append("目标偏心率应位于 [0, 1) 范围。")

            if not 0 <= task.targets.final_inclination.value <= 180:
                errors.append("目标倾角应位于 [0, 180] 度范围。")

    if task.missing_fields:
        warnings.append("存在未明确识别字段，当前使用了默认值或假设。")

    if task.mcs and task.mcs.run_after_generation:
        warnings.append("生成代码包含 RunMCS，真实执行前建议用户确认。")

    return errors, warnings


def build_execution_plan(task: StructuredTask) -> str:
    """生成用户可读的执行计划。"""
    if task.intent in {"single_satellite_orbit", "satellite_orbit_visualization"}:
        return build_satellite_orbit_visualization_plan(task)
    if task.intent == "ground_facility_setup":
        return build_ground_facility_setup_plan(task)
    if task.intent == "satellite_facility_access":
        return build_satellite_facility_access_plan(task)
    return build_inclination_change_transfer_plan(task)


def build_inclination_change_transfer_plan(task: StructuredTask) -> str:
    """生成倾角改变转移任务执行计划。"""
    targets = task.targets
    mcs = task.mcs
    if targets is None or mcs is None:
        return "当前任务缺少倾角改变转移模板必需字段，无法生成完整执行计划。"

    return "\n".join(
        [
            "# ATK 执行计划",
            "",
            f"任务类型：`{task.intent}`",
            f"场景名称：`{task.scenario_name}`",
            f"卫星名称：`{task.satellite_name}`",
            "",
            "系统将执行以下步骤：",
            "",
            "1. 连接本机 ATK，端口 6655。",
            f"2. 创建场景 `{task.scenario_name}`。",
            f"3. 创建卫星 `{task.satellite_name}`。",
            f"4. 设置分析时间：`{task.time_period.start}` 到 `{task.time_period.end}`。",
            "5. 将卫星轨道预报器设置为 Astrogator 机动规划。",
            (
                "6. 设置初始轨道："
                f"sma={task.initial_orbit.sma.value:g}m，"
                f"ecc={task.initial_orbit.ecc:g}，"
                f"inc={task.initial_orbit.inc.value:g}deg。"
            ),
            f"7. 第一组瞄准序列：远地点半径约束为 `{targets.apoapsis_radius.value:g}m`。",
            f"8. 第二组瞄准序列：偏心率约束为 `{targets.final_eccentricity:g}`。",
            (
                "9. 第三组瞄准序列："
                f"倾角约束为 `{targets.final_inclination.value:g}deg`，"
                f"偏心率约束为 `{targets.final_eccentricity:g}`。"
            ),
            f"10. 添加最终预报段，飞行时长 `{mcs.final_propagate_duration.value:g}sec`。",
            "11. 运行 MCS 并关闭 Connect 连接。",
        ]
    )


def build_satellite_orbit_visualization_plan(task: StructuredTask) -> str:
    """生成卫星轨道显示任务执行计划。"""
    satellite_lines = [
        f"- `{satellite.name}`：sma={satellite.sma.value:g}m，ecc={satellite.ecc:g}，inc={satellite.inc.value:g}deg"
        for satellite in task.satellites
    ]
    return "\n".join(
        [
            "# ATK 执行计划",
            "",
            f"任务类型：`{task.intent}`",
            f"场景名称：`{task.scenario_name}`",
            f"卫星数量：`{len(task.satellites)}`",
            "",
            "卫星参数：",
            "",
            *satellite_lines,
            "",
            "系统将执行以下步骤：",
            "",
            "1. 连接本机 ATK，端口 6655。",
            f"2. 创建场景 `{task.scenario_name}`。",
            "3. 按卫星列表逐个创建卫星对象。",
            f"4. 设置分析时间：`{task.time_period.start}` 到 `{task.time_period.end}`。",
            "5. 对每颗卫星使用 `SetState Classical` 设置经典轨道。",
            "6. 重置动画视图，显示一圈轨道预报效果。",
            "7. 关闭 Connect 连接。",
        ]
    )


def build_ground_facility_setup_plan(task: StructuredTask) -> str:
    """生成地面站创建任务执行计划。"""
    facility_lines = [
        f"- `{facility.name}`：lat={facility.latitude.value:g}deg，lon={facility.longitude.value:g}deg，alt={facility.altitude.value:g}m"
        for facility in task.facilities
    ]
    return "\n".join(
        [
            "# ATK 执行计划",
            "",
            f"任务类型：`{task.intent}`",
            f"场景名称：`{task.scenario_name}`",
            "",
            "地面站参数：",
            "",
            *facility_lines,
            "",
            "系统将执行以下步骤：",
            "",
            "1. 连接本机 ATK，端口 6655。",
            f"2. 创建场景 `{task.scenario_name}`。",
            "3. 创建地面站对象。",
            "4. 使用 `SetPosition Geodetic` 设置地面站经纬度和高度。",
            "5. 重置动画视图并关闭 Connect 连接。",
        ]
    )


def build_satellite_facility_access_plan(task: StructuredTask) -> str:
    """生成卫星-地面站可见性任务执行计划。"""
    return "\n".join(
        [
            build_satellite_orbit_visualization_plan(task),
            "",
            "## 可见性计算",
            "",
            f"- 地面站数量：`{len(task.facilities)}`",
            f"- 可见性对数量：`{len(task.access_pairs)}`",
            "- 使用 `Access <ObjectPath> <AccessObjectPath> TimePeriod <StartTime> <StopTime>` 计算。",
        ]
    )

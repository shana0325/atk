"""校验结构化任务的完整性、参数范围和风险提示。"""

from __future__ import annotations

from .models import StructuredTask


SUPPORTED_INTENTS = {"inclination_change_transfer"}


def validate_task(task: StructuredTask) -> tuple[list[str], list[str]]:
    """返回结构化任务的错误列表和警告列表。"""
    errors: list[str] = []
    warnings: list[str] = []

    if task.intent not in SUPPORTED_INTENTS:
        errors.append(f"不支持的任务类型：{task.intent}")

    if not task.scenario_name:
        errors.append("缺少场景名称。")
    if not task.satellite_name:
        errors.append("缺少卫星名称。")

    if task.initial_orbit.sma.unit != "m":
        errors.append("当前模板要求初始半长轴单位为 m。")
    if task.initial_orbit.sma.value <= 6_371_000:
        errors.append("初始半长轴应大于地球平均半径，当前值不合理。")

    if not 0 <= task.initial_orbit.ecc < 1:
        errors.append("初始偏心率应位于 [0, 1) 范围。")

    if not 0 <= task.initial_orbit.inc.value <= 180:
        errors.append("初始倾角应位于 [0, 180] 度范围。")

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

    if task.mcs.run_after_generation:
        warnings.append("生成代码包含 RunMCS，真实执行前建议用户确认。")

    return errors, warnings


def build_execution_plan(task: StructuredTask) -> str:
    """生成用户可读的执行计划。"""
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
            f"7. 第一组瞄准序列：远地点半径约束为 `{task.targets.apoapsis_radius.value:g}m`。",
            f"8. 第二组瞄准序列：偏心率约束为 `{task.targets.final_eccentricity:g}`。",
            (
                "9. 第三组瞄准序列："
                f"倾角约束为 `{task.targets.final_inclination.value:g}deg`，"
                f"偏心率约束为 `{task.targets.final_eccentricity:g}`。"
            ),
            f"10. 添加最终预报段，飞行时长 `{task.mcs.final_propagate_duration.value:g}sec`。",
            "11. 运行 MCS 并关闭 Connect 连接。",
        ]
    )

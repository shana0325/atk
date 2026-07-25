"""根据结构化任务生成 ATK Connect Python 代码。"""

from __future__ import annotations

from pathlib import Path

from .models import StructuredTask


def generate_connect_code(task: StructuredTask, template_path: Path) -> str:
    """使用受控模板生成 Connect Python 代码。"""
    template = template_path.read_text(encoding="utf-8")
    replacements = {
        "scenario_name": task.scenario_name,
        "satellite_name": task.satellite_name,
        "start_time": task.time_period.start,
        "end_time": task.time_period.end,
        "epoch": task.initial_orbit.epoch,
        "sma": format_number(task.initial_orbit.sma.value),
        "ecc": format_number(task.initial_orbit.ecc),
        "inc": format_number(task.initial_orbit.inc.value),
        "raan": format_number(task.initial_orbit.raan.value),
        "arg_perigee": format_number(task.initial_orbit.arg_perigee.value),
        "true_anomaly": format_number(task.initial_orbit.true_anomaly.value),
        "apoapsis_radius": format_number(task.targets.apoapsis_radius.value),
        "final_eccentricity": format_number(task.targets.final_eccentricity),
        "final_inclination": format_number(task.targets.final_inclination.value),
        "final_duration": format_number(task.mcs.final_propagate_duration.value),
    }

    generated_code = template
    for placeholder, value in replacements.items():
        generated_code = generated_code.replace("{{" + placeholder + "}}", value)
    return generated_code


def format_number(value: float) -> str:
    """格式化数值，避免整数参数出现多余小数点。"""
    if float(value).is_integer():
        return str(int(value))
    return str(value)

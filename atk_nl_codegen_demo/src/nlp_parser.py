"""将用户自然语言解析为受约束的 ATK 结构化任务。"""

from __future__ import annotations

import re

from .models import (
    InitialOrbit,
    McsSettings,
    Quantity,
    StructuredTask,
    TimePeriod,
    TransferTargets,
)


MONTH_MAP = {
    "1": "Jan",
    "01": "Jan",
    "2": "Feb",
    "02": "Feb",
    "3": "Mar",
    "03": "Mar",
    "4": "Apr",
    "04": "Apr",
    "5": "May",
    "05": "May",
    "6": "Jun",
    "06": "Jun",
    "7": "Jul",
    "07": "Jul",
    "8": "Aug",
    "08": "Aug",
    "9": "Sep",
    "09": "Sep",
    "10": "Oct",
    "11": "Nov",
    "12": "Dec",
}


def parse_natural_language(request: str) -> StructuredTask:
    """用规则版解析器演示自然语言到结构化任务的转换。"""
    normalized_request = request.strip()
    if not normalized_request:
        raise ValueError("任务描述不能为空。")

    missing_fields: list[str] = []
    assumptions: list[str] = []

    intent = detect_intent(normalized_request)
    if intent != "inclination_change_transfer":
        missing_fields.append("intent")
        assumptions.append("当前 Demo 仅支持倾角改变转移任务，已按该模板尝试解析。")

    scenario_name = extract_name(
        normalized_request,
        patterns=[r"场景(?:名|名称)?[为叫：:\s]*([A-Za-z_][A-Za-z0-9_]*)"],
        default="InclinationChange",
        assumptions=assumptions,
        assumption_text="未指定场景名，使用默认值 InclinationChange。",
    )
    satellite_name = extract_name(
        normalized_request,
        patterns=[r"卫星(?:名|名称)?[为叫：:\s]*([A-Za-z_][A-Za-z0-9_]*)"],
        default="SatInclinationChange",
        assumptions=assumptions,
        assumption_text="未指定卫星名，使用默认值 SatInclinationChange。",
    )

    start_time = extract_start_time(normalized_request)
    if not start_time:
        start_time = "5 Nov 2022 00:00:00.000"
        missing_fields.append("time_period.start")
        assumptions.append("未明确识别开始时间，使用案例默认值 5 Nov 2022 00:00:00.000。")

    end_time = extract_end_time(normalized_request)
    if not end_time:
        end_time = "8 Nov 2022 00:00:00.000"
        assumptions.append("未指定结束时间，使用案例默认值 8 Nov 2022 00:00:00.000。")

    semi_major_axis = extract_number_with_keywords(
        normalized_request,
        keywords=["半长轴", "sma", "初始轨道"],
        default=6570000,
        assumptions=assumptions,
        assumption_text="未识别初始半长轴，使用案例默认值 6570000 m。",
    )
    eccentricity = extract_number_with_keywords(
        normalized_request,
        keywords=["偏心率", "ecc"],
        default=0,
        assumptions=assumptions,
        assumption_text="未识别初始偏心率，使用案例默认值 0。",
    )
    initial_inclination = extract_initial_inclination(normalized_request)
    if initial_inclination is None:
        initial_inclination = 28
        assumptions.append("未识别初始倾角，使用案例默认值 28 deg。")
    apoapsis_radius = extract_number_with_keywords(
        normalized_request,
        keywords=["远地点"],
        default=42160000,
        assumptions=assumptions,
        assumption_text="未识别目标远地点半径，使用案例默认值 42160000 m。",
    )
    final_inclination = extract_final_inclination(normalized_request)
    if final_inclination is None:
        final_inclination = 0
        assumptions.append("未识别最终倾角，使用案例默认值 0 deg。")

    return StructuredTask(
        intent="inclination_change_transfer",
        scenario_name=scenario_name,
        satellite_name=satellite_name,
        time_period=TimePeriod(start=start_time, end=end_time),
        initial_orbit=InitialOrbit(
            coordinate_type="Modified Keplerian",
            epoch=f"{start_time} UTCG",
            sma=Quantity(value=semi_major_axis, unit="m"),
            ecc=eccentricity,
            inc=Quantity(value=initial_inclination, unit="deg"),
            raan=Quantity(value=0, unit="deg"),
            arg_perigee=Quantity(value=0, unit="deg"),
            true_anomaly=Quantity(value=0, unit="deg"),
        ),
        targets=TransferTargets(
            apoapsis_radius=Quantity(value=apoapsis_radius, unit="m"),
            final_eccentricity=0,
            final_inclination=Quantity(value=final_inclination, unit="deg"),
        ),
        mcs=McsSettings(
            run_after_generation=True,
            final_propagate_duration=Quantity(value=129600, unit="sec"),
        ),
        source_text=normalized_request,
        missing_fields=missing_fields,
        assumptions=assumptions,
    )


def detect_intent(request: str) -> str:
    """识别当前 Demo 支持的任务意图。"""
    intent_keywords = ["倾角改变", "倾角", "变轨", "转移", "GEO", "geo", "远地点"]
    if any(keyword in request for keyword in intent_keywords):
        return "inclination_change_transfer"
    return "unknown"


def extract_name(
    request: str,
    patterns: list[str],
    default: str,
    assumptions: list[str],
    assumption_text: str,
) -> str:
    """按规则提取英文对象名。"""
    for pattern in patterns:
        match = re.search(pattern, request)
        if match:
            return match.group(1)
    assumptions.append(assumption_text)
    return default


def extract_start_time(request: str) -> str | None:
    """提取中文日期并转换为 ATK 常用时间字符串。"""
    match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", request)
    if not match:
        return None
    year, month, day = match.groups()
    month_name = MONTH_MAP.get(month)
    if not month_name:
        return None
    return f"{int(day)} {month_name} {year} 00:00:00.000"


def extract_end_time(request: str) -> str | None:
    """当前规则版暂不主动解析结束时间。"""
    match = re.search(r"结束(?:时间)?[为是到：:\s]*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", request)
    if not match:
        return None
    year, month, day = match.groups()
    month_name = MONTH_MAP.get(month)
    if not month_name:
        return None
    return f"{int(day)} {month_name} {year} 00:00:00.000"


def extract_number_with_keywords(
    request: str,
    keywords: list[str],
    default: float,
    assumptions: list[str],
    assumption_text: str,
) -> float:
    """从关键词附近提取数字，支持米和千米的简单单位转换。"""
    for keyword in keywords:
        pattern = rf"{keyword}[^0-9负零一二三四五六七八九十百千万亿-]*(-?\d+(?:\.\d+)?)\s*(km|KM|千米|公里|m|米|度|deg)?"
        match = re.search(pattern, request)
        if not match:
            continue
        value = float(match.group(1))
        unit = match.group(2) or ""
        if unit in {"km", "KM", "千米", "公里"}:
            return value * 1000
        return value

    assumptions.append(assumption_text)
    return float(default)


def extract_initial_inclination(request: str) -> float | None:
    """提取初始倾角，避免把“倾角改变”误识别为数值字段。"""
    patterns = [
        r"倾角从\s*(-?\d+(?:\.\d+)?)\s*(?:度|deg)?",
        r"初始[^，。；]*?倾角(?:为|是|=|：|:)?\s*(-?\d+(?:\.\d+)?)\s*(?:度|deg)?",
        r"倾角(?:为|是|=|：|:)\s*(-?\d+(?:\.\d+)?)\s*(?:度|deg)?",
        r"倾角\s*(-?\d+(?:\.\d+)?)\s*(?:度|deg)?",
        r"inc(?:为|是|=|：|:)?\s*(-?\d+(?:\.\d+)?)\s*(?:度|deg)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def extract_final_inclination(request: str) -> float | None:
    """提取最终倾角目标。"""
    patterns = [
        r"倾角(?:降到|降为|变为|到|为)\s*(-?\d+(?:\.\d+)?)\s*(?:度|deg)?",
        r"最终倾角[^0-9-]*(-?\d+(?:\.\d+)?)\s*(?:度|deg)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, request)
        if match:
            return float(match.group(1))
    return None

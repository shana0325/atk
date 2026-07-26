"""将用户自然语言解析为受约束的 ATK 结构化任务。"""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta

from .models import (
    AccessPairSpec,
    FacilitySpec,
    InitialOrbit,
    McsSettings,
    Quantity,
    SatelliteOrbitSpec,
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


TASK_TYPE_OPTIONS = [
    {
        "id": "satellite_orbit_visualization",
        "label": "卫星轨道显示",
        "description": "创建一颗或多颗卫星，设置经典轨道，并显示约一圈轨道。",
        "sample": "创建两颗卫星绕地球转一圈，高度分别为500km和800km，倾角分别为45度和60度。",
    },
    {
        "id": "ground_facility_setup",
        "label": "地面站创建",
        "description": "创建地面站并设置经纬度、高度。",
        "sample": "创建一个北京地面站，纬度39.9度，经度116.4度，高度50米。",
    },
    {
        "id": "satellite_facility_access",
        "label": "卫星-地面站可见性",
        "description": "创建卫星和地面站，并计算二者在分析时间内的可见性。",
        "sample": "创建一颗高度500km倾角45度的卫星和一个北京地面站，计算它们之间的可见性。",
    },
    {
        "id": "inclination_change_transfer",
        "label": "倾角改变转移",
        "description": "使用 Astrogator 生成低轨到目标轨道的倾角改变机动规划。",
        "sample": "创建一个倾角改变轨道机动规划场景，从2022年11月5日开始，初始轨道半长轴6570000米，偏心率0，倾角28度，先抬升远地点到42160000米，再圆化轨道，最后把倾角降到0度。",
    },
]


def parse_natural_language(request: str, task_type: str = "auto") -> StructuredTask:
    """用规则版解析器演示自然语言到结构化任务的转换。"""
    normalized_request = request.strip()
    if not normalized_request:
        raise ValueError("任务描述不能为空。")

    intent = detect_intent(normalized_request) if task_type == "auto" else task_type
    if intent == "single_satellite_orbit":
        intent = "satellite_orbit_visualization"
    if intent == "satellite_orbit_visualization":
        return parse_satellite_orbit_visualization(normalized_request)
    if intent == "ground_facility_setup":
        return parse_ground_facility_setup(normalized_request)
    if intent == "satellite_facility_access":
        return parse_satellite_facility_access(normalized_request)
    if intent == "inclination_change_transfer":
        return parse_inclination_change_transfer(normalized_request)

    raise ValueError("当前无法把这句话可靠映射到已有任务模板，请换一种说法，或先选择支持的任务类型。")


def parse_inclination_change_transfer(request: str) -> StructuredTask:
    """解析倾角改变转移任务。"""
    missing_fields: list[str] = []
    assumptions: list[str] = []

    scenario_name = extract_name(
        request,
        patterns=[r"场景(?:名|名称)?[为叫：:\s]*([A-Za-z_][A-Za-z0-9_]*)"],
        default="InclinationChange",
        assumptions=assumptions,
        assumption_text="未指定场景名，使用默认值 InclinationChange。",
    )
    satellite_name = extract_name(
        request,
        patterns=[r"卫星(?:名|名称)?[为叫：:\s]*([A-Za-z_][A-Za-z0-9_]*)"],
        default="SatInclinationChange",
        assumptions=assumptions,
        assumption_text="未指定卫星名，使用默认值 SatInclinationChange。",
    )

    start_time = extract_start_time(request)
    if not start_time:
        start_time = "5 Nov 2022 00:00:00.000"
        missing_fields.append("time_period.start")
        assumptions.append("未明确识别开始时间，使用案例默认值 5 Nov 2022 00:00:00.000。")

    end_time = extract_end_time(request)
    if not end_time:
        end_time = "8 Nov 2022 00:00:00.000"
        assumptions.append("未指定结束时间，使用案例默认值 8 Nov 2022 00:00:00.000。")

    semi_major_axis = extract_number_with_keywords(
        request,
        keywords=["半长轴", "sma", "初始轨道"],
        default=6570000,
        assumptions=assumptions,
        assumption_text="未识别初始半长轴，使用案例默认值 6570000 m。",
    )
    eccentricity = extract_number_with_keywords(
        request,
        keywords=["偏心率", "ecc"],
        default=0,
        assumptions=assumptions,
        assumption_text="未识别初始偏心率，使用案例默认值 0。",
    )
    initial_inclination = extract_initial_inclination(request)
    if initial_inclination is None:
        initial_inclination = 28
        assumptions.append("未识别初始倾角，使用案例默认值 28 deg。")
    apoapsis_radius = extract_number_with_keywords(
        request,
        keywords=["远地点"],
        default=42160000,
        assumptions=assumptions,
        assumption_text="未识别目标远地点半径，使用案例默认值 42160000 m。",
    )
    final_inclination = extract_final_inclination(request)
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
        source_text=request,
        missing_fields=missing_fields,
        assumptions=assumptions,
    )


def parse_single_satellite_orbit(request: str) -> StructuredTask:
    """解析单卫星绕地显示任务。"""
    return parse_satellite_orbit_visualization(request)


def parse_satellite_orbit_visualization(request: str) -> StructuredTask:
    """解析一颗或多颗卫星绕地显示任务。"""
    missing_fields: list[str] = []
    assumptions: list[str] = []

    scenario_name = extract_name(
        request,
        patterns=[r"场景(?:名|名称)?[为叫：:\s]*([A-Za-z_][A-Za-z0-9_]*)"],
        default="SatelliteOrbitVisualization",
        assumptions=assumptions,
        assumption_text="未指定场景名，使用默认值 SatelliteOrbitVisualization。",
    )
    satellite_count = extract_satellite_count(request)
    satellite_names = extract_object_names(request, prefix="Sat", count=satellite_count)

    start_time = extract_start_time(request)
    if not start_time:
        start_time = "5 Nov 2022 00:00:00.000"
        missing_fields.append("time_period.start")
        assumptions.append("未明确识别开始时间，使用默认值 5 Nov 2022 00:00:00.000。")

    satellites = build_satellite_specs(request, satellite_names, assumptions)
    first_satellite = satellites[0]

    end_time = extract_end_time(request)
    if not end_time:
        duration_seconds = estimate_orbital_period_seconds(first_satellite.sma.value)
        end_time = add_seconds_to_atk_time(start_time, duration_seconds)
        assumptions.append(f"未指定结束时间，按半长轴估算一圈约 {duration_seconds:.0f} 秒。")

    return StructuredTask(
        intent="satellite_orbit_visualization",
        scenario_name=scenario_name,
        satellite_name=first_satellite.name,
        time_period=TimePeriod(start=start_time, end=end_time),
        initial_orbit=InitialOrbit(
            coordinate_type="Classical",
            epoch=start_time,
            sma=first_satellite.sma,
            ecc=first_satellite.ecc,
            inc=first_satellite.inc,
            raan=first_satellite.raan,
            arg_perigee=first_satellite.arg_perigee,
            true_anomaly=first_satellite.mean_anomaly,
        ),
        targets=None,
        mcs=None,
        source_text=request,
        missing_fields=missing_fields,
        assumptions=assumptions,
        satellites=satellites,
    )


def parse_ground_facility_setup(request: str) -> StructuredTask:
    """解析地面站创建任务。"""
    missing_fields: list[str] = []
    assumptions: list[str] = []
    scenario_name = extract_name(
        request,
        patterns=[r"场景(?:名|名称)?[为叫：:\s]*([A-Za-z_][A-Za-z0-9_]*)"],
        default="GroundFacilitySetup",
        assumptions=assumptions,
        assumption_text="未指定场景名，使用默认值 GroundFacilitySetup。",
    )
    start_time = extract_start_time(request) or "5 Nov 2022 00:00:00.000"
    end_time = extract_end_time(request) or "6 Nov 2022 00:00:00.000"
    facility = build_facility_spec(request, assumptions)

    return build_simple_task(
        intent="ground_facility_setup",
        scenario_name=scenario_name,
        source_text=request,
        time_period=TimePeriod(start=start_time, end=end_time),
        assumptions=assumptions,
        missing_fields=missing_fields,
        facilities=[facility],
    )


def parse_satellite_facility_access(request: str) -> StructuredTask:
    """解析卫星和地面站可见性分析任务。"""
    base_task = parse_satellite_orbit_visualization(request)
    base_task.intent = "satellite_facility_access"
    base_task.facilities = [build_facility_spec(request, base_task.assumptions)]
    base_task.access_pairs = [
        AccessPairSpec(
            from_object=f"*/Satellite/{base_task.satellites[0].name}",
            to_object=f"*/Facility/{base_task.facilities[0].name}",
        )
    ]
    return base_task


def detect_intent(request: str) -> str:
    """识别当前 Demo 支持的任务意图。"""
    transfer_keywords = ["倾角改变", "变轨", "转移", "GEO", "geo", "远地点", "圆化", "MCS"]
    orbit_keywords = ["单卫星", "一颗卫星", "转一圈", "绕一圈", "绕地", "绕地球", "跑一圈", "飞一圈"]
    facility_keywords = ["地面站", "站点", "测站"]
    access_keywords = ["可见性", "访问", "Access", "access", "过境"]
    if any(keyword in request for keyword in transfer_keywords):
        return "inclination_change_transfer"
    if any(keyword in request for keyword in access_keywords) and any(keyword in request for keyword in facility_keywords):
        return "satellite_facility_access"
    if any(keyword in request for keyword in facility_keywords) and not any(keyword in request for keyword in orbit_keywords):
        return "ground_facility_setup"
    if any(keyword in request for keyword in orbit_keywords):
        return "satellite_orbit_visualization"
    return "unknown"


def build_simple_task(
    intent: str,
    scenario_name: str,
    source_text: str,
    time_period: TimePeriod,
    assumptions: list[str],
    missing_fields: list[str],
    facilities: list[FacilitySpec] | None = None,
) -> StructuredTask:
    """构造不依赖 Astrogator 的简单任务对象。"""
    default_orbit = InitialOrbit(
        coordinate_type="Classical",
        epoch=time_period.start,
        sma=Quantity(value=7_000_000, unit="m"),
        ecc=0,
        inc=Quantity(value=45, unit="deg"),
        raan=Quantity(value=0, unit="deg"),
        arg_perigee=Quantity(value=0, unit="deg"),
        true_anomaly=Quantity(value=0, unit="deg"),
    )
    return StructuredTask(
        intent=intent,
        scenario_name=scenario_name,
        satellite_name="",
        time_period=time_period,
        initial_orbit=default_orbit,
        targets=None,
        mcs=None,
        source_text=source_text,
        missing_fields=missing_fields,
        assumptions=assumptions,
        facilities=facilities or [],
    )


def extract_satellite_count(request: str) -> int:
    """提取卫星数量，默认一颗，最多按 6 颗演示。"""
    text_number_map = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
    match = re.search(r"(\d+)\s*颗?卫星", request)
    if match:
        return max(1, min(int(match.group(1)), 6))
    for text, value in text_number_map.items():
        if f"{text}颗卫星" in request or f"{text}个卫星" in request:
            return value
    return 1


def extract_object_names(request: str, prefix: str, count: int) -> list[str]:
    """提取英文对象名，不足时自动补默认名。"""
    names = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", request)
    ignored = {"km", "KM", "m", "deg", "GEO", "MCS", "Access", "J2000"}
    names = [name for name in names if name not in ignored]
    if len(names) >= count:
        return names[:count]
    return [f"{prefix}{index + 1}" for index in range(count)]


def build_satellite_specs(
    request: str,
    satellite_names: list[str],
    assumptions: list[str],
) -> list[SatelliteOrbitSpec]:
    """根据自然语言构造多颗卫星轨道参数。"""
    altitudes = extract_values_with_unit(request, ["高度", "轨道高度"], default_unit="km")
    semi_major_axes = extract_values_with_unit(request, ["半长轴", "sma"], default_unit="m")
    inclinations = extract_degree_values(request, ["倾角", "inc"])
    eccentricities = extract_values_with_unit(request, ["偏心率", "ecc"], default_unit="")
    satellites: list[SatelliteOrbitSpec] = []

    if not altitudes and not semi_major_axes:
        assumptions.append("未识别轨道高度或半长轴，所有卫星默认使用 7000000 m 半长轴。")
    if not inclinations:
        assumptions.append("未识别卫星倾角，所有卫星默认使用 45 deg。")

    for index, name in enumerate(satellite_names):
        if index < len(semi_major_axes):
            sma = semi_major_axes[index]
        elif index < len(altitudes):
            sma = 6_371_000 + altitudes[index]
            assumptions.append(f"{name} 使用轨道高度换算半长轴：{sma:g} m。")
        elif semi_major_axes:
            sma = semi_major_axes[-1]
        elif altitudes:
            sma = 6_371_000 + altitudes[-1]
            assumptions.append(f"{name} 复用最后一个轨道高度换算半长轴：{sma:g} m。")
        else:
            sma = 7_000_000

        inclination = inclinations[index] if index < len(inclinations) else (inclinations[-1] if inclinations else 45)
        eccentricity = eccentricities[index] if index < len(eccentricities) else (eccentricities[-1] if eccentricities else 0)
        satellites.append(
            SatelliteOrbitSpec(
                name=name,
                sma=Quantity(value=sma, unit="m"),
                ecc=eccentricity,
                inc=Quantity(value=inclination, unit="deg"),
                raan=Quantity(value=index * 30, unit="deg"),
                arg_perigee=Quantity(value=0, unit="deg"),
                mean_anomaly=Quantity(value=index * 20, unit="deg"),
            )
        )
    return satellites


def build_facility_spec(request: str, assumptions: list[str]) -> FacilitySpec:
    """从自然语言中提取地面站名称和地理坐标。"""
    facility_name = extract_name(
        request,
        patterns=[r"地面站(?:名|名称)?[为叫：:\s]*([A-Za-z_][A-Za-z0-9_]*)"],
        default="Facility1",
        assumptions=assumptions,
        assumption_text="未指定英文地面站名，使用默认值 Facility1。",
    )
    latitude = extract_labeled_number(request, ["纬度", "lat"], default=39.9)
    longitude = extract_labeled_number(request, ["经度", "lon", "lng"], default=116.4)
    altitude = extract_facility_altitude(request)

    if "纬度" not in request and "lat" not in request:
        assumptions.append("未识别地面站纬度，使用北京附近默认值 39.9 deg。")
    if "经度" not in request and "lon" not in request and "lng" not in request:
        assumptions.append("未识别地面站经度，使用北京附近默认值 116.4 deg。")
    return FacilitySpec(
        name=facility_name,
        latitude=Quantity(value=latitude, unit="deg"),
        longitude=Quantity(value=longitude, unit="deg"),
        altitude=Quantity(value=altitude, unit="m"),
    )


def extract_facility_altitude(request: str) -> float:
    """提取地面站高度，避免误把卫星轨道高度当成地面站高度。"""
    station_match = re.search(r"(?:地面站|测站|站点)[^。；;\n]*?(?:高度|海拔)[^0-9-]*(-?\d+(?:\.\d+)?)", request)
    if station_match:
        return float(station_match.group(1))
    return extract_labeled_number(request, ["海拔", "alt"], default=0)


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


def extract_values_with_unit(request: str, keywords: list[str], default_unit: str) -> list[float]:
    """提取一组带单位的数值，用于多个卫星参数。"""
    values: list[float] = []
    keyword_pattern = "|".join(re.escape(keyword) for keyword in keywords)
    match = re.search(rf"(?:{keyword_pattern})[^。；;\n]*", request, re.IGNORECASE)
    if not match:
        return values
    search_text = match.group(0)
    for boundary in ["倾角", "偏心率", "半长轴", "高度", "纬度", "经度", "海拔"]:
        if boundary not in keywords and boundary in search_text:
            search_text = search_text.split(boundary, 1)[0]
    for value_text, unit in re.findall(r"(-?\d+(?:\.\d+)?)\s*(km|KM|千米|公里|m|米|度|deg)?", search_text):
        value = float(value_text)
        actual_unit = unit or default_unit
        if actual_unit in {"km", "KM", "千米", "公里"}:
            value *= 1000
        values.append(value)
    return values


def extract_degree_values(request: str, keywords: list[str]) -> list[float]:
    """提取一组角度值。"""
    values = extract_values_with_unit(request, keywords, default_unit="deg")
    return values


def extract_labeled_number(request: str, labels: list[str], default: float) -> float:
    """提取带标签的单个数值。"""
    for label in labels:
        match = re.search(rf"{label}[^0-9-]*(-?\d+(?:\.\d+)?)", request, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return default


def extract_orbit_size(request: str, assumptions: list[str]) -> float:
    """提取单卫星任务的轨道大小，支持半长轴或轨道高度。"""
    altitude_match = re.search(r"(?:轨道)?高度[^0-9-]*(-?\d+(?:\.\d+)?)\s*(km|KM|千米|公里|m|米)?", request)
    if altitude_match:
        altitude = float(altitude_match.group(1))
        unit = altitude_match.group(2) or "m"
        if unit in {"km", "KM", "千米", "公里"}:
            altitude *= 1000
        assumptions.append("识别到轨道高度，已按地球平均半径换算为半长轴。")
        return 6_371_000 + altitude

    return extract_number_with_keywords(
        request,
        keywords=["半长轴", "sma", "轨道"],
        default=7_000_000,
        assumptions=assumptions,
        assumption_text="未识别轨道半长轴或轨道高度，使用近地圆轨道默认值 7000000 m。",
    )


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


def estimate_orbital_period_seconds(semi_major_axis: float) -> float:
    """根据半长轴粗略估算两体圆轨道周期。"""
    earth_gravitational_parameter = 3.986004418e14
    return 2 * math.pi * math.sqrt(semi_major_axis**3 / earth_gravitational_parameter)


def add_seconds_to_atk_time(atk_time: str, seconds: float) -> str:
    """给 ATK 时间字符串增加秒数。"""
    start = datetime.strptime(atk_time, "%d %b %Y %H:%M:%S.%f")
    end = start + timedelta(seconds=seconds)
    return f"{end.day} {end.strftime('%b')} {end.year} {end.strftime('%H:%M:%S')}.000"

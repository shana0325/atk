"""调用 DeepSeek 做受限时间语义理解，并把结果应用到结构化任务。"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models import StructuredTask


CURRENT_DATE = "2026-07-26"
CURRENT_TIMEZONE = "Asia/Shanghai"
DEFAULT_MODEL = "deepseek-v4-flash"
EARTH_GRAVITATIONAL_PARAMETER = 3.986004418e14
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def interpret_time_with_deepseek(request: str, task_type: str) -> dict[str, Any]:
    """使用 DeepSeek 从自然语言中抽取时间字段。"""
    api_key = get_config_value("DEEPSEEK_API_KEY")
    if not api_key:
        return {
            "enabled": False,
            "status": "skipped",
            "provider": "deepseek",
            "reason": "未设置 DEEPSEEK_API_KEY，已跳过大模型时间理解。",
        }

    payload = build_deepseek_payload(request, task_type)
    base_url = get_config_value("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    request_url = f"{base_url}/chat/completions"
    http_request = urllib.request.Request(
        request_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(http_request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return build_error_result(f"DeepSeek HTTP 错误：{error.code} {error.reason}")
    except urllib.error.URLError as error:
        return build_error_result(f"DeepSeek 网络错误：{error.reason}")
    except TimeoutError:
        return build_error_result("DeepSeek 请求超时。")

    try:
        content = response_payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError) as error:
        return build_error_result(f"DeepSeek 返回内容不是合法 JSON：{error}")

    return normalize_time_result(parsed)


def build_deepseek_payload(request: str, task_type: str) -> dict[str, Any]:
    """构造 DeepSeek Chat Completions 请求体。"""
    return {
        "model": get_config_value("DEEPSEEK_MODEL", DEFAULT_MODEL),
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 ATK 航天任务助手里的时间字段抽取器。"
                    "只负责把自然语言中的时间含义转换成 JSON，不要生成 ATK Connect 命令。"
                    f"当前日期是 {CURRENT_DATE}，时区是 {CURRENT_TIMEZONE}。"
                    "如果用户说今天、明天、后天，必须转换为绝对日期。"
                    "如果没有明确说开始时间、结束时间、持续时间或圈数，对应字段填 null。"
                    "必须只输出 JSON，不要输出解释性正文。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请从下面任务中抽取时间字段，输出 JSON：\n"
                    "{\n"
                    '  "start_date": "YYYY-MM-DD 或 null",\n'
                    '  "start_time": "HH:MM:SS 或 null",\n'
                    '  "end_date": "YYYY-MM-DD 或 null",\n'
                    '  "end_time": "HH:MM:SS 或 null",\n'
                    '  "duration": {"value": 数字或 null, "unit": "day/hour/minute/second/null"},\n'
                    '  "orbit_count": 数字或 null,\n'
                    '  "confidence": 0到1之间的数字,\n'
                    '  "explanation": "一句中文说明",\n'
                    '  "missing_fields": ["缺失字段名"]\n'
                    "}\n\n"
                    f"任务类型：{task_type}\n"
                    f"用户输入：{request}"
                ),
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 800,
        "thinking": {"type": "disabled"},
    }


def normalize_time_result(parsed: dict[str, Any]) -> dict[str, Any]:
    """规范化 DeepSeek 时间 JSON，降低后续使用风险。"""
    duration = parsed.get("duration") if isinstance(parsed.get("duration"), dict) else {}
    return {
        "enabled": True,
        "status": "ok",
        "provider": "deepseek",
        "model": get_config_value("DEEPSEEK_MODEL", DEFAULT_MODEL),
        "time_fields": {
            "start_date": normalize_optional_string(parsed.get("start_date")),
            "start_time": normalize_optional_string(parsed.get("start_time")),
            "end_date": normalize_optional_string(parsed.get("end_date")),
            "end_time": normalize_optional_string(parsed.get("end_time")),
            "duration": {
                "value": normalize_optional_number(duration.get("value")),
                "unit": normalize_duration_unit(duration.get("unit")),
            },
            "orbit_count": normalize_optional_number(parsed.get("orbit_count")),
        },
        "confidence": normalize_confidence(parsed.get("confidence")),
        "explanation": str(parsed.get("explanation") or ""),
        "missing_fields": parsed.get("missing_fields") if isinstance(parsed.get("missing_fields"), list) else [],
    }


def apply_time_understanding(task: StructuredTask, time_result: dict[str, Any]) -> StructuredTask:
    """把时间理解结果应用到结构化任务。"""
    task.time_understanding = time_result
    if time_result.get("status") != "ok":
        return task

    fields = time_result.get("time_fields", {})
    if not isinstance(fields, dict):
        return task

    start_datetime = build_datetime(
        fields.get("start_date"),
        fields.get("start_time"),
        fallback=parse_atk_datetime(task.time_period.start),
    )
    if start_datetime:
        task.time_period.start = format_atk_datetime(start_datetime)
        task.initial_orbit.epoch = task.time_period.start

    end_datetime = build_datetime(fields.get("end_date"), fields.get("end_time"), fallback=None)
    if not end_datetime:
        end_datetime = build_end_from_duration(start_datetime, fields)
    if not end_datetime:
        end_datetime = build_end_from_orbit_count(task, start_datetime, fields)

    if end_datetime:
        task.time_period.end = format_atk_datetime(end_datetime)
        task.assumptions.append("已使用 DeepSeek 时间理解结果更新分析时间。")
    return task


def build_datetime(date_value: object, time_value: object, fallback: datetime | None) -> datetime | None:
    """根据日期和时间字段构造 datetime。"""
    if not date_value:
        return fallback
    time_text = str(time_value or "00:00:00")
    try:
        return datetime.strptime(f"{date_value} {time_text}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return fallback


def build_end_from_duration(start_datetime: datetime | None, fields: dict[str, Any]) -> datetime | None:
    """根据持续时间计算结束时间。"""
    if not start_datetime:
        return None
    duration = fields.get("duration", {})
    if not isinstance(duration, dict):
        return None
    value = duration.get("value")
    unit = duration.get("unit")
    if value is None or not unit:
        return None
    seconds = duration_to_seconds(float(value), str(unit))
    return start_datetime + timedelta(seconds=seconds)


def build_end_from_orbit_count(
    task: StructuredTask,
    start_datetime: datetime | None,
    fields: dict[str, Any],
) -> datetime | None:
    """根据圈数和半长轴估算结束时间。"""
    if not start_datetime:
        return None
    orbit_count = fields.get("orbit_count")
    if orbit_count is None:
        return None
    semi_major_axis = task.satellites[0].sma.value if task.satellites else task.initial_orbit.sma.value
    period_seconds = 2 * math.pi * math.sqrt(semi_major_axis**3 / EARTH_GRAVITATIONAL_PARAMETER)
    return start_datetime + timedelta(seconds=period_seconds * float(orbit_count))


def duration_to_seconds(value: float, unit: str) -> float:
    """把持续时间单位转换为秒。"""
    unit_seconds = {
        "day": 86400,
        "hour": 3600,
        "minute": 60,
        "second": 1,
    }
    return value * unit_seconds.get(unit, 0)


def parse_atk_datetime(value: str) -> datetime | None:
    """解析 ATK 常用日期字符串。"""
    try:
        return datetime.strptime(value, "%d %b %Y %H:%M:%S.%f")
    except ValueError:
        return None


def format_atk_datetime(value: datetime) -> str:
    """格式化为 ATK 常用日期字符串。"""
    return f"{value.day} {value.strftime('%b')} {value.year} {value.strftime('%H:%M:%S')}.000"


def normalize_optional_string(value: object) -> str | None:
    """规范化可选字符串字段。"""
    if value in {None, "", "null", "None"}:
        return None
    return str(value)


def normalize_optional_number(value: object) -> float | None:
    """规范化可选数字字段。"""
    try:
        if value in {None, "", "null", "None"}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_duration_unit(value: object) -> str | None:
    """规范化持续时间单位。"""
    unit = normalize_optional_string(value)
    if unit in {"day", "hour", "minute", "second"}:
        return unit
    return None


def normalize_confidence(value: object) -> float:
    """规范化置信度。"""
    number = normalize_optional_number(value)
    if number is None:
        return 0
    return max(0, min(1, number))


def build_error_result(reason: str) -> dict[str, Any]:
    """构造 DeepSeek 时间理解失败结果。"""
    return {
        "enabled": True,
        "status": "error",
        "provider": "deepseek",
        "reason": reason,
    }


def get_config_value(name: str, default: str = "") -> str:
    """优先读取环境变量，其次读取项目根目录 .env。"""
    env_value = os.environ.get(name)
    if env_value:
        return env_value.strip()

    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return default
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue
        key, value = stripped_line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return default

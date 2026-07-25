"""定义 ATK 自然语言 Demo 使用的结构化任务数据模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Quantity:
    """表示带单位的数值参数。"""

    value: float
    unit: str


@dataclass
class TimePeriod:
    """表示 ATK 场景分析时间范围。"""

    start: str
    end: str


@dataclass
class InitialOrbit:
    """表示倾角改变转移任务的初始轨道参数。"""

    coordinate_type: str
    epoch: str
    sma: Quantity
    ecc: float
    inc: Quantity
    raan: Quantity
    arg_perigee: Quantity
    true_anomaly: Quantity


@dataclass
class TransferTargets:
    """表示倾角改变转移任务的目标约束。"""

    apoapsis_radius: Quantity
    final_eccentricity: float
    final_inclination: Quantity


@dataclass
class McsSettings:
    """表示 Astrogator MCS 运行配置。"""

    run_after_generation: bool
    final_propagate_duration: Quantity


@dataclass
class StructuredTask:
    """表示 AI 解析后的受约束结构化任务。"""

    intent: str
    scenario_name: str
    satellite_name: str
    time_period: TimePeriod
    initial_orbit: InitialOrbit
    targets: TransferTargets
    mcs: McsSettings
    source_text: str
    missing_fields: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化字典。"""
        return asdict(self)

"""提供 Connect 命令到 ATK 帮助文档页面的轻量映射。"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote


HELP_ROOT = Path(r"D:\Shana\ATK-4.0.1\Help\html")
CONNECT_ROOT = HELP_ROOT / "二次开发教程" / "2-二次开发CONNECT模式" / "2-命令参考"
OBJECT_COMMAND_ROOT = CONNECT_ROOT / "3-Connect对象命令库"
ASTROGATOR_COMMAND_ROOT = CONNECT_ROOT / "4-Connect机动规划命令库"


def get_help_reference(command: str, cmd_string: str) -> dict[str, object]:
    """根据 Connect 命令返回帮助页链接、语法说明和排错提示。"""
    command = command.strip()
    cmd_string = cmd_string.strip()

    if command == "New":
        return build_reference(
            title="New：新建场景或对象",
            path=OBJECT_COMMAND_ROOT / "场景" / "New.html",
            syntax="New <ApplicationPath> <ClassPath> <NewObjectName> {NewOptions}",
            examples=[
                "New / Scenario See_DC",
                "New / */Satellite Satellite1 CentralBody Earth",
                "New / */Satellite/Satellite1/Sensor Sensor1",
            ],
            hints=get_new_hints(cmd_string),
        )

    if command == "SetAnalysisTimePeriod":
        return build_reference(
            title="SetAnalysisTimePeriod：设置场景分析时间",
            path=OBJECT_COMMAND_ROOT / "场景" / "SetAnalysisTimePeriod.html",
            syntax='SetAnalysisTimePeriod * "<StartTime>" "<StopTime>"',
            examples=['SetAnalysisTimePeriod * "5 Nov 2022 00:00:00.000" "8 Nov 2022 00:00:00.000"'],
            hints=["检查时间格式是否符合 ATK Connect 日期时间格式。", "检查当前是否已经存在有效场景。"],
        )

    if command == "Animate":
        return build_reference(
            title="Animate：仿真动画控制",
            path=OBJECT_COMMAND_ROOT / "场景" / "Animate.html",
            syntax="Animate <ApplicationPath> <AnimationOption>",
            examples=["Animate * Reset"],
            hints=["检查对象路径是否为 *。", "如果没有打开场景，动画命令可能失败。"],
        )

    if command == "Graphics":
        return build_reference(
            title="Graphics Basic：卫星二维显示属性",
            path=OBJECT_COMMAND_ROOT / "卫星" / "Graphics" / "Graphics Basic.html",
            syntax="Graphics <ObjectPath> Basic <Option> <Value>",
            examples=["Graphics */Satellite/Satellite1 Basic LineWidth 2"],
            hints=["检查卫星对象是否已经成功创建。", "检查对象路径中的卫星名称是否正确。"],
        )

    if command == "SetState":
        return build_reference(
            title="SetState Classical：设置卫星经典轨道状态",
            path=OBJECT_COMMAND_ROOT / "卫星" / "SetState" / "SetState Classical.html",
            syntax=(
                'SetState <VehObjectPath> Classical {Propagator} {TimeInterval} <StepSize> '
                '{CoordSystem} "<OrbitEpoch>" <SemiMajorAxis> <Eccentricity> '
                "<Inclination> <ArgOfPerigee> <RAAN> <MeanAnom>"
            ),
            examples=[
                'SetState */Satellite/Satellite1 Classical HPOP "1 Nov 2000 00:00:00.00" "1 Nov 2000 04:00:00.00" 60 J2000 "1 Nov 2000 00:00:00.00" 7163000.137079 0.5 98.5 0.0 139.7299 120.0'
            ],
            hints=[
                "检查卫星对象是否已经成功创建。",
                "检查半长轴是否大于地球半径，偏心率是否位于 [0, 1]。",
                "检查开始时间、结束时间和历元时间是否符合 ATK 日期格式。",
            ],
        )

    if command == "SetPosition":
        return build_reference(
            title="SetPosition：设置地面站位置",
            path=OBJECT_COMMAND_ROOT / "地面站" / "Set Position.html",
            syntax="SetPosition <ObjectPath> Geodetic <Lat> <Lon> <Altitude>",
            examples=["SetPosition */Facility/Facility1 Geodetic 37.9 -75.5 0.0"],
            hints=[
                "检查地面站对象是否已经创建。",
                "检查纬度是否位于 [-90, 90]，经度是否位于 [-180, 180]。",
                "当前 Demo 使用 Geodetic 经纬高格式。",
            ],
        )

    if command == "Access":
        return build_reference(
            title="Access：计算两个对象之间的可见性",
            path=OBJECT_COMMAND_ROOT / "工具" / "可见性命令" / "Access.html",
            syntax="Access <ObjectPath> <AccessObjectPath> {TimePeriod <StartTime> <StopTime>}",
            examples=[
                'Access */Satellite/Sat1 */Facility/Facility1 TimePeriod "5 Nov 2022 00:00:00.000" "6 Nov 2022 00:00:00.000"'
            ],
            hints=[
                "检查两个对象路径是否都已成功创建。",
                "检查 TimePeriod 时间格式是否符合 ATK Connect 日期格式。",
                "如果前面的 New 或 SetState 返回 NACK，可见性计算通常也会失败。",
            ],
        )

    if command == "Astrogator":
        return get_astrogator_reference(cmd_string)

    return build_reference(
        title=f"{command}：未配置精确帮助页",
        path=CONNECT_ROOT / "index.html",
        syntax="暂未配置",
        examples=[],
        hints=["当前命令尚未配置专门帮助页映射，可先查看 Connect 命令参考总目录。"],
    )


def get_astrogator_reference(cmd_string: str) -> dict[str, object]:
    """根据 Astrogator 二级命令返回更精确的帮助页。"""
    rules = [
        (
            "SetProp",
            "设置轨道预报器为机动规划",
            ASTROGATOR_COMMAND_ROOT / "命令" / "设置轨道预报器为机动规划.html",
            "Astrogator <SatellitePath> SetProp",
            ["检查卫星对象是否已经创建。", "检查对象路径是否为 */Satellite/<Name>。"],
        ),
        (
            "InsertSegment",
            "规划插入段",
            ASTROGATOR_COMMAND_ROOT / "命令" / "规划插入段.html",
            "Astrogator <SatellitePath> InsertSegment <SegmentPath> <SegmentType>",
            ["检查段路径是否存在。", "检查段类型名是否正确，例如 Propagate、Target_Sequence、Maneuver。"],
        ),
        (
            "AddMCSSegmentControl",
            "规划增加段控制量",
            ASTROGATOR_COMMAND_ROOT / "命令" / "规划增加段控制量.html",
            "Astrogator <SatellitePath> AddMCSSegmentControl <SegmentPath> <ControlName>",
            ["检查目标段是否已经创建。", "检查控制量名称是否正确。"],
        ),
        (
            "SetMCSControlValue",
            "规划设置段控制量",
            ASTROGATOR_COMMAND_ROOT / "命令" / "规划设置段控制量.html",
            "Astrogator <SatellitePath> SetMCSControlValue <ProfilePath> <Segment> <Control> <Property> <Value>",
            ["检查 Differential_Corrector 是否已创建。", "检查控制量是否已先 AddMCSSegmentControl。"],
        ),
        (
            "SetMCSConstraintValue",
            "规划设置段约束值",
            ASTROGATOR_COMMAND_ROOT / "命令" / "规划设置段约束值.html",
            "Astrogator <SatellitePath> SetMCSConstraintValue <ProfilePath> <Segment> <Constraint> <Property> <Value>",
            ["检查结果约束是否已加入 Maneuver.Results。", "检查约束名是否正确，例如 StateCalcEccentricity。"],
        ),
        (
            "RunMCS",
            "运行轨道规划",
            ASTROGATOR_COMMAND_ROOT / "命令" / "运行轨道规划.html",
            "Astrogator <SatellitePath> RunMCS",
            ["检查 MCS 段序列是否配置完整。", "若前面有 NACK，RunMCS 可能无法得到预期结果。"],
        ),
        (
            "SetValue",
            "规划设置属性值",
            ASTROGATOR_COMMAND_ROOT / "命令" / "规划设置属性值.html",
            "Astrogator <SatellitePath> SetValue <PropertyPath> <Value>",
            ["检查属性路径是否准确。", "检查单位、枚举值、段名是否符合帮助文档。"],
        ),
    ]

    for keyword, title, path, syntax, hints in rules:
        if keyword in cmd_string:
            return build_reference(
                title=f"Astrogator：{title}",
                path=path,
                syntax=syntax,
                examples=[],
                hints=hints,
            )

    return build_reference(
        title="Astrogator：机动规划命令库",
        path=ASTROGATOR_COMMAND_ROOT / "index.html",
        syntax="Astrogator <SatellitePath> <SubCommand> ...",
        examples=[],
        hints=["未识别具体 Astrogator 子命令，请查看机动规划命令库总目录。"],
    )


def get_new_hints(cmd_string: str) -> list[str]:
    """根据 New 命令参数返回更具体的排错提示。"""
    common_hints = [
        "检查对象是否已经存在，同名对象重复创建可能返回 NACK。",
        "检查当前 ATK 是否已有打开场景，必要时先关闭或更换场景名。",
    ]
    if "Satellite" in cmd_string:
        return common_hints + [
            "文档示例中卫星创建形式为：New / */Satellite Satellite1 CentralBody Earth。",
            "如果前一步 New Scenario 失败，卫星创建也可能跟着失败。",
        ]
    if "Scenario" in cmd_string:
        return common_hints + [
            "场景创建示例为：New / Scenario See_DC。",
            "如果场景 InclinationChange 已存在，可以换名或先卸载旧场景。",
        ]
    return common_hints


def build_reference(
    title: str,
    path: Path,
    syntax: str,
    examples: list[str],
    hints: list[str],
) -> dict[str, object]:
    """构造帮助引用对象。"""
    return {
        "title": title,
        "doc_path": str(path),
        "doc_url": path_to_file_url(path),
        "exists": path.exists(),
        "syntax": syntax,
        "examples": examples,
        "troubleshooting_hints": hints,
    }


def path_to_file_url(path: Path) -> str:
    """将 Windows 本地路径转换为 file URL。"""
    return "file:///" + quote(str(path).replace("\\", "/"), safe="/:()-.%")

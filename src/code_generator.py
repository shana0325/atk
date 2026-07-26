"""根据结构化任务生成 ATK Connect Python 代码。"""

from __future__ import annotations

import json
from pathlib import Path

from .models import StructuredTask


def generate_connect_code(task: StructuredTask, template_path: Path) -> str:
    """使用受控模板生成 Connect Python 代码。"""
    if task.intent in {
        "satellite_orbit_visualization",
        "ground_facility_setup",
        "satellite_facility_access",
    }:
        return generate_command_list_script(task)

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
    }
    if task.targets:
        replacements.update(
            {
                "apoapsis_radius": format_number(task.targets.apoapsis_radius.value),
                "final_eccentricity": format_number(task.targets.final_eccentricity),
                "final_inclination": format_number(task.targets.final_inclination.value),
            }
        )
    if task.mcs:
        replacements["final_duration"] = format_number(task.mcs.final_propagate_duration.value)

    generated_code = template
    for placeholder, value in replacements.items():
        generated_code = generated_code.replace("{{" + placeholder + "}}", value)
    return generated_code


def generate_command_list_script(task: StructuredTask) -> str:
    """根据原子 Connect 命令列表生成可执行 Python 脚本。"""
    commands = build_connect_commands(task)
    commands_literal = json.dumps(commands, ensure_ascii=False, indent=4)
    return f'''"""由原子 Connect 命令编排生成的 ATK Python 脚本。"""

from __future__ import annotations

import json
from pathlib import Path

from ATKConnectModule import atkClose, atkConnect as raw_atkConnect, atkOpen

# 真实运行前请确保 ATK 已启动，Connect 端口为 6655。

COMMANDS = {commands_literal}
CONNECT_LOGS: list[dict[str, str | int]] = []


def atkConnect(conID: int, command: str, cmd_string: str) -> str:
    """发送 Connect 命令，记录返回结果但不中断后续流程。"""
    step = getattr(atkConnect, "step", 0) + 1
    setattr(atkConnect, "step", step)
    result = raw_atkConnect(conID, command, cmd_string)
    result_text = "" if result is None else str(result)
    status = classify_result(result_text)
    CONNECT_LOGS.append(
        {{
            "step": step,
            "status": status,
            "command": command,
            "cmd_string": cmd_string,
            "result": result_text,
        }}
    )
    if status != "ok":
        print(f"[WARN] Connect 第 {{step}} 步返回 {{result_text or '<empty>'}}，已记录并继续执行。")
    return result


def classify_result(result: str) -> str:
    """将 ATK 返回值归类为 ok 或 nack，便于后续筛选展示。"""
    normalized_result = result.strip().upper()
    if normalized_result.startswith("NACK") or normalized_result == "FALSE":
        return "nack"
    return "ok"


def write_connect_logs() -> None:
    """将 Connect 执行日志写入 JSON 和 Markdown 文件。"""
    output_dir = Path(__file__).resolve().parent
    json_path = output_dir / "connect_execution_log.json"
    markdown_path = output_dir / "connect_execution_log.md"
    nack_logs = [item for item in CONNECT_LOGS if item["status"] == "nack"]
    json_path.write_text(
        json.dumps(
            {{
                "summary": {{
                    "total": len(CONNECT_LOGS),
                    "nack": len(nack_logs),
                    "ok": len(CONNECT_LOGS) - len(nack_logs),
                }},
                "logs": CONNECT_LOGS,
            }},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    lines = [
        "# ATK Connect 执行日志",
        "",
        f"- 总命令数：{{len(CONNECT_LOGS)}}",
        f"- NACK/失败信号：{{len(nack_logs)}}",
        f"- OK/空返回：{{len(CONNECT_LOGS) - len(nack_logs)}}",
        "",
        "## NACK 命令",
        "",
    ]
    if nack_logs:
        for item in nack_logs:
            lines.extend(
                [
                    f"### 第 {{item['step']}} 步",
                    "",
                    f"- 命令名：`{{item['command']}}`",
                    f"- 命令参数：`{{item['cmd_string']}}`",
                    f"- 返回：`{{item['result'] or '<empty>'}}`",
                    "",
                ]
            )
    else:
        lines.append("未发现 NACK。")
    lines.extend(["", "## 全部命令", ""])
    for item in CONNECT_LOGS:
        lines.append(
            f"- [{{item['status'].upper()}}] 第 {{item['step']}} 步：`{{item['command']}}` | `{{item['cmd_string']}}` | 返回：`{{item['result'] or '<empty>'}}`"
        )
    markdown_path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print(f"[SUMMARY] total={{len(CONNECT_LOGS)}}, nack={{len(nack_logs)}}, ok={{len(CONNECT_LOGS) - len(nack_logs)}}")
    print(f"[LOG] Connect 执行日志已写入：{{json_path}}")
    print(f"[LOG] Connect 执行摘要已写入：{{markdown_path}}")


def run() -> None:
    """执行由结构化任务编排得到的 Connect 命令。"""
    print("[ATK] 正在连接 127.0.0.1:6655 ...")
    conID = atkOpen("127.0.0.1", 6655)
    print(f"[ATK] 连接成功，conID={{conID}}")
    for command, cmd_string in COMMANDS:
        atkConnect(conID, command, cmd_string)
    print("[ATK] 命令序列已发送。")
    print("[ATK] 正在关闭 Connect 连接 ...")
    atkClose(conID)
    print("[ATK] Connect 连接已关闭。")
    write_connect_logs()


if __name__ == "__main__":
    run()
'''


def build_connect_commands(task: StructuredTask) -> list[list[str]]:
    """把结构化任务转换为原子 Connect 命令列表。"""
    commands: list[list[str]] = [
        ["New", f"/ Scenario {task.scenario_name}"],
        ["SetAnalysisTimePeriod", f'* "{task.time_period.start}" "{task.time_period.end}"'],
    ]

    for satellite in task.satellites:
        commands.extend(
            [
                ["New", f"/ */Satellite {satellite.name} CentralBody Earth"],
                [
                    "SetState",
                    (
                        f'*/Satellite/{satellite.name} Classical TwoBody '
                        f'"{task.time_period.start}" "{task.time_period.end}" 60 J2000 '
                        f'"{task.time_period.start}" {format_number(satellite.sma.value)} '
                        f"{format_number(satellite.ecc)} {format_number(satellite.inc.value)} "
                        f"{format_number(satellite.arg_perigee.value)} {format_number(satellite.raan.value)} "
                        f"{format_number(satellite.mean_anomaly.value)}"
                    ),
                ],
                ["Graphics", f"*/Satellite/{satellite.name} Basic LineWidth 2"],
            ]
        )

    for facility in task.facilities:
        commands.extend(
            [
                ["New", f"/ */Facility {facility.name}"],
                [
                    "SetPosition",
                    (
                        f"*/Facility/{facility.name} Geodetic "
                        f"{format_number(facility.latitude.value)} "
                        f"{format_number(facility.longitude.value)} "
                        f"{format_number(facility.altitude.value)}"
                    ),
                ],
            ]
        )

    for pair in task.access_pairs:
        commands.append(
            [
                "Access",
                f'{pair.from_object} {pair.to_object} TimePeriod "{task.time_period.start}" "{task.time_period.end}"',
            ]
        )

    commands.append(["Animate", "* Reset"])
    return commands


def format_number(value: float) -> str:
    """格式化数值，避免整数参数出现多余小数点。"""
    if float(value).is_integer():
        return str(int(value))
    return str(value)

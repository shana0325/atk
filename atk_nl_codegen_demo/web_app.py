"""本地网页服务入口，用于展示自然语言解析、生成结果和 Connect 执行日志。"""

from __future__ import annotations

import json
import mimetypes
import os
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.demo_runner import DEFAULT_REQUEST, GENERATED_DIR, PROJECT_ROOT, TASK_TYPE_OPTIONS, run_demo_artifacts
from src.help_links import HELP_ROOT, get_help_reference


WEB_DIR = PROJECT_ROOT / "web"
HOST = "127.0.0.1"
PORT = 8765


class AtkDemoWebHandler(BaseHTTPRequestHandler):
    """处理本地网页和 JSON API 请求。"""

    def do_GET(self) -> None:
        """处理 GET 请求。"""
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            self.serve_file(WEB_DIR / "index.html")
            return
        if parsed_url.path.startswith("/static/"):
            static_path = parsed_url.path[len("/static/") :]
            self.serve_static_file(static_path)
            return
        if parsed_url.path == "/api/sample":
            query = parse_qs(parsed_url.query)
            task_type = query.get("task_type", ["inclination_change_transfer"])[0]
            self.send_json({"request": get_sample_request(task_type)})
            return
        if parsed_url.path == "/api/task-types":
            self.send_json({"task_types": TASK_TYPE_OPTIONS})
            return
        if parsed_url.path == "/api/logs":
            self.send_json(read_connect_logs())
            return
        if parsed_url.path == "/api/help":
            query = parse_qs(parsed_url.query)
            command = query.get("command", [""])[0]
            cmd_string = query.get("cmd_string", [""])[0]
            self.send_json(get_help_reference(command, cmd_string))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        """处理 POST 请求。"""
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/parse":
            payload = self.read_json_body()
            request = str(payload.get("request", "")).strip()
            task_type = str(payload.get("task_type", "auto")).strip() or "auto"
            if not request:
                self.send_json({"error": "自然语言任务不能为空。"}, status=HTTPStatus.BAD_REQUEST)
                return
            try:
                self.send_json(run_demo_artifacts(request, task_type=task_type))
            except ValueError as error:
                self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as error:  # noqa: BLE001
                self.send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed_url.path == "/api/execute-latest":
            try:
                self.send_json(execute_latest_script())
            except FileNotFoundError as error:
                self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except TimeoutError as error:
                self.send_json({"error": str(error)}, status=HTTPStatus.GATEWAY_TIMEOUT)
            except Exception as error:  # noqa: BLE001
                self.send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed_url.path == "/api/open-help":
            payload = self.read_json_body()
            command = str(payload.get("command", "")).strip()
            cmd_string = str(payload.get("cmd_string", "")).strip()
            try:
                self.send_json(open_help_page(command, cmd_string))
            except FileNotFoundError as error:
                self.send_json({"error": str(error)}, status=HTTPStatus.NOT_FOUND)
            except PermissionError as error:
                self.send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except Exception as error:  # noqa: BLE001
                self.send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def read_json_body(self) -> dict[str, object]:
        """读取 JSON 请求体。"""
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw_body = self.rfile.read(length).decode("utf-8")
        return json.loads(raw_body)

    def send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        """返回 JSON 响应。"""
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def serve_file(self, path: Path) -> None:
        """返回静态文件。"""
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        encoded = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def serve_static_file(self, static_path: str) -> None:
        """只允许读取 web 目录内的静态资源。"""
        target_path = (WEB_DIR / static_path).resolve()
        if WEB_DIR.resolve() not in [target_path, *target_path.parents]:
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return
        self.serve_file(target_path)

    def log_message(self, format: str, *args: object) -> None:
        """减少默认请求日志噪声。"""
        print(f"[WEB] {self.address_string()} - {format % args}")


def read_connect_logs() -> dict[str, object]:
    """读取 Connect 执行日志，如果不存在则返回空状态。"""
    log_path = GENERATED_DIR / "connect_execution_log.json"
    if not log_path.exists():
        return {
            "summary": {"total": 0, "nack": 0, "ok": 0},
            "logs": [],
            "message": "尚未找到 connect_execution_log.json，请先运行生成脚本连接 ATK。",
        }
    return json.loads(log_path.read_text(encoding="utf-8"))


def execute_latest_script() -> dict[str, object]:
    """执行最近一次生成的 Connect Python 脚本，并返回执行结果。"""
    script_path = GENERATED_DIR / "generated_connect_latest.py"
    sdk_path = GENERATED_DIR / "ATKConnectModule.py"
    native_sdk_path = GENERATED_DIR / "_ATKConnectModule.pyd"
    if not script_path.exists():
        raise FileNotFoundError("尚未生成 generated_connect_latest.py，请先点击“解析并生成代码”。")
    if not sdk_path.exists() or not native_sdk_path.exists():
        raise FileNotFoundError("generated 目录缺少 ATKConnectModule.py 或 _ATKConnectModule.pyd，无法直接连接 ATK。")

    clear_previous_connect_logs()
    result = subprocess.run(
        [sys.executable, script_path.name],
        cwd=GENERATED_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    logs = read_connect_logs()
    return {
        "script": str(script_path),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "logs": logs,
        "success": result.returncode == 0,
    }


def open_help_page(command: str, cmd_string: str) -> dict[str, object]:
    """通过本机系统打开对应的 ATK 本地帮助页。"""
    help_reference = get_help_reference(command, cmd_string)
    doc_path = Path(str(help_reference["doc_path"])).resolve()
    help_root = HELP_ROOT.resolve()
    if help_root not in [doc_path, *doc_path.parents]:
        raise PermissionError("帮助页路径不在 ATK 帮助目录内，已拒绝打开。")
    if not doc_path.exists():
        raise FileNotFoundError(f"未找到帮助页：{doc_path}")

    os.startfile(str(doc_path))  # type: ignore[attr-defined]
    return {"opened": True, "doc_path": str(doc_path)}


def clear_previous_connect_logs() -> None:
    """清理旧执行日志，避免执行失败时页面误读上一次日志。"""
    for filename in ["connect_execution_log.json", "connect_execution_log.md"]:
        log_path = GENERATED_DIR / filename
        if log_path.exists():
            log_path.unlink()


def get_sample_request(task_type: str) -> str:
    """根据任务类型返回示例输入。"""
    for option in TASK_TYPE_OPTIONS:
        if option["id"] == task_type:
            return str(option["sample"])
    return DEFAULT_REQUEST


def main() -> None:
    """启动本地 Web 服务。"""
    server = ThreadingHTTPServer((HOST, PORT), AtkDemoWebHandler)
    print(f"ATK Demo Web 页面已启动：http://{HOST}:{PORT}")
    print("按 Ctrl+C 停止服务。")
    server.serve_forever()


if __name__ == "__main__":
    main()

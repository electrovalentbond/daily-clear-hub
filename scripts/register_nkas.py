"""Register the installed NKAS adapter as a local AUTO-MAS General profile."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.auto_setup import DEFAULT_TOOLS_ROOT
from core.automas_backend import (
    DEFAULT_PORT, NKAS_ADAPTER, NKAS_FAILURE, NKAS_SUCCESS,
    _check_success, _request, _validate_port, discover_automas,
)


PROFILE_NAME = "NIKKE 国际服（NKAS）"


def settings_for(adapter: Path, with_uu: bool) -> dict:
    runner = adapter / "run.py"
    arguments = f'-X utf8 -u "{runner.as_posix()}"'
    if with_uu:
        arguments += " --uu"
    return {
        "Info": {"Name": PROFILE_NAME, "RootPath": str(adapter)},
        "Game": {"Enabled": False},
        "Run": {"RunTimeLimit": 45, "RunTimesLimit": 1},
        "Script": {
            "ScriptPath": str(adapter / ".venv" / "Scripts" / "python.exe"),
            "Arguments": arguments,
            "IfTrackProcess": False,
            "ConfigPath": str(adapter / "nikke.json"),
            "ConfigPathMode": "File",
            "UpdateConfigMode": "Never",
            "LogPath": str(adapter / "logs" / "run-20000101-000000-000000.log"),
            "LogPathFormat": "run-%Y%m%d-%H%M%S-%f",
            "LogTimeStart": 1,
            "LogTimeEnd": 26,
            "LogTimeFormat": "%Y-%m-%d %H:%M:%S.%f",
            "SuccessLog": NKAS_SUCCESS,
            "SuccessLogMode": "Regex",
            "ErrorLog": NKAS_FAILURE,
            "ErrorLogMode": "Regex",
        },
    }


def register(tools_root: Path, port: int, with_uu: bool) -> str:
    port = _validate_port(port)
    adapter = tools_root / NKAS_ADAPTER
    settings = settings_for(adapter, with_uu)
    script = settings["Script"]
    paths = (
        script["ScriptPath"], script["ConfigPath"], script["LogPath"],
        adapter / "local.json", adapter / "run.py", adapter / "run_once.py",
    )
    if not all(Path(path).is_file() for path in paths):
        raise ValueError("NKAS 托管尚未准备好，请先运行 setup-windows.ps1 -Games nikke")
    if with_uu:
        uu_root = tools_root / "uu-automas"
        if not (uu_root / "uu_boost.py").is_file() or not (uu_root / ".venv/Scripts/python.exe").is_file():
            raise ValueError("启用 UU 前请运行 setup-windows.ps1 -Games nikke -WithUu")

    existing = discover_automas(port, ("nikke",))["nikke"]
    if len(existing) > 1:
        raise ValueError("发现多个 NKAS 托管，请先在 AUTO-MAS 中保留一个")

    def request(endpoint: str, payload: dict, label: str) -> dict:
        response = _request(port, f"/api/scripts/{endpoint}", payload)
        _check_success(response, label)
        return response

    uid = existing[0].script_id if existing else request("add", {"type": "General"}, "创建 NKAS 托管")["scriptId"]
    request("update", {"scriptId": uid, "data": settings}, "保存 NKAS 托管")
    users = request("user/get", {"scriptId": uid}, "读取 NKAS 账号")["data"]
    if not users:
        user = request("user/add", {"scriptId": uid}, "创建 NKAS 账号")["userId"]
        request("user/update", {
            "scriptId": uid, "userId": user,
            "data": {"Info": {"Name": "NKAS 本机实例", "Base": "native", "Status": True}},
        }, "启用 NKAS 账号")
    return uid


def main() -> int:
    parser = argparse.ArgumentParser(description="为本机 AUTO-MAS 注册 NIKKE 国际服 NKAS 托管")
    parser.add_argument("--tools-root", type=Path, default=DEFAULT_TOOLS_ROOT)
    parser.add_argument("--automas-port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--with-uu", action="store_true")
    args = parser.parse_args()
    try:
        uid = register(args.tools_root.resolve(), args.automas_port, args.with_uu)
    except (OSError, KeyError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"{PROFILE_NAME} 已配置（{uid}）。在 AUTO-MAS 调度队列中添加该托管。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
